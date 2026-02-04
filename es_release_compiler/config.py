"""Configuration for URL patterns and product settings."""

from dataclasses import dataclass, field
from typing import Dict, Optional, List, Any

from .version import Version


@dataclass
class ProductConfig:
    """Configuration for a specific Elastic product."""

    name: str
    display_name: str
    modern_base_url: str
    github_repo: str
    # Legacy docs URL (8.x and earlier) - None for modern-only products
    legacy_base_url: Optional[str] = None
    # URL path segment for legacy docs (e.g., "elasticsearch", "kibana")
    legacy_path: Optional[str] = None
    # Whether this product has legacy (8.x) docs
    has_legacy_docs: bool = True


# Navigation tree structure matching the Elastic docs site exactly
# Each node can have: "product" (leaf node) or "children" (branch node)
# The structure is: { "label": { "product": "key" } } for leaves
# or { "label": { "children": { ... } } } for branches
NAVIGATION_TREE: Dict[str, Any] = {
    # Elasticsearch and its clients
    "Elasticsearch": {
        "product": "elasticsearch",
        "children": {
            "Java Client": {"product": "es-client-java"},
            "JavaScript Client": {"product": "es-client-javascript"},
            ".NET Client": {"product": "es-client-dotnet"},
            "PHP Client": {"product": "es-client-php"},
            "Python Client": {"product": "es-client-python"},
            "Ruby Client": {"product": "es-client-ruby"},
            "Hadoop": {"product": "elasticsearch-hadoop"},
        }
    },
    "Kibana": {
        "product": "kibana",
    },
    "Elastic Agent": {
        "product": "elastic-agent",
    },
    "Fleet Server": {
        "product": "fleet-server",
    },
    "Logstash": {
        "product": "logstash",
    },
    "Beats": {
        "product": "beats",
    },
    # Each cloud product is a separate top-level item
    "Elastic Cloud Serverless": {
        "product": "cloud-serverless",
    },
    "Elastic Cloud Hosted": {
        "product": "cloud-hosted",
    },
    "Elastic Cloud Enterprise": {
        "product": "cloud-enterprise",
    },
    "Elastic Cloud on Kubernetes": {
        "product": "cloud-on-k8s",
    },
    # Observability with EDOT and APM nested
    "Elastic Observability": {
        "product": "observability",
        "children": {
            "EDOT Android": {"product": "edot-android"},
            "EDOT Cloud Forwarder for AWS": {"product": "edot-cloud-forwarder-aws"},
            "EDOT iOS": {"product": "edot-ios"},
            "EDOT Java": {"product": "edot-java"},
            "EDOT .NET": {"product": "edot-dotnet"},
            "EDOT Node.js": {"product": "edot-node"},
            "EDOT Python": {"product": "edot-python"},
            "EDOT PHP": {"product": "edot-php"},
            "Elastic APM": {
                "product": "apm",
                "children": {
                    ".NET Agent": {"product": "apm-agent-dotnet"},
                    "Go Agent": {"product": "apm-agent-go"},
                    "Java Agent": {"product": "apm-agent-java"},
                    "Node.js Agent": {"product": "apm-agent-nodejs"},
                    "PHP Agent": {"product": "apm-agent-php"},
                    "Python Agent": {"product": "apm-agent-python"},
                    "Ruby Agent": {"product": "apm-agent-ruby"},
                    "RUM JavaScript Agent": {"product": "apm-agent-rum-js"},
                }
            },
            "APM AWS Lambda Extension": {"product": "apm-aws-lambda"},
        }
    },
    "Elastic Security": {
        "product": "security",
    },
    "Elastic Common Schema (ECS)": {
        "product": "ecs",
    },
    "Elastic Cloud Control (ecctl)": {
        "product": "ecctl",
    },
}


PRODUCTS: Dict[str, ProductConfig] = {
    # ============================================
    # Elasticsearch and Clients
    # ============================================
    "elasticsearch": ProductConfig(
        name="elasticsearch",
        display_name="Elasticsearch",
        legacy_base_url="https://www.elastic.co/guide/en/elasticsearch/reference",
        modern_base_url="https://www.elastic.co/docs/release-notes/elasticsearch",
        github_repo="elastic/elasticsearch",
        legacy_path="elasticsearch/reference",
    ),
    "es-client-java": ProductConfig(
        name="es-client-java",
        display_name="Elasticsearch Java Client",
        modern_base_url="https://www.elastic.co/docs/release-notes/elasticsearch/clients/java",
        github_repo="elastic/elasticsearch-java",
        has_legacy_docs=False,
    ),
    "es-client-javascript": ProductConfig(
        name="es-client-javascript",
        display_name="Elasticsearch JavaScript Client",
        modern_base_url="https://www.elastic.co/docs/release-notes/elasticsearch/clients/javascript",
        github_repo="elastic/elasticsearch-js",
        has_legacy_docs=False,
    ),
    "es-client-dotnet": ProductConfig(
        name="es-client-dotnet",
        display_name="Elasticsearch .NET Client",
        modern_base_url="https://www.elastic.co/docs/release-notes/elasticsearch/clients/dotnet",
        github_repo="elastic/elasticsearch-net",
        has_legacy_docs=False,
    ),
    "es-client-php": ProductConfig(
        name="es-client-php",
        display_name="Elasticsearch PHP Client",
        modern_base_url="https://www.elastic.co/docs/release-notes/elasticsearch/clients/php",
        github_repo="elastic/elasticsearch-php",
        has_legacy_docs=False,
    ),
    "es-client-python": ProductConfig(
        name="es-client-python",
        display_name="Elasticsearch Python Client",
        modern_base_url="https://www.elastic.co/docs/release-notes/elasticsearch/clients/python",
        github_repo="elastic/elasticsearch-py",
        has_legacy_docs=False,
    ),
    "es-client-ruby": ProductConfig(
        name="es-client-ruby",
        display_name="Elasticsearch Ruby Client",
        modern_base_url="https://www.elastic.co/docs/release-notes/elasticsearch/clients/ruby",
        github_repo="elastic/elasticsearch-ruby",
        has_legacy_docs=False,
    ),
    "elasticsearch-hadoop": ProductConfig(
        name="elasticsearch-hadoop",
        display_name="Elasticsearch for Apache Hadoop",
        modern_base_url="https://www.elastic.co/docs/release-notes/elasticsearch-hadoop",
        github_repo="elastic/elasticsearch-hadoop",
        has_legacy_docs=False,
    ),

    # ============================================
    # Kibana
    # ============================================
    "kibana": ProductConfig(
        name="kibana",
        display_name="Kibana",
        legacy_base_url="https://www.elastic.co/guide/en/kibana",
        modern_base_url="https://www.elastic.co/docs/release-notes/kibana",
        github_repo="elastic/kibana",
        legacy_path="kibana",
    ),

    # ============================================
    # Elastic Agent & Fleet
    # ============================================
    "elastic-agent": ProductConfig(
        name="elastic-agent",
        display_name="Elastic Agent",
        modern_base_url="https://www.elastic.co/docs/release-notes/elastic-agent",
        github_repo="elastic/elastic-agent",
        has_legacy_docs=False,
    ),
    "fleet-server": ProductConfig(
        name="fleet-server",
        display_name="Fleet Server",
        modern_base_url="https://www.elastic.co/docs/release-notes/fleet-server",
        github_repo="elastic/fleet-server",
        has_legacy_docs=False,
    ),

    # ============================================
    # Logstash
    # ============================================
    "logstash": ProductConfig(
        name="logstash",
        display_name="Logstash",
        legacy_base_url="https://www.elastic.co/guide/en/logstash",
        modern_base_url="https://www.elastic.co/docs/release-notes/logstash",
        github_repo="elastic/logstash",
        legacy_path="logstash",
    ),

    # ============================================
    # Beats
    # ============================================
    "beats": ProductConfig(
        name="beats",
        display_name="Beats",
        legacy_base_url="https://www.elastic.co/guide/en/beats/libbeat",
        modern_base_url="https://www.elastic.co/docs/release-notes/beats",
        github_repo="elastic/beats",
        legacy_path="beats/libbeat",
    ),

    # ============================================
    # Elastic Cloud
    # ============================================
    "cloud-serverless": ProductConfig(
        name="cloud-serverless",
        display_name="Elastic Cloud Serverless",
        modern_base_url="https://www.elastic.co/docs/release-notes/cloud-serverless",
        github_repo="elastic/cloud",
        has_legacy_docs=False,
    ),
    "cloud-hosted": ProductConfig(
        name="cloud-hosted",
        display_name="Elastic Cloud Hosted",
        modern_base_url="https://www.elastic.co/docs/release-notes/cloud-hosted",
        github_repo="elastic/cloud",
        has_legacy_docs=False,
    ),
    "cloud-enterprise": ProductConfig(
        name="cloud-enterprise",
        display_name="Elastic Cloud Enterprise",
        modern_base_url="https://www.elastic.co/docs/release-notes/cloud-enterprise",
        github_repo="elastic/cloud-enterprise",
        has_legacy_docs=False,
    ),
    "cloud-on-k8s": ProductConfig(
        name="cloud-on-k8s",
        display_name="Elastic Cloud on Kubernetes",
        modern_base_url="https://www.elastic.co/docs/release-notes/cloud-on-k8s",
        github_repo="elastic/cloud-on-k8s",
        has_legacy_docs=False,
    ),
    "ecctl": ProductConfig(
        name="ecctl",
        display_name="Elastic Cloud Control (ecctl)",
        modern_base_url="https://www.elastic.co/docs/release-notes/ecctl",
        github_repo="elastic/ecctl",
        has_legacy_docs=False,
    ),

    # ============================================
    # Elastic Observability
    # ============================================
    "observability": ProductConfig(
        name="observability",
        display_name="Elastic Observability",
        modern_base_url="https://www.elastic.co/docs/release-notes/observability",
        github_repo="elastic/observability-docs",
        has_legacy_docs=False,
    ),

    # ============================================
    # EDOT SDKs (under Observability)
    # ============================================
    "edot-android": ProductConfig(
        name="edot-android",
        display_name="EDOT Android",
        modern_base_url="https://www.elastic.co/docs/release-notes/edot/sdks/android",
        github_repo="elastic/elastic-otel-android",
        has_legacy_docs=False,
    ),
    "edot-ios": ProductConfig(
        name="edot-ios",
        display_name="EDOT iOS",
        modern_base_url="https://www.elastic.co/docs/release-notes/edot/sdks/ios",
        github_repo="elastic/elastic-otel-ios",
        has_legacy_docs=False,
    ),
    "edot-java": ProductConfig(
        name="edot-java",
        display_name="EDOT Java",
        modern_base_url="https://www.elastic.co/docs/release-notes/edot/sdks/java",
        github_repo="elastic/elastic-otel-java",
        has_legacy_docs=False,
    ),
    "edot-dotnet": ProductConfig(
        name="edot-dotnet",
        display_name="EDOT .NET",
        modern_base_url="https://www.elastic.co/docs/release-notes/edot/sdks/dotnet",
        github_repo="elastic/elastic-otel-dotnet",
        has_legacy_docs=False,
    ),
    "edot-node": ProductConfig(
        name="edot-node",
        display_name="EDOT Node.js",
        modern_base_url="https://www.elastic.co/docs/release-notes/edot/sdks/node",
        github_repo="elastic/elastic-otel-node",
        has_legacy_docs=False,
    ),
    "edot-python": ProductConfig(
        name="edot-python",
        display_name="EDOT Python",
        modern_base_url="https://www.elastic.co/docs/release-notes/edot/sdks/python",
        github_repo="elastic/elastic-otel-python",
        has_legacy_docs=False,
    ),
    "edot-php": ProductConfig(
        name="edot-php",
        display_name="EDOT PHP",
        modern_base_url="https://www.elastic.co/docs/release-notes/edot/sdks/php",
        github_repo="elastic/elastic-otel-php",
        has_legacy_docs=False,
    ),
    "edot-cloud-forwarder-aws": ProductConfig(
        name="edot-cloud-forwarder-aws",
        display_name="EDOT Cloud Forwarder for AWS",
        modern_base_url="https://www.elastic.co/docs/release-notes/edot/cloud-forwarder/aws",
        github_repo="elastic/elastic-otel-collector",
        has_legacy_docs=False,
    ),

    # ============================================
    # APM (under Observability)
    # ============================================
    "apm": ProductConfig(
        name="apm",
        display_name="Elastic APM",
        modern_base_url="https://www.elastic.co/docs/release-notes/apm",
        github_repo="elastic/apm-server",
        has_legacy_docs=False,
    ),
    "apm-agent-dotnet": ProductConfig(
        name="apm-agent-dotnet",
        display_name="APM .NET Agent",
        modern_base_url="https://www.elastic.co/docs/release-notes/apm/agents/dotnet",
        github_repo="elastic/apm-agent-dotnet",
        has_legacy_docs=False,
    ),
    "apm-agent-go": ProductConfig(
        name="apm-agent-go",
        display_name="APM Go Agent",
        modern_base_url="https://www.elastic.co/docs/release-notes/apm/agents/go",
        github_repo="elastic/apm-agent-go",
        has_legacy_docs=False,
    ),
    "apm-agent-java": ProductConfig(
        name="apm-agent-java",
        display_name="APM Java Agent",
        modern_base_url="https://www.elastic.co/docs/release-notes/apm/agents/java",
        github_repo="elastic/apm-agent-java",
        has_legacy_docs=False,
    ),
    "apm-agent-nodejs": ProductConfig(
        name="apm-agent-nodejs",
        display_name="APM Node.js Agent",
        modern_base_url="https://www.elastic.co/docs/release-notes/apm/agents/nodejs",
        github_repo="elastic/apm-agent-nodejs",
        has_legacy_docs=False,
    ),
    "apm-agent-php": ProductConfig(
        name="apm-agent-php",
        display_name="APM PHP Agent",
        modern_base_url="https://www.elastic.co/docs/release-notes/apm/agents/php",
        github_repo="elastic/apm-agent-php",
        has_legacy_docs=False,
    ),
    "apm-agent-python": ProductConfig(
        name="apm-agent-python",
        display_name="APM Python Agent",
        modern_base_url="https://www.elastic.co/docs/release-notes/apm/agents/python",
        github_repo="elastic/apm-agent-python",
        has_legacy_docs=False,
    ),
    "apm-agent-ruby": ProductConfig(
        name="apm-agent-ruby",
        display_name="APM Ruby Agent",
        modern_base_url="https://www.elastic.co/docs/release-notes/apm/agents/ruby",
        github_repo="elastic/apm-agent-ruby",
        has_legacy_docs=False,
    ),
    "apm-agent-rum-js": ProductConfig(
        name="apm-agent-rum-js",
        display_name="APM RUM JavaScript Agent",
        modern_base_url="https://www.elastic.co/docs/release-notes/apm/agents/rum-js",
        github_repo="elastic/apm-agent-rum-js",
        has_legacy_docs=False,
    ),
    "apm-aws-lambda": ProductConfig(
        name="apm-aws-lambda",
        display_name="APM AWS Lambda Extension",
        modern_base_url="https://www.elastic.co/docs/release-notes/apm/aws-lambda",
        github_repo="elastic/apm-aws-lambda",
        has_legacy_docs=False,
    ),

    # ============================================
    # Elastic Security
    # ============================================
    "security": ProductConfig(
        name="security",
        display_name="Elastic Security",
        modern_base_url="https://www.elastic.co/docs/release-notes/security",
        github_repo="elastic/security-docs",
        has_legacy_docs=False,
    ),

    # ============================================
    # ECS
    # ============================================
    "ecs": ProductConfig(
        name="ecs",
        display_name="Elastic Common Schema (ECS)",
        modern_base_url="https://www.elastic.co/docs/release-notes/ecs",
        github_repo="elastic/ecs",
        has_legacy_docs=False,
    ),
}


def _collect_products_from_tree(node: Dict[str, Any], products: List[str]) -> None:
    """Recursively collect product keys from navigation tree."""
    if "product" in node:
        products.append(node["product"])
    if "children" in node:
        for child in node["children"].values():
            _collect_products_from_tree(child, products)


def get_all_product_keys() -> List[str]:
    """Get all product keys in navigation tree order."""
    products = []
    for node in NAVIGATION_TREE.values():
        _collect_products_from_tree(node, products)
    return products


def print_navigation_tree(colors: Any = None) -> None:
    """Print the navigation tree with proper indentation.

    Args:
        colors: Optional Colors class with color codes. If None, no colors used.
    """
    def _print_node(label: str, node: Dict[str, Any], indent: int = 0) -> None:
        prefix = "  " * indent

        # Determine colors (or empty strings if no colors)
        c_bold = colors.BOLD if colors else ""
        c_green = colors.GREEN if colors else ""
        c_cyan = colors.CYAN if colors else ""
        c_yellow = colors.YELLOW if colors else ""
        c_end = colors.END if colors else ""

        if "product" in node:
            product_key = node["product"]
            config = PRODUCTS.get(product_key)
            legacy_marker = "" if config and config.has_legacy_docs else f" {c_yellow}(9.x+){c_end}"

            if "children" in node:
                # Branch with its own product - show label and product key together
                print(f"{prefix}{c_cyan}{label}:{c_end} {c_green}{product_key}{c_end}{legacy_marker}")
                for child_label, child_node in node["children"].items():
                    _print_node(child_label, child_node, indent + 1)
            else:
                # Leaf node - show product key with label as description
                print(f"{prefix}{c_green}{product_key:30}{c_end} {label}{legacy_marker}")
        elif "children" in node:
            # Branch without its own product
            print(f"{prefix}{c_cyan}{label}:{c_end}")
            for child_label, child_node in node["children"].items():
                _print_node(child_label, child_node, indent + 1)

    print()
    for label, node in NAVIGATION_TREE.items():
        _print_node(label, node, 0)
        print()


# Version threshold for doc site transition (9.x uses modern site)
MODERN_DOCS_MIN_VERSION = Version(9, 0, 0)

# Known 8.x minor versions for doc site URL access
# The legacy fetcher will also auto-discover newer minors beyond these
KNOWN_8X_MINORS = ["8.17", "8.18", "8.19"]
LATEST_8X_MINOR = KNOWN_8X_MINORS[-1]

# URL patterns for legacy (8.x) docs
LEGACY_PATTERNS = {
    "release_notes": "{base}/{minor}/release-notes-{version}.html",
    "release_notes_index": "{base}/{minor}/es-release-notes.html",
    "breaking_changes": "{base}/{minor}/migrating-{target_minor}.html",
    "breaking_changes_index": "{base}/{minor}/breaking-changes.html",
}

# URL patterns for modern (9.x) docs
MODERN_PATTERNS = {
    "release_notes": "{base}",
    "breaking_changes": "{base}/breaking-changes",
    "deprecations": "{base}/deprecations",
    "known_issues": "{base}/known-issues",
}
