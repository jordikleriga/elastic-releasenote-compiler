"""HTML output generation for release notes."""

from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

from .models import CompiledReleaseNotes, SectionType, ConsolidatedItem
from .version import Version
from .config import PRODUCTS, MODERN_DOCS_MIN_VERSION, LATEST_8X_MINOR


# Elastic brand colors
ELASTIC_YELLOW = "#FEC514"
ELASTIC_BLUE = "#0077CC"
ELASTIC_DARK = "#1B1B1B"
ELASTIC_GRAY = "#69707D"
WARNING_RED = "#BD271E"
WARNING_BG = "#FFF3F2"


class HTMLGenerator:
    """Generates HTML output for compiled release notes."""

    SECTION_HEADERS = {
        SectionType.BREAKING_CHANGES: "Breaking Changes",
        SectionType.KNOWN_ISSUES: "Known Issues",
        SectionType.DEPRECATIONS: "Deprecations",
        SectionType.HIGHLIGHTS: "Highlights",
        SectionType.NEW_FEATURES: "Features & Enhancements",
        SectionType.ENHANCEMENTS: "Features & Enhancements",
        SectionType.BUG_FIXES: "Bug Fixes",
        SectionType.UPGRADES: "Upgrades",
    }

    SECTION_ORDER = [
        SectionType.NEW_FEATURES,
        SectionType.BUG_FIXES,
        SectionType.UPGRADES,
        SectionType.KNOWN_ISSUES,
        SectionType.DEPRECATIONS,
        SectionType.BREAKING_CHANGES,
    ]

    MERGED_SECTIONS = {
        SectionType.ENHANCEMENTS: SectionType.NEW_FEATURES,
    }

    def __init__(self, include_pr_links: bool = True):
        self.include_pr_links = include_pr_links

    def generate(
        self,
        compiled_notes: Dict[str, CompiledReleaseNotes],
        output_path: str,
        start_version: str,
        end_version: Optional[str] = None,
    ):
        """Generate HTML from compiled release notes."""
        html = self._build_html(compiled_notes, start_version, end_version)

        Path(output_path).write_text(html, encoding="utf-8")

    def _build_html(
        self,
        compiled_notes: Dict[str, CompiledReleaseNotes],
        start_version: str,
        end_version: Optional[str],
    ) -> str:
        """Build the complete HTML document."""
        end_display = end_version or "Latest"
        products = [PRODUCTS[p].display_name for p in compiled_notes.keys()]
        total_versions = sum(len(notes.releases) for notes in compiled_notes.values())

        html_parts = [
            self._get_html_head(start_version, end_display),
            '<body>',
            self._create_cover_section(start_version, end_display, products, total_versions),
            self._create_toc(compiled_notes),
        ]

        for product_name, notes in compiled_notes.items():
            html_parts.append(self._create_product_section(product_name, notes))

        html_parts.extend([
            self._create_footer(),
            '</body>',
            '</html>',
        ])

        return '\n'.join(html_parts)

    def _get_html_head(self, start_version: str, end_version: str) -> str:
        """Generate HTML head with styles."""
        return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Elastic Stack Release Notes: {start_version} → {end_version}</title>
    <style>
        :root {{
            --elastic-yellow: {ELASTIC_YELLOW};
            --elastic-blue: {ELASTIC_BLUE};
            --elastic-dark: {ELASTIC_DARK};
            --elastic-gray: {ELASTIC_GRAY};
            --warning-red: {WARNING_RED};
            --warning-bg: {WARNING_BG};
        }}

        * {{
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            line-height: 1.6;
            color: var(--elastic-dark);
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #fafafa;
        }}

        .cover {{
            text-align: center;
            padding: 60px 20px;
            background: white;
            border-radius: 8px;
            margin-bottom: 30px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}

        .cover h1 {{
            font-size: 2.5em;
            color: var(--elastic-dark);
            margin-bottom: 20px;
        }}

        .cover .subtitle {{
            font-size: 1.2em;
            color: var(--elastic-gray);
            margin: 10px 0;
        }}

        .cover .disclaimer {{
            margin-top: 40px;
            font-size: 0.9em;
            color: var(--elastic-gray);
        }}

        .toc {{
            background: white;
            padding: 30px;
            border-radius: 8px;
            margin-bottom: 30px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}

        .toc h2 {{
            color: var(--elastic-dark);
            border-bottom: 2px solid var(--elastic-yellow);
            padding-bottom: 10px;
        }}

        .toc-product {{
            margin: 20px 0;
        }}

        .toc-product > a {{
            font-size: 1.2em;
            font-weight: bold;
            color: var(--elastic-blue);
            text-decoration: none;
        }}

        .toc-product > a:hover {{
            text-decoration: underline;
        }}

        .toc-summary {{
            font-size: 0.9em;
            color: var(--elastic-gray);
            margin: 5px 0 10px 0;
        }}

        .toc-sections {{
            margin-left: 20px;
        }}

        .toc-section {{
            margin: 5px 0;
        }}

        .toc-section a {{
            color: var(--elastic-dark);
            text-decoration: none;
        }}

        .toc-section a:hover {{
            color: var(--elastic-blue);
        }}

        .toc-section.breaking a {{
            color: var(--warning-red);
        }}

        .toc-categories {{
            margin-left: 20px;
            font-size: 0.85em;
            color: var(--elastic-gray);
        }}

        .product-section {{
            background: white;
            padding: 30px;
            border-radius: 8px;
            margin-bottom: 30px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}

        .product-header {{
            color: var(--elastic-blue);
            font-size: 1.8em;
            border-bottom: 3px solid var(--elastic-yellow);
            padding-bottom: 10px;
            margin-bottom: 10px;
        }}

        .version-info {{
            color: var(--elastic-gray);
            font-style: italic;
            margin-bottom: 20px;
        }}

        .section {{
            margin: 30px 0;
        }}

        .section-header {{
            font-size: 1.3em;
            color: var(--elastic-dark);
            border-bottom: 1px solid #ddd;
            padding-bottom: 8px;
            margin-bottom: 15px;
        }}

        .section-header.warning {{
            color: var(--warning-red);
        }}

        .warning-banner {{
            background: var(--warning-bg);
            border-left: 4px solid var(--warning-red);
            padding: 12px 15px;
            margin-bottom: 15px;
            font-size: 0.95em;
        }}

        .category {{
            margin: 20px 0;
        }}

        .category-header {{
            font-size: 1.1em;
            color: var(--elastic-gray);
            margin-bottom: 10px;
        }}

        .item {{
            margin: 10px 0;
            padding-left: 20px;
            position: relative;
        }}

        .item::before {{
            content: "•";
            position: absolute;
            left: 5px;
            color: var(--elastic-gray);
        }}

        .item .version-tag {{
            font-weight: bold;
            color: var(--elastic-blue);
        }}

        .item .version-tag a {{
            color: var(--elastic-blue);
            text-decoration: none;
        }}

        .item .version-tag a:hover {{
            text-decoration: underline;
        }}

        .item .pr-link {{
            color: var(--elastic-blue);
            text-decoration: none;
            font-size: 0.9em;
        }}

        .item .pr-link:hover {{
            text-decoration: underline;
        }}

        .impact-action {{
            margin-left: 20px;
            font-size: 0.9em;
            color: var(--elastic-gray);
            margin-top: 3px;
        }}

        .footer {{
            text-align: center;
            padding: 20px;
            color: var(--elastic-gray);
            font-size: 0.9em;
        }}

        @media print {{
            body {{
                background: white;
                max-width: none;
            }}

            .cover, .toc, .product-section {{
                box-shadow: none;
                page-break-inside: avoid;
            }}

            .product-section {{
                page-break-before: always;
            }}
        }}
    </style>
</head>'''

    def _create_cover_section(
        self,
        start_version: str,
        end_version: str,
        products: List[str],
        total_versions: int,
    ) -> str:
        """Create the cover section."""
        return f'''
<div class="cover">
    <h1>Elastic Stack Release Notes</h1>
    <div class="subtitle">Versions: {start_version} → {end_version}</div>
    <div class="subtitle">Products: {', '.join(products)}</div>
    <div class="subtitle">Versions Covered: {total_versions}</div>
    <div class="disclaimer">
        <p>This document was compiled as a best effort summary.</p>
        <p>For the most up-to-date information, please visit:<br>
        <a href="https://www.elastic.co/docs/release-notes/">https://www.elastic.co/docs/release-notes/</a></p>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
    </div>
</div>'''

    def _make_anchor_name(self, *parts: str) -> str:
        """Create a valid anchor name from parts."""
        return "_".join(p.lower().replace(" ", "_").replace("-", "_") for p in parts)

    def _get_merged_section_items(
        self,
        notes: CompiledReleaseNotes,
        section_type: SectionType
    ) -> Dict[str, List[ConsolidatedItem]]:
        """Get consolidated items by category, merging any sections that should be combined."""
        items_by_category: Dict[str, List[ConsolidatedItem]] = {}

        primary_items = notes.get_consolidated_by_category(section_type)
        for cat, items in primary_items.items():
            items_by_category.setdefault(cat, []).extend(items)

        for source_type, target_type in self.MERGED_SECTIONS.items():
            if target_type == section_type:
                source_items = notes.get_consolidated_by_category(source_type)
                for cat, items in source_items.items():
                    items_by_category.setdefault(cat, []).extend(items)

        for cat in items_by_category:
            items_by_category[cat].sort(key=lambda x: x.versions[0])

        return items_by_category

    def _create_toc(self, compiled_notes: Dict[str, CompiledReleaseNotes]) -> str:
        """Create table of contents."""
        parts = ['<div class="toc">', '<h2>Table of Contents</h2>']

        for product_name, notes in compiled_notes.items():
            display_name = PRODUCTS[product_name].display_name
            product_anchor = self._make_anchor_name(product_name)

            parts.append(f'<div class="toc-product">')
            parts.append(f'<a href="#{product_anchor}">{display_name}</a>')

            # Summary
            total_items = sum(
                sum(len(items) for items in self._get_merged_section_items(notes, st).values())
                for st in self.SECTION_ORDER
            )
            breaking_count = len(notes.all_breaking_changes)
            deprecation_count = len(notes.all_deprecations)

            summary_parts = [f"{len(notes.releases)} versions", f"{total_items} total items"]
            if breaking_count > 0:
                summary_parts.append(f'<span style="color: {WARNING_RED}">{breaking_count} breaking changes</span>')
            if deprecation_count > 0:
                summary_parts.append(f"{deprecation_count} deprecations")

            parts.append(f'<div class="toc-summary">{" · ".join(summary_parts)}</div>')
            parts.append('<div class="toc-sections">')

            for section_type in self.SECTION_ORDER:
                items_by_category = self._get_merged_section_items(notes, section_type)
                if not items_by_category:
                    continue

                section_name = self.SECTION_HEADERS[section_type]
                section_anchor = self._make_anchor_name(product_name, section_name)
                total_section_items = sum(len(items) for items in items_by_category.values())

                css_class = "toc-section breaking" if section_type == SectionType.BREAKING_CHANGES else "toc-section"
                parts.append(f'<div class="{css_class}">')
                parts.append(f'<a href="#{section_anchor}">{section_name}</a> ({total_section_items} items)')

                if len(items_by_category) > 1:
                    cat_links = []
                    for cat_name in sorted(items_by_category.keys()):
                        cat_count = len(items_by_category[cat_name])
                        cat_anchor = self._make_anchor_name(product_name, section_name, cat_name)
                        cat_links.append(f'<a href="#{cat_anchor}">{cat_name}</a> ({cat_count})')
                    parts.append(f'<div class="toc-categories">{" · ".join(cat_links)}</div>')

                parts.append('</div>')

            parts.append('</div>')  # toc-sections
            parts.append('</div>')  # toc-product

        parts.append('</div>')
        return '\n'.join(parts)

    def _create_product_section(
        self,
        product_name: str,
        notes: CompiledReleaseNotes
    ) -> str:
        """Create consolidated content section for a product."""
        display_name = PRODUCTS[product_name].display_name
        product_anchor = self._make_anchor_name(product_name)

        parts = [
            f'<div class="product-section" id="{product_anchor}">',
            f'<h2 class="product-header">{display_name}</h2>',
            f'<div class="version-info">Versions {notes.start_version} → {notes.end_version} ({len(notes.releases)} releases)</div>',
        ]

        for section_type in self.SECTION_ORDER:
            section_html = self._create_consolidated_section(notes, section_type, product_name)
            if section_html:
                parts.append(section_html)

        parts.append('</div>')
        return '\n'.join(parts)

    def _create_consolidated_section(
        self,
        notes: CompiledReleaseNotes,
        section_type: SectionType,
        product_name: str
    ) -> Optional[str]:
        """Create a consolidated section."""
        items_by_category = self._get_merged_section_items(notes, section_type)

        if not items_by_category:
            return None

        section_name = self.SECTION_HEADERS[section_type]
        section_anchor = self._make_anchor_name(product_name, section_name)

        parts = [f'<div class="section" id="{section_anchor}">']

        if section_type == SectionType.BREAKING_CHANGES:
            parts.append(f'<h3 class="section-header warning">{section_name}</h3>')
            parts.append('<div class="warning-banner"><strong>Important:</strong> Review all breaking changes before upgrading.</div>')
        else:
            parts.append(f'<h3 class="section-header">{section_name}</h3>')

        for category in sorted(items_by_category.keys()):
            items = items_by_category[category]
            category_anchor = self._make_anchor_name(product_name, section_name, category)

            parts.append(f'<div class="category" id="{category_anchor}">')
            parts.append(f'<h4 class="category-header">{self._escape_html(category)}</h4>')

            for item in items:
                parts.append(self._create_consolidated_item(item, product_name, section_type))

            parts.append('</div>')

        parts.append('</div>')
        return '\n'.join(parts)

    def _get_version_url(self, version: Version, product_name: str, section_type: SectionType) -> str:
        """Build URL to the specific section on the Elastic docs site for a version."""
        product_config = PRODUCTS[product_name]

        legacy_section_anchors = {
            SectionType.BUG_FIXES: "bug",
            SectionType.NEW_FEATURES: "enhancement",
            SectionType.ENHANCEMENTS: "enhancement",
            SectionType.BREAKING_CHANGES: "breaking",
            SectionType.DEPRECATIONS: "deprecation",
            SectionType.KNOWN_ISSUES: "known-issue",
            SectionType.HIGHLIGHTS: "highlight",
            SectionType.UPGRADES: "upgrade",
        }

        modern_section_anchors = {
            SectionType.BUG_FIXES: "fixes",
            SectionType.NEW_FEATURES: "features-enhancements",
            SectionType.ENHANCEMENTS: "features-enhancements",
            SectionType.BREAKING_CHANGES: "breaking-changes",
            SectionType.DEPRECATIONS: "deprecations",
            SectionType.KNOWN_ISSUES: "known-issues",
            SectionType.HIGHLIGHTS: "highlights",
            SectionType.UPGRADES: "upgrades",
        }

        if version >= MODERN_DOCS_MIN_VERSION:
            base_url = product_config.modern_base_url
            section_anchor = modern_section_anchors.get(section_type, "")
            if section_anchor:
                return f"{base_url}#{product_name}-{version}-{section_anchor}"
            else:
                return f"{base_url}#{product_name}-{version}-release-notes"
        else:
            base_url = product_config.legacy_base_url
            anchor = legacy_section_anchors.get(section_type, "")
            if anchor:
                return f"{base_url}/{LATEST_8X_MINOR}/release-notes-{version}.html#{anchor}-{version}"
            else:
                return f"{base_url}/{LATEST_8X_MINOR}/release-notes-{version}.html"

    def _create_consolidated_item(
        self, item: ConsolidatedItem, product_name: str, section_type: SectionType
    ) -> str:
        """Create HTML for a consolidated item with version tags."""
        parts = ['<div class="item">']

        # Build version tag with hyperlinks
        version_links = []
        for v in item.versions:
            url = self._get_version_url(v, product_name, section_type)
            version_links.append(f'<a href="{url}">{v}</a>')

        if len(version_links) == 1:
            version_tag = f"[{version_links[0]}]"
        else:
            version_tag = f"[{', '.join(version_links)}]"

        text = f'<span class="version-tag">{version_tag}</span> {self._escape_html(item.description)}'

        if item.pr_number and self.include_pr_links:
            if item.pr_url:
                text += f' <a href="{item.pr_url}" class="pr-link">[#{item.pr_number}]</a>'
            else:
                text += f" [#{item.pr_number}]"

        parts.append(text)

        if item.impact:
            parts.append(f'<div class="impact-action"><strong>Impact:</strong> {self._escape_html(item.impact)}</div>')
        if item.action:
            parts.append(f'<div class="impact-action"><strong>Action:</strong> {self._escape_html(item.action)}</div>')

        parts.append('</div>')
        return '\n'.join(parts)

    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters."""
        if not text:
            return ""
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
        )

    def _create_footer(self) -> str:
        """Create footer section."""
        return '''
<div class="footer">
    <p>Generated by ES Release Compiler</p>
</div>'''
