.PHONY: help install dev-install test lint format type-check quality clean build publish

help:
	@echo "feelpp-aptly-publisher development commands:"
	@echo ""
	@echo "  make install      - Install package"
	@echo "  make dev-install  - Install package with dev dependencies"
	@echo "  make test         - Run tests"
	@echo "  make lint         - Run flake8 linter"
	@echo "  make format       - Format code with black"
	@echo "  make type-check   - Run mypy type checker"
	@echo "  make quality      - Run all quality checks (lint + type-check + format-check)"
	@echo "  make clean        - Clean build artifacts"
	@echo "  make build        - Build package"
	@echo "  make publish      - Publish to PyPI (requires credentials)"
	@echo "  make test-publish - Publish to Test PyPI"

install:
	uv pip install .

dev-install:
	uv pip install -e ".[dev]"

test:
	pytest -v --cov=feelpp_aptly_publisher --cov-report=term-missing --cov-report=html

lint:
	flake8 src/ tests/

format:
	black src/ tests/

format-check:
	black --check src/ tests/

type-check:
	mypy src/

quality: format-check lint type-check
	@echo "✓ All quality checks passed!"

clean:
	rm -rf build/ dist/ *.egg-info .pytest_cache .coverage htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

build: clean
	python -m build

test-publish: build
	twine check dist/*
	twine upload --repository testpypi dist/*

publish: build
	twine check dist/*
	twine upload dist/*
