"""Tests for the PLN / FLP / RTE parsers against the sample files."""
from pathlib import Path

import pytest

from src.models import WaypointType
from src.parsers import FlpParser, PlnParser, RteParser

SAMPLES = Path(__file__).parent.parent / "samples"


def test_pln_parses_sample():
    fp = PlnParser().parse(SAMPLES / "RJTT_RJOO.pln")
    assert fp is not None
    assert fp.departure_icao == "RJTT"
    assert fp.destination_icao == "RJOO"
    assert fp.total_waypoints == 7
    assert fp.cruise_altitude == 39000

    first = fp.waypoints[0]
    assert first.ident == "CLARK"
    assert first.latitude == pytest.approx(35.4667, abs=0.001)
    assert first.longitude == pytest.approx(139.6167, abs=0.001)
    assert first.airway == "Y28"


def test_flp_parses_sample():
    fp = FlpParser().parse(SAMPLES / "EGLL_LFPG.flp")
    assert fp is not None
    assert fp.departure_icao == "EGLL"
    assert fp.destination_icao == "LFPG"
    assert fp.waypoints[0].ident == "CPT"
    assert fp.waypoints[0].longitude == pytest.approx(-0.9867, abs=0.001)


def test_rte_parses_sample():
    fp = RteParser().parse(SAMPLES / "EDDF_EDDM.rte")
    assert fp is not None
    assert fp.departure_icao == "EDDF"
    assert fp.destination_icao == "EDDM"
    assert fp.departure.waypoint_type == WaypointType.AIRPORT
    assert fp.waypoints[0].ident == "RID"
    assert fp.waypoints[0].latitude == pytest.approx(49.8667, abs=0.001)


class TestCoordinateParsing:
    """Regression tests for the DDMM.MM vs decimal-degrees ambiguity."""

    def test_rte_decimal_longitude_over_100(self):
        # 139.6167 must parse as decimal degrees, not 1° 39.6167'
        assert RteParser()._parse_coordinate("139.6167") == pytest.approx(139.6167)

    def test_flp_decimal_longitude_over_100(self):
        assert FlpParser()._parse_coordinate("139.6167") == pytest.approx(139.6167)

    def test_rte_prefixed_ddmm(self):
        # N4736.2 = 47° 36.2' = 47.6033
        assert RteParser()._parse_coordinate("N4736.2") == pytest.approx(47.6033, abs=0.001)

    def test_rte_prefixed_dddmm_west(self):
        # W12225.5 = -122° 25.5' = -122.425
        assert RteParser()._parse_coordinate("W12225.5") == pytest.approx(-122.425, abs=0.001)

    def test_negative_decimal(self):
        assert FlpParser()._parse_coordinate("-0.9867") == pytest.approx(-0.9867)


def test_parsers_return_none_for_missing_file(tmp_path):
    missing = tmp_path / "nope.pln"
    assert PlnParser().parse(missing) is None
