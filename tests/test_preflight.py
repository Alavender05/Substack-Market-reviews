from src.config_loader import load_config
from src.preflight import run_preflight


def test_run_preflight_dns_failure(monkeypatch):
    config = load_config("tests/fixtures/sample_config.json")
    monkeypatch.setattr(
        "src.preflight.dns_check",
        lambda hosts: [{"host": host, "ok": False, "error": "dns failed"} for host in hosts],
    )
    monkeypatch.setattr(
        "src.preflight.http_check",
        lambda urls, headers=None: [{"url": url, "ok": True, "status_code": 200, "final_url": url} for url in urls],
    )

    result = run_preflight(config)

    assert result["core_status"] == "degraded"
    assert result["failure_stage"] == "preflight_dns"


def test_run_preflight_success(monkeypatch):
    config = load_config("tests/fixtures/sample_config.json")
    monkeypatch.setattr(
        "src.preflight.dns_check",
        lambda hosts: [{"host": host, "ok": True, "ip": "203.0.113.10"} for host in hosts],
    )
    monkeypatch.setattr(
        "src.preflight.http_check",
        lambda urls, headers=None: [{"url": url, "ok": True, "status_code": 200, "final_url": url} for url in urls],
    )

    result = run_preflight(config)

    assert result["core_status"] == "ok"
    assert result["failure_stage"] is None
