#!/bin/bash
# Example: Publishing MMG packages using feelpp-aptly-publisher

set -e

COMPONENT="mmg"
CHANNEL="${1:-stable}"
DISTRO="${2:-noble}"
PACKAGES_DIR="${3:-./packages}"

echo "Publishing $COMPONENT to $CHANNEL/$DISTRO"
echo "Packages from: $PACKAGES_DIR"
echo

feelpp-apt-publish \
    --component "$COMPONENT" \
    --channel "$CHANNEL" \
    --distro "$DISTRO" \
    --debs "$PACKAGES_DIR" \
    --verbose

echo
echo "Done! Packages published to https://feelpp.github.io/apt/$CHANNEL/dists/$DISTRO/"
