# Feel++ APT Repository Component Structure

## Overview

The Feel++ APT repository uses a **layer-based component structure** to organize packages logically and make it easier for users to manage dependencies.

## Component Layers

### 1. `base` - General External Dependencies

The `base` component contains third-party libraries, tools, and external dependencies that are newer or backported versions. These are shared across all Feel++ projects.

**Packages included:**
- **napp** (`libnapp-dev`) - Named Arguments in C++ header-only library
- **mmg** (`mmg`, `libmmg5`, `libmmg-dev`) - Simplicial remeshing tools
- **parmmg** (`parmmg`, `libparmmg5`, `libparmmg-dev`) - Parallel mmg remeshing
- Other backported/newer libraries and tools

**Purpose:**
- Foundation layer for all Feel++ software
- Stable, well-tested third-party dependencies
- Generic dependencies shared across everything

**Publishing:**
```bash
feelpp-aptly-publisher --component base --channel stable --distro noble --debs ./packages/
```

### 2. `feelpp` - Feel++ Core Framework

The `feelpp` component contains the Feel++ framework itself: libraries, headers, toolboxes, and meta-packages.

**Packages included:**
- Feel++ core libraries (`libfeelpp`, `libfeelpp-dev`)
- Feel++ headers and development files
- Feel++ toolboxes (CFD, heat transfer, solid mechanics, etc.)
- Feel++ meta-packages for common workflows
- Feel++ utilities and tools

**Purpose:**
- Main Feel++ finite element framework
- Core mathematical and numerical libraries
- Development environment for Feel++ applications

**Dependencies:** Requires `base` component

**Publishing:**
```bash
feelpp-aptly-publisher --component feelpp --channel stable --distro noble --debs ./packages/
```

### 3. `applications` - Feel++ Applications

The `applications` component contains end-user applications built on top of Feel++.

**Packages included:**
- **organ-on-chip** - Organ-on-chip simulations
- **feelpp-project** - Feel++ example projects
- **sepsis** - Sepsis modeling applications
- Other domain-specific applications using Feel++

**Purpose:**
- End-user simulation applications
- Domain-specific tools built with Feel++
- Research and production applications

**Dependencies:** Requires `feelpp` and `base` components

**Publishing:**
```bash
feelpp-aptly-publisher --component applications --channel stable --distro noble --debs ./packages/
```

### 4. `ktirio` - KTIRIO Domain Stack

The `ktirio` component contains the KTIRIO ecosystem built on Feel++ with additional dependencies from `base`.

**Packages included:**
- **ktirio-urban-building** - Urban building simulation
- **ktirio-geom** - KTIRIO geometry tools
- **ktirio-data** - KTIRIO data management
- **ktirio-*-meta** - KTIRIO meta-packages (optional)
- KTIRIO CLI tools and runners

**Purpose:**
- KTIRIO urban simulation domain stack
- Specialized tools for urban/building simulation
- Integration layer for KTIRIO workflows

**Dependencies:** Requires `feelpp` and `base` components

**Publishing:**
```bash
feelpp-aptly-publisher --component ktirio --channel stable --distro noble --debs ./packages/
```

## Dependency Structure

```
base ─┬─> feelpp ──> applications
      └────────────> ktirio
```

**Rule of thumb:**
- Generic external dependencies → `base`
- Feel++ core framework → `feelpp`
- General applications using Feel++ → `applications`
- KTIRIO ecosystem modules → `ktirio`

**Note:** Both `feelpp` and `ktirio` depend on `base`. The `applications` and `ktirio` components depend on `feelpp` + `base`.

## Why This Structure?

### ✅ Advantages

1. **Clear Separation of Concerns**
   - External dependencies (`base`) vs framework (`feelpp`) vs applications (`applications`, `ktirio`)
   - Easy to understand what each component contains
   - KTIRIO has its own ecosystem separate from general applications

2. **Flexible Installation**
   - Install only what you need
   - Base dependencies can be shared across multiple systems
   - KTIRIO users don't need general applications and vice versa

3. **Simplified Maintenance**
   - Core dependencies update independently
   - Feel++ framework evolves separately from applications
   - KTIRIO domain stack can be updated without affecting other apps
   - Applications can evolve without affecting the base or framework

4. **Better Dependency Management**
   - Clear dependency chain: base → feelpp → {applications, ktirio}
   - No circular dependencies
   - Easier to track what depends on what

4. **Better User Experience**
   - Single component for all core dependencies
   - Clear documentation and examples

5. **Logical Grouping**
   - Related packages grouped together
   - Easy to reason about dependencies

### 📊 Comparison with Other Approaches

#### ❌ Per-Package Components (Previous)
```
mmg/              # One component per package
parmmg/           # Too granular
napp/             # Hard to manage
ktirio-urban-building/  # Each package separate
```
**Issues:**
- Too many components to manage
- Complex APT sources configuration
- Harder for users to discover packages

#### ❌ Single Component
```
main/             # Everything in one component
```
**Issues:**
- No separation of concerns
- Difficult to version independently
- Can't install just dependencies

#### ✅ Layer-Based (Current)
```
base/             # External dependencies
feelpp/           # Feel++ framework
applications/     # General Feel++ applications
ktirio/           # KTIRIO domain stack
```
**Benefits:**
- Perfect balance of granularity
- Clear purpose for each layer
- Easy to use and maintain
- KTIRIO has its own identity

## User Guide

### Installing Core Dependencies Only

For development or building Feel++:

```bash
# Add GPG key
curl -fsSL https://feelpp.github.io/apt/feelpp.gpg | \
    sudo tee /usr/share/keyrings/feelpp.gpg >/dev/null

# Add base component
echo 'deb [arch=amd64 signed-by=/usr/share/keyrings/feelpp.gpg] \
    https://feelpp.github.io/apt/stable noble base' | \
    sudo tee /etc/apt/sources.list.d/feelpp-base.list

# Install packages
sudo apt update
sudo apt install mmg libmmg5 libmmg-dev parmmg libparmmg5 libparmmg-dev libnapp-dev
```

### Installing Feel++

For using Feel++ framework:

```bash
# Add base and feelpp components
echo 'deb [arch=amd64 signed-by=/usr/share/keyrings/feelpp.gpg] \
    https://feelpp.github.io/apt/stable noble base feelpp' | \
    sudo tee /etc/apt/sources.list.d/feelpp.list

# Install packages
sudo apt update
sudo apt install feelpp-core feelpp-dev
```

### Installing Feel++ Applications

For general Feel++ applications (organ-on-chip, feelpp-project, etc.):

```bash
# Add base, feelpp, and applications components
echo 'deb [arch=amd64 signed-by=/usr/share/keyrings/feelpp.gpg] \
    https://feelpp.github.io/apt/stable noble base feelpp applications' | \
    sudo tee /etc/apt/sources.list.d/feelpp-apps.list

# Install packages
sudo apt update
sudo apt install organ-on-chip feelpp-project
```

### Installing KTIRIO

For KTIRIO urban simulation tools:

```bash
# Add base, feelpp, and ktirio components
echo 'deb [arch=amd64 signed-by=/usr/share/keyrings/feelpp.gpg] \
    https://feelpp.github.io/apt/stable noble base feelpp ktirio' | \
    sudo tee /etc/apt/sources.list.d/feelpp-ktirio.list

# Install packages
sudo apt update
sudo apt install ktirio-urban-building ktirio-geom ktirio-data
```

### Using Different Channels

```bash
# Stable channel (production)
https://feelpp.github.io/apt/stable

# Testing channel (pre-release)
https://feelpp.github.io/apt/testing

# PR channel (development)
https://feelpp.github.io/apt/pr
```

## Developer Guide

### Publishing to `base`

For third-party dependencies (napp, mmg, parmmg):

```bash
# Build the package
dpkg-buildpackage -us -uc

# Publish to base component
feelpp-aptly-publisher \
    --component base \
    --channel testing \
    --distro noble \
    --debs ./packages/ \
    --verbose

# After testing, publish to stable
feelpp-aptly-publisher \
    --component base \
    --channel stable \
    --distro noble \
    --debs ./packages/ \
    --verbose
```

### Publishing to `feelpp`

For Feel++ core packages:

```bash
feelpp-aptly-publisher \
    --component feelpp \
    --channel stable \
    --distro noble \
    --debs ./packages/ \
    --verbose
```

### Publishing to `applications`

For general Feel++ applications:

```bash
feelpp-aptly-publisher \
    --component applications \
    --channel stable \
    --distro noble \
    --debs ./packages/ \
    --verbose
```

### Publishing to `ktirio`

For KTIRIO domain stack packages:

```bash
feelpp-aptly-publisher \
    --component ktirio \
    --channel stable \
    --distro noble \
    --debs ./packages/ \
    --verbose
```

### Multi-Component Publishing

The publisher handles multi-component properly. When you publish to the same channel/distro, all components are preserved:

```bash
# Publish base dependencies
feelpp-aptly-publisher --component base --channel stable --distro noble --debs ./base-packages/

# Add feelpp packages (base is preserved)
feelpp-aptly-publisher --component feelpp --channel stable --distro noble --debs ./feelpp-packages/

# Add applications (base and feelpp are preserved)
feelpp-aptly-publisher --component applications --channel stable --distro noble --debs ./app-packages/

# Add ktirio packages (all previous components preserved)
feelpp-aptly-publisher --component ktirio --channel stable --distro noble --debs ./ktirio-packages/

# Result: InRelease file lists all four components
# Components: base feelpp applications ktirio
```

## Component Migration

### Current Status

**Stable Channel:**
- `ktirio-urban-building` - Current individual component → Moving to `ktirio`
- `mmg` - Current individual component → Moving to `base`
- `parmmg` - Current individual component → Moving to `base`

**Testing Channel:**
- `feelpp-project` - Will move to `applications`
- `organ-on-chip` - Will move to `applications`
- `ktirio-urban-building` - Will move to `ktirio`
- `mmg` - Will move to `base`
- `parmmg` - Will move to `base`

### Migration Plan

1. **Publish new structure to testing:**
   ```bash
   # Republish to new components in testing channel
   feelpp-aptly-publisher --component base --channel testing --distro noble --debs ./base-packages/
   feelpp-aptly-publisher --component applications --channel testing --distro noble --debs ./app-packages/
   feelpp-aptly-publisher --component ktirio --channel testing --distro noble --debs ./ktirio-packages/
   ```

2. **Test in testing channel:**
   - Verify all packages install correctly
   - Test dependency resolution
   - Validate user workflows

3. **Publish to stable:**
   ```bash
   # Republish to new components in stable channel
   feelpp-aptly-publisher --component base --channel stable --distro noble --debs ./base-packages/
   feelpp-aptly-publisher --component ktirio --channel stable --distro noble --debs ./ktirio-packages/
   ```

4. **Update documentation:**
   - Update user guides
   - Update CI/CD pipelines
   - Notify users of changes

5. **Transition period:**
   - Old components (mmg, parmmg, ktirio-urban-building) remain available
   - Users gradually migrate to new structure
   - After 3-6 months, deprecate old components

## Best Practices

### When to Use Each Component

- **`base`**: Third-party libraries, external dependencies, backported packages, anything shared across all projects
- **`feelpp`**: Feel++ core framework, libraries, toolboxes, development files
- **`applications`**: General Feel++ applications (organ-on-chip, feelpp-project, sepsis, etc.)
- **`ktirio`**: KTIRIO domain stack (urban-building, geom, data, meta-packages)
- **`feelpp`**: Feel++ framework itself, core libraries
- **`applications`**: End-user applications, domain-specific tools

### Version Management

- Keep `base` packages stable (they're foundations)
- Update `feelpp` with major releases
- Update `applications` and `ktirio` independently as needed

### Dependency Management

- **Dependency chain:** base → feelpp → {applications, ktirio}
- `feelpp` depends on `base`
- `applications` depends on `feelpp` + `base`
- `ktirio` depends on `feelpp` + `base`
- Applications within the same component should not depend on each other
- KTIRIO packages can depend on each other within the `ktirio` component

## Examples

### Example 1: Developer Installing Dependencies

```bash
# Only need base for compiling Feel++ from source
echo 'deb [arch=amd64 signed-by=/usr/share/keyrings/feelpp.gpg] \
    https://feelpp.github.io/apt/stable noble base' | \
    sudo tee /etc/apt/sources.list.d/feelpp-base.list
sudo apt update
sudo apt install mmg libmmg-dev parmmg libparmmg-dev libnapp-dev
```

### Example 2: User Installing KTIRIO

```bash
# Need base, feelpp, and ktirio components
echo 'deb [arch=amd64 signed-by=/usr/share/keyrings/feelpp.gpg] \
    https://feelpp.github.io/apt/stable noble base feelpp ktirio' | \
    sudo tee /etc/apt/sources.list.d/feelpp-ktirio.list
sudo apt update
sudo apt install ktirio-urban-building ktirio-geom ktirio-data
```

### Example 3: User Installing Feel++ Application

```bash
# Need base, feelpp, and applications components
echo 'deb [arch=amd64 signed-by=/usr/share/keyrings/feelpp.gpg] \
    https://feelpp.github.io/apt/stable noble base feelpp applications' | \
    sudo tee /etc/apt/sources.list.d/feelpp-apps.list
sudo apt update
sudo apt install organ-on-chip feelpp-project
```

### Example 4: CI/CD Pipeline

```yaml
- name: Install Feel++ Dependencies
  run: |
    curl -fsSL https://feelpp.github.io/apt/feelpp.gpg | \
        sudo tee /usr/share/keyrings/feelpp.gpg >/dev/null
    echo 'deb [arch=amd64 signed-by=/usr/share/keyrings/feelpp.gpg] \
        https://feelpp.github.io/apt/testing noble base' | \
        sudo tee /etc/apt/sources.list.d/feelpp.list
    sudo apt update
    sudo apt install mmg libmmg-dev parmmg libparmmg-dev
```

## Troubleshooting

### Component Not Found

If you get "Component not found" errors:

1. Check the InRelease file:
   ```bash
   curl -s https://feelpp.github.io/apt/stable/dists/noble/InRelease | grep Components
   ```

2. Verify you're using the correct component name in your sources.list

3. Make sure packages have been published to that component

### Multiple Components

To install from multiple components:

```bash
# Single line with all needed components
deb [arch=amd64 signed-by=/usr/share/keyrings/feelpp.gpg] \
    https://feelpp.github.io/apt/stable noble base feelpp applications ktirio
```

Or separate them:

```bash
# Separate lines (equivalent to above)
deb [arch=amd64 signed-by=/usr/share/keyrings/feelpp.gpg] \
    https://feelpp.github.io/apt/stable noble base feelpp
deb [arch=amd64 signed-by=/usr/share/keyrings/feelpp.gpg] \
    https://feelpp.github.io/apt/stable noble applications ktirio
```

## References

- [Multi-Component Publishing](MULTI_COMPONENT_DESIGN.md)
- [Publishing Guide](PUBLISHING_GUIDE.md)
- [Feel++ Documentation](https://docs.feelpp.org)

## Contact

- Repository: https://github.com/feelpp/apt
- Feel++ Website: https://docs.feelpp.org
- Issues: https://github.com/feelpp/apt/issues
