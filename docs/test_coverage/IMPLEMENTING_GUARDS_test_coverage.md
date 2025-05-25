# Test Coverage for IMPLEMENTING_GUARDS.md

This document maps features and claims in IMPLEMENTING_GUARDS.md to their corresponding test coverage.

## Basic Guard Implementation

| Feature | Implementing Code | Test Files | Test Status |
|---------|------------------|------------|-------------|
| Basic `adri_guarded` decorator | adri/integrations/guard.py | tests/unit/integrations/test_guard.py | ✅ Covered |
| Minimum score enforcement | adri/integrations/guard.py | tests/unit/integrations/test_guard.py | ✅ Covered |
| ValueError when quality insufficient | adri/integrations/guard.py | tests/unit/integrations/test_guard.py | ✅ Covered |
| Custom parameter name | adri/integrations/guard.py | tests/unit/integrations/test_guard.py | ⚠️ Partial Coverage |

## Dimension-Specific Guards

| Feature | Implementing Code | Test Files | Test Status |
|---------|------------------|------------|-------------|
| Dimension-specific requirements | adri/integrations/guard.py | tests/unit/test_certification_guard.py:test_guard_dimension_specific_requirements | ✅ Covered |
| Multiple dimension requirements | adri/integrations/guard.py | | ❌ No Coverage |

## Pre-certified Data Usage

| Feature | Implementing Code | Test Files | Test Status |
|---------|------------------|------------|-------------|
| Cached report usage | adri/integrations/guard.py | tests/unit/test_certification_guard.py:test_guard_uses_cached_report | ✅ Covered |
| Ignoring cached reports when disabled | adri/integrations/guard.py | tests/unit/test_certification_guard.py:test_guard_ignores_cached_report_when_disabled | ✅ Covered |
| Report age validation | adri/integrations/guard.py | tests/unit/test_certification_guard.py:test_age_validation_implementation | ✅ Covered |
| Saving new reports | adri/integrations/guard.py | tests/unit/test_certification_guard.py:test_guard_saves_new_report | ✅ Covered |
| Not saving reports when disabled | adri/integrations/guard.py | tests/unit/test_certification_guard.py:test_guard_without_save | ✅ Covered |
| Data provider certification process | adri/report.py | | ❌ No Coverage |
| Verbose mode | adri/integrations/guard.py | | ❌ No Coverage |

## Framework-Specific Guards

| Feature | Implementing Code | Test Files | Test Status |
|---------|------------------|------------|-------------|
| LangChain Integration | adri/integrations/langchain/__init__.py | | ❌ No Coverage |
| CrewAI Integration | adri/integrations/crewai/__init__.py | | ❌ No Coverage |
| DSPy Integration | adri/integrations/dspy/__init__.py | | ❌ No Coverage |

## Advanced Guard Configuration

| Feature | Implementing Code | Test Files | Test Status |
|---------|------------------|------------|-------------|
| Custom Assessor Configuration | adri/integrations/guard.py | | ❌ No Coverage |
| Guard Chains | adri/integrations/guard.py | | ❌ No Coverage |

## Error Handling

| Feature | Implementing Code | Test Files | Test Status |
|---------|------------------|------------|-------------|
| Diagnostic error messages | adri/integrations/guard.py | tests/unit/integrations/test_guard.py | ⚠️ Partial Coverage |

## Coverage Gaps

The following features require additional test coverage:

1. **Framework Integrations**:
   - Need tests for LangChain, CrewAI, and DSPy integrations
   - Need tests for wrapping functions/pipelines with guards
   
2. **Advanced Guard Features**:
   - Need tests for custom assessor configurations with guards
   - Need tests for guard chains (multiple decorators)

3. **Error Handling**:
   - Need more comprehensive tests for error message content
   - Need tests for different error scenarios (various quality issues)

4. **Miscellaneous**:
   - Need tests for verbose mode output

## Next Steps

Based on the identified gaps, the following test development priorities are recommended:

1. Create integration tests for framework integrations
2. Add tests for advanced guard configurations
3. Enhance error handling tests
4. Add test for verbose mode output

## Test Plan Cross-Reference

| Guard Component | Test Plan Document |
|-----------------|-------------------|
| Certification Guard | Test plan not available |
