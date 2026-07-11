"""Round-trip tests: export a flightplan and re-parse it in each format."""
from pathlib import Path

import pytest

from src.exporters import export_flp, export_pln, export_rte
from src.parsers import FlpParser, PlnParser, RteParser

SAMPLES = Path(__file__).parent.parent / "samples"

ROUND_TRIPS = [
    ("pln", export_pln, PlnParser),
    ("flp", export_flp, FlpParser),
    ("rte", export_rte, RteParser),
]


@pytest.fixture
def source_flightplan():
    return PlnParser().parse(SAMPLES / "RJTT_RJOO.pln")


@pytest.mark.parametrize("ext,exporter,parser_cls", ROUND_TRIPS)
def test_round_trip(tmp_path, source_flightplan, ext, exporter, parser_cls):
    out = tmp_path / f"out.{ext}"
    assert exporter(source_flightplan, out) is True
    assert out.exists()

    reparsed = parser_cls().parse(out)
    assert reparsed is not None
    assert reparsed.departure_icao == source_flightplan.departure_icao
    assert reparsed.destination_icao == source_flightplan.destination_icao
    assert reparsed.total_waypoints == source_flightplan.total_waypoints

    # Coordinates survive the round trip (skip 0,0 placeholders such as
    # FLP airports, which carry no coordinates by format design)
    original = {w.ident: w for w in source_flightplan.all_waypoints()}
    for wpt in reparsed.all_waypoints():
        src = original.get(wpt.ident)
        if src and src.latitude != 0 and wpt.latitude != 0:
            assert wpt.latitude == pytest.approx(src.latitude, abs=0.01), wpt.ident
            assert wpt.longitude == pytest.approx(src.longitude, abs=0.01), wpt.ident


def test_pln_export_writes_dms(tmp_path, source_flightplan):
    out = tmp_path / "out.pln"
    export_pln(source_flightplan, out)
    content = out.read_text(encoding="utf-8")
    assert "<DepartureID>RJTT</DepartureID>" in content
    assert "N35°" in content  # DMS coordinate format
    assert "<ATCAirway>Y28</ATCAirway>" in content


def test_export_failure_returns_false(source_flightplan):
    bad_path = Path("/nonexistent-dir/out.pln")
    assert export_pln(source_flightplan, bad_path) is False
