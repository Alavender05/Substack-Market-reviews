from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from .utils.file_io import write_json


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def init_run_state() -> dict:
    now = utc_now()
    return {
        "run_id": now,
        "started_at": now,
        "finished_at": None,
        "run_status": "running",
        "failure_stage": None,
        "completed": False,
        "article_count": 0,
        "source_checks_attempted": 0,
        "source_checks_succeeded": 0,
        "source_checks_failed": 0,
        "preserved_last_successful_output": False,
        "warnings": [],
        "errors": [],
    }


def set_run_status(run_state: dict, status: str, failure_stage: str | None = None) -> dict:
    run_state["run_status"] = status
    run_state["failure_stage"] = failure_stage
    return run_state


def finalize_run_state(run_state: dict) -> dict:
    run_state["finished_at"] = utc_now()
    run_state["completed"] = True
    return run_state


def write_run_state(run_state: dict, latest_path: str = "data/latest_run_status.json") -> None:
    write_json(latest_path, run_state)
    history_dir = Path("data/run_history")
    history_dir.mkdir(parents=True, exist_ok=True)
    write_json(history_dir / f"{run_state['run_id'].replace(':', '-')}.json", run_state)
