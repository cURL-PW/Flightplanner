"""Flight calculation utilities for distance, time, and fuel estimation."""
import math
from dataclasses import dataclass
from typing import Optional

from .models import Waypoint, Flightplan


# Earth's radius in nautical miles
EARTH_RADIUS_NM = 3440.065


@dataclass
class LegInfo:
    """Information about a single leg between two waypoints."""
    from_waypoint: Waypoint
    to_waypoint: Waypoint
    distance_nm: float
    bearing: float  # degrees true
    cumulative_distance_nm: float
    estimated_time_minutes: Optional[float] = None


@dataclass
class RouteStatistics:
    """Statistics for a complete route."""
    total_distance_nm: float
    legs: list[LegInfo]
    estimated_flight_time_minutes: Optional[float] = None
    cruise_speed_knots: Optional[float] = None

    @property
    def total_distance_km(self) -> float:
        """Returns total distance in kilometers."""
        return self.total_distance_nm * 1.852

    @property
    def total_distance_sm(self) -> float:
        """Returns total distance in statute miles."""
        return self.total_distance_nm * 1.15078

    @property
    def formatted_time(self) -> str:
        """Returns formatted flight time (HH:MM)."""
        if self.estimated_flight_time_minutes is None:
            return "--:--"
        hours = int(self.estimated_flight_time_minutes // 60)
        minutes = int(self.estimated_flight_time_minutes % 60)
        return f"{hours:02d}:{minutes:02d}"


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great-circle distance between two points using Haversine formula.

    Args:
        lat1, lon1: Coordinates of the first point in decimal degrees
        lat2, lon2: Coordinates of the second point in decimal degrees

    Returns:
        Distance in nautical miles
    """
    # Convert to radians
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)

    # Haversine formula
    a = (math.sin(delta_lat / 2) ** 2 +
         math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return EARTH_RADIUS_NM * c


def calculate_bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the initial bearing from point 1 to point 2.

    Args:
        lat1, lon1: Coordinates of the first point in decimal degrees
        lat2, lon2: Coordinates of the second point in decimal degrees

    Returns:
        Bearing in degrees (0-360)
    """
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lon = math.radians(lon2 - lon1)

    x = math.sin(delta_lon) * math.cos(lat2_rad)
    y = (math.cos(lat1_rad) * math.sin(lat2_rad) -
         math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(delta_lon))

    bearing = math.degrees(math.atan2(x, y))
    return (bearing + 360) % 360


def calculate_route_statistics(
    flightplan: Flightplan,
    cruise_speed_knots: Optional[float] = None
) -> RouteStatistics:
    """
    Calculate statistics for a complete flightplan.

    Args:
        flightplan: The flightplan to analyze
        cruise_speed_knots: Optional cruise speed for time estimation

    Returns:
        RouteStatistics with distance and time information
    """
    waypoints = flightplan.all_waypoints()
    legs: list[LegInfo] = []
    total_distance = 0.0

    for i in range(len(waypoints) - 1):
        from_wpt = waypoints[i]
        to_wpt = waypoints[i + 1]

        # Skip waypoints with invalid coordinates
        if (from_wpt.latitude == 0 and from_wpt.longitude == 0) or \
           (to_wpt.latitude == 0 and to_wpt.longitude == 0):
            continue

        distance = haversine_distance(
            from_wpt.latitude, from_wpt.longitude,
            to_wpt.latitude, to_wpt.longitude
        )
        bearing = calculate_bearing(
            from_wpt.latitude, from_wpt.longitude,
            to_wpt.latitude, to_wpt.longitude
        )

        total_distance += distance

        # Calculate estimated time for this leg
        leg_time = None
        if cruise_speed_knots and cruise_speed_knots > 0:
            leg_time = (distance / cruise_speed_knots) * 60  # minutes

        legs.append(LegInfo(
            from_waypoint=from_wpt,
            to_waypoint=to_wpt,
            distance_nm=distance,
            bearing=bearing,
            cumulative_distance_nm=total_distance,
            estimated_time_minutes=leg_time
        ))

    # Calculate total flight time
    total_time = None
    if cruise_speed_knots and cruise_speed_knots > 0:
        total_time = (total_distance / cruise_speed_knots) * 60  # minutes

    return RouteStatistics(
        total_distance_nm=total_distance,
        legs=legs,
        estimated_flight_time_minutes=total_time,
        cruise_speed_knots=cruise_speed_knots
    )


def estimate_fuel_consumption(
    distance_nm: float,
    fuel_flow_per_hour: float,
    cruise_speed_knots: float,
    reserve_minutes: float = 45.0
) -> dict:
    """
    Estimate fuel consumption for a flight.

    Args:
        distance_nm: Distance in nautical miles
        fuel_flow_per_hour: Fuel flow in units per hour (e.g., lbs/hr or kg/hr)
        cruise_speed_knots: Cruise speed in knots
        reserve_minutes: Reserve fuel in minutes (default 45 min)

    Returns:
        Dictionary with fuel estimates
    """
    if cruise_speed_knots <= 0:
        return {}

    flight_time_hours = distance_nm / cruise_speed_knots
    trip_fuel = flight_time_hours * fuel_flow_per_hour
    reserve_fuel = (reserve_minutes / 60) * fuel_flow_per_hour
    total_fuel = trip_fuel + reserve_fuel

    return {
        'trip_fuel': trip_fuel,
        'reserve_fuel': reserve_fuel,
        'total_fuel': total_fuel,
        'flight_time_hours': flight_time_hours
    }


# Common aircraft cruise speeds (approximate, in knots TAS)
AIRCRAFT_SPEEDS = {
    # Airliners
    'B737': 450,
    'B738': 450,
    'B739': 450,
    'B747': 490,
    'B777': 490,
    'B787': 490,
    'A319': 450,
    'A320': 450,
    'A321': 450,
    'A330': 470,
    'A340': 470,
    'A350': 490,
    'A380': 490,
    'CRJ7': 420,
    'CRJ9': 420,
    'E170': 430,
    'E190': 430,
    # General Aviation
    'C172': 120,
    'C182': 140,
    'C208': 180,
    'BE36': 170,
    'SR22': 180,
    'TBM9': 320,
    'PC12': 280,
    # Business Jets
    'C525': 380,
    'C680': 450,
    'CL35': 460,
    'GLF5': 480,
}


def get_suggested_speed(aircraft_type: Optional[str]) -> Optional[float]:
    """
    Get suggested cruise speed for an aircraft type.

    Args:
        aircraft_type: ICAO aircraft type code

    Returns:
        Suggested cruise speed in knots, or None if unknown
    """
    if not aircraft_type:
        return None

    # Try exact match
    if aircraft_type.upper() in AIRCRAFT_SPEEDS:
        return AIRCRAFT_SPEEDS[aircraft_type.upper()]

    # Try partial match
    for code, speed in AIRCRAFT_SPEEDS.items():
        if code in aircraft_type.upper() or aircraft_type.upper() in code:
            return speed

    return None
