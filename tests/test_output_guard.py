from src.output_guard import load_display_payload, prepare_articles_payload, write_latest_articles_if_allowed
from src.utils.file_io import read_json


def test_write_latest_articles_only_promotes_healthy(tmp_path):
    latest_path = tmp_path / "latest_articles.json"
    latest_successful_path = tmp_path / "latest_successful_articles.json"
    run_state = {"run_status": "degraded"}
    payload = prepare_articles_payload("run-1", "degraded", [], "current")

    promoted = write_latest_articles_if_allowed(run_state, payload, str(latest_path), str(latest_successful_path))

    assert promoted is False
    assert read_json(latest_path)["run_status"] == "degraded"
    assert not latest_successful_path.exists()


def test_load_display_payload_uses_last_successful_on_degraded_empty(tmp_path):
    latest_path = tmp_path / "latest_articles.json"
    latest_successful_path = tmp_path / "latest_successful_articles.json"
    latest_path.write_text('{"run_id":"run-2","run_status":"degraded","articles":[]}', encoding="utf-8")
    latest_successful_path.write_text(
        '{"run_id":"run-1","run_status":"healthy","articles":[{"title":"Saved article"}]}',
        encoding="utf-8",
    )

    payload, banner = load_display_payload({"run_id": "run-2", "run_status": "degraded"}, str(latest_path), str(latest_successful_path))

    assert banner is not None
    assert payload["articles"][0]["data_freshness"] == "last_successful_fallback"
