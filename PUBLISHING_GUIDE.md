# Publishing to PyPI via GitHub Actions

## Overview

We'll use GitHub's **Trusted Publishing** (OpenID Connect) to publish to PyPI. This is more secure than using API tokens.

## Setup Steps

### 1. Configure PyPI Trusted Publishing

1. Go to https://pypi.org/ and log in
2. Go to your account settings
3. Navigate to "Publishing" section
4. Click "Add a new pending publisher"
5. Fill in the details:
   - **PyPI Project Name**: `feelpp-aptly-publisher`
   - **Owner**: `feelpp`
   - **Repository name**: `apt`
   - **Workflow name**: `publish.yml`
   - **Environment name**: `pypi` (optional but recommended)
   
6. Click "Add"

### 2. Create GitHub Environment (Optional but Recommended)

1. Go to https://github.com/feelpp/apt/settings/environments
2. Click "New environment"
3. Name it `pypi`
4. Add protection rules:
   - ✅ Required reviewers (optional)
   - ✅ Wait timer (optional)
   - ✅ Deployment branches: Only default branch
5. Click "Configure environment"

### 3. Create GitHub Release

```bash
# Make sure all changes are committed
cd /nvme0/prudhomm/Devel/feelpp.quickfix/apt
git add .
git commit -m "feat: ready for v1.0.0 release"
git push origin main

# Create and push tag
git tag -a v1.0.0 -m "Release v1.0.0 - Initial release"
git push origin v1.0.0
```

### 4. Create GitHub Release via Web Interface

1. Go to https://github.com/feelpp/apt/releases/new
2. Choose tag: `v1.0.0`
3. Release title: `v1.0.0 - Initial Release`
4. Description:
```markdown
# feelpp-aptly-publisher v1.0.0

First stable release of the Feel++ Aptly Publisher!

## 🚀 Features

- Publish Debian packages to APT repositories via GitHub Pages
- Support for multiple channels (stable, testing, pr)
- GPG signing support
- Zero external Python dependencies
- Comprehensive test suite
- Full CI/CD integration

## 📦 Installation

```bash
pip install feelpp-aptly-publisher
```

## 🎯 Quick Start

```bash
feelpp-apt-publish \
    --component myproject \
    --channel stable \
    --distro noble \
    --debs ./packages/
```

## 📚 Documentation

- [README](https://github.com/feelpp/apt/blob/main/README_PYPI.md)
- [Quick Start](https://github.com/feelpp/apt/blob/main/QUICKSTART.md)
- [Contributing](https://github.com/feelpp/apt/blob/main/CONTRIBUTING.md)

## ✅ Quality

- Python 3.8-3.12 compatible
- 10/10 tests passing
- Black, Flake8, Mypy verified
- Built with uv

**Full Changelog**: https://github.com/feelpp/apt/commits/v1.0.0
```

5. Click "Publish release"

### 5. Watch the Action

1. Go to https://github.com/feelpp/apt/actions
2. Watch the "Publish to PyPI" workflow run
3. It should:
   - Build the package
   - Validate with twine
   - Publish to PyPI using trusted publishing
   - Complete successfully ✅

## Alternative: Manual Trigger

If you want to test with Test PyPI first:

1. Go to https://github.com/feelpp/apt/actions/workflows/publish.yml
2. Click "Run workflow"
3. Select branch: `main`
4. Repository: `testpypi`
5. Click "Run workflow"

This will publish to Test PyPI where you can test installation:
```bash
pip install --index-url https://test.pypi.org/simple/ feelpp-aptly-publisher
```

## Verification After Publishing

Once published, verify:

```bash
# Search on PyPI
pip search feelpp-aptly-publisher

# Install
pip install feelpp-aptly-publisher

# Test
feelpp-apt-publish --version
feelpp-apt-publish --help
```

## Troubleshooting

### "Trusted publisher configured with an incorrect workflow filename"
- Make sure workflow file is named exactly `publish.yml`
- Check it's in `.github/workflows/`

### "Trusted publisher not configured"
- Complete Step 1 above on PyPI.org
- Wait a few minutes for propagation

### "Permission denied"
- Make sure the workflow has `id-token: write` permission
- Check our `.github/workflows/publish.yml` has this

### "Package name already exists"
- The name might be taken
- Choose alternative name or contact current owner

## What Happens Next

After successful publication:

1. **Package appears on PyPI**: https://pypi.org/project/feelpp-aptly-publisher/
2. **Anyone can install**: `pip install feelpp-aptly-publisher`
3. **Update MMG and other projects** to use it
4. **Monitor downloads**: Check PyPI stats

## Future Releases

For subsequent releases:

1. Update version in `pyproject.toml` and `src/feelpp_aptly_publisher/__init__.py`
2. Commit changes
3. Create new tag: `git tag v1.1.0`
4. Push: `git push origin v1.1.0`
5. Create GitHub release
6. CI publishes automatically

**No manual PyPI steps needed after initial setup!** 🎉
