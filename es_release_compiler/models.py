"""Data models for release notes."""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Set
from enum import Enum

from .version import Version


class SectionType(Enum):
    BREAKING_CHANGES = "breaking_changes"
    KNOWN_ISSUES = "known_issues"
    DEPRECATIONS = "deprecations"
    HIGHLIGHTS = "highlights"
    NEW_FEATURES = "new_features"
    ENHANCEMENTS = "enhancements"
    BUG_FIXES = "bug_fixes"
    UPGRADES = "upgrades"


@dataclass
class ReleaseItem:
    """Individual item within a release section."""

    description: str
    category: Optional[str] = None
    pr_number: Optional[int] = None
    pr_url: Optional[str] = None
    issue_number: Optional[int] = None
    issue_url: Optional[str] = None
    impact: Optional[str] = None
    action: Optional[str] = None

    def get_dedup_key(self) -> str:
        """Get a key for deduplication - use PR number if available, else description."""
        if self.pr_number:
            return f"pr:{self.pr_number}"
        # Normalize description for comparison
        return f"desc:{self.description.lower().strip()[:100]}"


@dataclass
class ConsolidatedItem:
    """An item that appears in one or more versions."""

    description: str
    versions: List[Version] = field(default_factory=list)
    category: Optional[str] = None
    pr_number: Optional[int] = None
    pr_url: Optional[str] = None
    issue_number: Optional[int] = None
    issue_url: Optional[str] = None
    impact: Optional[str] = None
    action: Optional[str] = None

    @classmethod
    def from_release_item(cls, item: ReleaseItem, version: Version) -> 'ConsolidatedItem':
        return cls(
            description=item.description,
            versions=[version],
            category=item.category,
            pr_number=item.pr_number,
            pr_url=item.pr_url,
            issue_number=item.issue_number,
            issue_url=item.issue_url,
            impact=item.impact,
            action=item.action,
        )

    def add_version(self, version: Version):
        if version not in self.versions:
            self.versions.append(version)
            self.versions.sort()

    @property
    def version_range_str(self) -> str:
        """Return a compact version string like '[9.0.3, 9.1.2]' or '[8.17.0]'."""
        if len(self.versions) == 1:
            return f"[{self.versions[0]}]"
        return f"[{', '.join(str(v) for v in self.versions)}]"


@dataclass
class ReleaseSection:
    """A section within release notes (e.g., Bug Fixes, Breaking Changes)."""

    section_type: SectionType
    items: List[ReleaseItem] = field(default_factory=list)

    def is_empty(self) -> bool:
        return len(self.items) == 0

    def items_by_category(self) -> Dict[str, List[ReleaseItem]]:
        """Group items by category."""
        grouped: Dict[str, List[ReleaseItem]] = {}
        for item in self.items:
            cat = item.category or "General"
            grouped.setdefault(cat, []).append(item)
        return grouped


@dataclass
class ReleaseNote:
    """Complete release notes for a single version."""

    version: Version
    product: str = "elasticsearch"
    sections: Dict[SectionType, ReleaseSection] = field(default_factory=dict)
    release_date: Optional[str] = None
    source_url: Optional[str] = None

    def get_section(self, section_type: SectionType) -> Optional[ReleaseSection]:
        return self.sections.get(section_type)

    def has_breaking_changes(self) -> bool:
        section = self.get_section(SectionType.BREAKING_CHANGES)
        return section is not None and not section.is_empty()

    def has_deprecations(self) -> bool:
        section = self.get_section(SectionType.DEPRECATIONS)
        return section is not None and not section.is_empty()


@dataclass
class CompiledReleaseNotes:
    """Compiled release notes across multiple versions."""

    product: str
    start_version: Version
    end_version: Version
    releases: List[ReleaseNote] = field(default_factory=list)

    def get_consolidated_section(self, section_type: SectionType) -> List[ConsolidatedItem]:
        """Get deduplicated items for a section type, grouped across versions."""
        items_by_key: Dict[str, ConsolidatedItem] = {}

        for release in self.releases:
            section = release.get_section(section_type)
            if not section:
                continue

            for item in section.items:
                key = item.get_dedup_key()
                if key in items_by_key:
                    # Add this version to existing item
                    items_by_key[key].add_version(release.version)
                else:
                    # Create new consolidated item
                    items_by_key[key] = ConsolidatedItem.from_release_item(item, release.version)

        # Sort by earliest version (ascending)
        result = list(items_by_key.values())
        result.sort(key=lambda x: x.versions[0])
        return result

    def get_consolidated_by_category(self, section_type: SectionType) -> Dict[str, List[ConsolidatedItem]]:
        """Get deduplicated items grouped by category."""
        items = self.get_consolidated_section(section_type)
        by_category: Dict[str, List[ConsolidatedItem]] = {}
        for item in items:
            cat = item.category or "General"
            by_category.setdefault(cat, []).append(item)
        return by_category

    @property
    def all_breaking_changes(self) -> List[ConsolidatedItem]:
        """Extract all breaking changes, deduplicated."""
        return self.get_consolidated_section(SectionType.BREAKING_CHANGES)

    @property
    def all_deprecations(self) -> List[ConsolidatedItem]:
        """Extract all deprecations, deduplicated."""
        return self.get_consolidated_section(SectionType.DEPRECATIONS)

    @property
    def all_enhancements(self) -> List[ConsolidatedItem]:
        """Extract all enhancements, deduplicated."""
        return self.get_consolidated_section(SectionType.ENHANCEMENTS)

    @property
    def all_bug_fixes(self) -> List[ConsolidatedItem]:
        """Extract all bug fixes, deduplicated."""
        return self.get_consolidated_section(SectionType.BUG_FIXES)

    @property
    def all_new_features(self) -> List[ConsolidatedItem]:
        """Extract all new features, deduplicated."""
        return self.get_consolidated_section(SectionType.NEW_FEATURES)

    @property
    def all_known_issues(self) -> List[ConsolidatedItem]:
        """Extract all known issues, deduplicated."""
        return self.get_consolidated_section(SectionType.KNOWN_ISSUES)
