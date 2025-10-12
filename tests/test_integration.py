"""Integration tests for multi-component APT repository publishing.

These tests verify the actual publishing workflow including:
- Single component publishing
- Multi-component publishing (adding components to existing publications)
- Updating existing components
- All three channels: stable, testing, pr
- Release and InRelease file consistency
"""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

from feelpp_aptly_publisher import AptlyPublisher


@pytest.fixture
def test_packages(tmp_path):
    """Create minimal test .deb packages for testing."""
    debs_dir = tmp_path / "debs"
    debs_dir.mkdir()

    # Create three minimal .deb packages
    for pkg_name in ["test-pkg1", "test-pkg2", "test-pkg3"]:
        pkg_dir = tmp_path / pkg_name
        debian_dir = pkg_dir / "DEBIAN"
        debian_dir.mkdir(parents=True)

        # Create minimal control file
        control = debian_dir / "control"
        control.write_text(
            f"""Package: {pkg_name}
Version: 1.0.0-1
Section: misc
Priority: optional
Architecture: amd64
Maintainer: Test <test@example.com>
Description: Test package {pkg_name}
 This is a test package for integration testing.
"""
        )

        # Create an empty file in the package
        usr_bin = pkg_dir / "usr" / "bin"
        usr_bin.mkdir(parents=True)
        (usr_bin / pkg_name).write_text("#!/bin/bash\necho test\n")
        (usr_bin / pkg_name).chmod(0o755)

        # Build the .deb package
        deb_file = debs_dir / f"{pkg_name}_1.0.0-1_amd64.deb"
        subprocess.run(
            ["dpkg-deb", "--build", str(pkg_dir), str(deb_file)],
            check=True,
            capture_output=True,
        )

    return debs_dir


@pytest.fixture
def git_repo(tmp_path):
    """Create a temporary git repository for testing."""
    # Create a bare repository that can be pushed to
    bare_repo = tmp_path / "test-apt-repo.git"
    bare_repo.mkdir()
    subprocess.run(["git", "init", "--bare"], cwd=bare_repo, check=True, capture_output=True)

    # Clone it to create a working copy with gh-pages branch
    work_repo = tmp_path / "test-apt-repo"
    subprocess.run(["git", "clone", str(bare_repo), str(work_repo)], check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=work_repo, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=work_repo, check=True, capture_output=True)

    # Create gh-pages branch and push it
    subprocess.run(["git", "checkout", "-b", "gh-pages"], cwd=work_repo, check=True, capture_output=True)
    readme = work_repo / "README.md"
    readme.write_text("# Test APT Repository\n")
    subprocess.run(["git", "add", "README.md"], cwd=work_repo, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=work_repo, check=True, capture_output=True)
    subprocess.run(["git", "push", "origin", "gh-pages"], cwd=work_repo, check=True, capture_output=True)

    # Return the bare repo path (what the publisher will clone)
    return bare_repo


def check_publication(bare_repo, channel, distro, expected_components):
    """Verify that a publication has the expected components."""
    # Clone the bare repo to check its contents
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        check_dir = Path(tmpdir) / "check"
        subprocess.run(
            ["git", "clone", "-b", "gh-pages", str(bare_repo), str(check_dir)],
            check=True,
            capture_output=True,
        )

        release_file = check_dir / channel / "dists" / distro / "Release"
        inrelease_file = check_dir / channel / "dists" / distro / "InRelease"

        # Both files should exist
        assert release_file.exists(), f"Release file not found: {release_file}"
        assert inrelease_file.exists(), f"InRelease file not found: {inrelease_file}"

        # Check Release file
        release_content = release_file.read_text()
        release_components = None
        for line in release_content.split("\n"):
            if line.startswith("Components:"):
                release_components = set(line.split(":", 1)[1].strip().split())
                break

        assert release_components is not None, "Components line not found in Release file"
        assert release_components == set(
            expected_components
        ), f"Release components mismatch: expected {expected_components}, got {release_components}"

        # Check InRelease file
        inrelease_content = inrelease_file.read_text()
        inrelease_components = None
        for line in inrelease_content.split("\n"):
            if line.startswith("Components:"):
                inrelease_components = set(line.split(":", 1)[1].strip().split())
                break

        assert inrelease_components is not None, "Components line not found in InRelease file"
        assert inrelease_components == set(
            expected_components
        ), f"InRelease components mismatch: expected {expected_components}, got {inrelease_components}"

        # Verify components are consistent between Release and InRelease
        assert (
            release_components == inrelease_components
        ), f"Release and InRelease components differ: {release_components} vs {inrelease_components}"

        # Check that Packages files exist for each component
        for component in expected_components:
            packages_file = check_dir / channel / "dists" / distro / component / "binary-amd64" / "Packages"
            assert packages_file.exists(), f"Packages file not found for component {component}: {packages_file}"

            # Verify packages file is not empty
            assert packages_file.stat().st_size > 0, f"Packages file is empty for component {component}"


@pytest.mark.integration
def test_single_component_publish_stable(test_packages, git_repo):
    """Test publishing a single component to stable channel."""
    # Create component directory with one package
    comp1_dir = test_packages.parent / "comp1"
    comp1_dir.mkdir()
    shutil.copy(test_packages / "test-pkg1_1.0.0-1_amd64.deb", comp1_dir)

    publisher = AptlyPublisher(
        component="component1",
        distro="noble",
        channel="stable",
        pages_repo=str(git_repo),
        branch="gh-pages",
        sign=False,
    )

    publisher.publish(debs_dir=str(comp1_dir))

    # Verify publication
    check_publication(git_repo, "stable", "noble", ["component1"])


@pytest.mark.integration
def test_multi_component_publish_stable(test_packages, git_repo):
    """Test publishing multiple components to stable channel."""
    # Publish first component
    comp1_dir = test_packages.parent / "comp1"
    comp1_dir.mkdir()
    shutil.copy(test_packages / "test-pkg1_1.0.0-1_amd64.deb", comp1_dir)

    publisher1 = AptlyPublisher(
        component="component1",
        distro="noble",
        channel="stable",
        pages_repo=str(git_repo),
        branch="gh-pages",
        sign=False,
    )
    publisher1.publish(debs_dir=str(comp1_dir))

    # Verify first component
    check_publication(git_repo, "stable", "noble", ["component1"])

    # Publish second component (should preserve first)
    comp2_dir = test_packages.parent / "comp2"
    comp2_dir.mkdir()
    shutil.copy(test_packages / "test-pkg2_1.0.0-1_amd64.deb", comp2_dir)

    publisher2 = AptlyPublisher(
        component="component2",
        distro="noble",
        channel="stable",
        pages_repo=str(git_repo),
        branch="gh-pages",
        sign=False,
    )
    publisher2.publish(debs_dir=str(comp2_dir))

    # Verify both components
    check_publication(git_repo, "stable", "noble", ["component1", "component2"])

    # Publish third component (should preserve both)
    comp3_dir = test_packages.parent / "comp3"
    comp3_dir.mkdir()
    shutil.copy(test_packages / "test-pkg3_1.0.0-1_amd64.deb", comp3_dir)

    publisher3 = AptlyPublisher(
        component="component3",
        distro="noble",
        channel="stable",
        pages_repo=str(git_repo),
        branch="gh-pages",
        sign=False,
    )
    publisher3.publish(debs_dir=str(comp3_dir))

    # Verify all three components
    check_publication(git_repo, "stable", "noble", ["component1", "component2", "component3"])


@pytest.mark.integration
def test_update_existing_component_stable(test_packages, git_repo):
    """Test updating an existing component in stable channel."""
    # Publish initial version
    comp1_dir = test_packages.parent / "comp1"
    comp1_dir.mkdir()
    shutil.copy(test_packages / "test-pkg1_1.0.0-1_amd64.deb", comp1_dir)

    publisher1 = AptlyPublisher(
        component="component1",
        distro="noble",
        channel="stable",
        pages_repo=str(git_repo),
        branch="gh-pages",
        sign=False,
    )
    publisher1.publish(debs_dir=str(comp1_dir))

    # Add second component
    comp2_dir = test_packages.parent / "comp2"
    comp2_dir.mkdir()
    shutil.copy(test_packages / "test-pkg2_1.0.0-1_amd64.deb", comp2_dir)

    publisher2 = AptlyPublisher(
        component="component2",
        distro="noble",
        channel="stable",
        pages_repo=str(git_repo),
        branch="gh-pages",
        sign=False,
    )
    publisher2.publish(debs_dir=str(comp2_dir))

    # Verify both components
    check_publication(git_repo, "stable", "noble", ["component1", "component2"])

    # Update first component (should preserve second)
    shutil.copy(test_packages / "test-pkg3_1.0.0-1_amd64.deb", comp1_dir / "test-pkg1-addon_1.0.0-1_amd64.deb")

    publisher1_update = AptlyPublisher(
        component="component1",
        distro="noble",
        channel="stable",
        pages_repo=str(git_repo),
        branch="gh-pages",
        sign=False,
    )
    publisher1_update.publish(debs_dir=str(comp1_dir))

    # Verify both components still present
    check_publication(git_repo, "stable", "noble", ["component1", "component2"])


@pytest.mark.integration
def test_publish_testing_channel(test_packages, git_repo):
    """Test publishing to testing channel."""
    comp1_dir = test_packages.parent / "comp1"
    comp1_dir.mkdir()
    shutil.copy(test_packages / "test-pkg1_1.0.0-1_amd64.deb", comp1_dir)

    publisher = AptlyPublisher(
        component="test-component",
        distro="noble",
        channel="testing",
        pages_repo=str(git_repo),
        branch="gh-pages",
        sign=False,
    )
    publisher.publish(debs_dir=str(comp1_dir))

    check_publication(git_repo, "testing", "noble", ["test-component"])


@pytest.mark.integration
def test_publish_pr_channel(test_packages, git_repo):
    """Test publishing to pr channel."""
    comp1_dir = test_packages.parent / "comp1"
    comp1_dir.mkdir()
    shutil.copy(test_packages / "test-pkg1_1.0.0-1_amd64.deb", comp1_dir)

    publisher = AptlyPublisher(
        component="pr-component",
        distro="noble",
        channel="pr",
        pages_repo=str(git_repo),
        branch="gh-pages",
        sign=False,
    )
    publisher.publish(debs_dir=str(comp1_dir))

    check_publication(git_repo, "pr", "noble", ["pr-component"])


@pytest.mark.integration
def test_multi_channel_independent(test_packages, git_repo):
    """Test that different channels are independent."""
    comp1_dir = test_packages.parent / "comp1"
    comp1_dir.mkdir()
    shutil.copy(test_packages / "test-pkg1_1.0.0-1_amd64.deb", comp1_dir)

    # Publish to stable
    publisher_stable = AptlyPublisher(
        component="stable-comp",
        distro="noble",
        channel="stable",
        pages_repo=str(git_repo),
        branch="gh-pages",
        sign=False,
    )
    publisher_stable.publish(debs_dir=str(comp1_dir))

    # Publish to testing
    publisher_testing = AptlyPublisher(
        component="testing-comp",
        distro="noble",
        channel="testing",
        pages_repo=str(git_repo),
        branch="gh-pages",
        sign=False,
    )
    publisher_testing.publish(debs_dir=str(comp1_dir))

    # Publish to pr
    publisher_pr = AptlyPublisher(
        component="pr-comp",
        distro="noble",
        channel="pr",
        pages_repo=str(git_repo),
        branch="gh-pages",
        sign=False,
    )
    publisher_pr.publish(debs_dir=str(comp1_dir))

    # Verify each channel has only its own component
    check_publication(git_repo, "stable", "noble", ["stable-comp"])
    check_publication(git_repo, "testing", "noble", ["testing-comp"])
    check_publication(git_repo, "pr", "noble", ["pr-comp"])


@pytest.mark.integration
def test_multi_component_all_channels(test_packages, git_repo):
    """Test multi-component publishing on all three channels."""
    for channel in ["stable", "testing", "pr"]:
        # Publish first component
        comp1_dir = test_packages.parent / f"{channel}_comp1"
        comp1_dir.mkdir(exist_ok=True)
        shutil.copy(test_packages / "test-pkg1_1.0.0-1_amd64.deb", comp1_dir)

        publisher1 = AptlyPublisher(
            component="component1",
            distro="noble",
            channel=channel,
            pages_repo=str(git_repo),
            branch="gh-pages",
            sign=False,
        )
        publisher1.publish(debs_dir=str(comp1_dir))

        # Publish second component
        comp2_dir = test_packages.parent / f"{channel}_comp2"
        comp2_dir.mkdir(exist_ok=True)
        shutil.copy(test_packages / "test-pkg2_1.0.0-1_amd64.deb", comp2_dir)

        publisher2 = AptlyPublisher(
            component="component2",
            distro="noble",
            channel=channel,
            pages_repo=str(git_repo),
            branch="gh-pages",
            sign=False,
        )
        publisher2.publish(debs_dir=str(comp2_dir))

        # Verify both components in this channel
        check_publication(git_repo, channel, "noble", ["component1", "component2"])
