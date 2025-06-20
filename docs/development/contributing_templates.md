# Contributing Templates to ADRI

Templates are the heart of ADRI's value proposition. By contributing a template, you're helping establish industry standards for agent-ready data and enabling AI interoperability across organizations.

## 🎯 Why Contribute Templates?

- **🌍 Industry Impact**: Your templates help others in your industry ensure data quality
- **🚀 Accelerate AI Adoption**: Enable faster, more reliable AI agent deployment
- **🏆 Build Reputation**: Become recognized as a data quality expert in your domain
- **💡 Learn and Improve**: Get feedback from the community to refine your standards

## 🚀 Quick Start (5 minutes)

### 1. Find a Similar Template
```bash
# Browse existing templates
ls adri/templates/catalog/

# Look at a template structure
cat adri/templates/catalog/general/crm-sales-v1.0.0.yaml
```

### 2. Copy and Customize
```bash
# Copy the closest match as your starting point
cp adri/templates/catalog/general/crm-sales-v1.0.0.yaml \
   my-awesome-template.yaml
   
# Edit with your requirements
```

### 3. Test Your Template
```bash
# Test with sample data
from adri import DataSourceAssessor

assessor = DataSourceAssessor()
report, evaluation = assessor.assess_file_with_template(
    "sample-data.csv",
    "my-awesome-template.yaml"
)
print(f"Compliance: {evaluation.is_compliant}")
```

### 4. Submit Your Template
Create a pull request with:
- Your template file in the appropriate catalog folder
- Sample data (if possible)
- Brief documentation

## 📋 Template Anatomy

Every ADRI template has four main sections:

### 1. Template Metadata
```yaml
template:
  id: "industry-usecase-v1.0.0"  # Unique identifier
  name: "Human Readable Name"     # Clear, descriptive name
  version: "1.0.0"               # Semantic versioning
  description: "What this template validates and why"
  category: "general|financial|healthcare|retail|logistics"
  tags: ["crm", "sales", "pipeline"]  # For discovery
  
  # IMPORTANT: Specify ADRI version compatibility
  # This ensures your template works with the right ADRI version
  requires_adri: ">=0.3.0"  # or specific version like "0.3.1"
```

### 2. Pattern Matching (Discovery)
```yaml
pattern_matching:
  # Columns that MUST exist
  required_columns: 
    - "order_id"
    - "customer_id"
    - "amount"
    
  # Optional but helpful columns
  optional_columns:
    - "discount"
    - "shipping_address"
    
  # Help ADRI recognize column variations
  column_synonyms:
    amount: ["total", "price", "order_value", "payment_amount"]
    customer_id: ["client_id", "user_id", "account_id"]
    order_id: ["transaction_id", "purchase_id", "invoice_number"]
```

### 3. Requirements (Quality Thresholds)
```yaml
requirements:
  # Overall quality score needed (0-100)
  overall_minimum: 75
  
  # Per-dimension requirements
  dimension_requirements:
    validity:
      minimum_score: 16  # Strict type checking
      description: "Order data must have valid types and formats"
      
    completeness:
      minimum_score: 18  # Critical fields must be present
      description: "All required order fields must be populated"
      
    consistency:
      minimum_score: 14  # Basic consistency needed
      description: "Order totals must match line items"
      
    freshness:
      minimum_score: 15  # Recent data required
      description: "Orders should be from the last 30 days"
      
    plausibility:
      minimum_score: 12  # Realistic values
      description: "Order amounts should be within normal ranges"
```

### 4. Dimension Rules (How to Calculate Scores)

**Important**: In template mode, each dimension's rules must have weights that sum to 20 points total. This ensures fair scoring across dimensions.

```yaml
dimensions:
  validity:
    weight: 1.0  # Dimension importance in overall score
    overall_minimum: 85
    rules:
      # Total weights must sum to 20
      - type: type_consistency
        params:
          enabled: true
          weight: 12  # 12 out of 20 points
          threshold: 0.95
          analyze_all_columns: true
          
      - type: range_validation
        params:
          enabled: true
          weight: 8   # 8 out of 20 points
          min_value: 0.01
          max_value: 10000
          columns: ["amount"]
          
  completeness:
    rules:
      # Total weights must sum to 20
      - type: required_fields
        params:
          enabled: true
          weight: 15  # 15 out of 20 points - critical
          required_columns: ["order_id", "customer_id", "amount"]
          threshold: 1.0
          
      - type: population_density
        params:
          enabled: true
          weight: 5   # 5 out of 20 points
          threshold: 0.90
          check_columns: ["email", "phone", "address"]
        
  consistency:
    rules:
      # Total weights must sum to 20
      - type: cross_field
        params:
          enabled: true
          weight: 20  # All 20 points for this critical check
          validation_type: "calculation"
          formula: "total_amount == (subtotal + shipping_cost - discount_amount)"
          
  freshness:
    rules:
      # Total weights must sum to 20
      - type: timestamp_recency
        params:
          enabled: true
          weight: 10  # 10 out of 20 points
          timestamp_column: "order_date"
          max_age_days: 30
          
      - type: update_frequency
        params:
          enabled: true
          weight: 10  # 10 out of 20 points
          timestamp_column: "last_updated"
          expected_frequency_days: 1
          
  plausibility:
    rules:
      # Total weights must sum to 20
      - type: range
        params:
          enabled: true
          weight: 12  # 12 out of 20 points
          column: "amount"
          min_value: 1.00
          max_value: 10000.00
          
      - type: outlier
        params:
          enabled: true
          weight: 8   # 8 out of 20 points
          column: "amount"
          method: "zscore"
          threshold: 3.0
```

## 🔧 Step-by-Step Template Creation

### Step 1: Identify Your Use Case
Ask yourself:
- What type of data will agents process? (invoices, customer records, inventory, etc.)
- What industry is this for? (retail, finance, healthcare, etc.)
- What will AI agents do with this data? (process payments, answer questions, make predictions)
- What are the critical quality requirements?

### Step 2: Analyze Sample Data
```python
<!-- audience: ai-builders -->
# [STANDARD_CONTRIBUTOR]
# Use ADRI in discovery mode to understand your data
from adri import DataSourceAssessor

assessor = DataSourceAssessor(mode="discovery")
report = assessor.assess_file("your-sample-data.csv")

# Review the report to understand:
# - Current quality scores
# - Detected patterns
# - Potential issues
```

### Step 3: Define Pattern Matching
Start with columns that uniquely identify your data type:
```yaml
pattern_matching:
  required_columns: ["invoice_number", "amount", "due_date"]
  
  # Add synonyms for common variations
  column_synonyms:
    invoice_number: ["inv_num", "invoice_no", "bill_number"]
```

### Step 4: Set Appropriate Requirements
Consider your use case:
- **Critical Financial Data**: Set high thresholds (85-95)
- **Analytical Data**: Medium thresholds (70-85)
- **Exploratory Data**: Lower thresholds (60-75)

```yaml
requirements:
  overall_minimum: 80  # High bar for financial data
  
  dimension_requirements:
    validity:
      minimum_score: 18  # Very strict validation
    completeness:
      minimum_score: 17  # Most fields required
```

### Step 5: Define Dimension Rules
For each dimension, think about what matters:

**Validity**: What formats and types are required?
```yaml
validity:
  rules:
    - name: "Valid Email"
      column: "customer_email"
      validation:
        type: "email"
```

**Completeness**: What fields must always be present?
```yaml
completeness:
  rules:
    - name: "Critical Fields"
      columns: ["id", "amount", "date"]
      threshold: 1.0  # 100% required
```

**Consistency**: What relationships must hold?
```yaml
consistency:
  rules:
    - name: "Date Logic"
      validation:
        type: "comparison"
        condition: "due_date >= invoice_date"
```

**Freshness**: How recent must the data be?
```yaml
freshness:
  rules:
    - name: "Recent Data"
      column: "last_updated"
      validation:
        type: "age"
        max_age_hours: 24
```

**Plausibility**: What values make business sense?
```yaml
plausibility:
  rules:
    - name: "Reasonable Amounts"
      column: "invoice_amount"
      validation:
        type: "range"
        min: 10.00
        max: 1000000.00
```

### Step 6: Test Thoroughly
Test your template with various data scenarios:

```python
<!-- audience: ai-builders -->
# [STANDARD_CONTRIBUTOR]
# Test with good data
good_report = assessor.assess_file_with_template("good-data.csv", "my-template.yaml")
assert good_report[1].is_compliant

# Test with bad data
bad_report = assessor.assess_file_with_template("bad-data.csv", "my-template.yaml")
assert not bad_report[1].is_compliant

# Test edge cases
edge_report = assessor.assess_file_with_template("edge-cases.csv", "my-template.yaml")
```

### Step 7: Document Your Template
Add clear documentation in the template:
```yaml
template:
  description: |
    This template validates e-commerce order data for payment processing agents.
    It ensures orders have valid IDs, positive amounts, and complete customer info.
    
    Use cases:
    - Automated payment processing
    - Order fulfillment systems
    - Customer service agents
    
  # Add context for each rule
  validity:
    rules:
      - name: "Credit Card Number"
        description: "Must be valid credit card format for payment processing"
        # ... rule details
```

## ✅ Template Contribution Checklist

Before submitting your template, ensure:

- [ ] **Naming Convention**: Follows `category/use-case-v1.0.0.yaml` format
- [ ] **ADRI Version**: Includes `requires_adri` field (if using specific features)
- [ ] **Metadata Complete**: Has id, name, version, description, category, tags
- [ ] **Pattern Matching**: Includes required_columns and column_synonyms
- [ ] **Requirements Set**: Defines overall_minimum and dimension requirements
- [ ] **All Dimensions**: Has rules for all five dimensions (even if minimal)
- [ ] **Clear Descriptions**: Every rule has a name and description
- [ ] **Tested**: Validated with at least 3 different datasets
- [ ] **Examples**: Includes sample data or examples in PR
- [ ] **Documentation**: Template purpose and use cases are clear

## 🎨 Template Examples

### Minimal Template (Starter)
See: `adri/templates/catalog/general/generic-minimal-v1.0.0.yaml`

### Production Template (Full Features)
See: `adri/templates/catalog/general/production-v1.0.0.yaml`

### Industry-Specific Template
See: `adri/templates/catalog/financial/basel-iii-v1.0.0.yaml`

## 📏 Best Practices

### DO:
- ✅ **Start Simple**: Begin with basic requirements, add complexity as needed
- ✅ **Test with Real Data**: Use actual datasets from your domain
- ✅ **Document Assumptions**: Explain why certain thresholds were chosen
- ✅ **Version Appropriately**: Use semantic versioning (1.0.0, 1.1.0, 2.0.0)
- ✅ **Consider Your Users**: Think about who will use this template

### DON'T:
- ❌ **Over-Engineer**: Don't add rules for edge cases that rarely occur
- ❌ **Set Impossible Standards**: Ensure thresholds are achievable
- ❌ **Assume Context**: Document domain-specific requirements
- ❌ **Skip Testing**: Always validate with multiple datasets
- ❌ **Forget Variations**: Include column synonyms for common alternatives

## 🤔 Common Questions

### Q: How specific should my template be?
**A**: Balance specificity with reusability. A template for "e-commerce orders" is better than "my-company-orders" but more specific than "transactions".

### Q: What if my industry has unique requirements?
**A**: Create industry-specific rules! Use the plausibility dimension for domain-specific validations and document the business context.

### Q: Can I update an existing template?
**A**: Yes! Increment the version number and document what changed. Use semantic versioning:
- Bug fixes: 1.0.0 → 1.0.1
- New features: 1.0.0 → 1.1.0  
- Breaking changes: 1.0.0 → 2.0.0

### Q: How do I test my template?
**A**: Create test datasets that include:
1. Perfect data (should score 100%)
2. Typical data (should pass requirements)
3. Poor data (should fail)
4. Edge cases (test specific rules)

## 🛠️ Template Development Tools

### Template Validation
```python
<!-- audience: ai-builders -->
# [STANDARD_CONTRIBUTOR]
from adri.templates import TemplateLoader

# Validate template syntax
loader = TemplateLoader()
try:
    template = loader.load_template("my-template.yaml")
    print("✅ Template is valid!")
except Exception as e:
    print(f"❌ Template error: {e}")
```

### Quick Testing Script
```python
<!-- audience: ai-builders -->
# [STANDARD_CONTRIBUTOR]
# Save as test_template.py
import sys
from adri import DataSourceAssessor

def test_template(data_file, template_file):
    assessor = DataSourceAssessor()
    report, evaluation = assessor.assess_file_with_template(
        data_file, template_file
    )
    
    print(f"Overall Score: {report.overall_score}")
    print(f"Compliant: {evaluation.is_compliant}")
    
    if not evaluation.is_compliant:
        print("\nGaps found:")
        for gap in evaluation.gaps:
            print(f"- {gap.dimension}: {gap.actual_value} < {gap.expected_value}")

if __name__ == "__main__":
    test_template(sys.argv[1], sys.argv[2])
```

## 🤝 Getting Help

- **💬 GitHub Discussions**: Ask questions in the [Templates category](https://github.com/adri-ai/adri/discussions)
- **🐛 Issues**: Report problems with the [template label](https://github.com/adri-ai/adri/issues)
- **📧 Community**: Use [GitHub Discussions](https://github.com/adri-standard/adri/discussions) with "template" tag
- **📚 Examples**: Study existing templates in `adri/templates/catalog/`

## 🏆 Recognition

Top template contributors receive:
- Credit in release notes
- "Template Author" badge in documentation
- Invitation to join Template Working Group
- Speaking opportunities at ADRI events
- Early access to new features

## 🚀 Ready to Contribute?

1. **Fork** the repository
2. **Create** your template following this guide
3. **Test** thoroughly with real data
4. **Submit** a pull request
5. **Celebrate** - you're helping build the future of AI interoperability!

Remember: Every template you contribute makes AI agents more reliable and accessible for everyone. Your domain expertise is invaluable to the community.

---

**Questions?** Don't hesitate to ask! We're here to help you create great templates.
