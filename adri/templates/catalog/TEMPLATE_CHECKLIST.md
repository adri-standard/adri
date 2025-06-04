# ADRI Template Contribution Checklist

Use this checklist to ensure your template is ready for submission.

## ✅ Required Elements

### Metadata
- [ ] `id` - Unique identifier following naming convention
- [ ] `name` - Human-readable name
- [ ] `version` - Semantic version (e.g., 1.0.0)
- [ ] `description` - Clear explanation of purpose
- [ ] `category` - One of: general, financial, healthcare, retail, logistics

### Structure
- [ ] `pattern_matching` section with `required_columns`
- [ ] `requirements` section with `overall_minimum`
- [ ] All 5 dimensions defined (validity, completeness, freshness, consistency, plausibility)
- [ ] At least one rule per dimension

### Optional but Recommended
- [ ] `requires_adri` - Minimum ADRI version if using specific features
- [ ] `tags` - For better discovery
- [ ] `column_synonyms` - Handle naming variations
- [ ] `dimension_requirements` - Per-dimension thresholds

## 📋 Quality Checks

### Documentation
- [ ] Clear description of what the template validates
- [ ] Each rule has a descriptive name
- [ ] Complex rules include comments or descriptions
- [ ] Use cases documented

### Testing
- [ ] Tested with at least 3 different datasets
- [ ] Includes both passing and failing test cases
- [ ] Edge cases considered
- [ ] Thresholds are achievable but meaningful

### Best Practices
- [ ] Not overly specific to one organization
- [ ] Balances strictness with practicality
- [ ] Uses appropriate validation types
- [ ] Follows naming convention: `{use-case}-v{version}.yaml`

## 🚀 Submission

### Before Creating PR
- [ ] Template placed in correct category folder
- [ ] File follows naming convention
- [ ] All required fields present
- [ ] Passes YAML validation
- [ ] Test data included (if possible)

### PR Description Should Include
- [ ] Brief description of use case
- [ ] Industries/scenarios where applicable
- [ ] Any special considerations
- [ ] Example of compliant data

## 📝 Example Template Structure

```yaml
template:
  id: "retail-inventory-v1.0.0"
  name: "Retail Inventory Management"
  version: "1.0.0"
  description: "Validates inventory data for retail operations"
  category: "retail"
  requires_adri: ">=0.3.0"  # If needed
  tags: ["inventory", "stock", "retail"]

pattern_matching:
  required_columns: ["sku", "quantity", "location"]
  column_synonyms:
    sku: ["product_id", "item_code"]

requirements:
  overall_minimum: 75
  dimension_requirements:
    validity: {minimum_score: 16}
    completeness: {minimum_score: 18}

dimensions:
  validity:
    rules:
      - name: "Valid SKU Format"
        column: "sku"
        validation: {type: "regex", pattern: "^[A-Z0-9-]+$"}
        
  completeness:
    rules:
      - name: "Required Fields Present"
        columns: ["sku", "quantity", "location"]
        threshold: 1.0
        
  freshness:
    rules:
      - name: "Recent Update"
        column: "last_updated"
        validation: {type: "age", max_age_days: 1}
        
  consistency:
    rules:
      - name: "Positive Quantity"
        column: "quantity"
        validation: {type: "range", min: 0}
        
  plausibility:
    rules:
      - name: "Reasonable Stock Levels"
        column: "quantity"
        validation: {type: "range", min: 0, max: 10000}
```

---

**Ready?** Once all items are checked, create your PR! 🎉
