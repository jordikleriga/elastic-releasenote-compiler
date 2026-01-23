# ES Release Notes Compiler

A CLI tool that compiles Elastic Stack release notes across multiple versions into a professional PDF or HTML document for upgrade planning.

## Features

- **Multi-version compilation**: Compile release notes from any version range (e.g., 8.10.0 to 9.2.0)
- **Cross-major-version support**: Handles both 8.x (legacy docs) and 9.x (modern docs) seamlessly
- **39 supported products**: Elasticsearch, Kibana, APM agents, EDOT SDKs, cloud products, and more
- **Multiple output formats**: PDF (default) or HTML
- **Professional output**: Cover page, clickable TOC, consolidated breaking changes, hyperlinks to docs/PRs
- **Category filtering**: Filter output to specific categories (e.g., ES|QL, Machine Learning)
- **Async mode**: Optional async HTTP fetching for better performance
- **Progress bar**: Visual progress indicator during compilation

## Installation

Requires Python 3.9+

```bash
git clone https://github.com/jordikleriga/elastic-releasenote-compiler.git
cd elastic-releasenote-compiler
pip3 install .
```

This installs the `es-release-compiler` command globally. Alternatively, run without installing:

```bash
pip3 install -r es_release_compiler/requirements.txt
python3 -m es_release_compiler --help
```

## Quick Start

```bash
# Compile Elasticsearch notes from 8.10.0 to latest
es-release-compiler --from 8.10.0

# Specific version range
es-release-compiler --from 8.10.0 --to 9.0.0

# Multiple products
es-release-compiler --from 8.10.0 --products elasticsearch,kibana

# HTML output
es-release-compiler --from 8.10.0 --format html

# List available products
es-release-compiler --list-products

# List versions for a product
es-release-compiler --list-versions --products elasticsearch
```

## CLI Reference

Run `es-release-compiler --help` for full options:

```
usage: es-release-compiler [-h] [--version] [--from VERSION] [--to VERSION]
                           [--products LIST] [--list-products] [--output FILE]
                           [--no-pr-links] [--include-prereleases]
                           [--list-versions] [--verbose] [--quiet] [--no-color]
                           [--no-progress] [--format {pdf,html}]
                           [--category CATEGORY] [--async]

Version Selection:
  --from, -f VERSION     Starting version (exclusive - your current version)
  --to, -t VERSION       Target version (inclusive). Defaults to latest.

Product Selection:
  --products, -p LIST    Comma-separated list of products. Default: elasticsearch
  --list-products        List all available products and exit

Output Options:
  --output, -o FILE      Output file path. Auto-generated if not specified.
  --no-pr-links          Exclude GitHub PR/issue links from output

Format Options:
  --format {pdf,html}    Output format (default: pdf)
  --category CATEGORY    Filter to specific category (e.g., 'ES|QL', 'Machine Learning')

Filtering:
  --include-prereleases  Include alpha, beta, and RC versions

Performance:
  --async                Use async HTTP fetching for better performance

Other Options:
  --list-versions        List available versions for specified products
  --verbose, -v          Enable verbose logging
  --quiet, -q            Suppress non-essential output
  --no-color             Disable colored output
  --no-progress          Disable progress bar
  --version, -V          Show version and exit
```

### Version Semantics

- `--from`: Your current installed version (**excluded** from output)
- `--to`: Your target version (**included** in output)

Example: `--from 8.10.0 --to 8.15.0` compiles notes for 8.10.1 through 8.15.0.

## Supported Products

Run `es-release-compiler --list-products` to see all 39 products organized by category:

| Category | Products |
|----------|----------|
| **Elasticsearch** | `elasticsearch`, `es-client-java`, `es-client-javascript`, `es-client-dotnet`, `es-client-php`, `es-client-python`, `es-client-ruby`, `elasticsearch-hadoop` |
| **Kibana** | `kibana` |
| **Ingestion** | `elastic-agent`, `fleet-server`, `logstash`, `beats` |
| **Cloud** | `cloud-serverless`, `cloud-hosted`, `cloud-enterprise`, `cloud-on-k8s` |
| **Observability** | `observability` |
| **EDOT SDKs** | `edot-android`, `edot-ios`, `edot-java`, `edot-dotnet`, `edot-node`, `edot-python`, `edot-php`, `edot-cloud-forwarder-aws` |
| **APM Agents** | `apm`, `apm-agent-java`, `apm-agent-dotnet`, `apm-agent-go`, `apm-agent-nodejs`, `apm-agent-php`, `apm-agent-python`, `apm-agent-ruby`, `apm-agent-rum-js`, `apm-aws-lambda` |
| **Security** | `security` |
| **Other** | `ecs`, `ecctl` |

## Example Output

```
╔═══════════════════════════════════════════════════════════╗
║           ES Release Notes Compiler v1.0.0               ║
║     Compile Elastic Stack release notes for upgrades      ║
╚═══════════════════════════════════════════════════════════╝

ℹ Compiling release notes...
  Products: Elasticsearch
  From:     8.17.0 (exclusive)
  To:       latest (inclusive)

ℹ Generating PDF: elasticsearch_release_notes_8.17.0_to_9.2.0.pdf

═══════════════════════════════════════════════════════════
  Summary
═══════════════════════════════════════════════════════════
  Versions compiled:  25
  Breaking changes:   50
  Deprecations:       3
  Features/Enhance:   150
  Bug fixes:          200
───────────────────────────────────────────────────────────
✓ Output: elasticsearch_release_notes_8.17.0_to_9.2.0.pdf
═══════════════════════════════════════════════════════════

⚠ 50 breaking changes found - review carefully!
```

## Dependencies

- **httpx** - HTTP client with async support
- **beautifulsoup4** + **lxml** - HTML parsing
- **tenacity** - Retry logic for network requests
- **reportlab** - PDF generation
- **rich** - Progress bars and styled output

## License

MIT License - see LICENSE file for details.
