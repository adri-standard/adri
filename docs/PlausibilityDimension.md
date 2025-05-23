# Plausibility Dimension

The **Plausibility** dimension of the Agent Data Readiness Index (ADRI) evaluates whether data values are reasonable based on context and domain knowledge, and most importantly, whether this contextual information is explicitly communicated to agents.

## Overview

Data plausibility refers to the reasonableness of values within their domain context. While validity ensures data follows expected patterns and formats, plausibility goes further by assessing if values make logical sense in their specific context, even if they are technically valid. For example, a $10,000 toaster is valid (it's a number in currency format) but implausible (it falls far outside normal price ranges for that product category).

The plausibility dimension is particularly important for autonomous agents because their decision-making improves when they can differentiate between valid-but-unlikely data and truly plausible information.

## Scoring Components

The plausibility dimension (maximum score: 20 points) evaluates the following aspects:

1. **Rules Defined (4 points)**: The quantity and quality of plausibility rules defined for the data.
   - 4 points: 10+ well-defined plausibility rules
   - 3 points: 5-9 plausibility rules
   - 2 points: 2-4 plausibility rules
   - 1 point: 1 plausibility rule
   - 0 points: No plausibility rules defined

2. **Rule Types (3 points)**: The diversity of plausibility rules, particularly checks for statistical outliers.
   - 3 points: Multiple rule types including outlier detection
   - 0 points: No outlier detection rules

3. **Rule Validity (4 points)**: Whether the rules are satisfied by the data.
   - 4 points: All plausibility rules pass
   - 3 points: Less than 20% of rules fail
   - 2 points: 20-50% of rules fail
   - 1 point: Over 50% of rules fail
   - 0 points: No rules defined or all fail

4. **Domain-Specific Checks (3 points)**: Rules that incorporate domain knowledge about what constitutes plausible data.
   - 3 points: Domain-specific plausibility rules defined and implemented
   - 0 points: No domain-specific plausibility rules

5. **Explicit Communication (6 points)**: Whether plausibility information is explicitly communicated to agents.
   - 6 points: Plausibility results explicitly communicated to agents
   - 0 points: No explicit communication of plausibility information

## Implementation

The plausibility dimension is implemented in `adri/dimensions/plausibility.py`. The assessor evaluates plausibility through the following process:

1. Check if plausibility rules are defined
2. Examine rule types (outlier detection, domain-specific, etc.)
3. Verify if rules pass or fail
4. Assess domain-specific plausibility rules
5. Evaluate whether plausibility results are communicated to agents

## Examples

### Good Plausibility Information

```json
{
  "has_explicit_plausibility_info": true,
  "communication_format": "json",
  "explicitly_communicated": true,
  "rule_results": [
    {
      "rule_name": "Price range check for Electronics",
      "type": "domain_specific",
      "field": "price",
      "condition": "category == 'Electronics' AND price > 0.99 AND price < 2000",
      "valid": true,
      "message": "Electronics products have reasonable prices between $0.99 and $2000"
    },
    {
      "rule_name": "Quantity outlier detection",
      "type": "outlier_detection",
      "field": "quantity",
      "valid": true,
      "message": "Purchase quantities are within reasonable ranges"
    }
  ],
  "valid_overall": true
}
```

### Poor Plausibility Information

```json
{
  "has_explicit_plausibility_info": false,
  "rule_results": [],
  "valid_overall": false
}
```

## Improving Plausibility

To improve data plausibility scoring:

1. **Define clear plausibility rules**: Create explicit rules that check if data values make sense within their context
2. **Include outlier detection**: Implement statistical outlier detection to identify anomalous values
3. **Add domain-specific rules**: Create rules that incorporate domain knowledge about what constitutes plausible data
4. **Address rule violations**: Fix data that fails plausibility checks or provide clear explanations for exceptional values
5. **Explicitly communicate plausibility**: Ensure plausibility information is accessible to agents

## Configuration Options

The plausibility dimension can be configured in several ways:

```python
from adri.config.config import Configuration

# Create custom configuration
config = Configuration({
    "plausibility_scoring": {
        "MAX_RULES_DEFINED_SCORE": 4,
        "MAX_RULE_TYPES_SCORE": 3,
        "MAX_RULE_VALIDITY_SCORE": 4,
        "MAX_CONTEXT_AWARENESS_SCORE": 3,
        "MAX_EXPLICIT_COMMUNICATION_SCORE": 6,
        "REQUIRE_EXPLICIT_METADATA": True  # When True, only explicit plausibility info gets full points
    }
})
```

## Usage with File Connectors

For file-based data sources, plausibility metadata can be provided in a companion `.plausibility.json` file:

```
data_source.csv
data_source.plausibility.json
```

The `.plausibility.json` file should contain plausibility rules and results as shown in the examples above.

## Testing Plausibility

The ADRI provides an implausible test dataset in `test_datasets/implausible_dataset.csv` that contains values that are technically valid but contextually unreasonable (like $9999.99 headphones or $0.09 air fryers).

You can run a plausibility assessment example with:

```bash
python examples/plausibility/plausibility_example.py
```
