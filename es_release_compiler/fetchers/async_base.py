"""Async base fetcher with HTTP client and retry logic."""

from abc import ABC, abstractmethod
from typing import Optional, List
import logging
import asyncio

import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    AsyncRetrying,
)

from ..config import ProductConfig
from ..version import Version
from ..models import ReleaseNote, ReleaseSection

logger = logging.getLogger(__name__)


class AsyncBaseFetcher(ABC):
    """Abstract base class for async documentation fetchers."""

    def __init__(self, product_config: ProductConfig):
        self.config = product_config
        self._client: Optional[httpx.AsyncClient] = None

    async def get_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=30.0,
                headers={"User-Agent": "ES-Release-Compiler/1.0"},
                follow_redirects=True,
            )
        return self._client

    async def fetch_page(self, url: str) -> Optional[str]:
        """Fetch HTML content with retry logic."""
        client = await self.get_client()

        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=2, max=10),
            retry=retry_if_exception_type((httpx.ConnectError, httpx.ReadTimeout)),
        ):
            with attempt:
                try:
                    logger.debug(f"Fetching: {url}")
                    response = await client.get(url)
                    response.raise_for_status()
                    return response.text
                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 404:
                        logger.debug(f"Page not found: {url}")
                        return None
                    logger.warning(f"HTTP error fetching {url}: {e}")
                    raise
                except Exception as e:
                    logger.warning(f"Error fetching {url}: {e}")
                    raise

        return None

    @abstractmethod
    async def fetch_available_versions(self) -> List[Version]:
        """Discover all available versions."""
        pass

    @abstractmethod
    async def fetch_release_notes(self, version: Version) -> Optional[ReleaseNote]:
        """Fetch release notes for a specific version."""
        pass

    @abstractmethod
    async def fetch_breaking_changes(self, version: Version) -> Optional[ReleaseSection]:
        """Fetch breaking changes for a specific version."""
        pass

    async def close(self):
        """Clean up HTTP client."""
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
