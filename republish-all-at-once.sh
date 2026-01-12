#!/bin/bash
# Download existing packages and republish them ALL AT ONCE in the same aptly session
# This ensures all components are added to the same publication

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CHANNEL="${1:-stable}"
DISTRO="${2:-noble}"
WORK_DIR="${3:-/tmp/republish-all-components}"

# APT repository base URL
REPO_BASE="https://feelpp.github.io/apt/$CHANNEL"

echo "=========================================="
echo "Multi-Component Republish"
echo "=========================================="
echo "Channel:  $CHANNEL"
echo "Distro:   $DISTRO"
echo "Work Dir: $WORK_DIR"
echo "=========================================="
echo

# Activate the virtual environment
if [[ -d "$SCRIPT_DIR/.venv" ]]; then
    source "$SCRIPT_DIR/.venv/bin/activate"
    echo "✓ Activated virtual environment"
else
    echo "❌ Virtual environment not found at $SCRIPT_DIR/.venv"
    exit 1
fi

# Verify version
VERSION=$(feelpp-apt-publish --version 2>&1 | awk '{print $2}')
echo "✓ Using feelpp-apt-publish version $VERSION"
echo

# Create work directories
mkdir -p "$WORK_DIR"/{mmg,parmmg,ktirio}
echo "✓ Created work directories"
echo

# Function to download packages from a component
download_component() {
    local component=$1
    local dest_dir=$2
    
    echo "Downloading $component packages..."
    
    local packages_url="$REPO_BASE/dists/$DISTRO/$component/binary-amd64/Packages"
    local packages_file="$dest_dir/Packages"
    
    if ! curl -fsSL "$packages_url" -o "$packages_file" 2>/dev/null; then
        echo "⚠️  Could not download Packages file for $component"
        return 1
    fi
    
    local count=0
    while IFS= read -r line; do
        if [[ "$line" =~ ^Filename:\ (.+)$ ]]; then
            local filename="${BASH_REMATCH[1]}"
            local deb_url="$REPO_BASE/$filename"
            local deb_name=$(basename "$filename")
            
            if curl -fsSL "$deb_url" -o "$dest_dir/$deb_name" 2>/dev/null; then
                count=$((count + 1))
            fi
        fi
    done < "$packages_file"
    
    rm "$packages_file"
    
    if [[ $count -eq 0 ]]; then
        return 1
    fi
    
    echo "✓ Downloaded $count package(s) for $component"
    return 0
}

# Download all components
echo "=========================================="
echo "Downloading Packages"
echo "=========================================="
echo

COMPONENTS=()
DEBS_DIRS=()

if download_component "mmg" "$WORK_DIR/mmg"; then
    COMPONENTS+=("mmg")
    DEBS_DIRS+=("$WORK_DIR/mmg")
fi

if download_component "parmmg" "$WORK_DIR/parmmg"; then
    COMPONENTS+=("parmmg")
    DEBS_DIRS+=("$WORK_DIR/parmmg")
fi

if download_component "ktirio-urban-building" "$WORK_DIR/ktirio"; then
    COMPONENTS+=("ktirio-urban-building")
    DEBS_DIRS+=("$WORK_DIR/ktirio")
fi

if [[ ${#COMPONENTS[@]} -eq 0 ]]; then
    echo "❌ No components could be downloaded"
    exit 1
fi

echo
echo "Downloaded components: ${COMPONENTS[*]}"
echo
read -p "Proceed with republishing? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled. Packages remain in $WORK_DIR"
    exit 0
fi

# Now republish all components in ORDER
# The first one will create the publication, the rest will be added
echo
echo "=========================================="
echo "Republishing All Components"
echo "=========================================="
echo "Strategy:"
echo "  1. Publish first component (creates publication)"
echo "  2-N. Publish remaining components (adds to publication)"
echo "=========================================="
echo

for i in "${!COMPONENTS[@]}"; do
    component="${COMPONENTS[$i]}"
    debs_dir="${DEBS_DIRS[$i]}"
    
    echo
    echo "[$((i+1))/${#COMPONENTS[@]}] Publishing: $component"
    echo "----------------------------------------"
    
    feelpp-apt-publish \
        --component "$component" \
        --channel "$CHANNEL" \
        --distro "$DISTRO" \
        --debs "$debs_dir" \
        --verbose 2>&1 | grep -E "INFO:|ERROR:|Successfully|Adding|Updating"
    
    if [[ $? -eq 0 ]]; then
        echo "✓ Published $component"
    else
        echo "❌ Failed to publish $component"
        exit 1
    fi
    
    # Give GitHub Pages a moment to update
    sleep 3
done

echo
echo "=========================================="
echo "✓ All Components Republished!"
echo "=========================================="
echo

# Wait a bit for GitHub Pages to update
echo "Waiting for GitHub Pages to update..."
sleep 10

echo "Verifying InRelease..."
COMPONENTS_LINE=$(curl -s "$REPO_BASE/dists/$DISTRO/InRelease" | grep "Components:")
echo "$COMPONENTS_LINE"

if [[ "$COMPONENTS_LINE" == *"mmg"* ]] && [[ "$COMPONENTS_LINE" == *"parmmg"* ]]; then
    echo
    echo "✅ SUCCESS! All components are now in InRelease"
else
    echo
    echo "⚠️  WARNING: Not all components found in InRelease"
    echo "Expected: mmg, parmmg, ktirio-urban-building"
    echo "Got: $COMPONENTS_LINE"
fi

echo
echo "Cleaning up work directory..."
rm -rf "$WORK_DIR"
echo "✓ Done"
echo
