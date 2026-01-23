"""Version parsing and comparison utilities."""

from dataclasses import dataclass
from functools import total_ordering
from typing import Optional, Tuple, List
import re


@total_ordering
@dataclass
class Version:
    """Semantic version representation with comparison support."""

    major: int
    minor: int
    patch: int
    prerelease: Optional[str] = None

    VERSION_PATTERN = re.compile(
        r'^(\d+)\.(\d+)\.(\d+)(?:[-.]?(alpha|beta|rc)(\d+))?$',
        re.IGNORECASE
    )

    @classmethod
    def parse(cls, version_str: str) -> 'Version':
        """Parse version string like '8.16.1' or '9.0.0-alpha1'."""
        match = cls.VERSION_PATTERN.match(version_str.strip())
        if not match:
            raise ValueError(f"Invalid version format: {version_str}")

        major = int(match.group(1))
        minor = int(match.group(2))
        patch = int(match.group(3))
        prerelease = None
        if match.group(4):
            prerelease = f"{match.group(4).lower()}{match.group(5)}"

        return cls(major, minor, patch, prerelease)

    @property
    def is_prerelease(self) -> bool:
        return self.prerelease is not None

    @property
    def major_minor(self) -> str:
        """Returns '8.17' format for URL construction."""
        return f"{self.major}.{self.minor}"

    def _comparison_tuple(self) -> Tuple:
        """Tuple for ordering: prereleases sort before release."""
        if self.prerelease:
            pre_match = re.match(r'(alpha|beta|rc)(\d+)', self.prerelease)
            if pre_match:
                pre_type = pre_match.group(1)
                pre_num = int(pre_match.group(2))
                pre_order = {'alpha': 0, 'beta': 1, 'rc': 2}
                return (self.major, self.minor, self.patch, pre_order.get(pre_type, 0), pre_num)
        return (self.major, self.minor, self.patch, 3, 0)

    def __lt__(self, other: 'Version') -> bool:
        if not isinstance(other, Version):
            return NotImplemented
        return self._comparison_tuple() < other._comparison_tuple()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Version):
            return NotImplemented
        return self._comparison_tuple() == other._comparison_tuple()

    def __str__(self) -> str:
        base = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            return f"{base}-{self.prerelease}"
        return base

    def __hash__(self) -> int:
        return hash(self._comparison_tuple())


class VersionRange:
    """Represents a range of versions for compilation."""

    def __init__(self, start: Version, end: Optional[Version] = None):
        self.start = start
        self.end = end

    def contains(self, version: Version) -> bool:
        """Check if version falls within range (exclusive start, inclusive end)."""
        if version <= self.start:
            return False
        if self.end and version > self.end:
            return False
        return True

    def filter_versions(self, versions: List[Version]) -> List[Version]:
        """Filter and sort versions within range."""
        filtered = [v for v in versions if self.contains(v)]
        return sorted(filtered)
