# Python API Usage Test Plan

This test plan focuses on the fourth component of the ADRI user journey: "Python API Usage". It validates that users can successfully use the ADRI Python API to programmatically assess data sources as described in the documentation.

## Prerequisites

- ADRI package successfully installed (from previous test plan)
- Test datasets available (from `test_datasets/` directory)
- Python development environment (IDE or text editor)
- Basic Python knowledge

## Test Cases

### 1. Import ADRI Module

**Test ID:** 4.1

**Description:** Verify that the ADRI module can be successfully imported in Python.

**Steps:**
1. Create a new Python script or start a Python interactive session
2. Add the import statement:
   ```python
   import adri
   # More specific imports
   from adri import DataSourceAssessor
   ```

**Expected Result:**
- Import statements execute without errors
- No warnings or deprecation notices appear
- The module is accessible for further use

**Actual Result:**
- [ ] Pass
- [ ] Fail

**Notes:**
_____________________________

### 2. Create DataSourceAssessor Instance

**Test ID:** 4.2

**Description:** Create an instance of the DataSourceAssessor class.

**Steps:**
1. Create a Python script with the following code:
   ```python
   from adri import DataSourceAssessor
   
   # Create an assessor with default settings
   assessor = DataSourceAssessor()
   
   # Create an assessor with custom settings (if applicable)
   custom_assessor = DataSourceAssessor(config={"dimensions": {"freshness": {"weight": 2.0}}})
   
   print(f"Assessor created successfully: {assessor}")
   ```
2. Execute the script

**Expected Result:**
- Script executes without errors
- Assessor instances are created successfully
- Default settings are applied to the first instance
- Custom settings are applied to the second instance

**Actual Result:**
- [ ] Pass
- [ ] Fail

**Notes:**
_____________________________

### 3. Assess File Using Python API

**Test ID:** 4.3

**Description:** Use the Python API to assess a CSV file.

**Steps:**
1. Create a Python script with the following code:
   ```python
   from adri import DataSourceAssessor
   
   assessor = DataSourceAssessor()
   
   # Assess a file with no issues
   report = assessor.assess_file("test_datasets/ideal_dataset.csv")
   
   print(f"Assessment completed with overall score: {report.overall_score}")
   print(f"Dimension scores: {report.dimension_scores}")
   ```
2. Execute the script

**Expected Result:**
- Script executes without errors
- Report object is returned
- Overall score is high for the ideal dataset (80-100)
- Dimension scores are accessible and reasonable
- Method provides appropriate status updates during processing

**Actual Result:**
- [ ] Pass
- [ ] Fail

**Notes:**
_____________________________

### 4. Access Scores Programmatically

**Test ID:** 4.4

**Description:** Test the ability to access assessment scores and results programmatically.

**Steps:**
1. Create a Python script with the following code:
   ```python
   from adri import DataSourceAssessor
   
   assessor = DataSourceAssessor()
   
   # Assess a file with completeness issues
   report = assessor.assess_file("test_datasets/incomplete_dataset.csv")
   
   # Access overall score
   print(f"Overall score: {report.overall_score}")
   
   # Access individual dimension scores
   for dimension, score in report.dimension_scores.items():
       print(f"{dimension.capitalize()} score: {score}")
   
   # Access findings
   for dimension, findings in report.findings.items():
       print(f"\n{dimension.capitalize()} findings:")
       for finding in findings:
           print(f"- {finding}")
   
   # Access recommendations
   print("\nRecommendations:")
   for recommendation in report.recommendations:
       print(f"- {recommendation}")
   ```
2. Execute the script

**Expected Result:**
- Script executes without errors
- Overall score is accessible and numeric
- Individual dimension scores are accessible and numeric
- Completeness score is notably lower due to the dataset's issues
- Findings related to missing data are present
- Recommendations are relevant to completeness issues

**Actual Result:**
- [ ] Pass
- [ ] Fail

**Notes:**
_____________________________

### 5. Save Reports Programmatically

**Test ID:** 4.5

**Description:** Test the ability to save reports to JSON and HTML formats.

**Steps:**
1. Create an output directory if it doesn't exist:
   ```bash
   mkdir -p api_test_outputs
   ```
2. Create a Python script with the following code:
   ```python
   from adri import DataSourceAssessor
   import os
   
   # Ensure output directory exists
   os.makedirs("api_test_outputs", exist_ok=True)
   
   assessor = DataSourceAssessor()
   
   # Assess a file with freshness issues
   report = assessor.assess_file("test_datasets/stale_dataset.csv")
   
   # Save as JSON
   json_path = "api_test_outputs/stale_report.json"
   report.save_json(json_path)
   print(f"JSON report saved to: {json_path}")
   
   # Save as HTML
   html_path = "api_test_outputs/stale_report.html"
   report.save_html(html_path)
   print(f"HTML report saved to: {html_path}")
   
   # Verify files exist
   print(f"JSON file exists: {os.path.exists(json_path)}")
   print(f"HTML file exists: {os.path.exists(html_path)}")
   ```
3. Execute the script

**Expected Result:**
- Script executes without errors
- Both JSON and HTML files are created at the specified paths
- JSON file contains valid JSON with appropriate report structure
- HTML file contains valid HTML that can be opened in a browser
- Reports contain appropriate information about freshness issues

**Actual Result:**
- [ ] Pass
- [ ] Fail

**Notes:**
_____________________________

### 6. Error Handling

**Test ID:** 4.6

**Description:** Test how the API handles errors and edge cases.

**Steps:**
1. Create a Python script to test various error scenarios:
   ```python
   from adri import DataSourceAssessor
   
   assessor = DataSourceAssessor()
   
   # Test case 1: Non-existent file
   try:
       report = assessor.assess_file("non_existent_file.csv")
   except Exception as e:
       print(f"Expected error for non-existent file: {e}")
   
   # Test case 2: Invalid file format
   with open("api_test_outputs/invalid.txt", "w") as f:
       f.write("This is not a CSV file")
   
   try:
       report = assessor.assess_file("api_test_outputs/invalid.txt")
   except Exception as e:
       print(f"Expected error for invalid format: {e}")
   
   # Test case 3: Empty file
   with open("api_test_outputs/empty.csv", "w") as f:
       pass
   
   try:
       report = assessor.assess_file("api_test_outputs/empty.csv")
   except Exception as e:
       print(f"Expected error for empty file: {e}")
   
   print("Error handling test completed")
   ```
2. Execute the script

**Expected Result:**
- Script executes without crashing
- Each error case is handled gracefully with informative error messages
- Errors are specific about what went wrong
- The assessment doesn't proceed with invalid inputs

**Actual Result:**
- [ ] Pass
- [ ] Fail

**Notes:**
_____________________________

### 7. Custom Configuration

**Test ID:** 4.7

**Description:** Test the ability to customize assessment parameters.

**Steps:**
1. Create a Python script with the following code:
   ```python
   from adri import DataSourceAssessor
   import json
   import os
   
   # Define custom configuration
   custom_config = {
       "dimensions": {
           "validity": {"weight": 0.5},
           "completeness": {"weight": 2.0},
           "freshness": {"weight": 1.5},
           "consistency": {"weight": 0.8},
           "plausibility": {"weight": 0.2}
       }
   }
   
   # Save config for reference
   os.makedirs("api_test_outputs", exist_ok=True)
   with open("api_test_outputs/custom_config.json", "w") as f:
       json.dump(custom_config, f, indent=2)
   
   # Create assessor with custom config
   custom_assessor = DataSourceAssessor(config=custom_config)
   
   # Assess with custom configuration
   custom_report = custom_assessor.assess_file("test_datasets/mixed_issues_dataset.csv")
   custom_report.save_json("api_test_outputs/custom_weighted_report.json")
   
   # Assess with default configuration for comparison
   default_assessor = DataSourceAssessor()
   default_report = default_assessor.assess_file("test_datasets/mixed_issues_dataset.csv")
   default_report.save_json("api_test_outputs/default_weighted_report.json")
   
   print(f"Custom config overall score: {custom_report.overall_score}")
   print(f"Default config overall score: {default_report.overall_score}")
   
   # Given the weights, completeness issues should have more impact in custom report
   print(f"Custom completeness score: {custom_report.dimension_scores.get('completeness')}")
   print(f"Default completeness score: {default_report.dimension_scores.get('completeness')}")
   ```
2. Execute the script

**Expected Result:**
- Script executes without errors
- Custom configuration is correctly applied
- Weighted scores reflect the custom weights (completeness has greater impact)
- Different overall scores between custom and default configurations
- Reports are saved successfully

**Actual Result:**
- [ ] Pass
- [ ] Fail

**Notes:**
_____________________________

### 8. API Documentation Accuracy

**Test ID:** 4.8

**Description:** Verify that the Python API behavior matches what is described in the documentation.

**Steps:**
1. Review the Python API documentation in:
   - README.md
   - Implementation-Guide.md
   - Any docstrings in the code (accessible via `help(DataSourceAssessor)`)
   - Any other documentation mentioning the Python API
2. Compare the documented methods and behaviors with the actual behavior tested in the previous cases

**Criteria to Check:**
- [ ] Method signatures match documentation
- [ ] All documented methods and attributes are available
- [ ] Method behavior matches descriptions
- [ ] Examples in documentation work as expected
- [ ] Default values are as documented
- [ ] Return values are as specified

**Assessment:**
- [ ] Excellent (all criteria met)
- [ ] Good (most criteria met)
- [ ] Fair (some criteria met)
- [ ] Poor (few criteria met)

**Notes:**
_____________________________

### 9. Integration with Python Ecosystem

**Test ID:** 4.9

**Description:** Test the integration of ADRI with common Python data processing libraries.

**Steps:**
1. Create a Python script that uses ADRI with pandas:
   ```python
   import pandas as pd
   from adri import DataSourceAssessor
   
   # Load data with pandas
   df = pd.read_csv("test_datasets/ideal_dataset.csv")
   
   # Make some intentional modifications to test assessment
   df.loc[0:5, 'satisfaction_score'] = None  # Add some missing values
   
   # Save modified CSV
   modified_csv = "api_test_outputs/pandas_modified.csv"
   df.to_csv(modified_csv, index=False)
   
   # Assess the modified data
   assessor = DataSourceAssessor()
   report = assessor.assess_file(modified_csv)
   
   print(f"Overall score after pandas modification: {report.overall_score}")
   print(f"Completeness score: {report.dimension_scores.get('completeness')}")
   
   # Access findings related to completeness
   completeness_findings = report.findings.get('completeness', [])
   print("\nCompleteness findings:")
   for finding in completeness_findings:
       print(f"- {finding}")
   ```
2. Execute the script

**Expected Result:**
- Script executes without errors
- Pandas integration works smoothly
- Assessment correctly identifies the introduced completeness issues
- Appropriate findings are reported for the missing values

**Actual Result:**
- [ ] Pass
- [ ] Fail

**Notes:**
_____________________________

### 10. Advanced API Features

**Test ID:** 4.10

**Description:** Test any advanced or unique features of the Python API.

**Steps:**
1. Review the API documentation for any advanced features such as:
   - Batch processing
   - Asynchronous processing
   - Custom dimension or check registration
   - Callbacks or hooks
   - Configuration imports/exports
   - Report comparison tools

2. Create appropriate test scripts for any identified advanced features

**Expected Result:**
- Advanced features work as documented
- Features provide additional value beyond basic assessment
- Features are stable and handle errors appropriately

**Actual Result:**
- [ ] Pass
- [ ] Fail
- [ ] Not applicable (no advanced features identified)

**Notes:**
_____________________________

## Test Results Summary

**Overall Status:**
- [ ] All tests passed
- [ ] Some tests passed with minor issues
- [ ] Major issues detected

**Key Findings:**

**Recommendations:**

## Next Steps

After completing this test plan, proceed to the next logical component in the user journey: "Advanced Configuration Testing" test plan.
