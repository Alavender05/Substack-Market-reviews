from pathlib import Path

from src.outputs.markdown_digest import (
    build_markdown_digest,
    group_articles_by_publication,
    load_daily_batch,
    render_digest_from_file,
)


def test_group_articles_by_publication_uses_fallbacks_and_sorting():
    batch = load_daily_batch("tests/fixtures/sample_daily_batch.json")
    digest_articles = [
        article
        for article in batch["articles"]
        if article["processing_status"] in {"completed", "partial"}
    ]
    grouped = group_articles_by_publication(digest_articles)

    assert list(grouped.keys()) == ["Macro Notes", "Unknown Publication"]
    assert grouped["Macro Notes"][0]["title"] == "Fed Signals Patience as Markets Reprice"


def test_build_markdown_digest_filters_failed_records_and_renders_sections():
    batch = load_daily_batch("tests/fixtures/sample_daily_batch.json")

    markdown = build_markdown_digest(batch)

    assert "# Daily Substack Digest - 2026-03-11" in markdown
    assert "## Macro Notes" in markdown
    assert "## Unknown Publication" in markdown
    assert "### [Fed Signals Patience as Markets Reprice](https://marketnotes.substack.com/p/fed-signals-patience)" in markdown
    assert "- The Fed signaled a cautious policy stance." in markdown
    assert "**Key takeaway:** Fed caution is still the main macro driver for market repricing." in markdown
    assert "failed_extraction" not in markdown
    assert "HTTP 403" not in markdown


def test_render_digest_from_file_writes_markdown_output(tmp_path):
    output_path = tmp_path / "daily_digest.md"

    markdown = render_digest_from_file(
        input_path="tests/fixtures/sample_daily_batch.json",
        output_path=output_path,
    )

    assert output_path.exists()
    assert output_path.read_text(encoding="utf-8") == markdown
    assert "Generated from public Reads activity." in markdown
