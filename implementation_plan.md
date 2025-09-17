# Implementation Plan

Systematic debloating of ADRI project while maintaining 80%+ test coverage on core functionality.

The ADRI project has significant bloat across multiple dimensions: duplicate test infrastructure (109 test files for 24 core files), excessive development tooling (96 files in development/ directory), and redundant configuration. This plan addresses these issues through a phased, safety-first approach that prioritizes core functionality preservation while aggressively removing non-essential components.

## [Overview]

Comprehensive debloating targeting 40-50% project size reduction through systematic removal of duplicate test infrastructure, development tooling excess, redundant examples, and configuration proliferation while maintaining complete core functionality and 80%+ test coverage.

## [Types]

No new type definitions required - this is a removal/consolidation effort.

Core types to preserve:
- AssessmentResult, DimensionScore, FieldAnalysis from assessor.py
- AuditRecord from audit_logger.py  
- All CLI command type annotations
- Configuration manager types

## [Files]

Systematic file removal and consolidation across four phases.

**Files to Remove:**
- `development/testing/` directory (85 test files) - duplicate test infrastructure
- `development/tools/` directory (11 script files) - excessive tooling
- `development/docs/` directory - redundant documentation
- `examples/` directory reduction from 7 to 3 framework examples
- 5-7 bundled standards (reduce from 15 to 8-10 essential ones)
- `tools/adri-setup.py` - redundant with CLI setup command
- `MagicMock/`, `subdir/`, `htmlcov/`, `logs/` directories - development artifacts

**Files to Consolidate:**
- Merge essential tests from `development/testing/tests/unit/` into `tests/unit/`
- Consolidate documentation from multiple sources into single location
- Merge configuration examples and templates

**Files to Preserve (Core):**
- All files in `adri/` package (24 files, 10,712 lines) - core functionality
- Essential tests in `tests/` directory (24 files) - coverage maintenance  
- Core configuration files (pyproject.toml, setup.py)
- LICENSE, README.md, CHANGELOG.md
- Essential bundled standards (8-10 most important)

## [Functions]

No function modifications required - this is purely removal/consolidation.

**Functions to Preserve:**
- All functions in core `adri/` package modules
- All CLI command functions in commands.py
- Essential test functions that provide core coverage
- Configuration management functions

**Functions to Remove:**
- Development-only utility functions
- Redundant test helper functions
- Example-specific utility functions
- Development tooling functions

## [Classes]

No class modifications required - preservation focus.

**Classes to Preserve:**
- DataQualityAssessor, AssessmentEngine, AssessmentResult
- All core classes in assessor.py, audit_logger.py, protection.py
- CLI command classes and configuration managers
- Essential test fixture classes

**Classes to Remove:**
- Development tooling classes
- Example-specific classes  
- Redundant test utility classes

## [Dependencies]

Dependency cleanup through removal of development-only requirements.

**Dependencies to Remove:**
- Development-only packages that are no longer needed after tooling removal
- Example-specific dependencies (if examples are removed)
- Testing dependencies that become redundant after consolidation

**Dependencies to Preserve:**
- All core runtime dependencies in pyproject.toml
- Essential test dependencies for coverage maintenance
- CLI dependencies

## [Testing]

Test consolidation strategy maintaining 80%+ core coverage.

**Testing Approach:**
- Consolidate duplicate tests from `development/testing/` into `tests/`
- Preserve all tests covering core `adri/` package functionality
- Remove redundant test infrastructure and utilities
- Maintain coverage reporting and validation
- Remove example-specific and development-only tests

**Coverage Validation:**
- Run coverage reports before and after each phase
- Ensure core package maintains 80%+ coverage throughout
- Implement rollback procedures if coverage drops

## [Implementation Order]

Phased approach with coverage validation at each step to ensure systematic, safe debloating.

1. **Phase 1: Coverage Audit and Backup**
   - Run comprehensive coverage analysis on current codebase
   - Identify critical test files providing core coverage
   - Create backup of essential tests before any changes
   - Document baseline coverage metrics

2. **Phase 2: Test Infrastructure Consolidation**
   - Merge essential tests from `development/testing/tests/unit/` to `tests/unit/`
   - Remove duplicate test utilities and fixtures
   - Validate coverage remains above 80% after consolidation
   - Remove `development/testing/` directory structure

3. **Phase 3: Development Tooling Removal**
   - Remove `development/tools/` directory (11 files)
   - Remove `development/docs/` redundant documentation
   - Clean up development artifacts (`MagicMock/`, `htmlcov/`, etc.)
   - Update pyproject.toml to remove unused dev dependencies

4. **Phase 4: Example and Configuration Cleanup**
   - Reduce examples from 7 to 3 most important frameworks
   - Consolidate bundled standards from 15 to 8-10 essential ones
   - Remove redundant configuration files
   - Clean up YAML file proliferation

5. **Phase 5: Final Validation and Documentation**
   - Run final coverage report to confirm 80%+ core coverage
   - Update documentation to reflect new project structure
   - Clean up any remaining development artifacts
   - Update CI/CD configurations for new structure

6. **Phase 6: Project Structure Validation**
   - Verify all core functionality works after cleanup
   - Run complete test suite to ensure no regressions
   - Validate CLI commands function correctly
   - Confirm package builds and installs properly
