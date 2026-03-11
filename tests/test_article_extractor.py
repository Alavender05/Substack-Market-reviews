from pathlib import Path

from src.models import ReadItem
from src.processing.article_extractor import build_article_record
from src.scraping.html_parser import ArticleHtmlParser


def test_build_article_record_from_fixture():
    html = Path("tests/fixtures/sample_article_page.html").read_text(encoding="utf-8")
    parser = ArticleHtmlParser()
    parsed = parser.parse(html, "https://news.example.com/p/market-review")
    record = build_article_record(
        ReadItem(
            source_url="https://example.substack.com/reads",
            article_url="https://news.example.com/p/market-review",
            discovered_at="2026-03-11T00:00:00",
            title_hint="Market Review"
        ),
        parsed,
    )
    assert record.canonical_url == "https://news.example.com/p/market-review"
    assert record.title == "Market Review"
    assert record.subtitle == "A short review of the latest market moves."
    assert "Federal Reserve" in record.body_text
    assert len(record.article_id) == 16
