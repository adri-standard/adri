# ADRI Diagnostic Rules System

This module implements the diagnostic rule system for the Agent Data Readiness Index (ADRI). It provides a flexible, extensible framework for evaluating data quality across multiple dimensions.

## Architecture

The rule system is built around the following components:

- **DiagnosticRule**: Base class for all rules
- **RuleRegistry**: Registry that maintains a catalog of available rules
- **Rule Implementations**: Specific rule implementations for each dimension
- **Configuration**: Settings that control rule behavior

### Rule Structure

Rules are organized by dimension, with each rule having:
- A unique ID (e.g., `validity.type_consistency`)
- Parameters that control its behavior
- An `evaluate()` method that analyzes data
- A `generate_narrative()` method that produces AI-friendly descriptions

### Rule Registry

The registry maintains a catalog of all available rules and provides methods to:
- Register new rules
- Create rule instances
- Get rules by dimension
- Generate documentation

## Available Rules

The following dimensions and rules are currently implemented:

### Validity Dimension

Rules that check if data values adhere to expected types, ranges, and formats.

- `validity.type_consistency`: Checks if values have consistent data types
- `validity.range_validation`: Validates numeric values against expected ranges
- `validity.format_consistency`: Checks text formats (dates, identifiers, etc.)

### Plausibility Dimension

Rules that check if data values are believable and realistic.

- `plausibility.outlier_detection`: Identifies statistical outliers
- `plausibility.pattern_consistency`: Checks consistency of text patterns
- `plausibility.domain_specific`: Applies domain-specific validations

## Customization

Rules can be customized through configuration files. See `adri/config/example_config.yaml` for an example.

Key customization options include:
- Enabling/disabling specific rules
- Adjusting thresholds and sensitivities
- Setting weights for different rules
- Configuring dimension-specific parameters

## Integration with Assessment

Rules are used by the assessment system to:
1. Evaluate data sources against each dimension
2. Calculate dimension scores
3. Generate an overall ADRI score
4. Produce narratives for AI consumption

## Examples

- `demo.py`: Demonstrates the rule registry
- `example_evaluation.py`: Shows how to evaluate rules on actual data
- `adri/config/show_custom_config.py`: Demonstrates custom configurations

## Extending the System

To add a new rule:

1. Create a new rule class that inherits from `DiagnosticRule`
2. Implement `evaluate()` and `generate_narrative()` methods
3. Decorate with `@RuleRegistry.register`
4. Add default settings to `adri/config/defaults.py`

Example:

```python
@RuleRegistry.register
class MyNewRule(DiagnosticRule):
    rule_id = "dimension.my_new_rule"
    dimension = "dimension"
    name = "My New Rule"
    description = "Description of what the rule does"
    
    def evaluate(self, data):
        # Implementation
        
    def generate_narrative(self, result):
        # Implementation
