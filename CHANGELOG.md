# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

No unreleased changes.

## [5.0.0] - 2025-04-05

### Overview
**Enterprise Edition First Release** - verodat-adri v5.0.0 marks the inaugural release of the enterprise edition, forked from community ADRI v4.4.0. This release introduces powerful enterprise features including Verodat cloud integration, event-driven assessment logging, fast-path ID capture, async callback infrastructure, and native workflow orchestration adapters. The package is now published as `verodat-adri` on PyPI while maintaining 100% backward compatibility with `import adri`.

### Breaking Changes
**None** - This release maintains full backward compatibility with community ADRI. All existing code using `import adri` continues to work unchanged.

### Added - Enterprise Features

- **Verodat Cloud Integration** (`src/adri/logging/enterprise.py`)
  - EnterpriseLogger with real-time upload to Verodat platform
  - Reduced batch flush interval: 60s → 5s for faster cloud sync
  - Cloud-based assessment history with team collaboration
  - Advanced analytics, reporting, and compliance audit trails
  - Secure API key authentication with workspace isolation

- **Event-Driven Architecture** (`src/adri/events/`)
  - Thread-safe EventBus with pub/sub pattern for real-time notifications
  - Five event types: CREATED, STARTED, COMPLETED, FAILED, PERSISTED
  - <5ms event publishing overhead with error isolation
  - Support for both sync and async event subscribers
  - Enables real-time workflow coordination and monitoring

- **Fast Path Logging** (`src/adri/logging/fast_path.py`)
  - Immediate assessment ID capture in <10ms (vs 30-60s in community edition)
  - Three storage backends: MemoryBackend, FileBackend, RedisBackend
  - `wait_for_completion()` API for blocking workflows
  - TTL-based automatic cleanup with configurable retention
  - Critical for real-time workflow orchestration integration

- **Unified Logger** (`src/adri/logging/unified.py`)
  - Coordinated dual-write to fast path and slow path (enterprise cloud)
  - Automatic error isolation between logging paths
  - Best of both worlds: immediate IDs + complete cloud logging
  - Graceful degradation when one path fails

- **Async Callback Infrastructure** (`src/adri/callbacks/`)
  - AsyncCallbackManager with configurable thread pool
  - Support for both async and sync callback functions
  - <50ms callback invocation overhead
  - Error handling and timeout management
  - Enables complex post-assessment workflows

- **Workflow Orchestration Adapters** (`src/adri/callbacks/workflow_adapters.py`)
  - PrefectAdapter for Prefect workflow integration
  - AirflowAdapter for Apache Airflow integration
  - Automatic artifact creation and XCom integration
  - Native state updates and failure handling
  - Pre-built callbacks for common workflow patterns

### Added - Package Infrastructure

- **Upstream Synchronization** (UPSTREAM_SYNC.md)
  - Documented workflow for syncing core modules from adri-standard/adri
  - Protected enterprise-only modules list (events, callbacks, enterprise logging)
  - Sync-eligible core modules list (decorator, validator, guard, analysis)
  - Automated weekly upstream check workflow (.github/workflows/upstream-sync-check.yml)
  - Cherry-pick and merge strategies with conflict resolution guidelines

- **Enterprise Features Documentation** (ENTERPRISE_FEATURES.md)
  - Complete feature comparison: community vs enterprise
  - Migration guide from community ADRI
  - Enterprise use case examples and code samples
  - Configuration examples and best practices
  - Performance comparison table

- **Package Rebranding**
  - Package name changed from "adri" to "verodat-adri"
  - Import name remains "adri" for 100% backward compatibility
  - Updated all URLs from adri-standard/adri to Verodat/verodat-adri
  - Enhanced package description with enterprise features
  - Added enterprise-specific classifiers and keywords

### Added - Optional Dependencies

```toml
# New optional dependency groups for enterprise features
redis = ["redis>=5.0.0"]  # For RedisBackend fast path storage
workflows = ["prefect>=2.0.0", "apache-airflow>=2.0.0"]  # Workflow adapters
events = ["verodat-adri[redis,workflows]"]  # Complete event stack
```

### Changed

- **Repository Structure**
  - Repository renamed from adri-enterprise to verodat-adri
  - Upstream remote configured to adri-standard/adri for core sync
  - Enhanced documentation with enterprise differentiation

- **Version Strategy**
  - Enterprise v5.0.0 aligns with community ADRI v5.0.0
  - Fallback version updated to 5.0.0 in setuptools_scm
  - Future releases maintain version parity with community edition

- **Package Metadata**
  - Authors/Maintainers updated to "Verodat"
  - Homepage, Repository, Issues URLs point to Verodat organization
  - Enhanced description emphasizes enterprise capabilities

### Testing

- **All Existing Tests Pass** - 1135+ tests from community ADRI v4.4.0
  - Zero test regressions during enterprise feature integration
  - Full compatibility maintained across all modules
  - Cross-platform testing: Ubuntu, Windows, macOS
  - Python versions: 3.10, 3.11, 3.12, 3.13

- **New Enterprise Tests** - 67 additional tests for enterprise features
  - Event system: 15 tests (96% coverage)
  - Fast path logging: 15 tests (58% coverage)
  - Async callbacks: 20 tests (91% coverage)
  - Integration tests: 17 tests (end-to-end workflows)
  - All tests passing (3 Redis tests skipped when Redis unavailable)

### Performance

Enterprise features meet all performance targets:
- ✅ Fast path writes: <10ms p99 latency
- ✅ Event publishing: <5ms overhead
- ✅ Async callbacks: <50ms invocation
- ✅ Memory overhead: <100MB
- ✅ Enterprise flush: 60s → 5s

### Migration from Community ADRI

**Installation Change:**
```bash
# Old (community)
pip install adri

# New (enterprise)
pip install verodat-adri

# With enterprise features
pip install verodat-adri[events]
```

**Code Changes:**
**None required!** All existing code using `import adri` continues to work:

```python
# This works in both community and enterprise editions
from adri import adri_protected

@adri_protected(standard="standard.yaml")
def process_data(data):
    return {"result": data}
```

**Optional Enterprise Features** (opt-in):
```python
# Add enterprise features gradually
from adri.logging.enterprise import EnterpriseLogger
from adri.logging.fast_path import FastPathLogger, MemoryBackend
from adri.events import EventBus

# Use enterprise logger for cloud sync
logger = EnterpriseLogger(api_base_url="https://api.verodat.com")

# Use fast path for immediate assessment IDs
fast_logger = FastPathLogger(backend=MemoryBackend())

# Use event bus for real-time notifications
event_bus = EventBus()

@adri_protected(
    standard="standard.yaml",
    logger=logger,
    fast_path_logger=fast_logger,
    event_bus=event_bus
)
def process_data(data):
    return {"result": data}
```

### Platform Support

- Cross-platform: Ubuntu Latest, Windows Latest, macOS Latest
- Python versions: 3.10, 3.11, 3.12, 3.13
- Comprehensive testing across 12 platform/Python combinations
- All CI pipelines passing: tests, security, docs

### Documentation

- **README.md**: Updated with enterprise branding and feature comparison
- **ENTERPRISE_FEATURES.md**: Complete enterprise feature documentation
- **UPSTREAM_SYNC.md**: Upstream synchronization workflow guide
- **.github/workflows/upstream-sync-check.yml**: Automated sync monitoring
- **CHANGELOG.md**: This comprehensive v5.0.0 release entry
- All documentation URLs updated to Verodat organization

### Contributors

- @thomas-ADRI - Enterprise feature implementation, package rebranding, documentation
- Verodat Engineering Team - Enterprise architecture and cloud integration

### References

- Enterprise Features: [ENTERPRISE_FEATURES.md](ENTERPRISE_FEATURES.md)
- Upstream Sync: [UPSTREAM_SYNC.md](UPSTREAM_SYNC.md)
- Community ADRI: https://github.com/adri-standard/adri
- verodat-adri Repository: https://github.com/Verodat/verodat-adri
- PyPI Package: https://pypi.org/project/verodat-adri/

### License

Apache 2.0 - Same as community ADRI, with additional enterprise components copyright Verodat.

---

## [4.4.0] - 2025-10-15

### Overview
This release introduces a powerful JSONL log reader with workflow orchestration support, enabling programmatic access to ADRI's audit logs for analysis, monitoring, and integration workflows. The new LogReader class provides filtering, parsing, and workflow correlation capabilities for both assessment and execution logs. Enhanced cross-platform testing documentation and test fixes improve reliability across all supported platforms. All changes maintain full backward compatibility with existing ADRI installations.

### Added
- **JSONL Log Reader**: New `LogReader` class for programmatic audit log access
  - Parse and filter assessment logs from JSONL audit files
  - Parse and filter workflow execution logs for orchestration tracking
  - Support for date range filtering, assessment ID lookup, and workflow correlation
  - Automatic handling of both JSONL and legacy CSV log formats
  - Iterator-based API for memory-efficient processing of large log files
  - Type-safe parsing with validation of log entry schemas
  - Integration with workflow orchestration for execution tracking
  - Comprehensive error handling for corrupted or incomplete log entries

- **Workflow Log Integration**: Enhanced workflow execution log reading capabilities
  - Parse `adri_workflow_executions.jsonl` with execution context
  - Link workflow executions to assessment logs via execution_id
  - Filter by workflow_id, run_id, step_id for targeted analysis
  - Support for parent-child execution relationships
  - Enable audit trail reconstruction across multi-step workflows

- **CLI Enhancement**: Updated `list-assessments` command with log reader
  - Improved performance using LogReader for large log files
  - Consistent formatting and error handling
  - Better support for filtered assessment retrieval
  - Enhanced display of workflow context information

### Fixed
- **Cross-Platform Path Comparison**: Resolved test failures on Windows
  - Updated path comparison logic to use platform-normalized paths
  - Fixed path separator inconsistencies between Windows and Unix systems
  - Enhanced test reliability across Ubuntu, Windows, and macOS
  - Prevents false test failures due to path representation differences

### Documentation
- **Cross-Platform Path Testing Best Practices**: New comprehensive guide
  - Document path handling patterns for cross-platform compatibility
  - Guidelines for writing platform-agnostic path tests
  - Common pitfalls and recommended solutions
  - Testing strategies for Windows/Unix path differences
  - Located at `docs/development/CROSS_PLATFORM_PATH_TESTING.md`

- **Workflow Orchestration Integration Guide**: Enhanced workflow documentation
  - Detailed guide for integrating LogReader with workflow systems
  - Examples of log analysis and monitoring workflows
  - Best practices for audit log processing
  - Located at `docs/WORKFLOW_ORCHESTRATION_INTEGRATION.md`

### Changed
- **Logging Module Structure**: Enhanced with log reading capabilities
  - New `log_reader.py` module in `src/adri/logging/`
  - Updated `__init__.py` to export LogReader class
  - Improved local logging with better JSONL format support
  - Enhanced configuration for log directory management

### Testing
- **Comprehensive Platform Coverage**: All tests passing across 12 platform/Python combinations
  - Ubuntu Latest: Python 3.10, 3.11, 3.12, 3.13 ✅
  - Windows Latest: Python 3.10, 3.11, 3.12, 3.13 ✅
  - macOS Latest: Python 3.10, 3.11, 3.12, 3.13 ✅
  - Total: 1135 tests passing, 8 skipped
  - Coverage: 59.97% overall coverage
  - Security scans: CodeQL ✅, Bandit ✅

- **New Test Suites**: Comprehensive coverage for log reader functionality
  - `tests/unit/logging/test_log_reader.py`: 20+ LogReader core tests
  - `tests/unit/logging/test_log_reader_workflow.py`: 25+ workflow integration tests
  - Cross-platform path comparison tests updated
  - Integration tests verify end-to-end log reading workflows
  - Zero test regressions from previous release

### Migration Notes
- **LogReader Usage**: New programmatic API available for log analysis
  - Existing CLI commands continue to work unchanged
  - New Python API for custom log processing workflows
  - No changes required to existing ADRI integrations
  - Log files remain in JSONL format (introduced in v4.3.0)

- **Cross-Platform Testing**: Enhanced test reliability
  - Existing tests benefit from improved path handling
  - No action required for end users
  - Test suite now more reliable on Windows environments

### Performance
- **Log Reading Efficiency**: Optimized for large audit log files
  - Iterator-based parsing reduces memory footprint
  - Lazy loading of log entries improves startup time
  - Efficient filtering reduces unnecessary parsing
  - Suitable for processing multi-GB log files

### Contributors
- @thomas-ADRI - Feature implementation, documentation, testing
- Community contributors for cross-platform testing feedback

### References
- Log Reader Implementation: `src/adri/logging/log_reader.py`
- Documentation: [Workflow Orchestration Integration](docs/WORKFLOW_ORCHESTRATION_INTEGRATION.md)
- Documentation: [Cross-Platform Path Testing](docs/development/CROSS_PLATFORM_PATH_TESTING.md)
- Tests: `tests/unit/logging/test_log_reader*.py`

## [4.3.0] - 2025-10-13

### Overview
This release introduces powerful extensibility features with assessment callbacks, modernized JSONL logging, and enhanced standard validation. The new callback system enables real-time result capture and custom processing, while JSONL logging replaces CSV format with structured, parseable logs. Standard validation now pre-validates YAML files before runtime, and dynamic rule weights provide flexible dimension scoring. Enhanced visual architecture documentation and assessment ID timing fixes round out this feature-rich release. All changes maintain full backward compatibility with existing ADRI installations.

### Added
- **Assessment Callback System**: New `on_assessment` parameter for capturing assessment results (PR #71)
  - Callback function receives AssessmentResult object for real-time processing
  - Enables custom workflows, notifications, and external system integration
  - Supports both decorator and programmatic API usage
  - Thread-safe callback execution with error isolation
  - Comprehensive documentation and examples for callback patterns
  - Facilitates integration with monitoring, alerting, and analytics systems

- **JSONL Logging Format**: Structured logging replaces CSV format (PR #70)
  - New JSONL (JSON Lines) format for all audit logs with improved parseability
  - Structured data enables easier integration with log aggregation systems
  - Enhanced error handling and recovery for corrupted log entries
  - Backward compatibility maintained through format detection
  - Migration utilities for converting existing CSV logs to JSONL
  - Improved timestamp precision and timezone handling
  - Better support for nested data structures and metadata

- **Standard Validation**: Pre-validation of YAML standards before runtime (PR #66)
  - `StandardValidator` class validates YAML files against schema requirements
  - Early detection of malformed standards prevents runtime failures
  - Comprehensive validation rules for schema compliance
  - Detailed error messages pinpoint validation issues
  - CLI validation command for pre-deployment checks
  - Integration tests ensure validation catches common errors
  - Reduces production issues from invalid standard configurations

- **Dynamic Rule Weights**: Flexible dimension scoring with configurable weights (PR #64-65)
  - Supports custom weight assignments for dimension-specific importance
  - Default equal weighting maintains backward compatibility
  - Weight normalization ensures consistent scoring behavior
  - Configuration-driven weight specification via YAML standards
  - Enhanced documentation with weighting examples and best practices
  - Enables domain-specific quality scoring customization

- **Visual Architecture Documentation**: Three-tier diagram system (PR #68)
  - Tier 1: Simple user flow diagram for quick understanding
  - Tier 2: Medium system flow showing component interactions
  - Tier 3: Complete technical architecture with implementation details
  - Mermaid-based diagrams for easy maintenance and version control
  - Progressive disclosure approach accommodates different audiences
  - Enhanced README and documentation site integration
  - Improves onboarding and system comprehension

### Changed
- **Logging Infrastructure**: Migration from CSV to JSONL format throughout codebase
  - All logging modules updated to support JSONL as primary format
  - Enhanced log parsing utilities for structured data extraction
  - Improved log rotation and retention policies
  - Better integration with modern observability platforms

- **Documentation Enhancements**: Updated guides for new features and best practices
  - Assessment callback usage patterns and examples
  - JSONL log format specification and parsing examples
  - Standard validation workflow and CLI usage
  - Dynamic rule weight configuration guidelines
  - Architecture diagram integration across documentation

- **Configuration Schema**: Extended YAML schema for new capabilities
  - Support for dimension weight specifications
  - Callback configuration options
  - Logging format preferences
  - Validation strictness levels

### Fixed
- **Assessment ID Timing**: Fixed workflow logging correlation (PR #67)
  - Corrected assessment_id generation timing to ensure proper correlation
  - Resolved race conditions in workflow execution logging
  - Enhanced transaction boundaries for atomic log operations
  - Improved foreign key integrity between execution and assessment logs
  - Added comprehensive integration tests for timing validation
  - Ensures reliable audit trail continuity across workflow steps

- **Standard Loading**: Improved error handling for malformed YAML files
  - Enhanced validation messages with actionable guidance
  - Better recovery from partial validation failures
  - Consistent error reporting across validation points

- **Log File Handling**: Robustness improvements for concurrent access
  - Better file locking mechanisms for JSONL logs
  - Improved handling of disk space and I/O errors
  - Enhanced recovery from interrupted write operations

### Testing
- **Comprehensive Platform Coverage**: All tests passing across 12 platform/Python combinations
  - Ubuntu Latest: Python 3.10, 3.11, 3.12, 3.13 ✅
  - Windows Latest: Python 3.10, 3.11, 3.12, 3.13 ✅
  - macOS Latest: Python 3.10, 3.11, 3.12, 3.13 ✅
  - Coverage: 94.2% on new code (58 commits)
  - Zero test regressions: 892 tests passing, 12 skipped
  - Security scans: CodeQL ✅, Bandit ✅

- **New Test Suites**: Comprehensive coverage for all new features
  - `tests/test_decorator.py`: Assessment callback tests
  - `tests/test_logging_local.py`: JSONL logging durability tests
  - `tests/test_standard_validator.py`: Standard validation tests
  - `tests/test_dimension_scoring_integrity.py`: Dynamic weight tests
  - `tests/test_assessment_id_timing.py`: Timing correlation tests
  - Integration tests verify end-to-end functionality

### Migration Notes
- **JSONL Logging Migration**: Existing CSV logs remain compatible
  - New logs automatically written in JSONL format
  - CSV reading still supported for backward compatibility
  - Use provided migration utilities to convert existing logs if needed
  - No action required for most users; migration is transparent

- **Standard Validation**: Optional validation recommended before deployment
  - Run `adri validate-standard <standard.yaml>` to check standards
  - Fix any validation errors before using in production
  - Existing valid standards continue to work without changes

### Contributors
- @thomas-ADRI - Feature implementation, documentation, testing
- Community contributors for feature requests and feedback

### References
- Pull Requests: #71, #70, #68, #67, #66, #64-65
- Documentation: [Assessment Callbacks](docs/docs/users/assessment-callbacks.md)
- Documentation: [JSONL Logging](docs/docs/users/audit-and-logging.md)
- Documentation: [Standard Validation](docs/docs/users/standard-validation.md)
- Architecture: [Visual Diagrams](docs/diagrams/)

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
