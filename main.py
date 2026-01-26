#!/usr/bin/env python3
"""
MSFS Flightplan Viewer

A tool for viewing Microsoft Flight Simulator 2020 flightplans from various
popular aircraft addons on an interactive map.

Supported Aircraft:
- MSFS Default Aircraft (B787, A320neo, etc.)
- PMDG 737/777/747 Series
- Fenix A320 Series
- FlyByWire A32NX
- iniBuilds A300/A310/A380
- Aerosoft CRJ Series
- And more...

Supported Formats:
- .pln (MSFS XML format)
- .flp (CFMS format - Fenix, FlyByWire, Aerosoft)
- .rte (PMDG format)
"""

import sys


def main():
    """Main entry point for the application."""
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QPalette, QColor

    from src.main_window import MainWindow

    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("MSFS Flightplan Viewer")
    app.setOrganizationName("MSFSFlightplanViewer")
    app.setStyle("Fusion")

    # Apply dark theme
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.Base, QColor(35, 35, 35))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(25, 25, 25))
    palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
    palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(35, 35, 35))
    app.setPalette(palette)

    # Apply stylesheet
    app.setStyleSheet("""
        QMainWindow {
            background-color: #353535;
        }
        QMenuBar {
            background-color: #2d2d2d;
            color: white;
            padding: 2px;
        }
        QMenuBar::item:selected {
            background-color: #3d3d3d;
        }
        QMenu {
            background-color: #2d2d2d;
            color: white;
            border: 1px solid #555;
        }
        QMenu::item:selected {
            background-color: #2a82da;
        }
        QTreeWidget {
            background-color: #252525;
            border: 1px solid #555;
            color: white;
        }
        QTreeWidget::item:selected {
            background-color: #2a82da;
        }
        QTreeWidget::item:hover {
            background-color: #3d3d3d;
        }
        QTableWidget {
            background-color: #252525;
            gridline-color: #444;
            border: 1px solid #555;
            color: white;
        }
        QTableWidget::item:selected {
            background-color: #2a82da;
        }
        QHeaderView::section {
            background-color: #2d2d2d;
            color: white;
            padding: 5px;
            border: 1px solid #444;
        }
        QPushButton {
            background-color: #2d2d2d;
            color: white;
            border: 1px solid #555;
            padding: 5px 15px;
            border-radius: 3px;
        }
        QPushButton:hover {
            background-color: #3d3d3d;
            border-color: #2a82da;
        }
        QPushButton:pressed {
            background-color: #2a82da;
        }
        QLineEdit {
            background-color: #252525;
            color: white;
            border: 1px solid #555;
            padding: 5px;
            border-radius: 3px;
        }
        QLineEdit:focus {
            border-color: #2a82da;
        }
        QComboBox {
            background-color: #252525;
            color: white;
            border: 1px solid #555;
            padding: 5px;
            border-radius: 3px;
        }
        QComboBox:hover {
            border-color: #2a82da;
        }
        QComboBox::drop-down {
            border: none;
            width: 20px;
        }
        QComboBox QAbstractItemView {
            background-color: #252525;
            color: white;
            selection-background-color: #2a82da;
        }
        QTabWidget::pane {
            border: 1px solid #555;
            background-color: #353535;
        }
        QTabBar::tab {
            background-color: #2d2d2d;
            color: white;
            padding: 8px 20px;
            border: 1px solid #555;
            border-bottom: none;
        }
        QTabBar::tab:selected {
            background-color: #353535;
            border-bottom: 2px solid #2a82da;
        }
        QTabBar::tab:hover:!selected {
            background-color: #3d3d3d;
        }
        QStatusBar {
            background-color: #2d2d2d;
            color: white;
        }
        QSplitter::handle {
            background-color: #555;
        }
        QGroupBox {
            border: 1px solid #555;
            border-radius: 5px;
            margin-top: 10px;
            padding-top: 10px;
        }
        QGroupBox::title {
            color: white;
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px;
        }
        QLabel {
            color: white;
        }
        QScrollBar:vertical {
            background-color: #252525;
            width: 12px;
            border: none;
        }
        QScrollBar::handle:vertical {
            background-color: #555;
            border-radius: 6px;
            min-height: 20px;
        }
        QScrollBar::handle:vertical:hover {
            background-color: #666;
        }
        QScrollBar:horizontal {
            background-color: #252525;
            height: 12px;
            border: none;
        }
        QScrollBar::handle:horizontal {
            background-color: #555;
            border-radius: 6px;
            min-width: 20px;
        }
        QScrollBar::handle:horizontal:hover {
            background-color: #666;
        }
    """)

    # Create and show main window
    window = MainWindow()
    window.show()

    # Run application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
