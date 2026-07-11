"""Exporter for .flp flightplan files (CoRte format, Fenix/Aerosoft)."""
import logging
from pathlib import Path

from ..models import Flightplan, WaypointType

logger = logging.getLogger(__name__)



_TYPE_NAMES = {
    WaypointType.AIRPORT: 'APT',
    WaypointType.VOR: 'VOR',
    WaypointType.NDB: 'NDB',
    WaypointType.FIX: 'INT',
    WaypointType.USER: 'INT',
    WaypointType.RUNWAY: 'INT',
    WaypointType.UNKNOWN: 'INT',
}


def export_flp(flightplan: Flightplan, file_path: Path) -> bool:
    """Export a flightplan as a .flp CoRte file.

    Format (matches the FlpParser CoRte reader):
        [CoRte]
        EGLL
        CPT VOR 51.2550 -0.9867 0 0 DIRECT
        ...
        LFPG

    Returns True on success.
    """
    try:
        lines = ['[CoRte]']

        if flightplan.departure:
            lines.append(flightplan.departure.ident)

        for wpt in flightplan.waypoints:
            type_name = _TYPE_NAMES.get(wpt.waypoint_type, 'INT')
            altitude = int(wpt.altitude) if wpt.altitude else 0
            airway = wpt.airway or 'DIRECT'
            lines.append(
                f"{wpt.ident} {type_name} "
                f"{wpt.latitude:.4f} {wpt.longitude:.4f} "
                f"{altitude} 0 {airway}"
            )

        if flightplan.destination:
            lines.append(flightplan.destination.ident)

        Path(file_path).write_text('\n'.join(lines) + '\n', encoding='utf-8')
        return True

    except Exception as e:
        logger.error(f"Error exporting FLP file {file_path}: {e}")
        return False
