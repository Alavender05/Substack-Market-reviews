from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


def _validate_url(value: str, field_name: str) -> str:
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"{field_name} must be a valid http(s) URL")
    return value


@dataclass
class ProfileConfig:
    substack_profile_url: str
    reads_enabled: bool = True

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProfileConfig":
        return cls(
            substack_profile_url=_validate_url(data["substack_profile_url"], "profile.substack_profile_url"),
            reads_enabled=bool(data.get("reads_enabled", True)),
        )


@dataclass
class PipelineConfig:
    article_fetch_limit_per_run: int = 10
    save_raw_html: bool = True
    daily_run_timezone: str = "UTC"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PipelineConfig":
        limit = int(data.get("article_fetch_limit_per_run", 10))
        if limit < 1:
            raise ValueError("pipeline.article_fetch_limit_per_run must be >= 1")
        return cls(
            article_fetch_limit_per_run=limit,
            save_raw_html=bool(data.get("save_raw_html", True)),
            daily_run_timezone=str(data.get("daily_run_timezone", "UTC")),
        )


@dataclass
class SummarizationConfig:
    enabled: bool = True
    provider: str = "openai"
    model: str = "gpt-4.1-mini"
    summary_length: str = "medium"
    max_input_chars: int = 12000
    include_bullets: bool = True

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SummarizationConfig":
        max_input_chars = int(data.get("max_input_chars", 12000))
        if max_input_chars < 1000:
            raise ValueError("summarization.max_input_chars must be >= 1000")
        return cls(
            enabled=bool(data.get("enabled", True)),
            provider=str(data.get("provider", "openai")),
            model=str(data.get("model", "gpt-4.1-mini")),
            summary_length=str(data.get("summary_length", "medium")),
            max_input_chars=max_input_chars,
            include_bullets=bool(data.get("include_bullets", True)),
        )


@dataclass
class OutputConfig:
    latest_dir: str = "output/latest"
    archive_dir: str = "output/archive"
    articles_file: str = "articles_enriched.json"
    digest_file: str = "daily_digest.json"
    dashboard_file: str = "dashboard_feed.json"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "OutputConfig":
        return cls(
            latest_dir=str(data.get("latest_dir", "output/latest")),
            archive_dir=str(data.get("archive_dir", "output/archive")),
            articles_file=str(data.get("articles_file", "articles_enriched.json")),
            digest_file=str(data.get("digest_file", "daily_digest.json")),
            dashboard_file=str(data.get("dashboard_file", "dashboard_feed.json")),
        )


@dataclass
class LoggingConfig:
    level: str = "INFO"
    log_to_file: bool = True
    log_dir: str = "logs"
    json_logs: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LoggingConfig":
        return cls(
            level=str(data.get("level", "INFO")),
            log_to_file=bool(data.get("log_to_file", True)),
            log_dir=str(data.get("log_dir", "logs")),
            json_logs=bool(data.get("json_logs", False)),
        )


@dataclass
class DeduplicationConfig:
    enabled: bool = True
    dedupe_key: str = "canonical_url"
    fallback_to_content_hash: bool = True
    seen_articles_path: str = "data/state/seen_articles.json"
    skip_existing_articles: bool = True

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DeduplicationConfig":
        return cls(
            enabled=bool(data.get("enabled", True)),
            dedupe_key=str(data.get("dedupe_key", "canonical_url")),
            fallback_to_content_hash=bool(data.get("fallback_to_content_hash", True)),
            seen_articles_path=str(data.get("seen_articles_path", "data/state/seen_articles.json")),
            skip_existing_articles=bool(data.get("skip_existing_articles", True)),
        )


@dataclass
class FetchingConfig:
    request_timeout_seconds: int = 20
    browser_wait_until: str = "networkidle"
    max_retries: int = 2
    user_agent: str = "SubstackReadsCollector/0.1"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FetchingConfig":
        timeout = int(data.get("request_timeout_seconds", 20))
        retries = int(data.get("max_retries", 2))
        if timeout < 1:
            raise ValueError("fetching.request_timeout_seconds must be >= 1")
        if retries < 0:
            raise ValueError("fetching.max_retries must be >= 0")
        return cls(
            request_timeout_seconds=timeout,
            browser_wait_until=str(data.get("browser_wait_until", "networkidle")),
            max_retries=retries,
            user_agent=str(data.get("user_agent", "SubstackReadsCollector/0.1")),
        )


@dataclass
class AppConfig:
    profile: ProfileConfig
    pipeline: PipelineConfig
    summarization: SummarizationConfig
    output: OutputConfig
    logging: LoggingConfig
    deduplication: DeduplicationConfig
    fetching: FetchingConfig

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AppConfig":
        return cls(
            profile=ProfileConfig.from_dict(data["profile"]),
            pipeline=PipelineConfig.from_dict(data.get("pipeline", {})),
            summarization=SummarizationConfig.from_dict(data.get("summarization", {})),
            output=OutputConfig.from_dict(data.get("output", {})),
            logging=LoggingConfig.from_dict(data.get("logging", {})),
            deduplication=DeduplicationConfig.from_dict(data.get("deduplication", {})),
            fetching=FetchingConfig.from_dict(data.get("fetching", {})),
        )


@dataclass
class SourceConfig:
    id: str
    type: str
    enabled: bool = True
    label: str = ""
    profile_url: str = ""
    reads_path_hint: str = "/reads"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SourceConfig":
        return cls(
            id=str(data["id"]),
            type=str(data["type"]),
            enabled=bool(data.get("enabled", True)),
            label=str(data.get("label", "")),
            profile_url=_validate_url(data["profile_url"], "sources.profile_url"),
            reads_path_hint=str(data.get("reads_path_hint", "/reads")),
        )


@dataclass
class SourcesConfig:
    sources: list[SourceConfig] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SourcesConfig":
        return cls(
            sources=[SourceConfig.from_dict(item) for item in data.get("sources", [])]
        )


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_config(config_path: str | Path = "config/config.json") -> AppConfig:
    path = Path(config_path)
    return AppConfig.from_dict(_load_json(path))


def load_sources(sources_path: str | Path = "config/sources.json") -> SourcesConfig:
    path = Path(sources_path)
    if not path.exists():
        return SourcesConfig()
    return SourcesConfig.from_dict(_load_json(path))
