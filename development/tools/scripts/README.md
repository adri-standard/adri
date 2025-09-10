# Scripts Directory

This directory contains development and release management scripts organized by purpose.

## Directory Structure

### `/core/` - Core Development Scripts
Essential scripts for day-to-day development and environment setup:

- `setup-dev-environment.sh` - Set up development environment
- `test-local.sh` - Run local tests
- `validate_version.py` - Validate version numbers
- `check_code_quality.py` - Code quality checks
- `cli.py` - CLI utilities
- `download_previous_benchmark.py` - Download benchmark data

### `/release/` - Release Management Scripts
Scripts for managing releases and PyPI publishing:

- `prepare_releases.py` - Prepare release packages
- `prepare_release.py` - Single release preparation
- `rollback_release.py` - Rollback failed releases
- `pypi_manager.py` - PyPI package management
- `publish_pypi.sh` - Publish to PyPI
- `update_release_registry.py` - Update release registry
- `update_version_tracking.py` - Version tracking updates

### `/testing/` - Testing Scripts
Scripts for comprehensive testing and benchmarking:

- `test_package.py` - Package testing
- `test_local.py` - Local testing utilities
- `test_prepare_releases.py` - Test release preparation
- `test_rollback_release.py` - Test rollback functionality
- `compare_benchmarks.py` - Benchmark comparison

## Usage

All scripts maintain their original functionality and can be executed from their new locations:

```bash
# Core development
./scripts/core/setup-dev-environment.sh
./scripts/core/test-local.sh

# Release management
./scripts/release/prepare_releases.py
./scripts/release/publish_pypi.sh

# Testing
./scripts/testing/test_package.py
./scripts/testing/compare_benchmarks.py
```

## Migration Notes

This reorganization improves script discoverability and maintenance without breaking existing functionality. All scripts preserve their original behavior and command-line interfaces.
