from __future__ import annotations


def classify_preflight_result(preflight: dict) -> tuple[str, str | None]:
    if preflight["core_status"] == "degraded":
        return "degraded", preflight["failure_stage"]
    return "ok", None


def classify_discovery_result(source_checks_succeeded: int, source_checks_failed: int) -> tuple[str, str | None]:
    if source_checks_succeeded == 0 and source_checks_failed > 0:
        return "degraded", "discovery"
    return "ok", None


def classify_final_run(internal_error: bool, degraded: bool) -> str:
    if internal_error:
        return "failed"
    if degraded:
        return "degraded"
    return "healthy"
