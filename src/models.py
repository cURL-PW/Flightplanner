"""Data models for flightplan elements."""
from dataclasses import dataclass, field
from enum import Enum


class WaypointType(Enum):
    """Types of waypoints in a flightplan."""
    AIRPORT = "airport"
    VOR = "vor"
    NDB = "ndb"
    FIX = "fix"
    USER = "user"
    RUNWAY = "runway"
    UNKNOWN = "unknown"


@dataclass
class Waypoint:
    """Represents a waypoint/fix in the flightplan."""
    ident: str
    latitude: float
    longitude: float
    waypoint_type: WaypointType = WaypointType.UNKNOWN
    altitude: float | None = None  # feet
    name: str | None = None
    region: str | None = None
    airway: str | None = None  # Airway used to reach this waypoint

    def __str__(self) -> str:
        return f"{self.ident} ({self.latitude:.4f}, {self.longitude:.4f})"

    @property
    def display_name(self) -> str:
        """Returns display name with type indicator."""
        type_icons = {
            WaypointType.AIRPORT: "[APT]",
            WaypointType.VOR: "[VOR]",
            WaypointType.NDB: "[NDB]",
            WaypointType.FIX: "[FIX]",
            WaypointType.USER: "[USR]",
            WaypointType.RUNWAY: "[RWY]",
            WaypointType.UNKNOWN: "[???]",
        }
        return f"{type_icons[self.waypoint_type]} {self.ident}"


@dataclass
class Flightplan:
    """Represents a complete flightplan."""
    title: str = ""
    departure: Waypoint | None = None
    destination: Waypoint | None = None
    waypoints: list[Waypoint] = field(default_factory=list)
    cruise_altitude: float | None = None  # feet
    aircraft_type: str | None = None
    source_file: str | None = None

    @property
    def departure_icao(self) -> str:
        """Returns departure airport ICAO code."""
        return self.departure.ident if self.departure else "----"

    @property
    def destination_icao(self) -> str:
        """Returns destination airport ICAO code."""
        return self.destination.ident if self.destination else "----"

    @property
    def route_string(self) -> str:
        """Returns a simple route string."""
        if not self.waypoints:
            return f"{self.departure_icao} -> {self.destination_icao}"

        wpt_idents = [w.ident for w in self.waypoints]
        return f"{self.departure_icao} {' '.join(wpt_idents)} {self.destination_icao}"

    @property
    def total_waypoints(self) -> int:
        """Returns total number of waypoints including departure and destination."""
        count = len(self.waypoints)
        if self.departure:
            count += 1
        if self.destination:
            count += 1
        return count

    def all_waypoints(self) -> list[Waypoint]:
        """Returns all waypoints including departure and destination."""
        result = []
        if self.departure:
            result.append(self.departure)
        result.extend(self.waypoints)
        if self.destination:
            result.append(self.destination)
        return result


@dataclass
class AircraftConfig:
    """Configuration for an aircraft addon."""
    name: str
    manufacturer: str
    flightplan_paths: list[str] = field(default_factory=list)
    supported_formats: list[str] = field(default_factory=list)
    icon: str | None = None

    def __str__(self) -> str:
        return f"{self.manufacturer} {self.name}"
