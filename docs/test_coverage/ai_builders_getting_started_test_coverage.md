# Test Coverage for docs/ai-builders/getting-started.md

This document maps features and functionality in the AI Builders getting started guide to their corresponding test coverage.

## Code Examples Test Coverage

| Feature | Code Example | Test File | Coverage Status |
|---------|--------------|-----------|-----------------|
| Basic guard decorator | `@adri_guarded(min_score=80)` | tests/unit/integrations/test_guard.py | ✅ Covered |
| Dimension-specific requirements | `dimensions={"validity": 18}` | tests/unit/test_certification_guard.py:test_guard_dimension_specific_requirements | ✅ Covered |
| Error handling pattern | `except ValueError as e:` | tests/unit/integrations/test_guard.py | ✅ Covered |
| Framework integration examples | LangChain, CrewAI, DSPy examples | tests/unit/integrations/*/test_guard.py | ✅ Covered |
| Pre-certified data usage | `use_cached_reports=True` | tests/unit/test_certification_guard.py:test_guard_uses_cached_report | ✅ Covered |

## Workflow Test Coverage

| Workflow Step | Implementation | Test File | Coverage Status |
|---------------|----------------|-----------|-----------------|
| Quick assessment | `adri assess data.csv` | tests/unit/test_assessor.py | ✅ Covered |
| Guard implementation | `@adri_guarded` decorator | tests/unit/integrations/test_guard.py | ✅ Covered |
| Framework integration | Guard wrapping patterns | tests/unit/integrations/*/test_guard.py | ✅ Covered |
| Error handling | Quality threshold enforcement | tests/unit/integrations/test_guard.py | ✅ Covered |

## Audience-Specific Code Examples

| Audience Tag | Example Type | Validation Rule | Coverage Status |
|--------------|--------------|-----------------|-----------------|
| [AI_BUILDER] | Guard implementation | Must be fully executable | ✅ Validated |
| [AI_BUILDER] | Framework integration | Must work with current API | ✅ Validated |
| [AI_BUILDER] | Error handling | Must demonstrate real patterns | ✅ Validated |

## Success Criteria Test Coverage

| Success Criterion | Implementation | Test File | Coverage Status |
|-------------------|----------------|-----------|-----------------|
| Agent protection from bad data | Guard blocking mechanism | tests/unit/integrations/test_guard.py | ✅ Covered |
| Quality threshold enforcement | Min score validation | tests/unit/integrations/test_guard.py | ✅ Covered |
| Framework integration | LangChain/CrewAI/DSPy guards | tests/unit/integrations/*/test_guard.py | ✅ Covered |
| Error diagnostics | Detailed error messages | tests/unit/integrations/test_guard.py | ⚠️ Partial Coverage |

## Coverage Gaps

### High Priority
- **Error message content validation**: Need tests that verify specific error message content matches documentation examples
- **End-to-end workflow testing**: Need integration tests that follow the complete 5-minute workflow

### Medium Priority
- **Performance benchmarks**: Need tests that verify guard overhead is within acceptable limits
- **Real-world data testing**: Need tests with actual problematic datasets

### Low Priority
- **Documentation link validation**: Ensure all referenced links work correctly
- **Code example freshness**: Automated checks that examples stay current with API changes

## Recommendations

1. **Add error message content tests**: Verify that error messages match the examples shown in documentation
2. **Create workflow integration tests**: Test the complete 5-minute getting started workflow
3. **Add performance regression tests**: Ensure guard overhead remains minimal
4. **Implement example freshness checks**: Automated validation that code examples work with current ADRI version

## Test Implementation Status

| Test Category | Status | Priority |
|---------------|--------|----------|
| Basic functionality | ✅ Complete | High |
| Framework integration | ✅ Complete | High |
| Error handling | ⚠️ Partial | High |
| Performance | ❌ Missing | Medium |
| Documentation links | ❌ Missing | Low |

## Related Test Plans

| Component | Test Plan Document |
|-----------|-------------------|
| Guard Implementation | [guard_implementation_test_coverage.md](guard_implementation_test_coverage.md) |
| Framework Integrations | [IMPLEMENTING_GUARDS_test_coverage.md](IMPLEMENTING_GUARDS_test_coverage.md) |
| Certification Guards | [certification_guard_test_plan_coverage.md](certification_guard_test_plan_coverage.md) |

---

**Last Updated**: 2025-06-20  
**Coverage Assessment**: 85% - Good coverage with identified gaps for improvement
