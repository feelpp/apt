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
- [Repository Cleanup](#repository-cleanup)
  - [Cleanup Commands](#cleanup-commands)
  - [Retention Policies](#retention-policies)
  - [Automated Cleanup Workflows](#automated-cleanup-workflows)
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

## Repository Cleanup

The publisher includes tools for cleaning up old packages, particularly pre-release versions (alpha, beta, rc) that accumulate over time.

### Cleanup Commands

#### Analyze (Dry Run)

Analyze the repository to see what packages would be cleaned up:

```bash
# Analyze all channels
feelpp-apt-publish analyze --repo-path ./apt-repo

# Analyze specific channel
feelpp-apt-publish analyze --repo-path ./apt-repo --channels testing,pr

# Custom age limit (default: 90 days)
feelpp-apt-publish analyze --repo-path ./apt-repo --max-age-days 60

# Output as JSON for CI integration
feelpp-apt-publish analyze --repo-path ./apt-repo --json --output report.json
```

#### Cleanup (Execute)

Actually delete old packages:

```bash
# Preview what would be deleted (default: dry-run mode)
feelpp-apt-publish cleanup --repo-path ./apt-repo

# Execute cleanup
feelpp-apt-publish cleanup --repo-path ./apt-repo --execute

# Cleanup with custom age limit
feelpp-apt-publish cleanup --repo-path ./apt-repo --execute --max-age-days 60

# Cleanup specific channels only
feelpp-apt-publish cleanup --repo-path ./apt-repo --execute --channels pr
```

### Retention Policies

Configure how packages are retained using a policy file:

```bash
# Create a default policy configuration
feelpp-apt-publish init-policy --output retention-policy.json

# Use custom policy
feelpp-apt-publish cleanup --repo-path ./apt-repo --policy retention-policy.json
```

**Default policy file: [`retention-policy.json`](./retention-policy.json)**

```json
{
  "prerelease_max_age_days": 90,
  "max_versions_per_package": 0,
  "channel_policies": {
    "stable": {
      "keep_prereleases": true,
      "max_versions": 0
    },
    "testing": {
      "keep_prereleases": false,
      "max_versions": 5
    },
    "pr": {
      "keep_prereleases": false,
      "max_versions": 3,
      "max_age_days": 30
    }
  },
  "protected_components": [],
  "protected_packages": []
}
```

**Policy Settings:**

| Setting | Description | Default |
|---------|-------------|---------|
| `prerelease_max_age_days` | Max age for pre-release packages | 90 |
| `max_versions_per_package` | Keep N latest versions (0=unlimited) | 0 |
| `keep_prereleases` | Whether to keep pre-releases in channel | varies |
| `protected_components` | Components to never clean | [] |
| `protected_packages` | Package name patterns to never clean | [] |

### Automated Cleanup Workflows

The repository includes GitHub Actions workflows for automated cleanup:

#### 1. Cleanup Analysis (Weekly Dry Run)

**Workflow**: `.github/workflows/cleanup-dry-run.yml`

Runs weekly (Sunday 3 AM UTC) to analyze what could be cleaned:

```yaml
# Manual trigger with custom settings
gh workflow run "Cleanup Analysis (Dry Run)" \
  -f max-age-days=60 \
  -f channel=testing \
  -f include-stable-prereleases=false
```

#### 2. Cleanup Old Packages (Monthly)

**Workflow**: `.github/workflows/cleanup.yml`

Runs monthly (1st of month, 4 AM UTC) to clean old pre-releases:

```yaml
# Manual trigger
gh workflow run "Cleanup Old Packages" \
  -f max-age-days=90 \
  -f channel=all \
  -f dry-run=false

# Preview mode (dry run)
gh workflow run "Cleanup Old Packages" \
  -f dry-run=true
```

#### 3. PR Channel Auto-Cleanup (Weekly)

**Workflow**: `.github/workflows/cleanup-pr-channel.yml`

Specifically cleans the PR channel (packages from closed PRs):

- Runs weekly (Monday 5 AM UTC)
- Removes packages older than 30 days
- Can be triggered when a PR is closed via `repository_dispatch`

```yaml
# Trigger cleanup for a specific closed PR
curl -X POST \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  https://api.github.com/repos/feelpp/apt/dispatches \
  -d '{"event_type":"pr-closed","client_payload":{"pr_number":"123"}}'
```

### What Gets Cleaned

**Pre-release versions** matching these patterns:
- `~alpha`, `~beta`, `~rc1`, `~pre`, `~dev`
- `~git`, `~svn`, `~bzr`
- `+git20231015`, `+svn1234`
- `alpha1`, `beta2`, `rc3`

**Version limits** (when configured):
- Excess versions beyond `max_versions` setting
- Oldest versions removed first (keeping newest)

**Channel-specific defaults:**

| Channel | Keep Pre-releases | Max Age | Max Versions |
|---------|-------------------|---------|--------------|
| stable | Yes | - | unlimited |
| testing | No | 90 days | 5 |
| pr | No | 30 days | 3 |

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
