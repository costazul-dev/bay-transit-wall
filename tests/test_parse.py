from datetime import datetime, timedelta, timezone
from pathlib import Path

from transit.parse import Arrival, extract_visits, parse_arrivals, to_arrival

FIXTURE = Path(__file__).parent / "fixtures" / "stop_monitoring_sample.json"
BOM = b"\xef\xbb\xbf"
PST = timezone(timedelta(hours=-8))


def _visit(**call):
    return {
        "MonitoringRef": "00000",
        "MonitoredVehicleJourney": {"LineRef": "22", "MonitoredCall": call},
    }


def test_parse_arrivals_from_recorded_fixture():
    arrivals = parse_arrivals(FIXTURE.read_bytes())

    assert len(arrivals) == 3
    assert all(a.line == "22" and a.direction == "IB" for a in arrivals)
    assert all(a.stop_code == "00000" for a in arrivals)
    assert arrivals[0] == Arrival("22", "00000", datetime(2026, 11, 9, 19, 43, 55, tzinfo=timezone.utc), "IB")
    assert arrivals[2].expected == datetime(2026, 11, 9, 20, 1, 49, tzinfo=timezone.utc)


def test_parse_arrivals_strips_leading_bom():
    assert parse_arrivals(BOM + FIXTURE.read_bytes()) == parse_arrivals(FIXTURE.read_bytes())


def test_to_arrival_falls_back_to_aimed_time():
    arrival = to_arrival(_visit(AimedArrivalTime="2026-11-09T10:34:00-08:00"))

    assert arrival is not None
    assert arrival.expected == datetime(2026, 11, 9, 10, 34, tzinfo=PST)


def test_to_arrival_returns_none_without_times():
    assert to_arrival(_visit()) is None


def test_extract_visits_wraps_single_dict():
    visit = _visit(AimedArrivalTime="2026-11-09T10:34:00-08:00")
    payload = {"Siri": {"ServiceDelivery": {"StopMonitoringDelivery": {"MonitoredStopVisit": visit}}}}

    assert extract_visits(payload) == [visit]


def test_extract_visits_missing_key_returns_empty():
    payload = {"Siri": {"ServiceDelivery": {"StopMonitoringDelivery": {}}}}

    assert extract_visits(payload) == []


def test_extract_visits_without_siri_wrapper():
    visit = {"MonitoredVehicleJourney": {"LineRef": "22"}}
    payload = {"ServiceDelivery": {"StopMonitoringDelivery": {"MonitoredStopVisit": [visit]}}}
    assert extract_visits(payload) == [visit]


def test_to_arrival_parses_utc_z_suffix():
    visit = {
        "MonitoredVehicleJourney": {
            "LineRef": "22",
            "MonitoredCall": {"ExpectedArrivalTime": "2026-11-24T01:02:31Z"},
        }
    }
    assert to_arrival(visit).expected == datetime(2026, 11, 24, 1, 2, 31, tzinfo=timezone.utc)


def test_to_arrival_reads_direction_ref():
    visit = {
        "MonitoredVehicleJourney": {
            "LineRef": "T",
            "DirectionRef": "S",
            "MonitoredCall": {"AimedArrivalTime": "2026-11-24T01:04:00Z"},
        }
    }
    assert to_arrival(visit).direction == "S"
