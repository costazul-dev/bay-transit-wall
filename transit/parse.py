"""Parse 511 SIRI StopMonitoring responses into arrivals.

Response shape (511 spec section 2.10; live responses omit the spec's `Siri` wrapper):
ServiceDelivery.StopMonitoringDelivery.MonitoredStopVisit[].MonitoredVehicleJourney
"""

import json
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Arrival:
    line: str
    stop_code: str
    expected: datetime
    direction: str = ""


def decode_response(raw: bytes) -> dict:
    """Decode a 511 response body; `utf-8-sig` strips the leading BOM 511 sends."""
    return json.loads(raw.decode("utf-8-sig"))


def extract_visits(payload: dict) -> list[dict]:
    """Return the MonitoredStopVisit entries as a list (single objects are wrapped).

    Live 511 responses start at `ServiceDelivery`; the spec's Appendix B.1.10 example
    wraps it in `Siri`, so both shapes are accepted.
    """
    root = payload.get("Siri", payload)
    visits = (
        root.get("ServiceDelivery", {})
        .get("StopMonitoringDelivery", {})
        .get("MonitoredStopVisit")
    )
    if visits is None:
        return []
    if isinstance(visits, dict):
        return [visits]
    return visits


def to_arrival(visit: dict) -> Arrival | None:
    """Build an Arrival from one visit, preferring ExpectedArrivalTime over AimedArrivalTime."""
    journey = visit.get("MonitoredVehicleJourney", {})
    call = journey.get("MonitoredCall", {})
    time_str = call.get("ExpectedArrivalTime") or call.get("AimedArrivalTime")
    if not time_str:
        return None
    return Arrival(
        line=journey.get("LineRef", ""),
        stop_code=visit.get("MonitoringRef", ""),
        expected=datetime.fromisoformat(time_str),
        direction=journey.get("DirectionRef", ""),
    )


def parse_arrivals(raw: bytes) -> list[Arrival]:
    """Parse a raw StopMonitoring response into arrivals for every line at the stop."""
    arrivals = (to_arrival(v) for v in extract_visits(decode_response(raw)))
    return [a for a in arrivals if a is not None]
