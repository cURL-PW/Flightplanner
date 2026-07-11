"""Navigation database for airports, VORs, NDBs, and fixes.

Provides coordinate lookup for waypoints with missing position data.
Supports loading from:
- Built-in database of major airports/navaids
- X-Plane earth_nav.dat format
- Custom CSV files
"""
import csv
import logging
from dataclasses import dataclass
from pathlib import Path

from .models import WaypointType

logger = logging.getLogger(__name__)



@dataclass
class NavaidRecord:
    """Record for a navaid in the database."""
    ident: str
    name: str
    latitude: float
    longitude: float
    navaid_type: WaypointType
    frequency: float | None = None  # MHz for VOR, kHz for NDB
    region: str | None = None
    elevation: float | None = None  # feet

    @property
    def type_code(self) -> str:
        """Returns short type code."""
        type_codes = {
            WaypointType.AIRPORT: 'APT',
            WaypointType.VOR: 'VOR',
            WaypointType.NDB: 'NDB',
            WaypointType.FIX: 'FIX',
        }
        return type_codes.get(self.navaid_type, '???')


class NavigationDatabase:
    """Navigation database for coordinate lookups."""

    def __init__(self):
        self._airports: dict[str, NavaidRecord] = {}
        self._vors: dict[str, list[NavaidRecord]] = {}  # Multiple VORs can have same ident
        self._ndbs: dict[str, list[NavaidRecord]] = {}
        self._fixes: dict[str, list[NavaidRecord]] = {}

        # Load built-in data
        self._load_builtin_data()

    def _load_builtin_data(self):
        """Load built-in airport and navaid data."""
        # Major world airports
        airports_data = [
            # Japan
            ("RJTT", "Tokyo Haneda", 35.5494, 139.7798),
            ("RJAA", "Tokyo Narita", 35.7647, 140.3864),
            ("RJOO", "Osaka Itami", 34.7855, 135.4385),
            ("RJBB", "Osaka Kansai", 34.4272, 135.2440),
            ("RJCC", "Sapporo New Chitose", 42.7752, 141.6925),
            ("RJFF", "Fukuoka", 33.5859, 130.4511),
            ("RJGG", "Nagoya Chubu", 34.8584, 136.8049),
            ("RJSS", "Sendai", 38.1397, 140.9170),
            ("RJFK", "Kagoshima", 31.8034, 130.7194),
            ("ROAH", "Naha Okinawa", 26.1958, 127.6459),

            # USA
            ("KJFK", "New York JFK", 40.6398, -73.7789),
            ("KLAX", "Los Angeles", 33.9425, -118.4081),
            ("KORD", "Chicago O'Hare", 41.9742, -87.9073),
            ("KATL", "Atlanta", 33.6407, -84.4277),
            ("KDFW", "Dallas Fort Worth", 32.8998, -97.0403),
            ("KDEN", "Denver", 39.8561, -104.6737),
            ("KSFO", "San Francisco", 37.6213, -122.3790),
            ("KLAS", "Las Vegas", 36.0840, -115.1537),
            ("KMIA", "Miami", 25.7959, -80.2870),
            ("KSEA", "Seattle", 47.4502, -122.3088),
            ("KBOS", "Boston", 42.3656, -71.0096),
            ("KEWR", "Newark", 40.6895, -74.1745),
            ("KLGA", "New York LaGuardia", 40.7769, -73.8740),
            ("KPHX", "Phoenix", 33.4373, -112.0078),
            ("KIAH", "Houston", 29.9902, -95.3368),

            # Europe
            ("EGLL", "London Heathrow", 51.4775, -0.4614),
            ("EGKK", "London Gatwick", 51.1537, -0.1821),
            ("EGLC", "London City", 51.5053, 0.0553),
            ("LFPG", "Paris CDG", 49.0097, 2.5479),
            ("LFPO", "Paris Orly", 48.7262, 2.3652),
            ("EDDF", "Frankfurt", 50.0333, 8.5706),
            ("EDDM", "Munich", 48.3539, 11.7861),
            ("EHAM", "Amsterdam", 52.3086, 4.7639),
            ("LEMD", "Madrid", 40.4936, -3.5668),
            ("LEBL", "Barcelona", 41.2971, 2.0785),
            ("LIRF", "Rome Fiumicino", 41.8003, 12.2389),
            ("LSZH", "Zurich", 47.4647, 8.5492),
            ("LOWW", "Vienna", 48.1103, 16.5697),
            ("EKCH", "Copenhagen", 55.6180, 12.6561),
            ("ENGM", "Oslo", 60.1939, 11.1004),
            ("ESSA", "Stockholm Arlanda", 59.6519, 17.9186),
            ("LFML", "Marseille", 43.4393, 5.2214),
            ("EGCC", "Manchester", 53.3537, -2.2750),
            ("EIDW", "Dublin", 53.4213, -6.2701),
            ("LPPT", "Lisbon", 38.7756, -9.1354),

            # Asia
            ("VHHH", "Hong Kong", 22.3080, 113.9185),
            ("WSSS", "Singapore Changi", 1.3644, 103.9915),
            ("RKSI", "Seoul Incheon", 37.4691, 126.4505),
            ("RCTP", "Taipei Taoyuan", 25.0777, 121.2330),
            ("ZBAA", "Beijing Capital", 40.0799, 116.6031),
            ("ZSPD", "Shanghai Pudong", 31.1434, 121.8052),
            ("VTBS", "Bangkok Suvarnabhumi", 13.6900, 100.7501),
            ("WMKK", "Kuala Lumpur", 2.7456, 101.7099),
            ("RPLL", "Manila", 14.5086, 121.0198),
            ("VIDP", "Delhi", 28.5665, 77.1031),
            ("VABB", "Mumbai", 19.0896, 72.8656),

            # Middle East
            ("OMDB", "Dubai", 25.2528, 55.3644),
            ("OERK", "Riyadh", 24.9576, 46.6988),
            ("OEJN", "Jeddah", 21.6796, 39.1565),
            ("OTBD", "Doha", 25.2731, 51.6081),
            ("OBBI", "Bahrain", 26.2708, 50.6336),
            ("LLBG", "Tel Aviv", 32.0114, 34.8867),

            # Oceania
            ("YSSY", "Sydney", -33.9461, 151.1772),
            ("YMML", "Melbourne", -37.6690, 144.8410),
            ("NZAA", "Auckland", -37.0082, 174.7850),
            ("NZWN", "Wellington", -41.3272, 174.8053),

            # South America
            ("SBGR", "Sao Paulo Guarulhos", -23.4356, -46.4731),
            ("SCEL", "Santiago", -33.3930, -70.7858),
            ("SAEZ", "Buenos Aires Ezeiza", -34.8222, -58.5358),
            ("SKBO", "Bogota", 4.7016, -74.1469),
            ("SPJC", "Lima", -12.0219, -77.1143),

            # Africa
            ("FACT", "Cape Town", -33.9649, 18.6017),
            ("FAOR", "Johannesburg", -26.1392, 28.2460),
            ("HECA", "Cairo", 30.1219, 31.4056),
            ("GMMN", "Casablanca", 33.3675, -7.5898),
        ]

        for icao, name, lat, lon in airports_data:
            self._airports[icao] = NavaidRecord(
                ident=icao,
                name=name,
                latitude=lat,
                longitude=lon,
                navaid_type=WaypointType.AIRPORT
            )

        # Major VORs
        vors_data = [
            # Japan
            ("HME", "Haneda", 35.5500, 139.7833, 112.2),
            ("TLE", "Tokyo", 35.7667, 139.3500, 114.5),
            ("XAC", "Narita", 35.8000, 140.3333, 115.4),
            ("KWE", "Kawasaki", 35.5167, 139.6833, 117.7),
            ("MYE", "Miyakejima", 34.0667, 139.5500, 113.6),
            ("YOE", "Yaizu", 34.8667, 138.3333, 113.2),
            ("XMC", "Kansai", 34.4333, 135.2333, 117.55),
            ("KNE", "Komatsu", 36.3833, 136.4000, 114.5),
            ("CHE", "New Chitose", 42.8000, 141.6833, 112.3),

            # USA (Major)
            ("JFK", "Kennedy", 40.6500, -73.7833, 115.9),
            ("LGA", "LaGuardia", 40.7833, -73.8667, 113.1),
            ("EWR", "Newark", 40.7000, -74.1667, 108.2),
            ("LAX", "Los Angeles", 33.9333, -118.4333, 113.6),
            ("ORD", "O'Hare", 41.9833, -87.9000, 113.9),
            ("ATL", "Atlanta", 33.6333, -84.4333, 116.9),
            ("DFW", "Dallas", 32.8500, -97.0333, 117.0),
            ("DEN", "Denver", 39.8500, -104.6667, 117.9),
            ("SFO", "San Francisco", 37.6167, -122.3833, 115.8),
            ("SEA", "Seattle", 47.4333, -122.3000, 116.8),
            ("MIA", "Miami", 25.7833, -80.2667, 115.9),

            # Europe (Major)
            ("LON", "London", 51.4833, -0.4500, 113.6),
            ("BPK", "Brookmans Park", 51.7500, -0.1000, 117.5),
            ("DVR", "Dover", 51.1500, 1.3500, 114.95),
            ("CGN", "Paris", 49.0167, 2.5333, 117.3),
            ("FFM", "Frankfurt", 50.0500, 8.5833, 114.2),
            ("MUN", "Munich", 48.3500, 11.7833, 112.3),
            ("AMS", "Amsterdam", 52.3000, 4.7500, 114.1),
            ("SPL", "Schiphol", 52.3333, 4.7500, 108.4),

            # Asia
            ("HKG", "Hong Kong", 22.3167, 113.9333, 113.3),
            ("SIN", "Singapore", 1.3500, 103.9833, 115.1),
            ("ICN", "Incheon", 37.4500, 126.4500, 115.4),
            ("TPE", "Taipei", 25.0667, 121.2167, 117.1),
        ]

        for ident, name, lat, lon, freq in vors_data:
            record = NavaidRecord(
                ident=ident,
                name=name,
                latitude=lat,
                longitude=lon,
                navaid_type=WaypointType.VOR,
                frequency=freq
            )
            if ident not in self._vors:
                self._vors[ident] = []
            self._vors[ident].append(record)

        # Common fixes (intersections)
        fixes_data = [
            # Japan
            ("CLARK", 35.4667, 139.6167),
            ("SPENS", 35.2167, 139.2500),
            ("OTONE", 35.0000, 138.8333),
            ("SUZKA", 34.8667, 136.5833),
            ("KODAI", 34.8333, 135.7500),
            ("YUBAR", 43.2833, 141.9000),
            ("TOHME", 38.8667, 140.5833),
            ("KANBE", 34.7167, 135.0333),

            # USA
            ("MERIT", 40.5833, -73.8333),
            ("ROBER", 40.4167, -73.9500),
            ("CAMRN", 40.1667, -74.3333),
            ("DIXIE", 39.7167, -74.6667),
            ("SEAGR", 38.8333, -75.1667),

            # Europe
            ("LOGAN", 51.1000, -0.3667),
            ("TIMBA", 51.3000, -0.0833),
            ("HARDY", 50.5167, 0.0333),
            ("BOGNA", 50.8500, -0.4500),
            ("KONAN", 50.3333, 0.4833),
        ]

        for ident, lat, lon in fixes_data:
            record = NavaidRecord(
                ident=ident,
                name=ident,
                latitude=lat,
                longitude=lon,
                navaid_type=WaypointType.FIX
            )
            if ident not in self._fixes:
                self._fixes[ident] = []
            self._fixes[ident].append(record)

    def lookup(
        self,
        ident: str,
        navaid_type: WaypointType | None = None,
        near_lat: float | None = None,
        near_lon: float | None = None
    ) -> NavaidRecord | None:
        """
        Look up a navaid by identifier.

        Args:
            ident: Navaid identifier (e.g., "RJTT", "HME", "CLARK")
            navaid_type: Optional type filter
            near_lat, near_lon: Optional coordinates to find nearest match

        Returns:
            NavaidRecord if found, None otherwise
        """
        ident = ident.upper().strip()
        candidates = []

        # Check airports first if no type specified or type is airport
        if navaid_type is None or navaid_type == WaypointType.AIRPORT:
            if ident in self._airports:
                candidates.append(self._airports[ident])

        # Check VORs
        if navaid_type is None or navaid_type == WaypointType.VOR:
            if ident in self._vors:
                candidates.extend(self._vors[ident])

        # Check NDBs
        if navaid_type is None or navaid_type == WaypointType.NDB:
            if ident in self._ndbs:
                candidates.extend(self._ndbs[ident])

        # Check fixes
        if navaid_type is None or navaid_type == WaypointType.FIX:
            if ident in self._fixes:
                candidates.extend(self._fixes[ident])

        if not candidates:
            return None

        # If only one candidate or no position preference, return first
        if len(candidates) == 1 or near_lat is None or near_lon is None:
            return candidates[0]

        # Find nearest candidate
        def distance_sq(rec: NavaidRecord) -> float:
            return (rec.latitude - near_lat) ** 2 + (rec.longitude - near_lon) ** 2

        return min(candidates, key=distance_sq)

    def lookup_airport(self, icao: str) -> NavaidRecord | None:
        """Look up an airport by ICAO code."""
        return self._airports.get(icao.upper().strip())

    def get_coordinates(
        self,
        ident: str,
        navaid_type: WaypointType | None = None,
        near_lat: float | None = None,
        near_lon: float | None = None
    ) -> tuple[float, float] | None:
        """
        Get coordinates for a navaid.

        Returns:
            Tuple of (latitude, longitude) if found, None otherwise
        """
        record = self.lookup(ident, navaid_type, near_lat, near_lon)
        if record:
            return (record.latitude, record.longitude)
        return None

    def load_airports_csv(self, file_path: Path) -> int:
        """
        Load airports from a CSV file.

        Expected columns: icao,name,latitude,longitude

        Returns:
            Number of airports loaded
        """
        count = 0
        try:
            with open(file_path, encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    icao = row.get('icao', '').strip().upper()
                    if not icao:
                        continue

                    try:
                        lat = float(row.get('latitude', 0))
                        lon = float(row.get('longitude', 0))
                    except ValueError:
                        continue

                    self._airports[icao] = NavaidRecord(
                        ident=icao,
                        name=row.get('name', icao),
                        latitude=lat,
                        longitude=lon,
                        navaid_type=WaypointType.AIRPORT
                    )
                    count += 1
        except Exception as e:
            logger.error(f"Error loading airports CSV: {e}")

        return count

    def load_xplane_earthnav(self, file_path: Path) -> int:
        """
        Load navaids from X-Plane earth_nav.dat file.

        Returns:
            Number of navaids loaded
        """
        count = 0
        try:
            with open(file_path, encoding='latin-1') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('I') or line.startswith('99'):
                        continue

                    parts = line.split()
                    if len(parts) < 9:
                        continue

                    try:
                        row_type = int(parts[0])
                        lat = float(parts[1])
                        lon = float(parts[2])
                        freq = float(parts[4]) / 100.0 if row_type in (2, 3) else None
                        ident = parts[7]
                        name = ' '.join(parts[8:]) if len(parts) > 8 else ident
                    except (ValueError, IndexError):
                        continue

                    # Type mapping: 2=NDB, 3=VOR, 11=Fix
                    if row_type == 2:  # NDB
                        record = NavaidRecord(
                            ident=ident,
                            name=name,
                            latitude=lat,
                            longitude=lon,
                            navaid_type=WaypointType.NDB,
                            frequency=freq
                        )
                        if ident not in self._ndbs:
                            self._ndbs[ident] = []
                        self._ndbs[ident].append(record)
                        count += 1
                    elif row_type == 3:  # VOR
                        record = NavaidRecord(
                            ident=ident,
                            name=name,
                            latitude=lat,
                            longitude=lon,
                            navaid_type=WaypointType.VOR,
                            frequency=freq
                        )
                        if ident not in self._vors:
                            self._vors[ident] = []
                        self._vors[ident].append(record)
                        count += 1
                    elif row_type == 11:  # Fix
                        record = NavaidRecord(
                            ident=ident,
                            name=name,
                            latitude=lat,
                            longitude=lon,
                            navaid_type=WaypointType.FIX
                        )
                        if ident not in self._fixes:
                            self._fixes[ident] = []
                        self._fixes[ident].append(record)
                        count += 1

        except Exception as e:
            logger.error(f"Error loading X-Plane nav data: {e}")

        return count

    @property
    def airport_count(self) -> int:
        """Returns number of airports in database."""
        return len(self._airports)

    @property
    def vor_count(self) -> int:
        """Returns number of VORs in database."""
        return sum(len(v) for v in self._vors.values())

    @property
    def ndb_count(self) -> int:
        """Returns number of NDBs in database."""
        return sum(len(v) for v in self._ndbs.values())

    @property
    def fix_count(self) -> int:
        """Returns number of fixes in database."""
        return sum(len(v) for v in self._fixes.values())

    @property
    def total_count(self) -> int:
        """Returns total number of navaids in database."""
        return self.airport_count + self.vor_count + self.ndb_count + self.fix_count


# Global database instance
_global_db: NavigationDatabase | None = None


def get_navdata() -> NavigationDatabase:
    """Get the global navigation database instance."""
    global _global_db
    if _global_db is None:
        _global_db = NavigationDatabase()
    return _global_db
