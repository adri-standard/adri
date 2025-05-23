# ADRI Diagnostic Rules

## Plausibility Dimension

| Rule ID | Name | Description | Parameters |
|---------|------|-------------|------------|
| `plausibility.domain_specific` | Domain-Specific Validation | Applies specialized validation rules based on the data domain. | enabled, weight, domains |
| `plausibility.outlier_detection` | Statistical Outlier Detection | Identifies abnormal values that deviate significantly from typical patterns. | enabled, method, threshold, weight, analyze_numeric_only |
| `plausibility.pattern_consistency` | Pattern Consistency Check | Checks if text and identifier fields follow consistent patterns. | enabled, weight, min_pattern_confidence, analyze_id_columns, analyze_text_columns |

## Validity Dimension

| Rule ID | Name | Description | Parameters |
|---------|------|-------------|------------|
| `validity.format_consistency` | Format Consistency | Checks if text values follow consistent formatting conventions. | enabled, weight, date_formats |
| `validity.range_validation` | Range Validation | Checks if numeric values fall within expected ranges. | enabled, weight, detect_outliers, outlier_threshold |
| `validity.type_consistency` | Type Consistency | Checks if values in columns have consistent data types. | enabled, weight, threshold, analyze_all_columns |

