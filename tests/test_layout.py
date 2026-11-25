from datetime import datetime, timedelta, timezone

from display.layout import (
    Row,
    build_row,
    build_rows,
    format_times,
    is_stale,
    minutes_until,
    next_minutes,
)
from transit.parse import Arrival

NOW = datetime(2026, 11, 9, 8, 0, 0, tzinfo=timezone(timedelta(hours=-8)))
ROW_22 = {"line": "22", "stop_code": "11111", "color": "blue"}
MAX_AGE = 432  # 2 * fetch_interval_seconds(3, 50)


def arrival(line: str, minutes: float, stop_code: str = "11111") -> Arrival:
    return Arrival(line=line, stop_code=stop_code, expected=NOW + timedelta(minutes=minutes))


def test_minutes_until_rounds_down():
    assert minutes_until(NOW + timedelta(minutes=3, seconds=59), NOW) == 3


def test_minutes_until_exact_minute():
    assert minutes_until(NOW + timedelta(minutes=11), NOW) == 11


def test_next_minutes_filters_by_line_drops_past_sorts_and_caps():
    arrivals = [
        arrival("22", 24),
        arrival("14", 2),
        arrival("22", -1),
        arrival("22", 3),
        arrival("22", 30),
        arrival("22", 11),
    ]
    assert next_minutes(arrivals, "22", NOW) == [3, 11, 24]


def test_next_minutes_respects_limit():
    arrivals = [arrival("22", 3), arrival("22", 11), arrival("22", 24)]
    assert next_minutes(arrivals, "22", NOW, limit=2) == [3, 11]


def test_next_minutes_keeps_arriving_now():
    assert next_minutes([arrival("22", 0.5)], "22", NOW) == [0]


def test_is_stale_when_never_fetched():
    assert is_stale(None, NOW, MAX_AGE)


def test_is_stale_false_when_fresh():
    assert not is_stale(NOW - timedelta(seconds=60), NOW, MAX_AGE)


def test_is_stale_true_when_expired():
    assert is_stale(NOW - timedelta(seconds=MAX_AGE + 1), NOW, MAX_AGE)


def test_format_times_populated():
    assert format_times([3, 11, 24]) == "3, 11, 24"


def test_format_times_empty():
    assert format_times([]) == "--"


def test_build_row_fresh_data_is_white():
    row = build_row(ROW_22, [arrival("22", 3), arrival("22", 11)], NOW, NOW, MAX_AGE)
    assert row == Row(line="22", badge_color="blue", text="3, 11", text_color="white")


def test_build_row_stale_data_is_yellow():
    last_success = NOW - timedelta(seconds=MAX_AGE + 1)
    row = build_row(ROW_22, [arrival("22", 3)], last_success, NOW, MAX_AGE)
    assert row.text == "3"
    assert row.text_color == "yellow"


def test_build_row_no_arrivals_is_yellow_dashes():
    row = build_row(ROW_22, [arrival("14", 3)], NOW, NOW, MAX_AGE)
    assert row.text == "--"
    assert row.text_color == "yellow"


def test_build_rows_maps_each_row_to_its_stop():
    rows_config = [ROW_22, {"line": "T", "stop_code": "22222", "color": "red"}]
    arrivals_by_stop = {"11111": [arrival("22", 5)]}
    last_success_by_stop = {"11111": NOW, "22222": None}
    rows = build_rows(rows_config, arrivals_by_stop, last_success_by_stop, NOW, MAX_AGE)
    assert rows == [
        Row(line="22", badge_color="blue", text="5", text_color="white"),
        Row(line="T", badge_color="red", text="--", text_color="yellow"),
    ]


def t_arrival(direction: str, minutes: float) -> Arrival:
    return Arrival(line="T", stop_code="00000", expected=NOW + timedelta(minutes=minutes), direction=direction)


def test_next_minutes_filters_by_direction():
    arrivals = [t_arrival("N", 2), t_arrival("S", 4), t_arrival("N", 9), t_arrival("S", 14)]
    assert next_minutes(arrivals, "T", NOW, direction="S") == [4, 14]


def test_next_minutes_without_direction_keeps_both():
    arrivals = [t_arrival("N", 2), t_arrival("S", 4)]
    assert next_minutes(arrivals, "T", NOW) == [2, 4]


def test_build_row_uses_configured_direction():
    row_config = {"line": "T", "stop_code": "00000", "color": "red", "direction": "S"}
    row = build_row(row_config, [t_arrival("N", 2), t_arrival("S", 6)], NOW, NOW, MAX_AGE)
    assert row.text == "6"
