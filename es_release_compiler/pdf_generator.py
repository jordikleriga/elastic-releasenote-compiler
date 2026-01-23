"""PDF output generation using reportlab."""

from datetime import datetime
from typing import Dict, List, Optional, Tuple

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Flowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT

from .models import CompiledReleaseNotes, SectionType, ConsolidatedItem
from .version import Version
from .config import PRODUCTS, MODERN_DOCS_MIN_VERSION, LATEST_8X_MINOR


class AnchorFlowable(Flowable):
    """Invisible flowable that creates a named anchor/bookmark."""

    def __init__(self, anchor_name: str):
        Flowable.__init__(self)
        self.anchor_name = anchor_name
        self.width = 0
        self.height = 0

    def draw(self):
        self.canv.bookmarkPage(self.anchor_name)

    def wrap(self, availWidth, availHeight):
        return (0, 0)


# Elastic brand colors
ELASTIC_YELLOW = colors.HexColor("#FEC514")
ELASTIC_BLUE = colors.HexColor("#0077CC")
ELASTIC_DARK = colors.HexColor("#1B1B1B")
ELASTIC_GRAY = colors.HexColor("#69707D")
WARNING_RED = colors.HexColor("#BD271E")
WARNING_BG = colors.HexColor("#FFF3F2")


class PDFGenerator:
    """Generates PDF output for compiled release notes."""

    SECTION_HEADERS = {
        SectionType.BREAKING_CHANGES: "Breaking Changes",
        SectionType.KNOWN_ISSUES: "Known Issues",
        SectionType.DEPRECATIONS: "Deprecations",
        SectionType.HIGHLIGHTS: "Highlights",
        SectionType.NEW_FEATURES: "Features & Enhancements",  # Combined section
        SectionType.ENHANCEMENTS: "Features & Enhancements",  # Combined section
        SectionType.BUG_FIXES: "Bug Fixes",
        SectionType.UPGRADES: "Upgrades",
    }

    # Order for consolidated sections (breaking changes at the end)
    # Note: ENHANCEMENTS is not listed - it gets merged into NEW_FEATURES
    SECTION_ORDER = [
        SectionType.HIGHLIGHTS,
        SectionType.NEW_FEATURES,  # This now includes enhancements
        SectionType.BUG_FIXES,
        SectionType.UPGRADES,
        SectionType.KNOWN_ISSUES,
        SectionType.DEPRECATIONS,
        SectionType.BREAKING_CHANGES,
    ]

    # Sections to merge together (source -> target)
    MERGED_SECTIONS = {
        SectionType.ENHANCEMENTS: SectionType.NEW_FEATURES,
    }

    def __init__(self, include_pr_links: bool = True):
        self.include_pr_links = include_pr_links
        self.styles = self._create_styles()

    def _create_styles(self) -> Dict:
        """Create custom paragraph styles."""
        styles = getSampleStyleSheet()

        # Title style
        styles.add(ParagraphStyle(
            name='CoverTitle',
            parent=styles['Title'],
            fontSize=28,
            textColor=ELASTIC_DARK,
            spaceAfter=20,
            alignment=TA_CENTER,
        ))

        # Subtitle style
        styles.add(ParagraphStyle(
            name='CoverSubtitle',
            parent=styles['Normal'],
            fontSize=14,
            textColor=ELASTIC_GRAY,
            alignment=TA_CENTER,
            spaceAfter=10,
        ))

        # Product header
        styles.add(ParagraphStyle(
            name='ProductHeader',
            parent=styles['Heading1'],
            fontSize=20,
            textColor=ELASTIC_BLUE,
            spaceBefore=20,
            spaceAfter=10,
        ))

        # Section header (Breaking Changes, etc.)
        styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=ELASTIC_DARK,
            spaceBefore=15,
            spaceAfter=8,
        ))

        # Warning section header (for breaking changes)
        styles.add(ParagraphStyle(
            name='WarningHeader',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=WARNING_RED,
            spaceBefore=15,
            spaceAfter=8,
        ))

        # Category header
        styles.add(ParagraphStyle(
            name='CategoryHeader',
            parent=styles['Heading3'],
            fontSize=12,
            textColor=ELASTIC_GRAY,
            spaceBefore=10,
            spaceAfter=5,
        ))

        # Item style
        styles.add(ParagraphStyle(
            name='Item',
            parent=styles['Normal'],
            fontSize=10,
            leftIndent=15,
            spaceBefore=2,
            spaceAfter=2,
        ))

        # Impact/Action style
        styles.add(ParagraphStyle(
            name='ImpactAction',
            parent=styles['Normal'],
            fontSize=9,
            leftIndent=30,
            textColor=ELASTIC_GRAY,
            spaceBefore=1,
            spaceAfter=1,
        ))

        # TOC styles
        styles.add(ParagraphStyle(
            name='TOCTitle',
            parent=styles['Heading1'],
            fontSize=22,
            textColor=ELASTIC_DARK,
            spaceBefore=0,
            spaceAfter=20,
        ))

        styles.add(ParagraphStyle(
            name='TOCProduct',
            parent=styles['Normal'],
            fontSize=14,
            textColor=ELASTIC_BLUE,
            fontName='Helvetica-Bold',
            spaceBefore=15,
            spaceAfter=5,
            leftIndent=0,
        ))

        styles.add(ParagraphStyle(
            name='TOCSection',
            parent=styles['Normal'],
            fontSize=11,
            textColor=ELASTIC_DARK,
            spaceBefore=3,
            spaceAfter=2,
            leftIndent=20,
        ))

        styles.add(ParagraphStyle(
            name='TOCCategory',
            parent=styles['Normal'],
            fontSize=9,
            textColor=ELASTIC_GRAY,
            spaceBefore=1,
            spaceAfter=1,
            leftIndent=40,
        ))

        styles.add(ParagraphStyle(
            name='TOCSummary',
            parent=styles['Normal'],
            fontSize=10,
            textColor=ELASTIC_GRAY,
            spaceBefore=5,
            spaceAfter=10,
            leftIndent=20,
        ))

        return styles

    def generate(
        self,
        compiled_notes: Dict[str, CompiledReleaseNotes],
        output_path: str,
        start_version: str,
        end_version: Optional[str] = None,
    ):
        """Generate PDF from compiled release notes."""
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=0.75 * inch,
            leftMargin=0.75 * inch,
            topMargin=0.75 * inch,
            bottomMargin=0.75 * inch,
        )

        story = []

        # Cover page
        story.extend(self._create_cover_page(compiled_notes, start_version, end_version))
        story.append(PageBreak())

        # Table of contents
        story.extend(self._create_toc(compiled_notes))
        story.append(PageBreak())

        # Consolidated content for each product
        for product_name, notes in compiled_notes.items():
            story.extend(self._create_product_section(product_name, notes))

        # Build PDF
        doc.build(story, onFirstPage=self._add_footer, onLaterPages=self._add_footer)

    def _create_cover_page(
        self,
        compiled_notes: Dict[str, CompiledReleaseNotes],
        start_version: str,
        end_version: Optional[str],
    ) -> List:
        """Create the cover page."""
        elements = []

        elements.append(Spacer(1, 2 * inch))

        # Title
        elements.append(Paragraph(
            "Elastic Stack Release Notes",
            self.styles['CoverTitle']
        ))

        elements.append(Spacer(1, 0.5 * inch))

        # Version range
        end_display = end_version or "Latest"
        elements.append(Paragraph(
            f"Versions: {start_version} → {end_display}",
            self.styles['CoverSubtitle']
        ))

        # Products included
        products = [PRODUCTS[p].display_name for p in compiled_notes.keys()]
        elements.append(Paragraph(
            f"Products: {', '.join(products)}",
            self.styles['CoverSubtitle']
        ))

        # Version count
        total_versions = sum(len(notes.releases) for notes in compiled_notes.values())
        elements.append(Paragraph(
            f"Versions Covered: {total_versions}",
            self.styles['CoverSubtitle']
        ))

        # Disclaimer
        elements.append(Spacer(1, 1 * inch))
        disclaimer_style = ParagraphStyle(
            name='Disclaimer',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=ELASTIC_GRAY,
            alignment=TA_CENTER,
            leading=14,
        )
        elements.append(Paragraph(
            "This document was compiled as a best effort summary.<br/>"
            "For the most up-to-date information, please visit:<br/>"
            '<a href="https://www.elastic.co/docs/release-notes/" color="#0077CC">'
            "https://www.elastic.co/docs/release-notes/</a>",
            disclaimer_style
        ))

        # Generation date at bottom
        elements.append(Spacer(1, 2 * inch))
        elements.append(Paragraph(
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            self.styles['CoverSubtitle']
        ))

        return elements

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

        # Get items from the primary section
        primary_items = notes.get_consolidated_by_category(section_type)
        for cat, items in primary_items.items():
            items_by_category.setdefault(cat, []).extend(items)

        # Check if any other sections should be merged into this one
        for source_type, target_type in self.MERGED_SECTIONS.items():
            if target_type == section_type:
                # Merge items from source section into this one
                source_items = notes.get_consolidated_by_category(source_type)
                for cat, items in source_items.items():
                    items_by_category.setdefault(cat, []).extend(items)

        # Sort items within each category by version
        for cat in items_by_category:
            items_by_category[cat].sort(key=lambda x: x.versions[0])

        return items_by_category

    def _create_toc(self, compiled_notes: Dict[str, CompiledReleaseNotes]) -> List:
        """Create table of contents with clickable links."""
        elements = []

        elements.append(Paragraph("Table of Contents", self.styles['TOCTitle']))

        for product_name, notes in compiled_notes.items():
            display_name = PRODUCTS[product_name].display_name
            product_anchor = self._make_anchor_name(product_name)

            # Product header with link
            elements.append(Paragraph(
                f'<a href="#{product_anchor}" color="#0077CC">{display_name}</a>',
                self.styles['TOCProduct']
            ))

            # Summary line - count items using merged sections
            total_items = sum(
                sum(len(items) for items in self._get_merged_section_items(notes, st).values())
                for st in self.SECTION_ORDER
            )
            breaking_count = len(notes.all_breaking_changes)
            deprecation_count = len(notes.all_deprecations)

            summary_parts = [f"{len(notes.releases)} versions"]
            summary_parts.append(f"{total_items} total items")
            if breaking_count > 0:
                summary_parts.append(f"<font color='#BD271E'>{breaking_count} breaking changes</font>")
            if deprecation_count > 0:
                summary_parts.append(f"{deprecation_count} deprecations")

            elements.append(Paragraph(
                f"<i>{' · '.join(summary_parts)}</i>",
                self.styles['TOCSummary']
            ))

            # Sections with links and category details
            for section_type in self.SECTION_ORDER:
                items_by_category = self._get_merged_section_items(notes, section_type)
                if not items_by_category:
                    continue

                section_name = self.SECTION_HEADERS[section_type]
                section_anchor = self._make_anchor_name(product_name, section_name)
                total_section_items = sum(len(items) for items in items_by_category.values())

                # Color breaking changes red
                if section_type == SectionType.BREAKING_CHANGES:
                    link_color = "#BD271E"
                else:
                    link_color = "#1B1B1B"

                elements.append(Paragraph(
                    f'<a href="#{section_anchor}" color="{link_color}">{section_name}</a>'
                    f' <font color="#69707D">({total_section_items} items)</font>',
                    self.styles['TOCSection']
                ))

                # Show all categories for each section
                if len(items_by_category) > 1:
                    # Display categories in rows of up to 4 per line for readability
                    sorted_cats = sorted(items_by_category.keys())
                    row_size = 4
                    for i in range(0, len(sorted_cats), row_size):
                        row_cats = sorted_cats[i:i + row_size]
                        category_parts = []
                        for cat_name in row_cats:
                            cat_count = len(items_by_category[cat_name])
                            cat_anchor = self._make_anchor_name(product_name, section_name, cat_name)
                            category_parts.append(
                                f'<a href="#{cat_anchor}" color="#69707D">{cat_name}</a> ({cat_count})'
                            )
                        elements.append(Paragraph(
                            " · ".join(category_parts),
                            self.styles['TOCCategory']
                        ))

            elements.append(Spacer(1, 0.1 * inch))

        return elements

    def _create_product_section(
        self,
        product_name: str,
        notes: CompiledReleaseNotes
    ) -> List:
        """Create consolidated content section for a product."""
        elements = []
        display_name = PRODUCTS[product_name].display_name
        product_anchor = self._make_anchor_name(product_name)

        # Add anchor for product
        elements.append(AnchorFlowable(product_anchor))

        # Product header
        elements.append(Paragraph(display_name, self.styles['ProductHeader']))

        # Version range info
        elements.append(Paragraph(
            f"<i>Versions {notes.start_version} → {notes.end_version} ({len(notes.releases)} releases)</i>",
            self.styles['Normal']
        ))
        elements.append(Spacer(1, 0.2 * inch))

        # Consolidated sections in order
        for section_type in self.SECTION_ORDER:
            section_elements = self._create_consolidated_section(notes, section_type, product_name)
            if section_elements:
                elements.extend(section_elements)

        elements.append(PageBreak())
        return elements

    def _create_consolidated_section(
        self,
        notes: CompiledReleaseNotes,
        section_type: SectionType,
        product_name: str
    ) -> List:
        """Create a consolidated section (e.g., all bug fixes grouped by category)."""
        items_by_category = self._get_merged_section_items(notes, section_type)

        if not items_by_category:
            return []

        elements = []
        section_name = self.SECTION_HEADERS[section_type]
        section_anchor = self._make_anchor_name(product_name, section_name)

        # Add section anchor
        elements.append(AnchorFlowable(section_anchor))

        # Use warning style for breaking changes
        if section_type == SectionType.BREAKING_CHANGES:
            elements.append(Paragraph(section_name, self.styles['WarningHeader']))
            elements.append(Paragraph(
                "<b>Important:</b> Review all breaking changes before upgrading.",
                ParagraphStyle(
                    name='WarningBanner',
                    parent=self.styles['Normal'],
                    backColor=WARNING_BG,
                    borderColor=WARNING_RED,
                    borderWidth=1,
                    borderPadding=8,
                    fontSize=10,
                )
            ))
            elements.append(Spacer(1, 0.1 * inch))
        else:
            elements.append(Paragraph(section_name, self.styles['SectionHeader']))

        # Items grouped by category
        for category in sorted(items_by_category.keys()):
            items = items_by_category[category]
            category_anchor = self._make_anchor_name(product_name, section_name, category)

            # Add category anchor
            elements.append(AnchorFlowable(category_anchor))
            elements.append(Paragraph(category, self.styles['CategoryHeader']))

            for item in items:
                elements.extend(self._create_consolidated_item(item, product_name, section_type))

        elements.append(Spacer(1, 0.2 * inch))
        return elements

    def _get_version_url(self, version: Version, product_name: str, section_type: SectionType) -> str:
        """Build URL to the specific section on the Elastic docs site for a version."""
        product_config = PRODUCTS[product_name]

        # Map section types to URL anchor fragments for 8.x legacy docs
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

        # Map section types to URL anchor fragments for 9.x modern docs
        # Example: #elasticsearch-9.2.0-fixes, #elasticsearch-9.2.0-features-enhancements
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
            # 9.x uses modern docs site
            # Example: https://www.elastic.co/docs/release-notes/elasticsearch#elasticsearch-9.2.0-fixes
            base_url = product_config.modern_base_url
            section_anchor = modern_section_anchors.get(section_type, "")
            if section_anchor:
                return f"{base_url}#{product_name}-{version}-{section_anchor}"
            else:
                return f"{base_url}#{product_name}-{version}-release-notes"
        else:
            # 8.x uses legacy docs site
            # Example: https://www.elastic.co/guide/en/elasticsearch/reference/8.19/release-notes-8.19.8.html#bug-8.19.8
            base_url = product_config.legacy_base_url
            anchor = legacy_section_anchors.get(section_type, "")
            if anchor:
                return f"{base_url}/{LATEST_8X_MINOR}/release-notes-{version}.html#{anchor}-{version}"
            else:
                return f"{base_url}/{LATEST_8X_MINOR}/release-notes-{version}.html"

    def _create_consolidated_item(
        self, item: ConsolidatedItem, product_name: str, section_type: SectionType
    ) -> List:
        """Create elements for a consolidated item with version tags."""
        elements = []

        # Build version tag with hyperlinks to docs
        version_links = []
        for v in item.versions:
            url = self._get_version_url(v, product_name, section_type)
            version_links.append(f'<a href="{url}" color="#0077CC">{v}</a>')

        if len(version_links) == 1:
            version_tag = f"[{version_links[0]}]"
        else:
            version_tag = f"[{', '.join(version_links)}]"

        text = f"• <b>{version_tag}</b> {self._escape_html(item.description)}"

        if item.pr_number and self.include_pr_links:
            if item.pr_url:
                text += f' <a href="{item.pr_url}" color="blue">[#{item.pr_number}]</a>'
            else:
                text += f" [#{item.pr_number}]"

        elements.append(Paragraph(text, self.styles['Item']))

        # Impact/Action for breaking changes
        if item.impact:
            elements.append(Paragraph(
                f"<b>Impact:</b> {self._escape_html(item.impact)}",
                self.styles['ImpactAction']
            ))
        if item.action:
            elements.append(Paragraph(
                f"<b>Action:</b> {self._escape_html(item.action)}",
                self.styles['ImpactAction']
            ))

        return elements

    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters."""
        if not text:
            return ""
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )

    def _add_footer(self, canvas, doc):
        """Add footer with page number."""
        canvas.saveState()
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(ELASTIC_GRAY)

        # Page number
        page_num = canvas.getPageNumber()
        text = f"Page {page_num}"
        canvas.drawRightString(
            doc.pagesize[0] - 0.75 * inch,
            0.5 * inch,
            text
        )

        # Generated by
        canvas.drawString(
            0.75 * inch,
            0.5 * inch,
            "Generated by ES Release Compiler"
        )

        canvas.restoreState()
