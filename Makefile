.PHONY: help venv run test lint format build install uninstall clean

VENV ?= .venv
PY := $(VENV)/bin/python

help:  ## Show this help
	@grep -E '^[a-z-]+:.*##' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  \033[1m%-10s\033[0m %s\n", $$1, $$2}'

venv:  ## Create a dev virtualenv (reuses system PySide6 if installed)
	python3 -m venv --system-site-packages $(VENV)
	$(PY) -m pip install -e ".[dev]"

run:  ## Launch the GUI from source
	$(VENV)/bin/yt-downloader --debug

test:  ## Run the test suite
	QT_QPA_PLATFORM=offscreen $(PY) -m pytest

lint:  ## Lint with ruff
	$(VENV)/bin/ruff check src tests

format:  ## Auto-fix lint issues
	$(VENV)/bin/ruff check --fix src tests

build:  ## Build sdist and wheel into dist/
	$(PY) -m pip install -q build
	$(PY) -m build

install:  ## Install for the current user (~/.local)
	./scripts/install.sh

uninstall:  ## Remove the user install
	./scripts/uninstall.sh

clean:  ## Remove build artifacts
	rm -rf build dist *.egg-info src/*.egg-info .pytest_cache .ruff_cache
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
