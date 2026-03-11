from __future__ import annotations

from pathlib import Path

import requests

from ..config_loader import AppConfig
from ..utils.file_io import write_text


class ArticleFetcher:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": config.fetching.user_agent})

    def fetch(self, url: str) -> str:
        timeout = self.config.fetching.request_timeout_seconds
        response = self.session.get(url, timeout=timeout)
        response.raise_for_status()
        return response.text

    def save_raw_html(self, article_id: str, html: str, run_date: str) -> str:
        raw_path = Path("data/raw/articles") / f"{run_date}_{article_id}.html"
        write_text(raw_path, html)
        return str(raw_path)

