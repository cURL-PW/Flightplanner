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
import logging
import sys


def main():
    """Main entry point for the application."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    from PyQt6.QtWidgets import QApplication

    from src import __version__
    from src.main_window import MainWindow
    from src.theme import apply_theme

    app = QApplication(sys.argv)
    app.setApplicationName("MSFS Flightplan Viewer")
    app.setApplicationVersion(__version__)
    app.setOrganizationName("MSFSFlightplanViewer")

    apply_theme(app)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
