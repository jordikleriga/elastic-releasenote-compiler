#!/usr/bin/env python3
"""Setup script for ES Release Notes Compiler."""

from setuptools import setup, find_packages
from pathlib import Path

# Read version from package
version = {}
with open("es_release_compiler/__init__.py") as f:
    exec(f.read(), version)

# Read long description from README
readme = Path("README.md").read_text(encoding="utf-8")

# Read requirements
requirements = Path("es_release_compiler/requirements.txt").read_text().strip().split("\n")

setup(
    name="es-release-compiler",
    version=version["__version__"],
    description="Compile Elasticsearch release notes across versions into a PDF for upgrade planning",
    long_description=readme,
    long_description_content_type="text/markdown",
    author="Jordi Kleriga",
    author_email="",
    url="https://github.com/jordikleriga/elastic-releasenote-compiler",
    license="MIT",
    packages=find_packages(),
    include_package_data=True,
    python_requires=">=3.9",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "es-release-compiler=es_release_compiler.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Documentation",
        "Topic :: Software Development :: Documentation",
        "Topic :: System :: Systems Administration",
    ],
    keywords="elasticsearch release-notes upgrade pdf documentation elastic",
)
