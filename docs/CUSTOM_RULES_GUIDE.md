# Creating Custom ADRI Rules

This guide shows you how to create custom rules for ADRI to meet your specific data quality needs. Whether you need industry-specific validations, business logic checks, or specialized pattern detection, custom rules give you the flexibility to extend ADRI's capabilities.

## Quick Start Example

Here's a simple custom rule that validates business email addresses:

```python
from adri.rules.base import DiagnosticRule
from adri.rules.registry import RuleRegistry
import pandas as pd
from typing import Dict, Any

@RuleRegistry.register
class BusinessEmailRule(DiagnosticRule):
    """Ensures email addresses are from business domains, not personal ones."""
    
    rule_id = "custom.business_email"
    dimension = "validity"
    name = "Business Email Validation"
    description = "Checks that email addresses are from business domains"
    version = "1.0.0"
    
    def evaluate(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Check if email addresses are from business domains."""
        if 'email' not in data.columns:
            return {
                "score": self.params.get("weight", 1.0),
                "valid": True,
                "findings": ["No email column found to validate"]
            }
        
        personal_domains = self.params.get("personal_domains", [
            'gmail.com', 'yahoo.com', 'outlook.com', 'hotmail.com',
            'aol.com', 'icloud.com', 'mail.com', 'protonmail.com'
        ])
        
        emails = data['email'].dropna()
        if len(emails) == 0:
            return {
                "score": self.params.get("weight", 1.0),
                "valid": True,
                "findings": ["No emails to validate"]
            }
        
        # Extract domains
        domains = emails.str.lower().str.extract(r'@(.+)$')[0]
        personal_count = domains.isin(personal_domains).sum()
        business_ratio = 1 - (personal_count / len(emails))
        
        return {
            "score": business_ratio * self.params.get("weight", 1.0),
            "valid": business_ratio >= self.params.get("threshold", 0.95),
            "findings": [
                f"Business email ratio: {business_ratio:.1%}",
                f"Personal emails found: {personal_count}"
            ],
            "details": {
                "personal_count": int(personal_count),
                "total_count": len(emails),
                "business_ratio": business_ratio
            }
        }
    
    def generate_narrative(self, result: Dict[str, Any]) -> str:
        """Generate AI-friendly description of the results."""
        ratio = result.get("details", {}).get("business_ratio", 0)
        return f"Email validation shows {ratio:.1%} business addresses. " + \
               f"{result['findings'][1]}. Rule {'passed' if result['valid'] else 'failed'}."
```

## Anatomy of a Custom Rule

Every ADRI rule follows this structure:

### 1. **Imports and Registration**
```python
from adri.rules.base import DiagnosticRule
from adri.rules.registry import RuleRegistry
import pandas as pd
from typing import Dict, Any

@RuleRegistry.register  # This decorator registers your rule
class YourCustomRule(DiagnosticRule):
```

### 2. **Rule Metadata**
```python
rule_id = "custom.your_rule"      # Unique identifier
dimension = "validity"            # Which dimension (validity/completeness/etc)
name = "Your Rule Name"          # Human-readable name
description = "What it does"      # Clear description
version = "1.0.0"                # Version tracking
```

### 3. **The evaluate() Method**
```python
def evaluate(self, data: pd.DataFrame) -> Dict[str, Any]:
    """Main evaluation logic."""
    return {
        "score": 0.0-1.0,        # Normalized score
        "valid": True/False,     # Pass/fail boolean
        "findings": [...],       # List of findings
        "details": {...}         # Additional structured data
    }
```

### 4. **The generate_narrative() Method**
```python
def generate_narrative(self, result: Dict[str, Any]) -> str:
    """Convert results to AI-friendly text."""
    return "Clear description of what was found"
```

## Step-by-Step Tutorial

Let's build a duplicate detection rule from scratch:

### Step 1: Define the Rule Class

```python
from adri.rules.base import DiagnosticRule
from adri.rules.registry import RuleRegistry
import pandas as pd
from typing import Dict, Any, List, Optional

@RuleRegistry.register
class DuplicateDetectionRule(DiagnosticRule):
    """Detects duplicate records based on key fields."""
    
    rule_id = "custom.duplicate_detection"
    dimension = "consistency"
    name = "Duplicate Record Detection"
    description = "Identifies duplicate records based on configurable key fields"
    version = "1.0.0"
```

### Step 2: Implement Evaluation Logic

```python
def evaluate(self, data: pd.DataFrame) -> Dict[str, Any]:
    """Detect duplicates based on key fields."""
    # Get key fields from params or use all columns
    key_fields = self.params.get("key_fields", list(data.columns))
    
    # Validate key fields exist
    missing_fields = [f for f in key_fields if f not in data.columns]
    if missing_fields:
        return {
            "score": 0.0,
            "valid": False,
            "findings": [f"Missing key fields: {missing_fields}"],
            "details": {"missing_fields": missing_fields}
        }
    
    # Find duplicates
    duplicates = data.duplicated(subset=key_fields, keep=False)
    duplicate_count = duplicates.sum()
    duplicate_ratio = duplicate_count / len(data)
    
    # Calculate score (inverse of duplicate ratio)
    score = (1 - duplicate_ratio) * self.params.get("weight", 1.0)
    
    # Identify duplicate groups
    if duplicate_count > 0:
        duplicate_groups = data[duplicates].groupby(key_fields).size()
        top_duplicates = duplicate_groups.nlargest(5).to_dict()
    else:
        top_duplicates = {}
    
    return {
        "score": score,
        "valid": duplicate_ratio <= self.params.get("threshold", 0.01),
        "findings": [
            f"Found {duplicate_count} duplicate records ({duplicate_ratio:.1%})",
            f"Key fields checked: {', '.join(key_fields)}"
        ],
        "details": {
            "duplicate_count": int(duplicate_count),
            "duplicate_ratio": duplicate_ratio,
            "key_fields": key_fields,
            "top_duplicates": top_duplicates
        }
    }
```

### Step 3: Add Narrative Generation

```python
def generate_narrative(self, result: Dict[str, Any]) -> str:
    """Generate AI-friendly description."""
    details = result.get("details", {})
    count = details.get("duplicate_count", 0)
    ratio = details.get("duplicate_ratio", 0)
    
    if count == 0:
        return "No duplicate records found. Data consistency is excellent."
    
    narrative = f"Found {count} duplicate records ({ratio:.1%} of total). "
    
    # Add details about top duplicates if available
    top_dupes = details.get("top_duplicates", {})
    if top_dupes:
        narrative += f"Most common duplicate appears {max(top_dupes.values())} times. "
    
    narrative += "Rule " + ("passed" if result["valid"] else "failed") + "."
    return narrative
```

### Step 4: Use Your Custom Rule

```python
# Register your rule (happens automatically with @RuleRegistry.register)
# Then use it in assessments:

from adri import DataSourceAssessor

assessor = DataSourceAssessor()

# Configure the rule
assessor.config['custom_duplicate_detection'] = {
    'enabled': True,
    'weight': 1.0,
    'threshold': 0.01,  # Allow up to 1% duplicates
    'key_fields': ['customer_id', 'order_date']
}

# Run assessment
report = assessor.assess("data.csv")
```

## Advanced Example: Business Logic Validation

Here's a more complex rule that validates cross-field business logic:

```python
@RuleRegistry.register
class RevenueLogicRule(DiagnosticRule):
    """Validates revenue calculations and business logic."""
    
    rule_id = "custom.revenue_logic"
    dimension = "plausibility"
    name = "Revenue Business Logic"
    description = "Ensures revenue calculations follow business rules"
    version = "1.0.0"
    
    def evaluate(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Validate revenue = quantity * unit_price * (1 - discount)."""
        required_cols = ['quantity', 'unit_price', 'discount', 'revenue']
        missing = [c for c in required_cols if c not in data.columns]
        
        if missing:
            return {
                "score": 0.0,
                "valid": False,
                "findings": [f"Missing required columns: {missing}"],
                "details": {"missing_columns": missing}
            }
        
        # Calculate expected revenue
        expected_revenue = (
            data['quantity'] * 
            data['unit_price'] * 
            (1 - data['discount'])
        )
        
        # Check accuracy within tolerance
        tolerance = self.params.get("tolerance", 0.01)  # 1 cent default
        accurate = abs(data['revenue'] - expected_revenue) <= tolerance
        accuracy_rate = accurate.sum() / len(data)
        
        # Find discrepancies
        discrepancies = data[~accurate].copy()
        discrepancies['expected'] = expected_revenue[~accurate]
        discrepancies['difference'] = discrepancies['revenue'] - discrepancies['expected']
        
        # Analyze patterns in discrepancies
        findings = [f"Revenue accuracy: {accuracy_rate:.1%}"]
        
        if len(discrepancies) > 0:
            avg_error = discrepancies['difference'].abs().mean()
            findings.append(f"Average discrepancy: ${avg_error:.2f}")
            
            # Check for systematic errors
            if discrepancies['difference'].std() < tolerance:
                findings.append("Errors appear systematic - check calculation logic")
        
        return {
            "score": accuracy_rate * self.params.get("weight", 1.0),
            "valid": accuracy_rate >= self.params.get("threshold", 0.99),
            "findings": findings,
            "details": {
                "accuracy_rate": accuracy_rate,
                "discrepancy_count": len(discrepancies),
                "total_records": len(data),
                "largest_errors": discrepancies.nlargest(5, 'difference')[
                    ['revenue', 'expected', 'difference']
                ].to_dict('records') if len(discrepancies) > 0 else []
            }
        }
    
    def generate_narrative(self, result: Dict[str, Any]) -> str:
        """Generate detailed narrative about revenue validation."""
        details = result.get("details", {})
        accuracy = details.get("accuracy_rate", 0)
        
        narrative = f"Revenue calculations show {accuracy:.1%} accuracy. "
        
        if details.get("discrepancy_count", 0) > 0:
            narrative += f"{details['discrepancy_count']} records have calculation errors. "
            
            # Add info about largest errors
            largest = details.get("largest_errors", [])
            if largest:
                max_error = max(abs(e['difference']) for e in largest)
                narrative += f"Largest discrepancy: ${max_error:.2f}. "
        
        narrative += "Rule " + ("passed" if result["valid"] else "failed") + "."
        return narrative
```

## Best Practices

### 1. **Consistent Return Structure**
Always return the standard dictionary with score, valid, findings, and details:
```python
return {
    "score": 0.0-1.0,      # Normalized score
    "valid": bool,         # Pass/fail
    "findings": [...],     # Human-readable findings
    "details": {...}       # Structured data for analysis
}
```

### 2. **Parameterization**
Make rules configurable through `self.params`:
```python
threshold = self.params.get("threshold", 0.95)  # Default 95%
weight = self.params.get("weight", 1.0)         # Default weight 1.0
custom_list = self.params.get("domains", [...]) # Custom lists
```

### 3. **Error Handling**
Handle missing columns and edge cases gracefully:
```python
if 'required_column' not in data.columns:
    return {
        "score": self.params.get("weight", 1.0),
        "valid": True,
        "findings": ["Required column not found - skipping rule"]
    }
```

### 4. **Performance Considerations**
- Use vectorized pandas operations instead of loops
- For large datasets, consider sampling:
```python
if len(data) > 100000:
    sample = data.sample(n=10000, random_state=42)
    # Run expensive operations on sample
```

### 5. **Clear Narratives**
Write narratives that are:
- Concise and factual
- Include key metrics
- Explain pass/fail status
- Suitable for AI agents to parse

## Configuration

Configure custom rules in your ADRI config:

```yaml
# config.yaml
custom_business_email:
  enabled: true
  weight: 1.0
  threshold: 0.95
  personal_domains:
    - gmail.com
    - yahoo.com
    - customdomain.com

custom_duplicate_detection:
  enabled: true
  weight: 2.0  # Higher weight = more important
  threshold: 0.01
  key_fields:
    - customer_id
    - transaction_date

custom_revenue_logic:
  enabled: true
  weight: 1.5
  threshold: 0.99
  tolerance: 0.01  # 1 cent tolerance
```

## Testing Your Rules

Always test custom rules with various data scenarios:

```python
import pandas as pd
from adri.rules.registry import RuleRegistry

# Get your registered rule
rule = RuleRegistry.create_rule("custom.business_email")

# Test with sample data
test_data = pd.DataFrame({
    'email': [
        'john@company.com',      # Business
        'jane@gmail.com',        # Personal
        'bob@enterprise.org',    # Business
        'alice@yahoo.com',       # Personal
    ]
})

result = rule.evaluate(test_data)
print(f"Score: {result['score']}")
print(f"Valid: {result['valid']}")
print(f"Narrative: {rule.generate_narrative(result)}")
```

## Common Patterns

### Pattern 1: Threshold-Based Rules
```python
metric = calculate_metric(data)
score = metric * self.params.get("weight", 1.0)
valid = metric >= self.params.get("threshold", 0.95)
```

### Pattern 2: Whitelist/Blacklist Rules
```python
allowed_values = self.params.get("allowed_values", [...])
invalid = ~data['column'].isin(allowed_values)
invalid_ratio = invalid.sum() / len(data)
score = (1 - invalid_ratio) * self.params.get("weight", 1.0)
```

### Pattern 3: Cross-Field Validation
```python
condition = (data['field1'] > data['field2']) & (data['field3'] == 'X')
violation_ratio = (~condition).sum() / len(data)
score = (1 - violation_ratio) * self.params.get("weight", 1.0)
```

## Next Steps

1. **Start Simple**: Begin with a basic rule like email validation
2. **Test Thoroughly**: Use diverse test data to verify behavior
3. **Iterate**: Refine based on real-world results
4. **Share**: Contribute useful rules back to the community

For more examples, see the `examples/custom_rules/` directory.

## Getting Help

- Check existing rules in `adri/rules/` for patterns
- See `examples/custom_rules/` for working examples
- Join the ADRI community for support
- Submit issues for rule ideas or bugs

Remember: The best rules are those that catch real data quality issues in your domain. Start with your most common data problems and build from there!
