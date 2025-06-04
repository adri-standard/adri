# ADRI Template Guard

## Overview

The Template Guard is a protective layer that ensures ADRI handles template issues gracefully without hanging or crashing. It validates templates before use and provides fallback mechanisms when templates are invalid or missing.

## Key Features

### 1. **Pre-flight Validation**
- Checks if template files exist before attempting to load them
- Validates file extensions (must be `.yaml` or `.yml`)
- Ensures files are readable

### 2. **Content Validation**
- Validates YAML syntax
- Checks for required sections (template, requirements, dimensions)
- Validates dimension names and rule weights
- Ensures rules sum to exactly 20 points per dimension

### 3. **Auto-fixing Capabilities**
- Adds missing dimension weights (defaults to 1.0)
- Adds missing `enabled` flags to rules (defaults to true)
- Calculates `overall_minimum` from dimension minimums if missing

### 4. **Fallback Mechanism**
- Provides an emergency fallback template when:
  - Template file is missing
  - Template has unfixable validation errors
  - Template loading fails for any reason
- The fallback template provides basic assessment with reasonable defaults

## Implementation

### TemplateGuard Class (`adri/templates/guard.py`)

```python
from adri.templates.guard import TemplateGuard

# Validate template source
is_valid, error = TemplateGuard.validate_template_source("path/to/template.yaml")

# Validate template content
is_valid, errors = TemplateGuard.validate_template_content(template_dict)

# Get fallback template
fallback = TemplateGuard.get_fallback_template()

# Fix common template issues
fixed_template, warnings = TemplateGuard.validate_and_fix_template(template_dict)
```

### Integration with DataSourceAssessor

The assessor now uses a safe template loader that:
1. Validates the template source
2. Attempts to load and validate the template
3. Tries to fix common issues
4. Falls back to emergency template if needed

```python
assessor = DataSourceAssessor()

# Will use fallback if template is invalid
report = assessor.assess_file("data.csv", template="/missing/template.yaml")
```

## Error Scenarios Handled

1. **Missing Template File**
   - Falls back to emergency template
   - Assessment continues with basic rules

2. **Invalid YAML Syntax**
   - Falls back to emergency template
   - Logs error for debugging

3. **Missing Required Fields**
   - Attempts to fix if possible
   - Falls back if unfixable

4. **Invalid Dimension Weights**
   - Validates that rules sum to 20 points
   - Reports specific errors

5. **Unknown Dimensions**
   - Rejects templates with invalid dimension names
   - Ensures compatibility with ADRI's dimension system

## Emergency Fallback Template

The fallback template (`fallback/emergency`) provides:
- Overall minimum score: 50
- Basic rules for all 5 dimensions
- Each dimension gets one simple rule worth 20 points
- No certification requirements

## Testing

Comprehensive test suite in `tests/unit/templates/test_guard.py` covers:
- Source validation
- Content validation
- Auto-fixing functionality
- Safe loader behavior
- Fallback scenarios

## Example Usage

See `examples/template_guard_demo.py` for a complete demonstration of:
- Handling missing templates
- Processing invalid templates
- Auto-fixing fixable issues
- Working with valid templates

## Benefits

1. **Robustness** - ADRI won't crash due to template issues
2. **User-Friendly** - Clear error messages and automatic fixes
3. **Fail-Safe** - Always able to perform basic assessment
4. **Debugging** - Detailed logging of what went wrong
5. **Flexibility** - Can fix common mistakes automatically

## Future Enhancements

Potential improvements could include:
- Template schema versioning
- More sophisticated auto-fix rules
- Template migration utilities
- Enhanced validation for business rules
- Template composition/inheritance support
