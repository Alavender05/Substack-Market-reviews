from __future__ import annotations

import re


def clean_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def trim_text(text: str, max_chars: int) -> str:
    cleaned = clean_whitespace(text)
    if len(cleaned) <= max_chars:
        return cleaned
    return cleaned[:max_chars].rsplit(" ", 1)[0].strip()


def first_sentences(text: str, limit: int = 3) -> str:
    parts = re.split(r"(?<=[.!?])\s+", clean_whitespace(text))
    return " ".join(parts[:limit]).strip()

