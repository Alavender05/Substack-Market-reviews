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
                "article_id": _field(article, "article_id"),
                "title": _field(article, "title"),
                "canonical_url": _field(article, "canonical_url"),
                "publication": _field(article, "publication"),
                "published_at": _field(article, "published_at"),
                "summary_short": _field(article, "summary_short"),
                "summary_bullets": _field(article, "summary_bullets"),
                "key_takeaway": _field(article, "key_takeaway"),
                "processing_status": _field(article, "processing_status"),
                "data_freshness": _field(article, "data_freshness"),
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
                "id": _field(article, "article_id"),
                "title": _field(article, "title"),
                "url": _field(article, "canonical_url"),
                "publication": _field(article, "publication"),
                "author": _field(article, "author"),
                "summary": _field(article, "summary_short"),
                "summary_status": _field(article, "summary_status"),
                "scraped_at": _field(article, "scraped_at"),
                "processing_status": _field(article, "processing_status"),
                "topic_tags": _field(article, "topic_tags"),
                "data_freshness": _field(article, "data_freshness"),
            }
        )
    return {
        "generated_at": now_utc_iso(),
        "items": items,
    }


def _field(article, name: str):
    if isinstance(article, dict):
        return article.get(name)
    return getattr(article, name, None)
