from src.config_loader import load_config, load_sources


def test_load_config_from_fixture():
    config = load_config("tests/fixtures/sample_config.json")
    assert config.profile.substack_profile_url == "https://example.substack.com"
    assert config.pipeline.article_fetch_limit_per_run == 5
    assert config.summarization.summary_length == "short"


def test_load_sources_default_file():
    sources = load_sources("config/sources.json")
    assert len(sources.sources) == 1
    assert sources.sources[0].id == "primary_substack"
