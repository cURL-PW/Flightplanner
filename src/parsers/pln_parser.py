"""Parser for MSFS .pln flightplan files (XML format)."""
import logging
from pathlib import Path

from lxml import etree

from ..models import Flightplan, Waypoint, WaypointType
from .base import FlightplanParser

logger = logging.getLogger(__name__)



class PlnParser(FlightplanParser):
    """Parser for Microsoft Flight Simulator .pln files.

    Used by:
    - MSFS Default aircraft (B787, A320neo, etc.)
    - PMDG aircraft
    - Many third-party aircraft
    """

    @property
    def supported_extensions(self) -> list[str]:
        return ['.pln']

    def parse(self, file_path: Path) -> Flightplan | None:
        """Parse a .pln XML flightplan file."""
        try:
            tree = etree.parse(str(file_path))
            root = tree.getroot()

            # Handle namespace if present
            nsmap = root.nsmap
            ns = {'fs': nsmap.get(None, '')} if nsmap.get(None) else {}

            flightplan = Flightplan(source_file=str(file_path))

            # Parse flight plan title
            title_elem = self._find_element(root, './/Title', ns)
            if title_elem is not None and title_elem.text:
                flightplan.title = title_elem.text

            # Parse cruise altitude
            cruise_elem = self._find_element(root, './/CruisingAlt', ns)
            if cruise_elem is not None and cruise_elem.text:
                try:
                    flightplan.cruise_altitude = float(cruise_elem.text)
                except ValueError:
                    pass

            # Parse departure
            dep_elem = self._find_element(root, './/DepartureID', ns)
            dep_pos = self._find_element(root, './/DepartureLLA', ns)
            if dep_elem is not None and dep_elem.text:
                lat, lon = self._parse_lla(dep_pos)
                flightplan.departure = Waypoint(
                    ident=dep_elem.text,
                    latitude=lat,
                    longitude=lon,
                    waypoint_type=WaypointType.AIRPORT
                )

            # Parse destination
            dest_elem = self._find_element(root, './/DestinationID', ns)
            dest_pos = self._find_element(root, './/DestinationLLA', ns)
            if dest_elem is not None and dest_elem.text:
                lat, lon = self._parse_lla(dest_pos)
                flightplan.destination = Waypoint(
                    ident=dest_elem.text,
                    latitude=lat,
                    longitude=lon,
                    waypoint_type=WaypointType.AIRPORT
                )

            # Parse waypoints
            waypoints = self._find_elements(root, './/ATCWaypoint', ns)
            for wpt_elem in waypoints:
                waypoint = self._parse_waypoint(wpt_elem, ns)
                if waypoint:
                    # Skip departure and destination airports in waypoint list
                    if flightplan.departure and waypoint.ident == flightplan.departure.ident:
                        continue
                    if flightplan.destination and waypoint.ident == flightplan.destination.ident:
                        continue
                    flightplan.waypoints.append(waypoint)

            return flightplan

        except Exception as e:
            logger.error(f"Error parsing PLN file {file_path}: {e}")
            return None

    def _find_element(self, parent, xpath: str, ns: dict):
        """Find element with optional namespace."""
        if ns and ns.get('fs'):
            # Add namespace prefix
            parts = xpath.split('//')
            ns_xpath = '//'.join(p if not p or p.startswith('.') else f"fs:{p}" for p in parts)
            result = parent.find(ns_xpath, ns)
        else:
            result = parent.find(xpath)
        return result

    def _find_elements(self, parent, xpath: str, ns: dict):
        """Find all elements with optional namespace."""
        if ns and ns.get('fs'):
            parts = xpath.split('//')
            ns_xpath = '//'.join(p if not p or p.startswith('.') else f"fs:{p}" for p in parts)
            return parent.findall(ns_xpath, ns)
        return parent.findall(xpath)

    def _parse_lla(self, elem) -> tuple[float, float]:
        """Parse LLA (Latitude, Longitude, Altitude) string."""
        if elem is None or elem.text is None:
            return 0.0, 0.0

        try:
            parts = elem.text.split(',')
            if len(parts) >= 2:
                lat = self._parse_coordinate(parts[0].strip())
                lon = self._parse_coordinate(parts[1].strip())
                return lat, lon
        except Exception:
            pass
        return 0.0, 0.0

    def _parse_coordinate(self, coord_str: str) -> float:
        """Parse coordinate string in various formats."""
        coord_str = coord_str.strip()

        # Handle degree format: N47° 26' 56.04" or similar
        if '°' in coord_str or "'" in coord_str or '"' in coord_str:
            direction = 1
            if coord_str.startswith(('N', 'E')):
                direction = 1
                coord_str = coord_str[1:]
            elif coord_str.startswith(('S', 'W')):
                direction = -1
                coord_str = coord_str[1:]

            # Parse degrees, minutes, seconds
            parts = coord_str.replace('°', ' ').replace("'", ' ').replace('"', ' ').split()
            if len(parts) >= 1:
                degrees = float(parts[0])
                minutes = float(parts[1]) if len(parts) > 1 else 0
                seconds = float(parts[2]) if len(parts) > 2 else 0
                return direction * (degrees + minutes / 60 + seconds / 3600)

        # Handle simple decimal format
        return float(coord_str)

    def _parse_waypoint(self, elem, ns: dict) -> Waypoint | None:
        """Parse a single ATCWaypoint element."""
        try:
            ident_attr = elem.get('id')
            if not ident_attr:
                return None

            # Get waypoint type
            wpt_type = WaypointType.UNKNOWN
            type_elem = self._find_element(elem, './/ATCWaypointType', ns)
            if type_elem is not None and type_elem.text:
                type_map = {
                    'Airport': WaypointType.AIRPORT,
                    'VOR': WaypointType.VOR,
                    'NDB': WaypointType.NDB,
                    'Intersection': WaypointType.FIX,
                    'User': WaypointType.USER,
                    'Runway': WaypointType.RUNWAY,
                }
                wpt_type = type_map.get(type_elem.text, WaypointType.UNKNOWN)

            # Get position
            pos_elem = self._find_element(elem, './/WorldPosition', ns)
            lat, lon = self._parse_lla(pos_elem)

            # Get ICAO region
            region = None
            icao_elem = self._find_element(elem, './/ICAORegion', ns)
            if icao_elem is not None and icao_elem.text:
                region = icao_elem.text

            # Get airway
            airway = None
            airway_elem = self._find_element(elem, './/ATCAirway', ns)
            if airway_elem is not None and airway_elem.text:
                airway = airway_elem.text

            return Waypoint(
                ident=ident_attr,
                latitude=lat,
                longitude=lon,
                waypoint_type=wpt_type,
                region=region,
                airway=airway
            )

        except Exception as e:
            logger.error(f"Error parsing waypoint: {e}")
            return None
