from __future__ import annotations

from ..models import (
    ArticleRecord,
    CanonicalArticleRecord,
    DailyArticleBatch,
    ReadItem,
    RunManifest,
    SummaryRecord,
)


def serialize_reads(items: list[ReadItem]) -> list[dict]:
    return [item.to_dict() for item in items]


def serialize_articles(items: list[ArticleRecord]) -> list[dict]:
    return [item.to_dict() for item in items]


def serialize_summaries(items: list[SummaryRecord]) -> list[dict]:
    return [item.to_dict() for item in items]


def serialize_canonical_records(items: list[CanonicalArticleRecord]) -> list[dict]:
    return [item.to_dict() for item in items]


def serialize_daily_batch(batch: DailyArticleBatch) -> dict:
    return batch.to_dict()


def serialize_manifest(manifest: RunManifest) -> dict:
    return manifest.to_dict()
