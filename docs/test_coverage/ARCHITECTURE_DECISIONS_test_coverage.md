# Test Coverage for ARCHITECTURE_DECISIONS.md

This document maps the architecture decisions and their implementations to corresponding test coverage.

## Single Dataset Assessment Decision

| Implementation | Test Files | Test Status |
|----------------|------------|-------------|
| Single dataset focus | tests/unit/test_assessor.py | ✅ Covered |
| No cross-dataset validation | N/A (architectural constraint) | ✅ By Design |
| Universal template support | tests/unit/templates/ | ✅ Covered |
| Simple, focused protocol | tests/unit/test_assessor.py | ✅ Covered |

## Agent Views Pattern

| Feature | Test Files | Test Status |
|---------|------------|-------------|
| Denormalized view creation | tests/unit/examples/test_09_agent_view_pattern.py | ❌ No Coverage |
| Custom templates for views | tests/unit/examples/test_09_agent_view_pattern.py | ❌ No Coverage |
| Single dataset assessment of views | tests/unit/examples/test_09_agent_view_pattern.py | ❌ No Coverage |

## Architecture Validation

| Aspect | Test Files | Test Status |
|--------|------------|-------------|
| Cannot assess multiple files simultaneously | tests/unit/test_assessor.py | ✅ Covered |
| Template universality | tests/unit/templates/test_yaml_template.py | ✅ Covered |
| Integration simplicity | tests/integration/ | ✅ Covered |

## Coverage Gaps

The following architectural aspects require test coverage:

1. **Agent View Pattern Tests**:
   - Test creation of denormalized views
   - Test assessment of agent views
   - Test custom templates for specific views

2. **Architecture Enforcement**:
   - Test that multi-dataset operations are properly rejected
   - Test that single dataset constraint is maintained

3. **Flexibility Mechanism**:
   - Test the recommended workarounds for multi-dataset needs
   - Test agent view pattern implementation

## Verification Tests Needed

To ensure the architecture decision is properly implemented:

```python
<!-- audience: ai-builders -->
def test_single_dataset_only():
    """Verify ADRI rejects multi-dataset operations"""
    assessor = DataSourceAssessor()
    with pytest.raises(NotImplementedError):
        assessor.assess_multiple_files(["file1.csv", "file2.csv"])

def test_agent_view_pattern():
    """Verify agent view pattern works as designed"""
    # Create denormalized view
    view = create_customer_360_view()
    
    # Create custom template
    template = create_agent_view_template()
    
    # Assess as single dataset
    report = assessor.assess_file(view)
    evaluation = template.evaluate(report)
    
    assert evaluation.is_compliant
```

## Next Steps

1. Implement tests for agent view pattern example (09_agent_view_pattern.py)
2. Add architecture enforcement tests
3. Document test patterns for teams implementing agent views
4. Create integration tests showing composition with other tools
