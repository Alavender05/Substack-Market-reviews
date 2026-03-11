from src.tools.network_checks import dns_check, http_check


def test_dns_check_uses_requested_hosts(monkeypatch):
    def fake_getaddrinfo(host, port):
        return [(None, None, None, None, ("203.0.113.10", port))]

    monkeypatch.setattr("socket.getaddrinfo", fake_getaddrinfo)

    results = dns_check(["example.com"])

    assert results == [{"host": "example.com", "dns_ok": True, "ip": "203.0.113.10"}]


def test_http_check_returns_error_shape(monkeypatch):
    def fake_get(url, timeout, headers):
        raise RuntimeError("network down")

    monkeypatch.setattr("requests.get", fake_get)

    results = http_check(["https://example.com"])

    assert results[0]["url"] == "https://example.com"
    assert results[0]["http_ok"] is False
    assert "RuntimeError" in results[0]["error"]
