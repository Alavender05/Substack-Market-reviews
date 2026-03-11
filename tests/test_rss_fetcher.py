from pathlib import Path

from src.models import PublicationRecord
from src.config_loader import load_config
from src.scraping.rss_fetcher import RSSFetcher


def test_rss_fetcher_parses_feed_fixture():
    feed_xml = Path("tests/fixtures/sample_feed.xml").read_text(encoding="utf-8")
    fetcher = RSSFetcher(load_config("tests/fixtures/sample_config.json"))
    publication = PublicationRecord(
        publication_id="pub123",
        publication_name="Macro Notes",
        publication_url="https://marketnotes.substack.com/",
        rss_url="https://marketnotes.substack.com/feed",
        discovered_from_profile="https://substack.com/@aleclavender",
        first_seen="2026-03-11T00:00:00+00:00",
        last_seen_on_reads="2026-03-11T00:00:00+00:00",
    )

    items = fetcher.parse_feed(feed_xml, publication, limit=3)

    assert len(items) == 2
    assert items[0].article_url == "https://marketnotes.substack.com/p/fed-signals-patience"
    assert items[0].discovered_via == "publication_rss"
