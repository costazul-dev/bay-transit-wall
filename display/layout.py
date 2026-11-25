"""Build display rows (route badge + countdown text) from cached arrivals.

Pure functions: every caller passes `now`, so nothing here reads the clock.
"""

import math
from dataclasses import dataclass
from datetime import datetime

from transit.parse import Arrival


@dataclass(frozen=True)
class Row:
    line: str
    badge_color: str
    text: str
    text_color: str


def minutes_until(expected: datetime, now: datetime) -> int:
    """Whole minutes from `now` to `expected`, rounded down."""
    return math.floor((expected - now).total_seconds() / 60)


def next_minutes(
    arrivals: list[Arrival], line: str, now: datetime, limit: int = 3, direction: str | None = None
) -> list[int]:
    """Upcoming countdowns for `line`, soonest first, past arrivals dropped, at most `limit`.

    When `direction` is given, only arrivals whose `DirectionRef` matches it are counted.
    """
    minutes = (
        minutes_until(a.expected, now)
        for a in arrivals
        if a.line == line and (direction is None or a.direction == direction)
    )
    return sorted(m for m in minutes if m >= 0)[:limit]


def is_stale(last_success: datetime | None, now: datetime, max_age_seconds: float) -> bool:
    """True when there has been no successful fetch, or the last one is older than `max_age_seconds`."""
    if last_success is None:
        return True
    return (now - last_success).total_seconds() > max_age_seconds


def format_times(minutes: list[int]) -> str:
    """`"3, 11, 24"`, or `"--"` when there are no upcoming arrivals."""
    if not minutes:
        return "--"
    return ", ".join(str(m) for m in minutes)


def build_row(
    row_config: dict,
    arrivals: list[Arrival],
    last_success: datetime | None,
    now: datetime,
    max_age_seconds: float,
) -> Row:
    """One display row; text is yellow when the stop's data is stale or the line has no arrivals."""
    minutes = next_minutes(arrivals, row_config["line"], now, direction=row_config.get("direction"))
    stale = is_stale(last_success, now, max_age_seconds)
    return Row(
        line=row_config["line"],
        badge_color=row_config["color"],
        text=format_times(minutes),
        text_color="yellow" if stale or not minutes else "white",
    )


def build_rows(
    rows_config: list[dict],
    arrivals_by_stop: dict[str, list[Arrival]],
    last_success_by_stop: dict[str, datetime | None],
    now: datetime,
    max_age_seconds: float,
) -> list[Row]:
    """Build every configured row, looking up arrivals and freshness by each row's `stop_code`."""
    return [
        build_row(
            row_config,
            arrivals_by_stop.get(row_config["stop_code"], []),
            last_success_by_stop.get(row_config["stop_code"]),
            now,
            max_age_seconds,
        )
        for row_config in rows_config
    ]
