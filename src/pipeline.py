from __future__ import annotations

import logging
from pathlib import Path

from .config_loader import AppConfig, SourcesConfig
from .models import CanonicalArticleRecord, RunManifest
from .outputs.digest_builder import build_daily_articles_batch, build_dashboard_feed, build_digest
from .outputs.writers import OutputWriter
from .processing.article_extractor import build_article_record
from .processing.deduper import Deduper
from .processing.normalizer import normalize_url
from .processing.serializer import (
    serialize_canonical_records,
    serialize_manifest,
    serialize_reads,
    serialize_summaries,
)
from .scraping.article_fetcher import ArticleFetcher
from .scraping.browser import browser_page
from .scraping.html_parser import ArticleHtmlParser
from .scraping.substack_reads_scraper import SubstackReadsScraper
from .summarization.summarizer import Summarizer
from .utils.dates import now_utc_iso, run_date, run_id
from .utils.file_io import read_json, write_json
from .utils.hashing import sha256_text


class Pipeline:
    def __init__(self, config: AppConfig, sources: SourcesConfig, logger: logging.Logger) -> None:
        self.config = config
        self.sources = sources
        self.logger = logger
        self.reads_scraper = SubstackReadsScraper(wait_until=config.fetching.browser_wait_until)
        self.article_fetcher = ArticleFetcher(config)
        self.article_parser = ArticleHtmlParser()
        self.summarizer = Summarizer(config.summarization)
        self.output_writer = OutputWriter(config.output)

    def run(self, dry_run: bool = False) -> dict:
        current_run_date = run_date(self.config.pipeline.daily_run_timezone)
        manifest = RunManifest(
            run_id=run_id(self.config.pipeline.daily_run_timezone),
            run_date=current_run_date,
            started_at=now_utc_iso(),
            dry_run=dry_run,
        )

        seen_articles = read_json(self.config.deduplication.seen_articles_path, default={}) or {}
        deduper = Deduper(seen_articles=seen_articles)

        reads = self._collect_reads()
        manifest.reads_discovered = len(reads)
        write_json(Path("data/raw/reads") / f"{current_run_date}.json", serialize_reads(reads))

        read_candidates = [
            {
                "article_url": normalize_url(item.article_url),
                "canonical_url": normalize_url(item.article_url),
                "source_url": item.source_url,
                "title_hint": item.title_hint,
                "source_label": item.source_label,
                "read_item": item,
            }
            for item in reads
        ]

        fresh_candidates = deduper.filter_new(
            read_candidates,
            skip_existing=self.config.deduplication.skip_existing_articles,
            fallback_to_content_hash=False,
        )
        fresh_candidates = fresh_candidates[: self.config.pipeline.article_fetch_limit_per_run]
        manifest.articles_selected = len(fresh_candidates)

        articles = []
        summaries = []
        canonical_records: list[CanonicalArticleRecord] = []
        source_profile = str(self.config.profile.substack_profile_url)

        for candidate in fresh_candidates:
            read_item = candidate["read_item"]
            try:
                html = self.article_fetcher.fetch(read_item.article_url)
                manifest.articles_fetched += 1
                if self.config.pipeline.save_raw_html and not dry_run:
                    self.article_fetcher.save_raw_html(candidate["canonical_url"].split("/")[-1], html, current_run_date)

                parsed = self.article_parser.parse(html, read_item.article_url)
                article = build_article_record(read_item, parsed)
                articles.append(article)

                if self.config.deduplication.enabled and deduper.is_seen(
                    article.canonical_url,
                    article.content_hash if self.config.deduplication.fallback_to_content_hash else None,
                ):
                    self.logger.info("Skipping duplicate article after fetch: %s", article.canonical_url)
                    continue

                summary = self.summarizer.summarize_article(article)
                summaries.append(summary)
                manifest.summaries_created += 1

                canonical_records.append(
                    self._build_canonical_record(
                        article=article,
                        summary=summary,
                        source_profile=source_profile,
                        run_date=current_run_date,
                    )
                )
                deduper.remember(article.canonical_url, article.article_id, article.content_hash, article.fetched_at)
            except Exception as exc:
                error = f"{read_item.article_url}: {exc}"
                self.logger.exception("Failed processing article")
                manifest.errors.append(error)
                canonical_records.append(
                    self._build_failed_canonical_record(
                        read_item=read_item,
                        source_profile=source_profile,
                        run_date=current_run_date,
                        error_message=str(exc),
                    )
                )

        daily_articles = build_daily_articles_batch(
            canonical_records=canonical_records,
            run_id=manifest.run_id,
            run_date=current_run_date,
            source_profile=source_profile,
            status="completed" if not manifest.errors else "completed_with_errors",
        )
        digest = build_digest(canonical_records)
        dashboard_feed = build_dashboard_feed(canonical_records)

        if not dry_run:
            self._write_processed_outputs(
                current_run_date=current_run_date,
                manifest=manifest,
                deduper=deduper,
                articles=articles,
                summaries=summaries,
                canonical_records=canonical_records,
                daily_articles=daily_articles,
                digest=digest,
                dashboard_feed=dashboard_feed,
            )

        manifest.finish("completed" if not manifest.errors else "completed_with_errors", now_utc_iso())
        if not dry_run:
            self._write_manifest_and_state(current_run_date, manifest, deduper)
        return manifest.to_dict()

    def _collect_reads(self):
        if not self.config.profile.reads_enabled:
            self.logger.info("Reads scraping disabled in config.")
            return []

        source_label = None
        if self.sources.sources:
            source_label = self.sources.sources[0].label

        with browser_page(user_agent=self.config.fetching.user_agent) as page:
            reads = self.reads_scraper.scrape(
                page,
                str(self.config.profile.substack_profile_url),
                source_label=source_label,
            )
        if not reads and self.reads_scraper.last_debug_snapshot_path:
            self.logger.warning(
                "No reads links found. Saved debug snapshot to %s",
                self.reads_scraper.last_debug_snapshot_path,
            )
        self.logger.info("Discovered %s read links", len(reads))
        return reads

    def _write_processed_outputs(
        self,
        current_run_date: str,
        manifest: RunManifest,
        deduper: Deduper,
        articles,
        summaries,
        canonical_records,
        daily_articles,
        digest,
        dashboard_feed,
    ) -> None:
        write_json(Path("data/processed/articles") / f"{current_run_date}.json", daily_articles)
        write_json(Path("data/processed/summaries") / f"{current_run_date}.json", serialize_summaries(summaries))

        index_path = Path("data/processed/indexes/articles_index.json")
        prior_index = read_json(index_path, default=[]) or []
        merged_index = {item["article_id"]: item for item in prior_index}
        for item in serialize_canonical_records(canonical_records):
            merged_index[item["article_id"]] = item
        write_json(index_path, list(merged_index.values()))

        self.output_writer.write_latest_outputs(daily_articles, digest, dashboard_feed)
        self.output_writer.write_archive_outputs(current_run_date, daily_articles, digest, dashboard_feed)

    def _write_manifest_and_state(self, current_run_date: str, manifest: RunManifest, deduper: Deduper) -> None:
        write_json(Path("data/raw/runs") / f"{current_run_date}.json", serialize_manifest(manifest))
        write_json(self.config.deduplication.seen_articles_path, deduper.seen_articles)

        run_history_path = Path("data/state/run_history.json")
        history = read_json(run_history_path, default=[]) or []
        history.append(serialize_manifest(manifest))
        write_json(run_history_path, history)

        checkpoints = read_json("data/state/checkpoints.json", default={}) or {}
        checkpoints["last_successful_run_date"] = current_run_date
        checkpoints["last_reads_scrape_date"] = current_run_date
        write_json("data/state/checkpoints.json", checkpoints)

    def _build_canonical_record(self, article, summary, source_profile: str, run_date: str) -> CanonicalArticleRecord:
        return CanonicalArticleRecord(
            article_id=article.article_id,
            source_profile=source_profile,
            source_label=article.metadata.get("source_label"),
            article_url=article.original_url,
            canonical_url=article.canonical_url,
            title=article.title,
            subtitle=article.subtitle or article.description,
            author=article.author,
            publication=article.publication,
            published_at=article.published_at,
            body_text=article.body_text,
            summary_short=summary.summary_short,
            summary_bullets=summary.summary_bullets,
            key_takeaway=summary.key_takeaway,
            topic_tags=article.topic_tags,
            scraped_at=article.fetched_at,
            run_date=run_date,
            processing_status="completed" if article.fetch_status == "fetched" else article.fetch_status,
            summary_status=summary.summary_status,
            summary_model=summary.model,
            content_hash=article.content_hash,
            error_message=None,
        )

    def _build_failed_canonical_record(self, read_item, source_profile: str, run_date: str, error_message: str) -> CanonicalArticleRecord:
        normalized_url = normalize_url(read_item.article_url)
        return CanonicalArticleRecord(
            article_id=sha256_text(normalized_url)[:16],
            source_profile=source_profile,
            source_label=read_item.source_label,
            article_url=normalized_url,
            canonical_url=normalized_url,
            title=read_item.title_hint,
            subtitle=None,
            author=None,
            publication=None,
            published_at=None,
            body_text="",
            summary_short=None,
            summary_bullets=[],
            key_takeaway=None,
            topic_tags=[],
            scraped_at=now_utc_iso(),
            run_date=run_date,
            processing_status="failed_extraction",
            summary_status="not_started",
            summary_model=None,
            content_hash=None,
            error_message=error_message,
        )
