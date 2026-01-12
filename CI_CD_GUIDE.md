# CI/CD Guide for Feel++ Debian Packages

This guide explains how to set up automated building and publishing of Debian packages to the Feel++ APT repository.

## Overview

The CI/CD system consists of:
1. **Reusable workflow** (`debian-publish-reusable.yml`) in the `feelpp/apt` repository
2. **GitHub Action** (`setup-aptly`) for installing aptly and publishing packages
3. **Package-specific workflows** in each repository (napp, mmg, parmmg, etc.)

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Package Repository (napp, mmg, parmmg, etc.)               │
│                                                             │
│  .github/workflows/debian-package.yml                       │
│    └─> Calls reusable workflow                             │
│                                                             │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ uses: feelpp/apt/.github/workflows/
                       │       debian-publish-reusable.yml@main
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  feelpp/apt Repository                                      │
│                                                             │
│  .github/workflows/debian-publish-reusable.yml              │
│    ├─> Build Debian package                                │
│    └─> Publish to appropriate channel                      │
│                                                             │
│  .github/actions/setup-aptly/                               │
│    └─> Install aptly + feelpp-aptly-publisher              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Publishing Logic

The system automatically determines the channel based on the trigger:

| Trigger | Channel | Use Case |
|---------|---------|----------|
| `release` (published) | `stable` | Production releases |
| `push` to main/master | `testing` | Development builds |
| `pull_request` | `pr` | PR preview builds |

## Component Mapping

Packages are published to appropriate components:

| Package | Component | Description |
|---------|-----------|-------------|
| napp | `base` | External dependencies |
| mmg | `base` | External dependencies |
| parmmg | `base` | External dependencies |
| feelpp-* | `feelpp` | Feel++ core libraries |
| feelpp-project | `applications` | General applications |
| organ-on-chip | `applications` | General applications |
| ktirio-* | `ktirio` | KTIRIO stack |

## Setting Up CI/CD for a Package

### 1. Simple Workflow (Recommended)

For most packages, create `.github/workflows/debian-package.yml`:

```yaml
name: Debian Package CI/CD

on:
  push:
    branches: [ master ]
  pull_request:
    branches: [ master ]
  release:
    types: [published]

jobs:
  # Optional: Run tests first
  test:
    runs-on: ubuntu-24.04
    steps:
    - uses: actions/checkout@v4
    - name: Build and test
      run: |
        cmake -B build
        cmake --build build
        ctest --test-dir build

  # Build and publish
  debian:
    needs: test  # Optional: remove if no tests
    uses: feelpp/apt/.github/workflows/debian-publish-reusable.yml@main
    with:
      component: base  # or feelpp, applications, ktirio
      distribution: noble
```

### 2. Custom Build Script

If you have a custom build script:

```yaml
  debian:
    uses: feelpp/apt/.github/workflows/debian-publish-reusable.yml@main
    with:
      component: base
      distribution: noble
      build-script: debian/build-deb.sh
      package-pattern: '../*.deb'
```

### 3. Additional Dependencies

If you need extra build dependencies:

```yaml
  debian:
    uses: feelpp/apt/.github/workflows/debian-publish-reusable.yml@main
    with:
      component: base
      distribution: noble
      build-dependencies: 'libscotch-dev libvtk9-dev'
```

## Examples

### NAPP (Header-only Library)

```yaml
name: Debian Package CI/CD

on:
  push:
    branches: [ master ]
  pull_request:
    branches: [ master ]
  release:
    types: [published]

jobs:
  test:
    strategy:
      matrix:
        os: [ubuntu-22.04, ubuntu-24.04]
        compiler: [g++, clang++]
    runs-on: ${{ matrix.os }}
    steps:
    - uses: actions/checkout@v4
    - run: cmake -B build -DCMAKE_CXX_COMPILER=${{ matrix.compiler }}
    - run: cmake --build build
    - run: ctest --test-dir build

  debian:
    needs: test
    uses: feelpp/apt/.github/workflows/debian-publish-reusable.yml@main
    with:
      component: base
      distribution: noble
```

### MMG (Compiled Library with Dependencies)

```yaml
name: Debian Package CI/CD

on:
  push:
    branches: [ master ]
  pull_request:
    branches: [ master ]
  release:
    types: [published]

jobs:
  # Complex test matrix (optional)
  test:
    strategy:
      matrix:
        os: [ubuntu-22.04, ubuntu-24.04, macos-14]
        scotch: [on, off]
        vtk: [on, off]
    runs-on: ${{ matrix.os }}
    steps:
    - uses: actions/checkout@v4
    - name: Install dependencies
      if: runner.os == 'Linux'
      run: |
        sudo apt-get update
        sudo apt-get install -y libscotch-dev libvtk9-dev
    - run: cmake -B build -DUSE_SCOTCH=${{ matrix.scotch }}
    - run: cmake --build build
    - run: ctest --test-dir build

  # Simple Debian packaging
  debian:
    needs: test
    uses: feelpp/apt/.github/workflows/debian-publish-reusable.yml@main
    with:
      component: base
      distribution: noble
      build-dependencies: 'libscotch-dev gfortran'
```

### Feel++ Applications

```yaml
jobs:
  debian:
    uses: feelpp/apt/.github/workflows/debian-publish-reusable.yml@main
    with:
      component: applications  # Not base!
      distribution: noble
      build-dependencies: 'libfeelpp-dev libboost-all-dev'
```

### KTIRIO Packages

```yaml
jobs:
  debian:
    uses: feelpp/apt/.github/workflows/debian-publish-reusable.yml@main
    with:
      component: ktirio  # Separate KTIRIO stack
      distribution: noble
```

## Manual Publishing

You can also use the action directly for more control:

```yaml
jobs:
  publish:
    runs-on: ubuntu-24.04
    steps:
    - uses: actions/checkout@v4
    
    - name: Build package
      run: dpkg-buildpackage -us -uc
    
    - name: Checkout APT repo
      uses: actions/checkout@v4
      with:
        repository: feelpp/apt
        ref: main
        path: apt-repo
    
    - name: Publish
      uses: feelpp/setup-aptly@v1
      with:
        publish: true
        component: base
        channel: testing
        distribution: noble
        debs-path: ..
        apt-repo-path: apt-repo
```

## Testing the CI/CD

### Test on Pull Request
1. Create a PR → automatically publishes to `pr` channel
2. Check: https://feelpp.github.io/apt/pr/dists/noble/

### Test on Push to Main
1. Push to main/master → publishes to `testing` channel
2. Check: https://feelpp.github.io/apt/testing/dists/noble/

### Release to Stable
1. Create GitHub release → publishes to `stable` channel
2. Check: https://feelpp.github.io/apt/stable/dists/noble/

## Troubleshooting

### Workflow Not Found
If you get "Unable to find reusable workflow":
- Ensure `feelpp/apt` has the workflow file
- Check the branch reference (`@main`)
- Verify repository permissions

### Package Not Published
1. Check if the build step succeeded
2. Verify artifact was uploaded
3. Check publish step logs
4. Ensure GITHUB_TOKEN has write permissions

### Wrong Component
Make sure the `component` input matches your package type:
- External deps → `base`
- Feel++ core → `feelpp`
- Apps → `applications`
- KTIRIO → `ktirio`

## Benefits

✅ **Reduced Boilerplate**: Single reusable workflow for all packages
✅ **Consistent Publishing**: Same logic for all repositories
✅ **Easy Maintenance**: Update once in `feelpp/apt`, applies everywhere
✅ **Automatic Channels**: No manual channel selection needed
✅ **Testing Support**: Optional test jobs before building
✅ **Matrix Testing**: Full test coverage with minimal config

## Migration Checklist

- [ ] Push reusable workflow to `feelpp/apt`
- [ ] Publish `setup-aptly` action
- [ ] Update NAPP workflow
- [ ] Update MMG workflow
- [ ] Update ParMmg workflow
- [ ] Test on PR
- [ ] Test on push to main
- [ ] Test on release
- [ ] Update documentation

## Related Files

- **Reusable Workflow**: `/nvme0/prudhomm/Devel/feelpp.quickfix/apt/.github/workflows/debian-publish-reusable.yml`
- **Setup Action**: `/nvme0/prudhomm/Devel/feelpp.quickfix/setup-aptly/action.yml`
- **NAPP Example**: `/nvme0/prudhomm/Devel/napp/.github/workflows/debian-package.yml`
- **Publisher Tool**: `/nvme0/prudhomm/Devel/feelpp.quickfix/apt/src/feelpp_aptly_publisher/`
