#!/usr/bin/env python3
"""CLI entry point for ES Release Compiler."""

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional, List

from . import __version__
from .compiler import ReleaseCompiler
from .pdf_generator import PDFGenerator
from .html_generator import HTMLGenerator
from .config import PRODUCTS, print_navigation_tree
from .models import SectionType


# ANSI color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

    @classmethod
    def disable(cls):
        """Disable colors (for non-TTY output)."""
        cls.HEADER = ''
        cls.BLUE = ''
        cls.CYAN = ''
        cls.GREEN = ''
        cls.YELLOW = ''
        cls.RED = ''
        cls.BOLD = ''
        cls.UNDERLINE = ''
        cls.END = ''


def supports_color() -> bool:
    """Check if the terminal supports color output."""
    if not hasattr(sys.stdout, 'isatty'):
        return False
    if not sys.stdout.isatty():
        return False
    return True


def print_banner():
    """Print a styled banner."""
    c = Colors
    print(f"""
{c.CYAN}{c.BOLD}╔═══════════════════════════════════════════════════════════╗
║           ES Release Notes Compiler v{__version__:<19}║
║     Compile Elastic Stack release notes for upgrades      ║
╚═══════════════════════════════════════════════════════════╝{c.END}
""")


def print_success(message: str):
    """Print a success message."""
    print(f"{Colors.GREEN}✓ {message}{Colors.END}")


def print_warning(message: str):
    """Print a warning message."""
    print(f"{Colors.YELLOW}⚠ {message}{Colors.END}")


def print_error(message: str):
    """Print an error message."""
    print(f"{Colors.RED}✗ {message}{Colors.END}")


def print_info(message: str):
    """Print an info message."""
    print(f"{Colors.CYAN}ℹ {message}{Colors.END}")


def print_products_list():
    """Print all available products in navigation tree structure."""
    print(f"\n{Colors.BOLD}Available Products ({len(PRODUCTS)} total):{Colors.END}")
    print_navigation_tree(Colors)


class ColoredHelpFormatter(argparse.RawDescriptionHelpFormatter):
    """Custom formatter that adds color to help output."""

    def __init__(self, prog, indent_increment=2, max_help_position=30, width=None):
        super().__init__(prog, indent_increment, max_help_position, width)

    def _format_action_invocation(self, action):
        if not action.option_strings:
            default = self._get_default_metavar_for_positional(action)
            metavar, = self._metavar_formatter(action, default)(1)
            return metavar
        else:
            parts = []
            if action.option_strings:
                parts.append(f"{Colors.GREEN}{', '.join(action.option_strings)}{Colors.END}")
            return ' '.join(parts)

    def _format_usage(self, usage, actions, groups, prefix):
        if prefix is None:
            prefix = f'{Colors.BOLD}Usage: {Colors.END}'
        return super()._format_usage(usage, actions, groups, prefix)


def create_parser() -> argparse.ArgumentParser:
    formatter_class = ColoredHelpFormatter if supports_color() else argparse.RawDescriptionHelpFormatter

    parser = argparse.ArgumentParser(
        prog="es-release-compiler",
        description=f"{Colors.BOLD}Compile Elastic Stack release notes across versions into a PDF{Colors.END}" if supports_color() else "Compile Elastic Stack release notes across versions into a PDF",
        formatter_class=formatter_class,
        epilog=f"""
{Colors.BOLD}Examples:{Colors.END}

  {Colors.CYAN}# Compile Elasticsearch notes from 8.10.0 to latest{Colors.END}
  %(prog)s --from 8.10.0

  {Colors.CYAN}# Compile notes for a specific version range{Colors.END}
  %(prog)s --from 8.10.0 --to 9.0.0

  {Colors.CYAN}# Cross major version upgrade (8.x to 9.x){Colors.END}
  %(prog)s --from 8.17.0 --to 9.2.0

  {Colors.CYAN}# Include multiple products in one PDF{Colors.END}
  %(prog)s --from 8.10.0 --products elasticsearch,kibana

  {Colors.CYAN}# Compile APM Java Agent notes{Colors.END}
  %(prog)s --from 1.40.0 --products apm-agent-java

  {Colors.CYAN}# Compile Elastic Security notes{Colors.END}
  %(prog)s --from 8.10.0 --products security

  {Colors.CYAN}# List all available products{Colors.END}
  %(prog)s --list-products

  {Colors.CYAN}# List available versions for a product{Colors.END}
  %(prog)s --list-versions --products elasticsearch

{Colors.BOLD}Product Categories:{Colors.END}
  Use --list-products to see all {len(PRODUCTS)} available products including:
  - Core: elasticsearch, kibana, logstash, beats
  - Clients: es-client-java, es-client-python, etc.
  - Cloud: cloud-hosted, cloud-enterprise, cloud-on-k8s
  - APM Agents: apm-agent-java, apm-agent-python, etc.
  - EDOT: edot-java, edot-python, edot-node, etc.
  - And more...

{Colors.BOLD}Version Semantics:{Colors.END}
  --from: Your current version (exclusive - not included in output)
  --to:   Your target version (inclusive - included in output)
""" if supports_color() else """
Examples:

  # Compile Elasticsearch notes from 8.10.0 to latest
  %(prog)s --from 8.10.0

  # Compile notes for a specific version range
  %(prog)s --from 8.10.0 --to 9.0.0

  # Cross major version upgrade (8.x to 9.x)
  %(prog)s --from 8.17.0 --to 9.2.0

  # Include multiple products in one PDF
  %(prog)s --from 8.10.0 --products elasticsearch,kibana

  # Compile APM Java Agent notes
  %(prog)s --from 1.40.0 --products apm-agent-java

  # Compile Elastic Security notes
  %(prog)s --from 8.10.0 --products security

  # List all available products
  %(prog)s --list-products

  # List available versions for a product
  %(prog)s --list-versions --products elasticsearch

Product Categories:
  Use --list-products to see all available products including:
  - Core: elasticsearch, kibana, logstash, beats
  - Clients: es-client-java, es-client-python, etc.
  - Cloud: cloud-hosted, cloud-enterprise, cloud-on-k8s
  - APM Agents: apm-agent-java, apm-agent-python, etc.
  - EDOT: edot-java, edot-python, edot-node, etc.
  - And more...

Version Semantics:
  --from: Your current version (exclusive - not included in output)
  --to:   Your target version (inclusive - included in output)
""",
    )

    # Version flag
    parser.add_argument(
        "--version", "-V",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    # Main arguments group
    version_group = parser.add_argument_group(f'{Colors.BOLD}Version Selection{Colors.END}' if supports_color() else 'Version Selection')
    version_group.add_argument(
        "--from", "-f",
        dest="from_version",
        metavar="VERSION",
        help="Starting version (your current version, exclusive)",
    )
    version_group.add_argument(
        "--to", "-t",
        dest="to_version",
        metavar="VERSION",
        default=None,
        help="Target version (inclusive). Defaults to latest available.",
    )

    # Product selection
    product_group = parser.add_argument_group(f'{Colors.BOLD}Product Selection{Colors.END}' if supports_color() else 'Product Selection')
    product_group.add_argument(
        "--products", "-p",
        metavar="LIST",
        default="elasticsearch",
        help="Comma-separated list of products. Default: elasticsearch",
    )
    product_group.add_argument(
        "--list-products",
        action="store_true",
        help="List all available products and exit",
    )

    # Output options
    output_group = parser.add_argument_group(f'{Colors.BOLD}Output Options{Colors.END}' if supports_color() else 'Output Options')
    output_group.add_argument(
        "--output", "-o",
        type=Path,
        metavar="FILE",
        default=None,
        help="Output PDF file path. Auto-generated if not specified.",
    )
    output_group.add_argument(
        "--no-pr-links",
        action="store_true",
        help="Exclude GitHub PR/issue links from output",
    )

    # Filtering options
    filter_group = parser.add_argument_group(f'{Colors.BOLD}Filtering{Colors.END}' if supports_color() else 'Filtering')
    filter_group.add_argument(
        "--include-prereleases",
        action="store_true",
        help="Include alpha, beta, and RC versions",
    )

    # Other options
    other_group = parser.add_argument_group(f'{Colors.BOLD}Other Options{Colors.END}' if supports_color() else 'Other Options')
    other_group.add_argument(
        "--list-versions",
        action="store_true",
        help="List all available versions for specified products and exit",
    )
    other_group.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging",
    )
    other_group.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress non-essential output",
    )
    other_group.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output",
    )
    other_group.add_argument(
        "--no-progress",
        action="store_true",
        help="Disable progress bar",
    )

    # Format options
    format_group = parser.add_argument_group(f'{Colors.BOLD}Format Options{Colors.END}' if supports_color() else 'Format Options')
    format_group.add_argument(
        "--format",
        choices=["pdf", "html"],
        default="pdf",
        help="Output format (default: pdf)",
    )
    format_group.add_argument(
        "--category",
        metavar="CATEGORY",
        help="Filter output to specific category (e.g., 'ES|QL', 'Machine Learning')",
    )

    # Performance options
    perf_group = parser.add_argument_group(f'{Colors.BOLD}Performance{Colors.END}' if supports_color() else 'Performance')
    perf_group.add_argument(
        "--async",
        dest="use_async",
        action="store_true",
        help="Use async HTTP fetching for better performance",
    )

    return parser


def filter_by_category(compiled, category_filter: str):
    """Filter compiled notes to only include items from a specific category."""
    from .models import CompiledReleaseNotes, ReleaseNote, ReleaseSection

    filtered = {}
    for product_name, notes in compiled.items():
        filtered_releases = []
        for release in notes.releases:
            filtered_sections = {}
            for section_type, section in release.sections.items():
                filtered_items = [
                    item for item in section.items
                    if item.category and category_filter.lower() in item.category.lower()
                ]
                if filtered_items:
                    filtered_sections[section_type] = ReleaseSection(
                        section_type=section_type,
                        items=filtered_items
                    )
            if filtered_sections:
                filtered_release = ReleaseNote(
                    version=release.version,
                    product=release.product,
                    sections=filtered_sections,
                    release_date=release.release_date,
                    source_url=release.source_url,
                )
                filtered_releases.append(filtered_release)

        filtered[product_name] = CompiledReleaseNotes(
            product=product_name,
            start_version=notes.start_version,
            end_version=notes.end_version,
            releases=filtered_releases,
        )
    return filtered


def main():
    # Pre-parse to check for --no-color before creating parser
    if '--no-color' in sys.argv or not supports_color():
        Colors.disable()

    parser = create_parser()
    args = parser.parse_args()

    # Apply --no-color if specified
    if args.no_color:
        Colors.disable()

    # Handle --list-products early (doesn't need compiler)
    if args.list_products:
        print_products_list()
        return

    # Configure logging
    if args.quiet:
        log_level = logging.WARNING
    elif args.verbose:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger(__name__)

    # Show banner unless quiet mode
    if not args.quiet and not args.list_versions:
        print_banner()

    # Parse products
    products = [p.strip().lower() for p in args.products.split(",")]
    for product in products:
        if product not in PRODUCTS:
            print_error(f"Unknown product: {product}")
            print_info("Use --list-products to see all available products")
            sys.exit(1)

    # Determine if we should use progress bar
    use_progress = (
        not args.quiet
        and not args.no_progress
        and not args.list_versions
        and supports_color()
    )

    # Determine if we should use async mode
    use_async = args.use_async

    # Initialize compiler with progress callback if enabled
    try:
        if use_async:
            if use_progress:
                from .async_compiler import AsyncReleaseCompilerWithProgress
                compiler = AsyncReleaseCompilerWithProgress(products=products)
            else:
                from .async_compiler import AsyncReleaseCompiler
                compiler = AsyncReleaseCompiler(products=products)
        elif use_progress:
            from .compiler import ReleaseCompilerWithProgress
            compiler = ReleaseCompilerWithProgress(products=products)
        else:
            compiler = ReleaseCompiler(products=products)
    except ValueError as e:
        print_error(str(e))
        sys.exit(1)

    try:
        # List versions mode
        if args.list_versions:
            for product in products:
                versions = compiler.discover_versions(product)
                display_name = PRODUCTS[product].display_name
                print(f"\n{Colors.BOLD}{display_name} versions ({len(versions)} total):{Colors.END}\n")

                if not versions:
                    print(f"  {Colors.YELLOW}No versions found{Colors.END}")
                    continue

                # Group by major version
                major_groups = {}
                for v in versions:
                    major = v.major
                    if major not in major_groups:
                        major_groups[major] = []
                    major_groups[major].append(v)

                for major in sorted(major_groups.keys(), reverse=True):
                    print(f"  {Colors.CYAN}{major}.x:{Colors.END}")
                    for v in major_groups[major]:
                        marker = f" {Colors.YELLOW}(pre-release){Colors.END}" if v.is_prerelease else ""
                        print(f"    {v}{marker}")
                    print()
            return

        # Require --from for compilation
        if not args.from_version:
            print_error("--from is required for compiling release notes")
            print_info("Use --help for usage examples")
            sys.exit(1)

        # Compile release notes
        if not args.quiet and not use_progress:
            print_info(f"Compiling release notes...")
            product_names = [PRODUCTS[p].display_name for p in products]
            print(f"  {Colors.BOLD}Products:{Colors.END} {', '.join(product_names)}")
            print(f"  {Colors.BOLD}From:{Colors.END}     {args.from_version} (exclusive)")
            print(f"  {Colors.BOLD}To:{Colors.END}       {args.to_version or 'latest'} (inclusive)")
            print()

        if use_async:
            import asyncio
            compiled = asyncio.run(compiler.compile_all(
                start_version=args.from_version,
                end_version=args.to_version,
                include_prereleases=args.include_prereleases,
            ))
        else:
            compiled = compiler.compile_all(
                start_version=args.from_version,
                end_version=args.to_version,
                include_prereleases=args.include_prereleases,
            )

        # Apply category filter if specified
        if args.category:
            compiled = filter_by_category(compiled, args.category)
            if not args.quiet:
                print_info(f"Filtered to category: {args.category}")

        # Check if we got any releases
        total_releases = sum(len(notes.releases) for notes in compiled.values())
        if total_releases == 0:
            print_warning("No release notes found for the specified version range")
            sys.exit(0)

        # Determine output format and file extension
        output_format = args.format
        extension = ".html" if output_format == "html" else ".pdf"

        # Generate output path
        if args.output:
            output_path = args.output
            # Ensure correct extension
            if not str(output_path).lower().endswith(extension):
                output_path = Path(str(output_path) + extension)
        else:
            # Determine actual end version from compiled notes
            actual_end = args.to_version
            if not actual_end:
                for notes in compiled.values():
                    if notes.releases:
                        actual_end = str(notes.end_version)
                        break
            # Use first product name in filename
            product_prefix = products[0] if len(products) == 1 else "elastic"
            output_path = Path(f"{product_prefix}_release_notes_{args.from_version}_to_{actual_end or 'latest'}{extension}")

        if not args.quiet:
            print_info(f"Generating {output_format.upper()}: {output_path}")

        # Generate output based on format
        if output_format == "html":
            generator = HTMLGenerator(include_pr_links=not args.no_pr_links)
        else:
            generator = PDFGenerator(include_pr_links=not args.no_pr_links)

        generator.generate(
            compiled_notes=compiled,
            output_path=str(output_path),
            start_version=args.from_version,
            end_version=args.to_version,
        )

        # Summary
        total_breaking = sum(len(notes.all_breaking_changes) for notes in compiled.values())
        total_deprecations = sum(len(notes.all_deprecations) for notes in compiled.values())
        total_features = sum(len(notes.all_new_features) + len(notes.all_enhancements) for notes in compiled.values())
        total_bugfixes = sum(len(notes.all_bug_fixes) for notes in compiled.values())

        print()
        print(f"{Colors.BOLD}{'═'*55}{Colors.END}")
        print(f"{Colors.BOLD}  Summary{Colors.END}")
        print(f"{Colors.BOLD}{'═'*55}{Colors.END}")
        print(f"  {Colors.CYAN}Versions compiled:{Colors.END}  {total_releases}")
        print(f"  {Colors.CYAN}Breaking changes:{Colors.END}   {total_breaking}")
        print(f"  {Colors.CYAN}Deprecations:{Colors.END}       {total_deprecations}")
        print(f"  {Colors.CYAN}Features/Enhance:{Colors.END}   {total_features}")
        print(f"  {Colors.CYAN}Bug fixes:{Colors.END}          {total_bugfixes}")
        print(f"{Colors.BOLD}{'─'*55}{Colors.END}")
        print_success(f"Output: {output_path}")
        print(f"{Colors.BOLD}{'═'*55}{Colors.END}")

        if total_breaking > 0:
            print()
            print_warning(f"{total_breaking} breaking changes found - review carefully!")

    except ValueError as e:
        print_error(f"Invalid input: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print()
        print_warning("Interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        print_error(f"Unexpected error: {e}")
        sys.exit(1)
    finally:
        if use_async:
            import asyncio
            asyncio.run(compiler.close())
        else:
            compiler.close()


if __name__ == "__main__":
    main()
