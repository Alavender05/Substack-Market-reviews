import json
from types import SimpleNamespace

from src.main import main
from src.utils.file_io import read_json


def test_main_short_circuits_on_preflight_dns_failure(tmp_path, monkeypatch):
    latest_status_path = tmp_path / "latest_run_status.json"
    connectivity_path = tmp_path / "connectivity_report.json"
    latest_articles_path = tmp_path / "latest_articles.json"
    latest_successful_path = tmp_path / "latest_successful_articles.json"
    latest_successful_path.write_text(
        json.dumps({"run_id": "old", "run_status": "healthy", "articles": [{"title": "Old"}]}),
        encoding="utf-8",
    )

    config = SimpleNamespace(
        logging=SimpleNamespace(level="INFO", log_to_file=False, log_dir=str(tmp_path), json_logs=False),
        output=SimpleNamespace(
            latest_dir=str(tmp_path / "output" / "latest"),
            archive_dir=str(tmp_path / "output" / "archive"),
            articles_file="articles_enriched.json",
            digest_file="daily_digest.json",
            dashboard_file="dashboard_feed.json",
        ),
        profile=SimpleNamespace(substack_profile_url="https://substack.com/@aleclavender"),
        pipeline=SimpleNamespace(daily_run_timezone="UTC"),
        monitoring=SimpleNamespace(publications_registry_path=str(tmp_path / "registry_state.json"), publication_expiry_days=30),
    )

    monkeypatch.setattr("src.main.parse_args", lambda: SimpleNamespace(config="x", sources="y", dry_run=False))
    monkeypatch.setattr("src.main.load_config", lambda path: config)
    monkeypatch.setattr("src.main.load_sources", lambda path: SimpleNamespace(sources=[]))
    monkeypatch.setattr("src.main.setup_logger", lambda cfg: SimpleNamespace(info=lambda *a, **k: None, exception=lambda *a, **k: None))
    monkeypatch.setattr(
        "src.main.run_preflight",
        lambda cfg: {"dns_checks": [{"host": "substack.com", "ok": False, "error": "dns fail"}], "http_checks": [], "core_status": "degraded", "failure_stage": "preflight_dns"},
    )

    def fake_write_json(path, payload):
        path = str(path)
        if path == "data/latest_run_status.json":
            path = str(latest_status_path)
        elif path == "data/connectivity_report.json":
            path = str(connectivity_path)
        elif path == "data/latest_articles.json":
            path = str(latest_articles_path)
        elif path == "data/latest_successful_articles.json":
            path = str(latest_successful_path)
        elif path == "data/registry.json":
            path = str(tmp_path / "registry.json")
        from src.utils.file_io import write_json as real_write_json

        real_write_json(path, payload)

    def fake_read_json(path, default=None):
        path = str(path)
        if path == "data/latest_articles.json":
            path = str(latest_articles_path)
        elif path == "data/latest_successful_articles.json":
            path = str(latest_successful_path)
        elif path == str(tmp_path / "registry_state.json"):
            return {"schema_version": "1.0", "updated_at": None, "publications": {}}
        return read_json(path, default=default)

    monkeypatch.setattr("src.main.write_json", fake_write_json)
    monkeypatch.setattr("src.output_guard.write_json", fake_write_json)
    monkeypatch.setattr("src.output_guard.read_json", fake_read_json)
    monkeypatch.setattr("src.processing.publication_registry.read_json", fake_read_json)
    monkeypatch.setattr("src.main.write_run_state", lambda run_state: fake_write_json("data/latest_run_status.json", run_state))

    main()

    latest_status = read_json(latest_status_path)
    latest_articles = read_json(latest_articles_path)

    assert latest_status["run_status"] == "degraded"
    assert latest_status["failure_stage"] == "preflight_dns"
    assert latest_articles["articles"] == []
