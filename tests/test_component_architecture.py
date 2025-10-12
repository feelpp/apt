"""Tests for the 4-layer component architecture.

This module tests the layer-based component structure:
- base: External dependencies
- feelpp: Feel++ core framework
- applications: General Feel++ applications
- ktirio: KTIRIO domain stack

Tests verify:
1. Publishing to each component layer
2. Dependency chain: base → feelpp → {applications, ktirio}
3. Multi-component coexistence
4. Component preservation during updates
5. All three channels (stable, testing, pr)
"""

import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

from feelpp_aptly_publisher import AptlyPublisher


@pytest.fixture
def architecture_packages(tmp_path):
    """Create test packages for each architecture layer."""
    packages = {}

    # Base layer packages (external dependencies)
    base_packages = ["mmg", "parmmg", "libnapp-dev"]
    packages["base"] = []

    for pkg_name in base_packages:
        pkg_dir = tmp_path / f"base_{pkg_name}"
        debian_dir = pkg_dir / "DEBIAN"
        debian_dir.mkdir(parents=True)

        control = debian_dir / "control"
        control.write_text(
            f"""Package: {pkg_name}
Version: 1.0.0-1feelpp1
Section: devel
Priority: optional
Architecture: amd64
Maintainer: Feel++ Team <feelpp@feelpp.org>
Description: Test package {pkg_name} (base layer)
 External dependency for Feel++ ecosystem.
"""
        )

        usr_lib = pkg_dir / "usr" / "lib"
        usr_lib.mkdir(parents=True)
        (usr_lib / f"lib{pkg_name}.so").write_text("# Library stub\n")

        deb_file = tmp_path / "base_debs" / f"{pkg_name}_1.0.0-1feelpp1_amd64.deb"
        deb_file.parent.mkdir(exist_ok=True)
        subprocess.run(["dpkg-deb", "--build", str(pkg_dir), str(deb_file)], check=True, capture_output=True)
        packages["base"].append(deb_file)

    # Feel++ layer packages (core framework)
    feelpp_packages = ["libfeelpp", "libfeelpp-dev", "feelpp-toolbox-cfd"]
    packages["feelpp"] = []

    for pkg_name in feelpp_packages:
        pkg_dir = tmp_path / f"feelpp_{pkg_name}"
        debian_dir = pkg_dir / "DEBIAN"
        debian_dir.mkdir(parents=True)

        # feelpp depends on base
        depends = "mmg, parmmg, libnapp-dev"
        control = debian_dir / "control"
        control.write_text(
            f"""Package: {pkg_name}
Version: 0.110.0-1
Section: science
Priority: optional
Architecture: amd64
Depends: {depends}
Maintainer: Feel++ Team <feelpp@feelpp.org>
Description: Test package {pkg_name} (feelpp layer)
 Feel++ core framework package.
"""
        )

        usr_lib = pkg_dir / "usr" / "lib" / "feelpp"
        usr_lib.mkdir(parents=True)
        (usr_lib / f"{pkg_name}.so").write_text("# Feel++ library\n")

        deb_file = tmp_path / "feelpp_debs" / f"{pkg_name}_0.110.0-1_amd64.deb"
        deb_file.parent.mkdir(exist_ok=True)
        subprocess.run(["dpkg-deb", "--build", str(pkg_dir), str(deb_file)], check=True, capture_output=True)
        packages["feelpp"].append(deb_file)

    # Applications layer packages (general Feel++ apps)
    app_packages = ["organ-on-chip", "feelpp-project", "sepsis-model"]
    packages["applications"] = []

    for pkg_name in app_packages:
        pkg_dir = tmp_path / f"app_{pkg_name}"
        debian_dir = pkg_dir / "DEBIAN"
        debian_dir.mkdir(parents=True)

        # apps depend on feelpp
        depends = "libfeelpp, libfeelpp-dev"
        control = debian_dir / "control"
        control.write_text(
            f"""Package: {pkg_name}
Version: 1.0.0-1
Section: science
Priority: optional
Architecture: amd64
Depends: {depends}
Maintainer: Feel++ Team <feelpp@feelpp.org>
Description: Test package {pkg_name} (applications layer)
 Feel++ application package.
"""
        )

        usr_bin = pkg_dir / "usr" / "bin"
        usr_bin.mkdir(parents=True)
        (usr_bin / pkg_name).write_text(f"#!/bin/bash\necho 'Running {pkg_name}'\n")
        (usr_bin / pkg_name).chmod(0o755)

        deb_file = tmp_path / "app_debs" / f"{pkg_name}_1.0.0-1_amd64.deb"
        deb_file.parent.mkdir(exist_ok=True)
        subprocess.run(["dpkg-deb", "--build", str(pkg_dir), str(deb_file)], check=True, capture_output=True)
        packages["applications"].append(deb_file)

    # KTIRIO layer packages (domain stack)
    ktirio_packages = ["ktirio-urban-building", "ktirio-geom", "ktirio-data"]
    packages["ktirio"] = []

    for pkg_name in ktirio_packages:
        pkg_dir = tmp_path / f"ktirio_{pkg_name}"
        debian_dir = pkg_dir / "DEBIAN"
        debian_dir.mkdir(parents=True)

        # ktirio depends on feelpp
        depends = "libfeelpp, libfeelpp-dev"
        control = debian_dir / "control"
        control.write_text(
            f"""Package: {pkg_name}
Version: 2.0.0-1
Section: science
Priority: optional
Architecture: amd64
Depends: {depends}
Maintainer: KTIRIO Team <ktirio@feelpp.org>
Description: Test package {pkg_name} (ktirio layer)
 KTIRIO domain stack package.
"""
        )

        usr_bin = pkg_dir / "usr" / "bin"
        usr_bin.mkdir(parents=True)
        (usr_bin / pkg_name).write_text(f"#!/bin/bash\necho 'Running {pkg_name}'\n")
        (usr_bin / pkg_name).chmod(0o755)

        deb_file = tmp_path / "ktirio_debs" / f"{pkg_name}_2.0.0-1_amd64.deb"
        deb_file.parent.mkdir(exist_ok=True)
        subprocess.run(["dpkg-deb", "--build", str(pkg_dir), str(deb_file)], check=True, capture_output=True)
        packages["ktirio"].append(deb_file)

    return packages


@pytest.fixture
def arch_git_repo(tmp_path):
    """Create a temporary git repository for architecture testing."""
    bare_repo = tmp_path / "test-feelpp-apt.git"
    bare_repo.mkdir()
    subprocess.run(["git", "init", "--bare"], cwd=bare_repo, check=True, capture_output=True)

    work_repo = tmp_path / "test-feelpp-apt"
    subprocess.run(["git", "clone", str(bare_repo), str(work_repo)], check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=work_repo, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=work_repo, check=True, capture_output=True)

    subprocess.run(["git", "checkout", "-b", "gh-pages"], cwd=work_repo, check=True, capture_output=True)
    readme = work_repo / "README.md"
    readme.write_text("# Feel++ APT Repository Test\n")
    subprocess.run(["git", "add", "README.md"], cwd=work_repo, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=work_repo, check=True, capture_output=True)
    subprocess.run(["git", "push", "origin", "gh-pages"], cwd=work_repo, check=True, capture_output=True)

    return bare_repo


def verify_architecture(bare_repo, channel, distro, expected_components):
    """Verify the component architecture in a publication."""
    with tempfile.TemporaryDirectory() as tmpdir:
        check_dir = Path(tmpdir) / "check"
        subprocess.run(
            ["git", "clone", "-b", "gh-pages", str(bare_repo), str(check_dir)],
            check=True,
            capture_output=True,
        )

        release_file = check_dir / channel / "dists" / distro / "Release"
        assert release_file.exists(), f"Release file not found: {release_file}"

        release_content = release_file.read_text()
        found_components = None
        for line in release_content.split("\n"):
            if line.startswith("Components:"):
                found_components = set(line.split(":", 1)[1].strip().split())
                break

        assert found_components is not None, "Components line not found"
        assert found_components == set(expected_components), (
            f"Component mismatch: expected {set(expected_components)}, " f"got {found_components}"
        )

        # Verify each component has packages
        for component in expected_components:
            packages_file = check_dir / channel / "dists" / distro / component / "binary-amd64" / "Packages"
            assert packages_file.exists(), f"Packages file missing for {component}"
            assert packages_file.stat().st_size > 0, f"Packages file empty for {component}"


@pytest.mark.architecture
def test_publish_base_layer(architecture_packages, arch_git_repo):
    """Test publishing base layer (external dependencies)."""
    base_dir = architecture_packages["base"][0].parent

    publisher = AptlyPublisher(
        component="base",
        distro="noble",
        channel="stable",
        pages_repo=str(arch_git_repo),
        branch="gh-pages",
        sign=False,
    )
    publisher.publish(debs_dir=str(base_dir))

    verify_architecture(arch_git_repo, "stable", "noble", ["base"])


@pytest.mark.architecture
def test_publish_feelpp_layer(architecture_packages, arch_git_repo):
    """Test publishing Feel++ layer on top of base."""
    # Publish base first
    base_dir = architecture_packages["base"][0].parent
    publisher_base = AptlyPublisher(
        component="base",
        distro="noble",
        channel="stable",
        pages_repo=str(arch_git_repo),
        branch="gh-pages",
        sign=False,
    )
    publisher_base.publish(debs_dir=str(base_dir))

    # Publish feelpp (should preserve base)
    feelpp_dir = architecture_packages["feelpp"][0].parent
    publisher_feelpp = AptlyPublisher(
        component="feelpp",
        distro="noble",
        channel="stable",
        pages_repo=str(arch_git_repo),
        branch="gh-pages",
        sign=False,
    )
    publisher_feelpp.publish(debs_dir=str(feelpp_dir))

    verify_architecture(arch_git_repo, "stable", "noble", ["base", "feelpp"])


@pytest.mark.architecture
def test_publish_applications_layer(architecture_packages, arch_git_repo):
    """Test publishing applications layer on top of base and feelpp."""
    # Publish base
    base_dir = architecture_packages["base"][0].parent
    publisher_base = AptlyPublisher(
        component="base", distro="noble", channel="stable", pages_repo=str(arch_git_repo), branch="gh-pages", sign=False
    )
    publisher_base.publish(debs_dir=str(base_dir))

    # Publish feelpp
    feelpp_dir = architecture_packages["feelpp"][0].parent
    publisher_feelpp = AptlyPublisher(
        component="feelpp",
        distro="noble",
        channel="stable",
        pages_repo=str(arch_git_repo),
        branch="gh-pages",
        sign=False,
    )
    publisher_feelpp.publish(debs_dir=str(feelpp_dir))

    # Publish applications (should preserve base and feelpp)
    app_dir = architecture_packages["applications"][0].parent
    publisher_app = AptlyPublisher(
        component="applications",
        distro="noble",
        channel="stable",
        pages_repo=str(arch_git_repo),
        branch="gh-pages",
        sign=False,
    )
    publisher_app.publish(debs_dir=str(app_dir))

    verify_architecture(arch_git_repo, "stable", "noble", ["base", "feelpp", "applications"])


@pytest.mark.architecture
def test_publish_ktirio_layer(architecture_packages, arch_git_repo):
    """Test publishing KTIRIO layer on top of base and feelpp."""
    # Publish base
    base_dir = architecture_packages["base"][0].parent
    publisher_base = AptlyPublisher(
        component="base", distro="noble", channel="stable", pages_repo=str(arch_git_repo), branch="gh-pages", sign=False
    )
    publisher_base.publish(debs_dir=str(base_dir))

    # Publish feelpp
    feelpp_dir = architecture_packages["feelpp"][0].parent
    publisher_feelpp = AptlyPublisher(
        component="feelpp",
        distro="noble",
        channel="stable",
        pages_repo=str(arch_git_repo),
        branch="gh-pages",
        sign=False,
    )
    publisher_feelpp.publish(debs_dir=str(feelpp_dir))

    # Publish ktirio (should preserve base and feelpp)
    ktirio_dir = architecture_packages["ktirio"][0].parent
    publisher_ktirio = AptlyPublisher(
        component="ktirio",
        distro="noble",
        channel="stable",
        pages_repo=str(arch_git_repo),
        branch="gh-pages",
        sign=False,
    )
    publisher_ktirio.publish(debs_dir=str(ktirio_dir))

    verify_architecture(arch_git_repo, "stable", "noble", ["base", "feelpp", "ktirio"])


@pytest.mark.architecture
def test_full_architecture_stable(architecture_packages, arch_git_repo):
    """Test publishing all four layers to stable channel."""
    # Publish in dependency order: base → feelpp → {applications, ktirio}

    # 1. Base layer
    base_dir = architecture_packages["base"][0].parent
    publisher_base = AptlyPublisher(
        component="base", distro="noble", channel="stable", pages_repo=str(arch_git_repo), branch="gh-pages", sign=False
    )
    publisher_base.publish(debs_dir=str(base_dir))
    verify_architecture(arch_git_repo, "stable", "noble", ["base"])

    # 2. Feel++ layer
    feelpp_dir = architecture_packages["feelpp"][0].parent
    publisher_feelpp = AptlyPublisher(
        component="feelpp",
        distro="noble",
        channel="stable",
        pages_repo=str(arch_git_repo),
        branch="gh-pages",
        sign=False,
    )
    publisher_feelpp.publish(debs_dir=str(feelpp_dir))
    verify_architecture(arch_git_repo, "stable", "noble", ["base", "feelpp"])

    # 3. Applications layer
    app_dir = architecture_packages["applications"][0].parent
    publisher_app = AptlyPublisher(
        component="applications",
        distro="noble",
        channel="stable",
        pages_repo=str(arch_git_repo),
        branch="gh-pages",
        sign=False,
    )
    publisher_app.publish(debs_dir=str(app_dir))
    verify_architecture(arch_git_repo, "stable", "noble", ["base", "feelpp", "applications"])

    # 4. KTIRIO layer
    ktirio_dir = architecture_packages["ktirio"][0].parent
    publisher_ktirio = AptlyPublisher(
        component="ktirio",
        distro="noble",
        channel="stable",
        pages_repo=str(arch_git_repo),
        branch="gh-pages",
        sign=False,
    )
    publisher_ktirio.publish(debs_dir=str(ktirio_dir))

    # Verify all four components coexist
    verify_architecture(arch_git_repo, "stable", "noble", ["base", "feelpp", "applications", "ktirio"])


@pytest.mark.architecture
def test_full_architecture_all_channels(architecture_packages, arch_git_repo):
    """Test publishing full architecture to all three channels."""
    for channel in ["stable", "testing", "pr"]:
        # Publish all four layers to this channel
        for component_name in ["base", "feelpp", "applications", "ktirio"]:
            debs_dir = architecture_packages[component_name][0].parent
            publisher = AptlyPublisher(
                component=component_name,
                distro="noble",
                channel=channel,
                pages_repo=str(arch_git_repo),
                branch="gh-pages",
                sign=False,
            )
            publisher.publish(debs_dir=str(debs_dir))

        # Verify all four components in this channel
        verify_architecture(arch_git_repo, channel, "noble", ["base", "feelpp", "applications", "ktirio"])


@pytest.mark.architecture
def test_update_base_preserves_others(architecture_packages, arch_git_repo):
    """Test updating base layer preserves other layers."""
    # Publish full architecture
    for component_name in ["base", "feelpp", "applications", "ktirio"]:
        debs_dir = architecture_packages[component_name][0].parent
        publisher = AptlyPublisher(
            component=component_name,
            distro="noble",
            channel="stable",
            pages_repo=str(arch_git_repo),
            branch="gh-pages",
            sign=False,
        )
        publisher.publish(debs_dir=str(debs_dir))

    # Update base layer (republish with same packages)
    base_dir = architecture_packages["base"][0].parent
    publisher_base_update = AptlyPublisher(
        component="base", distro="noble", channel="stable", pages_repo=str(arch_git_repo), branch="gh-pages", sign=False
    )
    publisher_base_update.publish(debs_dir=str(base_dir))

    # Verify all four components still present
    verify_architecture(arch_git_repo, "stable", "noble", ["base", "feelpp", "applications", "ktirio"])


@pytest.mark.architecture
def test_update_feelpp_preserves_others(architecture_packages, arch_git_repo):
    """Test updating feelpp layer preserves other layers."""
    # Publish full architecture
    for component_name in ["base", "feelpp", "applications", "ktirio"]:
        debs_dir = architecture_packages[component_name][0].parent
        publisher = AptlyPublisher(
            component=component_name,
            distro="noble",
            channel="stable",
            pages_repo=str(arch_git_repo),
            branch="gh-pages",
            sign=False,
        )
        publisher.publish(debs_dir=str(debs_dir))

    # Update feelpp layer
    feelpp_dir = architecture_packages["feelpp"][0].parent
    publisher_feelpp_update = AptlyPublisher(
        component="feelpp",
        distro="noble",
        channel="stable",
        pages_repo=str(arch_git_repo),
        branch="gh-pages",
        sign=False,
    )
    publisher_feelpp_update.publish(debs_dir=str(feelpp_dir))

    # Verify all four components still present
    verify_architecture(arch_git_repo, "stable", "noble", ["base", "feelpp", "applications", "ktirio"])


@pytest.mark.architecture
def test_channels_independent_architectures(architecture_packages, arch_git_repo):
    """Test that each channel can have independent architecture state."""
    # Stable: only base and feelpp
    for component_name in ["base", "feelpp"]:
        debs_dir = architecture_packages[component_name][0].parent
        publisher = AptlyPublisher(
            component=component_name,
            distro="noble",
            channel="stable",
            pages_repo=str(arch_git_repo),
            branch="gh-pages",
            sign=False,
        )
        publisher.publish(debs_dir=str(debs_dir))

    # Testing: full architecture
    for component_name in ["base", "feelpp", "applications", "ktirio"]:
        debs_dir = architecture_packages[component_name][0].parent
        publisher = AptlyPublisher(
            component=component_name,
            distro="noble",
            channel="testing",
            pages_repo=str(arch_git_repo),
            branch="gh-pages",
            sign=False,
        )
        publisher.publish(debs_dir=str(debs_dir))

    # PR: only base
    base_dir = architecture_packages["base"][0].parent
    publisher_pr = AptlyPublisher(
        component="base", distro="noble", channel="pr", pages_repo=str(arch_git_repo), branch="gh-pages", sign=False
    )
    publisher_pr.publish(debs_dir=str(base_dir))

    # Verify each channel has its own architecture
    verify_architecture(arch_git_repo, "stable", "noble", ["base", "feelpp"])
    verify_architecture(arch_git_repo, "testing", "noble", ["base", "feelpp", "applications", "ktirio"])
    verify_architecture(arch_git_repo, "pr", "noble", ["base"])


@pytest.mark.architecture
def test_component_name_normalization(architecture_packages, arch_git_repo):
    """Test that component names are properly normalized."""
    base_dir = architecture_packages["base"][0].parent

    # Publish with unnormalized name
    publisher = AptlyPublisher(
        component="Base_Layer",  # Should be normalized to "base-layer"
        distro="noble",
        channel="stable",
        pages_repo=str(arch_git_repo),
        branch="gh-pages",
        sign=False,
    )
    publisher.publish(debs_dir=str(base_dir))

    # Verify normalized component name
    verify_architecture(arch_git_repo, "stable", "noble", ["base-layer"])


@pytest.mark.architecture
def test_empty_bootstrap_component(arch_git_repo):
    """Test bootstrapping an empty component (no packages)."""
    publisher = AptlyPublisher(
        component="future-layer",
        distro="noble",
        channel="testing",
        pages_repo=str(arch_git_repo),
        branch="gh-pages",
        sign=False,
    )
    # Bootstrap without packages
    publisher.bootstrap()

    # Verify component exists (Packages file exists but is empty for empty components)
    with tempfile.TemporaryDirectory() as tmpdir:
        check_dir = Path(tmpdir) / "check"
        subprocess.run(
            ["git", "clone", "-b", "gh-pages", str(arch_git_repo), str(check_dir)],
            check=True,
            capture_output=True,
        )

        release_file = check_dir / "testing" / "dists" / "noble" / "Release"
        assert release_file.exists(), f"Release file not found: {release_file}"

        release_content = release_file.read_text()
        found_components = None
        for line in release_content.split("\n"):
            if line.startswith("Components:"):
                found_components = set(line.split(":", 1)[1].strip().split())
                break

        assert found_components is not None, "Components line not found"
        assert "future-layer" in found_components, f"future-layer not in components: {found_components}"

        # Verify Packages file exists (but may be empty for empty component)
        packages_file = check_dir / "testing" / "dists" / "noble" / "future-layer" / "binary-amd64" / "Packages"
        assert packages_file.exists(), f"Packages file missing for future-layer"
        # Empty component legitimately has empty Packages file
        assert packages_file.stat().st_size == 0, f"Packages file should be empty for empty component"
