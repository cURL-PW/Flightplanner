"""Tests for distance/bearing/great-circle calculations."""
import pytest

from src.flight_calculator import (
    calculate_bearing,
    calculate_route_statistics,
    great_circle_points,
    haversine_distance,
)
from src.models import Flightplan, Waypoint, WaypointType


def test_haversine_tokyo_osaka():
    # RJTT -> RJOO is roughly 220-225 NM
    dist = haversine_distance(35.5533, 139.7800, 34.7839, 135.4392)
    assert 215 < dist < 230


def test_haversine_zero_distance():
    assert haversine_distance(35.0, 139.0, 35.0, 139.0) == pytest.approx(0.0)


def test_bearing_due_east():
    bearing = calculate_bearing(0.0, 0.0, 0.0, 10.0)
    assert bearing == pytest.approx(90.0, abs=0.1)


def test_bearing_due_north():
    bearing = calculate_bearing(0.0, 0.0, 10.0, 0.0)
    assert bearing == pytest.approx(0.0, abs=0.1)


def test_great_circle_endpoints():
    pts = great_circle_points(35.55, 139.78, 34.78, 135.44, 16)
    assert len(pts) == 17
    assert pts[0] == pytest.approx((35.55, 139.78))
    assert pts[-1] == pytest.approx((34.78, 135.44))


def test_great_circle_antimeridian_unwrap():
    # Tokyo -> Los Angeles crosses the antimeridian
    pts = great_circle_points(35.55, 139.78, 33.94, -118.41, 32)
    lons = [lon for _, lon in pts]
    max_jump = max(abs(b - a) for a, b in zip(lons, lons[1:], strict=False))
    assert max_jump < 180, "polyline must not jump across the antimeridian"


def test_great_circle_identical_points():
    pts = great_circle_points(35.0, 139.0, 35.0, 139.0)
    assert len(pts) == 2


def _make_flightplan() -> Flightplan:
    dep = Waypoint("RJTT", 35.5533, 139.7800, WaypointType.AIRPORT)
    dest = Waypoint("RJOO", 34.7839, 135.4392, WaypointType.AIRPORT)
    mid = Waypoint("SPENS", 35.2500, 139.0833, WaypointType.FIX)
    return Flightplan(departure=dep, destination=dest, waypoints=[mid])


def test_route_statistics():
    stats = calculate_route_statistics(_make_flightplan(), cruise_speed_knots=450)
    assert len(stats.legs) == 2
    assert stats.total_distance_nm > 200
    assert stats.estimated_flight_time_minutes is not None
    assert ":" in stats.formatted_time


def test_route_statistics_skips_invalid_coords():
    fp = _make_flightplan()
    fp.waypoints.append(Waypoint("BROKEN", 0.0, 0.0, WaypointType.FIX))
    stats = calculate_route_statistics(fp)
    # Legs touching the (0,0) waypoint are skipped
    assert all(
        leg.from_waypoint.ident != "BROKEN" and leg.to_waypoint.ident != "BROKEN"
        for leg in stats.legs
    )
