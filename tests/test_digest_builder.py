from src.models import CanonicalArticleRecord
from src.outputs.digest_builder import build_dashboard_feed, build_daily_articles_batch, build_digest


def test_build_digest_and_dashboard_feed():
    article = CanonicalArticleRecord(
        article_id="article123",
        source_profile="https://example.substack.com",
        source_label="Example",
        article_url="https://news.example.com/p/market-review",
        canonical_url="https://news.example.com/p/market-review",
        title="Market Review",
        subtitle="A short review.",
        author="Jane Smith",
        publication="Macro Notes",
        published_at="2026-03-10T12:00:00Z",
        body_text="Body text",
        summary_short="A concise summary.",
        summary_bullets=["Point one", "Point two"],
        key_takeaway="Point one",
        topic_tags=["macro"],
        scraped_at="2026-03-11T00:00:00",
        run_date="2026-03-11",
        processing_status="completed",
        summary_status="completed",
        summary_model="gpt-4.1-mini",
        content_hash="hash123",
        error_message=None,
    )
    digest = build_digest([article])
    dashboard = build_dashboard_feed([article])
    daily_batch = build_daily_articles_batch(
        canonical_records=[article],
        run_id="20260311T000000",
        run_date="2026-03-11",
        source_profile="https://example.substack.com",
        status="completed",
    )
    assert digest["article_count"] == 1
    assert digest["items"][0]["summary_short"] == "A concise summary."
    assert dashboard["items"][0]["summary_status"] == "completed"
    assert daily_batch["articles"][0]["key_takeaway"] == "Point one"
