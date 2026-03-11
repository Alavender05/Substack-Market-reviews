from src.processing.publication_registry import PublicationRegistry


def test_publication_registry_upsert_and_expiry(tmp_path):
    registry_path = tmp_path / "publications_registry.json"
    registry = PublicationRegistry(str(registry_path), expiry_after_days=7)

    record = registry.upsert_from_reads(
        publication_name="Macro Notes",
        publication_url="https://marketnotes.substack.com",
        discovered_from_profile="https://substack.com/@aleclavender",
        seen_at="2026-03-01T00:00:00+00:00",
    )
    assert record.rss_url == "https://marketnotes.substack.com/feed"

    registry.mark_checked(
        "https://marketnotes.substack.com",
        checked_at="2026-03-02T00:00:00+00:00",
        success=True,
        monitor_method="rss",
    )
    registry.save()

    reloaded = PublicationRegistry(str(registry_path), expiry_after_days=7)
    active = reloaded.active_publications("2026-03-05T00:00:00+00:00")
    assert len(active) == 1
    assert active[0].publication_name == "Macro Notes"

    expired = reloaded.active_publications("2026-03-20T00:00:00+00:00")
    assert expired == []


def test_publication_registry_import_publications(tmp_path):
    registry_path = tmp_path / "publications_registry.json"
    registry = PublicationRegistry(str(registry_path), expiry_after_days=14)

    imported = registry.import_publications(
        [
            {
                "publication_name": "Macro Notes",
                "publication_url": "https://marketnotes.substack.com",
            },
            {
                "name": "Risk Journal",
                "url": "https://riskjournal.substack.com",
            },
        ],
        discovered_from_profile="https://substack.com/@aleclavender",
        seen_at="2026-03-11T00:00:00+00:00",
    )

    assert len(imported) == 2
    assert imported[0].publication_url == "https://marketnotes.substack.com/"
    assert imported[0].last_seen_on_reads == "2026-03-11T00:00:00+00:00"
    assert imported[1].publication_name == "Risk Journal"
