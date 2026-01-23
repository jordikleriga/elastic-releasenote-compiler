"""Async orchestration for fetching and compiling release notes."""

import asyncio
from typing import Optional, List, Dict
import logging

from .config import PRODUCTS, MODERN_DOCS_MIN_VERSION, ProductConfig
from .version import Version, VersionRange
from .models import ReleaseNote, CompiledReleaseNotes, SectionType
from .fetchers.async_legacy import AsyncLegacyFetcher
from .fetchers.async_modern import AsyncModernFetcher

logger = logging.getLogger(__name__)


class AsyncReleaseCompiler:
    """Async orchestrator for fetching and compiling release notes."""

    def __init__(
        self,
        products: Optional[List[str]] = None,
        max_concurrent: int = 10,
    ):
        self.product_names = products or ["elasticsearch"]
        self.max_concurrent = max_concurrent
        self._fetchers: Dict[str, Dict[str, object]] = {}
        self._semaphore = asyncio.Semaphore(max_concurrent)

        # Validate products
        for product in self.product_names:
            if product not in PRODUCTS:
                raise ValueError(f"Unknown product: {product}. Available: {list(PRODUCTS.keys())}")

    def _get_fetchers(self, product: str) -> tuple:
        """Get or create fetchers for a product."""
        if product not in self._fetchers:
            config = PRODUCTS[product]
            self._fetchers[product] = {}

            # Only create legacy fetcher if product has legacy docs
            if config.has_legacy_docs and config.legacy_base_url:
                self._fetchers[product]["legacy"] = AsyncLegacyFetcher(config)
            else:
                self._fetchers[product]["legacy"] = None

            # Always create modern fetcher
            self._fetchers[product]["modern"] = AsyncModernFetcher(config)

        return (
            self._fetchers[product]["legacy"],
            self._fetchers[product]["modern"],
        )

    def _get_fetcher_for_version(self, product: str, version: Version):
        """Select appropriate fetcher based on version and product capabilities."""
        legacy, modern = self._get_fetchers(product)
        config = PRODUCTS[product]

        # If product only has modern docs, always use modern fetcher
        if not config.has_legacy_docs or legacy is None:
            return modern

        # Otherwise, use version to decide
        if version >= MODERN_DOCS_MIN_VERSION:
            return modern
        return legacy

    async def discover_versions(self, product: str) -> List[Version]:
        """Discover all available versions for a product."""
        legacy, modern = self._get_fetchers(product)
        config = PRODUCTS[product]

        tasks = []

        # Only try legacy if product supports it
        if legacy is not None and config.has_legacy_docs:
            tasks.append(("legacy", legacy.fetch_available_versions()))

        # Always try modern
        tasks.append(("modern", modern.fetch_available_versions()))

        all_versions = set()

        for name, task in tasks:
            try:
                versions = await task
                logger.info(f"Found {len(versions)} {name} versions for {product}")
                all_versions.update(versions)
            except Exception as e:
                logger.warning(f"Failed to fetch {name} versions for {product}: {e}")

        return sorted(all_versions, reverse=True)

    async def _fetch_complete_release(self, product: str, version: Version) -> Optional[ReleaseNote]:
        """Fetch all release information for a version with rate limiting."""
        async with self._semaphore:
            fetcher = self._get_fetcher_for_version(product, version)

            # Fetch main release notes
            release = await fetcher.fetch_release_notes(version)
            if not release:
                return None

            # Enrich with breaking changes from dedicated page
            try:
                breaking = await fetcher.fetch_breaking_changes(version)
                if breaking and not breaking.is_empty():
                    if SectionType.BREAKING_CHANGES not in release.sections:
                        release.sections[SectionType.BREAKING_CHANGES] = breaking
                    else:
                        # Merge items, avoiding duplicates
                        existing = release.sections[SectionType.BREAKING_CHANGES]
                        existing_descs = {item.description for item in existing.items}
                        for item in breaking.items:
                            if item.description not in existing_descs:
                                existing.items.append(item)
            except Exception as e:
                logger.debug(f"Could not fetch breaking changes for {version}: {e}")

            # Fetch deprecations (modern fetcher only)
            if hasattr(fetcher, 'fetch_deprecations'):
                try:
                    deprecations = await fetcher.fetch_deprecations(version)
                    if deprecations and not deprecations.is_empty():
                        if SectionType.DEPRECATIONS not in release.sections:
                            release.sections[SectionType.DEPRECATIONS] = deprecations
                except Exception as e:
                    logger.debug(f"Could not fetch deprecations for {version}: {e}")

            # Fetch known issues (modern fetcher only)
            if hasattr(fetcher, 'fetch_known_issues'):
                try:
                    known_issues = await fetcher.fetch_known_issues(version)
                    if known_issues and not known_issues.is_empty():
                        if SectionType.KNOWN_ISSUES not in release.sections:
                            release.sections[SectionType.KNOWN_ISSUES] = known_issues
                except Exception as e:
                    logger.debug(f"Could not fetch known issues for {version}: {e}")

            return release

    async def compile_product(
        self,
        product: str,
        start_version: str,
        end_version: Optional[str] = None,
        include_prereleases: bool = False,
        progress_callback=None,
    ) -> CompiledReleaseNotes:
        """Compile release notes for a single product."""
        start = Version.parse(start_version)
        end = Version.parse(end_version) if end_version else None
        version_range = VersionRange(start, end)

        # Discover available versions
        all_versions = await self.discover_versions(product)

        if not all_versions:
            logger.warning(f"No versions found for {product}")
            return CompiledReleaseNotes(
                product=product,
                start_version=start,
                end_version=end or start,
            )

        # Filter to relevant versions
        target_versions = version_range.filter_versions(all_versions)
        if not include_prereleases:
            target_versions = [v for v in target_versions if not v.is_prerelease]

        logger.info(f"Compiling {len(target_versions)} versions for {product}")

        # Fetch release notes concurrently
        tasks = [
            self._fetch_complete_release(product, v)
            for v in target_versions
        ]

        releases: List[ReleaseNote] = []
        completed = 0

        for coro in asyncio.as_completed(tasks):
            try:
                release = await coro
                if release:
                    releases.append(release)
                    logger.debug(f"Fetched release notes for {product} {release.version}")
            except Exception as e:
                logger.warning(f"Failed to fetch release: {e}")

            completed += 1
            if progress_callback:
                progress_callback(completed, len(target_versions))

        # Sort by version
        releases.sort(key=lambda r: r.version)

        actual_end = target_versions[-1] if target_versions else start
        if end:
            actual_end = end

        return CompiledReleaseNotes(
            product=product,
            start_version=start,
            end_version=actual_end,
            releases=releases,
        )

    async def compile_all(
        self,
        start_version: str,
        end_version: Optional[str] = None,
        include_prereleases: bool = False,
    ) -> Dict[str, CompiledReleaseNotes]:
        """Compile release notes for all configured products."""
        results = {}

        for product in self.product_names:
            logger.info(f"Compiling release notes for {product}...")
            results[product] = await self.compile_product(
                product=product,
                start_version=start_version,
                end_version=end_version,
                include_prereleases=include_prereleases,
            )

        return results

    async def close(self):
        """Clean up resources."""
        for product_fetchers in self._fetchers.values():
            for fetcher in product_fetchers.values():
                if fetcher is not None:
                    await fetcher.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


class AsyncReleaseCompilerWithProgress(AsyncReleaseCompiler):
    """Async release compiler with rich progress bar support."""

    async def compile_product(
        self,
        product: str,
        start_version: str,
        end_version: Optional[str] = None,
        include_prereleases: bool = False,
        progress_callback=None,
    ) -> CompiledReleaseNotes:
        """Compile release notes for a single product with progress bar."""
        from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn
        from rich.console import Console

        console = Console()
        start = Version.parse(start_version)
        end = Version.parse(end_version) if end_version else None
        version_range = VersionRange(start, end)

        # Discover available versions with spinner
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            task = progress.add_task(f"Discovering {product} versions...", total=None)
            all_versions = await self.discover_versions(product)
            progress.update(task, completed=True)

        if not all_versions:
            logger.warning(f"No versions found for {product}")
            return CompiledReleaseNotes(
                product=product,
                start_version=start,
                end_version=end or start,
            )

        # Filter to relevant versions
        target_versions = version_range.filter_versions(all_versions)
        if not include_prereleases:
            target_versions = [v for v in target_versions if not v.is_prerelease]

        logger.info(f"Compiling {len(target_versions)} versions for {product}")

        # Fetch release notes with progress bar
        releases: List[ReleaseNote] = []

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeRemainingColumn(),
            console=console,
        ) as progress:
            task = progress.add_task(
                f"[cyan]Fetching {product} release notes...",
                total=len(target_versions)
            )

            tasks = [
                self._fetch_complete_release(product, v)
                for v in target_versions
            ]

            for coro in asyncio.as_completed(tasks):
                try:
                    release = await coro
                    if release:
                        releases.append(release)
                        logger.debug(f"Fetched release notes for {product} {release.version}")
                except Exception as e:
                    logger.warning(f"Failed to fetch release: {e}")
                finally:
                    progress.advance(task)

        # Sort by version
        releases.sort(key=lambda r: r.version)

        actual_end = target_versions[-1] if target_versions else start
        if end:
            actual_end = end

        return CompiledReleaseNotes(
            product=product,
            start_version=start,
            end_version=actual_end,
            releases=releases,
        )

    async def compile_all(
        self,
        start_version: str,
        end_version: Optional[str] = None,
        include_prereleases: bool = False,
    ) -> Dict[str, CompiledReleaseNotes]:
        """Compile release notes for all configured products with progress."""
        from rich.console import Console
        from rich.panel import Panel

        console = Console()

        # Show compilation info
        end_display = end_version or "latest"
        console.print(Panel(
            f"[bold]Compiling release notes (async)[/bold]\n"
            f"Products: [cyan]{', '.join(self.product_names)}[/cyan]\n"
            f"Range: [cyan]{start_version}[/cyan] → [cyan]{end_display}[/cyan]",
            title="ES Release Compiler",
            border_style="blue",
        ))

        results = {}

        for product in self.product_names:
            logger.info(f"Compiling release notes for {product}...")
            results[product] = await self.compile_product(
                product=product,
                start_version=start_version,
                end_version=end_version,
                include_prereleases=include_prereleases,
            )

        return results
