# Test Plan: Template-Driven Discovery Mode

## Overview
This test plan covers the implementation of template-driven discovery mode in ADRI, which replaces hard-coded business logic with intelligent template matching.

## Test Objectives
1. Verify template pattern matching accurately identifies data types
2. Ensure confidence scoring algorithm works correctly
3. Validate multi-template assessment functionality
4. Confirm proper integration with discovery mode
5. Test template catalog management

## Test Scope

### In Scope
- Template matcher implementation (`adri/templates/matcher.py`)
- Template pattern specifications in YAML format
- Confidence scoring algorithm
- Multi-template assessment reporting
- Integration with discovery mode
- Template catalog structure

### Out of Scope
- Backward compatibility (not required per design decision)
- ML-enhanced matching (future enhancement)
- Template hub integration (future phase)

## Test Categories

### 1. Unit Tests - Template Matcher Core

#### Test Case 1.1: Column Name Matching
```python
# tests/unit/templates/test_matcher_column_matching.py
```
- **Objective**: Verify exact column name matching
- **Input**: DataFrame with columns, template with required columns
- **Expected**: 100% confidence for exact matches
- **Priority**: High

#### Test Case 1.2: Fuzzy Column Matching
- **Objective**: Test fuzzy string matching for column names
- **Input**: DataFrame with "cust_id", template expects "customer_id"
- **Expected**: ~80% confidence based on similarity
- **Priority**: High

#### Test Case 1.3: Synonym-Based Matching
- **Objective**: Test column synonym recognition
- **Input**: DataFrame with "client", template defines "customer" with synonym "client"
- **Expected**: High confidence match using synonyms
- **Priority**: Medium

### 2. Unit Tests - Data Pattern Recognition

#### Test Case 2.1: Email Pattern Detection
```python
# tests/unit/templates/test_pattern_analyzer.py
```
- **Objective**: Verify email pattern recognition
- **Input**: Column with email addresses
- **Expected**: Pattern analyzer correctly identifies email format
- **Priority**: High

#### Test Case 2.2: Currency Pattern Detection
- **Objective**: Test currency value recognition
- **Input**: Column with values like "$1,234.56"
- **Expected**: Identifies as currency pattern
- **Priority**: High

#### Test Case 2.3: Categorical Pattern Detection
- **Objective**: Test categorical value recognition
- **Input**: Column with limited set of values
- **Expected**: Identifies as categorical with correct cardinality
- **Priority**: Medium

### 3. Unit Tests - Confidence Scoring

#### Test Case 3.1: Composite Score Calculation
```python
# tests/unit/templates/test_confidence_scoring.py
```
- **Objective**: Test weighted scoring algorithm
- **Input**: Various match scores (column: 80%, pattern: 90%, etc.)
- **Expected**: Correct weighted average calculation
- **Priority**: High

#### Test Case 3.2: Edge Cases in Scoring
- **Objective**: Test scoring with missing components
- **Input**: Template with no pattern specifications
- **Expected**: Graceful handling, reasonable default scores
- **Priority**: Medium

### 4. Integration Tests - Discovery Mode

#### Test Case 4.1: Discovery with Template Matching
```python
# tests/integration/test_discovery_template_matching.py
```
- **Objective**: Test discovery mode uses template matching
- **Input**: Raw CSV data without metadata
- **Expected**: Discovery mode finds and applies best template
- **Priority**: High

#### Test Case 4.2: Multi-Template Assessment
- **Objective**: Test assessment with multiple templates
- **Input**: Data that could match multiple templates
- **Expected**: Returns top 3 matches with confidence scores
- **Priority**: High

#### Test Case 4.3: Template Not Found Handling
- **Objective**: Test behavior when no templates match well
- **Input**: Unusual data format
- **Expected**: Falls back to generic template
- **Priority**: Medium

### 5. Integration Tests - End-to-End Workflow

#### Test Case 5.1: CLI Discovery Command
```python
# tests/integration/test_cli_discovery.py
```
- **Objective**: Test CLI with template discovery
- **Input**: `adri assess data.csv --show-templates=3`
- **Expected**: Shows multiple template matches in output
- **Priority**: High

#### Test Case 5.2: Metadata Generation with Templates
- **Objective**: Test metadata files generated using template
- **Input**: Discovery mode with CRM template match
- **Expected**: Metadata files reflect CRM-specific rules
- **Priority**: High

### 6. Template Validation Tests

#### Test Case 6.1: Template Schema Validation
```python
# tests/unit/templates/test_template_validation.py
```
- **Objective**: Validate template YAML structure
- **Input**: Various template files
- **Expected**: Proper validation of required fields
- **Priority**: High

#### Test Case 6.2: Pattern Specification Validation
- **Objective**: Test pattern specifications are valid
- **Input**: Template with regex patterns
- **Expected**: Validates regex syntax and structure
- **Priority**: Medium

## Test Data Requirements

### Sample DataFrames
1. **CRM Data**: opportunity_id, amount, stage, contact_email
2. **Inventory Data**: sku, quantity_on_hand, reorder_threshold
3. **Customer Data**: customer_id, email, phone, registration_date
4. **Mixed Data**: Ambiguous columns that could match multiple templates
5. **Edge Case Data**: Unusual column names, missing patterns

### Sample Templates
1. **crm-sales-v1.0.0.yaml**: Full pattern matching for CRM
2. **inventory-v1.0.0.yaml**: Inventory-specific patterns
3. **generic-tabular-v1.0.0.yaml**: Fallback template
4. **test-minimal-v1.0.0.yaml**: Minimal valid template
5. **test-invalid-v1.0.0.yaml**: Invalid template for testing

## Test Environment

### Dependencies
- pytest
- pandas
- python-Levenshtein (for fuzzy matching)
- pyyaml (already in requirements)

### Test Structure
```
tests/
├── unit/
│   └── templates/
│       ├── test_matcher_column_matching.py
│       ├── test_pattern_analyzer.py
│       ├── test_confidence_scoring.py
│       └── test_template_validation.py
├── integration/
│   ├── test_discovery_template_matching.py
│   └── test_cli_discovery.py
└── fixtures/
    └── templates/
        ├── test_templates.yaml
        └── sample_data.py
```

## Success Criteria
- All unit tests pass with 100% success rate
- Integration tests demonstrate proper template matching
- Discovery mode successfully identifies appropriate templates
- Confidence scores accurately reflect match quality
- No regression in existing functionality

## Risk Mitigation
- **Risk**: Performance impact of template matching
- **Mitigation**: Implement caching, optimize matching algorithms
- **Risk**: Template compatibility issues
- **Mitigation**: Strict schema validation, comprehensive testing

## Test Execution Timeline
1. **Phase 1**: Core matcher unit tests (Week 1)
2. **Phase 2**: Pattern recognition tests (Week 1-2)
3. **Phase 3**: Integration tests (Week 2)
4. **Phase 4**: End-to-end testing (Week 2-3)
5. **Phase 5**: Performance testing (Week 3)

## Test Coverage Goals
- Unit test coverage: >95% for new modules
- Integration test coverage: >85% for workflows
- All critical paths tested
- Edge cases documented and tested
