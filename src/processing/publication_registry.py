from __future__ import annotations

from dataclasses import asdict
from datetime import UTC, datetime
from typing import Any

from ..models import PublicationRecord
from ..processing.normalizer import normalize_url
from ..utils.file_io import read_json, write_json
from ..utils.hashing import sha256_text


class PublicationRegistry:
    def __init__(self, path: str, expiry_after_days: int) -> None:
        self.path = path
        self.expiry_after_days = expiry_after_days
        self.state = self._load_state()

    def _load_state(self) -> dict[str, Any]:
        state = read_json(
            self.path,
            default={"schema_version": "1.0", "updated_at": None, "publications": {}},
        ) or {"schema_version": "1.0", "updated_at": None, "publications": {}}
        state.setdefault("schema_version", "1.0")
        state.setdefault("updated_at", None)
        state.setdefault("publications", {})
        return state

    def upsert_from_reads(
        self,
        publication_name: str,
        publication_url: str,
        discovered_from_profile: str,
        seen_at: str,
        rss_url: str | None = None,
    ) -> PublicationRecord:
        normalized_url = normalize_url(publication_url)
        existing = self.state["publications"].get(normalized_url, {})
        record = PublicationRecord(
            publication_id=existing.get("publication_id", sha256_text(normalized_url)[:16]),
            publication_name=publication_name or existing.get("publication_name") or normalized_url,
            publication_url=normalized_url,
            rss_url=rss_url or existing.get("rss_url") or self._default_rss_url(normalized_url),
            discovered_from_profile=discovered_from_profile,
            first_seen=existing.get("first_seen", seen_at),
            last_seen_on_reads=seen_at,
            last_checked=existing.get("last_checked"),
            last_successful_check=existing.get("last_successful_check"),
            monitor_status=existing.get("monitor_status", "pending"),
            monitor_method=existing.get("monitor_method", "rss"),
            expiry_after_days=existing.get("expiry_after_days", self.expiry_after_days),
            is_active=True,
            error_message=None,
        )
        self.state["publications"][normalized_url] = record.to_dict()
        return record

    def upsert_publication(
        self,
        publication_name: str,
        publication_url: str,
        discovered_from_profile: str,
        seen_at: str,
        rss_url: str | None = None,
        mark_seen_on_reads: bool = False,
    ) -> PublicationRecord:
        normalized_url = normalize_url(publication_url)
        existing = self.state["publications"].get(normalized_url, {})
        last_seen_on_reads = existing.get("last_seen_on_reads")
        if mark_seen_on_reads or not last_seen_on_reads:
            last_seen_on_reads = seen_at
        record = PublicationRecord(
            publication_id=existing.get("publication_id", sha256_text(normalized_url)[:16]),
            publication_name=publication_name or existing.get("publication_name") or normalized_url,
            publication_url=normalized_url,
            rss_url=rss_url or existing.get("rss_url") or self._default_rss_url(normalized_url),
            discovered_from_profile=discovered_from_profile or existing.get("discovered_from_profile") or normalized_url,
            first_seen=existing.get("first_seen", seen_at),
            last_seen_on_reads=last_seen_on_reads,
            last_checked=existing.get("last_checked"),
            last_successful_check=existing.get("last_successful_check"),
            monitor_status=existing.get("monitor_status", "pending"),
            monitor_method=existing.get("monitor_method", "rss"),
            expiry_after_days=existing.get("expiry_after_days", self.expiry_after_days),
            is_active=True,
            error_message=None,
        )
        self.state["publications"][normalized_url] = record.to_dict()
        return record

    def import_publications(
        self,
        publications: list[dict[str, Any]],
        discovered_from_profile: str,
        seen_at: str,
    ) -> list[PublicationRecord]:
        imported: list[PublicationRecord] = []
        for publication in publications:
            publication_url = publication.get("publication_url") or publication.get("url")
            if not publication_url:
                continue
            imported.append(
                self.upsert_publication(
                    publication_name=publication.get("publication_name") or publication.get("name") or "",
                    publication_url=publication_url,
                    discovered_from_profile=publication.get("discovered_from_profile") or discovered_from_profile,
                    seen_at=seen_at,
                    rss_url=publication.get("rss_url"),
                    mark_seen_on_reads=False,
                )
            )
        return imported

    def active_publications(self, current_time: str) -> list[PublicationRecord]:
        self._apply_expiry(current_time)
        publications = [
            PublicationRecord(**record)
            for record in self.state["publications"].values()
            if record.get("is_active", True)
        ]
        return sorted(publications, key=lambda item: item.last_seen_on_reads, reverse=True)

    def mark_checked(
        self,
        publication_url: str,
        checked_at: str,
        success: bool,
        monitor_method: str,
        error_message: str | None = None,
    ) -> None:
        normalized_url = normalize_url(publication_url)
        record = self.state["publications"].get(normalized_url)
        if not record:
            return
        record["last_checked"] = checked_at
        record["monitor_method"] = monitor_method
        record["monitor_status"] = "ok" if success else "error"
        record["error_message"] = error_message
        if success:
            record["last_successful_check"] = checked_at
            record["is_active"] = True

    def save(self) -> None:
        self.state["updated_at"] = datetime.now(UTC).isoformat()
        write_json(self.path, self.state)

    def _apply_expiry(self, current_time: str) -> None:
        current_dt = _parse_datetime(current_time)
        for record in self.state["publications"].values():
            last_seen = record.get("last_seen_on_reads")
            if not last_seen:
                continue
            age_days = (current_dt - _parse_datetime(last_seen)).days
            if age_days > int(record.get("expiry_after_days", self.expiry_after_days)):
                record["is_active"] = False

    def _default_rss_url(self, publication_url: str) -> str:
        return publication_url.rstrip("/") + "/feed"


def _parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))
