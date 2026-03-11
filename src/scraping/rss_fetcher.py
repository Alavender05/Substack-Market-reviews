from __future__ import annotations

import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime

import requests

from ..config_loader import AppConfig
from ..models import PublicationRecord, ReadItem
from ..processing.normalizer import normalize_url
from ..utils.dates import now_utc_iso


class RSSFetcher:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": config.fetching.user_agent})

    def fetch_posts(self, publication: PublicationRecord) -> list[ReadItem]:
        response = self.session.get(
            publication.rss_url,
            timeout=self.config.fetching.request_timeout_seconds,
        )
        response.raise_for_status()
        return self.parse_feed(
            response.text,
            publication=publication,
            limit=self.config.monitoring.max_posts_per_publication_per_run,
        )

    def parse_feed(self, xml_text: str, publication: PublicationRecord, limit: int = 5) -> list[ReadItem]:
        root = ET.fromstring(xml_text)
        items = []
        entries = root.findall(".//item") or root.findall(".//{http://www.w3.org/2005/Atom}entry")
        for entry in entries[:limit]:
            title = _text(entry, "title")
            link = _entry_link(entry)
            if not link:
                continue
            published = _text(entry, "pubDate") or _text(entry, "published") or now_utc_iso()
            try:
                published = parsedate_to_datetime(published).isoformat()
            except Exception:
                published = published
            items.append(
                ReadItem(
                    source_url=publication.publication_url,
                    article_url=normalize_url(link),
                    discovered_at=published,
                    title_hint=title,
                    source_label=publication.publication_name,
                    discovered_via="publication_rss",
                )
            )
        return items


def _text(node: ET.Element, tag_name: str) -> str | None:
    for child in list(node):
        tag = child.tag.split("}")[-1]
        if tag == tag_name and child.text:
            return child.text.strip()
    return None


def _entry_link(node: ET.Element) -> str | None:
    for child in list(node):
        tag = child.tag.split("}")[-1]
        if tag == "link":
            href = child.attrib.get("href")
            if href:
                return href.strip()
            if child.text:
                return child.text.strip()
    return None
