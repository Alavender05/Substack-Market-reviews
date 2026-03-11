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
    def __init__(self, anchors, html: str) -> None:
        self.anchors = anchors
        self.html = html
        self.goto_calls = []
        self.wait_calls = []

    def goto(self, url: str, wait_until: str) -> None:
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


def test_scrape_saves_debug_snapshot_when_no_links_found(tmp_path):
    html = Path("tests/fixtures/sample_reads_page_no_posts.html").read_text(encoding="utf-8")
    scraper = SubstackReadsScraper(debug_dir=str(tmp_path))
    page = FakePage(anchors=[], html=html)

    items = scraper.scrape(page, "https://example.substack.com", source_label="Example")

    assert items == []
    assert page.goto_calls == [("https://example.substack.com/reads", "networkidle")]
    assert page.wait_calls == [1500]
    assert scraper.last_debug_snapshot_path is not None
    snapshot_path = Path(scraper.last_debug_snapshot_path)
    assert snapshot_path.exists()
    assert snapshot_path.read_text(encoding="utf-8") == html

