# Feel++ APT Publisher Tests

This directory contains comprehensive tests for the Feel++ APT repository publisher.

## Test Structure

### 1. `test_publisher.py` - Unit Tests
Basic unit tests for the `AptlyPublisher` class:
- Component name normalization
- Publisher initialization
- Configuration validation
- Different channels and distributions

**Run:** `pytest tests/test_publisher.py`

### 2. `test_integration.py` - Integration Tests
End-to-end integration tests for the publishing workflow:
- Single component publishing
- Multi-component publishing
- Component preservation during updates
- All three channels (stable, testing, pr)
- Release and InRelease file consistency
- Channel independence

**Run:** `pytest tests/test_integration.py -m integration`

### 3. `test_component_architecture.py` - Architecture Tests
Tests for the 4-layer component architecture:

```
base ─┬─> feelpp ──> applications
      └────────────> ktirio
```

**Layer tests:**
- Publishing base layer (external dependencies)
- Publishing feelpp layer (core framework)
- Publishing applications layer (general apps)
- Publishing ktirio layer (domain stack)
- Full architecture deployment
- Updates preserve other layers
- Independent channel architectures

**Run:** `pytest tests/test_component_architecture.py -m architecture`

## Running Tests

### All Tests
```bash
pytest tests/
```

### Specific Test Categories
```bash
# Unit tests only (fast)
pytest tests/test_publisher.py

# Integration tests (requires git, dpkg-deb, aptly)
pytest tests/test_integration.py -m integration

# Architecture tests (comprehensive)
pytest tests/test_component_architecture.py -m architecture
```

### With Coverage
```bash
pytest tests/ --cov=src/feelpp_aptly_publisher --cov-report=html
```

### Verbose Output
```bash
pytest tests/ -v -s
```

### Run Specific Test
```bash
pytest tests/test_component_architecture.py::test_full_architecture_stable -v
```

## Test Markers

Tests use pytest markers for categorization:

- `@pytest.mark.integration` - Integration tests (require external tools)
- `@pytest.mark.architecture` - Architecture layer tests

### Run by Marker
```bash
# Only integration tests
pytest -m integration

# Only architecture tests
pytest -m architecture

# Everything except integration tests
pytest -m "not integration"
```

## Requirements

### For All Tests
- Python 3.9+
- pytest
- feelpp-aptly-publisher package installed

### For Integration and Architecture Tests
- git (for repository operations)
- dpkg-deb (for building test .deb packages)
- aptly (for repository management)

Install test dependencies:
```bash
pip install -e ".[dev]"
```

Or manually:
```bash
pip install pytest pytest-cov
```

## Test Fixtures

### Common Fixtures

- `test_packages` - Creates minimal test .deb packages
- `git_repo` - Creates a temporary git repository with gh-pages branch
- `architecture_packages` - Creates test packages for all architecture layers
- `arch_git_repo` - Creates a git repo specifically for architecture testing

## Architecture Test Scenarios

### 1. Layer Publishing Order
Tests verify correct dependency chain:
1. Base layer (external dependencies)
2. Feel++ layer (depends on base)
3. Applications/KTIRIO layers (depend on feelpp + base)

### 2. Component Preservation
When updating any layer, all other layers are preserved:
- Update base → feelpp, applications, ktirio unchanged
- Update feelpp → base, applications, ktirio unchanged
- Update applications → other layers unchanged

### 3. Multi-Channel Independence
Each channel (stable, testing, pr) can have different component sets:
- Stable: base + feelpp only
- Testing: full architecture
- PR: experimental components

### 4. Migration Scenarios
Tests cover migration from per-package to layer-based components:
- Old components coexist with new ones
- Gradual migration path
- No disruption to existing users

## Example Test Output

```bash
$ pytest tests/test_component_architecture.py -v

tests/test_component_architecture.py::test_publish_base_layer PASSED                      [  8%]
tests/test_component_architecture.py::test_publish_feelpp_layer PASSED                    [ 16%]
tests/test_component_architecture.py::test_publish_applications_layer PASSED              [ 25%]
tests/test_component_architecture.py::test_publish_ktirio_layer PASSED                    [ 33%]
tests/test_component_architecture.py::test_full_architecture_stable PASSED                [ 41%]
tests/test_component_architecture.py::test_full_architecture_all_channels PASSED          [ 50%]
tests/test_component_architecture.py::test_update_base_preserves_others PASSED            [ 58%]
tests/test_component_architecture.py::test_update_feelpp_preserves_others PASSED          [ 66%]
tests/test_component_architecture.py::test_channels_independent_architectures PASSED      [ 75%]
tests/test_component_architecture.py::test_component_name_normalization PASSED            [ 83%]
tests/test_component_architecture.py::test_empty_bootstrap_component PASSED               [ 91%]

============================== 11 passed in 45.23s ==============================
```

## Continuous Integration

These tests are designed to run in CI/CD pipelines:

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Install dependencies
        run: |
          sudo apt-get update
          sudo apt-get install -y git aptly dpkg-dev
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install package
        run: |
          pip install -e ".[dev]"
      
      - name: Run tests
        run: |
          pytest tests/ -v --cov=src/feelpp_aptly_publisher
```

## Debugging Tests

### Enable Debug Logging
```bash
pytest tests/ -v -s --log-cli-level=DEBUG
```

### Keep Test Artifacts
```python
# In test file, use tmp_path without cleanup
def test_debug_publish(tmp_path):
    # Test code...
    print(f"Test artifacts in: {tmp_path}")
    # Add breakpoint or delay to inspect
    import time
    time.sleep(300)  # Keep for 5 minutes
```

### Interactive Debugging
```bash
pytest tests/test_component_architecture.py::test_full_architecture_stable --pdb
```

## Contributing Tests

When adding new features:

1. **Add unit tests** to `test_publisher.py` for new methods/functions
2. **Add integration tests** to `test_integration.py` for workflows
3. **Add architecture tests** to `test_component_architecture.py` for component changes

### Test Naming Convention
- `test_<feature>` - Basic test
- `test_<feature>_<scenario>` - Specific scenario
- `test_<feature>_<scenario>_<channel>` - Channel-specific test

### Test Documentation
Each test should have a clear docstring:
```python
def test_feature():
    """Test that feature X works correctly.
    
    Verifies:
    - Condition A is met
    - Condition B is preserved
    - Result C is produced
    """
```

## Troubleshooting

### "dpkg-deb: command not found"
```bash
sudo apt-get install dpkg-dev
```

### "aptly: command not found"
```bash
# Install aptly
wget https://github.com/aptly-dev/aptly/releases/download/v1.6.2/aptly_1.6.2_linux_amd64.tar.gz
tar xzf aptly_1.6.2_linux_amd64.tar.gz
sudo cp aptly_1.6.2_linux_amd64/aptly /usr/local/bin/
```

### Tests Hang on Git Operations
Ensure git is configured:
```bash
git config --global user.name "Test User"
git config --global user.email "test@example.com"
```

### Permission Errors
Ensure test directory is writable:
```bash
chmod -R u+w tests/
```

## Test Coverage Goals

Current coverage targets:
- Overall: > 80%
- Core publisher logic: > 90%
- CLI: > 70%

Check coverage:
```bash
pytest tests/ --cov=src/feelpp_aptly_publisher --cov-report=term-missing
```
