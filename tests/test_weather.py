"""Tests for the METAR client (mocked API responses)."""
import json
from unittest.mock import MagicMock, patch

from src.weather import MetarReport, fetch_metars

SAMPLE = [
    {
        'icaoId': 'RJTT',
        'rawOb': 'RJTT 060830Z 32012G20KT 9999 FEW030 28/21 Q1012 NOSIG',
        'temp': 28.0, 'dewp': 21.0, 'wdir': 320, 'wspd': 12, 'wgst': 20,
        'visib': '6+', 'altim': 1012.0, 'reportTime': '2026-07-06 08:30:00',
        'fltCat': None, 'clouds': [{'cover': 'FEW', 'base': 3000}],
    },
    {
        'icaoId': 'RJOO',
        'rawOb': 'RJOO 060830Z 27005KT 4000 BR BKN008 24/23 Q1010',
        'temp': 24.0, 'dewp': 23.0, 'wdir': 270, 'wspd': 5, 'wgst': None,
        'visib': '2.5', 'altim': 1010.0, 'reportTime': '2026-07-06 08:30:00',
        'fltCat': None, 'clouds': [{'cover': 'BKN', 'base': 800}],
    },
]


def _mock_response(payload) -> MagicMock:
    resp = MagicMock()
    resp.read.return_value = json.dumps(payload).encode()
    resp.__enter__ = lambda s: resp
    resp.__exit__ = MagicMock(return_value=False)
    return resp


def test_fetch_and_decode():
    with patch('urllib.request.urlopen', return_value=_mock_response(SAMPLE)):
        reports = fetch_metars(['RJTT', 'RJOO'])

    assert set(reports) == {'RJTT', 'RJOO'}
    rjtt = reports['RJTT']
    assert rjtt.temperature_c == 28.0
    assert rjtt.altimeter_hpa == 1012.0
    assert rjtt.wind_display == '320° 12kt (G 20kt)'


def test_flight_category_derivation():
    with patch('urllib.request.urlopen', return_value=_mock_response(SAMPLE)):
        reports = fetch_metars(['RJTT', 'RJOO'])

    assert reports['RJTT'].flight_category == 'VFR'
    assert reports['RJOO'].flight_category == 'IFR'  # 800 ft ceiling


def test_empty_input_makes_no_request():
    with patch('urllib.request.urlopen') as mock:
        assert fetch_metars([]) == {}
        assert fetch_metars(['----', '']) == {}
    mock.assert_not_called()


def test_wind_display_calm():
    assert MetarReport(icao='X', wind_speed_kts=0).wind_display == 'Calm'


def test_wind_display_unknown():
    assert MetarReport(icao='X').wind_display == '---'
