# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.1] - 2025-03-09

### Changed
- Simplified project structure by merging the separate API package into the main integration
- Updated package metadata and dependencies

### Fixed
- Fixed package configuration for PyPI publishing

## [1.0.0] - 2025-03-09

### Added
- Initial release of the EPB (Electric Power Board) integration
- Connect to the EPB API to retrieve energy usage data
- Display energy usage and cost as sensors in Home Assistant
- Automatic data refresh at configurable intervals
- Support for multiple EPB accounts
- Configuration flow for easy setup through the UI

### Fixed
- Resolved type checking issues with Home Assistant's typing helpers
- Fixed dependency conflicts in test requirements

[1.0.1]: https://github.com/asachs01/ha-epb/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/asachs01/ha-epb/releases/tag/v1.0.0
