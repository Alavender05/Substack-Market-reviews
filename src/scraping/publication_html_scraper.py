from __future__ import annotations

from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from ..config_loader import AppConfig
from ..models import PublicationRecord, ReadItem
from ..processing.normalizer import normalize_url
from ..utils.dates import now_utc_iso


class PublicationHtmlScraper:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": config.fetching.user_agent})

    def fetch_posts(self, publication: PublicationRecord) -> list[ReadItem]:
        response = self.session.get(
            publication.publication_url,
            timeout=self.config.fetching.request_timeout_seconds,
        )
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        items: list[ReadItem] = []
        seen: set[str] = set()

        for anchor in soup.select("main a[href], article a[href], a[href]"):
            href = (anchor.get("href") or "").strip()
            if not href:
                continue
            absolute_url = normalize_url(urljoin(publication.publication_url, href))
            if "/p/" not in absolute_url or absolute_url in seen:
                continue
            seen.add(absolute_url)
            items.append(
                ReadItem(
                    source_url=publication.publication_url,
                    article_url=absolute_url,
                    discovered_at=now_utc_iso(),
                    title_hint=anchor.get_text(" ", strip=True) or None,
                    source_label=publication.publication_name,
                    discovered_via="publication_html",
                )
            )
            if len(items) >= self.config.monitoring.max_posts_per_publication_per_run:
                break
        return items
