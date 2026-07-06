"""Weather (METAR/TAF) fetching from aviationweather.gov (NOAA, no API key)."""
import json
import threading
import urllib.request
import urllib.parse
from dataclasses import dataclass, field
from typing import Optional

from PyQt6.QtCore import QObject, pyqtSignal


AWC_METAR_URL = "https://aviationweather.gov/api/data/metar"
AWC_TAF_URL = "https://aviationweather.gov/api/data/taf"
REQUEST_TIMEOUT = 10  # seconds


@dataclass
class MetarReport:
    """A decoded METAR report."""
    icao: str
    raw_text: str = ""
    flight_category: str = ""   # VFR / MVFR / IFR / LIFR
    temperature_c: Optional[float] = None
    dewpoint_c: Optional[float] = None
    wind_dir_deg: Optional[int] = None
    wind_speed_kts: Optional[int] = None
    wind_gust_kts: Optional[int] = None
    visibility: Optional[str] = None
    altimeter_hpa: Optional[float] = None
    observation_time: str = ""

    @property
    def wind_display(self) -> str:
        """Human-readable wind string, e.g. 320° 12kt (G 20kt)."""
        if self.wind_speed_kts is None:
            return "---"
        if not self.wind_speed_kts:
            return "Calm"
        direction = f"{self.wind_dir_deg:03d}°" if self.wind_dir_deg else "VRB"
        text = f"{direction} {self.wind_speed_kts}kt"
        if self.wind_gust_kts:
            text += f" (G {self.wind_gust_kts}kt)"
        return text


def fetch_metars(icao_codes: list[str]) -> dict[str, MetarReport]:
    """Fetch METARs for the given airports from aviationweather.gov.

    Returns a dict keyed by ICAO code. Missing stations are omitted.
    Raises on network errors so the caller can report them.
    """
    codes = [c.strip().upper() for c in icao_codes if c and c != '----']
    if not codes:
        return {}

    params = urllib.parse.urlencode({
        'ids': ','.join(codes),
        'format': 'json',
    })
    url = f"{AWC_METAR_URL}?{params}"

    request = urllib.request.Request(
        url, headers={'User-Agent': 'MSFS-Flightplan-Viewer/1.3'}
    )
    with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT) as response:
        data = json.loads(response.read().decode('utf-8'))

    reports: dict[str, MetarReport] = {}
    for item in data:
        icao = item.get('icaoId', '')
        if not icao:
            continue

        wind_dir = item.get('wdir')
        report = MetarReport(
            icao=icao,
            raw_text=item.get('rawOb', ''),
            temperature_c=item.get('temp'),
            dewpoint_c=item.get('dewp'),
            wind_dir_deg=wind_dir if isinstance(wind_dir, int) else None,
            wind_speed_kts=item.get('wspd'),
            wind_gust_kts=item.get('wgst'),
            visibility=str(item.get('visib', '')) or None,
            altimeter_hpa=item.get('altim'),
            observation_time=item.get('reportTime', ''),
        )

        # Derive flight category if not provided
        report.flight_category = item.get('fltCat') or _derive_flight_category(item)
        reports[icao] = report

    return reports


def _derive_flight_category(item: dict) -> str:
    """Rough flight category from ceiling/visibility when API omits it."""
    try:
        visib = item.get('visib')
        if isinstance(visib, str):
            visib = float(visib.rstrip('+'))
        ceiling = None
        for cloud in item.get('clouds', []):
            if cloud.get('cover') in ('BKN', 'OVC') and cloud.get('base'):
                base = cloud['base']
                ceiling = base if ceiling is None else min(ceiling, base)

        if (ceiling is not None and ceiling < 500) or (visib is not None and visib < 1):
            return 'LIFR'
        if (ceiling is not None and ceiling < 1000) or (visib is not None and visib < 3):
            return 'IFR'
        if (ceiling is not None and ceiling < 3000) or (visib is not None and visib < 5):
            return 'MVFR'
        return 'VFR'
    except Exception:
        return ''


class WeatherFetcher(QObject):
    """Fetches METARs in a background thread and reports via Qt signals."""

    fetched = pyqtSignal(dict)    # dict[str, MetarReport]
    error = pyqtSignal(str)

    def fetch_async(self, icao_codes: list[str]):
        """Start a background fetch. Results arrive via signals."""
        thread = threading.Thread(
            target=self._worker, args=(list(icao_codes),), daemon=True
        )
        thread.start()

    def _worker(self, icao_codes: list[str]):
        try:
            reports = fetch_metars(icao_codes)
            self.fetched.emit(reports)
        except Exception as e:
            self.error.emit(str(e))
