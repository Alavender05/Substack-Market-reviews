from __future__ import annotations

from pathlib import Path
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from ..models import PublicationRecord, ReadItem, ReadsDiscoveryResult
from ..utils.hashing import sha256_text
from ..utils.dates import now_utc_iso
from ..utils.file_io import write_text
from ..processing.normalizer import normalize_url


class SubstackReadsScraper:
    PRIMARY_LINK_SELECTOR = "main a[href], a[href]"
    CHALLENGE_MARKERS = (
        "just a moment",
        "cf-browser-verification",
        "challenge-platform",
        "checking your browser",
        "cloudflare",
    )
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

    def scrape_reads(self, page: object, profile_url: str, source_label: str | None = None) -> ReadsDiscoveryResult:
        target_url = self.build_reads_url(profile_url)
        discovered_at = now_utc_iso()
        self.last_debug_snapshot_path = None
        html = self.load_reads_page(page, target_url)

        if self.is_challenge_page(html):
            snapshot_path = self.debug_dir / f"{discovered_at[:10]}_reads_debug.html"
            self.save_debug_snapshot(html, snapshot_path)
            self.last_debug_snapshot_path = str(snapshot_path)
            return ReadsDiscoveryResult(
                source_profile=profile_url,
                reads_url=target_url,
                discovered_at=discovered_at,
                debug_snapshot_path=self.last_debug_snapshot_path,
            )

        direct_articles = self.extract_visible_links(page, target_url, source_label=source_label)
        publications = self.extract_publications(html, profile_url, discovered_at)
        if not direct_articles:
            direct_articles = self.extract_read_items(html, target_url, source_label=source_label)

        if not direct_articles and not publications:
            snapshot_path = self.debug_dir / f"{discovered_at[:10]}_reads_debug.html"
            self.save_debug_snapshot(html, snapshot_path)
            self.last_debug_snapshot_path = str(snapshot_path)

        return ReadsDiscoveryResult(
            source_profile=profile_url,
            reads_url=target_url,
            discovered_at=discovered_at,
            publications=publications,
            direct_articles=direct_articles,
            debug_snapshot_path=self.last_debug_snapshot_path,
        )

    def scrape(self, page: object, profile_url: str, source_label: str | None = None) -> list[ReadItem]:
        return self.scrape_reads(page, profile_url, source_label=source_label).direct_articles

    def build_reads_url(self, profile_url: str) -> str:
        normalized = profile_url.rstrip("/")
        if "/@" in normalized:
            return normalized + "/reads"
        return normalized + "/reads"

    def load_reads_page(self, page: object, reads_url: str) -> str:
        try:
            page.goto(reads_url, wait_until="domcontentloaded", timeout=15000)
            # Give client-side rendering a short extra window before reading the DOM.
            page.wait_for_timeout(1500)
            return page.content()
        except PlaywrightTimeoutError:
            try:
                return page.content()
            except Exception:
                return ""

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
                    discovered_via="reads_direct",
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
                    discovered_via="reads_direct",
                )
            )
        return items

    def extract_publications(self, html: str, profile_url: str, discovered_at: str) -> list[PublicationRecord]:
        soup = BeautifulSoup(html, "html.parser")
        publications: list[PublicationRecord] = []
        seen: set[str] = set()
        profile_netloc = urlparse(profile_url).netloc.lower()

        for anchor in soup.select(self.PRIMARY_LINK_SELECTOR):
            href = (anchor.get("href") or "").strip()
            if not href:
                continue
            absolute_url = normalize_url(urljoin(profile_url, href))
            if absolute_url in seen:
                continue
            if not self.is_candidate_publication_url(absolute_url, profile_netloc):
                continue
            seen.add(absolute_url)
            publication_name = anchor.get_text(" ", strip=True) or absolute_url
            publications.append(
                PublicationRecord(
                    publication_id=sha256_text(absolute_url)[:16],
                    publication_name=publication_name,
                    publication_url=absolute_url,
                    rss_url=absolute_url.rstrip("/") + "/feed",
                    discovered_from_profile=profile_url,
                    first_seen=discovered_at,
                    last_seen_on_reads=discovered_at,
                )
            )
        return publications

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

    def is_candidate_publication_url(self, url: str, profile_netloc: str) -> bool:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            return False
        path = parsed.path.lower()
        if "/p/" in path:
            return False
        same_netloc = parsed.netloc.lower() == profile_netloc
        if same_netloc and "/@" not in path:
            return False
        if same_netloc and path in self.EXCLUDED_EXACT_PATHS:
            return False
        if any(path.startswith(prefix) for prefix in self.EXCLUDED_PATH_PREFIXES):
            return False
        return True

    def is_challenge_page(self, html: str) -> bool:
        lowered = html.lower()
        return any(marker in lowered for marker in self.CHALLENGE_MARKERS)

    def save_debug_snapshot(self, html: str, target_path: str | Path) -> None:
        write_text(target_path, html)
