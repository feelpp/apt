# aptly_publish.py: Script vs PyPI Package Comparison

## Current Workflow (Using Script)

### Project Setup
```bash
# In each project, need to reference the apt repo
cd my-project
git submodule add https://github.com/feelpp/apt.git tools/apt
# OR manually copy the script
cp ../apt/scripts/aptly_publish.py scripts/
```

### Publishing
```bash
# Long command with relative paths
python3 ../../apt/scripts/aptly_publish.py \
    --component my-project \
    --channel stable \
    --distro noble \
    --debs ./packages/ \
    --verbose
```

### CI/CD (GitHub Actions)
```yaml
- name: Checkout apt tools
  run: |
    git clone https://github.com/feelpp/apt.git /tmp/apt

- name: Publish
  run: |
    python3 /tmp/apt/scripts/aptly_publish.py \
      --component ${{ github.event.repository.name }} \
      --channel stable \
      --distro noble \
      --debs ./packages/
```

### Problems
❌ Must clone entire apt repo or use submodules  
❌ Path management is tedious  
❌ Version inconsistency across projects  
❌ Script updates require manual sync  
❌ No version pinning  
❌ Harder to test in isolation  

---

## Future Workflow (Using PyPI Package)

### Project Setup
```bash
# Nothing needed! Just use pip
pip install feelpp-aptly-publisher
```

### Publishing
```bash
# Simple command
feelpp-apt-publish \
    --component my-project \
    --channel stable \
    --distro noble \
    --debs ./packages/
```

### CI/CD (GitHub Actions)
```yaml
- name: Install publisher
  run: pip install feelpp-aptly-publisher

- name: Publish
  run: |
    feelpp-apt-publish \
      --component ${{ github.event.repository.name }} \
      --channel stable \
      --distro noble \
      --debs ./packages/
```

### Benefits
✅ One-line installation  
✅ Clean command name  
✅ Version pinning available (`pip install feelpp-aptly-publisher==1.2.3`)  
✅ Automatic updates (`pip install --upgrade`)  
✅ Standard Python packaging  
✅ Easy to test  

---

## Side-by-Side Comparison

### Installation
| Script | PyPI Package |
|--------|--------------|
| `git clone https://github.com/feelpp/apt.git` | `pip install feelpp-aptly-publisher` |
| ~5 MB download | ~50 KB download |
| Need git access | Public PyPI |

### Usage
| Script | PyPI Package |
|--------|--------------|
| `python3 /path/to/aptly_publish.py ...` | `feelpp-apt-publish ...` |
| Must know path | Available in PATH |
| 35+ characters | 20+ characters |

### Version Management
| Script | PyPI Package |
|--------|--------------|
| Git commit/tag | Semantic versioning |
| `git pull` to update | `pip install --upgrade` |
| No version pinning | `pip install feelpp-aptly-publisher==1.0.0` |
| Hard to rollback | Easy rollback: `pip install feelpp-aptly-publisher==0.9.0` |

### CI/CD Integration
| Script | PyPI Package |
|--------|--------------|
| 3-4 lines to setup | 1 line to install |
| Must manage paths | Auto-configured |
| Clone entire repo | Minimal download |

### Distribution
| Script | PyPI Package |
|--------|--------------|
| GitHub only | PyPI + GitHub |
| Requires git | Works offline (with cache) |
| Hard to discover | Searchable on PyPI |

### Testing
| Script | PyPI Package |
|--------|--------------|
| Test manually | Unit tests + pytest |
| No test framework | CI/CD testing |
| Hard to mock | Easy to test |

### Documentation
| Script | PyPI Package |
|--------|--------------|
| README in repo | PyPI project page |
| `--help` only | `--help` + docs + examples |
| Hard to find | Discoverable |

### Developer Experience
| Script | PyPI Package |
|--------|--------------|
| "Where is the script?" | "pip install it" |
| "Which version?" | "Check `pip list`" |
| "How to update?" | "pip install --upgrade" |
| "Path issues" | "Just works" |

---

## Real-World Example: Publishing MMG

### Current Way
```bash
# Terminal 1: Get the script
cd /tmp
git clone https://github.com/feelpp/apt.git
ls apt/scripts/aptly_publish.py  # Verify it exists

# Terminal 2: Run from project
cd ~/Devel/feelpp.quickfix/third-party/mmg
python3 /tmp/apt/scripts/aptly_publish.py \
    --component mmg \
    --channel stable \
    --distro noble \
    --debs ./packages/ \
    --pages-repo https://github.com/feelpp/apt.git \
    --branch gh-pages \
    --verbose
```

### PyPI Package Way
```bash
# One-time setup (anywhere)
pip install feelpp-aptly-publisher

# Run from project
cd ~/Devel/feelpp.quickfix/third-party/mmg
feelpp-apt-publish \
    --component mmg \
    --channel stable \
    --distro noble \
    --debs ./packages/
```

**Difference**: 
- Script: 4 commands, manage paths, clone repo
- PyPI: 2 commands, clean and simple

---

## Migration Path

### Phase 1: Both Coexist
```bash
# Old way still works
python3 ../../apt/scripts/aptly_publish.py ...

# New way available
feelpp-apt-publish ...
```

### Phase 2: Deprecate Script
```python
# Add to aptly_publish.py
print("WARNING: This script is deprecated.")
print("Please use: pip install feelpp-aptly-publisher")
print("Then run: feelpp-apt-publish ...")
```

### Phase 3: Remove Script
```bash
# Eventually remove scripts/aptly_publish.py
# Keep only reference in README
```

---

## Package Size Comparison

### Current (apt repo)
```
apt/
├── .git/                 ~2 MB
├── scripts/
│   ├── aptly_publish.py  ~12 KB
│   └── aptly.conf        ~1 KB
└── README.md             ~2 KB
Total: ~2+ MB
```

### PyPI Package
```
feelpp-aptly-publisher-1.0.0.tar.gz: ~30 KB
feelpp_aptly_publisher-1.0.0-py3-none-any.whl: ~20 KB
Total: ~50 KB
```

**40x smaller download!**

---

## Conclusion

### Use Script If:
- Quick one-off testing
- Internal tooling only
- No version requirements
- Already have apt repo cloned

### Use PyPI Package If: ✨ (Recommended)
- Multiple projects using it
- CI/CD automation
- Version consistency needed
- Clean developer experience wanted
- Future-proofing infrastructure

**Verdict**: PyPI package is the better long-term solution.

Initial effort: ~1 week  
Long-term savings: Weeks-months of reduced friction  
Developer happiness: 📈📈📈
