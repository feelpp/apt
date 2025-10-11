#!/bin/bash
# Setup development environment with uv

set -e

echo "Setting up feelpp-aptly-publisher development environment..."

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "Error: uv is not installed"
    echo "Install it with: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Create virtual environment
echo "Creating virtual environment with uv..."
uv venv

# Activate venv
echo "Activating virtual environment..."
source .venv/bin/activate

# Install package in development mode with dev dependencies
echo "Installing package in development mode..."
uv pip install -e ".[dev]"

echo
echo "✓ Development environment ready!"
echo
echo "To activate the environment, run:"
echo "  source .venv/bin/activate"
echo
echo "Available commands:"
echo "  pytest              - Run tests"
echo "  black src/ tests/   - Format code"
echo "  flake8 src/ tests/  - Lint code"
echo "  mypy src/           - Type check"
echo "  python -m build     - Build package"
