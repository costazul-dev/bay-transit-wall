"""Fetch 511 SIRI StopMonitoring responses for a single stop.

Endpoint and parameters: 511 spec section 2.10. Every call passes a stop code;
omitting it returns the whole agency and can take more than 5-7 seconds.
"""

import requests

STOP_MONITORING_URL = "https://api.511.org/transit/StopMonitoring"


class StopMonitoringError(Exception):
    """A failed StopMonitoring request; the message never contains the request URL or API key."""


def get_stop_monitoring(api_key: str, agency: str, stop_code: str, timeout: float = 10) -> bytes:
    """Return the raw response body for one stop; BOM handling lives in `transit/parse.py`.

    Raises `StopMonitoringError` on the documented 401, 404 and 500 responses and on
    connection or timeout failures. The original `requests` exception is not chained,
    because its message includes the full URL with `api_key`.
    """
    try:
        response = requests.get(
            STOP_MONITORING_URL,
            params={"api_key": api_key, "agency": agency, "stopCode": stop_code, "format": "json"},
            timeout=timeout,
        )
        response.raise_for_status()
    except requests.RequestException as error:
        status = getattr(error.response, "status_code", None)
        detail = f"HTTP {status}" if status is not None else type(error).__name__
        raise StopMonitoringError(f"StopMonitoring request failed for stop {stop_code}: {detail}") from None
    return response.content


def fetch_interval_seconds(stop_count: int, max_requests_per_hour: int) -> float:
    """Seconds between polling rounds so `stop_count` calls per round stay under the hourly cap."""
    return 3600 * stop_count / max_requests_per_hour
