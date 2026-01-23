"""Parser for 9.x documentation HTML structure (consolidated pages)."""

from typing import Optional, List
import re
import logging

from bs4 import BeautifulSoup, Tag

from ..version import Version
from ..models import ReleaseNote, ReleaseSection, ReleaseItem, SectionType

logger = logging.getLogger(__name__)


class ModernParser:
    """Parser for 9.x documentation HTML structure (consolidated pages)."""

    SECTION_MAPPINGS = {
        "known issues": SectionType.KNOWN_ISSUES,
        "breaking changes": SectionType.BREAKING_CHANGES,
        "deprecations": SectionType.DEPRECATIONS,
        "deprecation": SectionType.DEPRECATIONS,
        "highlights": SectionType.HIGHLIGHTS,
        "new features": SectionType.NEW_FEATURES,
        "features": SectionType.NEW_FEATURES,
        "enhancements": SectionType.ENHANCEMENTS,
        "enhancement": SectionType.ENHANCEMENTS,
        "bug fixes": SectionType.BUG_FIXES,
        "fixes": SectionType.BUG_FIXES,
        "upgrades": SectionType.UPGRADES,
    }

    PR_PATTERN = re.compile(r'\[#(\d+)\]\((https://github\.com/[^)]+/(?:pull|issues)/\d+)\)')
    PR_SIMPLE_PATTERN = re.compile(r'#(\d+)')

    def extract_version_list(self, html: str, product: str) -> List[Version]:
        """Extract versions from TOC anchors on consolidated page."""
        soup = BeautifulSoup(html, 'lxml')
        versions = []

        # Build product pattern - handle different product naming conventions
        # e.g., "elasticsearch" -> "elasticsearch"
        # e.g., "apm-agent-java" -> "elastic-apm-java-agent" (varies by product)
        product_lower = product.lower()

        # Pattern for version anchors with dots like "elasticsearch-9.0.0-release-notes"
        version_pattern_dots = re.compile(
            rf'{product_lower}-(\d+\.\d+\.\d+(?:-\w+\d*)?)',
            re.IGNORECASE
        )

        # Pattern for version anchors with dashes like "elastic-apm-java-agent-1-55-4-release-notes"
        # This handles products where versions use dashes instead of dots
        version_pattern_dashes = re.compile(
            r'-(\d+)-(\d+)-(\d+)(?:-(\w+))?-release-notes',
            re.IGNORECASE
        )

        # Also create a more flexible pattern for the product name in IDs
        # APM agents use "elastic-apm-{lang}-agent" format
        product_variants = [product_lower]
        if product_lower.startswith('apm-agent-'):
            lang = product_lower.replace('apm-agent-', '')
            product_variants.append(f'elastic-apm-{lang}-agent')
        if product_lower.startswith('edot-'):
            lang = product_lower.replace('edot-', '')
            product_variants.append(f'edot-{lang}')
            product_variants.append(f'elastic-otel-{lang}')

        # Check IDs of elements
        for elem in soup.find_all(id=True):
            elem_id = elem.get('id', '')

            # Try dots pattern first
            match = version_pattern_dots.search(elem_id)
            if match:
                try:
                    v = Version.parse(match.group(1))
                    versions.append(v)
                    continue
                except ValueError:
                    pass

            # Try dashes pattern for APM-style versions
            match = version_pattern_dashes.search(elem_id)
            if match:
                # Check if ID contains one of our product variants
                id_lower = elem_id.lower()
                if any(variant in id_lower for variant in product_variants):
                    try:
                        major, minor, patch = match.group(1), match.group(2), match.group(3)
                        prerelease = match.group(4) if match.lastindex >= 4 else None
                        version_str = f"{major}.{minor}.{patch}"
                        if prerelease:
                            version_str += f"-{prerelease}"
                        v = Version.parse(version_str)
                        versions.append(v)
                    except ValueError:
                        continue

        # Also check hrefs in links
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            if '#' not in href:
                continue

            # Try dots pattern
            match = version_pattern_dots.search(href)
            if match:
                try:
                    v = Version.parse(match.group(1))
                    versions.append(v)
                    continue
                except ValueError:
                    pass

            # Try dashes pattern
            match = version_pattern_dashes.search(href)
            if match:
                href_lower = href.lower()
                if any(variant in href_lower for variant in product_variants):
                    try:
                        major, minor, patch = match.group(1), match.group(2), match.group(3)
                        prerelease = match.group(4) if match.lastindex >= 4 else None
                        version_str = f"{major}.{minor}.{patch}"
                        if prerelease:
                            version_str += f"-{prerelease}"
                        v = Version.parse(version_str)
                        versions.append(v)
                    except ValueError:
                        continue

        # Also look for version patterns in headers
        for header in soup.find_all(['h2', 'h3']):
            header_text = header.get_text()
            simple_version = re.search(r'(\d+\.\d+\.\d+)', header_text)
            if simple_version:
                try:
                    v = Version.parse(simple_version.group(1))
                    versions.append(v)
                except ValueError:
                    continue

        return sorted(set(versions), reverse=True)

    def parse_release_notes_for_version(
        self, html: str, version: Version, product: str
    ) -> Optional[ReleaseNote]:
        """Extract release notes for specific version from consolidated page."""
        soup = BeautifulSoup(html, 'lxml')
        release = ReleaseNote(version=version, product=product)

        version_str = str(version)
        version_dashes = version_str.replace('.', '-')
        product_lower = product.lower()

        # Build possible ID patterns for this product/version combination
        possible_ids = [
            f"{product_lower}-{version_str}-release-notes",  # elasticsearch-9.0.0-release-notes
        ]

        # Add APM-style IDs
        if product_lower.startswith('apm-agent-'):
            lang = product_lower.replace('apm-agent-', '')
            possible_ids.append(f"elastic-apm-{lang}-agent-{version_dashes}-release-notes")

        # Add EDOT-style IDs
        if product_lower.startswith('edot-'):
            lang = product_lower.replace('edot-', '')
            possible_ids.append(f"edot-{lang}-{version_dashes}-release-notes")
            possible_ids.append(f"elastic-otel-{lang}-{version_dashes}-release-notes")

        # Try each possible ID pattern
        version_wrapper = None
        for version_id in possible_ids:
            version_wrapper = soup.find('div', id=version_id)
            if version_wrapper:
                break

        if not version_wrapper:
            # Fallback to searching headers
            for header in soup.find_all(['h2', 'h3']):
                if version_str in header.get_text():
                    version_wrapper = header.parent if header.parent and header.parent.name == 'div' else header
                    break

        if not version_wrapper:
            logger.debug(f"Could not find section for version {version}")
            return None

        # Extract content until next version header
        current_section_type: Optional[SectionType] = None
        current_category: Optional[str] = None

        for sibling in version_wrapper.find_next_siblings():
            # Stop at next version's release-notes wrapper
            if sibling.name == 'div':
                sibling_id = sibling.get('id', '')
                if sibling_id.endswith('-release-notes') and version_str not in sibling_id:
                    break

            # Handle heading-wrapper divs containing section headers (h3)
            if sibling.name == 'div' and 'heading-wrapper' in sibling.get('class', []):
                h3 = sibling.find('h3')
                if h3:
                    header_text = h3.get_text().lower().strip()

                    # Check if this is a different version's section
                    if re.search(r'\d+\.\d+\.\d+', header_text) and version_str not in header_text:
                        break

                    # Check for section type
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

            # Handle standalone h3 headers
            elif sibling.name == 'h3':
                header_text = sibling.get_text().lower().strip()

                if re.search(r'\d+\.\d+\.\d+', header_text) and version_str not in header_text:
                    break

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

            # Handle <details> dropdown elements (used for Highlights)
            elif sibling.name == 'details' and current_section_type:
                item = self._parse_details_item(sibling, current_category)
                if item:
                    section = release.sections.get(current_section_type)
                    if section:
                        section.items.append(item)

            # Handle category paragraphs (e.g., "Allocation:")
            elif sibling.name == 'p':
                text = sibling.get_text().strip()
                if text.endswith(':') and len(text) < 50:
                    current_category = text.rstrip(':').strip()

            # Handle h4 category headers
            elif sibling.name == 'h4' and current_section_type:
                current_category = sibling.get_text().strip()

            # Handle ul lists
            elif sibling.name == 'ul' and current_section_type:
                section = release.sections.get(current_section_type)
                if section:
                    for li in sibling.find_all('li', recursive=False):
                        item = self._parse_modern_item(li, current_category)
                        section.items.append(item)

        return release

    def _parse_modern_item(self, li: Tag, category: Optional[str]) -> ReleaseItem:
        """Parse item from modern format."""
        text = li.get_text().strip()

        # Look for impact/action in structured format
        impact = None
        action = None

        impact_elem = li.find('strong', string=re.compile(r'Impact', re.I))
        if impact_elem:
            next_text = impact_elem.next_sibling
            if next_text:
                impact = str(next_text).strip().lstrip(':').strip()

        action_elem = li.find('strong', string=re.compile(r'Action', re.I))
        if action_elem:
            next_text = action_elem.next_sibling
            if next_text:
                action = str(next_text).strip().lstrip(':').strip()

        pr_number = None
        pr_url = None
        issue_number = None
        issue_url = None

        # Find all anchor tags and look for GitHub PR/issue links
        for link in li.find_all('a', href=True):
            href = link.get('href', '')

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

        # Clean description - take first line
        description = text.split('\n')[0].strip()
        description = self.PR_SIMPLE_PATTERN.sub('', description)
        description = re.sub(r'\s+', ' ', description).strip()

        return ReleaseItem(
            description=description,
            category=category,
            pr_number=pr_number,
            pr_url=pr_url,
            impact=impact,
            action=action,
        )

    def parse_breaking_changes_for_version(
        self, html: str, version: Version, product: str = "elasticsearch"
    ) -> ReleaseSection:
        """Parse breaking changes from dedicated page for specific version."""
        soup = BeautifulSoup(html, 'lxml')
        section = ReleaseSection(SectionType.BREAKING_CHANGES)

        version_str = str(version)
        version_dashes = version_str.replace('.', '-')
        product_lower = product.lower()

        # Build possible ID patterns
        possible_ids = [
            f"{product_lower}-{version_str}-breaking-changes",
        ]

        if product_lower.startswith('apm-agent-'):
            lang = product_lower.replace('apm-agent-', '')
            possible_ids.append(f"elastic-apm-{lang}-agent-{version_dashes}-breaking-changes")

        if product_lower.startswith('edot-'):
            lang = product_lower.replace('edot-', '')
            possible_ids.append(f"edot-{lang}-{version_dashes}-breaking-changes")

        # Try each possible ID pattern
        version_wrapper = None
        for version_id in possible_ids:
            version_wrapper = soup.find('div', id=version_id)
            if version_wrapper:
                break

        if not version_wrapper:
            # Fallback to searching headers
            for header in soup.find_all(['h2', 'h3']):
                if version_str in header.get_text():
                    version_wrapper = header.parent if header.parent.name == 'div' else header
                    break

        if not version_wrapper:
            return section

        # Get all following siblings until the next version section
        current_category: Optional[str] = None
        found_content = False

        for sibling in version_wrapper.find_next_siblings():
            # Stop at next version heading wrapper
            if sibling.name == 'div' and sibling.get('class') and 'heading-wrapper' in sibling.get('class', []):
                break
            if sibling.name == 'div' and sibling.get('id', '').endswith('-breaking-changes'):
                break

            # Check for "no breaking changes" text
            if sibling.name == 'p':
                text = sibling.get_text().strip()
                if 'no breaking changes' in text.lower():
                    return section
                # Check for category (ends with colon)
                if text.endswith(':') and len(text) < 50:
                    current_category = text.rstrip(':').strip()
                    found_content = True

            # Handle <details> dropdown elements (modern breaking changes format)
            elif sibling.name == 'details':
                item = self._parse_details_item(sibling, current_category)
                if item:
                    section.items.append(item)
                    found_content = True

            elif sibling.name == 'ul':
                for li in sibling.find_all('li', recursive=False):
                    item = self._parse_modern_item(li, current_category)
                    section.items.append(item)
                    found_content = True

        return section

    def _parse_details_item(self, details: Tag, category: Optional[str]) -> Optional[ReleaseItem]:
        """Parse a <details> dropdown element for breaking changes."""
        # Get the summary/title
        summary = details.find('summary')
        if not summary:
            return None

        # Title is in dropdown-title__summary-text or just the summary text
        title_elem = summary.find(class_='dropdown-title__summary-text')
        if title_elem:
            title = title_elem.get_text().strip()
        else:
            title = summary.get_text().strip()

        if not title:
            return None

        # Get the content div
        content = details.find(class_='dropdown-content') or details.find('div')

        description = title
        impact = None
        action = None
        pr_number = None
        pr_url = None

        if content:
            # Extract full description from first paragraph(s) before Impact
            paragraphs = content.find_all('p')
            desc_parts = []
            for p in paragraphs:
                p_text = p.get_text().strip()
                if p_text.startswith('Impact:') or p_text.startswith('**Impact'):
                    break
                if not p_text.startswith('Action:') and not p_text.startswith('**Action'):
                    if not p_text.startswith('For more information'):
                        desc_parts.append(p_text)

            if desc_parts:
                description = title + " - " + " ".join(desc_parts)

            # Extract Impact
            for p in paragraphs:
                p_text = p.get_text().strip()
                if 'Impact:' in p_text:
                    impact = p_text.replace('Impact:', '').strip()
                    break

            # Extract Action
            for p in paragraphs:
                p_text = p.get_text().strip()
                if 'Action:' in p_text:
                    action = p_text.replace('Action:', '').strip()
                    break

            # Extract PR link
            for link in content.find_all('a', href=True):
                href = link.get('href', '')
                pr_match = re.search(r'github\.com/[^/]+/[^/]+/pull/(\d+)', href)
                if pr_match:
                    pr_number = int(pr_match.group(1))
                    pr_url = href
                    break

        return ReleaseItem(
            description=description,
            category=category,
            pr_number=pr_number,
            pr_url=pr_url,
            impact=impact,
            action=action,
        )

    def parse_deprecations_for_version(
        self, html: str, version: Version
    ) -> ReleaseSection:
        """Parse deprecations from dedicated page for specific version."""
        soup = BeautifulSoup(html, 'lxml')
        section = ReleaseSection(SectionType.DEPRECATIONS)

        version_str = str(version)
        version_header = None

        for header in soup.find_all(['h2', 'h3']):
            if version_str in header.get_text():
                version_header = header
                break

        if not version_header:
            return section

        next_elem = version_header.find_next_sibling()
        if next_elem and 'no deprecation' in next_elem.get_text().lower():
            return section

        current_category: Optional[str] = None

        for sibling in version_header.find_next_siblings():
            if sibling.name in ('h2',):
                sibling_text = sibling.get_text()
                if re.search(r'\d+\.\d+\.\d+', sibling_text) and version_str not in sibling_text:
                    break

            if sibling.name in ('h3', 'h4'):
                text = sibling.get_text()
                if re.search(r'\d+\.\d+\.\d+', text) and version_str not in text:
                    break
                current_category = text.strip()

            elif sibling.name == 'ul':
                for li in sibling.find_all('li', recursive=False):
                    item = self._parse_modern_item(li, current_category)
                    section.items.append(item)

        return section

    def parse_known_issues_for_version(
        self, html: str, version: Version
    ) -> ReleaseSection:
        """Parse known issues from dedicated page for specific version."""
        soup = BeautifulSoup(html, 'lxml')
        section = ReleaseSection(SectionType.KNOWN_ISSUES)

        version_str = str(version)
        version_header = None

        for header in soup.find_all(['h2', 'h3']):
            if version_str in header.get_text():
                version_header = header
                break

        if not version_header:
            return section

        current_category: Optional[str] = None

        for sibling in version_header.find_next_siblings():
            if sibling.name in ('h2',):
                sibling_text = sibling.get_text()
                if re.search(r'\d+\.\d+\.\d+', sibling_text) and version_str not in sibling_text:
                    break

            if sibling.name in ('h3', 'h4'):
                text = sibling.get_text()
                if re.search(r'\d+\.\d+\.\d+', text) and version_str not in text:
                    break
                current_category = text.strip()

            elif sibling.name == 'ul':
                for li in sibling.find_all('li', recursive=False):
                    item = self._parse_modern_item(li, current_category)
                    section.items.append(item)

        return section
