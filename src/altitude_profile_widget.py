"""Altitude profile chart widget for visualizing vertical flight path."""

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import (
    QColor,
    QFont,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
)
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget

from .flight_calculator import RouteStatistics, calculate_route_statistics
from .models import Flightplan


class AltitudeProfileChart(QWidget):
    """Widget for displaying altitude profile of a flightplan."""

    # Colors
    COLOR_BACKGROUND = QColor(35, 35, 35)
    COLOR_GRID = QColor(60, 60, 60)
    COLOR_GRID_MAJOR = QColor(80, 80, 80)
    COLOR_TEXT = QColor(200, 200, 200)
    COLOR_TEXT_DIM = QColor(140, 140, 140)
    COLOR_ROUTE = QColor(0, 170, 255)
    COLOR_ROUTE_FILL = QColor(0, 170, 255, 50)
    COLOR_WAYPOINT = QColor(255, 200, 0)
    COLOR_AIRPORT = QColor(0, 255, 100)
    COLOR_TOC = QColor(0, 255, 200)
    COLOR_TOD = QColor(255, 150, 0)

    # Margins
    MARGIN_LEFT = 60
    MARGIN_RIGHT = 20
    MARGIN_TOP = 30
    MARGIN_BOTTOM = 50

    def __init__(self, parent=None):
        super().__init__(parent)
        self.flightplan: Flightplan | None = None
        self.route_stats: RouteStatistics | None = None
        self.cruise_altitude: float = 35000  # feet

        self.setMinimumHeight(200)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def set_flightplan(self, flightplan: Flightplan, cruise_speed: float = 450):
        """Set the flightplan to display."""
        self.flightplan = flightplan
        self.route_stats = calculate_route_statistics(flightplan, cruise_speed)

        # Determine cruise altitude
        if flightplan.cruise_altitude:
            self.cruise_altitude = flightplan.cruise_altitude
        else:
            # Estimate from waypoint altitudes
            max_alt = 0
            for wpt in flightplan.all_waypoints():
                if wpt.altitude and wpt.altitude > max_alt:
                    max_alt = wpt.altitude
            self.cruise_altitude = max_alt if max_alt > 0 else 35000

        self.update()

    def clear(self):
        """Clear the display."""
        self.flightplan = None
        self.route_stats = None
        self.update()

    def paintEvent(self, event):
        """Paint the altitude profile chart."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Fill background
        painter.fillRect(self.rect(), self.COLOR_BACKGROUND)

        if not self.flightplan or not self.route_stats or not self.route_stats.legs:
            self._draw_empty_state(painter)
            return

        # Calculate chart area
        chart_rect = QRectF(
            self.MARGIN_LEFT,
            self.MARGIN_TOP,
            self.width() - self.MARGIN_LEFT - self.MARGIN_RIGHT,
            self.height() - self.MARGIN_TOP - self.MARGIN_BOTTOM
        )

        # Draw components
        self._draw_grid(painter, chart_rect)
        self._draw_altitude_axis(painter, chart_rect)
        self._draw_distance_axis(painter, chart_rect)
        self._draw_route(painter, chart_rect)
        self._draw_waypoints(painter, chart_rect)
        self._draw_title(painter)

    def _draw_empty_state(self, painter: QPainter):
        """Draw empty state message."""
        painter.setPen(self.COLOR_TEXT_DIM)
        painter.setFont(QFont("Segoe UI", 12))
        painter.drawText(
            self.rect(),
            Qt.AlignmentFlag.AlignCenter,
            "フライトプランを選択してください"
        )

    def _draw_grid(self, painter: QPainter, chart_rect: QRectF):
        """Draw the background grid."""
        # Horizontal grid lines (altitude)
        painter.setPen(QPen(self.COLOR_GRID, 1, Qt.PenStyle.DotLine))

        num_h_lines = 5
        for i in range(num_h_lines + 1):
            y = chart_rect.top() + (chart_rect.height() * i / num_h_lines)
            if i % 2 == 0:
                painter.setPen(QPen(self.COLOR_GRID_MAJOR, 1))
            else:
                painter.setPen(QPen(self.COLOR_GRID, 1, Qt.PenStyle.DotLine))
            painter.drawLine(
                QPointF(chart_rect.left(), y),
                QPointF(chart_rect.right(), y)
            )

        # Vertical grid lines (distance)
        num_v_lines = 8
        painter.setPen(QPen(self.COLOR_GRID, 1, Qt.PenStyle.DotLine))
        for i in range(1, num_v_lines):
            x = chart_rect.left() + (chart_rect.width() * i / num_v_lines)
            painter.drawLine(
                QPointF(x, chart_rect.top()),
                QPointF(x, chart_rect.bottom())
            )

    def _draw_altitude_axis(self, painter: QPainter, chart_rect: QRectF):
        """Draw the altitude (Y) axis."""
        painter.setPen(self.COLOR_TEXT)
        painter.setFont(QFont("Consolas", 9))

        # Max altitude with some margin
        max_alt = self.cruise_altitude * 1.1

        num_labels = 5
        for i in range(num_labels + 1):
            y = chart_rect.top() + (chart_rect.height() * i / num_labels)
            altitude = max_alt * (1 - i / num_labels)

            # Format as flight level
            if altitude >= 1000:
                label = f"FL{int(altitude / 100)}"
            else:
                label = f"{int(altitude)}"

            painter.drawText(
                QRectF(0, y - 10, self.MARGIN_LEFT - 5, 20),
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                label
            )

        # Axis label
        painter.save()
        painter.translate(15, chart_rect.center().y())
        painter.rotate(-90)
        painter.drawText(
            QRectF(-50, -10, 100, 20),
            Qt.AlignmentFlag.AlignCenter,
            "高度 (ft)"
        )
        painter.restore()

    def _draw_distance_axis(self, painter: QPainter, chart_rect: QRectF):
        """Draw the distance (X) axis."""
        painter.setPen(self.COLOR_TEXT)
        painter.setFont(QFont("Consolas", 9))

        total_dist = self.route_stats.total_distance_nm
        if total_dist <= 0:
            return

        num_labels = 8
        for i in range(num_labels + 1):
            x = chart_rect.left() + (chart_rect.width() * i / num_labels)
            distance = total_dist * i / num_labels

            label = f"{int(distance)}"
            painter.drawText(
                QRectF(x - 30, chart_rect.bottom() + 5, 60, 20),
                Qt.AlignmentFlag.AlignCenter,
                label
            )

        # Axis label
        painter.drawText(
            QRectF(chart_rect.left(), chart_rect.bottom() + 25, chart_rect.width(), 20),
            Qt.AlignmentFlag.AlignCenter,
            "距離 (NM)"
        )

    def _draw_route(self, painter: QPainter, chart_rect: QRectF):
        """Draw the altitude profile route line."""
        if not self.route_stats.legs:
            return

        total_dist = self.route_stats.total_distance_nm
        max_alt = self.cruise_altitude * 1.1

        if total_dist <= 0 or max_alt <= 0:
            return

        # Build path points
        points = []
        waypoints = self.flightplan.all_waypoints()

        # Add departure point
        dep_alt = waypoints[0].altitude or 0
        points.append(QPointF(
            chart_rect.left(),
            chart_rect.bottom() - (dep_alt / max_alt) * chart_rect.height()
        ))

        # Add intermediate points with estimated climb/cruise/descent profile
        cumulative_dist = 0
        for leg in self.route_stats.legs:
            cumulative_dist = leg.cumulative_distance_nm

            # Get altitude at this waypoint
            wpt_alt = leg.to_waypoint.altitude
            if wpt_alt is None or wpt_alt == 0:
                # Estimate based on position in route
                progress = cumulative_dist / total_dist
                if progress < 0.2:
                    # Climb phase
                    wpt_alt = self.cruise_altitude * (progress / 0.2)
                elif progress > 0.8:
                    # Descent phase
                    wpt_alt = self.cruise_altitude * ((1 - progress) / 0.2)
                else:
                    # Cruise phase
                    wpt_alt = self.cruise_altitude

            x = chart_rect.left() + (cumulative_dist / total_dist) * chart_rect.width()
            y = chart_rect.bottom() - (wpt_alt / max_alt) * chart_rect.height()
            points.append(QPointF(x, y))

        # Draw filled area under curve
        if len(points) >= 2:
            fill_path = QPainterPath()
            fill_path.moveTo(QPointF(points[0].x(), chart_rect.bottom()))
            for point in points:
                fill_path.lineTo(point)
            fill_path.lineTo(QPointF(points[-1].x(), chart_rect.bottom()))
            fill_path.closeSubpath()

            gradient = QLinearGradient(0, chart_rect.top(), 0, chart_rect.bottom())
            gradient.setColorAt(0, QColor(0, 170, 255, 80))
            gradient.setColorAt(1, QColor(0, 170, 255, 20))
            painter.fillPath(fill_path, gradient)

        # Draw route line
        painter.setPen(QPen(self.COLOR_ROUTE, 2))
        for i in range(len(points) - 1):
            painter.drawLine(points[i], points[i + 1])

        # Draw TOC and TOD markers
        self._draw_toc_tod(painter, chart_rect, points)

    def _draw_toc_tod(self, painter: QPainter, chart_rect: QRectF, points: list):
        """Draw Top of Climb and Top of Descent markers."""
        if len(points) < 3:
            return

        total_dist = self.route_stats.total_distance_nm

        # TOC - approximately 20% into flight
        toc_dist = total_dist * 0.18
        toc_x = chart_rect.left() + (toc_dist / total_dist) * chart_rect.width()
        toc_y = chart_rect.bottom() - (self.cruise_altitude / (self.cruise_altitude * 1.1)) * chart_rect.height()

        # TOD - approximately 80% into flight
        tod_dist = total_dist * 0.82
        tod_x = chart_rect.left() + (tod_dist / total_dist) * chart_rect.width()
        tod_y = toc_y

        # Draw markers
        marker_size = 6
        painter.setFont(QFont("Consolas", 8))

        # TOC
        painter.setPen(QPen(self.COLOR_TOC, 2))
        painter.setBrush(self.COLOR_TOC)
        painter.drawEllipse(QPointF(toc_x, toc_y), marker_size, marker_size)
        painter.setPen(self.COLOR_TOC)
        painter.drawText(
            QRectF(toc_x - 20, toc_y - 25, 40, 15),
            Qt.AlignmentFlag.AlignCenter,
            "T/C"
        )

        # TOD
        painter.setPen(QPen(self.COLOR_TOD, 2))
        painter.setBrush(self.COLOR_TOD)
        painter.drawEllipse(QPointF(tod_x, tod_y), marker_size, marker_size)
        painter.setPen(self.COLOR_TOD)
        painter.drawText(
            QRectF(tod_x - 20, tod_y - 25, 40, 15),
            Qt.AlignmentFlag.AlignCenter,
            "T/D"
        )

        painter.setBrush(Qt.BrushStyle.NoBrush)

    def _draw_waypoints(self, painter: QPainter, chart_rect: QRectF):
        """Draw waypoint markers on the profile."""
        if not self.route_stats.legs:
            return

        total_dist = self.route_stats.total_distance_nm
        max_alt = self.cruise_altitude * 1.1

        if total_dist <= 0:
            return

        waypoints = self.flightplan.all_waypoints()
        painter.setFont(QFont("Consolas", 8))

        # Draw departure
        dep = waypoints[0]
        dep_alt = dep.altitude or 0
        self._draw_waypoint_marker(
            painter, chart_rect,
            0, dep_alt, max_alt, total_dist,
            dep.ident, is_airport=True
        )

        # Draw intermediate waypoints
        cumulative_dist = 0
        for i, leg in enumerate(self.route_stats.legs):
            cumulative_dist = leg.cumulative_distance_nm
            wpt = leg.to_waypoint

            wpt_alt = wpt.altitude
            if wpt_alt is None or wpt_alt == 0:
                progress = cumulative_dist / total_dist
                if progress < 0.2:
                    wpt_alt = self.cruise_altitude * (progress / 0.2)
                elif progress > 0.8:
                    wpt_alt = self.cruise_altitude * ((1 - progress) / 0.2)
                else:
                    wpt_alt = self.cruise_altitude

            is_last = (i == len(self.route_stats.legs) - 1)
            self._draw_waypoint_marker(
                painter, chart_rect,
                cumulative_dist, wpt_alt, max_alt, total_dist,
                wpt.ident, is_airport=is_last
            )

    def _draw_waypoint_marker(
        self, painter: QPainter, chart_rect: QRectF,
        distance: float, altitude: float, max_alt: float, total_dist: float,
        ident: str, is_airport: bool = False
    ):
        """Draw a single waypoint marker."""
        x = chart_rect.left() + (distance / total_dist) * chart_rect.width()
        y = chart_rect.bottom() - (altitude / max_alt) * chart_rect.height()

        # Marker
        color = self.COLOR_AIRPORT if is_airport else self.COLOR_WAYPOINT
        painter.setPen(QPen(color, 2))
        painter.setBrush(color)

        if is_airport:
            painter.drawRect(QRectF(x - 4, y - 4, 8, 8))
        else:
            painter.drawEllipse(QPointF(x, y), 3, 3)

        # Label (draw every few waypoints to avoid clutter)
        painter.setPen(color)
        painter.drawText(
            QRectF(x - 25, chart_rect.bottom() + 2, 50, 12),
            Qt.AlignmentFlag.AlignCenter,
            ident
        )

        painter.setBrush(Qt.BrushStyle.NoBrush)

    def _draw_title(self, painter: QPainter):
        """Draw chart title."""
        if not self.flightplan:
            return

        painter.setPen(self.COLOR_TEXT)
        painter.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))

        title = f"{self.flightplan.departure_icao} → {self.flightplan.destination_icao}"
        if self.route_stats:
            title += f"  |  {self.route_stats.total_distance_nm:.0f} NM"
            if self.route_stats.estimated_flight_time_minutes:
                title += f"  |  {self.route_stats.formatted_time}"

        painter.drawText(
            QRectF(self.MARGIN_LEFT, 5, self.width() - self.MARGIN_LEFT - self.MARGIN_RIGHT, 20),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            title
        )


class AltitudeProfileWidget(QWidget):
    """Container widget with altitude profile chart and statistics."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        """Set up the widget UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        # Chart
        self.chart = AltitudeProfileChart()
        layout.addWidget(self.chart, 1)

        # Statistics bar
        stats_layout = QHBoxLayout()
        stats_layout.setContentsMargins(10, 5, 10, 5)

        self.stats_labels = {}
        stats = [
            ("distance", "距離: -- NM"),
            ("time", "時間: --:--"),
            ("cruise", "巡航: FL---"),
            ("legs", "レグ: --"),
        ]

        for key, text in stats:
            label = QLabel(text)
            label.setStyleSheet("color: #aaa; font-family: Consolas;")
            self.stats_labels[key] = label
            stats_layout.addWidget(label)

        stats_layout.addStretch()
        layout.addLayout(stats_layout)

    def set_flightplan(self, flightplan: Flightplan, cruise_speed: float = 450):
        """Set the flightplan to display."""
        self.chart.set_flightplan(flightplan, cruise_speed)

        # Update statistics
        stats = self.chart.route_stats
        if stats:
            self.stats_labels["distance"].setText(f"距離: {stats.total_distance_nm:.1f} NM")
            self.stats_labels["time"].setText(f"時間: {stats.formatted_time}")
            self.stats_labels["legs"].setText(f"レグ: {len(stats.legs)}")

        if flightplan.cruise_altitude:
            fl = int(flightplan.cruise_altitude / 100)
            self.stats_labels["cruise"].setText(f"巡航: FL{fl}")
        else:
            self.stats_labels["cruise"].setText(f"巡航: FL{int(self.chart.cruise_altitude / 100)}")

    def clear(self):
        """Clear the display."""
        self.chart.clear()
        self.stats_labels["distance"].setText("距離: -- NM")
        self.stats_labels["time"].setText("時間: --:--")
        self.stats_labels["cruise"].setText("巡航: FL---")
        self.stats_labels["legs"].setText("レグ: --")
