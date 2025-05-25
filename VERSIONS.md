# ADRI Version History and Compatibility

This document provides a comprehensive history of ADRI versions, changes to scoring methodology, and compatibility information between versions.

## Version Compatibility Matrix

| From Version | To Version | Score Compatible | Notes |
|--------------|------------|------------------|-------|
| 0.1.x        | 0.1.x      | Yes              | Initial alpha version with consistent scoring methodology |
| 0.1.x        | 0.2.0b1    | Yes              | Beta version maintains scoring compatibility with 0.1.x |
| 0.2.0b1      | 0.2.0b1    | Yes              | Beta release with version management system |

## Detailed Version Information

### 0.2.0b1 (Beta Release)
- **New Features**: Comprehensive version management system
- **Compatibility**: Maintains same scoring methodology as 0.1.0
- **Improvements**:
  - Added version embedding in assessment reports
  - Added compatibility checking when loading reports
  - Added TestPyPI integration for publishing testing
  - Improved documentation and release process
- **Technical Note**: Reports from this version can be safely compared with 0.1.x reports

### 0.1.0 (Initial Release)
- **Baseline Methodology**: First public release with core scoring methodology
- **Dimensions**: 
  - Validity (20%)
  - Completeness (20%)
  - Freshness (20%)
  - Consistency (20%)
  - Plausibility (20%)
- **Scoring System**: Equal weight across all dimensions (20 points each)
- **Report Format**: Basic JSON and HTML reports with radar visualization
- **Technical Note**: Reports from this version can be safely compared with other 0.1.x reports

## Version Migration

No migrations currently required as there is only one major version.

## Scoring Methodology Change Policy

ADRI follows a strict policy regarding changes to the scoring methodology:

1. **MAJOR Version Increments (X.y.z → X+1.y.z)**:
   - Required for any change that affects how scores are calculated
   - Required for dimension weight changes
   - Required for adding or removing core dimensions
   - Reports from different major versions are NOT directly comparable

2. **MINOR Version Increments (x.Y.z → x.Y+1.z)**:
   - Used for adding optional features, tools, or integrations
   - Used for extending dimension calculators with backward compatibility
   - Used for adding new output formats
   - No impact on score calculation

3. **PATCH Version Increments (x.y.Z → x.y.Z+1)**:
   - Bug fixes
   - Documentation improvements
   - Performance optimizations
   - No impact on score calculation or methodology

## Interpreting Assessment Reports

When interpreting ADRI assessment reports, always check which version was used to generate the report. The version information is included in:

1. The JSON report file under the `adri_version` field
2. The HTML report display header
3. The report summary printed to console

Comparing scores between different MAJOR versions without appropriate calibration may lead to incorrect conclusions.

<!-- ---------------------------------------------
TEST COVERAGE
----------------------------------------------
This document's policies and information are tested through:

1. Infrastructure tests:
   - tests/infrastructure/test_version_infrastructure.py (version file consistency)
   - tests/infrastructure/test_version_infrastructure.py (current version presence)

2. Integration tests:
   - tests/integration/test_version_integration.py (version compatibility checking)

3. Unit tests:
   - tests/unit/test_version.py (compatibility functions)
   - tests/unit/test_report.py (version embedding in reports)

4. CI/CD validation:
   - .github/workflows/publish.yml (version consistency validation)

5. Manual verification scripts:
   - scripts/verify_version.py (cross-file version consistency)

Complete test coverage details are documented in:
docs/test_coverage/VERSION_POLICY_test_coverage.md
--------------------------------------------- -->
