# Migration to Base Component

## Overview

This document explains how to migrate existing packages from their individual components (`mmg`, `parmmg`) to the unified `base` component in the Feel++ APT repository.

## Question: Can we move mmg and parmmg from stable to base component?

**Answer: YES!** ✅

The `feelpp-aptly-publisher` has sophisticated logic that makes this possible:

### How It Works

1. **Database Recovery**: The publisher automatically recovers the aptly database from existing publications by reading the published pool and metadata.

2. **Component Preservation**: When publishing to a component, the publisher:
   - Checks if a publication already exists
   - Reads existing components from the `Release`/`InRelease` file
   - Downloads existing packages from the pool
   - Republishes ALL components together (old + new)

3. **Multi-Component Support**: The publisher can manage multiple components in a single publication, so:
   - Old components (`mmg`, `parmmg`) continue to work
   - New component (`base`) gets all the packages
   - Users can migrate at their own pace

### Implementation Details

The key code is in `src/feelpp_aptly_publisher/publisher.py`:

```python
# Check if publication exists
release_path = aptly_public / self.channel / "dists" / self.distro / "Release"
if release_path.exists():
    # Parse existing components
    release_content = release_path.read_text()
    for line in release_content.split("\n"):
        if line.startswith("Components:"):
            existing_components = line.split(":", 1)[1].strip().split()
            
    # Import packages from existing components
    for existing_comp in existing_components:
        comp_packages_dir = aptly_public / self.channel / "pool" / existing_comp
        deb_files = glob(str(comp_packages_dir / "**" / "*.deb"), recursive=True)
        # Add to temporary repo and create snapshot
        
    # Publish ALL components together
    components_str = ",".join(all_components)
    aptly_run("publish", "snapshot", "-component", components_str, ...)
```

## Migration Process

### Automated Migration

Use the provided script:

```bash
cd /nvme0/prudhomm/Devel/feelpp.quickfix/apt
./migrate-to-base-component.sh
```

The script will:
1. Download existing mmg and parmmg packages from the stable channel
2. Publish napp to `stable/noble/base` (creates base component)
3. Publish mmg to `stable/noble/base` (adds to base, preserves others)
4. Publish parmmg to `stable/noble/base` (adds to base, preserves others)
5. Verify the migration

### Manual Migration

If you prefer manual control:

```bash
# 1. Ensure napp package is built
cd /nvme0/prudhomm/Devel/napp
./debian/build-deb.sh

# 2. Publish napp to base
./debian/publish-napp.sh stable noble

# 3. Download mmg packages (if not already local)
cd /nvme0/prudhomm/Devel/feelpp.quickfix/third-party/mmg
wget https://feelpp.github.io/apt/stable/pool/mmg/l/libmmg5/libmmg5_5.8.0-1feelpp1_amd64.deb
wget https://feelpp.github.io/apt/stable/pool/mmg/l/libmmg-dev/libmmg-dev_5.8.0-1feelpp1_amd64.deb
wget https://feelpp.github.io/apt/stable/pool/mmg/m/mmg/mmg_5.8.0-1feelpp1_amd64.deb

# 4. Publish mmg to base
./publish-mmg-pypi.sh stable noble

# 5. Download parmmg packages (if not already local)
cd /nvme0/prudhomm/Devel/feelpp.quickfix/third-party/ParMmg
wget https://feelpp.github.io/apt/stable/pool/parmmg/l/libparmmg5/libparmmg5_1.5.0-1_amd64.deb
wget https://feelpp.github.io/apt/stable/pool/parmmg/l/libparmmg-dev/libparmmg-dev_1.5.0-1_amd64.deb
wget https://feelpp.github.io/apt/stable/pool/parmmg/p/parmmg/parmmg_1.5.0-1_amd64.deb

# 6. Publish parmmg to base
./publish-parmmg-pypi.sh stable noble
```

## Result

After migration, the `stable/noble` publication will have multiple components:

```
Components: base ktirio-urban-building mmg parmmg
```

### Base Component Contains:
- `libnapp-dev` (0.3-1feelpp1)
- `libmmg5` (5.8.0-1feelpp1)
- `libmmg-dev` (5.8.0-1feelpp1)
- `mmg` (5.8.0-1feelpp1)
- `libparmmg5` (1.5.0-1)
- `libparmmg-dev` (1.5.0-1)
- `parmmg` (1.5.0-1)

### Old Components (Deprecated):
- `mmg`: Same packages (for backward compatibility)
- `parmmg`: Same packages (for backward compatibility)

### Other Components (Unchanged):
- `ktirio-urban-building`: Preserved as-is

## User Experience

### Before Migration

Users needed multiple APT sources:

```bash
# /etc/apt/sources.list.d/feelpp-mmg.list
deb https://feelpp.github.io/apt/stable noble mmg

# /etc/apt/sources.list.d/feelpp-parmmg.list
deb https://feelpp.github.io/apt/stable noble parmmg
```

### After Migration

Users can use a single APT source:

```bash
# /etc/apt/sources.list.d/feelpp-base.list
deb https://feelpp.github.io/apt/stable noble base
```

### Backward Compatibility

Old configurations continue to work during transition:

```bash
# Still works (deprecated but functional)
deb https://feelpp.github.io/apt/stable noble mmg
deb https://feelpp.github.io/apt/stable noble parmmg
```

## Verification

Check the migration succeeded:

```bash
# Check components list
curl -s https://feelpp.github.io/apt/stable/dists/noble/InRelease | grep "^Components:"

# List packages in base component
curl -s https://feelpp.github.io/apt/stable/dists/noble/base/binary-amd64/Packages | grep "^Package:"

# Test installation
sudo add-apt-repository "deb https://feelpp.github.io/apt/stable noble base"
sudo apt update
apt-cache policy libmmg5  # Should show version from base component
```

## Timeline

### Immediate (Now)
- ✅ Both old and new components coexist
- ✅ Users can start using `base` component
- ✅ Old components remain functional

### Transition Period (3-6 months)
- Update documentation to recommend `base` component
- Announce deprecation of old components
- Help users migrate their APT sources

### Future
- Remove deprecated `mmg` and `parmmg` components
- All users on `base` component

## Benefits

1. **Simplified Management**: Single component for all core dependencies
2. **Better User Experience**: One APT source instead of multiple
3. **Easier Maintenance**: Update once instead of multiple times
4. **Clearer Structure**: base/feelpp/applications hierarchy
5. **Backward Compatible**: No disruption during migration

## Technical Notes

### Why This Works

The `feelpp-aptly-publisher` uses:
- **rsync** to seed aptly from the published repository
- **aptly db recover** to rebuild the database from published metadata
- **Component merging** to publish multiple components in a single InRelease
- **Force overwrite** to allow republishing with different component structure

### Limitations

- Old and new components both consume space in the pool
- Can't remove old components until all users migrate
- GitHub Pages has size limits (recommend < 1GB per repo)

### Monitoring

Track migration progress:

```bash
# Check download counts (if using GitHub API)
curl -s https://api.github.com/repos/feelpp/apt/traffic/popular/paths

# Check which components users are accessing in server logs
```

## Rollback

If migration causes issues:

1. Old components (`mmg`, `parmmg`) remain unchanged
2. Users on old components are unaffected
3. Simply stop recommending `base` component
4. No data loss - all packages preserved

## References

- [COMPONENT_STRUCTURE.md](./COMPONENT_STRUCTURE.md) - Overall component design
- [PUBLISHING_GUIDE.md](./PUBLISHING_GUIDE.md) - How to publish packages
- [src/feelpp_aptly_publisher/publisher.py](./src/feelpp_aptly_publisher/publisher.py) - Implementation details
