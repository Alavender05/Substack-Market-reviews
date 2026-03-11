from __future__ import annotations

from pathlib import Path

from ..config_loader import OutputConfig
from ..utils.file_io import write_json


class OutputWriter:
    def __init__(self, config: OutputConfig) -> None:
        self.config = config

    def write_latest_outputs(
        self,
        articles_enriched: dict,
        digest: dict,
        dashboard_feed: dict,
    ) -> None:
        latest_dir = Path(self.config.latest_dir)
        latest_dir.mkdir(parents=True, exist_ok=True)
        write_json(latest_dir / self.config.articles_file, articles_enriched)
        write_json(latest_dir / self.config.digest_file, digest)
        write_json(latest_dir / self.config.dashboard_file, dashboard_feed)

    def write_archive_outputs(
        self,
        run_date: str,
        articles_enriched: dict,
        digest: dict,
        dashboard_feed: dict,
    ) -> None:
        archive_dir = Path(self.config.archive_dir) / run_date
        archive_dir.mkdir(parents=True, exist_ok=True)
        write_json(archive_dir / self.config.articles_file, articles_enriched)
        write_json(archive_dir / self.config.digest_file, digest)
        write_json(archive_dir / self.config.dashboard_file, dashboard_feed)
