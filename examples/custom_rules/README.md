# Custom Rules Examples

This directory contains working examples of custom ADRI rules that you can use as templates for your own rules.

## Quick Start

1. Copy any example rule to your project
2. Modify the rule logic for your needs
3. Register it with ADRI
4. Configure and use in assessments

## Example Rules

### 1. Business Email Rule (`business_email_rule.py`)
**Purpose**: Validates that email addresses are from business domains, not personal ones.

**Key Features**:
- Configurable list of personal domains to block
- Returns ratio of business vs personal emails
- Handles missing email columns gracefully

**Usage**:
```python
from business_email_rule import BusinessEmailRule

# Rule is auto-registered, just configure it:
config = {
    'custom_business_email': {
        'enabled': True,
        'threshold': 0.95,  # Require 95% business emails
        'personal_domains': ['gmail.com', 'yahoo.com']  # Customize blocklist
    }
}
```

### 2. Duplicate Detection Rule (`duplicate_detection_rule.py`)
**Purpose**: Identifies duplicate records based on configurable key fields.

**Key Features**:
- Configurable key fields for duplicate checking
- Shows top duplicate groups
- Supports multi-field composite keys

**Usage**:
```python
from duplicate_detection_rule import DuplicateDetectionRule

config = {
    'custom_duplicate_detection': {
        'enabled': True,
        'threshold': 0.01,  # Allow up to 1% duplicates
        'key_fields': ['customer_id', 'transaction_date']
    }
}
```

### 3. Revenue Logic Rule (`revenue_logic_rule.py`)
**Purpose**: Validates that revenue calculations follow business logic.

**Key Features**:
- Cross-field validation (revenue = quantity × price × (1 - discount))
- Configurable tolerance for rounding errors
- Identifies systematic calculation errors

**Usage**:
```python
from revenue_logic_rule import RevenueLogicRule

config = {
    'custom_revenue_logic': {
        'enabled': True,
        'threshold': 0.99,  # Require 99% accuracy
        'tolerance': 0.01   # Allow 1 cent rounding error
    }
}
```

## Test Data

The `test_data/` directory contains sample CSV files demonstrating each rule:

- `business_emails.csv` - Mix of business and personal email addresses
- `duplicate_records.csv` - Dataset with intentional duplicates
- `revenue_data.csv` - Sales data with some calculation errors

## Running the Examples

### Option 1: Standalone Testing
Each rule file can be run directly to see it in action:

```bash
python business_email_rule.py
python duplicate_detection_rule.py
python revenue_logic_rule.py
```

### Option 2: Integration with ADRI
Use the rules in a full ADRI assessment:

```python
from adri import DataSourceAssessor

# Import your custom rules (auto-registers them)
import business_email_rule
import duplicate_detection_rule
import revenue_logic_rule

# Configure and assess
assessor = DataSourceAssessor()
assessor.config.update({
    'custom_business_email': {'enabled': True},
    'custom_duplicate_detection': {'enabled': True},
    'custom_revenue_logic': {'enabled': True}
})

report = assessor.assess('your_data.csv')
print(report)
```

## Creating Your Own Rules

1. **Start with a template**: Copy the example closest to your needs
2. **Update metadata**: Change rule_id, name, description
3. **Implement logic**: Modify the evaluate() method
4. **Test thoroughly**: Use the test data pattern shown here
5. **Document well**: Help others understand your rule

## Best Practices Demonstrated

- **Graceful handling** of missing columns
- **Configurable parameters** via self.params
- **Clear narratives** for AI consumption
- **Detailed findings** for human review
- **Performance consideration** for large datasets

## Contributing

If you create a useful rule, consider contributing it back:
1. Ensure it follows ADRI patterns
2. Include test data
3. Document configuration options
4. Submit a PR to the ADRI repository

Happy rule building! 🚀
