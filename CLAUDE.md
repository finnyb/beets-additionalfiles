# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Do not create explainer documents or other documentation unless specifically asked to (see `AGENTS.md`).

## Commands

Environment is managed with `uv` (venv at `.venv/`):

```bash
uv sync --extra dev            # or: uv pip install -e ".[dev]"
make check                     # lint + tests (what CI runs, minus build)
make lint                      # ruff check beetsplug/ tests/
make format                    # ruff format + ruff check --fix
make test-coverage             # pytest --cov=beetsplug --cov-report=term-missing
uv build                       # build sdist/wheel (hatchling)

# Single test
pytest tests/test_additionalfiles.py::MoveFilesTestCase::test_move_files_single
```

CI (`.github/workflows/ci.yml`) runs ruff, pytest with coverage, and `uv build` on Python 3.10–3.13. After changing dependencies in `pyproject.toml`, run `uv lock` to update `uv.lock`.

## Architecture

The whole plugin is one module: `beetsplug/additionalfiles.py` (installed into beets' `beetsplug` namespace package; enabled in beets config as `additionalfiles`). It is a fork of Holzhaus/beets-extrafiles.

How it works:

1. **Collect.** `AdditionalFilesPlugin` listens for `item_moved` and `item_copied` and only records `(item, source, destination)` tuples. It does no file work during import.
2. **Process on exit.** On `cli_exit`, `gather_files` groups the recorded items by `(albumartist or artist, album)`. For each album, the source and destination roots are the `os.path.commonpath` of the item directories. This is why multi-disc layouts (`CD1/`, `CD2/`) match patterns relative to the parent album directory.
3. **Match.** `match_patterns` globs each configured pattern group under the source root. It skips any extension in `mediafile.TYPES`, since beets imports those itself. It also tracks `_scanned_paths` so an album dir is scanned only once.
4. **Destination.** `get_destination` looks up the pattern group (category) in `paths`. If it finds a template, it formats it with `AdditionalFileModel`/`FormattedAdditionalFileMapping`, a minimal `dbcore.Model` that exposes `artist`, `albumartist`, `album`, `albumpath`, `filename` and `basename`. If not, it falls back to `$albumpath/$filename`. `FormattedAdditionalFileMapping` special-cases `albumpath` so its path separators survive formatting. Only the basename is sanitized.
5. **Act.** `process_items` skips missing sources and existing destinations, then calls `_copy_file` or `_move_file`. Directories (e.g. `scans/`) are copied with `shutil.copytree`. `FilesystemError` is logged and does not raise.

Paths move between `bytes` (beets internals: `bytestring_path`) and `str` (`displayable_path` for glob/shutil). Keep both forms in mind when touching path code. Only Unix-like OSes are supported.

## Tests

`tests/test_additionalfiles.py` uses `unittest.TestCase` classes, run through pytest. `BaseTestCase` builds temp `single/` and `multiple/CD1,CD2/` album trees from `tests/rsrc/full.mp3`. It creates the plugin with a `confuse.RootView` patched over `beetsplug.additionalfiles.beets.plugins.beets.config`. Tests drive the plugin by calling `on_item_moved`/`on_item_copied` and then `on_cli_exit(None)` directly. They do not run a real beets import.

## Conventions

- Don't add code comments unless they're truly necessary, e.g. to explain a non-obvious reason the code can't show. Never comment just to restate what the code does.
- Every module starts with `from __future__ import annotations`. Use modern type hints (`str | None`, `dict[str, Any]`) and Google-style docstrings.
- Ruff: single quotes, line length 100, a broad rule set (see `pyproject.toml`). `PTH` is ignored on purpose because the beets API works with `os.path`, so don't convert to `pathlib`.
- Releases: bump `version` in `pyproject.toml` and move `CHANGELOG.md` `[Unreleased]` entries under the new version. Publishing a GitHub Release triggers the PyPI publish workflow (details in `.github/RELEASE-GUIDE.md` and `.github/PUBLISHING.md`).
