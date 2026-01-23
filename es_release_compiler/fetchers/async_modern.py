"""Async fetcher for 9.x documentation site (consolidated pages)."""

from typing import Optional, List, Dict
import logging

from .async_base import AsyncBaseFetcher
from ..config import ProductConfig, MODERN_PATTERNS
from ..version import Version
from ..models import ReleaseNote, ReleaseSection, SectionType

logger = logging.getLogger(__name__)


class AsyncModernFetcher(AsyncBaseFetcher):
    """Async fetcher for 9.x documentation site (single-page format)."""

    def __init__(self, product_config: ProductConfig):
        super().__init__(product_config)
        self._cached_pages: Dict[str, Optional[str]] = {}
        self._parser = None

    @property
    def parser(self):
        """Lazy load parser to avoid circular imports."""
        if self._parser is None:
            from ..parsers.modern import ModernParser
            self._parser = ModernParser()
        return self._parser

    def _build_url(self, pattern_key: str) -> str:
        """Build URL from pattern."""
        pattern = MODERN_PATTERNS[pattern_key]
        return pattern.format(base=self.config.modern_base_url)

    async def _get_cached_page(self, page_key: str) -> Optional[str]:
        """Fetch and cache a page."""
        if page_key not in self._cached_pages:
            url = self._build_url(page_key)
            self._cached_pages[page_key] = await self.fetch_page(url)
        return self._cached_pages[page_key]

    async def fetch_available_versions(self) -> List[Version]:
        """Extract all version anchors from the consolidated page."""
        html = await self._get_cached_page("release_notes")
        if not html:
            logger.warning(f"Could not fetch release notes for {self.config.name}")
            return []

        return self.parser.extract_version_list(html, self.config.name)

    async def fetch_release_notes(self, version: Version) -> Optional[ReleaseNote]:
        """Extract specific version from consolidated page."""
        html = await self._get_cached_page("release_notes")
        if not html:
            return None

        release = self.parser.parse_release_notes_for_version(
            html, version, self.config.name
        )
        if release:
            release.source_url = self._build_url("release_notes")
        return release

    async def fetch_breaking_changes(self, version: Version) -> Optional[ReleaseSection]:
        """Fetch from dedicated breaking changes page."""
        html = await self._get_cached_page("breaking_changes")
        if not html:
            return None

        return self.parser.parse_breaking_changes_for_version(html, version, self.config.name)

    async def fetch_deprecations(self, version: Version) -> Optional[ReleaseSection]:
        """Fetch from dedicated deprecations page."""
        html = await self._get_cached_page("deprecations")
        if not html:
            return None

        return self.parser.parse_deprecations_for_version(html, version)

    async def fetch_known_issues(self, version: Version) -> Optional[ReleaseSection]:
        """Fetch from dedicated known issues page."""
        html = await self._get_cached_page("known_issues")
        if not html:
            return None

        return self.parser.parse_known_issues_for_version(html, version)

    def clear_cache(self):
        """Clear the page cache."""
        self._cached_pages.clear()
