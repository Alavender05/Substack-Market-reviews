from __future__ import annotations

from ..diagnostics import dns_check as _dns_check
from ..diagnostics import http_check as _http_check


def dns_check(hosts: list[str] | None = None) -> list[dict[str, object]]:
    hosts = hosts or ["github.com", "substack.com"]
    results = _dns_check(hosts)
    return [
        {"host": item["host"], "dns_ok": item["ok"], **({"ip": item["ip"]} if item.get("ok") else {"error": item["error"]})}
        for item in results
    ]


def http_check(urls: list[str] | None = None) -> list[dict[str, object]]:
    urls = urls or ["https://github.com", "https://substack.com"]
    results = _http_check(urls, headers={"User-Agent": "Mozilla/5.0"})
    converted = []
    for item in results:
        converted_item = {"url": item["url"], "http_ok": item["ok"]}
        if item.get("ok"):
            converted_item["status_code"] = item["status_code"]
            converted_item["final_url"] = item["final_url"]
        else:
            converted_item["error"] = item["error"]
        converted.append(converted_item)
    return converted
