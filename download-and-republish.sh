#!/bin/bash
# Download existing packages from the APT repository and republish them
# This allows us to fix the InRelease file without rebuilding packages

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CHANNEL="${1:-stable}"
DISTRO="${2:-noble}"
WORK_DIR="${3:-/tmp/republish-packages}"

# APT repository base URL
REPO_BASE="https://feelpp.github.io/apt/$CHANNEL"

echo "=========================================="
echo "Downloading and Republishing Packages"
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
    echo "Run: uv venv $SCRIPT_DIR/.venv && uv pip install -e $SCRIPT_DIR"
    exit 1
fi

# Verify we have the updated version
VERSION=$(feelpp-apt-publish --version 2>&1 | awk '{print $2}')
echo "✓ Using feelpp-apt-publish version $VERSION"

if [[ "$VERSION" != "1.1.0" ]]; then
    echo "⚠️  Warning: Expected version 1.1.0, got $VERSION"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Please install version 1.1.0 first:"
        echo "  uv pip install -e $SCRIPT_DIR --force-reinstall --no-deps"
        exit 1
    fi
fi

echo

# Create work directories
mkdir -p "$WORK_DIR"/{mmg,parmmg,ktirio}
echo "✓ Created work directories"
echo

# Function to download packages from a component
download_component() {
    local component=$1
    local dest_dir=$2
    local pool_path=$3
    
    echo "----------------------------------------"
    echo "Downloading $component packages..."
    echo "----------------------------------------"
    
    # Get the Packages file to see what's available
    local packages_url="$REPO_BASE/dists/$DISTRO/$component/binary-amd64/Packages"
    echo "Fetching package list from: $packages_url"
    
    # Download Packages file
    local packages_file="$dest_dir/Packages"
    if ! curl -fsSL "$packages_url" -o "$packages_file" 2>/dev/null; then
        echo "⚠️  Could not download Packages file for $component"
        echo "   URL: $packages_url"
        return 1
    fi
    
    # Parse and download each .deb file
    local count=0
    while IFS= read -r line; do
        if [[ "$line" =~ ^Filename:\ (.+)$ ]]; then
            local filename="${BASH_REMATCH[1]}"
            local deb_url="$REPO_BASE/$filename"
            local deb_name=$(basename "$filename")
            
            echo "  Downloading: $deb_name"
            if curl -fsSL "$deb_url" -o "$dest_dir/$deb_name"; then
                count=$((count + 1))
            else
                echo "    ⚠️  Failed to download $deb_name"
            fi
        fi
    done < "$packages_file"
    
    rm "$packages_file"
    
    if [[ $count -eq 0 ]]; then
        echo "❌ No packages downloaded for $component"
        return 1
    fi
    
    echo "✓ Downloaded $count package(s) for $component"
    echo
    return 0
}

# Download packages for each component
COMPONENTS=()

if download_component "mmg" "$WORK_DIR/mmg" "pool/mmg"; then
    COMPONENTS+=("mmg")
fi

if download_component "parmmg" "$WORK_DIR/parmmg" "pool/parmmg"; then
    COMPONENTS+=("parmmg")
fi

if download_component "ktirio-urban-building" "$WORK_DIR/ktirio" "pool/ktirio-urban-building"; then
    COMPONENTS+=("ktirio-urban-building")
fi

if [[ ${#COMPONENTS[@]} -eq 0 ]]; then
    echo "❌ No components could be downloaded"
    exit 1
fi

echo "=========================================="
echo "Downloaded components: ${COMPONENTS[*]}"
echo "=========================================="
echo
read -p "Proceed with republishing? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled. Packages remain in $WORK_DIR"
    exit 0
fi

# Republish each component
for component in "${COMPONENTS[@]}"; do
    echo
    echo "=========================================="
    echo "Publishing: $component"
    echo "=========================================="
    
    case "$component" in
        "mmg")
            debs_dir="$WORK_DIR/mmg"
            ;;
        "parmmg")
            debs_dir="$WORK_DIR/parmmg"
            ;;
        "ktirio-urban-building")
            debs_dir="$WORK_DIR/ktirio"
            ;;
    esac
    
    feelpp-apt-publish \
        --component "$component" \
        --channel "$CHANNEL" \
        --distro "$DISTRO" \
        --debs "$debs_dir" \
        --verbose
    
    echo
    echo "✓ Published $component"
    sleep 2  # Give git/network a moment between publishes
done

echo
echo "=========================================="
echo "✓ Republishing Complete!"
echo "=========================================="
echo
echo "Verify the InRelease file includes all components:"
echo "  curl -s $REPO_BASE/dists/$DISTRO/InRelease | grep Components"
echo
echo "Cleaning up work directory..."
rm -rf "$WORK_DIR"
echo "✓ Done"
echo
