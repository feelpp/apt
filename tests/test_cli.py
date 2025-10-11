"""Tests for CLI interface."""

from unittest.mock import patch

import pytest


def test_cli_import():
    """Test that CLI module can be imported."""
    from feelpp_aptly_publisher import cli

    assert hasattr(cli, "main")


def test_cli_help():
    """Test CLI help message."""
    from feelpp_aptly_publisher.cli import main

    with patch("sys.argv", ["feelpp-apt-publish", "--help"]):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0


def test_cli_version():
    """Test CLI version flag."""
    from feelpp_aptly_publisher.cli import main

    with patch("sys.argv", ["feelpp-apt-publish", "--version"]):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0


def test_cli_missing_component():
    """Test CLI fails without required --component."""
    from feelpp_aptly_publisher.cli import main

    with patch("sys.argv", ["feelpp-apt-publish"]):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 2  # argparse error


def test_cli_sign_without_keyid():
    """Test CLI fails with --sign but no --keyid."""
    from feelpp_aptly_publisher.cli import main

    with patch("sys.argv", ["feelpp-apt-publish", "--component", "test", "--sign"]):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 2  # argparse error
