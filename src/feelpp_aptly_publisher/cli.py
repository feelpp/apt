"""Command-line interface for aptly publisher."""

import argparse
import os
import sys

from .publisher import AptlyPublisher


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Bootstrap or update a component in a GitHub Pages APT repo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Publish packages to stable channel
  %(prog)s --component mmg --channel stable --distro noble --debs ./packages/

  # Bootstrap empty component
  %(prog)s --component new-project --channel testing --distro noble

  # Publish with GPG signing
  %(prog)s --component feelpp --distro jammy --debs ./build/packages/ --sign --keyid YOUR_KEY_ID

Environment variables:
  PAGES_REPO    GitHub Pages repository URL (default: https://github.com/feelpp/apt.git)
  BRANCH        Git branch for GitHub Pages (default: gh-pages)
  GPG_KEYID     GPG key ID for signing
  GPG_PASSPHRASE GPG passphrase (use with caution)
        """,
    )
    parser.add_argument(
        "--component",
        required=True,
        help="project/component name (will be normalized to lowercase alphanumeric)",
    )
    parser.add_argument(
        "--distro",
        default="noble",
        help="Ubuntu/Debian distribution (e.g., jammy, noble, bookworm) (default: noble)",
    )
    parser.add_argument(
        "--channel",
        default="stable",
        choices=["stable", "testing", "pr"],
        help="publication channel/prefix (default: stable)",
    )
    parser.add_argument(
        "--debs",
        default=None,
        help="directory with .deb files; if omitted, bootstrap empty component",
    )
    parser.add_argument(
        "--pages-repo",
        default=os.environ.get("PAGES_REPO", "https://github.com/feelpp/apt.git"),
        help="GitHub Pages repository URL (default: from PAGES_REPO env or feelpp/apt)",
    )
    parser.add_argument(
        "--branch",
        default=os.environ.get("BRANCH", "gh-pages"),
        help="Git branch for GitHub Pages (default: from BRANCH env or gh-pages)",
    )
    parser.add_argument(
        "--sign",
        action="store_true",
        help="sign the publication with GPG",
    )
    parser.add_argument(
        "--keyid",
        default=os.environ.get("GPG_KEYID"),
        help="GPG key ID (required if --sign; can use GPG_KEYID env)",
    )
    parser.add_argument(
        "--passphrase",
        default=os.environ.get("GPG_PASSPHRASE"),
        help="GPG passphrase (optional; can use GPG_PASSPHRASE env)",
    )
    parser.add_argument(
        "--aptly-config",
        default=None,
        help="path to an aptly config file to reuse (optional)",
    )
    parser.add_argument(
        "--aptly-root",
        default=None,
        help="override aptly root directory (defaults to temp workspace)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="enable verbose/debug logging",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 1.0.0",
    )

    args = parser.parse_args()

    if args.sign and not args.keyid:
        parser.error("--keyid is required when --sign is used (or set GPG_KEYID environment variable)")

    try:
        publisher = AptlyPublisher(
            component=args.component,
            distro=args.distro,
            channel=args.channel,
            pages_repo=args.pages_repo,
            branch=args.branch,
            sign=args.sign,
            keyid=args.keyid,
            passphrase=args.passphrase,
            aptly_config=args.aptly_config,
            aptly_root=args.aptly_root,
            verbose=args.verbose,
        )

        publisher.publish(debs_dir=args.debs)

    except KeyboardInterrupt:
        print("\nInterrupted by user", file=sys.stderr)
        sys.exit(130)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        if args.verbose:
            raise
        sys.exit(1)


if __name__ == "__main__":
    main()
