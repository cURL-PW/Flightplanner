"""Exporter for PMDG .rte flightplan files."""
from pathlib import Path

from ..models import Flightplan, WaypointType


_TYPE_NAMES = {
    WaypointType.AIRPORT: 'APT',
    WaypointType.VOR: 'VOR',
    WaypointType.NDB: 'NDB',
    WaypointType.FIX: 'INT',
    WaypointType.USER: 'INT',
    WaypointType.RUNWAY: 'INT',
    WaypointType.UNKNOWN: 'INT',
}


def export_rte(flightplan: Flightplan, file_path: Path) -> bool:
    """Export a flightplan as a PMDG-style .rte text file.

    Format (matches the RteParser reader):
        IDENT REGION LAT LON TYPE ALTITUDE AIRWAY

    Returns True on success.
    """
    try:
        lines = []
        for wpt in flightplan.all_waypoints():
            region = wpt.region if wpt.region and len(wpt.region) == 2 else 'ZZ'
            type_name = _TYPE_NAMES.get(wpt.waypoint_type, 'INT')
            altitude = int(wpt.altitude) if wpt.altitude else 0
            airway = wpt.airway or 'DIRECT'
            lines.append(
                f"{wpt.ident} {region} "
                f"{wpt.latitude:.4f} {wpt.longitude:.4f} "
                f"{type_name} {altitude} {airway}"
            )

        Path(file_path).write_text('\n'.join(lines) + '\n', encoding='utf-8')
        return True

    except Exception as e:
        print(f"Error exporting RTE file {file_path}: {e}")
        return False
