# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

No unreleased changes.

## [4.2.0] - 2025-10-07

### Overview
This release introduces compliance-grade workflow orchestration with CSV-based audit logging for multi-step AI workflows. The new WorkflowLogger provides enterprise-ready audit trails that track workflow execution context, data provenance, and reasoning steps across complex AI pipelines. All changes maintain full backward compatibility with existing ADRI installations.

### Added
- **Workflow Orchestration Logging**: New `WorkflowLogger` class for compliance-grade CSV audit trails
  - Thread-safe CSV logging for workflow executions with automatic file rotation
  - Two new audit log files: `adri_workflow_executions.csv` and `adri_workflow_provenance.csv`
  - Foreign key relationships between executions, assessments, and reasoning logs
  - Optional workflow context tracking via `workflow_context` parameter in decorator and CLI
  - Supports complex multi-step workflows with execution_id linking
  - Closes #62

- **Reasoning Mode**: New reasoning validation and logging capabilities for AI decision-making workflows
  - `ReasoningLogger` class for tracking AI prompts and responses with structured validation
  - Reasoning mode support in `@adri_protected` decorator and CLI
  - Validation of reasoning steps against standards (prompts and responses)
  - Integration with workflow execution tracking via execution_id
  - Two new CSV audit files: `adri_reasoning_prompts.csv` and `adri_reasoning_responses.csv`

- **Enhanced Assessment Logging**: Extended `LocalLogger` with workflow orchestration columns
  - New columns: `execution_id`, `workflow_id`, `run_id`, `step_id`, `parent_execution_id`
  - Enables linking assessments to workflow executions for complete audit trails
  - Backward compatible with existing assessment logs (new columns are optional)

- **Cross-Platform UTF-8 Enforcement**: Robust encoding validation across all platforms
  - Pre-commit hook (`check-utf8-encoding.py`) validates file encodings before commits
  - Automated fix script (`fix-encoding-issues.py`) for bulk encoding corrections
  - Enhanced file I/O with explicit UTF-8 encoding declarations throughout codebase
  - Resolves Windows encoding issues that caused intermittent test failures

- **New Validation Standards**: Four new YAML standards for workflow and reasoning validation
  - `adri_execution_standard.yaml`: Validates workflow execution metadata
  - `adri_provenance_standard.yaml`: Validates data source provenance tracking
  - `adri_reasoning_prompts_standard.yaml`: Validates AI prompt structure and content
  - `adri_reasoning_responses_standard.yaml`: Validates AI response quality and format
  - Two additional example standards: `ai_decision_step_standard.yaml`, `ai_narrative_step_standard.yaml`

- **Comprehensive Documentation**: New guides for workflow orchestration and reasoning mode
  - `docs/WORKFLOW_ORCHESTRATION.md`: Complete guide to workflow logging features
  - `docs/development/CROSS_PLATFORM_BEST_PRACTICES.md`: Platform compatibility guidelines
  - `docs/development/github-tag-protection-setup.md`: Release management procedures
  - `docs/docs/users/reasoning-mode-guide.md`: User guide for reasoning validation
  - `docs/docs/users/tutorial-testing-reasoning-mode.md`: Step-by-step tutorial
  - Updated API reference with WorkflowLogger and ReasoningLogger documentation

- **Examples and Testing**: Comprehensive examples and 17 new tests with 93.66% coverage
  - `examples/workflow_orchestration_example.py`: Production-ready workflow example
  - `tests/test_workflow_logging.py`: 17 comprehensive WorkflowLogger tests
  - `tests/test_workflow_context_validation.py`: Workflow context validation tests
  - `tests/test_reasoning_logger.py`: ReasoningLogger comprehensive tests
  - `tests/test_reasoning_validator.py`: Reasoning validation tests
  - `tests/integration/test_reasoning_workflow.py`: End-to-end reasoning workflow tests
  - `tests/verification/test_final_integration.py`: Complete integration verification
  - Zero test regressions (884 tests passing, 12 skipped)

### Changed
- **CSV Schema Enhancements**: Updated schema with relational integrity and new columns
  - Assessment logs now include workflow execution linking columns
  - All CSV files support optional workflow context for audit trail continuity
  - Maintains backward compatibility with existing log readers

- **Configuration Updates**: Enhanced pyproject.toml with workflow and reasoning dependencies
  - Updated test paths and coverage configurations
  - Added pre-commit hook configurations for encoding validation
  - Improved development workflow automation

- **Documentation Site**: Updated with workflow orchestration and reasoning mode content
  - New user guides accessible through documentation navigation
  - Enhanced API reference with complete workflow examples
  - Updated contribution guidelines with encoding best practices

### Fixed
- **Cross-Platform Encoding Issues**: Resolved Windows-specific encoding failures
  - Fixed 100+ file encoding declarations to use explicit UTF-8
  - Eliminated intermittent test failures on Windows CI runners
  - Improved file I/O reliability across Ubuntu, Windows, and macOS
  - Enhanced error messages for encoding-related issues

- **File I/O Consistency**: Standardized file operations across all modules
  - Consistent use of `encoding='utf-8'` in all open() calls
  - Proper handling of newline characters across platforms
  - Improved CSV writing with configurable line terminators

### Testing
- **Comprehensive Platform Coverage**: All 884 tests passing across all environments
  - Ubuntu Latest: Python 3.10, 3.11, 3.12, 3.13 ✅
  - Windows Latest: Python 3.10, 3.11, 3.12, 3.13 ✅
  - macOS Latest: Python 3.10, 3.11, 3.12, 3.13 ✅
  - CodeQL security scanning: ✅
  - Bandit security analysis: ✅
  - Coverage: 93.66% on new code

### Contributors
- @thomas-ADRI - Feature implementation, documentation, testing
- @chatgpt-codex-connector - Code review and validation

### References
- Pull Request: #62
- Related Issues: Workflow orchestration feature request
- Documentation: [Workflow Orchestration Guide](docs/WORKFLOW_ORCHESTRATION.md)

## [4.1.4] - 2025-06-10

**Note:** This release supersedes v4.1.1, v4.1.2, and v4.1.3 due to TestPyPI tombstone restrictions and release workflow fixes. Core functionality is identical to v4.1.1, with Python 3.13 support added.

### Added
- **Python 3.13 Support**: Added compatibility with Python 3.13 (released October 2024)
  - Updated CI/CD test matrices to include Python 3.13
  - Added Python 3.13 classifier to package metadata
  - All 822 tests passing on Python 3.13 across Ubuntu, Windows, macOS
  - Closes #48

### Fixed
- **Issue #35 Regression**: Restored CLI/Decorator parity after test consolidation
  - Re-implemented `standard_path` tracking in AssessmentResult for transparency
  - Updated DataQualityAssessor to capture and pass standard file path used
  - Fixed ValidationPipeline to properly propagate standard_path parameter
  - Enhanced CLI to display which standard file was used in assessments
  - Updated audit logging to include `standard_path` in all CSV logs
  - Added `TestStandardPathConsistency` to prevent future regressions
  - Updated ADRI audit log standard YAML with new `standard_path` field
  - Ensures CLI, Decorator, Config, and Audit logs all use identical standard paths

### Changed
- Enhanced diagnostic logging in DataQualityAssessor and ValidationPipeline
  - Added detailed INFO-level logging for standard loading and dimension scoring
  - Helps users debug assessment issues and understand scoring process
  - Controlled via standard Python logging configuration

## [4.1.0] - 2025-05-10

### Overview
First public release of ADRI (AI Data Reliability Intelligence) - a comprehensive data quality framework for AI applications.

### Added
- Complete framework integration support for major AI frameworks (LangChain, LlamaIndex, CrewAI)
- Comprehensive security policy and GitHub community templates
- Production-ready documentation with GitHub Pages deployment
- Enhanced test coverage with 816 passing tests across multiple platforms

### Fixed
- **Issue #35**: Resolved CLI vs Decorator assessment consistency
  - Fixed discrepancy where identical data and standards produced different quality scores
  - Both CLI and decorator now use unified assessment and threshold resolution
  - Added comprehensive integration tests for consistency validation

### Changed
- **Governance Enhancement**: Simplified standard resolution to name-only approach
  - Decorator now accepts only standard names (not file paths) for improved security
  - Standard file locations determined by environment configuration (dev/prod)
  - Ensures centralized control and prevents path-based security issues
- Consolidated test configuration for better maintainability
- Improved CI/CD performance with optimized test settings
- Enhanced code quality through internal refactoring

### Platform Support
- Cross-platform compatibility: Ubuntu, Windows, macOS
- Python versions: 3.10, 3.11, 3.12
- Comprehensive testing across 9 platform/Python combinations

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
