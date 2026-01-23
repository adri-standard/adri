# ADRI Tutorials

This directory contains validated, production-tested use case examples for ADRI. Each tutorial demonstrates ADRI's data quality framework through real-world scenarios.

## 🎯 What Are Tutorials?

Tutorials are complete, working examples that:
- ✅ Show ADRI in action with real use cases
- ✅ Provide clean training data (100% quality guaranteed)
- ✅ Include test data with realistic quality issues
- ✅ Are automatically tested in CI/CD
- ✅ Serve as validated documentation

## 🚀 Adding a New Tutorial

Adding a tutorial is as simple as dropping two CSV files into a directory!

### Step 1: Create Tutorial Directory

```bash
mkdir ADRI/tutorials/<your_use_case>
cd ADRI/tutorials/<your_use_case>
```

### Step 2: Add Your CSV Files

Create exactly **two CSV files** following the naming convention:

```
ADRI/tutorials/<your_use_case>/
├── <your_use_case>_data.csv          # Clean training data (100% quality)
└── test_<your_use_case>_data.csv     # Test data with quality issues
```

**File Naming Rules:**
1. **Training file**: `<use_case>_data.csv` (e.g., `invoice_data.csv`)
   - Must contain perfectly clean data
   - Will be used to generate the ADRI standard
   - Must score 100% against its own standard

2. **Test file**: `test_<use_case>_data.csv` (e.g., `test_invoice_data.csv`)
   - Should contain realistic quality issues
   - Same columns as training file
   - Used to verify error detection works

### Step 3: Run Tests

That's it! The framework automatically:

```bash
# Run auto-discovery tests
pytest tests/test_tutorial_auto_discovery.py -v

# Tests auto-generated for your tutorial:
# ✓ Standard generation from training data
# ✓ 100% scoring guarantee for training data
# ✓ Error detection for test data
# ✓ Data structure consistency
# ✓ File naming convention validation
```

## 📋 Examples

### Example 1: Invoice Processing

```
ADRI/tutorials/invoice_processing/
├── invoice_data.csv           # Clean invoice data
└── test_invoice_data.csv      # Invoices with quality issues
```

**Columns**: Invoice Number, Invoice Date, Customer Name, Total Amount, Tax Amount, Payment Status

### Example 2: Customer Support (Template)

```
ADRI/tutorials/customer_support/
├── customer_support_data.csv       # Clean support tickets
└── test_customer_support_data.csv  # Tickets with issues
```

**Columns**: Ticket ID, Customer ID, Issue Type, Priority, Status, Created Date, Resolution

### Example 3: Financial Analysis (Template)

```
ADRI/tutorials/financial_analysis/
├── financial_analysis_data.csv       # Clean financial data
└── test_financial_analysis_data.csv  # Data with anomalies
```

**Columns**: Transaction ID, Date, Account, Category, Amount, Currency, Status

## 🔍 What Gets Tested Automatically?

For each tutorial, **8 tests** run automatically:

### 1. **100% Scoring Test** (CRITICAL)
- Generates ADRI standard from training data
- Validates training data scores 100%
- Ensures all quality dimensions are perfect
- **This is the most important test!**

### 2. **Standard Generation Test**
- Verifies standard is generated successfully
- Validates YAML structure
- Checks required fields are present

### 3. **Error Detection Test**
- Confirms test data scores below 100%
- Verifies quality issues are detected
- Ensures framework catches problems

### 4. **Data Consistency Test**
- Validates training and test files have same columns
- Checks both files are readable
- Ensures structural consistency

### 5. **Naming Convention Test**
- Verifies files follow required naming pattern
- Ensures use case names match

### 6. **Standard Validation Test** (NEW!)
- Validates generated standard meets ADRI requirements
- Checks standard structure and metadata
- Verifies all 5 quality dimensions are configured
- Ensures field requirements are properly defined

### 7. **Assessment & Audit Log Validation** (NEW!)
- Validates ADRI's own assessment JSON outputs
- Validates ADRI's audit log CSV outputs
- Ensures consistency between JSON and CSV
- Self-validation: ADRI validating its own outputs!

### 8. **Discovery Mechanism Test**
- Verifies the auto-discovery framework works
- Ensures tutorials are found correctly

## ✅ Quality Requirements

### Training Data (`<use_case>_data.csv`)

**MUST be 100% clean:**
- ✓ No missing values (or intentional NaN if part of schema)
- ✓ Correct data types
- ✓ Valid value ranges
- ✓ Proper formatting
- ✓ No duplicates (unless intentional)
- ✓ Consistent naming conventions

**Why?** Training data is used to generate the ADRI standard. It represents the "perfect" example that all other data will be compared against.

### Test Data (`test_<use_case>_data.csv`)

**SHOULD contain realistic issues:**
- Missing values
- Type inconsistencies
- Out-of-range values
- Format violations
- Duplicates
- Naming inconsistencies

**Why?** Test data validates that ADRI can detect real-world quality issues.

## 🎓 Best Practices

### 1. Start Small
Begin with 5-10 rows in your training data. Keep it simple and focused.

### 2. Use Real-World Examples
Base your tutorial on actual use cases you've encountered. This makes it more valuable.

### 3. Document Your Use Case
Add a comment row or separate README explaining:
- What the data represents
- What quality issues to look for
- Expected behavior

### 4. Keep Columns Consistent
Both training and test files must have identical columns in the same order.

### 5. Test Locally First
```bash
# Verify your files are discovered
python -c "from tests.fixtures.tutorial_discovery import find_tutorial_directories; print([t.use_case_name for t in find_tutorial_directories()])"

# Run tests
pytest tests/test_tutorial_auto_discovery.py::test_training_data_scores_100_percent -v
```

## 🔧 Troubleshooting

### "Training data failed to score 100%"
**Problem**: Your training data has quality issues

**Solution**:
1. Run standard generation manually to see errors
2. Fix data quality issues
3. Ensure all values are clean and consistent

### "Column mismatch between training and test data"
**Problem**: Files have different columns

**Solution**:
1. Ensure both files have identical column names
2. Check column order matches exactly
3. Verify no extra/missing columns

### "Tutorial not discovered"
**Problem**: Files don't match naming convention

**Solution**:
1. Check file names follow pattern exactly
2. Ensure files end with `_data.csv`
3. Test file must start with `test_`
4. Use case name must match in both files

### "Standard generation failed"
**Problem**: Data can't be analyzed

**Solution**:
1. Check CSV is properly formatted
2. Ensure data types are consistent within columns
3. Verify file encoding is UTF-8
4. Check for special characters in column names

## 📊 Current Tutorials

<!-- This list is auto-generated by discovery -->

- **invoice_processing**: Invoice data quality validation
  - Columns: Invoice Number, Invoice Date, Customer Name, Total Amount, Tax Amount, Payment Status
  - Use Case: Financial document processing

<!-- Add your tutorial here after creation -->

## 🤝 Contributing

Want to add a tutorial? Just:

1. Create your directory with two CSV files
2. Ensure training data is 100% clean
3. Add realistic issues to test data
4. Run tests to verify
5. Submit a PR!

No manual test writing required - the framework handles everything automatically!

## 📖 Additional Resources

- [Tutorial Framework Documentation](../../tests/fixtures/TUTORIAL_FRAMEWORK_README.md)
- [ADRI Main Documentation](../../README.md)
- [Standard Generation Guide](../../docs/)

## 🎯 Goals

Every tutorial in this directory:
- ✅ Is production-tested and validated
- ✅ Scores 100% on its training data
- ✅ Demonstrates real-world use cases
- ✅ Provides working examples for users
- ✅ Builds a library of validated patterns

---

**Remember**: Tutorials are living documentation. They're not just examples - they're tested, validated, production-quality use cases that users can trust and learn from!
