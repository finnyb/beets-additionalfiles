# beets-additionalfiles

A plugin for [beets](http://beets.io/) that copies additional files and directories during the import process.

**Note:** This is a fork of [https://github.com/Holzhaus/beets-extrafiles](https://github.com/Holzhaus/beets-extrafiles).

## Installation

### Install from PyPI

The plugin is released on [PyPI](https://pypi.org/project/beets-additionalfiles/) and can be installed via:

    $ uv pip install beets-additionalfiles

Or with pip:

    $ pip3 install --user beets-additionalfiles

### Install manually for development

Clone the repository and install using [uv](https://github.com/astral-sh/uv):

    $ git clone https://github.com/finnyb/beets-additionalfiles.git
    $ cd beets-additionalfiles
    $ uv venv
    $ source .venv/bin/activate  # On Unix/macOS
    $ uv pip install -e ".[dev]"

## Usage

Activate the plugin by adding it to the `plugins` list in beet's `config.yaml`:

```yaml
plugins:
  # [...]
  - additionalfiles
```

Also, you need to add [glob patterns](https://docs.python.org/3/library/glob.html#module-glob) that will be matched.
Patterns match files relative to the root directory of the album, which is the common directory of all the albums files.
This means that if an album has files in `albumdir/CD1` and `albumdir/CD2`, then all patterns will match relative to `albumdir`.

The snippet below will add a pattern group named `all` that matches all files that have an extension.

```yaml
additionalfiles:
    patterns:
        all: '*.*'
```

Pattern names are useful when you want to customize the destination path that the files will be copied or moved to.
The following configuration will match all folders named `scans`, `Scans`, `artwork` or `Artwork` (using the pattern group `artworkdir`), copy them to the album path and rename them to `artwork`:

```yaml
additionalfiles:
    patterns:
        artworkdir:
          - '[sS]cans/'
          - '[aA]rtwork/'
    paths:
        artworkdir: $albumpath/artwork
```


## Development

After cloning the git repository, set up a development environment using `uv`:

    $ git clone https://github.com/finnyb/beets-additionalfiles.git
    $ cd beets-additionalfiles
    $ uv venv
    $ source .venv/bin/activate  # On Unix/macOS
    $ uv pip install -e ".[dev]"

Or use `uv sync` for reproducible builds:

    $ uv sync --extra dev

This will install the plugin in editable mode along with all development dependencies (pytest, ruff, mypy, etc.).

When adding changes, please conform to [PEP 8](https://www.python.org/dev/peps/pep-0008/).
Also, please add docstrings to all modules, functions and methods that you create.

### Quick Commands (using Makefile)

    $ make install-dev    # Install with dev dependencies
    $ make test          # Run all tests
    $ make lint          # Check for linting issues
    $ make format        # Format code
    $ make check         # Run lint + tests
    $ make build         # Build distribution packages

### Code Quality

This project uses [Ruff](https://github.com/astral-sh/ruff) for linting and code formatting:

    $ ruff check beetsplug/ tests/          # Check for linting issues
    $ ruff check --fix beetsplug/ tests/    # Auto-fix issues
    $ ruff format beetsplug/ tests/         # Format code

Or use the Makefile:

    $ make lint    # Check for issues
    $ make format  # Format and fix

### Testing

You should *test every single commit* by running the test suite:

    $ pytest tests/

Or use the Makefile:

    $ make test              # Run all tests
    $ make test-fast         # Run tests in quiet mode
    $ make test-coverage     # Run with coverage report

If a test fails, please fix it *before* you create a pull request.
If you accidentally commit something that still contains errors, please amend, squash or fixup that commit instead of adding a new one.

### Building

To build distribution packages:

    $ uv build

Or use the Makefile:

    $ make build

### Publishing

This project uses automated publishing via GitHub Actions. See [`.github/PUBLISHING.md`](.github/PUBLISHING.md) for detailed instructions on:

- Setting up PyPI Trusted Publishing
- Publishing to TestPyPI for testing
- Creating production releases
- Troubleshooting common issues

## Continuous Integration

This project uses GitHub Actions for CI/CD:

- **CI**: Runs tests and linting on every push and PR
- **TestPyPI**: Publishes release candidates for testing
- **PyPI**: Automatically publishes to PyPI when a GitHub Release is created
