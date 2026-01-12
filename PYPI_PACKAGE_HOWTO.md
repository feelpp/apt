# Creating the PyPI Package: Step-by-Step Guide

## Overview
This guide walks through creating a PyPI package from the existing `aptly_publish.py` script.

## Step 1: Create New Repository

```bash
# Create new repository on GitHub: feelpp/aptly-publisher
gh repo create feelpp/aptly-publisher --public --description "Tool to publish Debian packages to Feel++ APT repository"

# Clone it
git clone https://github.com/feelpp/aptly-publisher.git
cd aptly-publisher
```

## Step 2: Set Up Project Structure

```bash
# Create directory structure
mkdir -p src/feelpp_aptly_publisher
mkdir -p tests
mkdir -p examples

# Create initial files
touch src/feelpp_aptly_publisher/__init__.py
touch src/feelpp_aptly_publisher/__main__.py
touch src/feelpp_aptly_publisher/publisher.py
touch src/feelpp_aptly_publisher/cli.py
touch tests/__init__.py
touch tests/test_publisher.py
```

## Step 3: Refactor Code

### src/feelpp_aptly_publisher/__init__.py
```python
"""Feel++ Aptly Publisher - Publish Debian packages to APT repository via GitHub Pages."""

__version__ = "1.0.0"

from .publisher import AptlyPublisher

__all__ = ["AptlyPublisher"]
```

### src/feelpp_aptly_publisher/publisher.py
```python
"""Core publishing logic."""

import json
import logging
import os
import re
import shlex
import subprocess
import tempfile
from datetime import datetime, UTC
from glob import glob
from pathlib import Path
from typing import Optional


class AptlyPublisher:
    """Manages APT repository publishing via aptly and GitHub Pages."""
    
    def __init__(
        self,
        component: str,
        distro: str,
        channel: str = "stable",
        pages_repo: str = "https://github.com/feelpp/apt.git",
        branch: str = "gh-pages",
        sign: bool = False,
        keyid: Optional[str] = None,
        passphrase: Optional[str] = None,
        aptly_config: Optional[str] = None,
        aptly_root: Optional[str] = None,
    ):
        """Initialize the publisher."""
        self.component = self._normalize_component(component)
        self.distro = distro
        self.channel = channel
        self.pages_repo = pages_repo
        self.branch = branch
        self.sign = sign
        self.keyid = keyid
        self.passphrase = passphrase
        self.aptly_config = aptly_config
        self.aptly_root = aptly_root
        
    @staticmethod
    def _normalize_component(s: str) -> str:
        """Normalize component name."""
        s = s.lower()
        s = re.sub(r"[^a-z0-9]+", "-", s)
        return s.strip("-")
    
    def publish(self, debs_dir: Optional[str] = None) -> None:
        """Publish packages to APT repository."""
        # Implementation extracted from aptly_publish.py
        # ... (full implementation)
        pass
    
    def bootstrap(self) -> None:
        """Bootstrap an empty component."""
        self.publish(debs_dir=None)
```

### src/feelpp_aptly_publisher/__main__.py
```python
"""CLI entry point."""

from .cli import main

if __name__ == "__main__":
    main()
```

### src/feelpp_aptly_publisher/cli.py
```python
"""Command-line interface."""

import argparse
import logging
import os
import sys

from .publisher import AptlyPublisher


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Bootstrap or update a component in a GitHub Pages APT repo"
    )
    parser.add_argument("--component", required=True, help="project/component name")
    parser.add_argument("--distro", default="noble", help="Ubuntu/Debian distribution")
    parser.add_argument("--channel", default="stable", choices=["stable", "testing", "pr"])
    parser.add_argument("--debs", default=None, help="directory with .deb files")
    parser.add_argument("--pages-repo", default=os.environ.get("PAGES_REPO", "https://github.com/feelpp/apt.git"))
    parser.add_argument("--branch", default=os.environ.get("BRANCH", "gh-pages"))
    parser.add_argument("--sign", action="store_true", help="sign with GPG")
    parser.add_argument("--keyid", default=None, help="GPG key id")
    parser.add_argument("--passphrase", default=None, help="GPG passphrase")
    parser.add_argument("--aptly-config", default=None, help="aptly config file")
    parser.add_argument("--aptly-root", default=None, help="aptly root directory")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    if args.sign and not args.keyid:
        logging.error("--keyid is required with --sign")
        sys.exit(1)

    publisher = AptlyPublisher(
        component=args.component,
        distro=args.distro,
        channel=args.channel,
        pages_repo=args.pages_repo,
        branch=args.branch,
        sign=args.sign,
        keyid=args.keyid,
        passphrase=args.passphrase,
        aptly_config=args.aptly_config,
        aptly_root=args.aptly_root,
    )

    try:
        publisher.publish(debs_dir=args.debs)
    except Exception as exc:
        logging.error("Publication failed: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
```

## Step 4: Copy Configuration Files

```bash
# Copy the pyproject.toml template
cp /nvme0/prudhomm/Devel/feelpp.quickfix/apt/pyproject.toml.example ./pyproject.toml

# Create README
cat > README.md << 'EOF'
# Feel++ Aptly Publisher

Tool to publish Debian packages to Feel++ APT repository via aptly and GitHub Pages.

## Installation

```bash
pip install feelpp-aptly-publisher
```

## Usage

```bash
feelpp-apt-publish \
    --component mmg \
    --channel stable \
    --distro noble \
    --debs ./packages/
```

See [documentation](https://github.com/feelpp/aptly-publisher) for more details.
EOF

# Copy examples
cp /nvme0/prudhomm/Devel/feelpp.quickfix/apt/scripts/aptly.conf examples/
```

## Step 5: Add Tests

```bash
# tests/test_publisher.py
cat > tests/test_publisher.py << 'EOF'
"""Tests for AptlyPublisher."""

import pytest
from feelpp_aptly_publisher import AptlyPublisher


def test_normalize_component():
    """Test component name normalization."""
    pub = AptlyPublisher(component="Test_Component", distro="noble")
    assert pub.component == "test-component"


def test_publisher_init():
    """Test publisher initialization."""
    pub = AptlyPublisher(
        component="mmg",
        distro="noble",
        channel="stable",
    )
    assert pub.component == "mmg"
    assert pub.distro == "noble"
    assert pub.channel == "stable"
EOF
```

## Step 6: Build and Test Locally

```bash
# Install in development mode
pip install -e .

# Run tests
pip install pytest
pytest

# Test CLI
feelpp-apt-publish --help

# Test with actual publishing (if you have access)
feelpp-apt-publish \
    --component test \
    --channel testing \
    --distro noble \
    --verbose
```

## Step 7: Publish to PyPI

```bash
# Install build tools
pip install build twine

# Build the package
python -m build

# Check the distribution
twine check dist/*

# Upload to Test PyPI first
twine upload --repository testpypi dist/*

# Test installation from Test PyPI
pip install --index-url https://test.pypi.org/simple/ feelpp-aptly-publisher

# If all good, upload to production PyPI
twine upload dist/*
```

## Step 8: Set Up CI/CD

Create `.github/workflows/publish.yml`:

```yaml
name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  publish:
    runs-on: ubuntu-latest
    permissions:
      id-token: write  # For trusted publishing
    steps:
      - uses: actions/checkout@v3
      
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install build
      
      - name: Build package
        run: python -m build
      
      - name: Publish to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
```

## Step 9: Update mmg Project

```bash
cd /nvme0/prudhomm/Devel/feelpp.quickfix/third-party/mmg

# Update publish-mmg.sh to use PyPI package
cat > publish-mmg.sh << 'EOF'
#!/bin/bash
set -e

CHANNEL="${1:-stable}"
DISTRO="${2:-noble}"
PACKAGES_DIR="$(dirname "$0")/packages"

# Install publisher if not available
if ! command -v feelpp-apt-publish &> /dev/null; then
    echo "Installing feelpp-aptly-publisher..."
    pip install feelpp-aptly-publisher
fi

# Publish
feelpp-apt-publish \
    --component mmg \
    --channel "$CHANNEL" \
    --distro "$DISTRO" \
    --debs "$PACKAGES_DIR" \
    --verbose
EOF

chmod +x publish-mmg.sh
```

## Benefits Achieved

✅ **Easy installation**: `pip install feelpp-aptly-publisher`  
✅ **Version management**: Semantic versioning on PyPI  
✅ **Reusability**: Any Feel++ project can use it  
✅ **CI/CD friendly**: No git submodules needed  
✅ **Consistent**: Same tool version everywhere  
✅ **Maintainable**: Single source of truth  
✅ **Documented**: PyPI provides standard documentation  

## Next Steps

1. Complete the refactoring (move all logic from aptly_publish.py)
2. Add comprehensive tests
3. Write detailed documentation
4. Publish to PyPI
5. Update all Feel++ projects to use it
6. Add to CI/CD pipelines
7. Deprecate the standalone script
