"""Parser for .flp flightplan files (Aerosoft/Fenix CFMS format)."""
from pathlib import Path
from typing import Optional
import re

from .base import FlightplanParser
from ..models import Flightplan, Waypoint, WaypointType


class FlpParser(FlightplanParser):
    """Parser for .flp files (CFMS format).

    Used by:
    - Fenix A320 series
    - FlyByWire A32NX
    - Aerosoft CRJ series
    """

    @property
    def supported_extensions(self) -> list[str]:
        return ['.flp']

    def parse(self, file_path: Path) -> Optional[Flightplan]:
        """Parse a .flp CFMS format flightplan file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            flightplan = Flightplan(source_file=str(file_path))

            # Parse based on format (CFMS or legacy)
            if '[CoRte]' in content:
                return self._parse_corte_format(content, flightplan)
            else:
                return self._parse_cfms_format(content, flightplan)

        except Exception as e:
            print(f"Error parsing FLP file {file_path}: {e}")
            return None

    def _parse_cfms_format(self, content: str, flightplan: Flightplan) -> Optional[Flightplan]:
        """Parse CFMS format .flp file."""
        lines = content.strip().split('\n')

        current_waypoint = {}
        waypoints = []

        for line in lines:
            line = line.strip()
            if not line:
                if current_waypoint:
                    wpt = self._create_waypoint(current_waypoint)
                    if wpt:
                        waypoints.append(wpt)
                    current_waypoint = {}
                continue

            if '=' in line:
                key, value = line.split('=', 1)
                current_waypoint[key.strip()] = value.strip()

        # Don't forget the last waypoint
        if current_waypoint:
            wpt = self._create_waypoint(current_waypoint)
            if wpt:
                waypoints.append(wpt)

        if waypoints:
            flightplan.departure = waypoints[0]
            flightplan.departure.waypoint_type = WaypointType.AIRPORT
            flightplan.destination = waypoints[-1]
            flightplan.destination.waypoint_type = WaypointType.AIRPORT
            flightplan.waypoints = waypoints[1:-1] if len(waypoints) > 2 else []

            flightplan.title = f"{flightplan.departure_icao} to {flightplan.destination_icao}"

        return flightplan

    def _parse_corte_format(self, content: str, flightplan: Flightplan) -> Optional[Flightplan]:
        """Parse CoRte (company route) format .flp file."""
        lines = content.strip().split('\n')

        waypoints = []
        in_route_section = False

        for line in lines:
            line = line.strip()

            if line.startswith('[CoRte]'):
                in_route_section = True
                continue

            if line.startswith('['):
                in_route_section = False
                continue

            if in_route_section and line:
                parts = line.split()
                if len(parts) == 1:
                    # Single identifier - likely airport code
                    wpt = Waypoint(
                        ident=parts[0],
                        latitude=0.0,
                        longitude=0.0,
                        waypoint_type=WaypointType.AIRPORT
                    )
                    waypoints.append(wpt)
                elif len(parts) >= 4:
                    # Format: IDENT TYPE LAT LON ALTITUDE SPEED AIRWAY
                    wpt = self._parse_corte_waypoint(parts)
                    if wpt:
                        waypoints.append(wpt)

        if waypoints:
            flightplan.departure = waypoints[0]
            flightplan.departure.waypoint_type = WaypointType.AIRPORT
            flightplan.destination = waypoints[-1]
            flightplan.destination.waypoint_type = WaypointType.AIRPORT
            flightplan.waypoints = waypoints[1:-1] if len(waypoints) > 2 else []

            flightplan.title = f"{flightplan.departure_icao} to {flightplan.destination_icao}"

        return flightplan

    def _create_waypoint(self, data: dict) -> Optional[Waypoint]:
        """Create waypoint from parsed CFMS data."""
        try:
            ident = data.get('ident') or data.get('Ident') or data.get('IDENT')
            if not ident:
                return None

            lat_str = data.get('lat') or data.get('Lat') or data.get('LAT')
            lon_str = data.get('long') or data.get('Long') or data.get('LONG') or \
                      data.get('lon') or data.get('Lon') or data.get('LON')

            lat = self._parse_coordinate(lat_str) if lat_str else 0.0
            lon = self._parse_coordinate(lon_str) if lon_str else 0.0

            wpt_type = WaypointType.UNKNOWN
            type_str = data.get('type') or data.get('Type') or data.get('TYPE')
            if type_str:
                type_map = {
                    '1': WaypointType.AIRPORT,
                    '2': WaypointType.VOR,
                    '3': WaypointType.NDB,
                    '5': WaypointType.FIX,
                    '11': WaypointType.FIX,
                    'APT': WaypointType.AIRPORT,
                    'VOR': WaypointType.VOR,
                    'NDB': WaypointType.NDB,
                    'INT': WaypointType.FIX,
                    'FIX': WaypointType.FIX,
                }
                wpt_type = type_map.get(type_str, WaypointType.UNKNOWN)

            altitude = None
            alt_str = data.get('alt') or data.get('Alt') or data.get('ALT')
            if alt_str:
                try:
                    altitude = float(alt_str)
                except ValueError:
                    pass

            airway = data.get('airway') or data.get('Airway') or data.get('AIRWAY')

            return Waypoint(
                ident=ident,
                latitude=lat,
                longitude=lon,
                waypoint_type=wpt_type,
                altitude=altitude,
                airway=airway
            )

        except Exception as e:
            print(f"Error creating waypoint: {e}")
            return None

    def _parse_corte_waypoint(self, parts: list) -> Optional[Waypoint]:
        """Parse waypoint from CoRte format line."""
        try:
            ident = parts[0]

            # Try to parse coordinates from parts
            lat = 0.0
            lon = 0.0

            # Look for coordinate-like values
            for i, part in enumerate(parts[1:], 1):
                if self._looks_like_coordinate(part):
                    if lat == 0.0:
                        lat = self._parse_coordinate(part)
                    else:
                        lon = self._parse_coordinate(part)
                        break

            wpt_type = WaypointType.UNKNOWN
            if len(parts) > 1:
                type_map = {
                    'APT': WaypointType.AIRPORT,
                    'AIRPORT': WaypointType.AIRPORT,
                    'VOR': WaypointType.VOR,
                    'NDB': WaypointType.NDB,
                    'INT': WaypointType.FIX,
                    'FIX': WaypointType.FIX,
                    'WPT': WaypointType.FIX,
                }
                wpt_type = type_map.get(parts[1].upper(), WaypointType.UNKNOWN)

            airway = None
            if len(parts) > 5:
                potential_airway = parts[-1]
                if re.match(r'^[A-Z]{1,2}\d+$', potential_airway):
                    airway = potential_airway

            return Waypoint(
                ident=ident,
                latitude=lat,
                longitude=lon,
                waypoint_type=wpt_type,
                airway=airway
            )

        except Exception:
            return None

    def _looks_like_coordinate(self, s: str) -> bool:
        """Check if string looks like a coordinate."""
        # Check for N/S/E/W prefix or numeric with decimal
        if not s:
            return False
        if s[0] in 'NSEW' and len(s) > 1:
            return True
        try:
            float(s)
            return True
        except ValueError:
            return False

    def _parse_coordinate(self, coord_str: str) -> float:
        """Parse coordinate string in various formats."""
        if not coord_str:
            return 0.0

        coord_str = coord_str.strip()

        try:
            # Handle N/S/E/W prefix
            direction = 1
            if coord_str.startswith(('N', 'E')):
                direction = 1
                coord_str = coord_str[1:]
            elif coord_str.startswith(('S', 'W')):
                direction = -1
                coord_str = coord_str[1:]

            # Handle DDMM.MM or DDDMM.MM format
            if len(coord_str) >= 4 and '.' in coord_str:
                dot_pos = coord_str.index('.')
                if dot_pos >= 3:
                    # DDMM.MM or DDDMM.MM format
                    deg_len = dot_pos - 2
                    degrees = float(coord_str[:deg_len])
                    minutes = float(coord_str[deg_len:])
                    return direction * (degrees + minutes / 60)

            # Simple decimal format
            return direction * float(coord_str)

        except ValueError:
            return 0.0
