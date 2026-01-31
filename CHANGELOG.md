# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

[Unreleased]: https://github.com/finnyb/beets-additionalfiles/compare/v0.0.1...HEAD
[0.0.1]: https://github.com/finnyb/beets-additionalfiles/releases/tag/v0.0.1
