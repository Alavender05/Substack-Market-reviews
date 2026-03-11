from pathlib import Path

from src.scraping.substack_reads_scraper import SubstackReadsScraper


class FakeAnchor:
    def __init__(self, href: str | None, text: str, visible: bool = True) -> None:
        self.href = href
        self.text = text
        self.visible = visible

    def is_visible(self) -> bool:
        return self.visible

    def get_attribute(self, name: str) -> str | None:
        if name == "href":
            return self.href
        return None

    def inner_text(self) -> str:
        return self.text


class FakeLocator:
    def __init__(self, anchors):
        self.anchors = anchors

    def count(self) -> int:
        return len(self.anchors)

    def nth(self, index: int) -> FakeAnchor:
        return self.anchors[index]


class FakePage:
    def __init__(self, anchors, html: str, raise_timeout: bool = False) -> None:
        self.anchors = anchors
        self.html = html
        self.goto_calls = []
        self.wait_calls = []
        self.raise_timeout = raise_timeout

    def goto(self, url: str, wait_until: str, timeout: int | None = None) -> None:
        if self.raise_timeout:
            from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

            raise PlaywrightTimeoutError("Timeout 15000ms exceeded.")
        self.goto_calls.append((url, wait_until))

    def wait_for_timeout(self, milliseconds: int) -> None:
        self.wait_calls.append(milliseconds)

    def locator(self, selector: str) -> FakeLocator:
        return FakeLocator(self.anchors)

    def content(self) -> str:
        return self.html


def test_extract_visible_links_deduplicates_and_filters_navigation_links():
    scraper = SubstackReadsScraper()
    page = FakePage(
        anchors=[
            FakeAnchor("https://news.example.com/p/market-review", "Market Review", True),
            FakeAnchor("https://news.example.com/p/market-review?utm_source=test", "Market Review", True),
            FakeAnchor("https://example.substack.com/about", "About", True),
            FakeAnchor("https://news.example.com/p/hidden", "Hidden", False),
            FakeAnchor("/p/local-post", "Local Post", True),
        ],
        html="",
    )

    items = scraper.extract_visible_links(page, "https://example.substack.com/reads", "Example")

    assert [item.article_url for item in items] == [
        "https://news.example.com/p/market-review",
        "https://example.substack.com/p/local-post",
    ]
    assert items[0].title_hint == "Market Review"


def test_extract_publications_from_reads_html():
    html = """
    <html>
      <body>
        <main>
          <a href="https://marketnotes.substack.com">Market Notes</a>
          <a href="https://news.example.com/p/market-review">Market Review</a>
          <a href="https://macroview.substack.com">Macro View</a>
        </main>
      </body>
    </html>
    """
    scraper = SubstackReadsScraper()

    publications = scraper.extract_publications(
        html,
        "https://substack.com/@aleclavender",
        "2026-03-11T00:00:00+00:00",
    )

    assert [item.publication_url for item in publications] == [
        "https://marketnotes.substack.com/",
        "https://macroview.substack.com/",
    ]


def test_scrape_saves_debug_snapshot_when_no_links_found(tmp_path):
    html = Path("tests/fixtures/sample_reads_page_no_posts.html").read_text(encoding="utf-8")
    scraper = SubstackReadsScraper(debug_dir=str(tmp_path))
    page = FakePage(anchors=[], html=html)

    items = scraper.scrape(page, "https://example.substack.com", source_label="Example")

    assert items == []
    assert page.goto_calls == [("https://example.substack.com/reads", "domcontentloaded")]
    assert page.wait_calls == [1500]
    assert scraper.last_debug_snapshot_path is not None
    snapshot_path = Path(scraper.last_debug_snapshot_path)
    assert snapshot_path.exists()
    assert snapshot_path.read_text(encoding="utf-8") == html


def test_build_reads_url_for_correct_profile_handle():
    scraper = SubstackReadsScraper()
    assert scraper.build_reads_url("https://substack.com/@aleclavender") == "https://substack.com/@aleclavender/reads"


def test_scrape_reads_detects_challenge_page_and_saves_snapshot(tmp_path):
    challenge_html = """
    <html>
      <head><title>Just a moment...</title></head>
      <body><div id="challenge-platform">Checking your browser</div></body>
    </html>
    """
    scraper = SubstackReadsScraper(debug_dir=str(tmp_path))
    page = FakePage(anchors=[], html=challenge_html)

    result = scraper.scrape_reads(page, "https://substack.com/@aleclavender", source_label="Example")

    assert result.publications == []
    assert result.direct_articles == []
    assert result.debug_snapshot_path is not None
    assert Path(result.debug_snapshot_path).exists()


def test_scrape_reads_timeout_returns_empty_result_with_snapshot(tmp_path):
    html = "<html><body><p>Partial page</p></body></html>"
    scraper = SubstackReadsScraper(debug_dir=str(tmp_path))
    page = FakePage(anchors=[], html=html, raise_timeout=True)

    result = scraper.scrape_reads(page, "https://substack.com/@aleclavender", source_label="Example")

    assert result.publications == []
    assert result.direct_articles == []
    assert result.debug_snapshot_path is not None
