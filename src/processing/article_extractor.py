from __future__ import annotations

from ..models import ArticleRecord, ReadItem
from ..utils.dates import now_utc_iso
from ..utils.hashing import sha256_text
from .normalizer import normalize_text, normalize_url


def build_article_record(read_item: ReadItem, parsed_article: dict[str, str | None]) -> ArticleRecord:
    canonical_url = normalize_url(parsed_article.get("canonical_url") or read_item.article_url)
    body_text = normalize_text(parsed_article.get("body_text")) or ""
    article_id = sha256_text(canonical_url)[:16]
    content_hash = sha256_text(body_text)

    return ArticleRecord(
        article_id=article_id,
        source_url=read_item.source_url,
        original_url=normalize_url(read_item.article_url),
        canonical_url=canonical_url,
        title=normalize_text(parsed_article.get("title")) or read_item.title_hint,
        subtitle=normalize_text(parsed_article.get("subtitle")) or normalize_text(parsed_article.get("description")),
        author=normalize_text(parsed_article.get("author")),
        publication=normalize_text(parsed_article.get("publication")),
        published_at=normalize_text(parsed_article.get("published_at")),
        description=normalize_text(parsed_article.get("description")),
        body_text=body_text,
        topic_tags=parsed_article.get("topic_tags") or [],
        content_hash=content_hash,
        fetch_status="fetched" if body_text else "partial",
        fetched_at=now_utc_iso(),
        metadata={"source_label": read_item.source_label},
    )
