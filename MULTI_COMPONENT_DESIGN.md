# Multi-Component Publishing Design

## Overview

The `feelpp-aptly-publisher` now supports publishing multiple components to the same 
distribution/channel while preserving all components in the InRelease file.

## Problem Statement

Previously, each call to `feelpp-apt-publish` would **replace** the entire publication,
resulting in the InRelease file listing only the most recently published component:

```bash
# First publish
feelpp-apt-publish --component ktirio --distro noble --debs ./ktirio-packages/
# Result: InRelease has "Components: ktirio"

# Second publish  
feelpp-apt-publish --component mmg --distro noble --debs ./mmg-packages/
# Result: InRelease has "Components: mmg" (ktirio is GONE!)
```

This is because `aptly publish switch` replaces the publication, not adds to it.

## Solution

The publisher now intelligently detects the current state and chooses the appropriate action:

1. **First Publication**: Use `aptly publish snapshot` to create initial publication
2. **Update Existing Component**: Use `aptly publish switch` to update that component's packages
3. **Add New Component**: Use `aptly publish add` to add a new component alongside existing ones

## Implementation

### Detection Logic

1. Check if publication exists: `aptly publish show <distro> <prefix>`
2. If exists, read the InRelease file to get existing components
3. Determine if the current component is new or existing
4. Choose appropriate aptly command

### Workflow

```python
if publication exists:
    if component in existing_components:
        # Update existing component
        aptly publish switch -component=<comp> <distro> <prefix> <snapshot>
    else:
        # Add new component
        aptly publish add <distro> <prefix> <snapshot> <component>
        aptly publish update <distro> <prefix>
else:
    # First publish
    aptly publish snapshot -distribution=<distro> -component=<comp> <snapshot> <prefix>
```

## Usage Examples

### First Component

```bash
# Publish ktirio-urban-building
feelpp-apt-publish \
    --component ktirio-urban-building \
    --channel stable \
    --distro noble \
    --debs ./ktirio-packages/
    
# Result: InRelease has "Components: ktirio-urban-building"
```

### Add Second Component

```bash
# Add mmg component
feelpp-apt-publish \
    --component mmg \
    --channel stable \
    --distro noble \
    --debs ./mmg-packages/
    
# Result: InRelease has "Components: ktirio-urban-building mmg"
```

### Add Third Component

```bash
# Add parmmg component
feelpp-apt-publish \
    --component parmmg \
    --channel stable \
    --distro noble \
    --debs ./parmmg-packages/
    
# Result: InRelease has "Components: ktirio-urban-building mmg parmmg"
```

### Update Existing Component

```bash
# Update mmg with new version
feelpp-apt-publish \
    --component mmg \
    --channel stable \
    --distro noble \
    --debs ./mmg-packages-updated/
    
# Result: InRelease still has "Components: ktirio-urban-building mmg parmmg"
#         But mmg packages are updated to new version
```

## Verification

After publishing, verify all components are listed:

```bash
# Check InRelease
curl -s https://feelpp.github.io/apt/stable/dists/noble/InRelease | grep Components
# Should show: Components: ktirio-urban-building mmg parmmg

# Verify each component has packages
curl -s https://feelpp.github.io/apt/stable/dists/noble/mmg/binary-amd64/Packages | head
curl -s https://feelpp.github.io/apt/stable/dists/noble/parmmg/binary-amd64/Packages | head
```

## APT Sources Configuration

Users can now use multiple components in a single sources.list entry:

```bash
# Single line with all components
deb [arch=amd64 signed-by=/usr/share/keyrings/feelpp.gpg] \
    https://feelpp.github.io/apt/stable noble ktirio-urban-building mmg parmmg
```

Or separate entries:

```bash
# Separate lines for each component
deb [arch=amd64 signed-by=/usr/share/keyrings/feelpp.gpg] \
    https://feelpp.github.io/apt/stable noble mmg

deb [arch=amd64 signed-by=/usr/share/keyrings/feelpp.gpg] \
    https://feelpp.github.io/apt/stable noble parmmg
```

## Technical Details

### Aptly Commands Used

1. **`aptly publish snapshot`**: Creates a new publication with specified component(s)
   ```bash
   aptly publish snapshot -distribution=noble -component=mmg <snapshot> stable
   ```

2. **`aptly publish switch`**: Updates an existing component's packages
   ```bash
   aptly publish switch -component=mmg noble stable <new-snapshot>
   ```

3. **`aptly publish add`**: Adds a new component to existing publication
   ```bash
   aptly publish add noble stable <snapshot> <component>
   ```

4. **`aptly publish update`**: Regenerates publication metadata (InRelease, Release, etc.)
   ```bash
   aptly publish update noble stable
   ```

### InRelease File Structure

The InRelease file lists all available components:

```
Hash: SHA512

Origin: Feel++
Label: Feel++
Codename: noble
Date: Sat, 12 Oct 2025 12:00:00 UTC
Architectures: amd64
Components: ktirio-urban-building mmg parmmg
Description: Feel++ APT Repository
...
```

APT reads this file first and only looks for package indices in listed components.

## Migration Path

### For Existing Repositories

If you've already published components separately and they're not all in InRelease:

1. **Option A: Re-publish in order**
   ```bash
   # Publish first component (creates publication)
   feelpp-apt-publish --component ktirio-urban-building --distro noble --debs ./ktirio/
   
   # Add remaining components
   feelpp-apt-publish --component mmg --distro noble --debs ./mmg/
   feelpp-apt-publish --component parmmg --distro noble --debs ./parmmg/
   ```

2. **Option B: Manual aptly commands**
   - Clone gh-pages branch
   - Use aptly directly to add missing components
   - Push changes back

## Backward Compatibility

The new behavior is fully backward compatible:

- Single-component publications work exactly as before
- Existing publications are detected and preserved
- Component updates work transparently

## Testing

Run the test suite to verify multi-component behavior:

```bash
cd /nvme0/prudhomm/Devel/feelpp.quickfix/apt
pytest tests/ -v
```

## Future Improvements

1. **Parallel Component Publishing**: Publish multiple components in one command
   ```bash
   feelpp-apt-publish --components mmg,parmmg --distro noble --debs-dir ./packages/
   ```

2. **Component Removal**: Add ability to remove components
   ```bash
   feelpp-apt-publish --remove-component old-project --distro noble
   ```

3. **Component Listing**: Show what components exist in a publication
   ```bash
   feelpp-apt-publish --list-components --distro noble --channel stable
   ```

## References

- Aptly documentation: https://www.aptly.info/doc/aptly/publish/
- APT repository format: https://wiki.debian.org/DebianRepository/Format
- Debian Policy Manual: https://www.debian.org/doc/debian-policy/
