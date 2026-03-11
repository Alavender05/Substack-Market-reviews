from __future__ import annotations

from typing import Any


class Deduper:
    def __init__(self, seen_articles: dict[str, Any] | None = None) -> None:
        self.seen_articles = seen_articles or {}

    def is_seen(self, canonical_url: str, content_hash: str | None = None) -> bool:
        if canonical_url in self.seen_articles:
            return True
        if content_hash is None:
            return False
        return any(
            entry.get("content_hash") == content_hash
            for entry in self.seen_articles.values()
            if isinstance(entry, dict)
        )

    def filter_new(
        self,
        candidates: list[dict[str, Any]],
        skip_existing: bool = True,
        fallback_to_content_hash: bool = True,
    ) -> list[dict[str, Any]]:
        fresh: list[dict[str, Any]] = []
        for candidate in candidates:
            canonical_url = candidate.get("canonical_url") or candidate.get("article_url")
            content_hash = candidate.get("content_hash") if fallback_to_content_hash else None
            seen = self.is_seen(canonical_url, content_hash)
            if skip_existing and seen:
                continue
            fresh.append(candidate)
        return fresh

    def remember(self, canonical_url: str, article_id: str, content_hash: str, seen_at: str) -> None:
        self.seen_articles[canonical_url] = {
            "article_id": article_id,
            "content_hash": content_hash,
            "first_seen": self.seen_articles.get(canonical_url, {}).get("first_seen", seen_at),
            "last_seen": seen_at,
        }

