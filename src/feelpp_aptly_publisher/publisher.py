"""Core publishing logic for aptly-based APT repository management.

Copyright (c) 2025 University of Strasbourg
Author: Christophe Prud'homme <christophe.prudhomme@cemosis.fr>

This file is part of Feel++ Aptly Publisher.
"""

import json
import logging
import os
import re
import shlex
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from glob import glob
from pathlib import Path
from typing import Optional, Union, List


class AptlyPublisher:
    """Manages APT repository publishing via aptly and GitHub Pages."""

    def __init__(
        self,
        component: str,
        distro: str,
        channel: str = "stable",
        pages_repo: str = "https://github.com/feelpp/apt.git",
        branch: str = "gh-pages",
        sign: bool = False,
        keyid: Optional[str] = None,
        passphrase: Optional[str] = None,
        aptly_config: Optional[str] = None,
        aptly_root: Optional[str] = None,
        verbose: bool = False,
    ):
        """
        Initialize the publisher.

        Args:
            component: Project/component name (will be normalized)
            distro: Ubuntu/Debian distribution (e.g., jammy, noble, bookworm)
            channel: Publication channel (stable, testing, or pr)
            pages_repo: GitHub Pages repository URL
            branch: Git branch for GitHub Pages
            sign: Whether to sign the publication with GPG
            keyid: GPG key ID (required if sign=True)
            passphrase: GPG passphrase (optional)
            aptly_config: Path to aptly config file (optional)
            aptly_root: Override aptly root directory (optional)
            verbose: Enable verbose logging
        """
        self.component = self._normalize_component(component)
        self.distro = distro
        self.channel = channel
        self.pages_repo = pages_repo
        self.branch = branch
        self.sign = sign
        self.keyid = keyid
        self.passphrase = passphrase
        self.aptly_config = aptly_config
        self.aptly_root = aptly_root
        self.verbose = verbose

        # Configure logging
        logging.basicConfig(
            level=logging.DEBUG if verbose else logging.INFO,
            format="%(levelname)s: %(message)s",
        )
        self.logger = logging.getLogger(__name__)

    @staticmethod
    def _normalize_component(s: str) -> str:
        """Normalize component name to lowercase alphanumeric with dashes."""
        s = s.lower()
        s = re.sub(r"[^a-z0-9]+", "-", s)
        return s.strip("-")

    def _run(
        self,
        cmd: Union[str, List[str]],
        cwd: Optional[str] = None,
        check: bool = True,
        env: Optional[dict] = None,
    ) -> subprocess.CompletedProcess:
        """Run a command with logging."""
        if isinstance(cmd, str):
            cmd_list = shlex.split(cmd)
        else:
            cmd_list = cmd
        self.logger.debug(
            "RUN%s: %s",
            f" (cwd={cwd})" if cwd else "",
            " ".join(shlex.quote(c) for c in cmd_list),
        )
        return subprocess.run(cmd_list, cwd=cwd, check=check, env=env)

    def _ensure_cmd(self, name: str):
        """Ensure a command is available on PATH."""
        try:
            self._run(["bash", "-lc", f"command -v {shlex.quote(name)}"], check=True)
        except subprocess.CalledProcessError:
            self.logger.error("Missing required command on PATH: %s", name)
            sys.exit(1)

    def publish(self, debs_dir: Optional[str] = None) -> None:
        """
        Publish packages to APT repository.

        Args:
            debs_dir: Directory containing .deb files. If None, creates an empty snapshot.
        """
        # Validate tools
        for tool in ("git", "rsync", "aptly"):
            self._ensure_cmd(tool)
        if self.sign:
            if not self.keyid:
                self.logger.error("--keyid is required with --sign")
                sys.exit(1)
            self._ensure_cmd("gpg")

        self.logger.info("Component : %s", self.component)
        self.logger.info("Distro    : %s", self.distro)
        self.logger.info("Channel   : %s", self.channel)
        self.logger.info("Repo      : %s (#%s)", self.pages_repo, self.branch)
        self.logger.info("Signing   : %s", "yes" if self.sign else "no")

        debs_path = Path(debs_dir) if debs_dir else None

        # Working directories
        with tempfile.TemporaryDirectory(prefix="apt-pages.") as pages_dir, tempfile.TemporaryDirectory(
            prefix="aptly."
        ) as aptly_dir:

            pages = Path(pages_dir)
            aptly_tmp_root = Path(aptly_dir)

            # Configure aptly
            if self.aptly_config:
                user_cfg_path = Path(self.aptly_config).expanduser().resolve()
                if not user_cfg_path.is_file():
                    self.logger.error("--aptly-config not found: %s", user_cfg_path)
                    sys.exit(1)
                try:
                    cfg_data = json.loads(user_cfg_path.read_text(encoding="utf-8"))
                except json.JSONDecodeError as exc:
                    self.logger.error("Failed to parse aptly config %s: %s", user_cfg_path, exc)
                    sys.exit(1)

                if self.aptly_root:
                    aptly_home = Path(self.aptly_root).expanduser().resolve()
                else:
                    root_dir = cfg_data.get("rootDir")
                    if not root_dir:
                        self.logger.error("Config %s lacks rootDir; supply --aptly-root", user_cfg_path)
                        sys.exit(1)
                    aptly_home = Path(root_dir)
                    if not aptly_home.is_absolute():
                        aptly_home = (user_cfg_path.parent / aptly_home).resolve()

                cfg_data["rootDir"] = str(aptly_home)
                aptly_cfg = aptly_tmp_root / "config.json"
                aptly_cfg.write_text(json.dumps(cfg_data, indent=2) + "\n", encoding="utf-8")
            else:
                aptly_cfg = aptly_tmp_root / "config.json"
                if self.aptly_root:
                    aptly_home = Path(self.aptly_root).expanduser().resolve()
                else:
                    aptly_home = aptly_tmp_root / ".aptly"

                cfg_payload = {"rootDir": str(aptly_home), "downloadConcurrency": 4}
                aptly_cfg.write_text(json.dumps(cfg_payload, indent=2) + "\n", encoding="utf-8")

            try:
                aptly_home.mkdir(parents=True, exist_ok=True)
            except OSError as exc:
                self.logger.error("Unable to create aptly root %s: %s", aptly_home, exc)
                sys.exit(1)
            aptly_public = aptly_home / "public"

            # Clone current gh-pages
            self.logger.info("Cloning %s (%s) ...", self.pages_repo, self.branch)
            res = self._run(["git", "clone", "-b", self.branch, self.pages_repo, str(pages)], check=False)
            if res.returncode != 0:
                # Branch not found: create orphan locally
                self._run(["git", "clone", self.pages_repo, str(pages)], check=True)
                self._run(["git", "checkout", "--orphan", self.branch], cwd=str(pages))
                self._run(["git", "rm", "-rf", "."], cwd=str(pages), check=False)

            # Setup aptly environment
            aptly_env = os.environ.copy()
            for key in ("APTLY_CONFIG", "APTLY_ROOT_DIR", "APTLY_ROOT", "APTLY_DB_DIR"):
                aptly_env.pop(key, None)
            aptly_env["APTLY_CONFIG"] = str(aptly_cfg)
            aptly_env["APTLY_ROOT_DIR"] = str(aptly_home)
            aptly_env["APTLY_ROOT"] = str(aptly_home)

            base_cmd = ["aptly", f"-config={aptly_cfg}"]

            def aptly_run(*args: str, check: bool = True) -> subprocess.CompletedProcess:
                return self._run(base_cmd + list(args), env=aptly_env, check=check)

            self.logger.info("Aptly cfg : %s", aptly_cfg)
            self.logger.info("Aptly root: %s", aptly_home)

            # Seed from current publication
            aptly_public.mkdir(parents=True, exist_ok=True)
            self._run(["rsync", "-a", f"{pages}/", f"{aptly_public}/"], check=True)

            # Recover aptly database from published repository if it exists
            # This is necessary so aptly knows about existing publications
            inrelease_check = aptly_public / self.channel / "dists" / self.distro / "InRelease"
            if inrelease_check.exists():
                self.logger.info("Recovering aptly database from existing publication...")
                # Capture output to see what was recovered
                recover_proc = subprocess.run(
                    base_cmd + ["db", "recover"], env=aptly_env, capture_output=True, text=True
                )
                if recover_proc.returncode == 0:
                    self.logger.info("Successfully recovered aptly database")
                    if self.verbose and recover_proc.stdout:
                        for line in recover_proc.stdout.strip().split("\n"):
                            self.logger.debug("  recover: %s", line)
                else:
                    self.logger.warning(
                        "Could not recover aptly database: %s",
                        recover_proc.stderr if recover_proc.stderr else "unknown error",
                    )

            # Stage repo and snapshot
            repo_name = f"{self.component}-{self.distro}-{self.channel}"
            self.logger.info("Staging repo: %s", repo_name)
            aptly_run(
                "repo", "create", f"-component={self.component}", f"-distribution={self.distro}", repo_name, check=False
            )

            if debs_path:
                if not debs_path.is_dir():
                    self.logger.error("--debs path does not exist or is not a directory: %s", debs_path)
                    sys.exit(1)
                debs = sorted(glob(str(debs_path / "*.deb")))
                if not debs:
                    self.logger.error("No .deb files found in %s", debs_path)
                    sys.exit(1)
                self.logger.info("Adding %d package(s) ...", len(debs))
                aptly_run("repo", "add", repo_name, *debs)
                is_empty = False
            else:
                self.logger.info("No --debs provided: creating an EMPTY snapshot (bootstrap).")
                is_empty = True

            ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
            snap = f"{repo_name}-{ts}"
            aptly_run("snapshot", "create", snap, "from", "repo", repo_name)

            # Publish or switch or add
            publish_prefix = self.channel
            sign_opts: List[str] = []
            if self.sign:
                sign_opts = ["-gpg-key", self.keyid]  # type: ignore
                if self.passphrase:
                    sign_opts += ["-passphrase", self.passphrase]
            else:
                sign_opts = ["-skip-signing"]

            # Check if publication exists by looking at Release/InRelease file in the published repository
            # Note: When using --skip-signing, InRelease might be stale, so check Release file
            # This is more reliable than aptly's database after rsync
            existing_components = []
            our_publication_exists = False

            # Check both Release and InRelease (Release is more up-to-date with skip-signing)
            release_path = aptly_public / self.channel / "dists" / self.distro / "Release"
            inrelease_path = aptly_public / self.channel / "dists" / self.distro / "InRelease"

            # Prefer Release file as it's always up-to-date
            check_path = release_path if release_path.exists() else inrelease_path

            if check_path.exists():
                our_publication_exists = True
                self.logger.info("Found existing publication at %s/%s", self.channel, self.distro)

                # Parse the file to get existing components
                release_content = check_path.read_text(encoding="utf-8")
                for line in release_content.split("\n"):
                    if line.startswith("Components:"):
                        components_str = line.split(":", 1)[1].strip()
                        existing_components = [c.strip() for c in components_str.split()]
                        self.logger.info("Existing components: %s", ", ".join(existing_components))
                        break
            else:
                self.logger.info("No existing publication found at %s/%s", self.channel, self.distro)

            # Decide on action: add/update component or create new publication
            if our_publication_exists:
                # Publication exists - need to republish with all components
                # Since db recover doesn't fully restore publication metadata, we can't use switch
                # Instead, we'll drop the publication and republish all components together
                if self.component in existing_components:
                    self.logger.info(
                        "Updating existing component '%s' in %s/%s ...", self.component, self.channel, self.distro
                    )
                    # Remove this component from existing list and add it back with new packages
                    existing_components = [c for c in existing_components if c != self.component]
                    if existing_components:
                        self.logger.info("Existing components will be preserved: %s", ", ".join(existing_components))
                    else:
                        self.logger.info("This is the only component in the publication")
                else:
                    self.logger.info(
                        "Adding new component '%s' to %s/%s ...", self.component, self.channel, self.distro
                    )
                    self.logger.info("Existing components will be preserved: %s", ", ".join(existing_components))

                # Create snapshots for existing components from their published packages
                all_snapshots = []
                all_components = []

                for existing_comp in existing_components:
                    # Create a temporary repo for this component
                    temp_repo_name = f"{existing_comp}-temp-{ts}"
                    self.logger.debug("Creating temporary repo for existing component: %s", existing_comp)
                    aptly_run(
                        "repo",
                        "create",
                        f"-component={existing_comp}",
                        f"-distribution={self.distro}",
                        temp_repo_name,
                        check=False,
                    )

                    # Import packages from the published pool
                    comp_packages_dir = aptly_public / self.channel / "pool" / existing_comp
                    if comp_packages_dir.exists():
                        self.logger.debug("Importing packages from %s", comp_packages_dir)
                        # Find all .deb files recursively
                        import glob as glob_module

                        deb_files = glob_module.glob(str(comp_packages_dir / "**" / "*.deb"), recursive=True)
                        if deb_files:
                            self.logger.debug("Found %d package(s) for %s", len(deb_files), existing_comp)
                            aptly_run("repo", "add", temp_repo_name, *deb_files, check=False)

                    # Create snapshot from this temp repo
                    temp_snap_name = f"{temp_repo_name}-snap"
                    aptly_run("snapshot", "create", temp_snap_name, "from", "repo", temp_repo_name)
                    all_snapshots.append(temp_snap_name)
                    all_components.append(existing_comp)

                # Add our new/updated component
                all_snapshots.append(snap)
                all_components.append(self.component)

                # Drop the existing publication (it's not in the database anyway after rsync)
                self.logger.info("Dropping existing publication to republish with all components...")
                # We can't drop what's not in the database, so just proceed to publish

                # Publish ALL components together
                components_str = ",".join(all_components)
                self.logger.info("Publishing with components: %s", components_str)

                snapshot_opts = [
                    "-distribution",
                    self.distro,
                    "-component",
                    components_str,
                    "-force-overwrite",
                ] + sign_opts
                publish_result = aptly_run(
                    "publish", "snapshot", *snapshot_opts, *all_snapshots, publish_prefix, check=False
                )

                if publish_result.returncode != 0:
                    self.logger.error("Failed to publish components")
                    self.logger.error("You may need to republish all components manually")
                    sys.exit(1)

                self.logger.info("Successfully published component '%s' with all existing components", self.component)
            else:
                # Publication doesn't exist - create it
                self.logger.info("Creating first-time publication %s/%s ...", self.channel, self.distro)
                snapshot_opts = [
                    "-distribution",
                    self.distro,
                    "-component",
                    self.component,
                    "-force-overwrite",
                ]

                # For first-time publications, we must specify architectures explicitly
                # Even for arch:all packages, aptly needs to know target architectures
                if is_empty:
                    self.logger.debug("Empty snapshot detected, specifying architectures explicitly")
                    snapshot_opts.extend(["-architectures", "amd64,arm64"])
                else:
                    # For non-empty first-time publications, also specify architectures
                    # to avoid "unable to figure out list of architectures" error
                    self.logger.debug("First-time publication, specifying architectures: amd64,arm64")
                    snapshot_opts.extend(["-architectures", "amd64,arm64"])

                snapshot_opts.extend(sign_opts)
                aptly_run("publish", "snapshot", *snapshot_opts, snap, publish_prefix)
                self.logger.info("Successfully created publication %s/%s", self.channel, self.distro)

            # Fix InRelease file when skip-signing is used
            # aptly doesn't update InRelease when using --skip-signing
            if not self.sign:
                release_file = aptly_public / self.channel / "dists" / self.distro / "Release"
                inrelease_file = aptly_public / self.channel / "dists" / self.distro / "InRelease"

                if release_file.exists():
                    self.logger.info("Updating InRelease file (skip-signing workaround)...")
                    # Copy Release to InRelease since we're not signing
                    inrelease_file.write_text(release_file.read_text(encoding="utf-8"), encoding="utf-8")
                    self.logger.debug("InRelease updated from Release")

            # Sync back & push
            self._run(["rsync", "-a", "--delete", f"{aptly_public}/", f"{pages}/"], check=True)
            # Ensure .nojekyll exists so Pages serves 'dists/'
            (pages / ".nojekyll").write_text("", encoding="utf-8")

            self._run(["git", "add", "-A"], cwd=str(pages), check=True)
            # Commit may be empty if nothing changed; ignore failure
            commit_ts = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            self._run(
                ["git", "commit", "-m", f"Publish {self.component} ({self.distro}/{self.channel}) {commit_ts}"],
                cwd=str(pages),
                check=False,
            )
            self._run(["git", "push", "origin", self.branch], cwd=str(pages), check=True)

            self.logger.info("Done. Browse: https://feelpp.github.io/apt/%s/dists/%s/", self.channel, self.distro)

    def bootstrap(self) -> None:
        """Bootstrap an empty component (no .deb files)."""
        self.publish(debs_dir=None)
