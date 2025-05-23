# Basic CLI Usage Test Plan

This test plan focuses on the third component of the ADRI user journey: "Basic CLI Usage". It validates that users can successfully use the ADRI command-line interface to perform basic assessment tasks as described in the documentation.

## Prerequisites

- ADRI package successfully installed (from previous test plan)
- Test datasets available (from `test_datasets/` directory)
- Terminal or command prompt access

## Test Cases

### 1. Help Command

**Test ID:** 3.1

**Description:** Run the help command to verify available options and commands.

**Steps:**
1. Open a terminal window
2. Activate the virtual environment with ADRI installed (if applicable)
3. Run the help command:
   ```bash
   adri --help
   ```

**Expected Result:**
- Command executes without errors
- Help text displays showing:
  - Available commands (at minimum: `assess`)
  - Global options
  - Usage examples
  - Version information

**Actual Result:**
- [ ] Pass
- [ ] Fail

**Notes:**
_____________________________

### 2. Version Command

**Test ID:** 3.2

**Description:** Verify the version command works correctly.

**Steps:**
1. Run the version command:
   ```bash
   adri --version
   ```

**Expected Result:**
- Command executes without errors
- Displays the current version number in the expected format (X.Y.Z)
- Version matches what was installed

**Actual Result:**
- [ ] Pass
- [ ] Fail

**Notes:**
_____________________________

### 3. Assess CSV File (JSON Output)

**Test ID:** 3.3

**Description:** Use the CLI to assess a CSV file and generate a JSON report.

**Steps:**
1. Navigate to the directory containing test datasets
2. Create an output directory if it doesn't exist:
   ```bash
   mkdir -p cli_test_outputs
   ```
3. Run the assessment command:
   ```bash
   adri assess --source test_datasets/ideal_dataset.csv --output cli_test_outputs/ideal_report.json
   ```

**Expected Result:**
- Command executes without errors
- Progress feedback is displayed during assessment
- JSON report is created at the specified location
- Terminal output indicates successful completion
- Report contains expected sections: overall score, dimension scores, findings, recommendations

**Actual Result:**
- [ ] Pass
- [ ] Fail

**Notes:**
_____________________________

### 4. Assess CSV File (HTML Output)

**Test ID:** 3.4

**Description:** Use the CLI to assess a CSV file and generate an HTML report.

**Steps:**
1. Run the assessment command with HTML output:
   ```bash
   adri assess --source test_datasets/incomplete_dataset.csv --output cli_test_outputs/incomplete_report.html
   ```

**Expected Result:**
- Command executes without errors
- HTML report is created at the specified location
- Terminal output indicates successful completion
- The HTML file can be opened in a browser and displays properly
- Report includes visualizations (e.g., radar chart)
- Report content matches the expected assessment for a dataset with completeness issues

**Actual Result:**
- [ ] Pass
- [ ] Fail

**Notes:**
_____________________________

### 5. Test with Invalid File

**Test ID:** 3.5

**Description:** Verify how the CLI handles an invalid or non-existent file.

**Steps:**
1. Run the assessment command with a non-existent file:
   ```bash
   adri assess --source non_existent_file.csv --output cli_test_outputs/error_report.json
   ```

**Expected Result:**
- Command fails with a clear error message
- Error message indicates that the file could not be found/accessed
- The system does not crash or produce confusing output
- No output file is created or, if created, it contains appropriate error information

**Actual Result:**
- [ ] Pass
- [ ] Fail

**Notes:**
_____________________________

### 6. Test with Malformed CSV

**Test ID:** 3.6

**Description:** Verify how the CLI handles a malformed CSV file.

**Steps:**
1. Create a malformed CSV file:
   ```bash
   echo "column1,column2\nvalue1,value2\nvalue3" > cli_test_outputs/malformed.csv
   ```
2. Run the assessment command:
   ```bash
   adri assess --source cli_test_outputs/malformed.csv --output cli_test_outputs/malformed_report.json
   ```

**Expected Result:**
- Command handles the error gracefully
- Clear error message indicating the CSV parsing issue
- The system does not crash
- If a report is generated, it contains appropriate error information

**Actual Result:**
- [ ] Pass
- [ ] Fail

**Notes:**
_____________________________

### 7. Output Directory Creation

**Test ID:** 3.7

**Description:** Verify if the CLI creates output directories when they don't exist.

**Steps:**
1. Specify an output path with non-existent directories:
   ```bash
   adri assess --source test_datasets/ideal_dataset.csv --output cli_test_outputs/new_directory/report.json
   ```

**Expected Result:**
- Command executes without errors
- New directory is created automatically
- Report is saved in the specified location

**Actual Result:**
- [ ] Pass
- [ ] Fail

**Notes:**
_____________________________

### 8. Custom Configuration Usage

**Test ID:** 3.8

**Description:** Test using a custom configuration file with the CLI.

**Steps:**
1. Create a simple configuration file:
   ```bash
   echo '{"dimensions": {"freshness": {"weight": 2.0}}}' > cli_test_outputs/custom_config.json
   ```
2. Run the assessment with this configuration:
   ```bash
   adri assess --source test_datasets/stale_dataset.csv --output cli_test_outputs/stale_custom_report.json --config cli_test_outputs/custom_config.json
   ```

**Expected Result:**
- Command executes without errors
- Report is generated with modified weights for freshness dimension
- The freshness dimension has more impact on the overall score compared to default settings

**Actual Result:**
- [ ] Pass
- [ ] Fail

**Notes:**
_____________________________

### 9. All Dimensions Test

**Test ID:** 3.9

**Description:** Verify that all five dimensions are assessed by default.

**Steps:**
1. Run assessment on a dataset with mixed issues:
   ```bash
   adri assess --source test_datasets/mixed_issues_dataset.csv --output cli_test_outputs/mixed_report.json
   ```
2. Examine the output file to verify all dimensions are included

**Expected Result:**
- Command executes without errors
- Report includes scores and findings for all dimensions:
  - Validity
  - Completeness
  - Freshness
  - Consistency
  - Plausibility
- Overall score is calculated based on all dimensions

**Actual Result:**
- [ ] Pass
- [ ] Fail

**Notes:**
_____________________________

### 10. CLI Documentation Accuracy

**Test ID:** 3.10

**Description:** Verify that the CLI behavior matches what is described in the documentation.

**Steps:**
1. Review the CLI documentation in:
   - README.md
   - Implementation-Guide.md
   - Any other documentation mentioning CLI usage
2. Compare the documented commands and options with the actual behavior tested in the previous cases

**Criteria to Check:**
- [ ] Command syntax matches documentation
- [ ] All documented options are available
- [ ] Option behavior matches descriptions
- [ ] Examples in documentation work as expected
- [ ] Default values are as documented

**Assessment:**
- [ ] Excellent (all criteria met)
- [ ] Good (most criteria met)
- [ ] Fair (some criteria met)
- [ ] Poor (few criteria met)

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

After completing this test plan, proceed to the next logical component in the user journey: "Python API Usage" test plan.
