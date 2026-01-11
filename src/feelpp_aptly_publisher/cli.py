"""Command-line interface for aptly publisher.

Copyright (c) 2025 University of Strasbourg
Author: Christophe Prud'homme <christophe.prudhomme@cemosis.fr>

This file is part of Feel++ Aptly Publisher.
"""

import argparse
import json
import os
import sys
from pathlib import Path

from .publisher import AptlyPublisher
from .cleaner import AptlyCleaner, RetentionPolicy


def cmd_publish(args):
    """Handle the publish command."""
    if args.sign and not args.keyid:
        print("Error: --keyid is required when --sign is used", file=sys.stderr)
        sys.exit(1)

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
            auto_bump=args.auto_bump,
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


def cmd_cleanup(args):
    """Handle the cleanup command."""
    try:
        repo_path = Path(args.repo_path)
        if not repo_path.exists():
            print(f"Error: Repository path does not exist: {repo_path}", file=sys.stderr)
            sys.exit(1)

        # Load or create retention policy
        if args.policy:
            policy = RetentionPolicy.from_file(Path(args.policy))
        else:
            # Check for include_stable_prereleases attribute
            include_stable = getattr(args, 'include_stable_prereleases', False)
            channel_policies = {
                'stable': {
                    'keep_prereleases': not include_stable,
                    'max_versions': 0,
                },
                'testing': {
                    'keep_prereleases': False,
                    'max_versions': args.max_versions if args.max_versions > 0 else 5,
                },
                'pr': {
                    'keep_prereleases': False,
                    'max_versions': args.max_versions if args.max_versions > 0 else 3,
                    'max_age_days': 30,
                },
            }
            policy = RetentionPolicy(
                prerelease_max_age_days=args.max_age_days,
                max_versions_per_package=args.max_versions,
                channel_policies=channel_policies,
            )

        cleaner = AptlyCleaner(
            repo_path=repo_path,
            policy=policy,
            verbose=args.verbose,
        )

        # Parse channels
        channels = args.channels.split(',') if args.channels else None

        # Find candidates
        packages = cleaner.scan_packages(channels)
        prerelease, version_limit = cleaner.find_cleanup_candidates(packages, channels)

        # Generate report
        report = cleaner.generate_report(prerelease, version_limit)

        if args.json:
            print(json.dumps(report, indent=2))
        else:
            print("=" * 70)
            print("APT REPOSITORY CLEANUP ANALYSIS")
            print("=" * 70)
            print()
            print("Summary:")
            print(f"  Total candidates: {report['summary']['total_candidates']}")
            print(f"  Pre-release packages: {report['summary']['prerelease_candidates']}")
            print(f"  Version limit excess: {report['summary']['version_limit_candidates']}")
            print(f"  Space to reclaim: {report['summary']['total_size_mb']} MB")
            print()

            for channel, pkgs in report['by_channel'].items():
                if pkgs:
                    print(f"[{channel.upper()}] ({len(pkgs)} packages)")
                    for pkg in sorted(pkgs, key=lambda x: (x['name'], x['version'])):
                        print(f"  - {pkg['name']} {pkg['version']} ({pkg['arch']}) - {pkg['age_days']} days old")
                    print()

        # Perform cleanup if not dry-run
        if not args.dry_run:
            result = cleaner.cleanup(prerelease, version_limit, dry_run=False)
            print()
            print(f"Cleanup completed: {result['deleted_count']} packages deleted")
            if result['failed_count'] > 0:
                print(f"Failed to delete: {result['failed_count']} packages")
        else:
            print()
            print("(Dry run - no packages were deleted)")

    except KeyboardInterrupt:
        print("\nInterrupted by user", file=sys.stderr)
        sys.exit(130)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        if args.verbose:
            raise
        sys.exit(1)


def cmd_analyze(args):
    """Handle the analyze command - analyze repository for cleanup candidates."""
    try:
        repo_path = Path(args.repo_path)
        if not repo_path.exists():
            print(f"Error: Repository path does not exist: {repo_path}", file=sys.stderr)
            sys.exit(1)

        # Load or create retention policy
        if args.policy:
            policy = RetentionPolicy.from_file(Path(args.policy))
        else:
            # Build policy from command-line args
            channel_policies = {
                'stable': {
                    'keep_prereleases': not args.include_stable_prereleases,
                    'max_versions': 0,
                },
                'testing': {
                    'keep_prereleases': False,
                    'max_versions': args.max_versions if args.max_versions > 0 else 5,
                },
                'pr': {
                    'keep_prereleases': False,
                    'max_versions': args.max_versions if args.max_versions > 0 else 3,
                    'max_age_days': 30,
                },
            }
            policy = RetentionPolicy(
                prerelease_max_age_days=args.max_age_days,
                max_versions_per_package=args.max_versions,
                channel_policies=channel_policies,
            )

        cleaner = AptlyCleaner(
            repo_path=repo_path,
            policy=policy,
            verbose=args.verbose,
        )

        # Parse channels
        if args.channels:
            channels = args.channels.split(',')
        else:
            channels = ['stable', 'testing', 'pr']

        # Scan and find candidates
        packages = cleaner.scan_packages(channels)
        prerelease, version_limit = cleaner.find_cleanup_candidates(packages, channels)

        # Calculate statistics
        total_size = sum(pkg.size for pkg in packages)
        cleanup_size = sum(pkg.size for pkg in prerelease)

        # Generate report
        report = cleaner.generate_report(prerelease, version_limit)

        if args.json:
            # Enhanced JSON output for CI
            output = {
                'summary': {
                    'total_packages': len(packages),
                    'total_size_mb': round(total_size / (1024 * 1024), 2),
                    'cleanup_candidates': len(prerelease),
                    'cleanup_size_mb': round(cleanup_size / (1024 * 1024), 2),
                    'version_limit_candidates': len(version_limit),
                },
                'cleanup_candidates': [
                    {
                        'name': pkg.name,
                        'version': pkg.version,
                        'arch': pkg.arch,
                        'channel': pkg.channel,
                        'component': pkg.component,
                        'path': str(pkg.path),
                        'size': pkg.size,
                        'age_days': pkg.age_days,
                        'is_prerelease': pkg.is_prerelease,
                    }
                    for pkg in prerelease
                ],
                'version_limit_candidates': [
                    {
                        'name': pkg.name,
                        'version': pkg.version,
                        'arch': pkg.arch,
                        'channel': pkg.channel,
                        'component': pkg.component,
                        'path': str(pkg.path),
                        'size': pkg.size,
                        'age_days': pkg.age_days,
                    }
                    for pkg in version_limit
                ],
                'config': {
                    'max_age_days': args.max_age_days,
                    'channels': channels,
                    'include_stable_prereleases': args.include_stable_prereleases,
                    'max_versions': args.max_versions,
                },
            }
            print(json.dumps(output, indent=2))
        else:
            # Human-readable output
            print("=" * 70)
            print("APT REPOSITORY CLEANUP ANALYSIS")
            print("=" * 70)
            print()
            print("Configuration:")
            print(f"  Max age for pre-releases: {args.max_age_days} days")
            print(f"  Channels analyzed: {', '.join(channels)}")
            print(f"  Include stable pre-releases: {args.include_stable_prereleases}")
            print(f"  Max versions per package: {args.max_versions if args.max_versions > 0 else 'unlimited'}")
            print()
            print("Repository Statistics:")
            print(f"  Total packages: {len(packages)}")
            print(f"  Total size: {total_size / (1024*1024):.2f} MB")
            print()

            if prerelease:
                print(f"Pre-release Packages to Clean ({len(prerelease)} packages, {cleanup_size / (1024*1024):.2f} MB):")
                print("-" * 70)

                # Group by channel
                from collections import defaultdict
                by_channel = defaultdict(list)
                for pkg in prerelease:
                    by_channel[pkg.channel].append(pkg)

                for channel in sorted(by_channel.keys()):
                    pkgs = by_channel[channel]
                    print(f"\n[{channel.upper()}] ({len(pkgs)} packages)")
                    for pkg in sorted(pkgs, key=lambda x: (x.name, x.version)):
                        size_kb = pkg.size / 1024
                        print(f"  - {pkg.name} {pkg.version} ({pkg.arch}) - {pkg.age_days} days old, {size_kb:.1f} KB")
            else:
                print("No pre-release packages found matching cleanup criteria.")

            if version_limit:
                print()
                print(f"Excess Versions to Clean ({len(version_limit)} packages):")
                print("-" * 70)
                for pkg in sorted(version_limit, key=lambda x: (x.channel, x.name, x.version)):
                    print(f"  - [{pkg.channel}] {pkg.name} {pkg.version} ({pkg.arch})")

            print()
            print("=" * 70)
            print("END OF ANALYSIS")
            print("=" * 70)

        # Write to output file if specified
        if args.output:
            output_path = Path(args.output)
            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            if not args.json:
                print(f"\nReport saved to: {output_path}")

        # Output GitHub Actions format if requested
        if args.github_output:
            github_output = os.environ.get('GITHUB_OUTPUT')
            if github_output:
                with open(github_output, 'a') as f:
                    f.write(f"total_packages={len(packages)}\n")
                    f.write(f"cleanup_count={len(prerelease)}\n")
                    f.write(f"cleanup_size_mb={round(cleanup_size / (1024*1024), 2)}\n")
                    f.write(f"version_limit_count={len(version_limit)}\n")

    except KeyboardInterrupt:
        print("\nInterrupted by user", file=sys.stderr)
        sys.exit(130)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        if args.verbose:
            raise
        sys.exit(1)


def cmd_init_policy(args):
    """Initialize a retention policy configuration file."""
    policy = RetentionPolicy()
    output_path = Path(args.output)

    policy.save(output_path)
    print(f"Created retention policy configuration: {output_path}")
    print()
    print("Edit this file to customize cleanup behavior.")


def add_publish_arguments(parser):
    """Add publish command arguments to a parser."""
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
        "--auto-bump",
        action="store_true",
        default=False,
        help="auto-bump Debian revision if package version already exists",
    )


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Feel++ APT Repository Publisher and Cleaner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  publish     Publish packages to APT repository
  cleanup     Analyze and clean up old packages
  init-policy Create a default retention policy configuration

For backwards compatibility, if no command is specified and --component
is provided, the 'publish' command is assumed.

Examples:
  # Publish packages (new style)
  %(prog)s publish --component mmg --channel stable --distro noble --debs ./packages/

  # Publish packages (legacy style, still supported)
  %(prog)s --component mmg --channel stable --distro noble --debs ./packages/

  # Analyze cleanup candidates (dry run)
  %(prog)s cleanup --repo-path ./apt-repo --dry-run

  # Perform cleanup
  %(prog)s cleanup --repo-path ./apt-repo --max-age-days 90

  # Create retention policy config
  %(prog)s init-policy --output retention-policy.json
        """,
    )
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 1.3.0",
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Publish command
    publish_parser = subparsers.add_parser(
        'publish',
        help='Publish packages to APT repository',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Publish packages to stable channel
  %(prog)s --component mmg --channel stable --distro noble --debs ./packages/

  # Bootstrap empty component
  %(prog)s --component new-project --channel testing --distro noble

  # Publish with GPG signing
  %(prog)s --component feelpp --distro jammy --debs ./build/packages/ --sign --keyid YOUR_KEY_ID
        """,
    )
    add_publish_arguments(publish_parser)
    publish_parser.set_defaults(func=cmd_publish)

    # Cleanup command
    cleanup_parser = subparsers.add_parser(
        'cleanup',
        help='Analyze and clean up old packages',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze what would be cleaned (dry run)
  %(prog)s --repo-path ./apt-repo --dry-run

  # Clean pre-releases older than 60 days
  %(prog)s --repo-path ./apt-repo --max-age-days 60

  # Clean only testing channel
  %(prog)s --repo-path ./apt-repo --channels testing

  # Use custom retention policy
  %(prog)s --repo-path ./apt-repo --policy retention-policy.json

  # Output as JSON
  %(prog)s --repo-path ./apt-repo --dry-run --json
        """,
    )
    cleanup_parser.add_argument(
        "--repo-path",
        required=True,
        help="Path to the APT repository (gh-pages checkout)",
    )
    cleanup_parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Only analyze, don't delete (default: true)",
    )
    cleanup_parser.add_argument(
        "--execute",
        action="store_false",
        dest="dry_run",
        help="Actually delete packages (opposite of --dry-run)",
    )
    cleanup_parser.add_argument(
        "--max-age-days",
        type=int,
        default=90,
        help="Maximum age in days for pre-release packages (default: 90)",
    )
    cleanup_parser.add_argument(
        "--max-versions",
        type=int,
        default=0,
        help="Maximum versions to keep per package, 0=unlimited (default: 0)",
    )
    cleanup_parser.add_argument(
        "--channels",
        default=None,
        help="Comma-separated list of channels to analyze (default: all)",
    )
    cleanup_parser.add_argument(
        "--include-stable-prereleases",
        action="store_true",
        default=False,
        help="Include pre-releases in stable channel (default: keep them)",
    )
    cleanup_parser.add_argument(
        "--policy",
        default=None,
        help="Path to retention policy JSON file",
    )
    cleanup_parser.add_argument(
        "--json",
        action="store_true",
        help="Output report as JSON",
    )
    cleanup_parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )
    cleanup_parser.set_defaults(func=cmd_cleanup)

    # Analyze command
    analyze_parser = subparsers.add_parser(
        'analyze',
        help='Analyze repository for cleanup candidates',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze all channels with default settings
  %(prog)s --repo-path ./apt-repo

  # Analyze with custom age limit
  %(prog)s --repo-path ./apt-repo --max-age-days 60

  # Analyze specific channels
  %(prog)s --repo-path ./apt-repo --channels testing,pr

  # Output as JSON for CI integration
  %(prog)s --repo-path ./apt-repo --json --github-output

  # Save report to file
  %(prog)s --repo-path ./apt-repo --output cleanup-report.json
        """,
    )
    analyze_parser.add_argument(
        "--repo-path",
        required=True,
        help="Path to the APT repository (gh-pages checkout)",
    )
    analyze_parser.add_argument(
        "--max-age-days",
        type=int,
        default=90,
        help="Maximum age in days for pre-release packages (default: 90)",
    )
    analyze_parser.add_argument(
        "--max-versions",
        type=int,
        default=0,
        help="Maximum versions to keep per package, 0=unlimited (default: 0)",
    )
    analyze_parser.add_argument(
        "--channels",
        default=None,
        help="Comma-separated list of channels to analyze (default: all)",
    )
    analyze_parser.add_argument(
        "--include-stable-prereleases",
        action="store_true",
        default=False,
        help="Include pre-releases in stable channel (default: keep them)",
    )
    analyze_parser.add_argument(
        "--policy",
        default=None,
        help="Path to retention policy JSON file",
    )
    analyze_parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON",
    )
    analyze_parser.add_argument(
        "--output",
        default=None,
        help="Save report to file",
    )
    analyze_parser.add_argument(
        "--github-output",
        action="store_true",
        help="Write summary to GITHUB_OUTPUT for CI integration",
    )
    analyze_parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )
    analyze_parser.set_defaults(func=cmd_analyze)

    # Init-policy command
    init_policy_parser = subparsers.add_parser(
        'init-policy',
        help='Create a default retention policy configuration',
    )
    init_policy_parser.add_argument(
        "--output",
        default="retention-policy.json",
        help="Output file path (default: retention-policy.json)",
    )
    init_policy_parser.set_defaults(func=cmd_init_policy)

    # For backwards compatibility, also add publish arguments to main parser
    # This allows: feelpp-apt-publish --component foo (without 'publish' subcommand)
    add_publish_arguments(parser)

    args = parser.parse_args()

    # Handle backwards compatibility: if no command but --component provided, assume publish
    if args.command is None:
        if hasattr(args, 'component') and args.component:
            args.func = cmd_publish
        else:
            parser.print_help()
            sys.exit(0)

    # Call the appropriate command function
    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()
        sys.exit(0)


if __name__ == "__main__":
    main()
