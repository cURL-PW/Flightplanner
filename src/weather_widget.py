"""Widget for displaying departure/destination weather (METAR)."""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .weather import MetarReport, WeatherFetcher

# Flight category badge colors
_CATEGORY_COLORS = {
    'VFR': '#00c853',
    'MVFR': '#2196f3',
    'IFR': '#f44336',
    'LIFR': '#d500f9',
}


class MetarCard(QGroupBox):
    """Card showing one airport's METAR."""

    def __init__(self, role_label: str, parent=None):
        super().__init__(role_label, parent)
        self._setup_ui()
        self.clear_display()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Header: ICAO + flight category badge
        header = QHBoxLayout()
        self.icao_label = QLabel("----")
        self.icao_label.setFont(QFont("Consolas", 14, QFont.Weight.Bold))
        header.addWidget(self.icao_label)

        self.category_label = QLabel("")
        self.category_label.setFixedHeight(22)
        self.category_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.addWidget(self.category_label)
        header.addStretch()

        self.time_label = QLabel("")
        self.time_label.setStyleSheet("color: #888; font-size: 10px;")
        header.addWidget(self.time_label)
        layout.addLayout(header)

        # Decoded values
        values = QHBoxLayout()
        self.wind_label = QLabel("風: ---")
        values.addWidget(self.wind_label)
        self.temp_label = QLabel("気温: ---")
        values.addWidget(self.temp_label)
        self.vis_label = QLabel("視程: ---")
        values.addWidget(self.vis_label)
        self.qnh_label = QLabel("QNH: ---")
        values.addWidget(self.qnh_label)
        values.addStretch()
        layout.addLayout(values)

        # Raw METAR
        self.raw_text = QTextEdit()
        self.raw_text.setReadOnly(True)
        self.raw_text.setFont(QFont("Consolas", 10))
        self.raw_text.setMaximumHeight(60)
        layout.addWidget(self.raw_text)

    def display_metar(self, report: MetarReport):
        """Show a METAR report."""
        self.icao_label.setText(report.icao)

        category = report.flight_category or ""
        if category:
            color = _CATEGORY_COLORS.get(category, '#888')
            self.category_label.setText(f" {category} ")
            self.category_label.setStyleSheet(
                f"background: {color}; color: white; font-weight: bold;"
                f"border-radius: 4px; padding: 2px 6px;"
            )
        else:
            self.category_label.setText("")
            self.category_label.setStyleSheet("")

        self.time_label.setText(report.observation_time)
        self.wind_label.setText(f"風: {report.wind_display}")

        if report.temperature_c is not None:
            temp = f"{report.temperature_c:.0f}°C"
            if report.dewpoint_c is not None:
                temp += f" / DP {report.dewpoint_c:.0f}°C"
            self.temp_label.setText(f"気温: {temp}")
        else:
            self.temp_label.setText("気温: ---")

        self.vis_label.setText(
            f"視程: {report.visibility} SM" if report.visibility else "視程: ---"
        )
        self.qnh_label.setText(
            f"QNH: {report.altimeter_hpa:.0f} hPa"
            if report.altimeter_hpa else "QNH: ---"
        )
        self.raw_text.setPlainText(report.raw_text)

    def show_missing(self, icao: str):
        """Show that no METAR is available for this airport."""
        self.clear_display()
        self.icao_label.setText(icao)
        self.raw_text.setPlainText("METARが見つかりませんでした（観測がない空港の可能性）")

    def clear_display(self):
        self.icao_label.setText("----")
        self.category_label.setText("")
        self.category_label.setStyleSheet("")
        self.time_label.setText("")
        self.wind_label.setText("風: ---")
        self.temp_label.setText("気温: ---")
        self.vis_label.setText("視程: ---")
        self.qnh_label.setText("QNH: ---")
        self.raw_text.clear()


class WeatherWidget(QWidget):
    """Weather tab: METARs for the departure and destination airports."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.departure_icao: str | None = None
        self.destination_icao: str | None = None

        self.fetcher = WeatherFetcher()
        self.fetcher.fetched.connect(self._on_fetched)
        self.fetcher.error.connect(self._on_error)

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Toolbar row
        top = QHBoxLayout()
        self.refresh_btn = QPushButton("METARを取得")
        self.refresh_btn.clicked.connect(self.refresh)
        top.addWidget(self.refresh_btn)

        self.status_label = QLabel("フライトプランを読み込むと気象情報を取得します")
        self.status_label.setStyleSheet("color: #888;")
        top.addWidget(self.status_label, 1)
        layout.addLayout(top)

        # METAR cards
        self.dep_card = MetarCard("出発地")
        layout.addWidget(self.dep_card)

        self.arr_card = MetarCard("目的地")
        layout.addWidget(self.arr_card)

        layout.addStretch()

        source_label = QLabel("データ提供: aviationweather.gov (NOAA)")
        source_label.setStyleSheet("color: #666; font-size: 10px;")
        source_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(source_label)

    def set_airports(self, departure: str | None, destination: str | None,
                     auto_fetch: bool = True):
        """Set the airports and optionally fetch their weather."""
        self.departure_icao = departure if departure and departure != '----' else None
        self.destination_icao = destination if destination and destination != '----' else None

        self.dep_card.clear_display()
        self.arr_card.clear_display()
        if self.departure_icao:
            self.dep_card.icao_label.setText(self.departure_icao)
        if self.destination_icao:
            self.arr_card.icao_label.setText(self.destination_icao)

        if auto_fetch and (self.departure_icao or self.destination_icao):
            self.refresh()

    def refresh(self):
        """Fetch METARs for the current airports."""
        codes = [c for c in (self.departure_icao, self.destination_icao) if c]
        if not codes:
            self.status_label.setText("フライトプランが読み込まれていません")
            return

        self.refresh_btn.setEnabled(False)
        self.status_label.setText("取得中...")
        self.fetcher.fetch_async(codes)

    def _on_fetched(self, reports: dict):
        """Handle fetched METAR reports."""
        self.refresh_btn.setEnabled(True)
        self.status_label.setText("取得完了")

        if self.departure_icao:
            report = reports.get(self.departure_icao)
            if report:
                self.dep_card.display_metar(report)
            else:
                self.dep_card.show_missing(self.departure_icao)

        if self.destination_icao:
            report = reports.get(self.destination_icao)
            if report:
                self.arr_card.display_metar(report)
            else:
                self.arr_card.show_missing(self.destination_icao)

    def _on_error(self, message: str):
        """Handle fetch errors."""
        self.refresh_btn.setEnabled(True)
        self.status_label.setText(f"取得失敗: {message[:60]}")
