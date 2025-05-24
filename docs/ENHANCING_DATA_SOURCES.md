# Enhancing Data Sources for Agent Readiness

## Why Enhance Your Data Sources?

While ADRI can assess any data source using automatic detection, you can significantly improve your readiness scores and agent performance by providing explicit metadata about your data's reliability characteristics.

Enhanced data sources enable:

1. **Higher ADRI Scores**: Explicit metadata can earn maximum points in each dimension
2. **Better Agent Performance**: Detailed metadata allows agents to handle edge cases better
3. **Clearer Communication**: Standardized metadata format improves reliability understanding
4. **Proactive Quality Control**: The process of creating metadata helps identify issues early

## Metadata File Structure

ADRI uses companion metadata files that sit alongside your primary data source:

```
customer_data.csv                  # Primary data source
customer_data.validation.json      # Validity metadata
customer_data.completeness.json    # Completeness metadata
customer_data.freshness.json       # Freshness metadata
customer_data.consistency.json     # Consistency metadata
customer_data.plausibility.json    # Plausibility metadata
```

Each metadata file focuses on one specific dimension of data reliability.

## Enhancing Validity

The validity metadata file helps agents understand the expected formats and value constraints.

### Example: `customer_data.validation.json`

```json
{
  "has_explicit_validity_info": true,
  "type_definitions": {
    "customer_id": {
      "type": "string",
      "format": "^CUS\\d{6}$",
      "description": "Customer ID starting with CUS followed by 6 digits"
    },
    "email": {
      "type": "string",
      "format": "email",
      "description": "Valid email address"
    },
    "age": {
      "type": "integer",
      "range": [18, 120],
      "description": "Customer age in years"
    },
    "purchase_amount": {
      "type": "decimal",
      "range": [0.01, 100000.00],
      "description": "Purchase amount in USD"
    },
    "membership_level": {
      "type": "string",
      "allowed_values": ["bronze", "silver", "gold", "platinum"],
      "description": "Customer membership tier"
    }
  },
  "validation_results": {
    "overall_valid": true,
    "fields": {
      "customer_id": {"valid": true, "invalid_count": 0},
      "email": {"valid": true, "invalid_count": 3, "examples": ["not.an.email", "missing@domain"]},
      "age": {"valid": true, "invalid_count": 1, "examples": [142]},
      "purchase_amount": {"valid": true, "invalid_count": 0},
      "membership_level": {"valid": true, "invalid_count": 0}
    }
  }
}
```

### Key Elements for Validity Metadata
- **type_definitions**: Explicit data types for each field
- **format**: Regular expressions or named formats for string validation
- **range**: Min/max boundaries for numeric values
- **allowed_values**: Enumerated list of valid values
- **validation_results**: Results of applying these rules to the data

## Enhancing Completeness

The completeness metadata helps agents understand which data is missing and why.

### Example: `customer_data.completeness.json`

```json
{
  "has_explicit_completeness_info": true,
  "overall_completeness": 0.97,
  "fields": {
    "customer_id": {
      "completeness": 1.0,
      "required": true,
      "description": "Primary identifier, never missing"
    },
    "email": {
      "completeness": 0.95,
      "required": true,
      "missing_values": ["", "N/A", "null", "none"],
      "missing_reason": "Customer opted out of email communications"
    },
    "age": {
      "completeness": 0.92,
      "required": false,
      "missing_values": [null, -1],
      "missing_reason": "Customer chose not to provide age"
    },
    "purchase_amount": {
      "completeness": 1.0,
      "required": true
    },
    "membership_level": {
      "completeness": 0.98,
      "required": true,
      "missing_reason": "New customers with pending assignment"
    }
  },
  "sections": {
    "personal_info": {
      "fields": ["customer_id", "email", "age"],
      "completeness": 0.96,
      "required": true
    },
    "purchase_info": {
      "fields": ["purchase_amount", "membership_level"],
      "completeness": 0.99,
      "required": true
    }
  }
}
```

### Key Elements for Completeness Metadata
- **overall_completeness**: The overall data completeness ratio (0-1)
- **required**: Whether a field must be present
- **missing_values**: Values that should be interpreted as missing
- **missing_reason**: Context about why values might be missing
- **sections**: Logical groupings of fields with section-level completeness

## Enhancing Freshness

The freshness metadata helps agents understand how recent the data is.

### Example: `customer_data.freshness.json`

```json
{
  "has_explicit_freshness_info": true,
  "dataset_timestamp": "2025-05-23T08:30:00Z",
  "update_frequency": "daily",
  "generation_process": "nightly batch process",
  "freshness_sla": {
    "max_age_hours": 24,
    "meets_sla": true
  },
  "fields": {
    "customer_id": {
      "timestamp_field": false
    },
    "email": {
      "timestamp_field": false,
      "last_verified_timestamp": "2025-05-20T00:00:00Z",
      "verification_frequency": "monthly"
    },
    "age": {
      "timestamp_field": false,
      "last_updated_timestamp": "2025-04-15T00:00:00Z",
      "update_frequency": "yearly"
    },
    "purchase_amount": {
      "timestamp_field": false
    },
    "last_purchase_date": {
      "timestamp_field": true,
      "timestamp_format": "YYYY-MM-DD",
      "timestamp_timezone": "UTC"
    },
    "membership_level": {
      "timestamp_field": false,
      "last_updated_timestamp": "2025-05-23T00:00:00Z",
      "time_sensitivity": "medium"
    }
  },
  "historical_updates": [
    {"timestamp": "2025-05-22T08:30:00Z", "description": "Daily update"},
    {"timestamp": "2025-05-21T08:30:00Z", "description": "Daily update"},
    {"timestamp": "2025-05-20T08:30:00Z", "description": "Daily update"}
  ]
}
```

### Key Elements for Freshness Metadata
- **dataset_timestamp**: When the data was last updated
- **update_frequency**: How often the data is updated
- **freshness_sla**: Service level agreement for data freshness
- **timestamp_field**: Fields that contain timestamp information
- **time_sensitivity**: How quickly data value degrades with time
- **historical_updates**: Record of past update history

## Enhancing Consistency

The consistency metadata helps agents understand logical relationships between data elements.

### Example: `customer_data.consistency.json`

```json
{
  "has_explicit_consistency_info": true,
  "rules": [
    {
      "id": "CS.1.1",
      "name": "membership_level_purchase_threshold",
      "description": "Membership level must correspond to purchase thresholds",
      "fields": ["membership_level", "lifetime_value"],
      "condition": "if membership_level=='platinum' then lifetime_value >= 10000",
      "valid": true,
      "failure_examples": []
    },
    {
      "id": "CS.2.1",
      "name": "age_senior_discount",
      "description": "Senior discount only applies to customers over 65",
      "fields": ["age", "has_senior_discount"],
      "condition": "if has_senior_discount==true then age >= 65",
      "valid": false,
      "failure_examples": [
        {"age": 42, "has_senior_discount": true},
        {"age": 58, "has_senior_discount": true}
      ]
    },
    {
      "id": "CS.3.1",
      "name": "purchase_count_sum",
      "description": "Total purchases must equal sum of purchase categories",
      "fields": ["total_purchases", "online_purchases", "in_store_purchases"],
      "condition": "total_purchases == online_purchases + in_store_purchases",
      "valid": true,
      "failure_examples": []
    }
  ],
  "cross_dataset_consistency": [
    {
      "id": "CS.6.1",
      "name": "inventory_balance",
      "description": "Product inventory must match across sales and inventory systems",
      "related_dataset": "inventory.csv",
      "condition": "customer_data.product_count == inventory.available_count",
      "valid": true
    }
  ],
  "overall_consistency_valid": false
}
```

### Key Elements for Consistency Metadata
- **rules**: Specific consistency rules to apply
- **fields**: Which fields are involved in each rule
- **condition**: Logical condition that should be true
- **valid**: Whether the rule passes for this dataset
- **failure_examples**: Examples of inconsistencies found
- **cross_dataset_consistency**: Rules that span multiple datasets

## Enhancing Plausibility

The plausibility metadata helps agents identify values that are technically valid but contextually unreasonable.

### Example: `customer_data.plausibility.json`

```json
{
  "has_explicit_plausibility_info": true,
  "rule_results": [
    {
      "id": "P.1.0",
      "rule_name": "Age distribution",
      "type": "outlier_detection",
      "field": "age",
      "valid": false,
      "message": "Several age values are statistical outliers",
      "examples": [112, 115],
      "statistics": {
        "mean": 42.7,
        "std_dev": 14.2,
        "outlier_threshold": 3.0
      }
    },
    {
      "id": "P.2.0",
      "rule_name": "Purchase amount by category",
      "type": "domain_specific",
      "field": "purchase_amount",
      "condition": "category == 'Groceries' AND purchase_amount < 2000",
      "valid": false,
      "message": "Grocery purchases should be under $2000",
      "examples": [4521.77, 3298.45]
    },
    {
      "id": "P.3.0",
      "rule_name": "Purchase frequency relationship",
      "type": "relationship_plausibility",
      "fields": ["purchase_frequency", "total_purchases"],
      "valid": true,
      "message": "Purchase frequency corresponds to total purchase count"
    },
    {
      "id": "P.4.0",
      "rule_name": "Seasonal purchase patterns",
      "type": "temporal_plausibility",
      "field": "purchase_date",
      "valid": true,
      "message": "Purchase patterns follow expected seasonal trends"
    }
  ],
  "valid_overall": false,
  "communication_format": "json"
}
```

### Key Elements for Plausibility Metadata
- **rule_results**: Results of plausibility checks
- **type**: The type of plausibility rule (outlier, domain-specific, etc.)
- **field/fields**: Which fields are involved in each rule
- **condition**: Specific condition defining plausible values
- **valid**: Whether the data passes this plausibility rule
- **examples**: Examples of implausible values found
- **statistics**: Statistical basis for outlier detection

## Integrating Multiple Dimensions

While each dimension has its own metadata file, they work together as a cohesive system:

1. **Validity** establishes basic correctness of data formats and ranges
2. **Completeness** identifies what data is missing and why
3. **Freshness** provides temporal context for interpreting the data
4. **Consistency** ensures logical relationships are maintained
5. **Plausibility** catches unusual values that might technically be valid

## Generating Metadata Files

ADRI includes utilities to help generate metadata templates:

```python
from adri.utils import generate_metadata_template

# Generate a template based on analyzing your data source
generate_metadata_template("customer_data.csv", dimensions=["validity", "plausibility"])
```

This will analyze your data and create initial template files that you can customize.

## Best Practices

1. **Start Small**: Begin with the dimensions most critical to your agent applications
2. **Be Explicit**: Clearly document expected formats, ranges, and relationships
3. **Include Context**: Provide explanations about why values might be missing or unusual
4. **Update Regularly**: Keep metadata in sync with your evolving data
5. **Automate Where Possible**: Integrate metadata generation into your ETL processes

## Conclusion

Enhancing your data sources with explicit reliability metadata is one of the most powerful ways to improve your Agent Data Readiness Index scores. More importantly, it provides crucial context that enables agents to make better decisions when processing your data.

For specific examples and templates for different data types, see the examples in the sections below.
