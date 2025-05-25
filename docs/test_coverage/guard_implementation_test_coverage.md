# Test Coverage for adri/integrations/guard.py

This document maps features and functionality in the ADRI guard implementation to their corresponding test coverage.

## Core Decorator Implementation

| Feature | Implementation | Test Files | Test Status |
|---------|---------------|------------|-------------|
| Basic decorator structure | `adri_guarded()` | tests/unit/integrations/test_guard.py | ✅ Covered |
| Function wrapping | `wrapper()` | tests/unit/integrations/test_guard.py | ✅ Covered |

## Parameter Handling

| Feature | Implementation | Test Files | Test Status |
|---------|---------------|------------|-------------|
| Data source extraction from kwargs | `data_source = kwargs[data_source_param]` | tests/unit/integrations/test_guard.py | ✅ Covered |
| Data source extraction from args | `data_source = args[idx]` | tests/unit/integrations/test_guard.py | ⚠️ Partial Coverage |
| Custom parameter name | `data_source_param` | tests/unit/integrations/test_guard.py | ⚠️ Partial Coverage |
| Missing data source handling | `raise ValueError()` | | ❌ No Coverage |

## Cached Report Handling

| Feature | Implementation | Test Files | Test Status |
|---------|---------------|------------|-------------|
| Cached report detection | `report_path.exists()` | tests/unit/test_certification_guard.py:test_guard_uses_cached_report | ✅ Covered |
| Report loading | `AssessmentReport.load_json()` | tests/unit/test_certification_guard.py:test_guard_uses_cached_report | ✅ Covered |
| Disabled report caching | `use_cached_reports=False` | tests/unit/test_certification_guard.py:test_guard_ignores_cached_report_when_disabled | ✅ Covered |
| Invalid report handling | `except Exception as e:` | | ❌ No Coverage |

## Report Age Validation

| Feature | Implementation | Test Files | Test Status |
|---------|---------------|------------|-------------|
| Age limit enforcement | `max_report_age_hours` | tests/unit/test_certification_guard.py:test_age_validation_implementation | ✅ Covered |
| Datetime handling | `datetime.fromisoformat()` | tests/unit/test_certification_guard.py:test_age_validation_implementation | ✅ Covered |
| Detecting expired reports | `datetime.now() - report_time > max_age` | tests/unit/test_certification_guard.py:test_age_validation_implementation | ✅ Covered |
| No age limit behavior | `elif verbose` | tests/unit/test_certification_guard.py | ⚠️ Partial Coverage |

## Fresh Assessment Execution

| Feature | Implementation | Test Files | Test Status |
|---------|---------------|------------|-------------|
| Assessment creation | `assessor = DataSourceAssessor()` | tests/unit/test_certification_guard.py | ✅ Covered |
| Running assessment | `report = assessor.assess_file()` | tests/unit/test_certification_guard.py | ✅ Covered |
| Verbose output | `if verbose: print()` | | ❌ No Coverage |

## Report Saving

| Feature | Implementation | Test Files | Test Status |
|---------|---------------|------------|-------------|
| Saving new reports | `report.save_json()` | tests/unit/test_certification_guard.py:test_guard_saves_new_report | ✅ Covered |
| Disabled report saving | `save_reports=False` | tests/unit/test_certification_guard.py:test_guard_without_save | ✅ Covered |
| Save failure handling | `except Exception as e:` | | ❌ No Coverage |

## Score Validation

| Feature | Implementation | Test Files | Test Status |
|---------|---------------|------------|-------------|
| Overall score check | `report.overall_score < min_score` | tests/unit/integrations/test_guard.py | ✅ Covered |
| Error message for scores | `raise ValueError()` | tests/unit/integrations/test_guard.py | ✅ Covered |
| Dimension score checks | `dimensions` parameter | tests/unit/test_certification_guard.py:test_guard_dimension_specific_requirements | ✅ Covered |
| Multiple dimension validation | `for dim_name, required_score in dimensions.items()` | | ❌ No Coverage |
| Missing dimension handling | `else: raise ValueError()` | | ❌ No Coverage |

## Function Execution

| Feature | Implementation | Test Files | Test Status |
|---------|---------------|------------|-------------|
| Successful execution | `return func(*args, **kwargs)` | tests/unit/integrations/test_guard.py | ✅ Covered |
| Arguments forwarding | `*args, **kwargs` | tests/unit/integrations/test_guard.py | ✅ Covered |

## Coverage Gaps

The following features require additional test coverage:

1. **Error Handling**:
   - Need tests for missing data source parameter
   - Need tests for invalid/corrupted report files
   - Need tests for save failure handling

2. **Multiple Dimensions**:
   - Need tests with multiple dimension requirements
   - Need tests for missing dimension handling

3. **Verbose Mode**:
   - Need tests for verbose output in various scenarios

4. **Edge Cases**:
   - Need tests for non-string assessment_time values
   - Need tests for unusual data source parameter handling

## Next Steps

Based on the identified gaps, the following test development priorities are recommended:

1. Create tests for error handling scenarios
2. Add tests for multiple dimension validations
3. Add tests for verbose mode output and logging

## Test Plan Cross-Reference

| Component | Test Plan Document |
|-----------|-------------------|
| Guard Implementation | Test plan not available |
