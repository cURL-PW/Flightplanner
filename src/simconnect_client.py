"""MSFS SimConnect client for real-time aircraft position tracking.

Uses the Python-SimConnect package (pip install SimConnect).
The package is optional: if it is not installed or MSFS is not
running, the client reports itself as unavailable and the rest of
the application keeps working normally.
"""
from dataclasses import dataclass, field

from PyQt6.QtCore import QObject, QTimer, pyqtSignal

# Optional dependency - only available on Windows with MSFS installed
try:
    from SimConnect import AircraftRequests, SimConnect
    SIMCONNECT_AVAILABLE = True
except ImportError:
    SIMCONNECT_AVAILABLE = False


@dataclass
class AircraftState:
    """Snapshot of the user aircraft state from the simulator."""
    latitude: float = 0.0
    longitude: float = 0.0
    altitude_ft: float = 0.0
    heading_deg: float = 0.0
    ground_speed_kts: float = 0.0
    vertical_speed_fpm: float = 0.0
    on_ground: bool = True

    @property
    def is_valid(self) -> bool:
        """Position (0, 0) means SimConnect returned no data yet."""
        return not (self.latitude == 0.0 and self.longitude == 0.0)


@dataclass
class FlightTrack:
    """Recorded flight track (list of positions actually flown)."""
    points: list[tuple[float, float]] = field(default_factory=list)
    min_distance_deg: float = 0.001  # ~0.06 NM between recorded points

    def add_point(self, lat: float, lon: float) -> bool:
        """Add a point if it moved far enough from the last one."""
        if self.points:
            last_lat, last_lon = self.points[-1]
            if (abs(lat - last_lat) < self.min_distance_deg and
                    abs(lon - last_lon) < self.min_distance_deg):
                return False
        self.points.append((lat, lon))
        return True

    def clear(self):
        self.points.clear()


class SimConnectClient(QObject):
    """Polls MSFS via SimConnect and emits aircraft state updates.

    Signals:
        state_updated(AircraftState): emitted on every successful poll
        connection_changed(bool, str): emitted when connection state changes
                                       (connected flag, status message)
    """

    state_updated = pyqtSignal(object)
    connection_changed = pyqtSignal(bool, str)

    POLL_INTERVAL_MS = 1000

    def __init__(self, parent=None):
        super().__init__(parent)
        self._sm: SimConnect | None = None
        self._requests: AircraftRequests | None = None
        self._connected = False
        self.track = FlightTrack()
        self.last_state: AircraftState | None = None

        self._timer = QTimer(self)
        self._timer.setInterval(self.POLL_INTERVAL_MS)
        self._timer.timeout.connect(self._poll)

    @property
    def is_available(self) -> bool:
        """Whether the SimConnect package is installed."""
        return SIMCONNECT_AVAILABLE

    @property
    def is_connected(self) -> bool:
        return self._connected

    def connect_to_sim(self) -> bool:
        """Attempt to connect to a running MSFS instance."""
        if not SIMCONNECT_AVAILABLE:
            self.connection_changed.emit(
                False,
                "SimConnectパッケージが未インストールです (pip install SimConnect)"
            )
            return False

        try:
            self._sm = SimConnect()
            self._requests = AircraftRequests(self._sm, _time=500)
            self._connected = True
            self.track.clear()
            self._timer.start()
            self.connection_changed.emit(True, "MSFSに接続しました")
            return True
        except Exception as e:
            self._sm = None
            self._requests = None
            self._connected = False
            self.connection_changed.emit(
                False,
                f"MSFSに接続できません（シミュレータ起動中ですか？）: {e}"
            )
            return False

    def disconnect_from_sim(self):
        """Disconnect from the simulator."""
        self._timer.stop()
        if self._sm:
            try:
                self._sm.exit()
            except Exception:
                pass
        self._sm = None
        self._requests = None
        if self._connected:
            self._connected = False
            self.connection_changed.emit(False, "MSFSから切断しました")

    def clear_track(self):
        """Clear the recorded flight track."""
        self.track.clear()

    def _poll(self):
        """Poll aircraft state from the simulator."""
        if not self._requests:
            return

        try:
            state = AircraftState(
                latitude=self._get_float("PLANE_LATITUDE"),
                longitude=self._get_float("PLANE_LONGITUDE"),
                altitude_ft=self._get_float("PLANE_ALTITUDE"),
                heading_deg=self._get_float("PLANE_HEADING_DEGREES_TRUE"),
                ground_speed_kts=self._get_float("GROUND_VELOCITY"),
                vertical_speed_fpm=self._get_float("VERTICAL_SPEED") * 60,
                on_ground=bool(self._get_float("SIM_ON_GROUND")),
            )
        except Exception:
            # Simulator was probably closed
            self.disconnect_from_sim()
            self.connection_changed.emit(False, "MSFSとの接続が失われました")
            return

        if state.is_valid:
            self.track.add_point(state.latitude, state.longitude)
            self.last_state = state
            self.state_updated.emit(state)

    def _get_float(self, name: str) -> float:
        """Fetch a single SimVar as float (0.0 on failure)."""
        try:
            value = self._requests.get(name)
            return float(value) if value is not None else 0.0
        except Exception:
            return 0.0
