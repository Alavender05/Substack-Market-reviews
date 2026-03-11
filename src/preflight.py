from __future__ import annotations

from .config_loader import AppConfig
from .diagnostics import dns_check, http_check


def run_preflight(config: AppConfig) -> dict:
    dns_results = dns_check(config.preflight.dns_hosts)
    http_results = http_check(config.preflight.http_urls, headers=config.preflight.headers)

    dns_failures = [item for item in dns_results if not item["ok"]]
    http_failures = [item for item in http_results if not item["ok"]]

    if dns_failures:
        core_status = "degraded"
        failure_stage = "preflight_dns"
    elif http_failures:
        core_status = "degraded"
        failure_stage = "preflight_http"
    else:
        core_status = "ok"
        failure_stage = None

    return {
        "dns_checks": dns_results,
        "http_checks": http_results,
        "core_status": core_status,
        "failure_stage": failure_stage,
    }
