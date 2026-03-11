from __future__ import annotations

import argparse

from dotenv import load_dotenv

from .config_loader import load_config, load_sources
from .logger import setup_logger
from .output_guard import load_display_payload, prepare_articles_payload, write_latest_articles_if_allowed
from .outputs.digest_builder import build_dashboard_feed, build_digest
from .outputs.writers import OutputWriter
from .pipeline import Pipeline
from .preflight import run_preflight
from .processing.publication_registry import PublicationRegistry
from .run_state import finalize_run_state, init_run_state, set_run_status, write_run_state
from .status_rules import classify_discovery_result, classify_final_run, classify_preflight_result
from .utils.dates import now_utc_iso, run_date
from .utils.file_io import write_json


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Substack Reads summary pipeline.")
    parser.add_argument("--config", default="config/config.json", help="Path to config.json")
    parser.add_argument("--sources", default="config/sources.json", help="Path to sources.json")
    parser.add_argument("--dry-run", action="store_true", help="Run without writing processed outputs")
    return parser.parse_args()


def main() -> None:
    load_dotenv()
    args = parse_args()
    run_state = init_run_state()
    degraded = False
    logger = None

    try:
        config = load_config(args.config)
        sources = load_sources(args.sources)
        logger = setup_logger(config.logging)
        output_writer = OutputWriter(config.output)
        preflight = run_preflight(config)
        write_json("data/connectivity_report.json", {"run_id": run_state["run_id"], **preflight})

        preflight_status, preflight_stage = classify_preflight_result(preflight)
        if preflight_status == "degraded":
            degraded = True
            set_run_status(run_state, "degraded", preflight_stage)
            run_state["warnings"].append("DNS resolution failed for required external domains." if preflight_stage == "preflight_dns" else "Preflight checks failed.")
            current_payload = prepare_articles_payload(run_state["run_id"], "degraded", [], "current")
            promoted = write_latest_articles_if_allowed(
                run_state,
                current_payload,
                "data/latest_articles.json",
                "data/latest_successful_articles.json",
            )
            run_state["preserved_last_successful_output"] = not promoted
            _write_consumer_outputs(config, output_writer, run_state)
            _write_registry_snapshot(config, run_state, preflight, reads_status="error")
            return

        pipeline = Pipeline(config=config, sources=sources, logger=logger)
        result = pipeline.run(dry_run=args.dry_run)

        run_state["source_checks_attempted"] = result["source_checks_attempted"]
        run_state["source_checks_succeeded"] = result["source_checks_succeeded"]
        run_state["source_checks_failed"] = result["source_checks_failed"]
        run_state["article_count"] = len(result["articles"])
        run_state["errors"].extend(result.get("errors", []))

        discovery_status, discovery_stage = classify_discovery_result(
            result["source_checks_succeeded"],
            result["source_checks_failed"],
        )
        if discovery_status == "degraded" or result["source_checks_succeeded"] == 0:
            degraded = True
            set_run_status(run_state, "degraded", discovery_stage or "discovery")
            run_state["warnings"].append("No sources could be checked successfully.")

        run_state["run_status"] = classify_final_run(
            internal_error=bool(result.get("internal_error")),
            degraded=degraded,
        )

        current_payload = prepare_articles_payload(
            run_state["run_id"],
            run_state["run_status"],
            result["articles"],
            "current",
        )
        promoted = write_latest_articles_if_allowed(
            run_state,
            current_payload,
            "data/latest_articles.json",
            "data/latest_successful_articles.json",
        )
        run_state["preserved_last_successful_output"] = not promoted
        _write_consumer_outputs(
            config,
            output_writer,
            run_state,
            selected_run_date=result.get("run_date") or run_date(config.pipeline.daily_run_timezone),
        )
        reads_status = "error" if result.get("discovery_blocked") else "ok"
        _write_registry_snapshot(config, run_state, preflight, reads_status=reads_status)
    except Exception as exc:
        set_run_status(run_state, "failed", "internal")
        run_state["errors"].append(repr(exc))
        if logger:
            logger.exception("Pipeline failed")
    finally:
        finalize_run_state(run_state)
        write_run_state(run_state)
        if logger:
            logger.info("Pipeline finished with status=%s", run_state["run_status"])


def _write_consumer_outputs(config, output_writer: OutputWriter, run_state: dict, selected_run_date: str | None = None) -> None:
    selected_payload, banner = load_display_payload(
        run_state,
        "data/latest_articles.json",
        "data/latest_successful_articles.json",
    )
    articles = selected_payload.get("articles", [])
    latest_batch = {
        "schema_version": "1.0",
        "run_id": run_state["run_id"],
        "run_date": selected_run_date or run_date(config.pipeline.daily_run_timezone),
        "source_profile": str(config.profile.substack_profile_url),
        "generated_at": now_utc_iso(),
        "article_count": len(articles),
        "status": run_state["run_status"],
        "articles": articles,
    }
    digest = build_digest(articles)
    dashboard = build_dashboard_feed(articles)
    if banner:
        latest_batch["banner_message"] = banner
        digest["banner_message"] = banner
        dashboard["banner_message"] = banner
    output_writer.write_latest_outputs(latest_batch, digest, dashboard)


def _write_registry_snapshot(config, run_state: dict, preflight: dict, reads_status: str) -> None:
    registry = PublicationRegistry(
        config.monitoring.publications_registry_path,
        expiry_after_days=config.monitoring.publication_expiry_days,
    )
    reads_source = {
        "name": "Substack Reads",
        "url": str(config.profile.substack_profile_url),
        "monitor_status": reads_status,
        "last_successful_check": now_utc_iso() if reads_status == "ok" else None,
        "last_attempted_check": run_state["started_at"],
        "last_error_type": _preflight_reads_error_type(preflight),
        "last_error_message": _preflight_reads_error_message(preflight),
    }
    write_json("data/registry.json", registry.build_health_snapshot(reads_source=reads_source))


def _preflight_reads_error_type(preflight: dict) -> str | None:
    if preflight.get("failure_stage") == "preflight_dns":
        return "dns_failure"
    if preflight.get("failure_stage") == "preflight_http":
        failures = [item for item in preflight.get("http_checks", []) if "substack.com" in item.get("url", "") and not item.get("ok")]
        if failures and failures[0].get("status_code") == 403:
            return "http_403"
        return "http_failure"
    return None


def _preflight_reads_error_message(preflight: dict) -> str | None:
    if preflight.get("failure_stage") == "preflight_dns":
        failures = [item for item in preflight.get("dns_checks", []) if "substack.com" in item.get("host", "") and not item.get("ok")]
        if failures:
            return failures[0].get("error")
    if preflight.get("failure_stage") == "preflight_http":
        failures = [item for item in preflight.get("http_checks", []) if "substack.com" in item.get("url", "") and not item.get("ok")]
        if failures:
            return failures[0].get("error") or f"HTTP {failures[0].get('status_code')}"
    return None


if __name__ == "__main__":
    main()
