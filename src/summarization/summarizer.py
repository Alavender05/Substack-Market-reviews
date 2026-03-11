from __future__ import annotations

from ..config_loader import SummarizationConfig
from ..models import ArticleRecord, SummaryRecord
from ..utils.dates import now_utc_iso
from ..utils.text_cleaning import first_sentences, trim_text
from .llm_client import LLMClient
from .prompts import build_summary_prompt


class Summarizer:
    def __init__(self, config: SummarizationConfig) -> None:
        self.config = config
        self.client = LLMClient(provider=config.provider, model=config.model)

    def summarize_article(self, article: ArticleRecord) -> SummaryRecord:
        source_text = trim_text(article.body_text, self.config.max_input_chars)
        if not self.config.enabled:
            return self._fallback(article, source_text, status="disabled")

        prompt = build_summary_prompt(article.title, source_text, self.config.summary_length)
        try:
            summary_text = self.client.summarize(prompt)
            if not summary_text:
                return self._fallback(article, source_text, status="empty_response")
            bullets = self._bullets(summary_text) if self.config.include_bullets else []
            return SummaryRecord(
                article_id=article.article_id,
                canonical_url=article.canonical_url,
                summary_short=summary_text,
                summary_bullets=bullets,
                key_takeaway=self._key_takeaway(summary_text),
                summary_status="completed",
                provider=self.config.provider,
                model=self.config.model,
                created_at=now_utc_iso(),
                content_hash=article.content_hash,
            )
        except Exception:
            return self._fallback(article, source_text, status="fallback")

    def _fallback(self, article: ArticleRecord, source_text: str, status: str) -> SummaryRecord:
        summary_text = first_sentences(source_text, limit=3) or "No summary available."
        return SummaryRecord(
            article_id=article.article_id,
            canonical_url=article.canonical_url,
            summary_short=summary_text,
            summary_bullets=self._bullets(summary_text) if self.config.include_bullets else [],
            key_takeaway=self._key_takeaway(summary_text),
            summary_status=status,
            provider=self.config.provider,
            model=self.config.model,
            created_at=now_utc_iso(),
            content_hash=article.content_hash,
        )

    def _bullets(self, summary_text: str) -> list[str]:
        lines = [line.strip("- ").strip() for line in summary_text.splitlines() if line.strip()]
        if len(lines) > 1:
            return lines[:3]
        return [segment.strip() for segment in summary_text.split(". ")[:3] if segment.strip()]

    def _key_takeaway(self, summary_text: str) -> str | None:
        bullets = self._bullets(summary_text)
        if bullets:
            return bullets[0]
        return summary_text.strip() or None
