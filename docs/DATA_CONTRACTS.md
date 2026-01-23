# ADRI Data Contracts

## Overview

**ADRI standards are executable data contracts** - formal, enforceable agreements between data producers and consumers that define data quality expectations.

## What is a Data Contract?

A data contract is a formal agreement that specifies:

1. **Schema**: What fields must exist and their data types
2. **Quality Rules**: Validation constraints that data must satisfy
3. **SLAs**: Quality thresholds that define "good enough" data
4. **Metadata**: Documentation, ownership, and lineage information

## ADRI Standards as Data Contracts

ADRI transforms traditional data contracts into **executable, self-validating agreements**:

```yaml
# Traditional data contract (documentation only)
fields:
  - customer_id: string (required)
  - email: string (must be valid email)

# ADRI contract (executable validation)
field_requirements:
  customer_id:
    type: string
    nullable: false
    validation_rules:
      - name: customer_id required
        severity: CRITICAL
        rule_expression: IS_NOT_NULL
      - name: customer_id must be unique
        severity: CRITICAL  
        rule_expression: IS_UNIQUE
```

## Contract Enforcement Workflow

### 1. Contract Creation

```bash
# Generate contract from good data
adri generate-standard data/customer_data.csv

# Creates: customer_data_ADRI_standard.yaml
# This is your data contract
```

### 2. Contract Validation

```python
@adri_protected(contract="customer_data")
def process_customers(data):
    # ADRI enforces the contract BEFORE function executes
    # Only contract-compliant data reaches your code
    return processed_data
```

### 3. Contract Compliance Check

When ADRI validates data against a contract:

**Step 1: Schema Compliance**
```
✓ Field names match contract terms
✓ Required fields present
⚠ Detect case mismatches (auto-fix available)
```

**Step 2: Quality Compliance**
```
✓ Data types match contract
✓ Values within allowed ranges
✓ Validation rules pass
```

**Step 3: SLA Compliance**
```
✓ Overall score ≥ min_score
✓ Dimension scores meet requirements  
✓ Row readiness threshold met
```

## Data Contract Benefits

### For Data Producers
- **Clear Expectations**: Know exactly what constitutes valid data
- **Early Validation**: Catch issues before data reaches consumers
- **Automated Testing**: Contracts are executable tests

### For Data Consumers
- **Guaranteed Quality**: Data meets contract SLAs
- **Reduced Errors**: Invalid data blocked at entry
- **Trust & Transparency**: Contract terms are explicit

### For Data Teams
- **Shift-Left Quality**: Validation at source
- **Self-Service**: Automated contract generation from good data
- **Auditability**: Every contract violation logged

## Alignment with Modern Data Concepts

### Data Mesh

ADRI contracts enable **domain-owned data products**:

```yaml
# Domain: Customer Service
# Owner: Customer Success Team
# Contract: customer_service_standard.yaml

standards:
  name: Customer Service Data Contract
  authority: Customer Success Team
  
requirements:
  overall_minimum: 90.0  # SLA
  
field_requirements:
  customer_id: 
    nullable: false      # Schema contract
    validation_rules:    # Quality contract
      - severity: CRITICAL
```

### Data Fabric

ADRI provides **unified contract enforcement** across:
- API endpoints
- Data pipelines
- ML workflows
- Agent systems

### DataOps

ADRI contracts support **automated quality gates**:

```python
# CI/CD Pipeline
@adri_protected(
    standard="production_data",
    min_score=95,
    on_failure="raise"
)
def deploy_model(training_data):
    # Contract enforces production quality
    # Bad data can't reach production
```

## Contract Types

### 1. Domain Contracts

Business entity contracts (customers, orders, transactions):

```yaml
# ADRI/contracts/domains/customer_service_standard.yaml
# Contract for: Customer service interactions
# Owner: Customer Success Team
# Consumers: Support agents, analytics team
```

### 2. Framework Contracts

Integration contracts for AI frameworks:

```yaml
# ADRI/contracts/frameworks/langchain_chain_input_standard.yaml  
# Contract for: LangChain chain inputs
# Owner: AI Team
# Consumers: LangChain-based agents
```

### 3. Template Contracts

Reusable structural contracts:

```yaml
# ADRI/contracts/templates/api_response_template.yaml
# Contract for: API response payloads
# Owner: Platform Team
# Consumers: All API consumers
```

## Contract Compliance Validation

### Schema Validation (Pre-Assessment)

Ensures data structure matches contract:

```python
from adri.validator.schema_validator import SchemaValidator

validator = SchemaValidator(strict_mode=False)
result = validator.validate(data, field_requirements)

if result.has_critical_issues():
    print("⚠ Data violates contract schema!")
    for warning in result.warnings:
        print(f"  {warning.message}")
        print(f"  Fix: {warning.remediation}")
```

### Quality Validation (Assessment)

Ensures data quality meets contract SLAs:

```python
from adri.validator.engine import DataQualityAssessor

assessor = DataQualityAssessor()
assessment = assessor.assess(data, "customer_data.yaml")

if assessment.overall_score >= 90:
    print("✓ Data meets contract SLA")
else:
    print("⚠ Data violates quality contract")
```

## Contract Violation Handling

### Fail-Fast (Production)

```python
@adri_protected(
    standard="financial_data",
    on_failure="raise"  # Contract violation blocks execution
)
```

### Warn-Only (Development)

```python
@adri_protected(
    standard="test_data",
    on_failure="warn"  # Contract violation logged but allowed
)
```

## Contract Versioning

Track contract evolution:

```yaml
standards:
  version: 2.1.0
  
metadata:
  last_updated: 2025-01-15
  update_notes: "Added email validation rule to contract"
  breaking_changes: false
```

## Contract Lineage

Track data-contract relationships:

```yaml
training_data_lineage:
  source_path: /data/customers.csv
  file_hash: abc123...
  snapshot_path: /snapshots/customers_abc123.csv
```

## Best Practices

### 1. Generate from Production Data

```bash
# Use real production data as contract source
adri generate-standard prod/good_customer_data.csv
```

### 2. Version Control Contracts

```bash
git add ADRI/contracts/
git commit -m "Update customer data contract - add email validation"
```

### 3. Test Before Deploying

```bash
# Validate test data against contract
adri assess test/customer_sample.csv \
  --standard customer_data_ADRI_standard.yaml
```

### 4. Monitor Contract Violations

```bash
# Review contract violations in logs
adri view-logs --failed-only
```

## Migration from Traditional Contracts

### Before: Static Documentation

```markdown
# Customer Data Contract (docs/contracts/customer.md)

Fields:
- customer_id (required, unique)
- email (required, valid email format)
- status (one of: ACTIVE, INACTIVE)

Quality: Best effort
```

### After: Executable ADRI Contract

```yaml
# ADRI/contracts/customer_data_standard.yaml

field_requirements:
  customer_id:
    nullable: false
    validation_rules:
      - severity: CRITICAL
        rule_expression: IS_UNIQUE
        
  email:
    pattern: ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$
    validation_rules:
      - severity: CRITICAL
        rule_expression: REGEX_MATCH('...')
        
  status:
    valid_values: [ACTIVE, INACTIVE]

requirements:
  overall_minimum: 90.0  # SLA
```

## Real-World Examples

### E-commerce Order Contract

```python
@adri_protected(contract="ecommerce_order")
def process_order(order_data):
    # Contract ensures:
    # - order_id is unique
    # - customer_id references valid customer
    # - total_amount is positive
    # - order_status in valid set
    return processed_order
```

### Healthcare Patient Contract

```python
@adri_protected(
    standard="healthcare_patient",
    min_score=95,  # HIPAA requires high quality
    on_failure="raise"
)
def update_patient_record(patient_data):
    # Contract enforces HIPAA compliance
    # PHI data quality guaranteed
    return updated_record
```

## Summary

**ADRI = Data Contracts for AI Agents**

- Standards are executable contracts
- Validation enforces contract compliance
- Quality SLAs defined in contracts
- Contract violations prevent bad data from reaching agents

This positions ADRI as the **contract enforcement layer** in modern data architectures, bridging data mesh principles with AI agent reliability.
