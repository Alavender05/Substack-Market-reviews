from __future__ import annotations

from copy import deepcopy

from .utils.file_io import read_json, write_json


def should_promote_to_latest(run_state: dict, article_count: int) -> bool:
    return run_state["run_status"] == "healthy"


def preserve_last_successful_output() -> bool:
    return True


def write_latest_articles_if_allowed(
    run_state: dict,
    articles_payload: dict,
    latest_path: str,
    latest_successful_path: str,
) -> bool:
    write_json(latest_path, articles_payload)
    if should_promote_to_latest(run_state, len(articles_payload.get("articles", []))):
        write_json(latest_successful_path, articles_payload)
        return True
    return False


def prepare_articles_payload(run_id: str, run_status: str, articles: list[dict], freshness: str) -> dict:
    prepared_articles = []
    for article in articles:
        prepared = deepcopy(article)
        prepared["data_freshness"] = freshness
        prepared_articles.append(prepared)
    return {
        "run_id": run_id,
        "run_status": run_status,
        "articles": prepared_articles,
    }


def load_display_payload(run_state: dict, latest_path: str, latest_successful_path: str) -> tuple[dict, str | None]:
    latest_payload = read_json(latest_path, default={"run_id": run_state["run_id"], "run_status": run_state["run_status"], "articles": []}) or {
        "run_id": run_state["run_id"],
        "run_status": run_state["run_status"],
        "articles": [],
    }
    latest_successful_payload = read_json(
        latest_successful_path,
        default={"run_id": run_state["run_id"], "run_status": "healthy", "articles": []},
    ) or {"run_id": run_state["run_id"], "run_status": "healthy", "articles": []}

    if run_state["run_status"] == "healthy" or latest_payload.get("articles"):
        return latest_payload, None

    if run_state["run_status"] == "degraded" and not latest_payload.get("articles"):
        fallback_payload = prepare_articles_payload(
            latest_successful_payload.get("run_id", run_state["run_id"]),
            run_state["run_status"],
            latest_successful_payload.get("articles", []),
            "last_successful_fallback",
        )
        return fallback_payload, "Current monitoring run degraded. Displaying last successful dataset."

    return latest_payload, None
