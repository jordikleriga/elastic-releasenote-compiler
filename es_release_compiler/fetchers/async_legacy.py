"""Async fetcher for 8.x documentation site structure."""

from typing import Optional, List
import re
import logging

from .async_base import AsyncBaseFetcher
from ..config import ProductConfig, LEGACY_PATTERNS, LATEST_8X_MINOR, KNOWN_8X_MINORS
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

    def _build_url(self, pattern_key: str, minor: str = None, **kwargs) -> str:
        """Build URL from pattern, using specified minor or latest_minor."""
        pattern = LEGACY_PATTERNS[pattern_key]
        return pattern.format(
            base=self.config.legacy_base_url,
            minor=minor or self.latest_minor,
            **kwargs
        )

    async def _discover_all_minors(self) -> List[str]:
        """Discover all available 8.x minor version doc pages.

        Starts from KNOWN_8X_MINORS and probes for newer ones beyond the last known.
        """
        minors = list(KNOWN_8X_MINORS)
        # Probe for minors beyond the last known (e.g., 8.20, 8.21, ...)
        last_known_minor = int(KNOWN_8X_MINORS[-1].split(".")[1])
        for next_minor_num in range(last_known_minor + 1, last_known_minor + 5):
            probe_minor = f"8.{next_minor_num}"
            pattern = LEGACY_PATTERNS["release_notes_index"]
            probe_url = pattern.format(base=self.config.legacy_base_url, minor=probe_minor)
            html = await self.fetch_page(probe_url)
            if html:
                logger.info(f"Discovered new minor version docs: {probe_minor}")
                minors.append(probe_minor)
            else:
                break  # Stop probing once we hit a missing page
        return minors

    async def fetch_available_versions(self) -> List[Version]:
        """Parse release notes index pages from all 8.x minors to discover versions."""
        all_minors = await self._discover_all_minors()
        versions = set()

        for minor in all_minors:
            url = self._build_url("release_notes_index", minor=minor)
            html = await self.fetch_page(url)
            if not html:
                logger.debug(f"No release notes index found for minor {minor}")
                continue

            for match in self.VERSION_LINK_PATTERN.finditer(html):
                try:
                    version = Version.parse(match.group(1))
                    # Only include 8.x versions
                    if version.major == 8:
                        versions.add(version)
                except ValueError:
                    continue

            logger.info(f"Scanned {minor} index, total versions so far: {len(versions)}")

        return sorted(versions, reverse=True)

    async def fetch_release_notes(self, version: Version) -> Optional[ReleaseNote]:
        """Fetch individual release notes page."""
        # Use the version's own major.minor for the URL path
        url = self._build_url("release_notes", minor=version.major_minor, version=str(version))
        html = await self.fetch_page(url)
        if not html:
            return None

        release_note = self.parser.parse_release_notes(html, version, self.config.name)
        release_note.source_url = url
        return release_note

    async def fetch_breaking_changes(self, version: Version) -> Optional[ReleaseSection]:
        """Fetch migration guide for breaking changes."""
        url = self._build_url("breaking_changes", minor=version.major_minor, target_minor=version.major_minor)
        html = await self.fetch_page(url)
        if not html:
            return None

        return self.parser.parse_breaking_changes(html, version)

    async def fetch_breaking_changes_index(self) -> Optional[str]:
        """Fetch the breaking changes index page."""
        url = self._build_url("breaking_changes_index")
        return await self.fetch_page(url)
