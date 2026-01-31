.PHONY: help install install-dev test test-fast test-coverage lint format check clean build

help:
	@echo "Available targets:"
	@echo "  install       - Install the plugin in editable mode"
	@echo "  install-dev   - Install the plugin with development dependencies"
	@echo "  test          - Run all tests"
	@echo "  test-fast     - Run tests in quiet mode"
	@echo "  test-coverage - Run tests with coverage report"
	@echo "  lint          - Check code for linting issues"
	@echo "  format        - Format code with ruff"
	@echo "  check         - Run lint and tests"
	@echo "  clean         - Remove build artifacts and cache files"
	@echo "  build         - Build distribution packages"

install:
	uv pip install -e .

install-dev:
	uv pip install -e ".[dev]"

test:
	pytest tests/

test-fast:
	pytest -q tests/

test-coverage:
	pytest --cov=beetsplug --cov-report=term-missing tests/

lint:
	ruff check beetsplug/ tests/

format:
	ruff format beetsplug/ tests/
	ruff check --fix beetsplug/ tests/

check: lint test

clean:
	rm -rf build dist *.egg-info
	rm -rf .pytest_cache .ruff_cache
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build:
	uv build
