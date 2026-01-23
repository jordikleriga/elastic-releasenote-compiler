"""Parser for 8.x documentation HTML structure."""

from typing import Optional, List
import re
import logging

from bs4 import BeautifulSoup, Tag

from ..version import Version
from ..models import ReleaseNote, ReleaseSection, ReleaseItem, SectionType

logger = logging.getLogger(__name__)


class LegacyParser:
    """Parser for 8.x documentation HTML structure."""

    # Section heading mappings
    SECTION_MAPPINGS = {
        "known issues": SectionType.KNOWN_ISSUES,
        "breaking changes": SectionType.BREAKING_CHANGES,
        "deprecations": SectionType.DEPRECATIONS,
        "deprecation": SectionType.DEPRECATIONS,
        "highlights": SectionType.HIGHLIGHTS,
        "new features": SectionType.NEW_FEATURES,
        "enhancements": SectionType.ENHANCEMENTS,
        "enhancement": SectionType.ENHANCEMENTS,
        "bug fixes": SectionType.BUG_FIXES,
        "fixes": SectionType.BUG_FIXES,
        "upgrades": SectionType.UPGRADES,
    }

    PR_PATTERN = re.compile(r'\[#(\d+)\]\((https://github\.com/[^)]+/pull/\d+)\)')
    ISSUE_PATTERN = re.compile(r'\(issue:\s*\[#?(\d+)\]\(([^)]+)\)\)')
    PR_SIMPLE_PATTERN = re.compile(r'#(\d+)')

    def extract_version_list(self, html: str) -> List[Version]:
        """Extract all version links from release notes index."""
        soup = BeautifulSoup(html, 'lxml')
        versions = []
        version_pattern = re.compile(r'release-notes-(\d+\.\d+\.\d+(?:-\w+\d*)?)')

        for link in soup.find_all('a', href=version_pattern):
            match = version_pattern.search(link['href'])
            if match:
                try:
                    versions.append(Version.parse(match.group(1)))
                except ValueError:
                    continue

        return sorted(set(versions), reverse=True)

    def parse_release_notes(self, html: str, version: Version, product: str) -> ReleaseNote:
        """Parse a single release notes page."""
        soup = BeautifulSoup(html, 'lxml')
        release = ReleaseNote(version=version, product=product)

        # Find the main content area
        content = soup.find('div', class_='chapter') or soup.find('article') or soup.body

        if not content:
            logger.warning(f"Could not find content area for {version}")
            return release

        current_section_type: Optional[SectionType] = None
        current_category: Optional[str] = None

        for element in content.find_all(['h2', 'h3', 'h4', 'ul', 'dl']):
            if element.name in ('h2', 'h3'):
                header_text = element.get_text().lower().strip()

                # Check if this is a section header
                matched_section = None
                for pattern, section_type in self.SECTION_MAPPINGS.items():
                    if pattern in header_text:
                        matched_section = section_type
                        break

                if matched_section:
                    current_section_type = matched_section
                    if current_section_type not in release.sections:
                        release.sections[current_section_type] = ReleaseSection(current_section_type)
                    current_category = None
                elif current_section_type:
                    # This might be a category header
                    current_category = element.get_text().strip()

            elif element.name == 'h4' and current_section_type:
                current_category = element.get_text().strip()

            elif element.name == 'ul' and current_section_type:
                section = release.sections.get(current_section_type)
                if section:
                    for li in element.find_all('li', recursive=False):
                        item = self._parse_list_item(li, current_category)
                        section.items.append(item)

            elif element.name == 'dl' and current_section_type:
                # Definition lists: <dt> is category, <dd> contains actual items
                section = release.sections.get(current_section_type)
                if section:
                    current_dl_category = current_category
                    for child in element.children:
                        if child.name == 'dt':
                            # This is a category header
                            current_dl_category = child.get_text().strip()
                        elif child.name == 'dd':
                            # This contains the actual item with PR link
                            item = self._parse_list_item(child, current_dl_category)
                            if item.description:  # Only add if there's content
                                section.items.append(item)

        return release

    def _parse_list_item(self, li: Tag, category: Optional[str]) -> ReleaseItem:
        """Parse a single list item into a ReleaseItem."""
        text = li.get_text().strip()

        pr_number = None
        pr_url = None
        issue_number = None
        issue_url = None

        # Find all anchor tags and look for GitHub PR/issue links
        for link in li.find_all('a', href=True):
            href = link.get('href', '')
            link_text = link.get_text().strip()

            # Check for PR link (github.com/.../pull/123)
            pr_match = re.search(r'github\.com/[^/]+/[^/]+/pull/(\d+)', href)
            if pr_match:
                pr_number = int(pr_match.group(1))
                pr_url = href
                continue

            # Check for issue link (github.com/.../issues/123)
            issue_match = re.search(r'github\.com/[^/]+/[^/]+/issues/(\d+)', href)
            if issue_match:
                issue_number = int(issue_match.group(1))
                issue_url = href
                continue

        # If no URL found but we have a PR number pattern in text, extract it
        if not pr_number:
            simple_match = self.PR_SIMPLE_PATTERN.search(text)
            if simple_match:
                pr_number = int(simple_match.group(1))
                # Build the URL if we know the repo
                pr_url = f"https://github.com/elastic/elasticsearch/pull/{pr_number}"

        # Clean description - remove PR/issue references
        description = self.PR_SIMPLE_PATTERN.sub('', text)
        description = re.sub(r'\s+', ' ', description).strip()

        return ReleaseItem(
            description=description,
            category=category,
            pr_number=pr_number,
            pr_url=pr_url,
            issue_number=issue_number,
            issue_url=issue_url,
        )

    def parse_breaking_changes(self, html: str, version: Version) -> ReleaseSection:
        """Parse migration guide for breaking changes."""
        soup = BeautifulSoup(html, 'lxml')
        section = ReleaseSection(SectionType.BREAKING_CHANGES)

        content = soup.find('div', class_='chapter') or soup.body
        if not content:
            return section

        current_category: Optional[str] = None
        in_relevant_section = False
        version_minor = version.major_minor

        for element in content.find_all(['h2', 'h3', 'h4', 'ul', 'dl', 'p']):
            if element.name == 'h2':
                header = element.get_text().lower()
                # Check if this section relates to our version
                in_relevant_section = (
                    version_minor in header or
                    'breaking' in header or
                    'migrat' in header
                )

            elif element.name in ('h3', 'h4') and in_relevant_section:
                current_category = element.get_text().strip()

            elif element.name == 'ul' and in_relevant_section:
                for li in element.find_all('li', recursive=False):
                    item = self._parse_list_item(li, current_category)
                    section.items.append(item)

            elif element.name == 'dl' and in_relevant_section:
                dts = element.find_all('dt')
                dds = element.find_all('dd')
                for dt, dd in zip(dts, dds):
                    item = ReleaseItem(
                        description=dt.get_text().strip(),
                        category=current_category,
                        impact=dd.get_text().strip() if dd else None,
                    )
                    section.items.append(item)

        return section
