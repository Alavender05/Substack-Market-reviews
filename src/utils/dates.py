from __future__ import annotations

from datetime import UTC, datetime
from zoneinfo import ZoneInfo


def now_utc_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def run_date(timezone_name: str = "UTC") -> str:
    zone = ZoneInfo(timezone_name)
    return datetime.now(zone).strftime("%Y-%m-%d")


def run_id(timezone_name: str = "UTC") -> str:
    zone = ZoneInfo(timezone_name)
    return datetime.now(zone).strftime("%Y%m%dT%H%M%S")
