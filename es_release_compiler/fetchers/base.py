"""Base fetcher with HTTP client and retry logic."""

from abc import ABC, abstractmethod
from typing import Optional, List
import logging

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from ..config import ProductConfig
from ..version import Version
from ..models import ReleaseNote, ReleaseSection

logger = logging.getLogger(__name__)


class BaseFetcher(ABC):
    """Abstract base class for documentation fetchers."""

    def __init__(self, product_config: ProductConfig):
        self.config = product_config
        self.client = httpx.Client(
            timeout=30.0,
            headers={"User-Agent": "ES-Release-Compiler/1.0"},
            follow_redirects=True,
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.ConnectError, httpx.ReadTimeout)),
    )
    def fetch_page(self, url: str) -> Optional[str]:
        """Fetch HTML content with retry logic."""
        try:
            logger.debug(f"Fetching: {url}")
            response = self.client.get(url)
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

    @abstractmethod
    def fetch_available_versions(self) -> List[Version]:
        """Discover all available versions."""
        pass

    @abstractmethod
    def fetch_release_notes(self, version: Version) -> Optional[ReleaseNote]:
        """Fetch release notes for a specific version."""
        pass

    @abstractmethod
    def fetch_breaking_changes(self, version: Version) -> Optional[ReleaseSection]:
        """Fetch breaking changes for a specific version."""
        pass

    def close(self):
        """Clean up HTTP client."""
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
