# Republishing Workflow with Multi-Component Support

## Current Status

**Version**: feelpp-aptly-publisher 1.1.0 ✅  
**Branch**: fix/multi-component-inrelease  
**Installed**: Yes (in `.venv`)

## What Changed

The publisher now intelligently preserves ALL components in the InRelease file:

- **Before v1.1.0**: Each publish would **overwrite** the InRelease Components field
- **After v1.1.0**: Each publish **adds to** or **updates** the Components field

## How It Works

When you run `feelpp-apt-publish`:

1. **Checks if publication exists**: `aptly publish show <distro> <prefix>`
2. **Reads InRelease file**: Parses existing components
3. **Decides action**:
   - Component exists → `aptly publish switch` (update packages)
   - Component new → `aptly publish add` (add alongside existing)
   - No publication → `aptly publish snapshot` (first-time)

## Republishing All Components

To fix the current InRelease file and include all three components:

### Step 1: Update Other Publishing Environments

If you have `.venv-publishing` in MMG and ParMmg directories:

```bash
# Update MMG publishing environment
cd /nvme0/prudhomm/Devel/feelpp.quickfix/third-party/mmg
uv pip install -e /nvme0/prudhomm/Devel/feelpp.quickfix/apt --force-reinstall --no-deps --python .venv-publishing/bin/python3

# Update ParMmg publishing environment  
cd /nvme0/prudhomm/Devel/feelpp.quickfix/third-party/ParMmg
uv pip install -e /nvme0/prudhomm/Devel/feelpp.quickfix/apt --force-reinstall --no-deps --python .venv-publishing/bin/python3
```

### Step 2: Republish in Order

The order matters for the first republish! Publish them one by one:

```bash
# 1. First, check what's currently in InRelease
curl -s https://feelpp.github.io/apt/stable/dists/noble/InRelease | grep "Components:"

# 2. If ktirio-urban-building is there, it will be updated
#    If not there, you'll need the packages to add it

# 3. Publish MMG (will be ADDED to existing components)
cd /nvme0/prudhomm/Devel/feelpp.quickfix/third-party/mmg
.venv-publishing/bin/feelpp-apt-publish \
    --component mmg \
    --channel stable \
    --distro noble \
    --debs packages \
    --verbose

# 4. Publish ParMmg (will be ADDED to existing components)
cd /nvme0/prudhomm/Devel/feelpp.quickfix/third-party/ParMmg
.venv-publishing/bin/feelpp-apt-publish \
    --component parmmg \
    --channel stable \
    --distro noble \
    --debs packages \
    --verbose

# 5. Verify all components are listed
curl -s https://feelpp.github.io/apt/stable/dists/noble/InRelease | grep "Components:"
# Expected: Components: ktirio-urban-building mmg parmmg
```

### Step 3: Test Docker Build

Once all components are in InRelease:

```bash
cd /nvme0/prudhomm/Devel/feelpp.quickfix/third-party/mmg
docker build -f Dockerfile.mmg -t feelpp/mmg:latest .
```

This should now work! 🎉

## Expected Output During Republish

### For MMG (new component):
```
INFO: Publication stable/noble exists
INFO: Existing components: ktirio-urban-building
INFO: Adding new component 'mmg' to stable/noble ...
INFO: Successfully added component 'mmg'
INFO: Updating publication metadata to include new component...
INFO: Successfully updated publication metadata
```

### For ParMmg (new component):
```
INFO: Publication stable/noble exists
INFO: Existing components: ktirio-urban-building, mmg
INFO: Adding new component 'parmmg' to stable/noble ...
INFO: Successfully added component 'parmmg'
INFO: Updating publication metadata to include new component...
INFO: Successfully updated publication metadata
```

### Future Updates (existing component):
```
INFO: Publication stable/noble exists
INFO: Existing components: ktirio-urban-building, mmg, parmmg
INFO: Updating existing component 'mmg' in stable/noble ...
INFO: Successfully updated component 'mmg'
```

## Troubleshooting

### If packages are not in the repository yet

Download them from the pool:

```bash
# Create temp directory for packages
mkdir -p /tmp/mmg-packages /tmp/parmmg-packages

# Download MMG packages
cd /tmp/mmg-packages
curl -O https://feelpp.github.io/apt/stable/pool/mmg/m/mmg/mmg_5.8.0-1feelpp1_amd64.deb
curl -O https://feelpp.github.io/apt/stable/pool/mmg/m/mmg/libmmg5_5.8.0-1feelpp1_amd64.deb
curl -O https://feelpp.github.io/apt/stable/pool/mmg/m/mmg/libmmg-dev_5.8.0-1feelpp1_amd64.deb

# Download ParMmg packages
cd /tmp/parmmg-packages
curl -O https://feelpp.github.io/apt/stable/pool/parmmg/p/parmmg/parmmg_1.5.0-1_amd64.deb
curl -O https://feelpp.github.io/apt/stable/pool/parmmg/p/parmmg/libparmmg5_1.5.0-1_amd64.deb
curl -O https://feelpp.github.io/apt/stable/pool/parmmg/p/parmmg/libparmmg-dev_1.5.0-1_amd64.deb

# Then publish using these temp directories
```

### If InRelease still doesn't show all components

Check the verbose output for errors. The publisher will log:
- Whether publication exists
- What components it found
- Which action it's taking (add/switch/snapshot)
- Any errors from aptly commands

## Next Steps

1. **Push the branch**: `git push -u origin fix/multi-component-inrelease`
2. **Create PR**: For review and merging to main
3. **Republish**: Update the live repository
4. **Tag release**: `v1.1.0` after testing
5. **Publish to PyPI**: Make it available for everyone

## Files Changed

- `src/feelpp_aptly_publisher/publisher.py`: Multi-component logic
- `src/feelpp_aptly_publisher/cli.py`: Version bump
- `pyproject.toml`: Version bump to 1.1.0
