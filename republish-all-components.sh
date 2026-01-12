#!/bin/bash
# Script to republish all components with the new multi-component support
#
# This will properly update the InRelease file to include ALL components

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CHANNEL="${1:-stable}"
DISTRO="${2:-noble}"

echo "=========================================="
echo "Republishing All Components"
echo "=========================================="
echo "Channel: $CHANNEL"
echo "Distro:  $DISTRO"
echo "Tool:    feelpp-apt-publish v1.1.0"
echo "=========================================="
echo

# Activate the virtual environment if it exists
if [[ -d "$SCRIPT_DIR/.venv" ]]; then
    echo "Activating virtual environment..."
    source "$SCRIPT_DIR/.venv/bin/activate"
fi

# Verify we have the updated version
echo "Checking tool version..."
feelpp-apt-publish --version

echo
echo "This will republish components in order:"
echo "  1. ktirio-urban-building (if packages available)"
echo "  2. mmg (if packages available)"
echo "  3. parmmg (if packages available)"
echo
read -p "Continue? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 1
fi

# Note: You'll need to provide the actual package directories
# This is a template - adjust paths as needed

# Component 1: ktirio-urban-building
if [[ -d "/path/to/ktirio/packages" ]]; then
    echo
    echo "=========================================="
    echo "Publishing: ktirio-urban-building"
    echo "=========================================="
    feelpp-apt-publish \
        --component ktirio-urban-building \
        --channel "$CHANNEL" \
        --distro "$DISTRO" \
        --debs /path/to/ktirio/packages \
        --verbose
else
    echo
    echo "⚠️  Skipping ktirio-urban-building (packages not found)"
fi

# Component 2: mmg
if [[ -d "/nvme0/prudhomm/Devel/feelpp.quickfix/third-party/mmg/packages" ]]; then
    echo
    echo "=========================================="
    echo "Publishing: mmg"
    echo "=========================================="
    feelpp-apt-publish \
        --component mmg \
        --channel "$CHANNEL" \
        --distro "$DISTRO" \
        --debs /nvme0/prudhomm/Devel/feelpp.quickfix/third-party/mmg/packages \
        --verbose
else
    echo
    echo "⚠️  Skipping mmg (packages not found)"
fi

# Component 3: parmmg
if [[ -d "/nvme0/prudhomm/Devel/feelpp.quickfix/third-party/ParMmg/packages" ]]; then
    echo
    echo "=========================================="
    echo "Publishing: parmmg"
    echo "=========================================="
    feelpp-apt-publish \
        --component parmmg \
        --channel "$CHANNEL" \
        --distro "$DISTRO" \
        --debs /nvme0/prudhomm/Devel/feelpp.quickfix/third-party/ParMmg/packages \
        --verbose
else
    echo
    echo "⚠️  Skipping parmmg (packages not found)"
fi

echo
echo "=========================================="
echo "✓ Republishing Complete!"
echo "=========================================="
echo
echo "Verify the InRelease file includes all components:"
echo "  curl -s https://feelpp.github.io/apt/$CHANNEL/dists/$DISTRO/InRelease | grep Components"
echo
echo "Expected: Components: ktirio-urban-building mmg parmmg"
echo
