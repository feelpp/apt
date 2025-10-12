# Feel++ APT Repository Component Structure

## Overview

The Feel++ APT repository uses a **layer-based component structure** to organize packages logically and make it easier for users to manage dependencies.

## Component Layers

### 1. `base` - Core Dependencies

The `base` component contains third-party libraries and core dependencies required by Feel++ and its applications.

**Packages included:**
- **napp** (`libnapp-dev`) - Named Arguments in C++ header-only library
- **mmg** (`mmg`, `libmmg5`, `libmmg-dev`) - Simplicial remeshing tools
- **parmmg** (`parmmg`, `libparmmg5`, `libparmmg-dev`) - Parallel mmg remeshing

**Purpose:**
- Foundation layer for all Feel++ software
- Stable, well-tested third-party dependencies
- Required by Feel++ core and applications

**Publishing:**
```bash
feelpp-apt-publish --component base --channel stable --distro noble --debs ./packages/
```

### 2. `feelpp` - Feel++ Core

The `feelpp` component contains the Feel++ framework itself.

**Packages included:**
- Feel++ core libraries
- Feel++ development files
- Feel++ tools and utilities

**Purpose:**
- Main Feel++ framework
- Core finite element libraries
- Development tools

**Publishing:**
```bash
feelpp-apt-publish --component feelpp --channel stable --distro noble --debs ./packages/
```

### 3. `applications` - Feel++ Applications

The `applications` component contains Feel++ applications and downstream projects.

**Packages included:**
- **ktirio-urban-building** - Urban building simulation
- **organ-on-chip** - Organ-on-chip simulations
- **feelpp-project** - Feel++ example projects
- Other Feel++ applications

**Purpose:**
- End-user applications built with Feel++
- Domain-specific simulation tools
- Research and production applications

**Publishing:**
```bash
feelpp-apt-publish --component applications --channel stable --distro noble --debs ./packages/
```

## Why This Structure?

### ✅ Advantages

1. **Clear Separation of Concerns**
   - Dependencies vs framework vs applications
   - Easy to understand what each component contains

2. **Flexible Installation**
   - Install only what you need
   - Base dependencies can be shared across multiple systems

3. **Simplified Maintenance**
   - Core dependencies update independently
   - Applications can evolve without affecting the base

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
base/             # Core dependencies
feelpp/           # Feel++ framework
applications/     # Feel++ applications
```
**Benefits:**
- Perfect balance of granularity
- Clear purpose for each layer
- Easy to use and maintain

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

### Installing Applications

For end-user applications:

```bash
# Add all three components
echo 'deb [arch=amd64 signed-by=/usr/share/keyrings/feelpp.gpg] \
    https://feelpp.github.io/apt/stable noble base feelpp applications' | \
    sudo tee /etc/apt/sources.list.d/feelpp-all.list

# Install packages
sudo apt update
sudo apt install ktirio-urban-building
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
feelpp-apt-publish \
    --component base \
    --channel testing \
    --distro noble \
    --debs ./packages/ \
    --verbose

# After testing, publish to stable
feelpp-apt-publish \
    --component base \
    --channel stable \
    --distro noble \
    --debs ./packages/ \
    --verbose
```

### Publishing to `feelpp`

For Feel++ core packages:

```bash
feelpp-apt-publish \
    --component feelpp \
    --channel stable \
    --distro noble \
    --debs ./packages/ \
    --verbose
```

### Publishing to `applications`

For Feel++ applications:

```bash
feelpp-apt-publish \
    --component applications \
    --channel stable \
    --distro noble \
    --debs ./packages/ \
    --verbose
```

### Multi-Component Publishing

The publisher handles multi-component properly. When you publish to the same channel/distro, all components are preserved:

```bash
# Publish base dependencies
feelpp-apt-publish --component base --channel stable --distro noble --debs ./base-packages/

# Add feelpp packages (base is preserved)
feelpp-apt-publish --component feelpp --channel stable --distro noble --debs ./feelpp-packages/

# Add applications (base and feelpp are preserved)
feelpp-apt-publish --component applications --channel stable --distro noble --debs ./app-packages/

# Result: InRelease file lists all three components
# Components: base feelpp applications
```

## Component Migration

### Current Status

**Stable Channel:**
- `ktirio-urban-building` - Will move to `applications`
- `mmg` - Will move to `base`
- `parmmg` - Will move to `base`

**Testing Channel:**
- `feelpp-project` - Will move to `applications`
- `organ-on-chip` - Will move to `applications`
- `ktirio-urban-building` - Will move to `applications`
- `mmg` - Will move to `base`
- `parmmg` - Will move to `base`

### Migration Plan

1. **Publish new structure to testing:**
   ```bash
   # Republish to new components in testing channel
   feelpp-apt-publish --component base --channel testing --distro noble --debs ./base-packages/
   feelpp-apt-publish --component applications --channel testing --distro noble --debs ./app-packages/
   ```

2. **Test in testing channel:**
   - Verify all packages install correctly
   - Test dependency resolution
   - Validate user workflows

3. **Publish to stable:**
   ```bash
   # Republish to new components in stable channel
   feelpp-apt-publish --component base --channel stable --distro noble --debs ./base-packages/
   feelpp-apt-publish --component applications --channel stable --distro noble --debs ./app-packages/
   ```

4. **Update documentation:**
   - Update user guides
   - Update CI/CD pipelines
   - Notify users of changes

## Best Practices

### When to Use Each Component

- **`base`**: Third-party libraries, core dependencies, anything that doesn't change often
- **`feelpp`**: Feel++ framework itself, core libraries
- **`applications`**: End-user applications, domain-specific tools

### Version Management

- Keep `base` packages stable (they're foundations)
- Update `feelpp` with releases
- Update `applications` as needed

### Dependency Management

- `applications` depends on `feelpp` depends on `base`
- All dependencies must be in `base` or `feelpp`
- Applications should not depend on each other

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

### Example 2: User Installing Ktirio

```bash
# Need base, feelpp, and applications
echo 'deb [arch=amd64 signed-by=/usr/share/keyrings/feelpp.gpg] \
    https://feelpp.github.io/apt/stable noble base feelpp applications' | \
    sudo tee /etc/apt/sources.list.d/feelpp.list
sudo apt update
sudo apt install ktirio-urban-building
```

### Example 3: CI/CD Pipeline

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
# Single line with all components
deb [arch=amd64 signed-by=/usr/share/keyrings/feelpp.gpg] \
    https://feelpp.github.io/apt/stable noble base feelpp applications
```

## References

- [Multi-Component Publishing](MULTI_COMPONENT_DESIGN.md)
- [Publishing Guide](PUBLISHING_GUIDE.md)
- [Feel++ Documentation](https://docs.feelpp.org)

## Contact

- Repository: https://github.com/feelpp/apt
- Feel++ Website: https://docs.feelpp.org
- Issues: https://github.com/feelpp/apt/issues
