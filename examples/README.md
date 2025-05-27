# ADRI Examples

This directory contains examples demonstrating how to use the Agent Data Readiness Index (ADRI) framework.

## Examples

### Basic Assessment

The `basic_assessment.py` script demonstrates how to:
1. Create a simple CSV data source with sample data
2. Configure an assessment with custom rules
3. Run the assessment
4. Display and save the results

To run this example:

```bash
# Make sure you're in the project root directory
python examples/basic_assessment.py
```

This will:
- Create a sample CSV file in `examples/data/`
- Run a data quality assessment on it
- Display the results in the console
- Save detailed results to `examples/data/assessment_results.json`

### Sample Output

The assessment results include:
- Overall data quality score
- Scores for each dimension (e.g., Validity)
- Detailed rule execution results with specific data issues
- Sample of problematic data points

### Plausibility Assessment

The `plausibility_assessment.py` script demonstrates how to use the plausibility dimension rules to evaluate if data appears reasonable and likely to be correct. It shows:

1. Creating synthetic data with intentional statistical anomalies
2. Configuring different types of plausibility rules:
   - Outlier detection using statistical methods (Z-score, IQR, Modified Z-score)
   - Distribution analysis to check if data follows expected patterns
   - Range checking for values within expected boundaries
   - Pattern frequency analysis for categorical data
3. Running the assessment and interpreting plausibility results

To run this example:

```bash
# Make sure you're in the project root directory
python examples/plausibility_assessment.py
```

### Consistency Assessment

The `consistency_assessment.py` script demonstrates how to validate internal consistency between data elements. It shows:

1. Creating data with inconsistency issues between related fields
2. Setting up consistency rules:
   - Cross-field validation to check logical relationships
   - Uniform representation validation
   - Calculation consistency checks
3. Analyzing the results to identify inconsistent data

To run this example:

```bash
# Make sure you're in the project root directory
python examples/consistency_assessment.py
```

### Comprehensive Assessment

The `comprehensive_assessment.py` script demonstrates how to use all dimensions of the ADRI framework together for a complete data quality assessment. It shows:

1. Creating a complex dataset with various quality issues
2. Configuring rules for all dimensions:
   - Validity: Type and format validation
   - Completeness: Required field checks
   - Plausibility: Statistical checks and range validation
   - Freshness: Timestamp age verification
   - Consistency: Cross-field and calculation checks
3. Running a full assessment and analyzing results across dimensions
4. Generating a comprehensive HTML report

To run this example:

```bash
# Make sure you're in the project root directory
python examples/comprehensive_assessment.py
```

### AI Status Auditor Demo

The `07_status_auditor_demo.py` script demonstrates how ADRI can be used to create a business-focused audit tool that identifies workflow breakdowns in CRM data. This example showcases:

1. Creating realistic CRM data with common quality issues:
   - Missing close dates in late-stage deals
   - Stale opportunities with no recent activity
   - Missing contact information
   - Ownership conflicts between deals and accounts
2. Generating ADRI metadata files for all 5 dimensions with business-specific rules
3. Running an assessment and translating technical results to business language
4. Producing an actionable audit report that highlights:
   - Revenue at risk from data issues
   - Process breakdowns affecting operations
   - Immediate actions to improve data quality

To run this example:

```bash
# Make sure you're in the project root directory
python examples/07_status_auditor_demo.py
```

This will:
- Create `crm_audit_demo.csv` with sample CRM data
- Generate 5 ADRI metadata files (`crm_audit_demo.*.json`)
- Run the assessment and create an HTML report
- Display a business-focused audit report showing:
  - Revenue at risk (e.g., "$340K in deals missing close dates")
  - Process breakdowns (e.g., "23 contacts missing email")
  - Immediate actions (e.g., "Review stale deals with: John S., Mary K.")

This example demonstrates the "AHA moment" for business users: "This would have taken me 4 hours to find manually!"

## Creating Your Own Examples

To create your own examples:
1. Create a new Python file in this directory
2. Import the necessary components from the ADRI framework
3. Create a data source
4. Configure the assessment with appropriate rules
5. Run the assessment and process the results

See the examples above for different templates depending on your use case.
