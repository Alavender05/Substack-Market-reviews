from src.processing.normalizer import normalize_text, normalize_url


def test_normalize_url_strips_query_and_trailing_slash():
    result = normalize_url("HTTPS://Example.com/p/test-post/?utm_source=feed")
    assert result == "https://example.com/p/test-post"


def test_normalize_text_collapses_whitespace():
    assert normalize_text("  Alpha \n\n Beta   ") == "Alpha Beta"

