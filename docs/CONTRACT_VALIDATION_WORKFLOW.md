# ADRI Standard Validation Workflow

## Overview

This document describes the automated workflow for validating that community-submitted or new ADRI standards are functional and work correctly within the ADRI system.

## The Problem

When users submit new standards to the catalog, we need to ensure:
1. The standard structure is valid (proper YAML format)
2. The validation rules work correctly
3. The standard produces accurate quality scores
4. Dimension calculations are correct
5. The standard integrates properly with ADRI

Previously, this required manual CSV creation for each standard - time-consuming and error-prone.

## The Solution

**Automated Standard Validation Pipeline:**

```
1. User provides standard YAML
   ↓
2. Script validates structure
   ↓
3. Script generates training CSV (100% quality)
   ↓
4. Script generates test CSV (with errors)
   ↓
5. CSVs placed in ADRI/tutorials/<standard_id>/
   ↓
6. Existing tutorial discovery finds them
   ↓
7. 9 comprehensive tests run automatically
   ↓
8. Reports if standard is catalog-ready
```

## How to Use

### Step 1: Validate a Standard

Run the generator script with your standard YAML:

```bash
python scripts/generate_standard_test_data.py path/to/your_standard.yaml
```

**Example:**
```bash
python scripts/generate_standard_test_data.py adri/contracts/domains/customer_service_standard.yaml
```

**Output:**
```
======================================================================
ADRI Standard Test Data Generator
======================================================================
Loading standard: adri/contracts/domains/customer_service_standard.yaml
✓ Standard validated: customer_service_standard
  Fields: 10

Generating training data (5 rows)...
✓ Generated 5 training rows

Generating test data with errors (5 rows)...
✓ Generated 5 test rows with ~16 errors

✓ Created tutorial directory: ADRI/tutorials/customer_service_standard
✓ Wrote training data: customer_service_standard_data.csv
✓ Wrote test data: test_customer_service_standard_data.csv

======================================================================
✓ Test data generation complete!
======================================================================
```

### Step 2: Run Validation Tests

The tutorial discovery system automatically finds and tests your standard:

```bash
pytest tests/test_tutorial_auto_discovery.py -v -k customer_service_standard
```

**Output:**
```
tests/test_tutorial_auto_discovery.py::test_training_data_scores_100_percent[customer_service_standard] PASSED
tests/test_tutorial_auto_discovery.py::test_standard_generation_succeeds[customer_service_standard] PASSED
tests/test_tutorial_auto_discovery.py::test_error_detection_works[customer_service_standard] PASSED
tests/test_tutorial_auto_discovery.py::test_data_structure_consistency[customer_service_standard] PASSED
tests/test_tutorial_auto_discovery.py::test_file_naming_convention[customer_service_standard] PASSED
tests/test_tutorial_auto_discovery.py::test_generated_standard_is_valid[customer_service_standard] PASSED
tests/test_tutorial_auto_discovery.py::test_assessment_and_logs_are_valid[customer_service_standard] PASSED

============================== 7 passed, 1 skipped in 3.02s ==============================
```

## What Gets Tested

For each standard, **9 comprehensive tests** run automatically:

1. **Training Data Validation** - Training CSV passes with 100% quality score
2. **Standard Generation** - Standard can be loaded and parsed correctly
3. **Error Detection** - Test CSV has quality issues as expected
4. **Data Structure** - CSV structure matches field_requirements
5. **File Naming** - Files follow correct naming convention
6. **Standard Validity** - Standard YAML is structurally valid
7. **Assessment Logs** - JSONL logs are generated correctly
8. **Baseline Regression** - Results match expected baselines
9. **Integration** - Standard works correctly with ADRI system

## How It Works

### Data Generation Strategy

**Training Data (100% Quality):**
- Reads each field's type (string, integer, date, etc.)
- Reads validation rules (not_null, pattern, numeric_bounds, etc.)
- Generates values that satisfy ALL rules
- Creates 5 realistic rows that pass validation

**Test Data (With Errors):**
- Same structure as training data
- Intentionally violates 25-50% of fields per row
- Mix of violations:
  - Null values where not allowed (CRITICAL)
  - Out of range numbers (CRITICAL)
  - Invalid enum values (CRITICAL)
  - Pattern mismatches (WARNING)
  - Length violations (WARNING)
- Targets ~60-80% quality score

### Tutorial Integration

The generator places CSVs in `ADRI/tutorials/<standard_id>/` following the tutorial naming convention:
- `<standard_id>_data.csv` - Training data
- `test_<standard_id>_data.csv` - Test data

This allows the existing tutorial discovery system (`tests/fixtures/tutorial_discovery.py`) to automatically find and test the standard - **no code changes needed!**

## Use Cases

### Community Standard Submission

When a community member submits a new standard:

```bash
# 1. Validate structure and generate test data
python scripts/generate_standard_test_data.py community_standard.yaml

# 2. Run validation tests
pytest tests/test_tutorial_auto_discovery.py -v -k community_standard

# 3. If all tests pass, standard is catalog-ready!
```

### Core ADRI Standards

For validating existing ADRI standards:

```bash
# Generate test data for all standards
for standard in adri/contracts/domains/*.yaml; do
    python scripts/generate_standard_test_data.py $standard
done

# Run all validation tests
pytest tests/test_tutorial_auto_discovery.py -v
```

### CI/CD Integration

Add to your CI pipeline:

```yaml
# .github/workflows/validate-standards.yml
- name: Validate New Standards
  run: |
    python scripts/generate_standard_test_data.py ${{ github.event.inputs.standard_path }}
    pytest tests/test_tutorial_auto_discovery.py -v -k $(basename ${{ github.event.inputs.standard_path }} .yaml)
```

## Example: Customer Service Standard

### Generated Training Data

```csv
ticket_id,customer_id,created_date,category,priority,status,first_response_time_hours,resolution_time_hours,customer_satisfaction_score,agent_id
TICKET_ID-01000,CUSTOMER_ID-01000,2024-01-15,Technical Support,High,Resolved,2.5,24.0,5,AGENT_ID-01000
TICKET_ID-01001,CUSTOMER_ID-01001,2024-01-22,Billing,Medium,Closed,1.0,8.5,4,AGENT_ID-01001
TICKET_ID-01002,CUSTOMER_ID-01002,2024-01-29,Product Inquiry,Low,Open,0.5,15.2,3,AGENT_ID-01002
...
```

### Generated Test Data (With Errors)

```csv
ticket_id,customer_id,created_date,category,priority,status,first_response_time_hours,resolution_time_hours,customer_satisfaction_score,agent_id
BAD-ID,CUSTOMER_ID-01000,NOT-A-DATE,INVALID,High,Resolved,2.5,24.0,5,AGENT_ID-01000
TICKET_ID-01001,,2024-01-22,Billing,Medium,Closed,-10,8.5,4,AGENT_ID-01001
TICKET_ID-01002,CUSTOMER_ID-01002,2024-01-29,Product Inquiry,INVALID,Open,0.5,999999,10,
...
```

## Benefits

### For Quality Assurance
- ✅ Automated validation of every standard
- ✅ Catches errors before catalog publication
- ✅ Verifies calculation accuracy
- ✅ Prevents breaking changes

### For Community
- ✅ Clear submission process
- ✅ Automated feedback on standards
- ✅ Confidence in catalog quality
- ✅ Standards proven to work

### For Development
- ✅ Zero manual CSV creation
- ✅ Consistent test coverage
- ✅ Self-documenting standards
- ✅ Easy to add new standards

## Files Created

### Generator Script
- `scripts/generate_standard_test_data.py` - Main generator

### Test Infrastructure (Already Exists)
- `tests/fixtures/tutorial_discovery.py` - Auto-discovers tutorials
- `tests/test_tutorial_auto_discovery.py` - Runs 9 tests per tutorial

### Generated Output
- `ADRI/tutorials/<standard_id>/`
  - `<standard_id>_data.csv` - Training data
  - `test_<standard_id>_data.csv` - Test data

## Limitations & Future Enhancements

### Current Limitations
- Data generation is rule-based, not intelligent
- May not catch all edge cases
- Generated data is synthetic, not real-world

### Potential Enhancements
- Use LLMs to generate more realistic data
- Add property-based testing (hypothesis)
- Generate data from real-world examples
- Add performance benchmarking
- Generate visual reports

## Related Documentation

- [Tutorial Auto-Discovery](../tests/README.md) - Tutorial testing system
- [Severity Levels](SEVERITY_LEVELS.md) - CRITICAL vs WARNING rules
- [Standards Library](STANDARDS_LIBRARY.md) - Available standards

## Summary

The standard validation workflow provides **automated, comprehensive testing** for all ADRI standards.

**To validate any standard:**
1. Run: `python scripts/generate_standard_test_data.py <standard.yaml>`
2. Run: `pytest tests/test_tutorial_auto_discovery.py -v -k <standard_id>`
3. Done! Standard is validated and catalog-ready.

**No manual work required!** The system automatically generates test data and runs comprehensive validation tests using the existing tutorial infrastructure.
