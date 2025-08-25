# Implementation Plan

## Overview
Ensure ADRI Validator is a fully standalone component with clear boundaries, independent deployment capabilities, and clean separation from external dependencies.

This implementation plan addresses the complete verification and refinement of the ADRI Validator as a standalone component. The validator currently operates as a self-contained Python package (v3.0.1) with bundled standards, but requires cleanup of dependency references, documentation of interfaces, and validation of its independence from the adri-standards package.

## Types
Define clear type interfaces for the ADRI Validator component boundaries.

The following type definitions and interfaces need to be established:
- **StandardFormat**: Interface for YAML standard structure with required fields (standards, requirements, schema sections)
- **AssessmentResult**: Data class for assessment outcomes including overall_score, dimension_scores, and metadata
- **ProtectionConfig**: Configuration type for data protection settings (min_score, failure_mode, cache_duration)
- **AuditRecord**: Structure for audit logging with timestamp, function_name, assessment_result, execution_context
- **VerodatPayload**: Interface for Verodat API integration (optional feature)
- **DimensionScore**: Type for individual dimension scoring (validity, completeness, freshness, consistency, plausibility)

## Files
Files to be created, modified, or verified for standalone operation.

### Files to Modify:
- **setup.py** (line 37): Remove `"adri-standards>=1.0.0"` dependency completely
- **pyproject.toml** (line 36): Remove commented `# "adri-standards>=0.1.0"` line entirely
- **adri/standards/loader.py** (lines 50-56): Remove fallback to ADRI/dev/standards path, rely only on bundled standards
- **adri/config/manager.py**: Review and commit recent changes for audit configuration
- **adri/core/assessor.py**: Review and commit assessment engine updates
- **adri/core/protection.py**: Review and commit protection engine enhancements

### Files to Create:
- **docs/STANDALONE_ARCHITECTURE.md**: Document component boundaries and interfaces
- **docs/DEPLOYMENT_GUIDE.md**: Installation and deployment instructions
- **docs/API_REFERENCE.md**: Complete API documentation for public interfaces
- **.github/workflows/standalone-test.yml**: CI/CD pipeline for standalone testing
- **COMPONENT_MANIFEST.json**: Metadata about the component's capabilities and requirements

### Files to Review:
- **adri/core/audit_logger.py**: New audit logging implementation
- **adri/core/verodat_logger.py**: Verodat integration (optional feature)
- **adri/core/audit_logger_csv.py**: CSV-based audit logging

## Functions
Key functions requiring modification or verification.

### Functions to Modify:
- **StandardsLoader._get_standards_path()** (adri/standards/loader.py): Remove ADRI/dev/standards fallback, use only bundled/env paths
- **DataProtectionEngine.__init__()** (adri/core/protection.py): Ensure audit logger initialization is properly configured
- **AssessmentEngine.assess()** (adri/core/assessor.py): Verify standalone operation without external dependencies

### Functions to Create:
- **verify_standalone_installation()** (adri/utils/verification.py): Runtime check for standalone operation
- **list_bundled_standards()** (adri/standards/__init__.py): Public API to list available bundled standards
- **export_component_metadata()** (adri/utils/metadata.py): Generate component manifest

### Functions to Document:
- **adri_protected()** decorator: Complete parameter documentation and examples
- **DataProtectionEngine.protect_function_call()**: Document all parameters and return types
- **StandardsLoader.load_standard()**: Document standard format requirements

## Classes
Classes requiring updates for standalone operation.

### Classes to Modify:
- **StandardsLoader** (adri/standards/loader.py): Remove external dependencies, ensure bundled-only operation
- **DataProtectionEngine** (adri/core/protection.py): Validate audit logger integration
- **ConfigManager** (adri/config/manager.py): Ensure all config paths are relative to package

### Classes to Create:
- **ComponentBoundary** (adri/core/boundary.py): Interface definition for external integrations
- **StandaloneValidator** (adri/utils/validator.py): Utility to verify standalone installation

### Classes to Document:
- **AuditLogger**: Complete documentation of audit trail functionality
- **VerodatLogger**: Document optional Verodat integration
- **AssessmentEngine**: Document assessment algorithm and scoring

## Dependencies
Verify and clean up all package dependencies.

### Dependencies to Remove:
- **adri-standards**: Remove from setup.py (line 37)
- **adri-standards**: Remove commented reference from pyproject.toml (line 36)

### Core Dependencies (Keep):
- **pandas>=1.5.0**: Data manipulation
- **pyyaml>=6.0**: YAML parsing for standards
- **click>=8.0**: CLI interface
- **pyarrow>=14.0.0**: Parquet file support

### Optional Dependencies (Document):
- **requests**: Only for optional Verodat integration
- **pytest**: Development testing
- **black/flake8/mypy**: Code quality tools

## Testing
Comprehensive testing strategy for standalone validation.

### Test Files to Create:
- **tests/test_standalone_operation.py**: Verify component works without external dependencies
- **tests/test_bundled_standards.py**: Validate all 15 bundled standards load correctly
- **tests/test_deployment.py**: Test installation in clean environment
- **tests/test_component_boundaries.py**: Verify interface contracts

### Test Scenarios:
- Install package in fresh virtual environment
- Run all decorators with bundled standards only
- Verify no network calls unless explicitly configured
- Test audit logging without external dependencies
- Validate CLI commands work standalone

### CI/CD Tests:
- GitHub Actions workflow for standalone testing
- Matrix testing across Python 3.10, 3.11, 3.12
- Deploy to test PyPI for installation verification

## Implementation Order
Logical sequence of changes to ensure successful standalone operation.

1. **Clean up dependencies** (setup.py, pyproject.toml) - Remove all adri-standards references
2. **Update StandardsLoader** - Remove external path fallbacks, ensure bundled-only operation
3. **Review and commit local changes** - Audit logger, Verodat logger, protection engine updates
4. **Create verification utilities** - Standalone validator, component boundary definitions
5. **Document architecture** - Create STANDALONE_ARCHITECTURE.md, API_REFERENCE.md
6. **Write comprehensive tests** - Standalone operation, deployment, boundaries
7. **Set up CI/CD pipeline** - GitHub Actions for automated testing
8. **Create deployment guide** - Installation instructions, configuration options
9. **Generate component manifest** - Metadata about capabilities and requirements
10. **Final validation** - Test complete package in isolated environment
