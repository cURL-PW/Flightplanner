"""Tests for the SimBrief client (mocked API responses)."""
import io
import json
import urllib.error
from unittest.mock import MagicMock, patch

from src.simbrief import SimBriefClient

OFP_OK = {
    'fetch': {'status': 'Success'},
    'params': {'units': 'kgs', 'request_id': '1', 'time_generated': ''},
    'general': {
        'flight_number': 'ANA37', 'route': 'DCT', 'air_distance': 250,
        'initial_altitude': 39000, 'cruise_altitude': 39000,
    },
    'origin': {'icao_code': 'RJTT', 'name': 'Tokyo'},
    'destination': {'icao_code': 'RJOO', 'name': 'Osaka'},
    'alternate': {},
    'aircraft': {'icaocode': 'B788', 'name': 'B787-8', 'reg': 'JA801A'},
    'fuel': {'plan_ramp': 15000},
    'weights': {
        'pax_count': 100, 'cargo': 0, 'payload': 0,
        'est_zfw': 0, 'est_tow': 0, 'est_ldw': 0,
    },
    'times': {'est_time_enroute': '0100'},
    'navlog': {'fix': [
        {'ident': 'SPENS', 'type': 'wpt', 'pos_lat': '35.25',
         'pos_long': '139.08', 'via_airway': 'Y28'},
    ]},
    'weather': {},
}


def _mock_response(payload: dict) -> MagicMock:
    resp = MagicMock()
    resp.read.return_value = json.dumps(payload).encode()
    resp.__enter__ = lambda s: resp
    resp.__exit__ = MagicMock(return_value=False)
    return resp


def _http_error(url: str, status: str) -> urllib.error.HTTPError:
    body = json.dumps({'fetch': {'status': status}}).encode()
    return urllib.error.HTTPError(url, 400, 'Bad Request', {}, io.BytesIO(body))


def test_numeric_id_uses_userid_param():
    urls = []

    def fake(req, timeout=None):
        urls.append(req.full_url)
        return _mock_response(OFP_OK)

    with patch('urllib.request.urlopen', side_effect=fake):
        ofp = SimBriefClient('123456').fetch_latest_ofp()

    assert ofp is not None
    assert 'userid=123456' in urls[0]


def test_alias_uses_username_param():
    urls = []

    def fake(req, timeout=None):
        urls.append(req.full_url)
        return _mock_response(OFP_OK)

    with patch('urllib.request.urlopen', side_effect=fake):
        ofp = SimBriefClient('my_alias').fetch_latest_ofp()

    assert ofp is not None
    assert 'username=my_alias' in urls[0]


def test_ofp_fields_parsed():
    with patch('urllib.request.urlopen', return_value=_mock_response(OFP_OK)):
        ofp = SimBriefClient('123456').fetch_latest_ofp()

    assert ofp.departure_icao == 'RJTT'
    assert ofp.arrival_icao == 'RJOO'
    assert ofp.flight_time_minutes == 60
    assert len(ofp.waypoints) == 1
    assert ofp.waypoints[0].airway == 'Y28'


def test_ofp_to_flightplan():
    with patch('urllib.request.urlopen', return_value=_mock_response(OFP_OK)):
        client = SimBriefClient('123456')
        ofp = client.fetch_latest_ofp()

    fp = client.ofp_to_flightplan(ofp)
    assert fp.departure_icao == 'RJTT'
    assert fp.destination_icao == 'RJOO'
    assert fp.cruise_altitude == 39000


def test_unknown_userid_error_message():
    def fake(req, timeout=None):
        raise _http_error(req.full_url, 'Error: Unknown UserID')

    with patch('urllib.request.urlopen', side_effect=fake):
        client = SimBriefClient('999999')
        assert client.fetch_latest_ofp() is None

    assert 'Pilot ID' in client.last_error


def test_no_flight_plan_error_message():
    def fake(req, timeout=None):
        raise _http_error(req.full_url, 'Error: No flight plan on file for the specified user')

    with patch('urllib.request.urlopen', side_effect=fake):
        client = SimBriefClient('123456')
        assert client.fetch_latest_ofp() is None

    assert 'フライトプラン' in client.last_error


def test_empty_pilot_id():
    client = SimBriefClient('')
    assert client.fetch_latest_ofp() is None
    assert client.last_error is not None
