"""Main application window for MSFS Flightplan Viewer."""
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtGui import QAction, QFont
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QTreeWidget, QTreeWidgetItem, QGroupBox, QLabel, QPushButton,
    QFileDialog, QMessageBox, QStatusBar, QMenuBar, QMenu,
    QTableWidget, QTableWidgetItem, QHeaderView, QTabWidget,
    QLineEdit, QComboBox
)

from .models import Flightplan, Waypoint, WaypointType, AircraftConfig
from .map_widget import MapWidget
from .aircraft_config import AircraftManager
from .parsers import PlnParser, FlpParser, RteParser


class WaypointTableWidget(QTableWidget):
    """Table widget for displaying waypoint information."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_table()

    def _setup_table(self):
        """Set up table columns and style."""
        self.setColumnCount(7)
        self.setHorizontalHeaderLabels([
            'No.', 'Ident', 'Type', 'Latitude', 'Longitude', 'Altitude', 'Via'
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

        self.setColumnWidth(0, 40)
        self.setColumnWidth(2, 70)
        self.setColumnWidth(3, 90)
        self.setColumnWidth(4, 90)
        self.setColumnWidth(5, 70)
        self.setColumnWidth(6, 70)

        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

    def display_flightplan(self, flightplan: Flightplan):
        """Display waypoints from a flightplan."""
        self.setRowCount(0)

        waypoints = flightplan.all_waypoints()

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

    def clear_display(self):
        """Clear all waypoints from the table."""
        self.setRowCount(0)


class FlightplanInfoWidget(QWidget):
    """Widget for displaying flightplan summary information."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        """Set up the info widget UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # Title
        self.title_label = QLabel("No flightplan loaded")
        self.title_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        layout.addWidget(self.title_label)

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

        layout.addLayout(details_layout)

    def display_flightplan(self, flightplan: Flightplan):
        """Display flightplan information."""
        self.title_label.setText(flightplan.title or "Unnamed Flightplan")
        self.route_label.setText(flightplan.route_string)
        self.departure_label.setText(f"DEP: {flightplan.departure_icao}")
        self.destination_label.setText(f"ARR: {flightplan.destination_icao}")
        self.waypoint_count_label.setText(f"WPT: {flightplan.total_waypoints}")

        if flightplan.cruise_altitude:
            self.altitude_label.setText(f"ALT: FL{int(flightplan.cruise_altitude / 100)}")
        else:
            self.altitude_label.setText("ALT: -----")

    def clear_display(self):
        """Clear the display."""
        self.title_label.setText("No flightplan loaded")
        self.route_label.setText("")
        self.departure_label.setText("DEP: ----")
        self.destination_label.setText("ARR: ----")
        self.waypoint_count_label.setText("WPT: 0")
        self.altitude_label.setText("ALT: -----")


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()

        self.aircraft_manager = AircraftManager()
        self.parsers = [PlnParser(), FlpParser(), RteParser()]
        self.current_flightplan: Optional[Flightplan] = None
        self.settings = QSettings("MSFSFlightplanViewer", "FlightplanViewer")

        self._setup_ui()
        self._setup_menus()
        self._load_settings()
        self._scan_flightplans()

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

        # Left panel - File browser
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)

        # Aircraft filter
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Aircraft:"))
        self.aircraft_filter = QComboBox()
        self.aircraft_filter.addItem("All Aircraft")
        for config in self.aircraft_manager.configs:
            self.aircraft_filter.addItem(str(config))
        self.aircraft_filter.currentIndexChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self.aircraft_filter, 1)
        left_layout.addLayout(filter_layout)

        # Search box
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search:"))
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Filter flightplans...")
        self.search_box.textChanged.connect(self._on_search_changed)
        search_layout.addWidget(self.search_box, 1)
        left_layout.addLayout(search_layout)

        # Flightplan tree
        self.flightplan_tree = QTreeWidget()
        self.flightplan_tree.setHeaderLabels(["Flightplan Files"])
        self.flightplan_tree.itemDoubleClicked.connect(self._on_flightplan_selected)
        left_layout.addWidget(self.flightplan_tree)

        # Buttons
        btn_layout = QHBoxLayout()
        self.open_btn = QPushButton("Open File...")
        self.open_btn.clicked.connect(self._on_open_file)
        btn_layout.addWidget(self.open_btn)

        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self._scan_flightplans)
        btn_layout.addWidget(self.refresh_btn)

        self.add_folder_btn = QPushButton("Add Folder...")
        self.add_folder_btn.clicked.connect(self._on_add_folder)
        btn_layout.addWidget(self.add_folder_btn)

        left_layout.addLayout(btn_layout)

        splitter.addWidget(left_panel)

        # Right panel - Map and info
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)

        # Info panel at top
        self.info_widget = FlightplanInfoWidget()
        right_layout.addWidget(self.info_widget)

        # Map and waypoint table in tabs
        self.tab_widget = QTabWidget()

        # Map tab
        self.map_widget = MapWidget()
        self.tab_widget.addTab(self.map_widget, "Map")

        # Waypoint table tab
        self.waypoint_table = WaypointTableWidget()
        self.tab_widget.addTab(self.waypoint_table, "Waypoints")

        right_layout.addWidget(self.tab_widget, 1)

        splitter.addWidget(right_panel)

        # Set splitter sizes
        splitter.setSizes([300, 900])

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready - Double-click a flightplan to load it")

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

    def _save_settings(self):
        """Save application settings."""
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("custom_paths",
                               [str(p) for p in self.aircraft_manager.custom_paths])

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

            for fp_file, config in sorted(aircraft_files, key=lambda x: x[0].name):
                file_item = QTreeWidgetItem([fp_file.name])
                file_item.setData(0, Qt.ItemDataRole.UserRole, str(fp_file))
                file_item.setToolTip(0, str(fp_file))
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

        # Update displays
        self.info_widget.display_flightplan(flightplan)
        self.map_widget.display_flightplan(flightplan)
        self.waypoint_table.display_flightplan(flightplan)

        self.status_bar.showMessage(
            f"Loaded: {flightplan.departure_icao} → {flightplan.destination_icao} "
            f"({flightplan.total_waypoints} waypoints)"
        )

    def _show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About MSFS Flightplan Viewer",
            "<h2>MSFS Flightplan Viewer</h2>"
            "<p>Version 1.0</p>"
            "<p>A tool for viewing Microsoft Flight Simulator 2020 flightplans.</p>"
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
            "<h3>Supported Formats:</h3>"
            "<ul>"
            "<li>.pln (MSFS XML format)</li>"
            "<li>.flp (CFMS format)</li>"
            "<li>.rte (PMDG format)</li>"
            "</ul>"
        )

    def closeEvent(self, event):
        """Handle window close event."""
        self._save_settings()
        self.map_widget.cleanup()
        event.accept()
