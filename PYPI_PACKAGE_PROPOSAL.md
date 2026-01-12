# PyPI Package Proposal: `feelpp-aptly-publisher`

## Overview
Create a standalone PyPI package for the aptly publishing tool to enable easy distribution and reuse across all Feel++ projects and third-party dependencies.

## Package Structure

```
feelpp-aptly-publisher/
├── pyproject.toml
├── README.md
├── LICENSE
├── .gitignore
├── src/
│   └── feelpp_aptly_publisher/
│       ├── __init__.py
│       ├── __main__.py
│       ├── publisher.py          # Core logic from aptly_publish.py
│       ├── cli.py                # CLI interface
│       └── config.py             # Config handling
├── tests/
│   ├── __init__.py
│   ├── test_publisher.py
│   └── test_cli.py
└── examples/
    ├── aptly.conf
    └── publish_example.sh
```

## Installation

```bash
# From PyPI
pip install feelpp-aptly-publisher

# From source
pip install git+https://github.com/feelpp/aptly-publisher.git
```

## Usage

### As a CLI tool:
```bash
# Simple usage
feelpp-apt-publish \
    --component mmg \
    --channel stable \
    --distro noble \
    --debs ./packages/

# With signing
feelpp-apt-publish \
    --component feelpp \
    --channel stable \
    --distro jammy \
    --debs ./build/packages/ \
    --sign \
    --keyid YOUR_GPG_KEY_ID

# Bootstrap empty component
feelpp-apt-publish \
    --component new-project \
    --channel testing \
    --distro noble
```

### As a Python library:
```python
from feelpp_aptly_publisher import AptlyPublisher

publisher = AptlyPublisher(
    component="mmg",
    distro="noble",
    channel="stable",
    pages_repo="https://github.com/feelpp/apt.git",
)

# Publish with .deb files
publisher.publish(debs_dir="./packages/")

# Or bootstrap empty
publisher.bootstrap()
```

## Features

- ✅ Bootstrap or update APT repository components
- ✅ Support for multiple channels (stable, testing, pr)
- ✅ Multiple distributions (Ubuntu, Debian)
- ✅ GPG signing support
- ✅ GitHub Pages integration
- ✅ Reusable aptly configuration
- ✅ Comprehensive logging
- ✅ CI/CD friendly

## Environment Variables

```bash
PAGES_REPO=https://github.com/feelpp/apt.git
BRANCH=gh-pages
GPG_KEYID=your-key-id
GPG_PASSPHRASE=your-passphrase  # Optional, for automation
```

## Dependencies

```toml
[project]
name = "feelpp-aptly-publisher"
version = "1.0.0"
requires-python = ">=3.8"
dependencies = []  # Only stdlib, or add 'click' for better CLI

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-cov>=4.0",
    "black>=23.0",
    "mypy>=1.0",
    "ruff>=0.1.0",
]
```

## CI/CD Integration

### GitHub Actions Example:
```yaml
- name: Install publisher
  run: pip install feelpp-aptly-publisher

- name: Publish to APT
  env:
    PAGES_REPO: ${{ secrets.APT_REPO }}
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

### Jenkins Example:
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
                    --channel ${BRANCH_NAME == 'master' ? 'stable' : 'testing'} \
                    --distro noble \
                    --debs ./packages/ \
                    --sign
            '''
        }
    }
}
```

## Benefits

1. **Easy Distribution**: `pip install` anywhere
2. **Version Control**: Track tool versions separately from projects
3. **Testing**: Proper unit tests and CI
4. **Documentation**: Standard PyPI docs + examples
5. **Independence**: Projects don't need the entire apt repo
6. **Consistency**: Same tool version across all Feel++ projects
7. **Extensibility**: Easy to add plugins or extensions

## Migration Path

### Phase 1: Create Package
- Extract `aptly_publish.py` into package structure
- Add tests and documentation
- Publish to PyPI

### Phase 2: Update Projects
- Add to CI/CD pipelines
- Create wrapper scripts (like `publish-mmg.sh`)
- Update documentation

### Phase 3: Deprecation
- Keep `apt/scripts/aptly_publish.py` as alias
- Eventually remove in favor of PyPI package

## Package Name Options

1. `feelpp-aptly-publisher` (recommended)
2. `feelpp-apt-tools`
3. `aptly-gh-pages`
4. `apt-component-publisher`

## Repository

- **Name**: `feelpp/aptly-publisher`
- **URL**: https://github.com/feelpp/aptly-publisher
- **PyPI**: https://pypi.org/project/feelpp-aptly-publisher/

## Next Steps

1. Create new repository `feelpp/aptly-publisher`
2. Refactor `aptly_publish.py` into package structure
3. Add tests and CI
4. Publish to PyPI
5. Update mmg and other projects to use it
6. Document in Feel++ developer guide
