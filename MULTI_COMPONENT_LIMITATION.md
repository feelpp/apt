# Multi-Component Publishing Limitation

## Current Status

**Version**: 1.1.0  
**Branch**: fix/multi-component-inrelease  
**Status**: Partially implemented

## Problem

Aptly does NOT have a built-in command to "add a component" to an existing publication.

The available commands are:
- `aptly publish snapshot` - Creates a NEW publication (overwrites existing)
- `aptly publish switch` - Updates ONE component's packages (if component already exists)
- `aptly publish drop` - Removes entire publication

There is **NO** `aptly publish add` command.

## What Was Implemented

✅ Detection of existing publications by reading InRelease file  
✅ Detection of existing components  
✅ Logic to use `publish switch` when updating existing components  
✅ Force-overwrite flag to handle existing pool files  
✅ Database recovery from published repository  

❌ Actual adding of new components to existing publications

## Why It's Hard

To publish multiple components together, you need:

1. **Snapshots for ALL components** (not just the new one)
2. **Single publish command** with all snapshots:
   ```bash
   aptly publish snapshot \
     -distribution=noble \
     -component=comp1,comp2,comp3 \
     snapshot1 snapshot2 snapshot3 \
     stable
   ```

When you call `feelpp-apt-publish` sequentially:
- First call: Creates publication with component1
- Second call: Overwrites publication with component2 only
- Third call: Overwrites publication with component3 only

**Result**: Only the LAST component remains in InRelease.

## Workarounds

### Workaround 1: Use Docker with Local Packages

This bypasses the APT repository entirely:

```bash
cd /nvme0/prudhomm/Devel/feelpp.quickfix/third-party/mmg
docker build -f Dockerfile.mmg.local -t feelpp/mmg:local .
```

✅ **This works perfectly!**

### Workaround 2: Manual Aptly Commands

Create a script that:
1. Clones gh-pages
2. Creates snapshots for ALL components
3. Publishes them together

Example:
```bash
# Create snapshots
aptly snapshot create mmg-snap from repo mmg-repo
aptly snapshot create parmmg-snap from repo parmmg-repo  
aptly snapshot create ktirio-snap from repo ktirio-repo

# Drop existing publication
aptly publish drop noble stable

# Publish all together
aptly publish snapshot \
  -distribution=noble \
  -component=mmg,parmmg,ktirio-urban-building \
  -skip-signing \
  mmg-snap parmmg-snap ktirio-snap \
  stable
```

### Workaround 3: Republish from Scratch

Download all packages and publish them in a SINGLE aptly session:

```bash
# This would require extending feelpp-apt-publish to accept multiple components
feelpp-apt-publish \
  --components mmg,parmmg,ktirio-urban-building \
  --debs-mmg /path/to/mmg/packages \
  --debs-parmmg /path/to/parmmg/packages \
  --debs-ktirio /path/to/ktirio/packages \
  --channel stable \
  --distro noble
```

**Note**: This requires implementing multi-component support in the tool.

## Proper Solution

Refactor `feelpp-aptly-publisher` to support true multi-component publishing:

### New CLI Interface

```bash
# Publish multiple components at once
feelpp-apt-publish \
  --multi-component mmg=/path/to/mmg,parmmg=/path/to/parmmg \
  --channel stable \
  --distro noble

# Or with a config file
feelpp-apt-publish \
  --components-file components.yaml \
  --channel stable \
  --distro noble
```

### Implementation Steps

1. **Accept multiple components**: Extend CLI to accept component:path pairs
2. **Create multiple snapshots**: One for each component
3. **Single publish command**: Use `aptly publish snapshot` with all components
4. **Handle updates**: When some components exist and some are new
5. **Preserve existing**: Download and republish components not being updated

### Estimated Effort

- **Design**: 2 hours
- **Implementation**: 8 hours  
- **Testing**: 4 hours
- **Documentation**: 2 hours
- **Total**: ~2 days

## Current Recommendation

**For MMG/ParMmg Docker images**: Use `Dockerfile.mmg.local` ✅

**For APT repository**: Manual fix using direct aptly commands or wait for proper multi-component support in v2.0.0

## Files Modified

- `src/feelpp_aptly_publisher/publisher.py`:
  - Added InRelease file reading
  - Added existing component detection
  - Added force-overwrite flag
  - Added database recovery
  - Added logic to use switch vs snapshot

- `pyproject.toml`: Version 1.0.0 → 1.1.0
- `src/feelpp_aptly_publisher/cli.py`: Version string updated

## Testing Done

✅ Docker image builds from local packages  
✅ Tool detects existing publications  
✅ Tool detects existing components  
✅ Tool uses switch for existing components  
❌ Adding new components (aptly limitation)

## Next Steps

1. **Short term**: Document workarounds clearly
2. **Medium term**: Create manual republish script using direct aptly commands
3. **Long term**: Implement proper multi-component support in v2.0.0

## Related Issues

- Aptly issue: https://github.com/aptly-dev/aptly/issues/...
- APT multi-component specification: https://wiki.debian.org/DebianRepository/Format

## Conclusion

The current implementation (v1.1.0) provides:
- ✅ Better detection of existing publications
- ✅ Smarter decision making (switch vs snapshot)
- ✅ Force-overwrite to handle conflicts
- ❌ **Cannot truly add components due to aptly limitations**

**Recommendation**: Use Docker with local packages until v2.0.0 implements proper multi-component support.
