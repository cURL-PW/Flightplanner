"""Parser for PMDG .rte flightplan files."""
import logging
from pathlib import Path

from ..models import Flightplan, Waypoint, WaypointType
from .base import FlightplanParser

logger = logging.getLogger(__name__)



class RteParser(FlightplanParser):
    """Parser for PMDG .rte files.

    Used by:
    - PMDG 737 series
    - PMDG 777 series
    - PMDG 747 series
    """

    @property
    def supported_extensions(self) -> list[str]:
        return ['.rte']

    def parse(self, file_path: Path) -> Flightplan | None:
        """Parse a PMDG .rte flightplan file."""
        try:
            with open(file_path, encoding='utf-8') as f:
                lines = f.readlines()

            flightplan = Flightplan(source_file=str(file_path))
            waypoints = []

            # PMDG RTE format varies by aircraft version
            # Common format: IDENT REGION LAT LON TYPE ALTITUDE AIRWAY
            i = 0
            while i < len(lines):
                line = lines[i].strip()
                i += 1

                if not line or line.startswith(';'):
                    continue

                # Try to parse as waypoint line
                wpt = self._parse_waypoint_line(line)
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

        except Exception as e:
            logger.error(f"Error parsing RTE file {file_path}: {e}")
            return None

    def _parse_waypoint_line(self, line: str) -> Waypoint | None:
        """Parse a waypoint from a line in the RTE file."""
        parts = line.split()
        if len(parts) < 4:
            return None

        try:
            ident = parts[0]

            # Try different parsing strategies based on line format
            lat = 0.0
            lon = 0.0
            wpt_type = WaypointType.UNKNOWN
            region = None
            airway = None
            altitude = None

            # Check if second part is a region code (2 letters)
            idx = 1
            if len(parts) > 1 and len(parts[1]) == 2 and parts[1].isalpha():
                region = parts[1]
                idx = 2

            # Parse coordinates
            if idx < len(parts):
                lat = self._parse_coordinate(parts[idx])
                idx += 1
            if idx < len(parts):
                lon = self._parse_coordinate(parts[idx])
                idx += 1

            # Parse waypoint type if present
            if idx < len(parts):
                type_str = parts[idx].upper()
                type_map = {
                    'APT': WaypointType.AIRPORT,
                    'AIRPORT': WaypointType.AIRPORT,
                    'VOR': WaypointType.VOR,
                    'VORDME': WaypointType.VOR,
                    'NDB': WaypointType.NDB,
                    'INT': WaypointType.FIX,
                    'FIX': WaypointType.FIX,
                    'WPT': WaypointType.FIX,
                    '1': WaypointType.AIRPORT,
                    '2': WaypointType.VOR,
                    '3': WaypointType.NDB,
                    '5': WaypointType.FIX,
                }
                wpt_type = type_map.get(type_str, WaypointType.UNKNOWN)
                idx += 1

            # Parse altitude if present
            if idx < len(parts):
                try:
                    altitude = float(parts[idx])
                    idx += 1
                except ValueError:
                    pass

            # Parse airway if present
            if idx < len(parts):
                potential_airway = parts[idx]
                if self._looks_like_airway(potential_airway):
                    airway = potential_airway

            return Waypoint(
                ident=ident,
                latitude=lat,
                longitude=lon,
                waypoint_type=wpt_type,
                region=region,
                altitude=altitude,
                airway=airway
            )

        except Exception as e:
            logger.error(f"Error parsing waypoint line '{line}': {e}")
            return None

    def _parse_coordinate(self, coord_str: str) -> float:
        """Parse coordinate string."""
        if not coord_str:
            return 0.0

        coord_str = coord_str.strip()

        try:
            # Handle N/S/E/W prefix
            direction = 1
            has_prefix = False
            if coord_str.startswith(('N', 'E')):
                direction = 1
                has_prefix = True
                coord_str = coord_str[1:]
            elif coord_str.startswith(('S', 'W')):
                direction = -1
                has_prefix = True
                coord_str = coord_str[1:]

            # Handle DDMM.MMM format (degrees and decimal minutes).
            # Only applies with a hemisphere prefix (e.g. N4736.2) -
            # plain values like 139.6167 are decimal degrees.
            if has_prefix and len(coord_str) >= 4 and '.' in coord_str:
                dot_pos = coord_str.index('.')
                if dot_pos >= 3:
                    deg_len = dot_pos - 2
                    degrees = float(coord_str[:deg_len])
                    minutes = float(coord_str[deg_len:])
                    return direction * (degrees + minutes / 60)

            # Try simple decimal format
            return direction * float(coord_str)

        except ValueError:
            return 0.0

    def _looks_like_airway(self, s: str) -> bool:
        """Check if string looks like an airway identifier."""
        if not s or len(s) < 2:
            return False
        # Airways are typically like A1, B2, J10, V123, UL851, etc.
        import re
        return bool(re.match(r'^[A-Z]{1,3}\d+$', s.upper()))
