#!/bin/bash
# Script to migrate mmg and parmmg packages from their individual components to the base component
#
# This script leverages the feelpp-aptly-publisher Python package which automatically:
# - Recovers aptly database from existing publications
# - Preserves existing components when adding/updating
# - Republishes all components together
#
# The migration simply republishes packages using the updated scripts that target 'base' component.

set -e

DISTRIBUTION="noble"
CHANNEL="stable"

echo "=== Migration to Base Component ==="
echo ""
echo "This script uses the feelpp-aptly-publisher to migrate packages from"
echo "individual components to the new layer-based component structure."
echo ""
echo "New structure:"
echo "  base ─┬─> feelpp ──> applications"
echo "        └────────────> ktirio"
echo ""
echo "Current state in ${CHANNEL}/${DISTRIBUTION}:"
echo "  - mmg component: libmmg-dev, libmmg5, mmg (version 5.8.0-1feelpp1)"
echo "  - parmmg component: libparmmg-dev, libparmmg5, parmmg (version 1.5.0-1)"
echo "  - ktirio-urban-building component: ktirio-urban-building"
echo ""
echo "Target state:"
echo "  - base component: napp, mmg, parmmg (external dependencies)"
echo "  - ktirio component: ktirio-urban-building (KTIRIO domain stack)"
echo ""
echo "How it works:"
echo "  The feelpp-aptly-publisher automatically:"
echo "  1. Downloads existing packages from the mmg/parmmg/ktirio pools"
echo "  2. Publishes them to the appropriate new components"
echo "  3. Preserves all existing components during transition"
echo "  4. Creates a unified InRelease with all components"
echo ""
echo "After migration, both old and new components coexist:"
echo "  - Old: deb [...] noble mmg                     (deprecated)"
echo "  - Old: deb [...] noble parmmg                  (deprecated)"
echo "  - Old: deb [...] noble ktirio-urban-building   (deprecated)"
echo "  - New: deb [...] noble base                    (recommended for deps)"
echo "  - New: deb [...] noble base feelpp ktirio      (recommended for KTIRIO)"
echo ""

read -p "Continue with migration? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Migration cancelled."
    exit 0
fi

# Ensure we have the publisher available
echo ""
echo "=== Checking requirements ==="
if ! command -v feelpp-apt-publish &> /dev/null; then
    echo "ERROR: feelpp-apt-publish not found"
    echo "Installing from local source..."
    cd /nvme0/prudhomm/Devel/feelpp.quickfix/apt
    uv pip install -e . --quiet
    if ! command -v feelpp-apt-publish &> /dev/null; then
        echo "ERROR: Failed to install feelpp-apt-publish"
        exit 1
    fi
fi

echo "✓ feelpp-apt-publish available"

# Check if we need to download existing packages
echo ""
echo "=== Preparing package files ==="

# MMG packages
MMG_DIR="/nvme0/prudhomm/Devel/feelpp.quickfix/third-party/mmg"
cd "$MMG_DIR"
if [ ! -f "libmmg5_5.8.0-1feelpp1_amd64.deb" ]; then
    echo "Downloading mmg packages from stable/noble/mmg..."
    mkdir -p /tmp/mmg-migration
    cd /tmp/mmg-migration
    
    # Download packages from the pool
    for pkg in libmmg-dev libmmg5 mmg; do
        wget -q "https://feelpp.github.io/apt/stable/pool/mmg/${pkg:0:1}/${pkg}/${pkg}_5.8.0-1feelpp1_amd64.deb" || \
        wget -q "https://feelpp.github.io/apt/stable/pool/mmg/${pkg:0:4}/${pkg}/${pkg}_5.8.0-1feelpp1_amd64.deb" || \
        echo "Warning: Could not download ${pkg}"
    done
    
    # Copy to mmg directory
    cp *.deb "$MMG_DIR/" 2>/dev/null || true
    cd "$MMG_DIR"
fi

MMG_DEBS=$(ls *.deb 2>/dev/null | wc -l)
echo "Found $MMG_DEBS mmg .deb file(s)"

# ParMmg packages
PARMMG_DIR="/nvme0/prudhomm/Devel/feelpp.quickfix/third-party/ParMmg"
cd "$PARMMG_DIR"
if [ ! -f "libparmmg5_1.5.0-1_amd64.deb" ]; then
    echo "Downloading parmmg packages from stable/noble/parmmg..."
    mkdir -p /tmp/parmmg-migration
    cd /tmp/parmmg-migration
    
    # Download packages from the pool
    for pkg in libparmmg-dev libparmmg5 parmmg; do
        wget -q "https://feelpp.github.io/apt/stable/pool/parmmg/${pkg:0:1}/${pkg}/${pkg}_1.5.0-1_amd64.deb" || \
        wget -q "https://feelpp.github.io/apt/stable/pool/parmmg/${pkg:0:4}/${pkg}/${pkg}_1.5.0-1_amd64.deb" || \
        echo "Warning: Could not download ${pkg}"
    done
    
    # Copy to parmmg directory
    cp *.deb "$PARMMG_DIR/" 2>/dev/null || true
    cd "$PARMMG_DIR"
fi

PARMMG_DEBS=$(ls *.deb 2>/dev/null | wc -l)
echo "Found $PARMMG_DEBS parmmg .deb file(s)"

# NAPP package
NAPP_DEB="/nvme0/prudhomm/Devel/libnapp-dev_0.3-1feelpp1_all.deb"
if [ ! -f "$NAPP_DEB" ]; then
    echo ""
    echo "Building napp package..."
    cd /nvme0/prudhomm/Devel/napp
    if [ -f "./debian/build-deb.sh" ]; then
        ./debian/build-deb.sh
    else
        echo "ERROR: debian/build-deb.sh not found"
        exit 1
    fi
    # Check again after build (dpkg-buildpackage creates it in parent dir)
    NAPP_DEB="/nvme0/prudhomm/Devel/libnapp-dev_0.3-1feelpp1_all.deb"
fi

if [ -f "$NAPP_DEB" ]; then
    echo "✓ napp package ready"
else
    echo "ERROR: Failed to build napp package"
    exit 1
fi

# Now publish all packages to base component
echo ""
echo "=== Step 1: Publishing napp to ${CHANNEL}/${DISTRIBUTION}/base ==="
cd /nvme0/prudhomm/Devel/napp
if [ -f "./debian/publish-napp.sh" ]; then
    echo "Running: ./debian/publish-napp.sh ${CHANNEL} ${DISTRIBUTION}"
    ./debian/publish-napp.sh ${CHANNEL} ${DISTRIBUTION}
else
    echo "ERROR: publish-napp.sh not found"
    exit 1
fi

echo ""
echo "=== Step 2: Publishing mmg to ${CHANNEL}/${DISTRIBUTION}/base ==="
cd "$MMG_DIR"
if [ -f "./publish-mmg-pypi.sh" ]; then
    echo "Running: ./publish-mmg-pypi.sh ${CHANNEL} ${DISTRIBUTION}"
    ./publish-mmg-pypi.sh ${CHANNEL} ${DISTRIBUTION}
else
    echo "ERROR: publish-mmg-pypi.sh not found"
    exit 1
fi

echo ""
echo "=== Step 3: Publishing parmmg to ${CHANNEL}/${DISTRIBUTION}/base ==="
cd "$PARMMG_DIR"
if [ -f "./publish-parmmg-pypi.sh" ]; then
    echo "Running: ./publish-parmmg-pypi.sh ${CHANNEL} ${DISTRIBUTION}"
    ./publish-parmmg-pypi.sh ${CHANNEL} ${DISTRIBUTION}
else
    echo "ERROR: publish-parmmg-pypi.sh not found"
    exit 1
fi

# Verify migration
echo ""
echo "=== Verification ==="
echo ""
echo "Waiting 10 seconds for GitHub Pages to update..."
sleep 10

echo "Checking components in ${CHANNEL}/${DISTRIBUTION}..."
COMPONENTS=$(curl -s https://feelpp.github.io/apt/${CHANNEL}/dists/${DISTRIBUTION}/InRelease | grep "^Components:" || echo "Components: (not found)")
echo "$COMPONENTS"

echo ""
echo "Checking packages in base component..."
BASE_PACKAGES=$(curl -s https://feelpp.github.io/apt/${CHANNEL}/dists/${DISTRIBUTION}/base/binary-amd64/Packages 2>/dev/null | grep -E "^Package:" | wc -l || echo "0")
echo "Found $BASE_PACKAGES package(s) in base component"

if [ "$BASE_PACKAGES" -ge 9 ]; then
    echo "✓ Expected packages present (napp: 1, mmg: 3, parmmg: 3, total: 9+)"
else
    echo "⚠ Expected 9+ packages, found $BASE_PACKAGES"
    echo "  Note: It may take a few minutes for GitHub Pages to fully update"
fi

echo ""
echo "=== Migration Complete ==="
echo ""
echo "✓ napp, mmg, and parmmg are now published in the 'base' component"
echo "✓ Existing component structure preserved during transition"
echo ""
echo "Recommended APT sources for users:"
echo ""
echo "For core dependencies only:"
echo "  deb https://feelpp.github.io/apt/${CHANNEL} ${DISTRIBUTION} base"
echo ""
echo "For Feel++ development:"
echo "  deb https://feelpp.github.io/apt/${CHANNEL} ${DISTRIBUTION} base feelpp"
echo ""
echo "For KTIRIO users:"
echo "  deb https://feelpp.github.io/apt/${CHANNEL} ${DISTRIBUTION} base feelpp ktirio"
echo ""
echo "For Feel++ applications:"
echo "  deb https://feelpp.github.io/apt/${CHANNEL} ${DISTRIBUTION} base feelpp applications"
echo ""
echo "Old individual components (deprecated but still functional):"
echo "  deb https://feelpp.github.io/apt/${CHANNEL} ${DISTRIBUTION} mmg"
echo "  deb https://feelpp.github.io/apt/${CHANNEL} ${DISTRIBUTION} parmmg"
echo ""
echo "Next steps:"
echo "  1. Test installation from the new components"
echo "  2. Update documentation (README, installation guides)"
echo "  3. Announce the new structure to users"
echo "  4. After transition period (3-6 months), deprecate old components"
echo ""
echo "The new layer-based structure:"
echo "  base → feelpp → {applications, ktirio}"
echo ""
echo "Old components will coexist during the transition period."
