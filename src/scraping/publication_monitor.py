from __future__ import annotations

from ..config_loader import AppConfig
from ..models import PublicationRecord, ReadItem
from ..scraping.publication_html_scraper import PublicationHtmlScraper
from ..scraping.rss_fetcher import RSSFetcher


class PublicationMonitor:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.rss_fetcher = RSSFetcher(config)
        self.html_scraper = PublicationHtmlScraper(config)

    def fetch_recent_posts(self, publication: PublicationRecord) -> tuple[list[ReadItem], str]:
        if self.config.monitoring.rss_enabled:
            try:
                return self.rss_fetcher.fetch_posts(publication), "rss"
            except Exception:
                if not self.config.monitoring.html_fallback_enabled:
                    raise

        if self.config.monitoring.html_fallback_enabled:
            return self.html_scraper.fetch_posts(publication), "html_fallback"

        return [], "disabled"
