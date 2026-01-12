# Feel++ Aptly Publisher

[![PyPI version](https://badge.fury.io/py/feelpp-aptly-publisher.svg)](https://badge.fury.io/py/feelpp-aptly-publisher)
[![Python Support](https://img.shields.io/pypi/pyversions/feelpp-aptly-publisher.svg)](https://pypi.org/project/feelpp-aptly-publisher/)
[![License: LGPL v3](https://img.shields.io/badge/License-LGPL%20v3-blue.svg)](https://www.gnu.org/licenses/lgpl-3.0)

Tool to publish Debian packages to Feel++ APT repository via aptly and GitHub Pages.

## Features

- ✅ Bootstrap or update APT repository components
- ✅ Support for multiple channels (stable, testing, pr)
- ✅ Multiple distributions (Ubuntu, Debian)
- ✅ GPG signing support
- ✅ GitHub Pages integration
- ✅ Reusable aptly configuration
- ✅ Comprehensive logging
- ✅ CI/CD friendly
- ✅ Zero external Python dependencies (stdlib only)

## Requirements

System tools (must be on PATH):
- `aptly` - APT repository management tool
- `git` - Version control
- `rsync` - File synchronization
- `gpg` - GPG signing (optional, only if using --sign)

## Installation

```bash
# From PyPI
pip install feelpp-aptly-publisher

# From source
pip install git+https://github.com/feelpp/apt.git

# Development mode
git clone https://github.com/feelpp/apt.git
cd apt
pip install -e .
```

## Quick Start

### Publish Debian packages

```bash
feelpp-apt-publish \
    --component mmg \
    --channel stable \
    --distro noble \
    --debs ./packages/
```

### Bootstrap empty component

```bash
feelpp-apt-publish \
    --component new-project \
    --channel testing \
    --distro noble
```

### With GPG signing

```bash
feelpp-apt-publish \
    --component feelpp \
    --channel stable \
    --distro jammy \
    --debs ./build/packages/ \
    --sign \
    --keyid YOUR_GPG_KEY_ID
```

## Usage

### Command Line

```bash
feelpp-apt-publish [OPTIONS]

Options:
  --component TEXT         Project/component name (required)
  --distro TEXT           Distribution (default: noble)
  --channel TEXT          Channel: stable|testing|pr (default: stable)
  --debs PATH             Directory with .deb files (optional)
  --pages-repo URL        GitHub Pages repo (default: feelpp/apt)
  --branch TEXT           Git branch (default: gh-pages)
  --sign                  Enable GPG signing
  --keyid TEXT            GPG key ID (required if --sign)
  --passphrase TEXT       GPG passphrase (optional)
  --aptly-config PATH     Aptly config file (optional)
  --aptly-root PATH       Aptly root directory (optional)
  --verbose               Enable debug logging
  --version               Show version
  --help                  Show help message
```

### As Python Library

```python
from feelpp_aptly_publisher import AptlyPublisher

# Create publisher
publisher = AptlyPublisher(
    component="mmg",
    distro="noble",
    channel="stable",
    pages_repo="https://github.com/feelpp/apt.git",
    verbose=True,
)

# Publish packages
publisher.publish(debs_dir="./packages/")

# Or bootstrap empty component
publisher.bootstrap()
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PAGES_REPO` | GitHub Pages repository URL | `https://github.com/feelpp/apt.git` |
| `BRANCH` | Git branch for GitHub Pages | `gh-pages` |
| `GPG_KEYID` | GPG key ID for signing | None |
| `GPG_PASSPHRASE` | GPG passphrase | None |

## Channels

- **stable**: Production releases
- **testing**: Beta/RC releases  
- **pr**: Pull request builds

## Distributions

Supported distributions include:
- **Ubuntu**: `noble` (24.04), `jammy` (22.04), `focal` (20.04)
- **Debian**: `bookworm` (12), `bullseye` (11)

## CI/CD Integration

### GitHub Actions

```yaml
name: Publish to APT

on:
  push:
    tags:
      - 'v*'

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Install publisher
        run: pip install feelpp-aptly-publisher
      
      - name: Publish to APT
        env:
          GPG_KEYID: ${{ secrets.GPG_KEYID }}
          GPG_PASSPHRASE: ${{ secrets.GPG_PASSPHRASE }}
        run: |
          feelpp-apt-publish \
            --component ${{ github.event.repository.name }} \
            --channel stable \
            --distro noble \
            --debs ./packages/ \
            --sign
```

### Jenkins

```groovy
stage('Publish to APT') {
    steps {
        sh 'pip install feelpp-aptly-publisher'
        withCredentials([
            string(credentialsId: 'gpg-keyid', variable: 'GPG_KEYID'),
            string(credentialsId: 'gpg-pass', variable: 'GPG_PASSPHRASE')
        ]) {
            sh '''
                feelpp-apt-publish \
                    --component ${JOB_NAME} \
                    --channel stable \
                    --distro noble \
                    --debs ./packages/ \
                    --sign
            '''
        }
    }
}
```

### GitLab CI

```yaml
publish:apt:
  stage: deploy
  script:
    - pip install feelpp-aptly-publisher
    - |
      feelpp-apt-publish \
        --component ${CI_PROJECT_NAME} \
        --channel stable \
        --distro noble \
        --debs ./packages/ \
        --sign \
        --keyid ${GPG_KEYID}
  only:
    - tags
```

## Examples

See the [examples/](examples/) directory for:
- Sample aptly configuration
- Publishing scripts
- CI/CD templates

## Development

```bash
# Clone repository
git clone https://github.com/feelpp/apt.git
cd apt

# Install in development mode with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black src/ tests/

# Lint code
ruff check src/ tests/

# Type check
mypy src/
```

## License

This project is licensed under the GNU Lesser General Public License v3.0 or later (LGPL-3.0-or-later). See [COPYING.LESSER](COPYING.LESSER) for details.

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Support

- **Issues**: https://github.com/feelpp/apt/issues
- **Documentation**: https://github.com/feelpp/apt#readme
- **Feel++ Website**: https://www.feelpp.org
- **APT Repository**: https://feelpp.github.io/apt/

## Authors

- Feel++ Consortium <contact@feelpp.org>
- Feel++ Packaging Team

## Acknowledgments

Built for the Feel++ project ecosystem to simplify Debian package distribution via APT repositories hosted on GitHub Pages.
