# ADRI Standards Documentation

ADRI standards define data quality requirements using YAML files. This guide covers creating, using, and managing standards.

## What is an ADRI Standard?

A standard defines **what "good quality" looks like** for your specific data type. Each standard contains:
- **Metadata** (name, version, authority)  
- **Overall score requirements** (minimum 75/100)
- **Field-specific rules** (type, format, constraints)
- **Dimension requirements** (validity, completeness, etc.)

## Standard Structure

```yaml
standards:
  id: customer_data_standard
  name: Customer Data Standard  
  version: 1.0.0
  authority: Data Team
  description: Quality requirements for customer data

requirements:
  overall_minimum: 80.0
  
  field_requirements:
    customer_id:
      type: string
      nullable: false
      pattern: "^CUST_[0-9]+$"
    
    email:
      type: string  
      nullable: false
      pattern: "^[^@]+@[^@]+\\.[^@]+$"
    
    age:
      type: integer
      nullable: false
      min_value: 0
      max_value: 120
  
  dimension_requirements:
    validity:
      minimum_score: 17.0
    completeness:
      minimum_score: 18.0
    consistency:
      minimum_score: 15.0
    freshness:
      minimum_score: 16.0
    plausibility:
      minimum_score: 14.0
```

## Working with Standards

### Creating Standards

**Option 1: Auto-generate from data**
```bash
adri generate-standard customer_data.csv
```

**Option 2: Manual creation**
```bash
# Create YAML file manually
vim ADRI/dev/standards/my_standard.yaml
```

### Using Standards

```python
from adri import adri_protected

@adri_protected(standard="customer_data_standard")
def process_customers(customer_data):
    return analyze_customers(customer_data)
```

### Managing Standards

```bash
# List available standards
adri list-standards

# Show standard details
adri show-standard customer_data_standard --verbose

# Validate standard format
adri validate-standard customer_data_standard
```

## Field Requirements

### Data Types

| Type | Description | Example |
|------|-------------|---------|
| `string` | Text data | "John Doe" |
| `integer` | Whole numbers | 42 |  
| `float` | Decimal numbers | 3.14159 |
| `boolean` | True/False | true |
| `date` | Date values | "2024-01-15" |
| `datetime` | Date with time | "2024-01-15T10:30:00Z" |

### Constraints

**String Constraints:**
```yaml
email:
  type: string
  nullable: false
  pattern: "^[^@]+@[^@]+\\.[^@]+$"  # Email format
  min_length: 5
  max_length: 100
```

**Numeric Constraints:**
```yaml
age:
  type: integer
  nullable: false
  min_value: 0
  max_value: 120
```

**List of Allowed Values:**
```yaml
status:
  type: string
  nullable: false
  allowed_values: ["active", "inactive", "pending"]
```

## Dimension Requirements

ADRI evaluates 5 quality dimensions:

### Validity (Format Correctness)
- **What it checks:** Emails, dates, phone numbers follow correct format
- **Typical minimum:** 15-19/20 (depending on criticality)
- **Example failure:** Email "not-an-email" instead of "user@domain.com"

### Completeness (Missing Data)
- **What it checks:** Required fields are not null/empty
- **Typical minimum:** 15-19/20 
- **Example failure:** Customer record missing required name field

### Consistency (Format Consistency)
- **What it checks:** Same data type/format across all records
- **Typical minimum:** 12-16/20
- **Example failure:** Dates in mixed formats "2024-01-15" and "01/15/2024"

### Freshness (Data Age)
- **What it checks:** Data is recent enough for business needs
- **Typical minimum:** 15-18/20
- **Example failure:** Customer data from 2019 in 2024 system

### Plausibility (Realistic Values)
- **What it checks:** Values make business sense
- **Typical minimum:** 12-16/20
- **Example failure:** Customer age of -5 or 250 years

## Standards Management

### Bundled Standards

ADRI ships with built-in standards for common data types:
- `customer_data_standard` - Customer information
- `financial_data_standard` - Financial transactions
- `user_profile_standard` - User profiles  
- `order_data_standard` - E-commerce orders

```bash
adri list-standards  # See all bundled standards
```

### Custom Standards

Create standards for your specific data:

```bash
# Generate from your data
adri generate-standard my_data.csv

# Edit the generated standard
vim my_data_ADRI_standard.yaml

# Test your standard
adri assess my_data.csv --standard my_data_ADRI_standard
```

### Standard Versioning

```yaml
standards:
  id: customer_data_standard
  name: Customer Data Standard
  version: 2.1.0  # Semantic versioning
  authority: Data Engineering Team
  effective_date: "2024-03-01T00:00:00Z"
```

## Advanced Features

### Environment-Specific Standards

```yaml
# Development environment (more permissive)
requirements:
  overall_minimum: 70.0
  
# Production environment (strict)  
requirements:
  overall_minimum: 90.0
```

### Conditional Requirements

```yaml
# Different rules for different customer types
field_requirements:
  premium_features:
    type: string
    nullable: true  # Only required for premium customers
    conditional: "customer_tier == 'premium'"
```

## CLI Commands Reference

```bash
# Standard management
adri generate-standard data.csv               # Create from data
adri validate-standard my_standard            # Validate format
adri list-standards                           # List available
adri show-standard my_standard --verbose      # Show details

# Assessment with standards
adri assess data.csv --standard my_standard   # Test data quality
```

## Best Practices

1. **Start with generated standards** then customize as needed
2. **Use semantic versioning** for standard versions
3. **Document business rules** in the description field
4. **Test standards thoroughly** before production use
5. **Review and update standards** as data patterns evolve
6. **Use environment-specific requirements** for dev vs prod

For implementation examples, see [Guard Modes Documentation](./guard_modes.md) and [Installation Guide](./install.md).
