# Quick Start Guide

## For Users

### Installation

```bash
pip install feelpp-aptly-publisher
```

### Basic Usage

```bash
# Publish packages to stable channel
feelpp-apt-publish \
    --component myproject \
    --channel stable \
    --distro noble \
    --debs ./packages/

# Bootstrap empty component
feelpp-apt-publish \
    --component newproject \
    --channel testing \
    --distro noble
```

### With Environment Variables

```bash
export PAGES_REPO=https://github.com/feelpp/apt.git
export BRANCH=gh-pages

feelpp-apt-publish \
    --component myproject \
    --debs ./packages/
```

## For Developers

### Setup (5 minutes)

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and setup
git clone https://github.com/feelpp/apt.git
cd apt
./setup-dev.sh

# Activate environment
source .venv/bin/activate
```

### Development Commands

```bash
# Run tests
make test

# Check code quality
make quality

# Build package
make build

# Publish to Test PyPI
make test-publish
```

### First Contribution

1. Fork the repository
2. Create feature branch: `git checkout -b feature/my-feature`
3. Make changes and add tests
4. Run `make quality` and `make test`
5. Commit: `git commit -m "feat: add my feature"`
6. Push and create pull request

## Examples

### Publish MMG Package

```bash
# Build debian packages
cd mmg
dpkg-buildpackage -us -uc

# Publish to APT
feelpp-apt-publish \
    --component mmg \
    --channel stable \
    --distro noble \
    --debs ./packages/ \
    --verbose
```

### Use in CI/CD

```yaml
# .github/workflows/publish-apt.yml
- name: Install publisher
  run: pip install feelpp-aptly-publisher

- name: Publish
  run: |
    feelpp-apt-publish \
      --component ${{ github.event.repository.name }} \
      --channel stable \
      --distro noble \
      --debs ./packages/
```

### Python API

```python
from feelpp_aptly_publisher import AptlyPublisher

publisher = AptlyPublisher(
    component="myproject",
    distro="noble",
    channel="stable",
)

publisher.publish(debs_dir="./packages/")
```

## Common Issues

### Command not found

```bash
# Ensure package is installed
pip install feelpp-aptly-publisher

# Check installation
which feelpp-apt-publish
```

### Missing system tools

```bash
# Ubuntu/Debian
sudo apt install aptly git rsync

# For signing
sudo apt install gnupg
```

### Permission errors

```bash
# Ensure you have access to the repository
git clone https://github.com/feelpp/apt.git

# Configure git credentials
gh auth login
```

## Next Steps

- Read full documentation in [README_PYPI.md](README_PYPI.md)
- See [CONTRIBUTING.md](CONTRIBUTING.md) for development guide
- Check [examples/](examples/) for more examples
- Visit [https://feelpp.github.io/apt/](https://feelpp.github.io/apt/) for repository info
