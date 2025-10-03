

## Test Organization (Updated 2025-10-03)

### Consolidated Test Structure
The test framework has been modernized with a quality-first approach:

**Validator Tests (4 files, 151 tests):**
- `test_validator_integration.py` - Integration tests, real-world scenarios
- `test_validator_engine.py` - Core engine functionality
- `test_validator_rules.py` - Validation rules and constraints
- `test_validator_loaders.py` - Standard loading

**Decorator Tests (2 files, 20 tests):**
- `test_decorator.py` - Core decorator functionality
- `test_decorator_autogen_equivalence.py` - Autogen behavior verification

**Config Tests (1 file, 23 tests):**
- `test_config.py` - Configuration loading and management

**Guard Tests (1 file, 21 tests):**
- `test_guard_modes.py` - Protection mode functionality

**Tutorial Tests (5 files, 72 tests):**
- `test_tutorial_auto_discovery.py` - Auto-discovery framework + baseline regression
- `test_tutorial_framework.py` - Core tutorial framework
- `test_tutorial_cli_decorator_parity.py` - CLI/Decorator equivalence
- `test_tutorial_invoice_flow_validation.py` - Invoice validation
- `test_tutorial_framework_example.py` - Framework examples

### Testing Principles
✅ All tests verify real functionality (no mocking of internal code)
✅ Baseline regression testing for tutorials
✅ Focus on functional coverage over test count
✅ Clean organization by component

### Running Tests
```bash
# Run all consolidated tests
pytest tests/test_validator*.py tests/test_decorator*.py tests/test_config.py tests/test_guard*.py

# Run with coverage
pytest tests/ --cov=src/adri --cov-report=html

# Run baseline regression
pytest tests/test_tutorial_auto_discovery.py::test_baseline_regression -k invoice
```

See CONSOLIDATION_SUMMARY.md for detailed before/after metrics.
