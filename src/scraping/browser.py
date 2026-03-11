from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator


@contextmanager
def browser_page(user_agent: str | None = None) -> Iterator[object]:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(user_agent=user_agent)
        page = context.new_page()
        try:
            yield page
        finally:
            context.close()
            browser.close()

