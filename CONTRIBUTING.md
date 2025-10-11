# Developer Guide

## Setup Development Environment

### Prerequisites

- Python 3.8 or later
- [uv](https://github.com/astral-sh/uv) - Fast Python package installer
- git

### Install uv

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Clone and Setup

```bash
# Clone repository
git clone https://github.com/feelpp/apt.git
cd apt

# Run setup script
./setup-dev.sh

# Or manually:
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"
```

## Development Workflow

### Run Quality Checks

```bash
# Format code
make format

# Run linter
make lint

# Type check
make type-check

# Run all quality checks
make quality
```

### Run Tests

```bash
# Run all tests
make test

# Run specific test
pytest tests/test_publisher.py -v

# Run with coverage
pytest --cov=feelpp_aptly_publisher --cov-report=html
```

### Build Package

```bash
# Build distribution packages
make build

# Check build
ls -lh dist/
```

## Code Quality Standards

### Black (Code Formatting)

We use [Black](https://black.readthedocs.io/) for consistent code formatting:

```bash
# Format all code
black src/ tests/

# Check formatting without changes
black --check src/ tests/
```

**Configuration**: `pyproject.toml`
- Line length: 120
- Target versions: Python 3.8+

### Flake8 (Linting)

We use [Flake8](https://flake8.pycqa.org/) for code linting:

```bash
# Lint all code
flake8 src/ tests/
```

**Configuration**: `.flake8`
- Max line length: 120
- Ignored errors: E203 (whitespace before ':'), W503 (line break before binary operator)
- Plugins: flake8-bugbear, flake8-comprehensions

### Mypy (Type Checking)

We use [Mypy](http://mypy-lang.org/) for static type checking:

```bash
# Type check
mypy src/
```

**Configuration**: `pyproject.toml`
- Python version: 3.8
- Warn on unused configs
- Return types checked

## Project Structure

```
apt/
├── src/
│   └── feelpp_aptly_publisher/
│       ├── __init__.py          # Package initialization
│       ├── __main__.py          # CLI entry point
│       ├── cli.py               # Command-line interface
│       ├── publisher.py         # Core publishing logic
│       └── py.typed             # Type stub marker
├── tests/
│   ├── __init__.py
│   ├── test_publisher.py        # Publisher tests
│   └── test_cli.py              # CLI tests
├── examples/
│   ├── aptly.conf               # Example aptly config
│   └── publish_example.sh       # Example usage script
├── .github/
│   └── workflows/
│       ├── quality.yml          # Quality checks CI
│       ├── build.yml            # Build and test CI
│       └── publish.yml          # PyPI publishing CI
├── pyproject.toml               # Project metadata and config
├── Makefile                     # Development commands
├── setup-dev.sh                 # Development setup script
├── .flake8                      # Flake8 configuration
├── .gitignore                   # Git ignore rules
└── README_PYPI.md               # Package README
```

## CI/CD Workflows

### Quality Checks (`.github/workflows/quality.yml`)

Runs on every push and PR:
- Black formatting check
- Flake8 linting
- Mypy type checking
- Pytest with coverage
- Tests on Python 3.8-3.12

### Build and Test (`.github/workflows/build.yml`)

Runs on every push and PR:
- Builds package
- Validates with twine
- Tests installation on multiple Python versions
- Tests CLI functionality

### Publish to PyPI (`.github/workflows/publish.yml`)

Runs on releases or manual trigger:
- Builds package
- Publishes to PyPI (on release)
- Publishes to Test PyPI (manual)
- Uses trusted publishing (no API tokens needed)

## Publishing Workflow

### Test PyPI (Testing)

```bash
# Build
make build

# Publish to Test PyPI
make test-publish

# Test installation
pip install --index-url https://test.pypi.org/simple/ feelpp-aptly-publisher
```

### Production PyPI

#### Method 1: GitHub Release (Recommended)

1. Update version in `pyproject.toml`
2. Commit and push
3. Create GitHub release with tag `v1.0.0`
4. CI automatically publishes to PyPI

#### Method 2: Manual

```bash
# Build and publish
make publish

# Or step by step
make build
twine check dist/*
twine upload dist/*
```

## Testing Locally

### Test the CLI

```bash
# Install in development mode
uv pip install -e .

# Test help
feelpp-apt-publish --help

# Test version
feelpp-apt-publish --version

# Test with dry-run (without actual publishing)
feelpp-apt-publish \
    --component test \
    --channel testing \
    --distro noble \
    --verbose
```

### Test as Library

```python
from feelpp_aptly_publisher import AptlyPublisher

pub = AptlyPublisher(
    component="test",
    distro="noble",
    channel="testing",
    verbose=True,
)

# This would publish, so be careful
# pub.publish(debs_dir="./packages/")
```

## Common Tasks

### Add New Feature

1. Create feature branch: `git checkout -b feature/my-feature`
2. Write code with tests
3. Run quality checks: `make quality`
4. Run tests: `make test`
5. Commit and push
6. Create pull request

### Fix Bug

1. Create bugfix branch: `git checkout -b fix/issue-123`
2. Write failing test
3. Fix the bug
4. Verify test passes
5. Run quality checks
6. Commit and push
7. Create pull request

### Update Dependencies

```bash
# Update all dependencies
uv pip install --upgrade -e ".[dev]"

# Update specific dependency
uv pip install --upgrade black

# Freeze requirements
uv pip freeze > requirements-dev.txt
```

## Troubleshooting

### Import Errors

If you see import errors in your IDE:

```bash
# Reinstall in development mode
uv pip install -e .

# Or set PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
```

### Test Failures

```bash
# Run with verbose output
pytest -vv

# Run specific test
pytest tests/test_publisher.py::test_publisher_init -v

# Debug with pdb
pytest --pdb
```

### Type Checking Issues

```bash
# Run mypy with verbose output
mypy --show-error-codes src/

# Ignore specific error
# type: ignore[error-code]
```

## Git Workflow

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add support for multiple architectures
fix: handle missing GPG key gracefully
docs: update README with examples
test: add tests for error handling
ci: update GitHub Actions to use uv
```

### Branch Naming

- `feature/description` - New features
- `fix/issue-number` - Bug fixes
- `docs/description` - Documentation updates
- `refactor/description` - Code refactoring
- `test/description` - Test improvements

## Release Process

1. Update version in `src/feelpp_aptly_publisher/__init__.py`
2. Update version in `pyproject.toml`
3. Update CHANGELOG (if exists)
4. Commit: `git commit -m "chore: bump version to 1.1.0"`
5. Tag: `git tag v1.1.0`
6. Push: `git push && git push --tags`
7. Create GitHub release
8. CI publishes to PyPI automatically

## Resources

- [uv Documentation](https://github.com/astral-sh/uv)
- [Black Documentation](https://black.readthedocs.io/)
- [Flake8 Documentation](https://flake8.pycqa.org/)
- [Mypy Documentation](http://mypy-lang.org/)
- [Pytest Documentation](https://docs.pytest.org/)
- [Python Packaging Guide](https://packaging.python.org/)
- [Conventional Commits](https://www.conventionalcommits.org/)
