from __future__ import annotations

from pathlib import Path

from ..utils.file_io import read_json, write_text
from ..utils.text_cleaning import clean_whitespace

ALLOWED_STATUSES = {"completed", "partial"}
DEFAULT_INPUT_PATH = "output/latest/articles_enriched.json"
DEFAULT_OUTPUT_PATH = "output/latest/daily_digest.md"


def load_daily_batch(path: str | Path) -> dict:
    batch = read_json(path)
    if not isinstance(batch, dict):
        raise ValueError("Daily batch file must contain a JSON object.")
    if "run_date" not in batch:
        raise ValueError("Daily batch file is missing required field: run_date")
    if "articles" not in batch:
        raise ValueError("Daily batch file is missing required field: articles")
    if not isinstance(batch["articles"], list):
        raise ValueError("Daily batch field 'articles' must be a list.")
    return batch


def group_articles_by_publication(articles: list[dict]) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = {}
    for article in articles:
        publication = (
            clean_whitespace(article.get("publication") or "")
            or "Unknown Publication"
        )
        grouped.setdefault(publication, []).append(article)

    for publication, publication_articles in grouped.items():
        grouped[publication] = sorted(
            publication_articles,
            key=_article_sort_key,
            reverse=True,
        )
    return dict(sorted(grouped.items(), key=lambda item: item[0].lower()))


def build_markdown_digest(batch: dict) -> str:
    run_date = batch["run_date"]
    articles = [
        article
        for article in batch["articles"]
        if article.get("processing_status") in ALLOWED_STATUSES
    ]
    grouped_articles = group_articles_by_publication(articles)

    lines = [
        f"# Daily Substack Digest - {run_date}",
        "",
        "Generated from public Reads activity.",
        "",
    ]

    if not grouped_articles:
        lines.extend(
            [
                "No completed or partial articles were available for this run.",
                "",
            ]
        )
        return "\n".join(lines).rstrip() + "\n"

    for publication, items in grouped_articles.items():
        lines.append(f"## {publication}")
        lines.append("")
        for article in items:
            lines.extend(_render_article_block(article))
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def render_digest_from_file(
    input_path: str | Path = DEFAULT_INPUT_PATH,
    output_path: str | Path | None = DEFAULT_OUTPUT_PATH,
) -> str:
    batch = load_daily_batch(input_path)
    markdown = build_markdown_digest(batch)
    if output_path is not None:
        write_text(output_path, markdown)
    return markdown


def _render_article_block(article: dict) -> list[str]:
    title = clean_whitespace(article.get("title") or "") or "Untitled Article"
    link = article.get("canonical_url") or article.get("article_url") or "#"
    summary = clean_whitespace(article.get("summary_short") or "") or "No summary available."
    bullets = _clean_bullets(article.get("summary_bullets") or [])
    key_takeaway = clean_whitespace(article.get("key_takeaway") or "")

    lines = [
        f"### [{title}]({link})",
        "",
        summary,
        "",
    ]

    for bullet in bullets:
        lines.append(f"- {bullet}")

    if bullets:
        lines.append("")

    if key_takeaway:
        lines.append(f"**Key takeaway:** {key_takeaway}")
        lines.append("")

    return lines


def _clean_bullets(values: list[str]) -> list[str]:
    bullets = []
    for value in values:
        cleaned = clean_whitespace(value)
        if cleaned:
            bullets.append(cleaned)
    return bullets


def _article_sort_key(article: dict) -> tuple[str, str]:
    published_at = article.get("published_at") or ""
    scraped_at = article.get("scraped_at") or ""
    return (published_at, scraped_at)
