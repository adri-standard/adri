# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive security policy for vulnerability disclosure
- GitHub community templates for improved contributions
- Unified pytest configuration with enhanced test coverage
- Production-ready GitHub Pages documentation deployment

### Fixed
- Jekyll configuration for GitHub Pages deployment
- Pytest configuration conflicts between multiple config files
- Pre-commit configuration improvements

### Changed
- Consolidated test configuration in pyproject.toml
- Enhanced test markers for better categorization
- Improved CI performance with optimized test settings

## [4.0.0] - 2024-12-09

### Added
- Complete framework integration support for major AI frameworks
- Comprehensive data quality assessment engine
- Advanced audit logging capabilities with CSV and structured output
- Flexible configuration management system
- Production-ready CLI interface
- Enterprise-grade data protection and boundary controls
- Automated standard generation from data profiling
- Benchmark comparison and performance testing
- Multi-format data support (CSV, Parquet, JSON)
- Extensive documentation and examples

### Security
- Input validation and sanitization
- Secure configuration defaults
- Data privacy protection mechanisms
- Comprehensive audit trails

### Performance
- Optimized data processing for large datasets
- Efficient memory usage patterns
- Parallel processing capabilities
- Caching and optimization strategies

## [3.1.0] - 2024-11-15

### Added
- Enhanced Verodat enterprise integration
- Improved error handling and user feedback
- Additional validation rules and patterns
- Extended framework compatibility

### Fixed
- Memory optimization for large datasets
- Configuration loading edge cases
- CSV export formatting improvements

## [3.0.0] - 2024-10-20

### Added
- New assessment engine architecture
- Advanced reporting capabilities
- Integration framework foundation
- Comprehensive test suite

### Breaking Changes
- API restructuring for better extensibility
- Configuration format updates
- Module reorganization

### Migration Guide
- See [Migration Guide](docs/migration/v3.0.0.md) for upgrade instructions

## [2.x.x] - Legacy Versions

For changes in version 2.x.x and earlier, please refer to the
[legacy changelog](docs/legacy/CHANGELOG-v2.md).

---

## Release Process

This project follows semantic versioning and automated changelog generation:

1. **Major versions** (x.0.0): Breaking changes, major feature additions
2. **Minor versions** (x.y.0): New features, backwards compatible
3. **Patch versions** (x.y.z): Bug fixes, security updates

### Automated Changelog

Changes are automatically generated from conventional commit messages:
- `feat:` → **Added** section
- `fix:` → **Fixed** section
- `docs:` → **Documentation** updates
- `style:` → **Code style** improvements
- `refactor:` → **Refactoring** changes
- `perf:` → **Performance** improvements
- `test:` → **Testing** updates
- `chore:` → **Maintenance** tasks

### Contributing to Changelog

When submitting PRs, use conventional commit format:
```
type(scope): description

body (optional)

footer (optional)
```

Examples:
- `feat(core): add new assessment algorithm`
- `fix(cli): resolve argument parsing issue`
- `docs(readme): update installation instructions`

For more details, see our [Contributing Guide](CONTRIBUTING.md).

From ca4ecffdc2f275402e139fd249fe1cf5d904fe03 Mon Sep 17 00:00:00 2001
From: TESThomas <trussell@thinkevolvesolve.ie>
Date: Thu, 11 Sep 2025 16:35:25 +0100
Subject: [PATCH 2/3] Fix CI Essential workflow test paths

- Update pyproject.toml testpaths to point to development/testing/tests
- Update CI Essential workflow to run core unit tests instead of examples/demos
- Replace incorrect test commands with development/testing/tests/unit/ execution
- Resolves systematic CI failures blocking PR merges

This fixes the core issue where CI Essential was running example/demo tests
instead of comprehensive core unit tests, causing false CI failures.
---
 .github/workflows/ci-essential.yml | 10 ++--------
 pyproject.toml                     |  2 +-
 2 files changed, 3 insertions(+), 9 deletions(-)

diff --git a/.github/workflows/ci-essential.yml b/.github/workflows/ci-essential.yml
index 163e440..f17dc0c 100644
--- a/.github/workflows/ci-essential.yml
++ b/.github/workflows/ci-essential.yml
@@ -69,14 +69,8 @@ jobs:
         run: |
           echo "🧪 Running core test suite..."
