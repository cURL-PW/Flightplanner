"""Map widget for displaying flightplan routes using Leaflet.js."""
import json
import tempfile
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt, pyqtSignal, QUrl
from PyQt6.QtWebEngineCore import QWebEngineSettings
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import QWidget, QVBoxLayout

from .models import Flightplan, Waypoint, WaypointType


class MapWidget(QWidget):
    """Widget for displaying flightplan routes on an interactive map."""

    waypoint_clicked = pyqtSignal(object)  # Emits Waypoint when clicked

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_flightplan: Optional[Flightplan] = None
        self._temp_file: Optional[Path] = None

        self._setup_ui()

    def _setup_ui(self):
        """Set up the map widget UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.web_view = QWebEngineView()
        # Allow file:// pages to load remote CDN resources (Leaflet.js)
        self.web_view.settings().setAttribute(
            QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True
        )
        layout.addWidget(self.web_view)

        # Load initial empty map
        self._load_empty_map()

    def _load_empty_map(self):
        """Load an empty map centered on the world."""
        self._load_map_html(self._generate_map_html())

    def _load_map_html(self, html: str):
        """Load HTML content into the web view."""
        # Write to temp file for proper loading
        if self._temp_file and self._temp_file.exists():
            self._temp_file.unlink()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
            f.write(html)
            self._temp_file = Path(f.name)

        self.web_view.setUrl(QUrl.fromLocalFile(str(self._temp_file)))

    def display_flightplan(self, flightplan: Flightplan):
        """Display a flightplan on the map."""
        self.current_flightplan = flightplan
        html = self._generate_map_html(flightplan)
        self._load_map_html(html)

    def clear_map(self):
        """Clear the map and show empty state."""
        self.current_flightplan = None
        self._load_empty_map()

    def _generate_map_html(self, flightplan: Optional[Flightplan] = None) -> str:
        """Generate HTML with Leaflet.js map."""

        # Prepare waypoint data
        waypoints_js = "[]"
        route_coords_js = "[]"
        center_lat = 45.0
        center_lon = 0.0
        zoom = 2

        if flightplan:
            all_wpts = flightplan.all_waypoints()
            if all_wpts:
                # Calculate center
                lats = [w.latitude for w in all_wpts if w.latitude != 0]
                lons = [w.longitude for w in all_wpts if w.longitude != 0]

                if lats and lons:
                    center_lat = sum(lats) / len(lats)
                    center_lon = sum(lons) / len(lons)

                    # Calculate appropriate zoom level
                    lat_range = max(lats) - min(lats)
                    lon_range = max(lons) - min(lons)
                    max_range = max(lat_range, lon_range)

                    if max_range < 1:
                        zoom = 10
                    elif max_range < 5:
                        zoom = 7
                    elif max_range < 10:
                        zoom = 6
                    elif max_range < 20:
                        zoom = 5
                    elif max_range < 50:
                        zoom = 4
                    else:
                        zoom = 3

                # Prepare waypoint data for JavaScript
                waypoints_data = []
                for i, wpt in enumerate(all_wpts):
                    waypoints_data.append({
                        'index': i,
                        'ident': wpt.ident,
                        'lat': wpt.latitude,
                        'lon': wpt.longitude,
                        'type': wpt.waypoint_type.value,
                        'altitude': wpt.altitude,
                        'airway': wpt.airway,
                        'region': wpt.region,
                        'isFirst': i == 0,
                        'isLast': i == len(all_wpts) - 1
                    })

                waypoints_js = json.dumps(waypoints_data)

                # Route coordinates
                route_coords = [[w.latitude, w.longitude] for w in all_wpts
                               if w.latitude != 0 and w.longitude != 0]
                route_coords_js = json.dumps(route_coords)

        html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MSFS Flightplan Viewer</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        html, body {{ height: 100%; width: 100%; }}
        #map {{ height: 100%; width: 100%; }}

        .waypoint-label {{
            background: rgba(0, 0, 0, 0.75);
            color: white;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 11px;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-weight: bold;
            white-space: nowrap;
            border: 1px solid #444;
        }}

        .waypoint-label.airport {{
            background: rgba(0, 100, 0, 0.85);
            border-color: #0f0;
        }}

        .waypoint-label.vor {{
            background: rgba(0, 0, 150, 0.85);
            border-color: #00f;
        }}

        .waypoint-label.ndb {{
            background: rgba(150, 0, 150, 0.85);
            border-color: #f0f;
        }}

        .waypoint-label.fix {{
            background: rgba(100, 100, 0, 0.85);
            border-color: #ff0;
        }}

        .info-panel {{
            position: absolute;
            top: 10px;
            right: 10px;
            background: rgba(255, 255, 255, 0.95);
            padding: 10px 15px;
            border-radius: 5px;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 12px;
            z-index: 1000;
            box-shadow: 0 2px 10px rgba(0,0,0,0.3);
            max-width: 300px;
        }}

        .info-panel h3 {{
            margin: 0 0 8px 0;
            font-size: 14px;
            border-bottom: 1px solid #ccc;
            padding-bottom: 5px;
        }}

        .info-panel .route {{
            color: #666;
            margin-bottom: 5px;
        }}

        .legend {{
            position: absolute;
            bottom: 30px;
            left: 10px;
            background: rgba(255, 255, 255, 0.95);
            padding: 8px 12px;
            border-radius: 5px;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 11px;
            z-index: 1000;
            box-shadow: 0 2px 10px rgba(0,0,0,0.3);
        }}

        .legend-item {{
            display: flex;
            align-items: center;
            margin: 3px 0;
        }}

        .legend-color {{
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 6px;
            border: 2px solid;
        }}
    </style>
</head>
<body>
    <div id="map"></div>

    <script>
        // Initialize map
        var map = L.map('map', {{
            zoomControl: true,
            attributionControl: true
        }}).setView([{center_lat}, {center_lon}], {zoom});

        // Add tile layers
        var osmLayer = L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
            attribution: '&copy; OpenStreetMap contributors',
            maxZoom: 19
        }});

        var esriLayer = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{{z}}/{{y}}/{{x}}', {{
            attribution: '&copy; Esri',
            maxZoom: 18
        }});

        var cartoLayer = L.tileLayer('https://{{s}}.basemaps.cartocdn.com/dark_all/{{z}}/{{x}}/{{y}}{{r}}.png', {{
            attribution: '&copy; CartoDB',
            maxZoom: 19
        }});

        // Default layer
        cartoLayer.addTo(map);

        // Layer control
        var baseMaps = {{
            "Dark": cartoLayer,
            "Streets": osmLayer,
            "Satellite": esriLayer
        }};
        L.control.layers(baseMaps).addTo(map);

        // Waypoint data
        var waypoints = {waypoints_js};
        var routeCoords = {route_coords_js};

        // Waypoint type colors and styles
        var typeStyles = {{
            'airport': {{ color: '#00ff00', fillColor: '#004400', radius: 8 }},
            'vor': {{ color: '#0088ff', fillColor: '#002266', radius: 6 }},
            'ndb': {{ color: '#ff00ff', fillColor: '#440044', radius: 5 }},
            'fix': {{ color: '#ffff00', fillColor: '#444400', radius: 4 }},
            'user': {{ color: '#ff8800', fillColor: '#442200', radius: 4 }},
            'runway': {{ color: '#00ffff', fillColor: '#004444', radius: 5 }},
            'unknown': {{ color: '#888888', fillColor: '#222222', radius: 4 }}
        }};

        // Draw route line
        if (routeCoords.length > 1) {{
            var routeLine = L.polyline(routeCoords, {{
                color: '#00aaff',
                weight: 3,
                opacity: 0.8,
                dashArray: null
            }}).addTo(map);

            // Add directional arrows
            var arrowHead = L.polyline(routeCoords, {{
                color: '#00aaff',
                weight: 2,
                opacity: 0.6
            }});
        }}

        // Add waypoint markers
        waypoints.forEach(function(wpt, index) {{
            if (wpt.lat === 0 && wpt.lon === 0) return;

            var style = typeStyles[wpt.type] || typeStyles['unknown'];

            // Larger markers for airports
            var radius = style.radius;
            if (wpt.isFirst || wpt.isLast) {{
                radius = 10;
            }}

            // Create marker
            var marker = L.circleMarker([wpt.lat, wpt.lon], {{
                radius: radius,
                color: style.color,
                fillColor: style.fillColor,
                fillOpacity: 0.8,
                weight: 2
            }}).addTo(map);

            // Create label
            var labelClass = 'waypoint-label ' + wpt.type;
            var labelContent = wpt.ident;
            if (wpt.airway) {{
                labelContent = wpt.airway + ' > ' + wpt.ident;
            }}

            var label = L.divIcon({{
                className: labelClass,
                html: labelContent,
                iconSize: null,
                iconAnchor: [-5, 10]
            }});

            L.marker([wpt.lat, wpt.lon], {{
                icon: label,
                interactive: false
            }}).addTo(map);

            // Popup with waypoint info
            var popupContent = '<strong>' + wpt.ident + '</strong><br>';
            popupContent += 'Type: ' + wpt.type.toUpperCase() + '<br>';
            popupContent += 'Position: ' + wpt.lat.toFixed(4) + ', ' + wpt.lon.toFixed(4);
            if (wpt.altitude) {{
                popupContent += '<br>Altitude: FL' + Math.round(wpt.altitude / 100);
            }}
            if (wpt.airway) {{
                popupContent += '<br>Via: ' + wpt.airway;
            }}
            if (wpt.region) {{
                popupContent += '<br>Region: ' + wpt.region;
            }}

            marker.bindPopup(popupContent);
        }});

        // Fit bounds to show all waypoints
        if (routeCoords.length > 0) {{
            map.fitBounds(routeCoords, {{ padding: [50, 50] }});
        }}

        // Add info panel if we have a flightplan
        if (waypoints.length > 0) {{
            var infoPanel = L.control({{ position: 'topright' }});
            infoPanel.onAdd = function(map) {{
                var div = L.DomUtil.create('div', 'info-panel');
                var departure = waypoints.find(w => w.isFirst);
                var destination = waypoints.find(w => w.isLast);

                div.innerHTML = '<h3>Flight Plan</h3>';
                if (departure && destination) {{
                    div.innerHTML += '<div class="route">' + departure.ident + ' → ' + destination.ident + '</div>';
                }}
                div.innerHTML += '<div>Waypoints: ' + waypoints.length + '</div>';

                return div;
            }};
            infoPanel.addTo(map);

            // Add legend
            var legend = L.control({{ position: 'bottomleft' }});
            legend.onAdd = function(map) {{
                var div = L.DomUtil.create('div', 'legend');
                div.innerHTML = '<strong>Legend</strong>';
                div.innerHTML += '<div class="legend-item"><span class="legend-color" style="background:#004400;border-color:#0f0"></span>Airport</div>';
                div.innerHTML += '<div class="legend-item"><span class="legend-color" style="background:#002266;border-color:#08f"></span>VOR</div>';
                div.innerHTML += '<div class="legend-item"><span class="legend-color" style="background:#440044;border-color:#f0f"></span>NDB</div>';
                div.innerHTML += '<div class="legend-item"><span class="legend-color" style="background:#444400;border-color:#ff0"></span>FIX</div>';
                return div;
            }};
            legend.addTo(map);
        }}
    </script>
</body>
</html>'''

        return html

    def cleanup(self):
        """Clean up temporary files."""
        if self._temp_file and self._temp_file.exists():
            try:
                self._temp_file.unlink()
            except Exception:
                pass
