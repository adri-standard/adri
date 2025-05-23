# Understanding ADRI Dimensions

The Agent Data Readiness Index (ADRI) evaluates data across five key dimensions, each measuring a different aspect of reliability. This multi-dimensional approach ensures a comprehensive assessment of how ready your data is for use by AI agents.

## Overview

| Dimension | Key Question | Why It Matters for Agents |
|-----------|-------------|--------------------------|
| **Validity** | Is the data correctly formatted and within expected ranges? | Agents can't easily detect or recover from invalid data formats |
| **Completeness** | Is all the required data present? | Agents may not know what data is missing or how to handle gaps |
| **Freshness** | Is the data sufficiently recent? | Agents may make decisions based on outdated information |
| **Consistency** | Does the data maintain logical coherence? | Agents can be confused by contradictory or inconsistent information |
| **Plausibility** | Are the values reasonable in their domain context? | Agents may not question implausible values that humans would immediately notice |

Each dimension is scored on a scale of 0-20 points, with the combined weighted score determining the overall Agent Data Readiness Index (0-100).

## Validity Dimension

### What It Measures
Validity assesses whether your data adheres to expected formats, types, and ranges. It looks at:
- Clear data type definitions
- Format specifications (patterns)
- Range constraints
- Validation rules and their results

### Real-World Example
A banking agent receives a transaction dataset where amounts are sometimes formatted as strings ("$1,000.00") and sometimes as numbers (1000.00). Without explicit metadata about the expected format, the agent might:
- Treat "$1,000.00" as an invalid number
- Process the transaction incorrectly
- Fail to detect an unusual transaction amount

### Good vs. Problematic Data
**Good:** Clear type definitions specifying the expected formats, with explicit validation results.
```json
{
  "transaction_amount": {
    "type": "decimal",
    "format": "currency",
    "range": [0.01, 1000000.00],
    "validation_passed": true
  }
}
```

**Problematic:** No format specifications or validation information, forcing the agent to guess.

### Impact on Agent Performance
Agents with high-validity data can:
- Parse input correctly the first time
- Apply appropriate operations to the right data types
- Validate inputs before processing
- Detect anomalous values that fall outside expected ranges

## Completeness Dimension

### What It Measures
Completeness evaluates whether all necessary data is present and appropriately populated. It considers:
- Overall data completeness
- Field-level missing values
- Distinction between null and missing
- Required vs. optional fields
- Section-level completeness

### Real-World Example
A medical diagnosis agent analyzes patient data where critical test results are missing for some patients. Without explicit completeness metadata, the agent might:
- Assume tests were performed with negative results
- Make recommendations based on incomplete information
- Fail to request the missing tests

### Good vs. Problematic Data
**Good:** Explicit tracking of completeness with clear distinction between null and missing values.
```json
{
  "blood_test_results": {
    "completeness": 0.94,
    "missing_reason": "test_not_performed",
    "required": true,
    "missing_handling": "request_test"
  }
}
```

**Problematic:** No indication of which fields are missing or why, leaving the agent to process incomplete data blindly.

### Impact on Agent Performance
Agents with high-completeness data can:
- Identify and address missing information
- Make appropriate decisions about when to proceed despite gaps
- Request specific missing data when needed
- Communicate confidence levels based on data completeness

## Freshness Dimension

### What It Measures
Freshness evaluates how recent the data is and whether it meets timeliness requirements. It examines:
- Timestamp information
- Data age
- Update frequency
- Service level agreements (SLAs)
- Time-sensitivity flags

### Real-World Example
A stock trading agent makes decisions using market data that's 30 minutes delayed. Without explicit freshness metadata, the agent might:
- Trade based on outdated prices
- Miss rapid market movements
- Fail to adjust its strategy for data staleness

### Good vs. Problematic Data
**Good:** Clear timestamp and freshness evaluation that the agent can consider.
```json
{
  "market_data": {
    "timestamp": "2025-05-23T14:25:30Z",
    "age_seconds": 120,
    "update_frequency": "15s",
    "meets_freshness_sla": false,
    "staleness_warning": "Data is outside real-time window"
  }
}
```

**Problematic:** No timestamp or freshness information, leaving the agent unaware of when the data was collected or last updated.

### Impact on Agent Performance
Agents with high-freshness data can:
- Adjust confidence based on data recency
- Make time-appropriate decisions
- Request fresher data when needed
- Apply different strategies for different staleness levels

## Consistency Dimension

### What It Measures
Consistency evaluates the logical coherence within and across datasets. It looks at:
- Cross-field validation rules
- Referential integrity
- Aggregation consistency
- Business rule compliance
- Temporal consistency

### Real-World Example
A customer service agent works with a dataset where a customer's status is "active" but their subscription end date is in the past. Without consistency metadata, the agent might:
- Offer renewal options to a customer who already churned
- Provide conflicting information to the customer
- Fail to recognize the data contradiction

### Good vs. Problematic Data
**Good:** Explicit consistency checks with clear results.
```json
{
  "consistency_results": [
    {
      "rule_name": "active_status_valid_subscription",
      "fields": ["status", "subscription_end_date"],
      "valid": false,
      "message": "Customer marked active but subscription expired"
    }
  ]
}
```

**Problematic:** No consistency validation, leaving contradictory information undetected and unexplained.

### Impact on Agent Performance
Agents with high-consistency data can:
- Avoid contradictory statements or actions
- Identify and resolve conflicting information
- Apply business rules correctly
- Maintain logical coherence in their responses

## Plausibility Dimension

### What It Measures
Plausibility assesses whether values are reasonable based on context and domain knowledge. It considers:
- Statistical outlier detection
- Domain-specific value ranges
- Relationship plausibility
- Contextual validation

### Real-World Example
A shopping agent encounters a dataset with a $10,000 toaster and a $5 laptop. Without plausibility metadata, the agent might:
- Recommend the "bargain" laptop
- Fail to flag the suspiciously priced toaster
- Make recommendations based on implausible data

### Good vs. Problematic Data
**Good:** Domain-specific plausibility rules with explicit results.
```json
{
  "plausibility_results": [
    {
      "rule_name": "Price range check for Electronics",
      "field": "price",
      "valid": false,
      "message": "Laptop price ($5.00) outside plausible range ($200-$5000)",
      "examples": [5.00]
    }
  ]
}
```

**Problematic:** No plausibility evaluation, leaving the agent unable to distinguish between unusual-but-valid values and likely errors.

### Impact on Agent Performance
Agents with high-plausibility data can:
- Flag suspicious values for human review
- Apply domain knowledge to data interpretation
- Distinguish between unusual and erroneous values
- Communicate uncertainty about implausible data

## Enhancing Your Dimensions

Each dimension can be enhanced by providing explicit metadata for your data sources:

| Dimension | Default Assessment | Enhanced Assessment |
|-----------|-------------------|---------------------|
| **Validity** | Automatic type inference | `dataset.validation.json` with explicit types, formats, and ranges |
| **Completeness** | Basic null counting | `dataset.completeness.json` with missing value semantics |
| **Freshness** | File timestamp analysis | `dataset.freshness.json` with update frequency and SLAs |
| **Consistency** | Limited cross-checking | `dataset.consistency.json` with business rules |
| **Plausibility** | Statistical outliers | `dataset.plausibility.json` with domain constraints |

These metadata files should be placed alongside your data source with the same base name. For example, if your data is in `customer_data.csv`, the enhanced validity metadata would be in `customer_data.validation.json`.

## Dimension Weights

You can configure the relative importance of dimensions based on your specific agent's needs:

```python
from adri import DataSourceAssessor

# Create an assessor that emphasizes plausibility and freshness
assessor = DataSourceAssessor(config={
    "dimension_weights": {
        "validity": 1.0,      # Standard weight
        "completeness": 1.0,  # Standard weight
        "freshness": 2.0,     # Double weight
        "consistency": 1.0,   # Standard weight
        "plausibility": 2.0   # Double weight
    }
})

# Assess with custom weights
report = assessor.assess_file("customer_data.csv")
```

By understanding and optimizing across all five dimensions, you can significantly improve the reliability of data for your agent workflows.
