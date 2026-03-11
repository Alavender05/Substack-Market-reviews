from __future__ import annotations

from pathlib import Path
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from ..models import ReadItem
from ..utils.dates import now_utc_iso
from ..utils.file_io import write_text
from ..processing.normalizer import normalize_url


class SubstackReadsScraper:
    PRIMARY_LINK_SELECTOR = "main a[href], a[href]"
    EXCLUDED_PATH_PREFIXES = (
        "/publish",
        "/api",
        "/account",
        "/signin",
        "/subscribe",
        "/search",
        "/feed",
    )
    EXCLUDED_EXACT_PATHS = {"/", "/archive", "/about", "/reads"}
    EXCLUDED_URL_PARTS = ("/likes", "/notes", "/podcast", "#", "?output=")

    def __init__(self, wait_until: str = "networkidle", debug_dir: str = "data/raw/reads") -> None:
        self.wait_until = wait_until
        self.debug_dir = Path(debug_dir)
        self.last_debug_snapshot_path: str | None = None

    def scrape(self, page: object, profile_url: str, source_label: str | None = None) -> list[ReadItem]:
        # Reset the previous debug path so each run reports only its own snapshot.
        target_url = self.build_reads_url(profile_url)
        self.last_debug_snapshot_path = None
        self.load_reads_page(page, target_url)

        # Use Playwright's live DOM first so we only collect links that are actually rendered.
        items = self.extract_visible_links(page, target_url, source_label=source_label)
        if items:
            return items

        # Fall back to rendered HTML parsing in case locator-based extraction misses the markup.
        html = page.content()
        fallback_items = self.extract_read_items(html, target_url, source_label=source_label)
        if fallback_items:
            return fallback_items

        # Save the final rendered page for debugging when no candidate links can be found.
        snapshot_path = self.debug_dir / f"{now_utc_iso()[:10]}_reads_debug.html"
        self.save_debug_snapshot(html, snapshot_path)
        self.last_debug_snapshot_path = str(snapshot_path)
        return []

    def build_reads_url(self, profile_url: str) -> str:
        return profile_url.rstrip("/") + "/reads"

    def load_reads_page(self, page: object, reads_url: str) -> None:
        page.goto(reads_url, wait_until=self.wait_until)
        # Give late client-side rendering a short extra window before reading the DOM.
        page.wait_for_timeout(1500)

    def extract_visible_links(
        self,
        page: object,
        source_url: str,
        source_label: str | None = None,
    ) -> list[ReadItem]:
        items: list[ReadItem] = []
        seen: set[str] = set()
        locator = page.locator(self.PRIMARY_LINK_SELECTOR)

        for index in range(locator.count()):
            anchor = locator.nth(index)
            if not anchor.is_visible():
                continue

            href = (anchor.get_attribute("href") or "").strip()
            if not href or href.startswith("#"):
                continue

            # Normalize URLs before filtering so deduplication is stable across tracking params.
            absolute_url = urljoin(source_url, href)
            normalized_url = normalize_url(absolute_url)
            if not self.is_candidate_article_url(normalized_url):
                continue
            if normalized_url in seen:
                continue

            seen.add(normalized_url)
            title_hint = anchor.inner_text().strip() or None
            items.append(
                ReadItem(
                    source_url=source_url,
                    article_url=normalized_url,
                    discovered_at=now_utc_iso(),
                    title_hint=title_hint,
                    source_label=source_label,
                )
            )
        return items

    def extract_read_items(
        self,
        html: str,
        source_url: str,
        source_label: str | None = None,
    ) -> list[ReadItem]:
        soup = BeautifulSoup(html, "html.parser")
        items: list[ReadItem] = []
        seen: set[str] = set()

        for anchor in soup.select(self.PRIMARY_LINK_SELECTOR):
            href = anchor.get("href", "").strip()
            if not href or href.startswith("#"):
                continue
            absolute_url = normalize_url(urljoin(source_url, href))
            if not self.is_candidate_article_url(absolute_url):
                continue
            if absolute_url in seen:
                continue
            seen.add(absolute_url)
            items.append(
                ReadItem(
                    source_url=source_url,
                    article_url=absolute_url,
                    discovered_at=now_utc_iso(),
                    title_hint=anchor.get_text(" ", strip=True) or None,
                    source_label=source_label,
                )
            )
        return items

    def is_candidate_article_url(self, url: str) -> bool:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            return False

        path = parsed.path.lower()
        if path in self.EXCLUDED_EXACT_PATHS:
            return False
        if any(path.startswith(prefix) for prefix in self.EXCLUDED_PATH_PREFIXES):
            return False
        if any(part in url.lower() for part in self.EXCLUDED_URL_PARTS):
            return False
        if "/p/" in path:
            return True
        return path.count("/") >= 2 and len(path.rsplit("/", 1)[-1]) > 1

    def save_debug_snapshot(self, html: str, target_path: str | Path) -> None:
        write_text(target_path, html)
