# ADRI Template Development - Test-Driven Approach

This directory contains the test-driven development (TDD) infrastructure for creating production-ready ADRI templates.

## 🎯 Philosophy

**We write tests FIRST, then create templates to pass those tests.**

This ensures every template:
- Solves real problems
- Prevents known failure modes
- Has measurable success criteria
- Works with actual data patterns

## 📁 Directory Structure

```
development/
├── tests/              # Test suites define template requirements
│   ├── test_invoice_processing.py
│   ├── test_crm_opportunities.py
│   └── conftest.py    # Shared test fixtures
├── templates/          # Templates under development
│   └── (empty until tests pass)
└── README.md          # This file
```

## 🚀 The TDD Process

### 1. Write Tests First (30 min)
```python
# tests/test_new_template.py
class TestNewTemplate:
    def test_perfect_data_scores_high(self):
        # Define what perfect data looks like
        # Assert it scores 95+
        
    def test_typical_data_passes_minimum(self):
        # Define real-world data
        # Assert it passes threshold
        
    def test_known_failure_prevented(self):
        # Define problematic data
        # Assert template catches it
```

### 2. Run Tests - They Should Fail
```bash
cd adri/templates/development
pytest tests/test_new_template.py -v
# All tests fail - no template exists yet!
```

### 3. Create Minimal Template
```yaml
# templates/new-template.yaml
template:
  id: "category/new-template-v1.0.0"
  # Just enough to make first test pass
```

### 4. Iterate Until All Pass
- Run tests
- Add/adjust template rules
- Repeat until green

### 5. Template is DONE When
- ✅ All tests pass
- ✅ No unnecessary complexity
- ✅ Ready for production

## 📋 Test Requirements

Each template test suite MUST include:

1. **Perfect Data Test** - Scores 95+
2. **Typical Data Test** - Passes minimum threshold
3. **Failure Mode Tests** - Each known issue prevented
4. **Business Logic Tests** - Validates use case enablement

## 🔄 Promotion to Production

Once all tests pass:

1. Peer review the template
2. Test with 5+ real datasets
3. Document the use cases
4. Move to `../catalog/` directory
5. Delete from `development/`

## 🛠️ Running Tests

```bash
# Run all template tests
pytest tests/ -v

# Run specific template tests
pytest tests/test_invoice_processing.py -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html

# Run in watch mode (auto-rerun on changes)
pytest-watch tests/
```

## 📝 Creating a New Template

1. **Copy test template**:
   ```bash
   cp tests/test_invoice_processing.py tests/test_your_template.py
   ```

2. **Modify for your use case**:
   - Update TEMPLATE_ID
   - Define test data scenarios
   - Set appropriate thresholds

3. **Run tests** (they should fail)

4. **Create template** in `templates/` to pass tests

5. **Iterate** until all tests pass

## 🎯 Key Principles

- **Tests Define Success**: If it's not tested, it's not required
- **Minimal Complexity**: Only add what tests demand
- **Real-World Focus**: Test with actual data patterns
- **Fail First**: All tests must fail before template exists
- **Green Means Done**: All passing tests = production ready

## 📊 Current Templates Under Development

| Template | Test File | Status |
|----------|-----------|--------|
| Invoice Processing | test_invoice_processing.py | 🔴 Tests Written |
| CRM Opportunities | test_crm_opportunities.py | ⚪ Not Started |
| Inventory Management | test_inventory_management.py | ⚪ Not Started |
| Patient Records | test_patient_records.py | ⚪ Not Started |
| Support Tickets | test_support_tickets.py | ⚪ Not Started |

Legend: 🔴 Tests Only | 🟡 In Progress | 🟢 All Tests Pass

---

Remember: **No template enters production without passing all tests!**
