#!/usr/bin/env python3
"""
aptly_publish.py — Bootstrap or update a component (project) in a GitHub Pages APT repo.

- Clones current gh-pages to preserve existing content
- Seeds an aptly workspace from it
- If --debs provided: adds .deb files to a staging repo
  else: creates an empty (bootstrap) snapshot
- Publishes under prefix (=channel) and distro into the given component
- Syncs back the static APT tree and pushes to gh-pages

Requirements (on PATH): aptly, git, rsync, and gpg if using --sign
"""

import argparse
import json
import logging
import os
import re
import shlex
import subprocess
import sys
import tempfile
from glob import glob
from pathlib import Path
from datetime import datetime, UTC


def run(
    cmd: str | list[str],
    cwd: str | None = None,
    check: bool = True,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess:
    if isinstance(cmd, str):
        cmd_list = shlex.split(cmd)
    else:
        cmd_list = cmd
    logging.debug("RUN%s: %s", f" (cwd={cwd})" if cwd else "", " ".join(shlex.quote(c) for c in cmd_list))
    return subprocess.run(cmd_list, cwd=cwd, check=check, env=env)


def ensure_cmd(name: str):
    try:
        run(["bash", "-lc", f"command -v {shlex.quote(name)}"], check=True)
    except subprocess.CalledProcessError:
        logging.error("Missing required command on PATH: %s", name)
        sys.exit(1)


def norm_component(s: str) -> str:
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


def main():
    p = argparse.ArgumentParser(description="Bootstrap or update a component in a GitHub Pages APT repo")
    p.add_argument("--component", required=True, help="project/component name (will be normalized)")
    p.add_argument("--distro", default="noble", help="Ubuntu/Debian distribution (e.g., jammy, noble, bookworm)")
    p.add_argument("--channel", default="stable", choices=["stable", "testing", "pr"], help="prefix (channel)")
    p.add_argument("--debs", default=None, help="directory with .deb files; if omitted, bootstrap empty component")
    p.add_argument("--pages-repo", default=os.environ.get("PAGES_REPO", "https://github.com/feelpp/apt.git"))
    p.add_argument("--branch", default=os.environ.get("BRANCH", "gh-pages"))
    p.add_argument("--sign", action="store_true", help="sign the publication with GPG")
    p.add_argument("--keyid", default=None, help="GPG key id (required if --sign)")
    p.add_argument("--passphrase", default=None, help="GPG passphrase (optional)")
    p.add_argument("--aptly-config", default=None, help="path to an aptly config file to reuse (optional)")
    p.add_argument("--aptly-root", default=None, help="override aptly root directory (defaults to temp workspace)")
    p.add_argument("--verbose", action="store_true")
    args = p.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    component = norm_component(args.component)
    distro = args.distro
    channel = args.channel
    pages_repo = args.pages_repo
    branch = args.branch
    debs_dir = Path(args.debs) if args.debs else None

    # Tools present?
    for tool in ("git", "rsync", "aptly"):
        ensure_cmd(tool)
    if args.sign:
        if not args.keyid:
            logging.error("--keyid is required with --sign")
            sys.exit(1)
        ensure_cmd("gpg")

    logging.info("Component : %s", component)
    logging.info("Distro    : %s", distro)
    logging.info("Channel   : %s", channel)
    logging.info("Repo      : %s (#%s)", pages_repo, branch)
    logging.info("Signing   : %s", "yes" if args.sign else "no")

    # Working dirs
    with tempfile.TemporaryDirectory(prefix="apt-pages.") as pages_dir, \
         tempfile.TemporaryDirectory(prefix="aptly.") as aptly_dir:

        pages = Path(pages_dir)
        aptly_tmp_root = Path(aptly_dir)

        if args.aptly_config:
            user_cfg_path = Path(args.aptly_config).expanduser().resolve()
            if not user_cfg_path.is_file():
                logging.error("--aptly-config not found: %s", user_cfg_path)
                sys.exit(1)
            try:
                cfg_data = json.loads(user_cfg_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                logging.error("Failed to parse aptly config %s: %s", user_cfg_path, exc)
                sys.exit(1)

            if args.aptly_root:
                aptly_home = Path(args.aptly_root).expanduser().resolve()
            else:
                root_dir = cfg_data.get("rootDir")
                if not root_dir:
                    logging.error("Config %s lacks rootDir; supply --aptly-root", user_cfg_path)
                    sys.exit(1)
                aptly_home = Path(root_dir)
                if not aptly_home.is_absolute():
                    aptly_home = (user_cfg_path.parent / aptly_home).resolve()

            cfg_data["rootDir"] = str(aptly_home)
            aptly_cfg = aptly_tmp_root / "config.json"
            aptly_cfg.write_text(json.dumps(cfg_data, indent=2) + "\n", encoding="utf-8")
        else:
            aptly_cfg = aptly_tmp_root / "config.json"
            if args.aptly_root:
                aptly_home = Path(args.aptly_root).expanduser().resolve()
            else:
                aptly_home = aptly_tmp_root / ".aptly"

            cfg_payload = {"rootDir": str(aptly_home), "downloadConcurrency": 4}
            aptly_cfg.write_text(json.dumps(cfg_payload, indent=2) + "\n", encoding="utf-8")

        try:
            aptly_home.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            logging.error("Unable to create aptly root %s: %s", aptly_home, exc)
            sys.exit(1)
        aptly_public = aptly_home / "public"

        # Clone current gh-pages (or create orphan if missing)
        logging.info("Cloning %s (%s) ...", pages_repo, branch)
        res = run(["git", "clone", "-b", branch, pages_repo, str(pages)], check=False)
        if res.returncode != 0:
            # Branch not found: create orphan locally
            run(["git", "clone", pages_repo, str(pages)], check=True)
            run(["git", "checkout", "--orphan", branch], cwd=str(pages))
            run(["git", "rm", "-rf", "."], cwd=str(pages), check=False)

        # Init aptly config + seed from current publication
        aptly_env = os.environ.copy()
        for key in ("APTLY_CONFIG", "APTLY_ROOT_DIR", "APTLY_ROOT", "APTLY_DB_DIR"):
            aptly_env.pop(key, None)
        aptly_env["APTLY_CONFIG"] = str(aptly_cfg)
        aptly_env["APTLY_ROOT_DIR"] = str(aptly_home)
        aptly_env["APTLY_ROOT"] = str(aptly_home)

        base_cmd = [
            "aptly",
            f"-config={aptly_cfg}",
        ]

        def aptly_run(*args: str, check: bool = True) -> subprocess.CompletedProcess:
            return run(base_cmd + list(args), env=aptly_env, check=check)

        logging.info("Aptly cfg : %s", aptly_cfg)
        logging.info("Aptly root: %s", aptly_home)

        aptly_public.mkdir(parents=True, exist_ok=True)
        run(["rsync", "-a", f"{pages}/", f"{aptly_public}/"], check=True)

        # Stage repo and snapshot
        repo_name = f"{component}-{distro}-{channel}"
        logging.info("Staging repo: %s", repo_name)
        aptly_run("repo", "create", f"-component={component}", f"-distribution={distro}", repo_name, check=False)

        if debs_dir:
            if not debs_dir.is_dir():
                logging.error("--debs path does not exist or is not a directory: %s", debs_dir)
                sys.exit(1)
            debs = sorted(glob(str(debs_dir / "*.deb")))
            if not debs:
                logging.error("No .deb files found in %s", debs_dir)
                sys.exit(1)
            logging.info("Adding %d package(s) ...", len(debs))
            aptly_run("repo", "add", repo_name, *debs)
        else:
            logging.info("No --debs provided: creating an EMPTY snapshot (bootstrap).")

        ts = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
        snap = f"{repo_name}-{ts}"
        aptly_run("snapshot", "create", snap, "from", "repo", repo_name)

        # Publish or switch
        publish_prefix = channel
        snapshot_opts = ["-distribution", distro, "-component", component]
        add_opts = [f"-prefix={publish_prefix}", "-component", component]
        switch_opts = ["-component", component]
        if args.sign:
            sign_opts = ["-gpg-key", args.keyid]
            if args.passphrase:
                sign_opts += ["-passphrase", args.passphrase]
            snapshot_opts += sign_opts
            switch_opts += sign_opts
            # Note: add_opts don't support GPG flags, signing happens in publish update
        else:
            snapshot_opts += ["-skip-signing"]
            switch_opts += ["-skip-signing"]

        target_dists = aptly_public / channel / "dists" / distro
        component_root = target_dists / component
        first_publish = not target_dists.exists()
        component_exists = component_root.exists()

        if first_publish:
            logging.info("First-time publish %s/%s ...", channel, distro)
            aptly_run("publish", "snapshot", *snapshot_opts, snap, publish_prefix)
        elif component_exists:
            logging.info("Updating existing component via publish switch ...")
            aptly_run("publish", "switch", *switch_opts, distro, publish_prefix, snap)
        else:
            logging.info("Adding/updating component %s to existing publication ...", component)
            # Try to add first, if it fails (already exists), replace it
            add_result = aptly_run("publish", "source", "add", *add_opts, distro, snap, check=False)
            if add_result.returncode != 0:
                logging.info("Component already staged, replacing instead ...")
                replace_opts = [f"-prefix={publish_prefix}", "-component", component]
                # Note: replace doesn't support GPG flags, signing happens in publish update
                aptly_run("publish", "source", "replace", *replace_opts, distro, snap)
            
            # After adding/replacing source, we need to update the publication
            update_opts = []
            if not args.sign:
                update_opts += ["-skip-signing"]
            elif args.keyid:
                update_opts += ["-gpg-key", args.keyid]
                if args.passphrase:
                    update_opts += ["-passphrase", args.passphrase]
            aptly_run("publish", "update", *update_opts, distro, publish_prefix)

        # Sync back & push
        run(["rsync", "-a", "--delete", f"{aptly_public}/", f"{pages}/"], check=True)
        # Ensure .nojekyll exists so Pages serves 'dists/'
        (pages / ".nojekyll").write_text("", encoding="utf-8")

        run(["git", "add", "-A"], cwd=str(pages), check=True)
        # Commit may be empty if nothing changed; ignore failure
        commit_ts = datetime.now(UTC).isoformat().replace("+00:00", "Z")
        run(["git", "commit", "-m", f"Publish {component} ({distro}/{channel}) {commit_ts}"],
            cwd=str(pages), check=False)
        run(["git", "push", "origin", branch], cwd=str(pages), check=True)

        logging.info("Done. Browse: https://feelpp.github.io/apt/%s/dists/%s/", channel, distro)


if __name__ == "__main__":
    main()
