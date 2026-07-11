"""Main application window for MSFS Flightplan Viewer."""
from pathlib import Path

from PyQt6.QtCore import QSettings, Qt
from PyQt6.QtGui import QAction, QFont
from PyQt6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QSplitter,
    QStatusBar,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QToolBar,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .aircraft_config import AircraftManager
from .altitude_profile_widget import AltitudeProfileWidget
from .exporters import export_flp, export_pln, export_rte
from .flight_calculator import RouteStatistics, calculate_route_statistics, haversine_distance
from .history_manager import HistoryManager
from .map_widget import MapWidget
from .models import AircraftConfig, Flightplan, WaypointType
from .navdata import get_navdata
from .parsers import FlpParser, PlnParser, RteParser
from .settings_dialog import SettingsDialog
from .simbrief import SimBriefClient, SimBriefOFP
from .simconnect_client import AircraftState, SimConnectClient
from .weather_widget import WeatherWidget


class WaypointTableWidget(QTableWidget):
    """Table widget for displaying waypoint information with distance."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_table()

    def _setup_table(self):
        """Set up table columns and style."""
        self.setColumnCount(9)
        self.setHorizontalHeaderLabels([
            'No.', 'Ident', 'Type', 'Latitude', 'Longitude',
            'Altitude', 'Via', 'Dist(NM)', 'Bearing'
        ])

        # Set column widths
        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.Fixed)

        self.setColumnWidth(0, 40)
        self.setColumnWidth(2, 60)
        self.setColumnWidth(3, 85)
        self.setColumnWidth(4, 85)
        self.setColumnWidth(5, 65)
        self.setColumnWidth(6, 65)
        self.setColumnWidth(7, 70)
        self.setColumnWidth(8, 60)

        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

    def display_flightplan(self, flightplan: Flightplan, route_stats: RouteStatistics | None = None):
        """Display waypoints from a flightplan with route statistics."""
        self.setRowCount(0)

        waypoints = flightplan.all_waypoints()

        # Build leg info lookup
        leg_info = {}
        if route_stats:
            for leg in route_stats.legs:
                leg_info[leg.to_waypoint.ident] = {
                    'distance': leg.distance_nm,
                    'bearing': leg.bearing,
                    'cumulative': leg.cumulative_distance_nm
                }

        for i, wpt in enumerate(waypoints):
            self.insertRow(i)

            # Number
            num_item = QTableWidgetItem(str(i + 1))
            num_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.setItem(i, 0, num_item)

            # Ident
            ident_item = QTableWidgetItem(wpt.ident)
            ident_item.setFont(QFont("Consolas", 10, QFont.Weight.Bold))
            self.setItem(i, 1, ident_item)

            # Type
            type_names = {
                WaypointType.AIRPORT: 'APT',
                WaypointType.VOR: 'VOR',
                WaypointType.NDB: 'NDB',
                WaypointType.FIX: 'FIX',
                WaypointType.USER: 'USR',
                WaypointType.RUNWAY: 'RWY',
                WaypointType.UNKNOWN: '???',
            }
            type_item = QTableWidgetItem(type_names.get(wpt.waypoint_type, '???'))
            type_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.setItem(i, 2, type_item)

            # Latitude
            lat_item = QTableWidgetItem(f"{wpt.latitude:.4f}")
            lat_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.setItem(i, 3, lat_item)

            # Longitude
            lon_item = QTableWidgetItem(f"{wpt.longitude:.4f}")
            lon_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.setItem(i, 4, lon_item)

            # Altitude
            alt_text = f"FL{int(wpt.altitude / 100)}" if wpt.altitude else "-"
            alt_item = QTableWidgetItem(alt_text)
            alt_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.setItem(i, 5, alt_item)

            # Via (Airway)
            via_item = QTableWidgetItem(wpt.airway or "-")
            via_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.setItem(i, 6, via_item)

            # Distance and Bearing
            info = leg_info.get(wpt.ident, {})
            dist_text = f"{info.get('distance', 0):.1f}" if info else "-"
            bearing_text = f"{info.get('bearing', 0):.0f}°" if info else "-"

            dist_item = QTableWidgetItem(dist_text)
            dist_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.setItem(i, 7, dist_item)

            bearing_item = QTableWidgetItem(bearing_text)
            bearing_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.setItem(i, 8, bearing_item)

    def clear_display(self):
        """Clear all waypoints from the table."""
        self.setRowCount(0)


class FlightplanInfoWidget(QWidget):
    """Widget for displaying flightplan summary information with statistics."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_favorite = False
        self.current_file_path: str | None = None
        self._setup_ui()

    def _setup_ui(self):
        """Set up the info widget UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # Top row with title and favorite button
        top_layout = QHBoxLayout()

        self.title_label = QLabel("No flightplan loaded")
        self.title_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        top_layout.addWidget(self.title_label, 1)

        self.favorite_btn = QPushButton("☆")
        self.favorite_btn.setFixedSize(30, 30)
        self.favorite_btn.setToolTip("Add to favorites")
        self.favorite_btn.setStyleSheet("""
            QPushButton { font-size: 16px; border: none; background: transparent; }
            QPushButton:hover { background: #2f3549; border-radius: 15px; }
        """)
        top_layout.addWidget(self.favorite_btn)

        layout.addLayout(top_layout)

        # Route summary
        self.route_label = QLabel("")
        self.route_label.setFont(QFont("Consolas", 10))
        self.route_label.setWordWrap(True)
        layout.addWidget(self.route_label)

        # Details grid
        details_layout = QHBoxLayout()

        self.departure_label = QLabel("DEP: ----")
        self.departure_label.setFont(QFont("Consolas", 11, QFont.Weight.Bold))
        details_layout.addWidget(self.departure_label)

        details_layout.addWidget(QLabel(" → "))

        self.destination_label = QLabel("ARR: ----")
        self.destination_label.setFont(QFont("Consolas", 11, QFont.Weight.Bold))
        details_layout.addWidget(self.destination_label)

        details_layout.addStretch()

        self.waypoint_count_label = QLabel("WPT: 0")
        details_layout.addWidget(self.waypoint_count_label)

        self.altitude_label = QLabel("ALT: -----")
        details_layout.addWidget(self.altitude_label)

        # New: Distance and time
        self.distance_label = QLabel("DIST: --- NM")
        self.distance_label.setStyleSheet("color: #7aa2f7;")
        details_layout.addWidget(self.distance_label)

        self.time_label = QLabel("TIME: --:--")
        self.time_label.setStyleSheet("color: #9ece6a;")
        details_layout.addWidget(self.time_label)

        layout.addLayout(details_layout)

    def display_flightplan(
        self,
        flightplan: Flightplan,
        route_stats: RouteStatistics | None = None,
        is_favorite: bool = False
    ):
        """Display flightplan information."""
        self.title_label.setText(flightplan.title or "Unnamed Flightplan")
        self.route_label.setText(flightplan.route_string)
        self.departure_label.setText(f"DEP: {flightplan.departure_icao}")
        self.destination_label.setText(f"ARR: {flightplan.destination_icao}")
        self.waypoint_count_label.setText(f"WPT: {flightplan.total_waypoints}")
        self.current_file_path = flightplan.source_file

        if flightplan.cruise_altitude:
            self.altitude_label.setText(f"ALT: FL{int(flightplan.cruise_altitude / 100)}")
        else:
            self.altitude_label.setText("ALT: -----")

        # Update distance and time
        if route_stats:
            self.distance_label.setText(f"DIST: {route_stats.total_distance_nm:.1f} NM")
            self.time_label.setText(f"TIME: {route_stats.formatted_time}")
        else:
            self.distance_label.setText("DIST: --- NM")
            self.time_label.setText("TIME: --:--")

        # Update favorite button
        self.set_favorite(is_favorite)

    def set_favorite(self, is_favorite: bool):
        """Update favorite button state."""
        self.is_favorite = is_favorite
        if is_favorite:
            self.favorite_btn.setText("★")
            self.favorite_btn.setStyleSheet("""
                QPushButton { font-size: 16px; border: none; background: transparent; color: gold; }
                QPushButton:hover { background: #2f3549; border-radius: 15px; }
            """)
            self.favorite_btn.setToolTip("Remove from favorites")
        else:
            self.favorite_btn.setText("☆")
            self.favorite_btn.setStyleSheet("""
                QPushButton { font-size: 16px; border: none; background: transparent; }
                QPushButton:hover { background: #2f3549; border-radius: 15px; }
            """)
            self.favorite_btn.setToolTip("Add to favorites")

    def clear_display(self):
        """Clear the display."""
        self.title_label.setText("No flightplan loaded")
        self.route_label.setText("")
        self.departure_label.setText("DEP: ----")
        self.destination_label.setText("ARR: ----")
        self.waypoint_count_label.setText("WPT: 0")
        self.altitude_label.setText("ALT: -----")
        self.distance_label.setText("DIST: --- NM")
        self.time_label.setText("TIME: --:--")
        self.current_file_path = None
        self.set_favorite(False)


class HistoryWidget(QWidget):
    """Widget for displaying history and favorites."""

    def __init__(self, history_manager: HistoryManager, parent=None):
        super().__init__(parent)
        self.history_manager = history_manager
        self.on_item_selected = None  # Callback
        self._setup_ui()
        self.refresh()

    def _setup_ui(self):
        """Set up the history widget UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Tab widget for favorites and history
        self.tabs = QTabWidget()

        # Favorites tab
        self.favorites_list = QListWidget()
        self.favorites_list.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.tabs.addTab(self.favorites_list, "★ お気に入り")

        # History tab
        self.history_list = QListWidget()
        self.history_list.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.tabs.addTab(self.history_list, "履歴")

        layout.addWidget(self.tabs)

        # Clear history button
        btn_layout = QHBoxLayout()
        self.clear_btn = QPushButton("履歴をクリア")
        self.clear_btn.clicked.connect(self._on_clear_history)
        btn_layout.addStretch()
        btn_layout.addWidget(self.clear_btn)
        layout.addLayout(btn_layout)

    def refresh(self):
        """Refresh the lists."""
        # Refresh favorites
        self.favorites_list.clear()
        for entry in self.history_manager.get_favorites():
            item = QListWidgetItem(f"{entry.route_display}\n{entry.filename}")
            item.setData(Qt.ItemDataRole.UserRole, entry.file_path)
            item.setToolTip(f"{entry.file_path}\n{entry.last_opened_display}")
            self.favorites_list.addItem(item)

        # Refresh history
        self.history_list.clear()
        for entry in self.history_manager.get_history(limit=20):
            item = QListWidgetItem(f"{entry.route_display}\n{entry.filename}")
            item.setData(Qt.ItemDataRole.UserRole, entry.file_path)
            item.setToolTip(f"{entry.file_path}\n{entry.last_opened_display}")

            # Mark favorites with star
            if entry.is_favorite:
                item.setText(f"★ {entry.route_display}\n{entry.filename}")

            self.history_list.addItem(item)

    def _on_item_double_clicked(self, item: QListWidgetItem):
        """Handle item double-click."""
        file_path = item.data(Qt.ItemDataRole.UserRole)
        if file_path and self.on_item_selected:
            self.on_item_selected(file_path)

    def _on_clear_history(self):
        """Clear history."""
        reply = QMessageBox.question(
            self,
            "履歴をクリア",
            "履歴をクリアしますか？\n（お気に入りは保持されます）",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.history_manager.clear_history()
            self.refresh()


class SimBriefWidget(QWidget):
    """Widget for SimBrief integration."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.simbrief_client: SimBriefClient | None = None
        self.current_ofp: SimBriefOFP | None = None
        self.on_flightplan_loaded = None  # Callback
        self._setup_ui()

    def _setup_ui(self):
        """Set up the widget UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # Status
        self.status_label = QLabel("SimBriefに接続していません")
        self.status_label.setStyleSheet("color: #565f89;")
        layout.addWidget(self.status_label)

        # Fetch button
        self.fetch_btn = QPushButton("最新OFPを取得")
        self.fetch_btn.clicked.connect(self._fetch_ofp)
        layout.addWidget(self.fetch_btn)

        # OFP info
        self.info_group = QGroupBox("フライトプラン")
        info_layout = QVBoxLayout(self.info_group)

        self.flight_label = QLabel("便名: ---")
        self.flight_label.setFont(QFont("Consolas", 11, QFont.Weight.Bold))
        info_layout.addWidget(self.flight_label)

        self.route_label = QLabel("ルート: ---- → ----")
        info_layout.addWidget(self.route_label)

        self.aircraft_label = QLabel("機材: ---")
        info_layout.addWidget(self.aircraft_label)

        self.distance_label = QLabel("距離: --- NM")
        info_layout.addWidget(self.distance_label)

        self.fuel_label = QLabel("燃料: --- lbs")
        info_layout.addWidget(self.fuel_label)

        self.info_group.setVisible(False)
        layout.addWidget(self.info_group)

        # Load button
        self.load_btn = QPushButton("このプランを読み込む")
        self.load_btn.clicked.connect(self._load_flightplan)
        self.load_btn.setVisible(False)
        self.load_btn.setProperty("accent", True)
        layout.addWidget(self.load_btn)

        layout.addStretch()

        # Configure hint
        hint_label = QLabel(
            "SimBrief Pilot IDは\n"
            "ツール → 設定 で設定できます"
        )
        hint_label.setStyleSheet("color: #565f89; font-size: 10px;")
        hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(hint_label)

    def set_client(self, client: SimBriefClient):
        """Set the SimBrief client."""
        self.simbrief_client = client
        if client and client.pilot_id:
            self.status_label.setText(f"Pilot ID: {client.pilot_id}")
            self.status_label.setStyleSheet("color: #9ece6a;")
        else:
            self.status_label.setText("SimBriefに接続していません")
            self.status_label.setStyleSheet("color: #565f89;")

    def _fetch_ofp(self):
        """Fetch the latest OFP from SimBrief."""
        if not self.simbrief_client or not self.simbrief_client.pilot_id:
            QMessageBox.warning(
                self,
                "エラー",
                "SimBrief Pilot IDが設定されていません。\n"
                "ツール → 設定 で設定してください。"
            )
            return

        self.fetch_btn.setEnabled(False)
        self.fetch_btn.setText("取得中...")
        self.status_label.setText("OFPを取得中...")

        try:
            ofp = self.simbrief_client.fetch_latest_ofp()

            if ofp:
                self.current_ofp = ofp
                self._display_ofp(ofp)
                self.status_label.setText("OFPを取得しました")
                self.status_label.setStyleSheet("color: #9ece6a;")
            else:
                self.status_label.setText("OFPの取得に失敗しました")
                self.status_label.setStyleSheet("color: #f7768e;")
                reason = self.simbrief_client.last_error or \
                    "SimBriefからOFPを取得できませんでした。"
                QMessageBox.warning(self, "SimBrief", reason)
        except Exception as e:
            self.status_label.setText(f"エラー: {str(e)[:30]}")
            self.status_label.setStyleSheet("color: #f7768e;")
        finally:
            self.fetch_btn.setEnabled(True)
            self.fetch_btn.setText("最新OFPを取得")

    def _display_ofp(self, ofp: SimBriefOFP):
        """Display OFP information."""
        self.flight_label.setText(f"便名: {ofp.flight_number}")
        self.route_label.setText(f"ルート: {ofp.departure_icao} → {ofp.arrival_icao}")
        self.aircraft_label.setText(f"機材: {ofp.aircraft_name} ({ofp.aircraft_reg})")
        self.distance_label.setText(f"距離: {ofp.distance_nm:.0f} NM")
        self.fuel_label.setText(f"燃料: {ofp.fuel_plan_ramp:.0f} {ofp.fuel_unit}")

        self.info_group.setVisible(True)
        self.load_btn.setVisible(True)

    def _load_flightplan(self):
        """Load the current OFP as a flightplan."""
        if self.current_ofp and self.simbrief_client and self.on_flightplan_loaded:
            flightplan = self.simbrief_client.ofp_to_flightplan(self.current_ofp)
            self.on_flightplan_loaded(flightplan)


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()

        self.aircraft_manager = AircraftManager()
        self.parsers = [PlnParser(), FlpParser(), RteParser()]
        self.current_flightplan: Flightplan | None = None
        self.current_route_stats: RouteStatistics | None = None
        self.settings = QSettings("MSFSFlightplanViewer", "FlightplanViewer")
        self.history_manager = HistoryManager(self.settings)
        self.cruise_speed = 450  # Default cruise speed in knots

        # Phase 2: NavData and SimBrief
        self.navdata = get_navdata()
        self.simbrief_client = SimBriefClient()

        # Phase 3: SimConnect real-time tracking
        self.simconnect_client = SimConnectClient(self)
        self.simconnect_client.state_updated.connect(self._on_sim_state_updated)
        self.simconnect_client.connection_changed.connect(self._on_sim_connection_changed)

        self._setup_ui()
        self._setup_menus()
        self._setup_toolbar()
        self._load_settings()
        self._scan_flightplans()

        # Auto-fetch SimBrief if configured
        if self.settings.value("simbrief/auto_fetch", False, type=bool):
            self._auto_fetch_simbrief()

    def _setup_ui(self):
        """Set up the main window UI."""
        self.setWindowTitle("MSFS Flightplan Viewer")
        self.setMinimumSize(1200, 800)

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)

        # Main layout with splitter
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(5, 5, 5, 5)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)

        # Left panel - File browser and history
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)

        # Left panel tabs
        self.left_tabs = QTabWidget()

        # Flightplan browser tab
        browser_widget = QWidget()
        browser_layout = QVBoxLayout(browser_widget)
        browser_layout.setContentsMargins(5, 5, 5, 5)

        # Aircraft filter
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Aircraft:"))
        self.aircraft_filter = QComboBox()
        self.aircraft_filter.addItem("All Aircraft")
        for config in self.aircraft_manager.configs:
            self.aircraft_filter.addItem(str(config))
        self.aircraft_filter.currentIndexChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self.aircraft_filter, 1)
        browser_layout.addLayout(filter_layout)

        # Search box
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search:"))
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Filter flightplans...")
        self.search_box.textChanged.connect(self._on_search_changed)
        search_layout.addWidget(self.search_box, 1)
        browser_layout.addLayout(search_layout)

        # Flightplan tree
        self.flightplan_tree = QTreeWidget()
        self.flightplan_tree.setHeaderLabels(["Flightplan Files"])
        self.flightplan_tree.itemDoubleClicked.connect(self._on_flightplan_selected)
        browser_layout.addWidget(self.flightplan_tree)

        # Buttons
        btn_layout = QHBoxLayout()
        self.open_btn = QPushButton("Open...")
        self.open_btn.clicked.connect(self._on_open_file)
        btn_layout.addWidget(self.open_btn)

        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self._scan_flightplans)
        btn_layout.addWidget(self.refresh_btn)

        self.add_folder_btn = QPushButton("Add Folder")
        self.add_folder_btn.clicked.connect(self._on_add_folder)
        btn_layout.addWidget(self.add_folder_btn)

        browser_layout.addLayout(btn_layout)

        self.left_tabs.addTab(browser_widget, "ファイル")

        # History tab
        self.history_widget = HistoryWidget(self.history_manager)
        self.history_widget.on_item_selected = lambda path: self._load_flightplan(Path(path))
        self.left_tabs.addTab(self.history_widget, "履歴")

        # SimBrief tab
        self.simbrief_widget = SimBriefWidget()
        self.simbrief_widget.on_flightplan_loaded = self._on_simbrief_flightplan_loaded
        self.left_tabs.addTab(self.simbrief_widget, "SimBrief")

        left_layout.addWidget(self.left_tabs)
        splitter.addWidget(left_panel)

        # Right panel - Map and info
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)

        # Info panel at top
        self.info_widget = FlightplanInfoWidget()
        self.info_widget.favorite_btn.clicked.connect(self._on_toggle_favorite)
        right_layout.addWidget(self.info_widget)

        # Main content tabs
        self.tab_widget = QTabWidget()

        # Map tab
        self.map_widget = MapWidget()
        self.tab_widget.addTab(self.map_widget, "地図")

        # Waypoint table tab
        self.waypoint_table = WaypointTableWidget()
        self.tab_widget.addTab(self.waypoint_table, "ウェイポイント")

        # Altitude profile tab
        self.altitude_widget = AltitudeProfileWidget()
        self.tab_widget.addTab(self.altitude_widget, "高度プロファイル")

        # Weather tab
        self.weather_widget = WeatherWidget()
        self.tab_widget.addTab(self.weather_widget, "気象")

        right_layout.addWidget(self.tab_widget, 1)

        splitter.addWidget(right_panel)

        # Set splitter sizes
        splitter.setSizes([300, 900])

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready - Double-click a flightplan to load it")

        # Permanent widgets: flight progress + SimConnect status
        self.progress_label = QLabel("")
        self.progress_label.setStyleSheet("color: #9ece6a; padding-right: 8px;")
        self.status_bar.addPermanentWidget(self.progress_label)

        self.sim_status_label = QLabel("MSFS: 未接続")
        self.sim_status_label.setStyleSheet("color: #565f89; padding-right: 4px;")
        self.status_bar.addPermanentWidget(self.sim_status_label)

    def _setup_toolbar(self):
        """Set up the toolbar."""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        # Cruise speed input
        toolbar.addWidget(QLabel(" 巡航速度: "))
        self.speed_spinbox = QSpinBox()
        self.speed_spinbox.setRange(100, 600)
        self.speed_spinbox.setValue(self.cruise_speed)
        self.speed_spinbox.setSuffix(" kts")
        self.speed_spinbox.setToolTip("巡航速度を設定すると飛行時間が計算されます")
        self.speed_spinbox.valueChanged.connect(self._on_speed_changed)
        toolbar.addWidget(self.speed_spinbox)

        toolbar.addSeparator()

        # Quick view buttons
        self.map_btn = QPushButton("地図")
        self.map_btn.clicked.connect(lambda: self.tab_widget.setCurrentIndex(0))
        toolbar.addWidget(self.map_btn)

        self.wpt_btn = QPushButton("WPT")
        self.wpt_btn.clicked.connect(lambda: self.tab_widget.setCurrentIndex(1))
        toolbar.addWidget(self.wpt_btn)

        self.alt_btn = QPushButton("高度")
        self.alt_btn.clicked.connect(lambda: self.tab_widget.setCurrentIndex(2))
        toolbar.addWidget(self.alt_btn)

        toolbar.addSeparator()

        # SimBrief button
        self.simbrief_btn = QPushButton("SimBrief")
        self.simbrief_btn.setToolTip("SimBriefから最新のOFPを取得")
        self.simbrief_btn.clicked.connect(self._on_fetch_simbrief)
        toolbar.addWidget(self.simbrief_btn)

        toolbar.addSeparator()

        # SimConnect buttons
        self.sim_connect_btn = QPushButton("✈ MSFS接続")
        self.sim_connect_btn.setCheckable(True)
        self.sim_connect_btn.setToolTip("MSFSに接続して自機位置をリアルタイム表示")
        self.sim_connect_btn.clicked.connect(self._on_toggle_simconnect)
        toolbar.addWidget(self.sim_connect_btn)

        self.follow_btn = QPushButton("追従")
        self.follow_btn.setCheckable(True)
        self.follow_btn.setEnabled(False)
        self.follow_btn.setToolTip("地図を自機位置に追従させる")
        self.follow_btn.toggled.connect(
            lambda checked: self.map_widget.set_follow_aircraft(checked)
        )
        toolbar.addWidget(self.follow_btn)

        self.clear_track_btn = QPushButton("軌跡クリア")
        self.clear_track_btn.setEnabled(False)
        self.clear_track_btn.setToolTip("記録した飛行軌跡を消去")
        self.clear_track_btn.clicked.connect(self._on_clear_track)
        toolbar.addWidget(self.clear_track_btn)

    def _setup_menus(self):
        """Set up the menu bar."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        open_action = QAction("&Open Flightplan...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self._on_open_file)
        file_menu.addAction(open_action)

        add_folder_action = QAction("Add &Folder...", self)
        add_folder_action.triggered.connect(self._on_add_folder)
        file_menu.addAction(add_folder_action)

        file_menu.addSeparator()

        # Export submenu (format conversion)
        self.export_menu = file_menu.addMenu("&Export As")

        export_pln_action = QAction("MSFS PLN形式 (.pln)...", self)
        export_pln_action.triggered.connect(lambda: self._on_export('pln'))
        self.export_menu.addAction(export_pln_action)

        export_flp_action = QAction("Fenix/Aerosoft FLP形式 (.flp)...", self)
        export_flp_action.triggered.connect(lambda: self._on_export('flp'))
        self.export_menu.addAction(export_flp_action)

        export_rte_action = QAction("PMDG RTE形式 (.rte)...", self)
        export_rte_action.triggered.connect(lambda: self._on_export('rte'))
        self.export_menu.addAction(export_rte_action)

        self.export_menu.setEnabled(False)

        file_menu.addSeparator()

        # Add to favorites
        self.fav_action = QAction("Add to &Favorites", self)
        self.fav_action.setShortcut("Ctrl+D")
        self.fav_action.triggered.connect(self._on_toggle_favorite)
        self.fav_action.setEnabled(False)
        file_menu.addAction(self.fav_action)

        file_menu.addSeparator()

        refresh_action = QAction("&Refresh", self)
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(self._scan_flightplans)
        file_menu.addAction(refresh_action)

        file_menu.addSeparator()

        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Alt+F4")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # View menu
        view_menu = menubar.addMenu("&View")

        map_action = QAction("Show &Map", self)
        map_action.setShortcut("Ctrl+M")
        map_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(0))
        view_menu.addAction(map_action)

        table_action = QAction("Show &Waypoints", self)
        table_action.setShortcut("Ctrl+W")
        table_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(1))
        view_menu.addAction(table_action)

        profile_action = QAction("Show &Altitude Profile", self)
        profile_action.setShortcut("Ctrl+A")
        profile_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(2))
        view_menu.addAction(profile_action)

        weather_action = QAction("Show W&eather", self)
        weather_action.setShortcut("Ctrl+E")
        weather_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(3))
        view_menu.addAction(weather_action)

        view_menu.addSeparator()

        history_action = QAction("Show &History", self)
        history_action.setShortcut("Ctrl+H")
        history_action.triggered.connect(lambda: self.left_tabs.setCurrentIndex(1))
        view_menu.addAction(history_action)

        # Tools menu
        tools_menu = menubar.addMenu("&Tools")

        simbrief_action = QAction("Fetch from &SimBrief", self)
        simbrief_action.setShortcut("Ctrl+B")
        simbrief_action.triggered.connect(self._on_fetch_simbrief)
        tools_menu.addAction(simbrief_action)

        tools_menu.addSeparator()

        navdata_info_action = QAction("&NavData Info", self)
        navdata_info_action.triggered.connect(self._show_navdata_info)
        tools_menu.addAction(navdata_info_action)

        tools_menu.addSeparator()

        settings_action = QAction("&Settings...", self)
        settings_action.setShortcut("Ctrl+,")
        settings_action.triggered.connect(self._show_settings)
        tools_menu.addAction(settings_action)

        # Help menu
        help_menu = menubar.addMenu("&Help")

        about_action = QAction("&About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _load_settings(self):
        """Load application settings."""
        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)

        # Load custom paths
        custom_paths = self.settings.value("custom_paths", [])
        if custom_paths:
            for path_str in custom_paths:
                self.aircraft_manager.add_custom_path(Path(path_str))

        # Load cruise speed
        speed = self.settings.value("cruise_speed", 450, type=int)
        self.cruise_speed = speed
        self.speed_spinbox.setValue(speed)

        # Load SimBrief settings
        pilot_id = self.settings.value("simbrief/pilot_id", "")
        if pilot_id:
            self.simbrief_client.set_pilot_id(pilot_id)
            self.simbrief_widget.set_client(self.simbrief_client)

        # Load NavData if configured
        navdata_path = self.settings.value("navdata/path", "")
        if navdata_path and Path(navdata_path).exists():
            count = self.navdata.load_xplane_earthnav(Path(navdata_path))
            if count > 0:
                self.status_bar.showMessage(f"Loaded {count} navaids from external file")

    def _save_settings(self):
        """Save application settings."""
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("custom_paths",
                               [str(p) for p in self.aircraft_manager.custom_paths])
        self.settings.setValue("cruise_speed", self.cruise_speed)

    def _scan_flightplans(self):
        """Scan for flightplan files and populate the tree."""
        self.flightplan_tree.clear()
        self.status_bar.showMessage("Scanning for flightplans...")

        files = self.aircraft_manager.get_all_flightplan_files()

        # Group by aircraft
        by_aircraft: dict[str, list[tuple[Path, AircraftConfig]]] = {}
        for fp_file, config in files:
            key = str(config)
            if key not in by_aircraft:
                by_aircraft[key] = []
            by_aircraft[key].append((fp_file, config))

        # Populate tree
        for aircraft_name, aircraft_files in sorted(by_aircraft.items()):
            aircraft_item = QTreeWidgetItem([f"{aircraft_name} ({len(aircraft_files)} files)"])
            aircraft_item.setExpanded(False)

            for fp_file, _config in sorted(aircraft_files, key=lambda x: x[0].name):
                file_item = QTreeWidgetItem([fp_file.name])
                file_item.setData(0, Qt.ItemDataRole.UserRole, str(fp_file))
                file_item.setToolTip(0, str(fp_file))

                # Mark favorites
                if self.history_manager.is_favorite(str(fp_file)):
                    file_item.setText(0, f"★ {fp_file.name}")

                aircraft_item.addChild(file_item)

            self.flightplan_tree.addTopLevelItem(aircraft_item)

        total_files = sum(len(f) for f in by_aircraft.values())
        self.status_bar.showMessage(f"Found {total_files} flightplan files")

    def _on_filter_changed(self, index: int):
        """Handle aircraft filter change."""
        self._apply_filters()

    def _on_search_changed(self, text: str):
        """Handle search text change."""
        self._apply_filters()

    def _on_speed_changed(self, value: int):
        """Handle cruise speed change."""
        self.cruise_speed = value
        # Recalculate if flightplan is loaded
        if self.current_flightplan:
            self._update_route_stats()

    def _update_route_stats(self):
        """Update route statistics with current speed."""
        if not self.current_flightplan:
            return

        self.current_route_stats = calculate_route_statistics(
            self.current_flightplan,
            self.cruise_speed
        )

        # Update displays
        is_fav = self.history_manager.is_favorite(self.current_flightplan.source_file or "")
        self.info_widget.display_flightplan(
            self.current_flightplan,
            self.current_route_stats,
            is_fav
        )
        self.waypoint_table.display_flightplan(
            self.current_flightplan,
            self.current_route_stats
        )
        self.altitude_widget.set_flightplan(
            self.current_flightplan,
            self.cruise_speed
        )

    def _apply_filters(self):
        """Apply current filters to the tree."""
        search_text = self.search_box.text().lower()
        filter_idx = self.aircraft_filter.currentIndex()

        for i in range(self.flightplan_tree.topLevelItemCount()):
            aircraft_item = self.flightplan_tree.topLevelItem(i)

            # Check aircraft filter
            aircraft_visible = filter_idx == 0  # "All Aircraft"
            if filter_idx > 0:
                config = self.aircraft_manager.configs[filter_idx - 1]
                aircraft_visible = str(config) in aircraft_item.text(0)

            visible_children = 0
            for j in range(aircraft_item.childCount()):
                child = aircraft_item.child(j)
                child_visible = aircraft_visible

                # Apply search filter
                if child_visible and search_text:
                    child_visible = search_text in child.text(0).lower()

                child.setHidden(not child_visible)
                if child_visible:
                    visible_children += 1

            aircraft_item.setHidden(visible_children == 0)

    def _on_flightplan_selected(self, item: QTreeWidgetItem, column: int):
        """Handle flightplan selection from tree."""
        file_path = item.data(0, Qt.ItemDataRole.UserRole)
        if file_path:
            self._load_flightplan(Path(file_path))

    def _on_open_file(self):
        """Open a flightplan file via file dialog."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Flightplan",
            "",
            "All Flightplans (*.pln *.flp *.rte);;PLN Files (*.pln);;FLP Files (*.flp);;RTE Files (*.rte)"
        )
        if file_path:
            self._load_flightplan(Path(file_path))

    def _on_add_folder(self):
        """Add a custom folder to scan."""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Flightplan Folder",
            ""
        )
        if folder:
            self.aircraft_manager.add_custom_path(Path(folder))
            self._save_settings()
            self._scan_flightplans()

    def _on_toggle_favorite(self):
        """Toggle favorite status for current flightplan."""
        if not self.current_flightplan or not self.current_flightplan.source_file:
            return

        is_now_favorite = self.history_manager.toggle_favorite(
            self.current_flightplan.source_file
        )
        self.info_widget.set_favorite(is_now_favorite)
        self.history_widget.refresh()
        self._scan_flightplans()  # Refresh to update stars

    def _load_flightplan(self, file_path: Path):
        """Load and display a flightplan file."""
        self.status_bar.showMessage(f"Loading {file_path.name}...")

        # Find appropriate parser
        flightplan = None
        for parser in self.parsers:
            if parser.can_parse(file_path):
                flightplan = parser.parse(file_path)
                if flightplan:
                    break

        if not flightplan:
            QMessageBox.warning(
                self,
                "Error",
                f"Could not parse flightplan file:\n{file_path}"
            )
            self.status_bar.showMessage("Failed to load flightplan")
            return

        self.current_flightplan = flightplan

        # Enhance waypoints with NavData coordinates (e.g. FLP airports)
        self._enhance_waypoints_with_navdata(flightplan)

        # Calculate route statistics
        self.current_route_stats = calculate_route_statistics(
            flightplan,
            self.cruise_speed
        )

        # Add to history
        self.history_manager.add_to_history(
            str(file_path),
            flightplan.departure_icao,
            flightplan.destination_icao,
            flightplan.title
        )
        self.history_widget.refresh()

        # Check if favorite
        is_fav = self.history_manager.is_favorite(str(file_path))

        # Update displays
        self.info_widget.display_flightplan(flightplan, self.current_route_stats, is_fav)
        self.map_widget.display_flightplan(flightplan)
        self.waypoint_table.display_flightplan(flightplan, self.current_route_stats)
        self.altitude_widget.set_flightplan(flightplan, self.cruise_speed)
        self.weather_widget.set_airports(
            flightplan.departure_icao, flightplan.destination_icao
        )

        # Enable favorite action and export menu
        self.fav_action.setEnabled(True)
        self.export_menu.setEnabled(True)

        # Status message with distance/time
        stats_msg = ""
        if self.current_route_stats:
            stats_msg = f" | {self.current_route_stats.total_distance_nm:.0f} NM"
            if self.current_route_stats.estimated_flight_time_minutes:
                stats_msg += f" | {self.current_route_stats.formatted_time}"

        self.status_bar.showMessage(
            f"Loaded: {flightplan.departure_icao} → {flightplan.destination_icao} "
            f"({flightplan.total_waypoints} waypoints){stats_msg}"
        )

    def _on_fetch_simbrief(self):
        """Fetch OFP from SimBrief."""
        if not self.simbrief_client.pilot_id:
            QMessageBox.warning(
                self,
                "SimBrief",
                "SimBrief Pilot IDが設定されていません。\n"
                "ツール → 設定 で設定してください。"
            )
            self._show_settings()
            return

        self.left_tabs.setCurrentIndex(2)  # Switch to SimBrief tab
        self.simbrief_widget._fetch_ofp()

    def _on_simbrief_flightplan_loaded(self, flightplan: Flightplan):
        """Handle flightplan loaded from SimBrief."""
        self._display_flightplan(flightplan)

    def _display_flightplan(self, flightplan: Flightplan):
        """Display a flightplan (from any source)."""
        self.current_flightplan = flightplan

        # Enhance waypoints with NavData coordinates
        self._enhance_waypoints_with_navdata(flightplan)

        # Calculate route statistics
        self.current_route_stats = calculate_route_statistics(
            flightplan,
            self.cruise_speed
        )

        # Update displays
        self.info_widget.display_flightplan(flightplan, self.current_route_stats, False)
        self.map_widget.display_flightplan(flightplan)
        self.waypoint_table.display_flightplan(flightplan, self.current_route_stats)
        self.altitude_widget.set_flightplan(flightplan, self.cruise_speed)
        self.weather_widget.set_airports(
            flightplan.departure_icao, flightplan.destination_icao
        )

        # Enable favorite action and export menu
        self.fav_action.setEnabled(bool(flightplan.source_file))
        self.export_menu.setEnabled(True)

        # Status message
        stats_msg = ""
        if self.current_route_stats:
            stats_msg = f" | {self.current_route_stats.total_distance_nm:.0f} NM"
            if self.current_route_stats.estimated_flight_time_minutes:
                stats_msg += f" | {self.current_route_stats.formatted_time}"

        self.status_bar.showMessage(
            f"Loaded: {flightplan.departure_icao} → {flightplan.destination_icao} "
            f"({flightplan.total_waypoints} waypoints){stats_msg}"
        )

    def _enhance_waypoints_with_navdata(self, flightplan: Flightplan):
        """Enhance waypoints with coordinates from NavData."""
        all_wpts = flightplan.all_waypoints()

        for i, wpt in enumerate(all_wpts):
            # Skip if already has valid coordinates
            if wpt.latitude != 0 or wpt.longitude != 0:
                continue

            # Get nearby waypoint for reference
            near_lat, near_lon = None, None
            if i > 0 and all_wpts[i - 1].latitude != 0:
                near_lat = all_wpts[i - 1].latitude
                near_lon = all_wpts[i - 1].longitude

            # Look up in NavData
            coords = self.navdata.get_coordinates(
                wpt.ident,
                wpt.waypoint_type,
                near_lat,
                near_lon
            )

            if coords:
                wpt.latitude = coords[0]
                wpt.longitude = coords[1]

    def _auto_fetch_simbrief(self):
        """Auto-fetch SimBrief OFP on startup."""
        if self.simbrief_client.pilot_id:
            self.simbrief_widget.set_client(self.simbrief_client)
            # Don't auto-fetch immediately, just set up the client

    def _on_export(self, fmt: str):
        """Export the current flightplan in the selected format."""
        if not self.current_flightplan:
            return

        fp = self.current_flightplan
        default_name = f"{fp.departure_icao}_{fp.destination_icao}.{fmt}"

        filters = {
            'pln': "MSFS Flightplan (*.pln)",
            'flp': "FLP Flightplan (*.flp)",
            'rte': "PMDG Route (*.rte)",
        }

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "フライトプランをエクスポート",
            default_name,
            filters.get(fmt, "All Files (*)")
        )
        if not file_path:
            return

        exporters = {
            'pln': export_pln,
            'flp': export_flp,
            'rte': export_rte,
        }
        success = exporters[fmt](fp, Path(file_path))

        if success:
            self.status_bar.showMessage(
                f"エクスポート完了: {Path(file_path).name}", 5000
            )
        else:
            QMessageBox.warning(
                self,
                "エクスポート失敗",
                f"ファイルの書き込みに失敗しました:\n{file_path}"
            )

    # ------------------------------------------------------------------
    # SimConnect real-time tracking
    # ------------------------------------------------------------------

    def _on_toggle_simconnect(self, checked: bool):
        """Connect to / disconnect from MSFS."""
        if checked:
            if not self.simconnect_client.is_available:
                QMessageBox.warning(
                    self,
                    "SimConnect",
                    "SimConnectパッケージがインストールされていません。\n\n"
                    "コマンドプロンプトで以下を実行してください:\n"
                    "pip install SimConnect\n\n"
                    "※ Windows + MSFS環境でのみ動作します"
                )
                self.sim_connect_btn.setChecked(False)
                return

            if not self.simconnect_client.connect_to_sim():
                self.sim_connect_btn.setChecked(False)
        else:
            self.simconnect_client.disconnect_from_sim()

    def _on_sim_connection_changed(self, connected: bool, message: str):
        """Handle SimConnect connection state changes."""
        self.sim_connect_btn.setChecked(connected)
        self.follow_btn.setEnabled(connected)
        self.clear_track_btn.setEnabled(connected)

        if connected:
            self.sim_status_label.setText("MSFS: 接続中")
            self.sim_status_label.setStyleSheet("color: #9ece6a; padding-right: 4px;")
        else:
            self.sim_status_label.setText("MSFS: 未接続")
            self.sim_status_label.setStyleSheet("color: #565f89; padding-right: 4px;")
            self.progress_label.setText("")
            self.map_widget.remove_aircraft()

        self.status_bar.showMessage(message, 5000)

    def _on_sim_state_updated(self, state: AircraftState):
        """Handle aircraft state updates from the simulator."""
        # Update aircraft marker on the map
        self.map_widget.update_aircraft(
            state.latitude, state.longitude,
            state.heading_deg, state.altitude_ft, state.ground_speed_kts
        )

        # Update flight track
        self.map_widget.update_flight_track(self.simconnect_client.track.points)

        # Update flight progress against the loaded flightplan
        self._update_flight_progress(state)

    def _on_clear_track(self):
        """Clear the recorded flight track."""
        self.simconnect_client.clear_track()
        self.map_widget.update_flight_track([])
        self.map_widget.remove_aircraft()

    def _update_flight_progress(self, state: AircraftState):
        """Update the progress label: next fix and distance to destination."""
        if not self.current_route_stats or not self.current_route_stats.legs:
            self.progress_label.setText(
                f"GS {state.ground_speed_kts:.0f} kt / "
                f"ALT {state.altitude_ft:.0f} ft"
            )
            return

        legs = self.current_route_stats.legs

        # Find the leg the aircraft is currently on: the one that minimizes
        # d(aircraft, A) + d(aircraft, B) - d(A, B)
        best_idx = 0
        best_score = float('inf')
        for i, leg in enumerate(legs):
            d_a = haversine_distance(
                state.latitude, state.longitude,
                leg.from_waypoint.latitude, leg.from_waypoint.longitude
            )
            d_b = haversine_distance(
                state.latitude, state.longitude,
                leg.to_waypoint.latitude, leg.to_waypoint.longitude
            )
            score = d_a + d_b - leg.distance_nm
            if score < best_score:
                best_score = score
                best_idx = i

        current_leg = legs[best_idx]
        next_fix = current_leg.to_waypoint

        # Distance to destination = distance to next fix + remaining legs
        dist_to_next = haversine_distance(
            state.latitude, state.longitude,
            next_fix.latitude, next_fix.longitude
        )
        remaining = dist_to_next + sum(
            leg.distance_nm for leg in legs[best_idx + 1:]
        )

        # ETE based on current ground speed
        ete_text = ""
        if state.ground_speed_kts > 30:
            ete_minutes = (remaining / state.ground_speed_kts) * 60
            hours = int(ete_minutes // 60)
            minutes = int(ete_minutes % 60)
            ete_text = f" / ETE {hours:02d}:{minutes:02d}"

        self.progress_label.setText(
            f"次: {next_fix.ident} {dist_to_next:.0f} NM / "
            f"残り {remaining:.0f} NM{ete_text}"
        )

    def _show_settings(self):
        """Show the settings dialog."""
        dialog = SettingsDialog(self.settings, self)
        if dialog.exec():
            # Reload settings
            pilot_id = self.settings.value("simbrief/pilot_id", "")
            if pilot_id:
                self.simbrief_client.set_pilot_id(pilot_id)
                self.simbrief_widget.set_client(self.simbrief_client)

            # Reload custom paths
            self.aircraft_manager.custom_paths.clear()
            custom_paths = self.settings.value("custom_paths", []) or []
            for path_str in custom_paths:
                self.aircraft_manager.add_custom_path(Path(path_str))

            # Reload cruise speed
            speed = self.settings.value("cruise_speed", 450, type=int)
            self.cruise_speed = speed
            self.speed_spinbox.setValue(speed)

            # Rescan flightplans
            self._scan_flightplans()

    def _show_navdata_info(self):
        """Show NavData information."""
        info = (
            f"<h3>ナビゲーションデータベース</h3>"
            f"<p><b>空港:</b> {self.navdata.airport_count}</p>"
            f"<p><b>VOR:</b> {self.navdata.vor_count}</p>"
            f"<p><b>NDB:</b> {self.navdata.ndb_count}</p>"
            f"<p><b>FIX:</b> {self.navdata.fix_count}</p>"
            f"<p><b>合計:</b> {self.navdata.total_count}</p>"
            f"<hr>"
            f"<p>ツール → 設定 から追加のナビデータ<br>"
            f"(X-Plane earth_nav.dat) を読み込めます。</p>"
        )
        QMessageBox.information(self, "NavData Info", info)

    def _show_about(self):
        """Show about dialog."""
        from . import __version__
        QMessageBox.about(
            self,
            "About MSFS Flightplan Viewer",
            "<h2>MSFS Flightplan Viewer</h2>"
            f"<p>Version {__version__}</p>"
            "<p>A tool for viewing Microsoft Flight Simulator 2020 flightplans.</p>"
            "<h3>Features:</h3>"
            "<ul>"
            "<li>Interactive map display</li>"
            "<li>Distance and time calculation</li>"
            "<li>Altitude profile chart</li>"
            "<li>Favorites and history</li>"
            "<li>SimBrief integration</li>"
            "<li>NavData coordinate lookup</li>"
            "</ul>"
            "<h3>Supported Aircraft:</h3>"
            "<ul>"
            "<li>MSFS Default Aircraft (B787, A320neo, etc.)</li>"
            "<li>PMDG 737/777/747 Series</li>"
            "<li>Fenix A320 Series</li>"
            "<li>FlyByWire A32NX</li>"
            "<li>iniBuilds A300/A310</li>"
            "<li>Aerosoft CRJ Series</li>"
            "<li>And more...</li>"
            "</ul>"
        )

    def closeEvent(self, event):
        """Handle window close event."""
        self.simconnect_client.disconnect_from_sim()
        self._save_settings()
        self.map_widget.cleanup()
        event.accept()
