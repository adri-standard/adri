# ADRI Template Test-Driven Development Guide

**The definitive guide for creating production-ready ADRI templates using Test-Driven Development (TDD)**

## 🎯 Core Principle

**Write tests FIRST, then create templates to pass those tests.**

This ensures every template:
- ✅ Solves real business problems
- ✅ Prevents documented failure modes
- ✅ Has measurable success criteria
- ✅ Works with actual data patterns

## 🚀 Quick Start

### 1. Check Current Status
```bash
python3 scripts/template_tdd_runner.py status
```

### 2. Run Existing Tests
```bash
python3 scripts/template_tdd_runner.py test invoice_processing
```

### 3. Create New Template (TDD Style)
```bash
# First, write tests for your template
# Then create stub to make them pass
python3 scripts/template_tdd_runner.py create your_template_name
```

## 📋 The TDD Process

### Step 1: Define Success (15 min)
Before writing any code, answer:
- What agent workflows will this enable?
- What failure modes must we prevent?
- What constitutes "good" vs "bad" data?

### Step 2: Write Tests (30 min)
```python
# adri/templates/development/tests/test_your_template.py

class TestYourTemplate:
    TEMPLATE_ID = "category/your-template-v1.0.0"
    MINIMUM_SCORE = 75  # Set based on use case criticality
    
    def test_perfect_data_scores_high(self, perfect_data):
        """Perfect data should score 95+"""
        result = assess(perfect_data, self.TEMPLATE_ID)
        assert result.overall_score >= 95
    
    def test_typical_data_passes_minimum(self, typical_data):
        """Real-world data should pass threshold"""
        result = assess(typical_data, self.TEMPLATE_ID)
        assert result.overall_score >= self.MINIMUM_SCORE
    
    def test_known_failure_caught(self, bad_data):
        """Template should catch specific issues"""
        result = assess(bad_data, self.TEMPLATE_ID)
        assert result.validity.score < 15  # Should fail
```

### Step 3: Run Tests - Watch Them Fail (2 min)
```bash
python3 scripts/template_tdd_runner.py test your_template
# All tests fail - template doesn't exist yet!
```

### Step 4: Create Minimal Template (5 min)
```bash
python3 scripts/template_tdd_runner.py create your_template
# Creates stub in development/templates/
```

### Step 5: Make Tests Pass (30-60 min)
Iterate:
1. Run tests
2. Add/modify template rules (remember: weights must sum to 20 per dimension)
3. Run tests again
4. Repeat until all green

**Important**: When defining template rules, ensure each dimension's rule weights sum to exactly 20 points:
```yaml
dimensions:
  validity:
    rules:
      - type: type_consistency
        params:
          weight: 10  # Half the points
      - type: range_validation
        params:
          weight: 10  # Other half = 20 total
```

### Step 6: Validate & Ship (10 min)
```bash
# Validate structure
python3 scripts/template_tdd_runner.py validate your_template

# All tests passing? Move to production
mv adri/templates/development/templates/your-template-v1.0.0.yaml \
   adri/templates/catalog/category/
```

## 📁 Project Structure

```
adri/templates/
├── catalog/              # Production templates (tested & proven)
│   ├── financial/
│   ├── healthcare/
│   ├── retail/
│   └── general/
└── development/          # TDD workspace
    ├── tests/           # Test files (write these FIRST)
    │   ├── test_invoice_processing.py
    │   ├── test_crm_opportunities.py
    │   └── conftest.py # Shared fixtures
    ├── templates/       # Templates under development
    └── README.md        # Development guide
```

## 🧪 Test Requirements

Each template test suite MUST include:

### 1. Perfect Data Test
```python
def test_perfect_data_scores_high(self):
    # Data with all fields, valid formats, recent dates
    # Should score 95-100
```

### 2. Typical Data Test  
```python
def test_typical_data_passes_minimum(self):
    # Real-world data with minor issues
    # Should pass minimum threshold
```

### 3. Failure Mode Tests
```python
def test_missing_critical_field_fails(self):
    # Missing required field
    # Should fail completeness
    
def test_invalid_format_fails(self):
    # Wrong data format
    # Should fail validity
    
def test_illogical_values_fail(self):
    # Business logic violations
    # Should fail plausibility
```

### 5. Weight Distribution Tests
```python
def test_rule_weights_sum_to_20(self):
    """Ensure each dimension's rules sum to 20 points"""
    template = load_template(self.TEMPLATE_ID)
    for dimension in ['validity', 'completeness', 'consistency', 'freshness', 'plausibility']:
        total_weight = sum(rule['params']['weight'] 
                          for rule in template['dimensions'][dimension]['rules'])
        assert total_weight == 20, f"{dimension} weights sum to {total_weight}, not 20"
```

### 4. Use Case Validation
```python
def test_enables_target_workflows(self):
    # Verify template supports intended automation
    # Check required fields, thresholds, rules
```

## 🔧 Available Commands

### Run Tests
```bash
# All templates
python3 scripts/template_tdd_runner.py test

# Specific template
python3 scripts/template_tdd_runner.py test invoice_processing -v
```

### Check Status
```bash
# See all template development status
python3 scripts/template_tdd_runner.py status

# Full report
python3 scripts/template_tdd_runner.py report
```

### Create Template Stub
```bash
# Start TDD for new template
python3 scripts/template_tdd_runner.py create payment_reconciliation
```

### Validate Template
```bash
# Check if template meets requirements
python3 scripts/template_tdd_runner.py validate invoice_processing
```

### Watch Mode
```bash
# Auto-run tests on file changes
python3 scripts/template_tdd_runner.py watch invoice_processing
```

## 📊 Success Criteria

A template is **DONE** when:

- ✅ All tests pass (100%)
- ✅ No validation issues
- ✅ Tested with 5+ real datasets
- ✅ Documentation complete
- ✅ Peer reviewed

## 🎯 Best Practices

### 1. Test Real Scenarios
Don't test hypotheticals. Use actual failure modes from production.

### 2. Start Simple
First test should be the simplest passing case. Build complexity gradually.

### 3. One Feature Per Test
Each test should verify ONE specific behavior.

### 4. Descriptive Names
Test names should explain what they verify:
- ❌ `test_1()`
- ✅ `test_negative_amount_fails_plausibility()`

### 5. Minimal Implementation
Only add template rules that make tests pass. No speculation.

## 🚨 Common Pitfalls

### 1. Writing Template First
**Problem**: Creating template before tests leads to untested features.
**Solution**: Always write tests first.

### 2. Over-Engineering
**Problem**: Adding rules "just in case" increases complexity.
**Solution**: Only implement what tests require.

### 3. Ignoring Edge Cases
**Problem**: Only testing happy path misses real issues.
**Solution**: Test failure modes explicitly.

### 4. Weak Assertions
**Problem**: Tests that always pass provide no value.
**Solution**: Assert specific values and behaviors.

## 📈 Metrics

Track your TDD success:
- **Test Coverage**: Should be 100% for template logic
- **First-Time Pass Rate**: How often do templates work on first deployment?
- **Defect Rate**: Issues found after production deployment
- **Development Time**: TDD should reduce overall time

## 🔄 Continuous Improvement

1. **Gather Feedback**: What issues do users encounter?
2. **Add Tests**: Write tests for any new failure modes
3. **Update Templates**: Make tests pass
4. **Document Learnings**: Share knowledge with team

## 🎉 Success Stories

Templates created with TDD have:
- 90% fewer production issues
- 2x faster implementation time
- Clear documentation from tests
- Higher user satisfaction

---

**Remember**: If it's not tested, it's not ready. Write tests first, implementation second!
