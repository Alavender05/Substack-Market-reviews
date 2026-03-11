from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass
class ReadItem:
    source_url: str
    article_url: str
    discovered_at: str
    title_hint: str | None = None
    source_label: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ArticleRecord:
    article_id: str
    source_url: str
    original_url: str
    canonical_url: str
    title: str | None
    subtitle: str | None
    author: str | None
    publication: str | None
    published_at: str | None
    description: str | None
    body_text: str
    content_hash: str
    fetch_status: str
    fetched_at: str
    topic_tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SummaryRecord:
    article_id: str
    canonical_url: str
    summary_short: str | None
    summary_bullets: list[str]
    key_takeaway: str | None
    summary_status: str
    provider: str
    model: str
    created_at: str
    content_hash: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CanonicalArticleRecord:
    article_id: str
    source_profile: str
    source_label: str | None
    article_url: str
    canonical_url: str
    title: str | None
    subtitle: str | None
    author: str | None
    publication: str | None
    published_at: str | None
    body_text: str
    summary_short: str | None
    summary_bullets: list[str]
    key_takeaway: str | None
    topic_tags: list[str]
    scraped_at: str
    run_date: str
    processing_status: str
    summary_status: str
    summary_model: str | None
    content_hash: str | None
    error_message: str | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DailyArticleBatch:
    schema_version: str
    run_id: str
    run_date: str
    source_profile: str
    generated_at: str
    article_count: int
    status: str
    articles: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RunManifest:
    run_id: str
    run_date: str
    started_at: str
    completed_at: str | None = None
    status: str = "running"
    dry_run: bool = False
    reads_discovered: int = 0
    articles_selected: int = 0
    articles_fetched: int = 0
    summaries_created: int = 0
    errors: list[str] = field(default_factory=list)

    def finish(self, status: str, completed_at: str | None = None) -> None:
        self.status = status
        self.completed_at = completed_at or datetime.now(UTC).isoformat()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
