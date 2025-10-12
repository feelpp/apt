# Feel++ APT Repository Publisher

**Repository URL**: https://feelpp.github.io/apt/  
**Public key**: [`feelpp.gpg`](./feelpp.gpg)

This repository contains the `feelpp-aptly-publisher` tool for publishing Debian packages to the Feel++ APT repository using aptly and GitHub Pages, with full support for multi-component publications.

## Table of Contents

- [Repository Structure](#repository-structure)
- [Client Setup](#client-setup)
- [Publishing Packages](#publishing-packages)
  - [Quick Start](#quick-start)
  - [Publishing to Different Channels](#publishing-to-different-channels)
  - [Multi-Component Support](#multi-component-support)
- [Installation](#installation)
- [Development](#development)
- [Testing](#testing)

## Repository Structure

The APT repository is organized as follows:

- **Channels (prefixes)**: `stable/`, `testing/`, `pr/`
  - `stable`: Production-ready packages
  - `testing`: Pre-release packages for testing
  - `pr`: Pull request builds for CI/CD
  
- **Distributions**: `noble`, `jammy`, `focal`, `bookworm`, `bullseye`, etc.
  - Ubuntu codenames (noble = 24.04, jammy = 22.04, etc.)
  - Debian codenames (bookworm = 12, bullseye = 11, etc.)
  
- **Components (projects)**: Independent project namespaces
  - Examples: `feelpp-project`, `mmg`, `parmmg`, `ktirio-urban-building`, `organ-on-chip`
  - Each component can have multiple packages
  - Components are isolated - updates to one don't affect others

## Client Setup

Add the Feel++ APT repository to your system:

```bash
# Download and install the GPG key
curl -fsSL https://feelpp.github.io/apt/feelpp.gpg \
  | sudo tee /usr/share/keyrings/feelpp.gpg >/dev/null

# Add the repository (example: stable channel, noble distribution, multiple components)
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/feelpp.gpg] \
https://feelpp.github.io/apt/stable noble mmg parmmg" \
| sudo tee /etc/apt/sources.list.d/feelpp-mmg.list

# Update package lists
sudo apt update

# Install packages
sudo apt install mmg libmmg5 libmmg-dev parmmg libparmmg5 libparmmg-dev
```

**Note**: Specify the components you need in the sources.list line. Available components can be found in the [Release file](https://feelpp.github.io/apt/stable/dists/noble/Release).

## Publishing Packages

### Quick Start

1. **Install the publisher tool**:
```bash
pip install feelpp-aptly-publisher
# or for development:
pip install -e .
```

2. **Build your Debian packages**:
```bash
# Your package building process, e.g.:
dpkg-buildpackage -us -uc -b
```

3. **Publish to the repository**:
```bash
feelpp-apt-publish \
  --component my-project \
  --channel stable \
  --distro noble \
  --debs /path/to/directory/with/debs
```

That's it! Your packages are now available at:
- `https://feelpp.github.io/apt/stable/dists/noble/my-project/`

### Publishing to Different Channels

**Stable** (production releases):
```bash
feelpp-apt-publish --component mmg --channel stable --distro noble --debs ./debs/
```

**Testing** (pre-release testing):
```bash
feelpp-apt-publish --component mmg --channel testing --distro noble --debs ./debs/
```

**PR** (continuous integration):
```bash
feelpp-apt-publish --component mmg --channel pr --distro noble --debs ./debs/
```

### Multi-Component Support

The publisher **automatically preserves existing components** when adding or updating a component. You don't need to do anything special!

**Example scenario:**

1. Initial state: Repository has `component-a` and `component-b`
2. You publish `component-c`:
   ```bash
   feelpp-apt-publish --component component-c --channel stable --distro noble --debs ./debs/
   ```
3. Result: Repository now has `component-a`, `component-b`, **and** `component-c`

**Updating an existing component:**

```bash
# This will update component-a while preserving component-b and component-c
feelpp-apt-publish --component component-a --channel stable --distro noble --debs ./new-debs/
```

**How it works:**
- The publisher reads the current Release file to detect existing components
- It creates temporary repositories for existing components from the pool
- It publishes all components together using aptly's multi-component support
- Both Release and InRelease files are updated consistently

### Command-Line Options

```bash
feelpp-apt-publish --help
```

**Required options:**
- `--component NAME`: Component (project) name (will be normalized: `My_Project` → `my-project`)
- `--distro NAME`: Distribution codename (e.g., `noble`, `jammy`, `bookworm`)

**Optional options:**
- `--channel NAME`: Publication channel (default: `stable`, options: `stable`, `testing`, `pr`)
- `--debs PATH`: Directory containing .deb files (default: current directory)
- `--pages-repo URL`: GitHub Pages repository (default: `https://github.com/feelpp/apt.git`)
- `--branch NAME`: Git branch name (default: `gh-pages`)
- `--sign`: Enable GPG signing (default: disabled)
- `--keyid ID`: GPG key ID (required if --sign is used)
- `--verbose`: Enable verbose logging

**Examples:**

```bash
# Minimal example (uses defaults: stable channel, skip signing)
feelpp-apt-publish --component mmg --distro noble --debs ./debs/

# Full example with all options
feelpp-apt-publish \
  --component my-project \
  --distro noble \
  --channel testing \
  --debs /tmp/my-debs \
  --verbose

# With GPG signing
feelpp-apt-publish \
  --component mmg \
  --distro noble \
  --sign \
  --keyid ABCD1234 \
  --debs ./debs/
```

## Installation

### From PyPI (when published)

```bash
pip install feelpp-aptly-publisher
```

### From Source

```bash
git clone https://github.com/feelpp/apt.git
cd apt
pip install -e .
```

### Development Setup

```bash
# Install with development dependencies
pip install -e ".[dev]"

# Or using the setup script
./setup-dev.sh
```

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run only unit tests (fast)
pytest -m "not integration"

# Run integration tests (slower, tests actual publishing)
pytest -m integration

# Run with coverage
pytest --cov=feelpp_aptly_publisher --cov-report=html
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint
flake8 src/ tests/

# Type checking
mypy src/
```

## Testing

The repository includes comprehensive tests:

- **Unit tests** (`tests/test_*.py`): Fast tests for individual components
  - CLI argument parsing
  - Component name normalization
  - Publisher initialization
  
- **Integration tests** (`tests/test_integration.py`): Full workflow tests
  - Single component publishing
  - Multi-component publishing (adding components)
  - Updating existing components
  - All three channels (stable, testing, pr)
  - Channel independence
  - Release/InRelease file consistency

Run the test suite:
```bash
# All tests
pytest -v

# Only integration tests
pytest -v -m integration

# Only unit tests (fast)
pytest -v -m "not integration"
```

## Troubleshooting

### Components Not Listed in InRelease

**Problem**: After publishing, packages install correctly but InRelease file doesn't list all components.

**Solution**: This was a bug in earlier versions. Update to `feelpp-aptly-publisher >= 1.1.0` which fixes multi-component support.

### Existing Components Lost After Publishing

**Problem**: Publishing a new component removes existing components from the repository.

**Solution**: Upgrade to version >= 1.1.0. The new version automatically detects and preserves all existing components.

### Package Not Found After Publishing

**Problem**: Published package but `apt update` doesn't see it.

**Checklist**:
1. Check that the component is listed in your sources.list
2. Verify the component appears in the Release file:
   ```bash
   curl -s https://feelpp.github.io/apt/stable/dists/noble/Release | grep Components
   ```
3. Check that packages exist:
   ```bash
   curl -s https://feelpp.github.io/apt/stable/dists/noble/COMPONENT/binary-amd64/Packages
   ```
4. Wait a few minutes for GitHub Pages to update (caching)

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

## License

LGPL-3.0-or-later - see [COPYING.LESSER](COPYING.LESSER)

## Authors

Feel++ Packaging Team <contact@feelpp.org>

---

**Repository**: https://github.com/feelpp/apt  
**Feel++ Project**: https://www.feelpp.org
