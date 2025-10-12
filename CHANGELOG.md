# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2025-10-12

### Added
- Comprehensive integration test suite with 7 tests covering all publishing scenarios
- Enhanced multi-component publishing using aptly's native multi-component support
- Complete README rewrite with detailed publishing guide and examples
- GitHub Actions CI workflow for automated testing with aptly installation
- Git identity configuration for CI integration tests

### Changed
- **Breaking improvement**: Multi-component publishing now uses aptly's native `-component` flag
- Always reads Release file (not InRelease) for reliable component detection
- Always drops and republishes all components together to ensure consistency
- Creates temporary repos from pool for existing components before republishing
- Copies Release to InRelease when using `--skip-signing` to work around aptly limitation

### Fixed
- Multi-component publications now consistently show all components in both Release and InRelease
- Resolved issue where InRelease could be stale when using `--skip-signing`
- Fixed pool file conflicts by always using `--force-overwrite`
- Added database recovery with `aptly db recover` before operations
- Fixed CI code quality checks (black formatting, flake8 linting)

### Technical Details
- Integration tests verify single component, multi-component, updates, and all channels
- Tests use bare git repositories to simulate real GitHub Pages workflow
- CI now runs unit tests first, then installs aptly, then runs integration tests
- Coverage reporting combines results from both unit and integration tests
- All code passes black, flake8, and mypy quality checks

## [1.1.0] - 2025-10-12

### Added
- Multi-component support in InRelease and Release files
- Automatic detection of existing publications and components
- Smart decision logic to use `aptly publish add` for new components
- Preserves existing components when adding or updating others
- Comprehensive logging of component operations
- Documentation for multi-component publishing design

### Changed
- Publishing logic now preserves all components in InRelease file
- Uses `aptly publish add` to add new components to existing publications
- Uses `aptly publish switch` to update existing components
- Uses `aptly publish snapshot` for first-time publications
- Improved error handling and user feedback

### Fixed
- **Critical**: InRelease file now includes ALL components, not just the last published one
- Components are no longer overwritten when publishing different components
- APT can now discover all published packages correctly
- Docker builds from APT repository now work with multiple components

### Technical Details
- Reads InRelease file to detect existing components before publishing
- Chooses appropriate aptly command based on publication state
- Maintains backward compatibility with single-component workflows
- Properly regenerates metadata after adding components

## [1.0.0] - 2025-10-10

### Added
- Initial release of feelpp-aptly-publisher
- Basic component publishing to GitHub Pages APT repository
- Support for multiple channels (stable, testing, pr)
- GPG signing support
- Bootstrap mode for empty components
- Command-line interface with argparse
- Environment variable support for common options
- Comprehensive documentation and examples

### Features
- Publishes .deb packages to GitHub Pages APT repository
- Uses aptly for repository management
- Automatic git operations (clone, commit, push)
- Temporary workspace for aptly operations
- Support for custom aptly configurations
- Verbose logging mode

[1.2.0]: https://github.com/feelpp/apt/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/feelpp/apt/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/feelpp/apt/releases/tag/v1.0.0
