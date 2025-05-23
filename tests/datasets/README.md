# ADRI Test Datasets

This directory contains datasets designed to test the Agent Data Readiness Index (ADRI) framework's ability to assess data quality across its five dimensions.

## Dataset Structure

All datasets follow a common e-commerce order schema with the following fields:

| Field | Description | Type | 
|-------|-------------|------|
| customer_id | Unique identifier for the customer | String/Integer |
| product_id | Unique identifier for the product | String |
| product_name | Name of the product | String |
| category | Product category | String |
| purchase_date | Date of purchase | Date (YYYY-MM-DD) |
| price | Price of the product | Numeric |
| quantity | Number of units purchased | Integer |
| payment_method | Method of payment | String |
| shipping_address | Delivery address | String |
| satisfaction_score | Customer rating (1-5) | Integer |
| return_date | Date of return (if applicable) | Date (YYYY-MM-DD) |
| return_reason | Reason for return (if applicable) | String |

## Test Datasets

### 1. Ideal Dataset (`ideal_dataset.csv`)

A control dataset with no quality issues. All fields are properly formatted, complete, and reasonable. This serves as a baseline for comparison.

### 2. Incomplete Dataset (`incomplete_dataset.csv`)

Tests the completeness dimension of ADRI. This dataset contains:
- Missing values across various fields
- Completely empty fields for some records
- Varying degrees of completeness across different columns

### 3. Stale Dataset (`stale_dataset.csv`)

Tests the freshness dimension of ADRI. This dataset contains:
- Purchase dates ranging from very recent to over a year old
- A mix of recent and older timestamps
- Some records with timestamps in the distant past

### 4. Invalid Dataset (`invalid_dataset.csv`)

Tests the validity dimension of ADRI. This dataset contains:
- Incorrect ID formats
- Invalid dates (e.g., "2025-13-12", "Tomorrow")
- Negative quantity values
- Text values in numeric fields
- Numeric values with invalid formats

### 5. Inconsistent Dataset (`inconsistent_dataset.csv`)

Tests the consistency dimension of ADRI. This dataset contains:
- Duplicate records with different values
- Return dates that are earlier than purchase dates
- Inconsistent categorization (same product in different categories)
- Multiple entries for the same product with different prices/attributes
- Logical inconsistencies in customer journey

### 6. Implausible Dataset (`implausible_dataset.csv`)

Tests the plausibility dimension of ADRI. This dataset contains:
- Extremely high prices (e.g., $9999.99 headphones)
- Extremely low prices (e.g., $0.99 speakers)
- Unreasonable quantities (e.g., 200 headphones in one order)
- Values that are technically valid but statistically unlikely

### 7. Mixed Issues Dataset (`mixed_issues_dataset.csv`)

This dataset combines all of the above issues to test ADRI's overall assessment capabilities. It contains:
- Missing values
- Stale data
- Invalid formats
- Inconsistencies
- Implausible values

## Expected Results

When assessed by ADRI, these datasets should produce predictable scoring patterns:

| Dataset | Overall Score | Validity | Completeness | Freshness | Consistency | Plausibility |
|---------|--------------|----------|--------------|-----------|-------------|--------------|
| ideal_dataset.csv | High | High | High | High | High | High |
| incomplete_dataset.csv | Medium-Low | High | Low | High | Medium | Medium |
| stale_dataset.csv | Medium-Low | High | High | Low | High | Medium |
| invalid_dataset.csv | Medium-Low | Low | High | High | Medium | Medium |
| inconsistent_dataset.csv | Medium-Low | High | High | High | Low | Medium |
| implausible_dataset.csv | Medium-Low | High | High | High | Medium | Low |
| mixed_issues_dataset.csv | Low | Low | Low | Low | Low | Low |

## Using These Datasets

These datasets can be used to validate that ADRI correctly identifies and scores issues in each quality dimension:

```bash
# Example: Using the CLI to assess a dataset
adri assess --source test_datasets/ideal_dataset.csv --output reports/ideal_report.json

# Example: Using the Python API
from adri import DataSourceAssessor

assessor = DataSourceAssessor()
report = assessor.assess_file("test_datasets/incomplete_dataset.csv")
report.save_json("reports/incomplete_report.json")
```

Then compare the assessment results against the expected patterns to validate that ADRI is functioning correctly.

## Note About Actual Scores

The specific numeric scores may vary depending on the ADRI version and configuration. The important aspect is the relative relationship between scores (e.g., incomplete_dataset.csv should have a lower completeness score than ideal_dataset.csv).
