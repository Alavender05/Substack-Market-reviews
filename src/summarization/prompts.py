from __future__ import annotations


def build_summary_prompt(article_title: str | None, article_text: str, summary_length: str) -> str:
    title = article_title or "Untitled article"
    return (
        f"Summarize the following article in a {summary_length} format. "
        "Return plain text only.\n\n"
        f"Title: {title}\n\n"
        f"Article:\n{article_text}"
    )

