from src.processing.deduper import Deduper


def test_filter_new_skips_seen_urls():
    deduper = Deduper(
        {
            "https://example.com/p/known": {
                "article_id": "1",
                "content_hash": "abc",
                "first_seen": "2026-03-10T00:00:00",
                "last_seen": "2026-03-10T00:00:00"
            }
        }
    )
    candidates = [
        {"canonical_url": "https://example.com/p/known"},
        {"canonical_url": "https://example.com/p/new"}
    ]
    fresh = deduper.filter_new(candidates)
    assert fresh == [{"canonical_url": "https://example.com/p/new"}]


def test_is_seen_uses_content_hash_fallback():
    deduper = Deduper(
        {
            "https://example.com/p/known": {
                "article_id": "1",
                "content_hash": "samehash",
                "first_seen": "2026-03-10T00:00:00",
                "last_seen": "2026-03-10T00:00:00"
            }
        }
    )
    assert deduper.is_seen("https://example.com/p/other", "samehash") is True

