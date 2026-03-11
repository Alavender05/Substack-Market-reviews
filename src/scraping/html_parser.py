from __future__ import annotations

from bs4 import BeautifulSoup

from ..utils.text_cleaning import clean_whitespace


class ArticleHtmlParser:
    def parse(self, html: str, source_url: str) -> dict[str, str | list[str] | None]:
        soup = BeautifulSoup(html, "html.parser")

        canonical = self._meta_content(soup, "link[rel='canonical']", "href") or source_url
        title = (
            self._meta_content(soup, "meta[property='og:title']", "content")
            or self._meta_content(soup, "meta[name='twitter:title']", "content")
            or (soup.title.get_text(strip=True) if soup.title else None)
        )
        description = (
            self._meta_content(soup, "meta[name='description']", "content")
            or self._meta_content(soup, "meta[property='og:description']", "content")
        )
        subtitle = (
            self._meta_content(soup, "meta[name='twitter:description']", "content")
            or description
        )
        author = (
            self._meta_content(soup, "meta[name='author']", "content")
            or self._meta_content(soup, "meta[property='article:author']", "content")
        )
        publication = self._meta_content(soup, "meta[property='og:site_name']", "content")
        published_at = (
            self._meta_content(soup, "meta[property='article:published_time']", "content")
            or self._meta_content(soup, "time[datetime]", "datetime")
        )
        body_text = self._extract_body_text(soup)
        topic_tags = self._extract_topic_tags(soup)

        return {
            "canonical_url": canonical,
            "title": title,
            "subtitle": subtitle,
            "description": description,
            "author": author,
            "publication": publication,
            "published_at": published_at,
            "body_text": body_text,
            "topic_tags": topic_tags,
        }

    def _meta_content(self, soup: BeautifulSoup, selector: str, attribute: str) -> str | None:
        node = soup.select_one(selector)
        if not node:
            return None
        value = node.get(attribute)
        return clean_whitespace(value) if value else None

    def _extract_body_text(self, soup: BeautifulSoup) -> str:
        for selector in ("article", "main", "[data-testid='post-content']"):
            node = soup.select_one(selector)
            if node:
                return clean_whitespace(node.get_text(" ", strip=True))
        return clean_whitespace(soup.get_text(" ", strip=True))

    def _extract_topic_tags(self, soup: BeautifulSoup) -> list[str]:
        keywords = self._meta_content(soup, "meta[name='keywords']", "content")
        if not keywords:
            return []
        return [clean_whitespace(part) for part in keywords.split(",") if clean_whitespace(part)]
