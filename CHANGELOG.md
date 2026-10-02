# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.0.0] - 2026-10-02

### Changed
- **Breaking:** Requires beets 2.12.0 or newer (previously 2.5.1)

### Fixed
- Fixed plugin failing to load on beets 2.12+ (`beets.ui.get_path_formats` removed) and
  failing to build destination paths on beets 2.13+ (`DefaultTemplateFunctions` arguments
  now required) ([#4](https://github.com/finnyb/beets-additionalfiles/issues/4))
- Pattern groups named `comp` or `singleton` are no longer rewritten to beets queries when
  matching `paths`

## [1.0.0] - 2026-02-01

### Added
- Migrated to modern uv build system with hatchling backend
- Added GitHub Actions workflows for CI and PyPI publishing
- Added Makefile with convenient development commands
- Added comprehensive documentation for publishing process
- Added type hints and improved code quality with ruff linting

### Changed
- Updated build system from deprecated uv_build to hatchling
- Updated documentation to reflect modern development workflow
- Improved code formatting and style consistency

### Fixed
- Fixed linting issues with type-only imports

## [0.0.1] - Initial Release

### Added
- Initial fork from beets-extrafiles
- Support for copying additional files during beets import
- Pattern-based file matching with glob support
- Customizable destination paths with template support
- Support for both file and directory copying

[Unreleased]: https://github.com/finnyb/beets-additionalfiles/compare/v2.0.0...HEAD
[2.0.0]: https://github.com/finnyb/beets-additionalfiles/compare/v1.0.0...v2.0.0
[1.0.0]: https://github.com/finnyb/beets-additionalfiles/releases/tag/v1.0.0
[0.0.1]: https://github.com/finnyb/beets-additionalfiles/releases/tag/v0.0.1
