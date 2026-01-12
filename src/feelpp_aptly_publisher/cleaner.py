"""Package cleanup and retention management for APT repositories.

Copyright (c) 2025 University of Strasbourg
Author: Christophe Prud'homme <christophe.prudhomme@cemosis.fr>

This file is part of Feel++ Aptly Publisher.
"""

import json
import logging
import re
import subprocess
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


@dataclass
class RetentionPolicy:
    """Configuration for package retention policies."""

    # Maximum age in days for pre-release packages (alpha, beta, rc, etc.)
    prerelease_max_age_days: int = 90

    # Maximum number of versions to keep per package (0 = unlimited)
    max_versions_per_package: int = 0

    # Channels and their specific policies
    channel_policies: Dict[str, dict] = field(
        default_factory=lambda: {
            "stable": {
                "keep_prereleases": True,  # Keep pre-releases in stable (they're intentional)
                "max_versions": 0,  # Keep all versions
            },
            "testing": {
                "keep_prereleases": False,  # Clean old pre-releases
                "max_versions": 5,  # Keep last 5 versions
            },
            "pr": {
                "keep_prereleases": False,  # Clean old pre-releases
                "max_versions": 3,  # Keep last 3 versions
                "max_age_days": 30,  # PR packages expire faster
            },
        }
    )

    # Components to exclude from cleanup
    protected_components: List[str] = field(default_factory=list)

    # Specific package patterns to never delete
    protected_packages: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "prerelease_max_age_days": self.prerelease_max_age_days,
            "max_versions_per_package": self.max_versions_per_package,
            "channel_policies": self.channel_policies,
            "protected_components": self.protected_components,
            "protected_packages": self.protected_packages,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "RetentionPolicy":
        """Create from dictionary."""
        return cls(
            prerelease_max_age_days=data.get("prerelease_max_age_days", 90),
            max_versions_per_package=data.get("max_versions_per_package", 0),
            channel_policies=data.get("channel_policies", cls().channel_policies),
            protected_components=data.get("protected_components", []),
            protected_packages=data.get("protected_packages", []),
        )

    @classmethod
    def from_file(cls, path: Path) -> "RetentionPolicy":
        """Load retention policy from JSON file."""
        with open(path, "r", encoding="utf-8") as f:
            return cls.from_dict(json.load(f))

    def save(self, path: Path) -> None:
        """Save retention policy to JSON file."""
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)


@dataclass
class PackageInfo:
    """Information about a Debian package."""

    name: str
    version: str
    arch: str
    filename: str
    path: Path
    channel: str
    component: str
    size: int
    age_days: int
    is_prerelease: bool

    def __hash__(self):
        return hash(self.path)

    def __eq__(self, other):
        if isinstance(other, PackageInfo):
            return self.path == other.path
        return False


class DebianVersionCompare:
    """Compare Debian package versions using dpkg --compare-versions."""

    @staticmethod
    def compare(v1: str, v2: str) -> int:
        """
        Compare two Debian versions.

        Returns:
            -1 if v1 < v2
             0 if v1 == v2
             1 if v1 > v2
        """
        try:
            # Try using dpkg for accurate comparison
            result = subprocess.run(["dpkg", "--compare-versions", v1, "lt", v2], capture_output=True)
            if result.returncode == 0:
                return -1

            result = subprocess.run(["dpkg", "--compare-versions", v1, "gt", v2], capture_output=True)
            if result.returncode == 0:
                return 1

            return 0
        except FileNotFoundError:
            # Fallback to simple string comparison if dpkg not available
            if v1 < v2:
                return -1
            elif v1 > v2:
                return 1
            return 0

    @staticmethod
    def sort_versions(versions: List[str], reverse: bool = False) -> List[str]:
        """Sort a list of Debian versions."""
        from functools import cmp_to_key

        return sorted(versions, key=cmp_to_key(DebianVersionCompare.compare), reverse=reverse)


class AptlyCleaner:
    """Manages cleanup of APT repository packages."""

    # Pre-release version patterns (Debian conventions)
    PRERELEASE_PATTERNS = [
        r"~alpha\d*",
        r"~beta\d*",
        r"~rc\d*",
        r"~pre\d*",
        r"~dev",
        r"~git\d*",
        r"~svn\d*",
        r"~bzr\d*",
        r"\+git\d{8}",
        r"\+svn\d+",
        r"alpha\d+",
        r"beta\d+",
        r"rc\d+",
        r"\.0~",  # Sometimes used for pre-releases
    ]

    def __init__(
        self,
        repo_path: Path,
        policy: Optional[RetentionPolicy] = None,
        verbose: bool = False,
    ):
        """
        Initialize the cleaner.

        Args:
            repo_path: Path to the APT repository (gh-pages checkout)
            policy: Retention policy configuration
            verbose: Enable verbose logging
        """
        self.repo_path = Path(repo_path)
        self.policy = policy or RetentionPolicy()
        self.verbose = verbose

        logging.basicConfig(
            level=logging.DEBUG if verbose else logging.INFO,
            format="%(levelname)s: %(message)s",
        )
        self.logger = logging.getLogger(__name__)

        self._prerelease_re = re.compile("|".join(self.PRERELEASE_PATTERNS), re.IGNORECASE)

    def is_prerelease(self, version: str) -> bool:
        """Check if a version string indicates a pre-release."""
        return bool(self._prerelease_re.search(version))

    def parse_deb_filename(self, filename: str) -> Optional[Dict[str, str]]:
        """Parse Debian package filename into components."""
        # Format: name_version_arch.deb
        match = re.match(r"^(.+)_([^_]+)_([^_]+)\.deb$", filename)
        if match:
            return {
                "name": match.group(1),
                "version": match.group(2),
                "arch": match.group(3),
            }
        return None

    def scan_packages(self, channels: Optional[List[str]] = None) -> List[PackageInfo]:
        """
        Scan repository for all packages.

        Args:
            channels: List of channels to scan (default: all)

        Returns:
            List of PackageInfo objects
        """
        if channels is None:
            channels = ["stable", "testing", "pr"]

        packages = []

        for channel in channels:
            pool_dir = self.repo_path / channel / "pool"
            if not pool_dir.exists():
                self.logger.debug("Channel %s has no pool directory", channel)
                continue

            # Pool structure: pool/<component>/<first-letter>/<package-name>/<files>
            for deb_file in pool_dir.rglob("*.deb"):
                parsed = self.parse_deb_filename(deb_file.name)
                if not parsed:
                    self.logger.warning("Could not parse filename: %s", deb_file.name)
                    continue

                # Extract component from path
                relative = deb_file.relative_to(pool_dir)
                component = relative.parts[0] if relative.parts else "unknown"

                # Get file stats
                stat = deb_file.stat()
                age = datetime.now() - datetime.fromtimestamp(stat.st_mtime)

                pkg = PackageInfo(
                    name=parsed["name"],
                    version=parsed["version"],
                    arch=parsed["arch"],
                    filename=deb_file.name,
                    path=deb_file,
                    channel=channel,
                    component=component,
                    size=stat.st_size,
                    age_days=age.days,
                    is_prerelease=self.is_prerelease(parsed["version"]),
                )
                packages.append(pkg)

        self.logger.info("Scanned %d packages across %d channel(s)", len(packages), len(channels))
        return packages

    def find_cleanup_candidates(
        self,
        packages: Optional[List[PackageInfo]] = None,
        channels: Optional[List[str]] = None,
    ) -> Tuple[List[PackageInfo], List[PackageInfo]]:
        """
        Find packages that are candidates for cleanup.

        Args:
            packages: Pre-scanned packages (optional)
            channels: Channels to analyze

        Returns:
            Tuple of (prerelease_candidates, version_limit_candidates)
        """
        if packages is None:
            packages = self.scan_packages(channels)

        prerelease_candidates = []
        version_limit_candidates = []

        # Group packages by (channel, component, name, arch)
        package_groups: Dict[Tuple[str, str, str, str], List[PackageInfo]] = defaultdict(list)
        for pkg in packages:
            key = (pkg.channel, pkg.component, pkg.name, pkg.arch)
            package_groups[key].append(pkg)

        for (channel, component, name, _arch), group in package_groups.items():
            # Get channel-specific policy
            channel_policy = self.policy.channel_policies.get(channel, {})
            keep_prereleases = channel_policy.get("keep_prereleases", True)
            max_versions = channel_policy.get("max_versions", self.policy.max_versions_per_package)
            max_age = channel_policy.get("max_age_days", self.policy.prerelease_max_age_days)

            # Check protected components
            if component in self.policy.protected_components:
                self.logger.debug("Skipping protected component: %s", component)
                continue

            # Check protected packages
            if any(re.match(pattern, name) for pattern in self.policy.protected_packages):
                self.logger.debug("Skipping protected package: %s", name)
                continue

            # Find old pre-releases
            if not keep_prereleases:
                for pkg in group:
                    if pkg.is_prerelease and pkg.age_days > max_age:
                        prerelease_candidates.append(pkg)
                        self.logger.debug(
                            "Pre-release candidate: %s %s (%d days old)", pkg.name, pkg.version, pkg.age_days
                        )

            # Apply version limits
            if max_versions > 0 and len(group) > max_versions:
                # Sort by version (newest first)
                sorted_group = sorted(group, key=lambda p: p.version, reverse=True)
                # Try to use dpkg for proper sorting
                try:
                    versions = [p.version for p in group]
                    sorted_versions = DebianVersionCompare.sort_versions(versions, reverse=True)
                    version_to_pkg = {p.version: p for p in group}
                    sorted_group = [version_to_pkg[v] for v in sorted_versions if v in version_to_pkg]
                except Exception:
                    pass  # Fall back to string sort

                # Mark excess versions for cleanup
                excess = sorted_group[max_versions:]
                for pkg in excess:
                    if pkg not in prerelease_candidates:
                        version_limit_candidates.append(pkg)
                        self.logger.debug(
                            "Version limit candidate: %s %s (keeping %d versions)", pkg.name, pkg.version, max_versions
                        )

        self.logger.info(
            "Found %d pre-release candidates, %d version-limit candidates",
            len(prerelease_candidates),
            len(version_limit_candidates),
        )

        return prerelease_candidates, version_limit_candidates

    def generate_report(
        self,
        prerelease_candidates: List[PackageInfo],
        version_limit_candidates: List[PackageInfo],
    ) -> dict:
        """Generate a cleanup report."""
        all_candidates = list(set(prerelease_candidates + version_limit_candidates))

        total_size = sum(pkg.size for pkg in all_candidates)

        # Group by channel
        by_channel = defaultdict(list)
        for pkg in all_candidates:
            by_channel[pkg.channel].append(
                {
                    "name": pkg.name,
                    "version": pkg.version,
                    "arch": pkg.arch,
                    "component": pkg.component,
                    "size": pkg.size,
                    "age_days": pkg.age_days,
                    "is_prerelease": pkg.is_prerelease,
                    "path": str(pkg.path),
                }
            )

        return {
            "summary": {
                "total_candidates": len(all_candidates),
                "prerelease_candidates": len(prerelease_candidates),
                "version_limit_candidates": len(version_limit_candidates),
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
            },
            "by_channel": dict(by_channel),
            "policy": self.policy.to_dict(),
            "generated_at": datetime.now().isoformat(),
        }

    def cleanup(
        self,
        prerelease_candidates: List[PackageInfo],
        version_limit_candidates: List[PackageInfo],
        dry_run: bool = True,
    ) -> dict:
        """
        Perform cleanup of packages.

        Args:
            prerelease_candidates: Pre-release packages to remove
            version_limit_candidates: Excess version packages to remove
            dry_run: If True, only report what would be deleted

        Returns:
            Cleanup result report
        """
        all_candidates = list(set(prerelease_candidates + version_limit_candidates))

        deleted = []
        failed = []

        for pkg in all_candidates:
            if dry_run:
                self.logger.info("[DRY RUN] Would delete: %s", pkg.path)
                deleted.append(str(pkg.path))
            else:
                try:
                    pkg.path.unlink()
                    self.logger.info("Deleted: %s", pkg.path)
                    deleted.append(str(pkg.path))

                    # Remove empty parent directories up to pool level
                    # Stop at repo_path or if directory is not empty
                    parent = pkg.path.parent
                    while parent != self.repo_path and self.repo_path in parent.parents:
                        try:
                            if not any(parent.iterdir()):
                                parent.rmdir()
                                self.logger.debug("Removed empty directory: %s", parent)
                                parent = parent.parent
                            else:
                                break  # Directory not empty, stop
                        except OSError:
                            break  # Permission or other error, stop

                except Exception as e:
                    self.logger.error("Failed to delete %s: %s", pkg.path, e)
                    failed.append({"path": str(pkg.path), "error": str(e)})

        return {
            "dry_run": dry_run,
            "deleted_count": len(deleted),
            "failed_count": len(failed),
            "deleted": deleted,
            "failed": failed,
        }

    def regenerate_metadata(self, channels: Optional[List[str]] = None) -> None:
        """
        Regenerate repository metadata after cleanup.

        This requires aptly to be installed and will rebuild the
        Packages/Release files for affected distributions.

        Args:
            channels: Channels to regenerate (default: all modified)
        """
        if channels is None:
            channels = ["stable", "testing", "pr"]

        self.logger.info("Regenerating repository metadata for channels: %s", ", ".join(channels))

        # This is a placeholder - actual implementation would use aptly
        # to republish the repository with updated metadata
        self.logger.warning(
            "Metadata regeneration requires running the publisher tool " "to republish affected distributions"
        )


def find_pr_cleanup_candidates(
    repo_path: Path,
    closed_prs: Optional[List[int]] = None,
    max_age_days: int = 30,
) -> List[PackageInfo]:
    """
    Find PR channel packages that should be cleaned up.

    Args:
        repo_path: Path to repository
        closed_prs: List of closed PR numbers (packages for these will be cleaned)
        max_age_days: Maximum age for PR packages regardless of PR status

    Returns:
        List of packages to clean
    """
    cleaner = AptlyCleaner(repo_path)
    packages = cleaner.scan_packages(channels=["pr"])

    candidates = []

    for pkg in packages:
        # Check age
        if pkg.age_days > max_age_days:
            candidates.append(pkg)
            continue

        # Check if from a closed PR (would need PR number in package name/version)
        # This is a placeholder for more sophisticated PR tracking
        if closed_prs:
            # Extract PR number from version if encoded (e.g., 1.0.0~pr123)
            pr_match = re.search(r"pr(\d+)", pkg.version, re.IGNORECASE)
            if pr_match:
                pr_num = int(pr_match.group(1))
                if pr_num in closed_prs:
                    candidates.append(pkg)

    return candidates
