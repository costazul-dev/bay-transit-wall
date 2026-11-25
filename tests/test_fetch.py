import pytest
import requests

from transit.fetch import StopMonitoringError, fetch_interval_seconds, get_stop_monitoring

API_KEY = "secret-test-key-123"
LEAKY_URL = f"https://api.511.org/transit/StopMonitoring?api_key={API_KEY}&agency=SF&stopCode=00000"


def test_fetch_interval_for_three_stops_at_fifty_per_hour():
    assert fetch_interval_seconds(3, 50) == 216


def test_fetch_interval_for_one_stop_at_sixty_per_hour():
    assert fetch_interval_seconds(1, 60) == 60


def unauthorized_response():
    response = requests.Response()
    response.status_code = 401
    response.reason = "Unauthorized"
    response.url = LEAKY_URL
    return response


def test_http_error_message_omits_api_key(monkeypatch):
    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: unauthorized_response())
    with pytest.raises(StopMonitoringError) as excinfo:
        get_stop_monitoring(API_KEY, "SF", "00000")
    assert API_KEY not in str(excinfo.value)
    assert "401" in str(excinfo.value)
    assert "00000" in str(excinfo.value)
    assert excinfo.value.__cause__ is None
    assert excinfo.value.__suppress_context__


def test_connection_error_message_omits_api_key(monkeypatch):
    def raise_connection_error(*args, **kwargs):
        raise requests.ConnectionError(f"Max retries exceeded with url: {LEAKY_URL}")

    monkeypatch.setattr(requests, "get", raise_connection_error)
    with pytest.raises(StopMonitoringError) as excinfo:
        get_stop_monitoring(API_KEY, "SF", "00000")
    assert API_KEY not in str(excinfo.value)
    assert "ConnectionError" in str(excinfo.value)
    assert excinfo.value.__cause__ is None
    assert excinfo.value.__suppress_context__
