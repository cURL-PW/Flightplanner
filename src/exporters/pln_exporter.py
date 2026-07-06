"""Exporter for MSFS .pln flightplan files (XML format)."""
from pathlib import Path
from xml.sax.saxutils import escape

from ..models import Flightplan, Waypoint, WaypointType


_TYPE_NAMES = {
    WaypointType.AIRPORT: 'Airport',
    WaypointType.VOR: 'VOR',
    WaypointType.NDB: 'NDB',
    WaypointType.FIX: 'Intersection',
    WaypointType.USER: 'User',
    WaypointType.RUNWAY: 'Runway',
    WaypointType.UNKNOWN: 'Intersection',
}


def _format_dms(value: float, positive: str, negative: str) -> str:
    """Format a decimal coordinate as MSFS DMS: N35° 33' 12.00" """
    hemi = positive if value >= 0 else negative
    value = abs(value)
    degrees = int(value)
    minutes_f = (value - degrees) * 60
    minutes = int(minutes_f)
    seconds = (minutes_f - minutes) * 60
    return f"{hemi}{degrees}° {minutes}' {seconds:.2f}\""


def _format_lla(lat: float, lon: float, alt_ft: float = 0.0) -> str:
    """Format an LLA string: N35° 33' 12.00",E139° 46' 48.00",+000035.00"""
    lat_str = _format_dms(lat, 'N', 'S')
    lon_str = _format_dms(lon, 'E', 'W')
    return f"{lat_str},{lon_str},{alt_ft:+010.2f}"


def _waypoint_xml(wpt: Waypoint, indent: str = '        ') -> str:
    """Generate an ATCWaypoint XML block."""
    lines = [f'{indent}<ATCWaypoint id="{escape(wpt.ident)}">']
    lines.append(
        f'{indent}    <ATCWaypointType>'
        f'{_TYPE_NAMES.get(wpt.waypoint_type, "Intersection")}'
        f'</ATCWaypointType>'
    )
    alt = wpt.altitude or 0.0
    lines.append(
        f'{indent}    <WorldPosition>'
        f'{_format_lla(wpt.latitude, wpt.longitude, alt)}'
        f'</WorldPosition>'
    )
    lines.append(f'{indent}    <ICAOIdent>{escape(wpt.ident)}</ICAOIdent>')
    if wpt.region:
        lines.append(f'{indent}    <ICAORegion>{escape(wpt.region)}</ICAORegion>')
    if wpt.airway:
        lines.append(f'{indent}    <ATCAirway>{escape(wpt.airway)}</ATCAirway>')
    lines.append(f'{indent}</ATCWaypoint>')
    return '\n'.join(lines)


def export_pln(flightplan: Flightplan, file_path: Path) -> bool:
    """Export a flightplan as an MSFS .pln XML file.

    Returns True on success.
    """
    try:
        dep = flightplan.departure
        dest = flightplan.destination
        title = flightplan.title or (
            f"{flightplan.departure_icao} to {flightplan.destination_icao}"
        )
        cruise = flightplan.cruise_altitude or 35000

        parts = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<SimBase.Document Type="AceXML" version="1,0">',
            '    <Descr>AceXML Document</Descr>',
            '    <FlightPlan.FlightPlan>',
            f'        <Title>{escape(title)}</Title>',
            '        <FPType>IFR</FPType>',
            '        <RouteType>HighAlt</RouteType>',
            f'        <CruisingAlt>{int(cruise)}</CruisingAlt>',
        ]

        if dep:
            parts.append(f'        <DepartureID>{escape(dep.ident)}</DepartureID>')
            parts.append(
                f'        <DepartureLLA>'
                f'{_format_lla(dep.latitude, dep.longitude, dep.altitude or 0)}'
                f'</DepartureLLA>'
            )
        if dest:
            parts.append(f'        <DestinationID>{escape(dest.ident)}</DestinationID>')
            parts.append(
                f'        <DestinationLLA>'
                f'{_format_lla(dest.latitude, dest.longitude, dest.altitude or 0)}'
                f'</DestinationLLA>'
            )

        parts.append(f'        <Descr>{escape(title)}</Descr>')

        for wpt in flightplan.all_waypoints():
            parts.append(_waypoint_xml(wpt))

        parts.append('    </FlightPlan.FlightPlan>')
        parts.append('</SimBase.Document>')

        Path(file_path).write_text('\n'.join(parts) + '\n', encoding='utf-8')
        return True

    except Exception as e:
        print(f"Error exporting PLN file {file_path}: {e}")
        return False
