from __future__ import annotations

from ..models import CanonicalArticleRecord, DailyArticleBatch
from ..utils.dates import now_utc_iso


def build_daily_articles_batch(
    canonical_records: list[CanonicalArticleRecord],
    run_id: str,
    run_date: str,
    source_profile: str,
    status: str,
) -> dict:
    batch = DailyArticleBatch(
        schema_version="1.0",
        run_id=run_id,
        run_date=run_date,
        source_profile=source_profile,
        generated_at=now_utc_iso(),
        article_count=len(canonical_records),
        status=status,
        articles=[item.to_dict() for item in canonical_records],
    )
    return batch.to_dict()


def build_digest(canonical_records: list[CanonicalArticleRecord]) -> dict:
    items = []
    for article in canonical_records:
        items.append(
            {
                "article_id": article.article_id,
                "title": article.title,
                "canonical_url": article.canonical_url,
                "publication": article.publication,
                "published_at": article.published_at,
                "summary_short": article.summary_short,
                "summary_bullets": article.summary_bullets,
                "key_takeaway": article.key_takeaway,
                "processing_status": article.processing_status,
            }
        )
    return {
        "generated_at": now_utc_iso(),
        "article_count": len(items),
        "items": items,
    }


def build_dashboard_feed(canonical_records: list[CanonicalArticleRecord]) -> dict:
    items = []
    for article in canonical_records:
        items.append(
            {
                "id": article.article_id,
                "title": article.title,
                "url": article.canonical_url,
                "publication": article.publication,
                "author": article.author,
                "summary": article.summary_short,
                "summary_status": article.summary_status,
                "scraped_at": article.scraped_at,
                "processing_status": article.processing_status,
                "topic_tags": article.topic_tags,
            }
        )
    return {
        "generated_at": now_utc_iso(),
        "items": items,
    }
