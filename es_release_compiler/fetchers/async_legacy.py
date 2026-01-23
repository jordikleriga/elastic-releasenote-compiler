"""Async fetcher for 8.x documentation site structure."""

from typing import Optional, List
import re
import logging

from .async_base import AsyncBaseFetcher
from ..config import ProductConfig, LEGACY_PATTERNS, LATEST_8X_MINOR
from ..version import Version
from ..models import ReleaseNote, ReleaseSection

logger = logging.getLogger(__name__)


class AsyncLegacyFetcher(AsyncBaseFetcher):
    """Async fetcher for 8.x documentation site structure."""

    VERSION_LINK_PATTERN = re.compile(r'release-notes-(\d+\.\d+\.\d+(?:-\w+\d*)?)')

    def __init__(self, product_config: ProductConfig, latest_minor: str = LATEST_8X_MINOR):
        super().__init__(product_config)
        self.latest_minor = latest_minor
        self._parser = None

    @property
    def parser(self):
        """Lazy load parser to avoid circular imports."""
        if self._parser is None:
            from ..parsers.legacy import LegacyParser
            self._parser = LegacyParser()
        return self._parser

    def _build_url(self, pattern_key: str, **kwargs) -> str:
        """Build URL from pattern."""
        pattern = LEGACY_PATTERNS[pattern_key]
        return pattern.format(
            base=self.config.legacy_base_url,
            minor=self.latest_minor,
            **kwargs
        )

    async def fetch_available_versions(self) -> List[Version]:
        """Parse the release notes index page to discover versions."""
        url = self._build_url("release_notes_index")
        html = await self.fetch_page(url)
        if not html:
            logger.warning(f"Could not fetch release notes index for {self.config.name}")
            return []

        versions = []
        for match in self.VERSION_LINK_PATTERN.finditer(html):
            try:
                version = Version.parse(match.group(1))
                # Only include 8.x versions
                if version.major == 8:
                    versions.append(version)
            except ValueError:
                continue

        return sorted(set(versions), reverse=True)

    async def fetch_release_notes(self, version: Version) -> Optional[ReleaseNote]:
        """Fetch individual release notes page."""
        url = self._build_url("release_notes", version=str(version))
        html = await self.fetch_page(url)
        if not html:
            return None

        release_note = self.parser.parse_release_notes(html, version, self.config.name)
        release_note.source_url = url
        return release_note

    async def fetch_breaking_changes(self, version: Version) -> Optional[ReleaseSection]:
        """Fetch migration guide for breaking changes."""
        url = self._build_url("breaking_changes", target_minor=version.major_minor)
        html = await self.fetch_page(url)
        if not html:
            return None

        return self.parser.parse_breaking_changes(html, version)

    async def fetch_breaking_changes_index(self) -> Optional[str]:
        """Fetch the breaking changes index page."""
        url = self._build_url("breaking_changes_index")
        return await self.fetch_page(url)
