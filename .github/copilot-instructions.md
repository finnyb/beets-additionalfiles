# Copilot Instructions for beets-additionalfiles

## Project Overview

This is a **beets plugin** called `beets-additionalfiles` that copies additional files and directories during the beets import process. The plugin is written in modern Python 3.10+ and extends the beets music library management system.

**Key Facts:**
- Plugin namespace: `beetsplug`
- Main module: `beetsplug/additionalfiles.py`
- Targets: Python 3.10+, Unix-like OS only (no Windows support)
- Dependencies: `beets>=2.5.1`, `mediafile>=0.12.0`, `setuptools`
- Dev Dependencies: `pytest>=7.0.0`, `pytest-cov>=4.0.0`, `ruff>=0.1.0`, `mypy>=1.0.0`

## Code Style & Conventions

### Modern Python Standards (3.10+)
- Use `from __future__ import annotations` for all modules
- Add comprehensive type hints to all functions and methods
- Use modern union syntax: `str | None` instead of `Optional[str]`
- Use built-in collection types: `dict[str, Any]`, `list[str]`, `set[int]`
- Use f-strings for string formatting
- Use `super()` without arguments
- Annotate class variables with `ClassVar` when appropriate

### Beets Plugin Patterns
- Extend `beets.plugins.BeetsPlugin` for plugin classes
- Use `beets.dbcore.db.Model` for database models
- Use `beets.ui` for command-line interactions
- Use `beets.util` for utility functions
- Always handle both bytes and unicode strings properly (use `.decode('utf-8', 'ignore')` when needed)

### Code Quality
- Run `ruff check beetsplug/ tests/` before committing
- Use `ruff format beetsplug/ tests/` to format code
- Follow single-quote style for strings
- Line length: 100 characters max
- Use the Makefile for convenience: `make check`, `make lint`, `make format`

## Testing

- **Framework**: Use Python's built-in `unittest` or `pytest`
- **Location**: Place tests in `tests/` directory
- **Test Files**: Name test files with `test_` prefix (e.g., `test_additionalfiles.py`)
- **Test Resources**: Store test resources in `tests/rsrc/`
- **Coverage**: Aim for comprehensive test coverage of plugin functionality

### Running Tests
```bash
# Using Makefile (recommended)
make test                 # Run all tests
make test-coverage        # Run tests with coverage report
make test-fast           # Run tests in quiet mode

# Using pytest directly
python -m pytest tests/
python -m pytest tests/test_additionalfiles.py
python -m pytest --cov=beetsplug tests/
```

## Dependencies & Environment

### Virtual Environment
- Use `uv` for dependency and environment management (preferred)
- Standard venv location: `.venv/`
- All dependencies are managed in `pyproject.toml`

### Installing for Development
```bash
# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"

# Or use uv sync (if using uv.lock)
uv sync --extra dev

# Install just the package in editable mode
uv pip install -e .
```

### Adding Dependencies
- **Runtime dependencies**: Add to `[project.dependencies]` in `pyproject.toml`, then run `uv pip install -e .`
- **Test dependencies**: Add to `[project.optional-dependencies.test]` in `pyproject.toml`
- **Dev dependencies**: Add to `[project.optional-dependencies.dev]` in `pyproject.toml`
- Keep version constraints minimal but specify minimum versions when needed
- Use `uv add package-name` to add dependencies automatically
- Use `uv add --dev package-name` for dev dependencies

### Updating Dependencies
```bash
# Update all dependencies
uv pip compile pyproject.toml -o requirements.txt
uv pip sync requirements.txt

# Or use uv lock for reproducible builds
uv lock
uv sync
```

## Compatibility Considerations

### Python Version Support
- Minimum Python version: 3.10+
- Uses modern Python features: PEP 604 union syntax, PEP 585 built-in types
- Type hints use `from __future__ import annotations`

### OS Compatibility
- **Supported**: Unix-like systems (Linux, macOS)
- **Not supported**: Windows
- Use `os.path` for path operations (automatically handles OS differences)
- Use `os.sep` for path separators (handles bytes vs strings)

### String Handling
- Always handle both `bytes` and `str` types properly
- Use type checks: `isinstance(value, bytes)`
- Decode bytes with: `value.decode('utf-8', 'ignore')`
- Encode strings with: `value.encode('utf-8')`

## Common Patterns

### File Operations
```python
# Use shutil for file operations
import shutil
shutil.copy2(src, dst)  # Preserve metadata

# Use glob for pattern matching
import glob
files = glob.glob(pattern)

# Use os.path for path operations
import os
os.path.join(base, path)
os.path.dirname(path)
os.path.exists(path)
```

### Beets Integration
```python
# Access plugin configuration
config = self.config['setting_name'].get()

# Log messages
self._log.info('Message')
self._log.debug('Debug message')
self._log.error('Error message')

# Handle items and albums
for item in album.items():
    # Process item
    pass
```

### Error Handling
- Use try/except for file operations
- Import `traceback` for detailed error logging
- Always log errors appropriately using beets logging

## Documentation

- **README.md**: Keep installation, usage, and configuration instructions up to date
- **Docstrings**: Document all public classes, methods, and functions
- **Comments**: Use inline comments sparingly, prefer self-documenting code
- **Configuration**: Document all configuration options in README

## Git Workflow

- Write clear, descriptive commit messages
- Keep commits focused and atomic
- Reference issue numbers in commits when applicable

## Code Review Checklist

When suggesting or reviewing code changes:
- [ ] Follows PEP 8 style guidelines
- [ ] Uses modern Python 3.10+ syntax (type unions, built-in collection types)
- [ ] Has comprehensive type hints with `from __future__ import annotations`
- [ ] Has appropriate docstrings (Google style)
- [ ] Handles both bytes and str types correctly
- [ ] Compatible with Python 3.10+
- [ ] Includes tests for new functionality
- [ ] Updates documentation if needed
- [ ] No hardcoded paths or platform-specific code
- [ ] Proper error handling and logging
- [ ] Follows existing code patterns in the project
- [ ] Passes `make check` (lint, format, and tests)

## Security & Best Practices

- Validate file paths to prevent directory traversal
- Use `shutil.copy2()` instead of `shutil.copy()` to preserve metadata
- Never use `eval()` or `exec()` on user input
- Sanitize user input before using in file operations
- Use context managers (`with` statements) for file operations

## Performance Considerations

- Avoid unnecessary file system operations
- Use generators for large collections
- Cache expensive computations when appropriate
- Be mindful of memory usage with large music libraries

## When Making Changes

1. **Understand the context**: This is a plugin for beets, so always consider how it integrates with the beets ecosystem
2. **Maintain backwards compatibility**: Don't break existing configurations or workflows
3. **Test thoroughly**: Especially test with different file types, encodings, and edge cases
4. **Update version**: Bump version in `pyproject.toml` for releases
5. **Document**: Update README.md if adding new features or changing behavior
6. **Dependencies**: Use `uv` to manage dependencies via `pyproject.toml`

