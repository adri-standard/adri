# Changelog

All notable changes to the Agent Data Readiness Index (ADRI) project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.0] - 2025-05-28

### Added
- **"Facilitation, not enforcement" philosophy** - Major paradigm shift in how ADRI approaches data quality
- Assessment modes system with Discovery, Validation, and Auto modes
- Automatic metadata generation for all five dimensions in Discovery mode
- Business-specific dimension rules for domain-aware quality assessment
- Comprehensive assessment mode documentation
- Unit tests for assessment modes functionality

### Changed
- **Discovery mode now scores based on intrinsic data quality (100% weight)** - No penalties for missing metadata
- Data that previously scored 8/100 for lacking metadata now scores fairly (e.g., 72/100) based on actual quality
- Assessment reports now include generated metadata file paths
- Mode selection logic intelligently chooses between Discovery and Validation
- Report format includes assessment mode information

### Improved
- User experience transformed from penalizing to helpful
- Clear separation between quality analysis (Discovery) and compliance checking (Validation)
- Better alignment with ADRI's vision of enabling AI agent workflows
- More intuitive scoring that reflects actual data quality

## [0.2.0b1-1] - 2025-04-18
### Fixed
- GitHub Actions workflow for release assets
- Dependencies installation in CI pipeline

## [0.2.0b1] - 2025-04-18

### Added
- Comprehensive version management system
- Version compatibility checking in report loading
- Version embedding in reports
- TestPyPI integration for release testing
- Publishing verification scripts

## [0.1.0] - 2025-04-18

### Added
- Initial release of the ADRI framework
- Core assessment functionality with five dimensions:
  - Validity
  - Completeness
  - Freshness
  - Consistency
  - Plausibility
- Support for multiple data source types:
  - File-based data sources
  - Database connections
  - API endpoints
- Report generation in JSON and HTML formats
- Command-line interface
- Interactive assessment mode
- Framework integrations:
  - LangChain integration
  - DSPy integration
  - CrewAI integration
  - Guard integration

[Unreleased]: https://github.com/verodat/agent-data-readiness-index/compare/v0.2.0b1-1...HEAD
[0.2.0b1-1]: https://github.com/verodat/agent-data-readiness-index/compare/v0.2.0b1...v0.2.0b1-1
[0.2.0b1]: https://github.com/verodat/agent-data-readiness-index/compare/v0.1.0...v0.2.0b1
[0.1.0]: https://github.com/verodat/agent-data-readiness-index/releases/tag/v0.1.0

<!-- ---------------------------------------------
TEST COVERAGE
----------------------------------------------
This document's maintenance and accuracy are tested through:

1. CI/CD validation:
   - .github/workflows/publish.yml (version presence check)
   - Ensures version appears in CHANGELOG before release

2. Infrastructure tests:
   - tests/infrastructure/test_version_infrastructure.py (file existence)

3. Release process:
   - RELEASING.md documents update procedure
   - PR review ensures changes documented

4. Format compliance:
   - Follows Keep a Changelog standard
   - Semantic versioning adherence

Complete test coverage details are documented in:
docs/test_coverage/RELEASE_PROCESS_test_coverage.md
--------------------------------------------- -->
