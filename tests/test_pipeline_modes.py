import logging

from src.config_loader import load_config
from src.models import ReadItem, SummaryRecord
from src.pipeline import Pipeline
from src.processing.publication_registry import PublicationRegistry


def test_pipeline_registry_only_mode_uses_existing_registry(tmp_path, monkeypatch):
    config = load_config("tests/fixtures/sample_config.json")
    config.monitoring.discovery_mode = "registry_only"
    config.monitoring.publications_registry_path = str(tmp_path / "publications_registry.json")
    config.deduplication.seen_articles_path = str(tmp_path / "seen_articles.json")

    registry = PublicationRegistry(config.monitoring.publications_registry_path, expiry_after_days=14)
    registry.import_publications(
        [
            {
                "publication_name": "Macro Notes",
                "publication_url": "https://marketnotes.substack.com",
            }
        ],
        discovered_from_profile="https://substack.com/@aleclavender",
        seen_at="2026-03-11T00:00:00+00:00",
    )
    registry.save()

    pipeline = Pipeline(config=config, sources=type("Sources", (), {"sources": []})(), logger=logging.getLogger("test"))

    monkeypatch.setattr(pipeline, "_collect_reads", lambda: (_ for _ in ()).throw(AssertionError("Reads should not be called")))
    monkeypatch.setattr(
        pipeline,
        "_monitor_publications",
        lambda publication_registry, checked_at: [
            ReadItem(
                source_url="https://marketnotes.substack.com/",
                article_url="https://marketnotes.substack.com/p/new-post",
                discovered_at=checked_at,
                title_hint="New Post",
                source_label="Macro Notes",
                discovered_via="publication_rss",
            )
        ],
    )
    monkeypatch.setattr(pipeline.article_fetcher, "fetch", lambda url: "<html></html>")
    monkeypatch.setattr(
        pipeline.article_parser,
        "parse",
        lambda html, url: {
            "canonical_url": url,
            "title": "New Post",
            "publication": "Macro Notes",
            "body_text": "First paragraph. Second paragraph.",
        },
    )
    monkeypatch.setattr(
        pipeline.summarizer,
        "summarize_article",
        lambda article: SummaryRecord(
            article_id=article.article_id,
            canonical_url=article.canonical_url,
            summary_short="Short summary.",
            summary_bullets=["Point one", "Point two"],
            key_takeaway="Point one",
            summary_status="completed",
            provider="test",
            model="test",
            created_at="2026-03-11T00:00:00+00:00",
            content_hash=article.content_hash,
        ),
    )
    monkeypatch.setattr("src.pipeline.write_json", lambda path, data: None)
    monkeypatch.setattr("src.pipeline.read_json", lambda path, default=None: default if default is not None else {})

    result = pipeline.run(dry_run=True)

    assert result["status"] == "completed"
    assert result["articles_selected"] == 1
    assert result["summaries_created"] == 1


def test_pipeline_manual_seed_mode_loads_seed_file(tmp_path):
    config = load_config("tests/fixtures/sample_config.json")
    config.monitoring.discovery_mode = "manual_seed"
    config.monitoring.publication_seeds_path = str(tmp_path / "publication_seeds.json")
    config.monitoring.publications_registry_path = str(tmp_path / "publications_registry.json")

    (tmp_path / "publication_seeds.json").write_text(
        """
        {
          "publications": [
            {
              "publication_name": "Macro Notes",
              "publication_url": "https://marketnotes.substack.com"
            }
          ]
        }
        """,
        encoding="utf-8",
    )

    pipeline = Pipeline(config=config, sources=type("Sources", (), {"sources": []})(), logger=logging.getLogger("test"))

    discovery = pipeline._discover_publications(
        PublicationRegistry(config.monitoring.publications_registry_path, expiry_after_days=14)
    )

    assert len(discovery.publications) == 1
    assert discovery.publications[0].publication_url == "https://marketnotes.substack.com/"
