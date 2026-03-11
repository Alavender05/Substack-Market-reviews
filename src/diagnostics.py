from __future__ import annotations

import socket

import requests


def dns_check(hosts: list[str]) -> list[dict]:
    results = []
    for host in hosts:
        try:
            ip = socket.getaddrinfo(host, 443)[0][4][0]
            results.append({"host": host, "ok": True, "ip": ip})
        except Exception as exc:  # pragma: no cover - environment-specific
            results.append({"host": host, "ok": False, "error": repr(exc)})
    return results


def http_check(urls: list[str], headers: dict | None = None) -> list[dict]:
    results = []
    for url in urls:
        try:
            response = requests.get(url, headers=headers, timeout=20)
            results.append(
                {
                    "url": url,
                    "ok": 200 <= response.status_code < 400,
                    "status_code": response.status_code,
                    "final_url": response.url,
                }
            )
        except Exception as exc:  # pragma: no cover - environment-specific
            results.append({"url": url, "ok": False, "error": repr(exc)})
    return results
