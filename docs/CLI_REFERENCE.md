# ADRI CLI Reference

Complete command-line interface documentation for ADRI.

## Table of Contents

1. [Overview](#overview)
2. [Global Options](#global-options)
3. [Commands](#commands)
   - [assess](#assess)
   - [generate-standard](#generate-standard)
   - [validate-standard](#validate-standard)
   - [list-standards](#list-standards)
   - [show-config](#show-config)
   - [setup](#setup)
4. [Common Workflows](#common-workflows)
5. [Examples](#examples)

## Overview

ADRI provides a command-line interface for data quality operations:

```bash
adri [COMMAND] [OPTIONS]
```

**Quick help:**
```bash
adri --help              # Show all commands
adri assess --help       # Help for specific command
```

## Global Options

Available across all commands:

```bash
--version              Show ADRI version
--help                Show help message
--verbose, -v         Enable verbose output
--quiet, -q           Suppress non-error output
--config PATH         Use custom config file
```

**Examples:**
```bash
adri --version
adri assess data.csv --verbose
adri generate-standard data.json --config custom-config.yaml
```

## Commands

### guide

Interactive walkthrough for first-time users.

**Usage:**
```bash
adri guide
```

**Description:**
Provides a comprehensive 3-minute interactive tutorial that covers:
- ADRI concepts and how it works
- Project setup and folder structure
- Decorator usage with code examples
- Generating quality standards from sample data
- Assessing data quality with real-world examples
- Reviewing audit logs and assessment history
- Next steps for AI agent integration

**Recommended for:**
- First-time ADRI users
- Teams onboarding new members
- Quick refresher on ADRI workflows
- Understanding ADRI before diving into code

**Examples:**

Run the interactive guide:
```bash
adri guide
```

**Output:**
```
🚀 Welcome to ADRI - AI Data Reliability Inspector

This interactive guide will walk you through:
  1️⃣  Setting up your project
  2️⃣  Understanding decorator usage
  3️⃣  Creating quality standards
  4️⃣  Assessing data quality
  5️⃣  Reviewing audit logs
  6️⃣  Integrating with AI agents

⏱️  This will take about 3 minutes
```

The guide will automatically:
- Check if ADRI is set up, or initialize it
- Show practical examples with real data
- Generate a sample standard from tutorial data
- Assess test data to demonstrate quality checks
- Display audit logs to show tracking capabilities
- Provide next steps for your own projects

**Keyboard shortcuts:**
- Press `Ctrl+C` to exit at any time
- The guide can be restarted anytime with `adri guide`

### assess

Assess data quality against a standard.

**Usage:**
```bash
adri assess [OPTIONS] DATA_PATH
```

**Arguments:**
- `DATA_PATH` - Path to data file (CSV, JSON, or Parquet)

**Options:**
```bash
--standard NAME, -s NAME        Standard name to validate against
--auto-generate, -a             Auto-generate standard if not found
--output PATH, -o PATH          Save assessment report to file
--format FORMAT                 Output format: json, yaml, text (default: text)
--min-score SCORE              Minimum acceptable quality score (0-100)
--show-details                 Show detailed quality breakdown
--filter EXPRESSION            Filter data before assessment
```

**Examples:**

Basic assessment:
```bash
adri assess customers.csv --standard customer_data
```

With auto-generation:
```bash
adri assess sales.json --auto-generate
```

Save detailed report:
```bash
adri assess data.parquet --standard my_standard --output report.json --format json
```

With minimum score:
```bash
adri assess transactions.csv --standard financial --min-score 90
```

Show details:
```bash
adri assess customers.csv --standard customer_data --show-details
```

**Output:**
```
🛡️ Data Quality Assessment

📁 File: customers.csv
📋 Standard: customer_data v1.0.0
📊 Overall Score: 94.2/100

Quality Dimensions:
✅ Validity:      19.5/20  (97.5%)
✅ Completeness:  20.0/20  (100%)
✅ Consistency:   19.0/20  (95.0%)
✅ Accuracy:      18.2/20  (91.0%)
✅ Timeliness:    17.5/20  (87.5%)

✅ Assessment: PASSED (Score ≥ 80.0)

📝 3 rows processed
⚠️  2 minor issues found (see details)
```

### generate-standard

Generate a quality standard from data.

**Usage:**
```bash
adri generate-standard [OPTIONS] DATA_PATH
```

**Arguments:**
- `DATA_PATH` - Path to data file(s), supports wildcards

**Options:**
```bash
--name NAME, -n NAME           Standard name (required)
--output PATH, -o PATH         Output file path
--description DESC, -d DESC    Standard description
--version VERSION              Standard version (default: 1.0.0)
--strict                      Generate strict rules (tighter ranges)
--permissive                  Generate permissive rules (looser ranges)
--include-patterns            Include pattern detection
--max-age-days DAYS           Maximum age for timeliness checks
```

**Examples:**

Basic generation:
```bash
adri generate-standard data.csv --name customer_standard
```

Multiple files:
```bash
adri generate-standard data/*.csv --name combined_standard
```

With description:
```bash
adri generate-standard sales.json \
  --name sales_standard \
  --description "Sales transaction data quality standard"
```

Strict standard:
```bash
adri generate-standard customers.csv \
  --name strict_customer \
  --strict \
  --max-age-days 30
```

Custom output location:
```bash
adri generate-standard data.parquet \
  --name my_standard \
  --output ~/ADRI/dev/contracts/custom.yaml
```

**Output:**
```
✅ Analyzing data structure...
📊 Processed 1,247 rows

Detected Fields:
- customer_id (integer, required)
- email (string, required, email pattern)
- age (integer, required, range: 18-89)
- signup_date (date, required)

✅ Standard generated: customer_standard v1.0.0
📁 Saved to: ADRI/dev/contracts/customer_standard.yaml

Next steps:
1. Review and customize the standard
2. Use: adri assess data.csv --standard customer_standard
```

### validate-standard

Validate a standard file for correctness.

**Usage:**
```bash
adri validate-standard [OPTIONS] STANDARD_PATH
```

**Arguments:**
- `STANDARD_PATH` - Path to standard YAML file

**Options:**
```bash
--strict                Check for recommended best practices
--show-warnings        Show non-critical warnings
```

**Examples:**

Basic validation:
```bash
adri validate-standard ADRI/dev/contracts/customer_standard.yaml
```

Strict validation:
```bash
adri validate-standard my_standard.yaml --strict --show-warnings
```

**Output:**
```
✅ Validating standard: customer_standard.yaml

Structure: ✅ Valid
  - Name: customer_standard
  - Version: 1.0.0
  - Fields: 4 defined

Field Validation: ✅ Passed
  ✅ customer_id: integer, required
  ✅ email: string, pattern validation
  ✅ age: integer, range [18-120]
  ✅ signup_date: date, max age 365 days

⚠️  Warnings (non-critical):
  - Consider adding description to standard
  - Field 'email' could benefit from max_length

✅ Standard is valid and ready to use
```

### list-standards

List available quality standards.

**Usage:**
```bash
adri list-standards [OPTIONS]
```

**Options:**
```bash
--verbose, -v          Show detailed information
--path PATH            List standards from specific path
--bundled             Show only bundled standards
--user                Show only user standards
--project             Show only project standards
--format FORMAT       Output format: table, json, yaml
```

**Examples:**

List all standards:
```bash
adri list-standards
```

Detailed listing:
```bash
adri list-standards --verbose
```

Only project standards:
```bash
adri list-standards --project
```

JSON output:
```bash
adri list-standards --format json
```

**Output:**
```
📋 Available Standards

Project Standards (ADRI/dev/contracts/):
  ✅ customer_standard v1.0.0
     Fields: 4 | Last modified: 2024-01-15

  ✅ sales_standard v2.1.0
     Fields: 8 | Last modified: 2024-01-14

User Standards (~/ADRI/dev/contracts/):
  ✅ financial_data v1.5.0
     Fields: 12 | Last modified: 2024-01-10

Bundled Standards:
  ✅ high_quality_agent_data v1.0.0
     Fields: 6 | Built-in standard

Total: 4 standards available
```

### show-config

Display current ADRI configuration.

**Usage:**
```bash
adri show-config [OPTIONS]
```

**Options:**
```bash
--format FORMAT        Output format: yaml, json, text
--show-defaults       Show default values
--show-sources        Show config sources
```

**Examples:**

Show current config:
```bash
adri show-config
```

With defaults:
```bash
adri show-config --show-defaults
```

JSON format:
```bash
adri show-config --format json
```

**Output:**
```
📋 ADRI Configuration

Standards:
  Path: .adri/standards
  Bundled Path: ~/.adri/bundled
  Auto-generate: true

Logging:
  Level: INFO
  Path: .adri/logs
  Console Output: true

Validation:
  Default Mode: block
  Min Score: 80.0
  Strict Mode: false

Sources:
  ✅ Project: ADRI/config.yaml
  ✅ User: ~/ADRI/config.yaml
  ✅ Defaults: Built-in
```

### setup

Interactive configuration setup with optional guided tour.

**Usage:**
```bash
adri setup [OPTIONS]
```

**Options:**
```bash
--guide               Interactive guided tour with examples and tutorials
--global              Configure global settings
--project             Configure project settings (default)
--reset               Reset to defaults
--non-interactive     Use defaults without prompts
```

**Examples:**

Guided tour (recommended for first-time users):
```bash
adri setup --guide
```

Interactive setup:
```bash
adri setup
```

Global configuration:
```bash
adri setup --global
```

Reset configuration:
```bash
adri setup --reset
```

**Interactive prompts:**
```
🔧 ADRI Setup

Where should standards be stored?
  [1] .adri/standards (project-local, recommended)
  [2] ~/.adri/standards (user-global)
  [3] Custom path
Choice [1]: 1

What log level do you prefer?
  [1] INFO (recommended)
  [2] DEBUG (verbose)
  [3] WARNING (minimal)
  [4] ERROR (errors only)
Choice [1]: 1

Default guard mode?
  [1] block (strict, recommended for production)
  [2] warn (permissive, good for development)
Choice [1]: 1

Auto-generate standards when missing?
  [Y/n]: Y

✅ Configuration saved to ADRI/config.yaml

Next steps:
1. Protect a function: @adri_protected(contract="data", data_param="data")
2. Generate a standard: adri generate-standard data.csv --name my_standard
3. Assess data quality: adri assess data.csv --standard my_standard
```

## Common Workflows

### Workflow 1: First-Time Setup

```bash
# 1. Install ADRI
pip install adri

# 2. Configure ADRI
adri setup

# 3. Generate your first standard
adri generate-standard sample_data.csv --name my_standard

# 4. Assess new data
adri assess new_data.csv --standard my_standard
```

### Workflow 2: Data Quality Pipeline

```bash
# 1. Generate standard from good data
adri generate-standard golden_dataset.csv --name production_standard

# 2. Validate the standard
adri validate-standard ADRI/dev/contracts/production_standard.yaml

# 3. Assess production data
adri assess production_data.csv \
  --standard production_standard \
  --min-score 90 \
  --output quality_report.json
```

### Workflow 3: Multi-File Assessment

```bash
# 1. Generate combined standard
adri generate-standard data/*.csv --name combined_standard

# 2. Assess each file
for file in data/*.csv; do
  echo "Assessing $file"
  adri assess "$file" \
    --standard combined_standard \
    --output "reports/$(basename $file .csv)_report.json"
done
```

### Workflow 4: Standard Evolution

```bash
# 1. Generate initial standard
adri generate-standard initial_data.csv --name evolving_standard

# 2. Review and customize
cat ADRI/dev/contracts/evolving_standard.yaml
# Edit the YAML file...

# 3. Validate changes
adri validate-standard ADRI/dev/contracts/evolving_standard.yaml

# 4. Test with new data
adri assess new_data.csv --standard evolving_standard
```

### Workflow 5: Continuous Integration

```bash
# In CI/CD pipeline

# 1. List available standards
adri list-standards --project

# 2. Assess data quality (fail if score too low)
adri assess data.csv \
  --standard required_standard \
  --min-score 85 \
  --output ci_report.json

# 3. Exit with error if quality too low
if [ $? -ne 0 ]; then
  echo "Data quality check failed"
  exit 1
fi
```

## Examples

### Example 1: Quick Assessment

```bash
# Assess with auto-generation
adri assess customers.csv --auto-generate

# Output shows quality score and any issues
```

### Example 2: Generate and Use Standard

```bash
# Generate from sample data
adri generate-standard sample.csv --name customer_data

# Assess new data against standard
adri assess new_customers.csv --standard customer_data
```

### Example 3: Detailed Quality Report

```bash
# Generate comprehensive report
adri assess sales.json \
  --standard sales_data \
  --show-details \
  --output detailed_report.json \
  --format json
```

### Example 4: Strict Validation

```bash
# Generate strict standard
adri generate-standard data.csv \
  --name strict_standard \
  --strict \
  --max-age-days 7

# Assess with high threshold
adri assess new_data.csv \
  --standard strict_standard \
  --min-score 95
```

### Example 5: Batch Processing

```bash
# Process multiple files
for file in data/*.csv; do
  adri assess "$file" \
    --standard unified_standard \
    --output "reports/$(basename $file).report"
done
```

### Example 6: Configuration Management

```bash
# Show current config
adri show-config

# Setup new configuration
adri setup --project

# Validate configuration
adri show-config --show-sources
```

### Example 7: Standard Validation

```bash
# Validate before deployment
adri validate-standard production_standard.yaml --strict

# List all standards
adri list-standards --verbose
```

## Exit Codes

ADRI CLI commands return standard exit codes:

- `0` - Success
- `1` - Quality check failed (assess command)
- `2` - Invalid arguments or options
- `3` - File not found
- `4` - Standard not found
- `5` - Configuration error

**Example:**
```bash
adri assess data.csv --standard my_standard
if [ $? -eq 1 ]; then
  echo "Quality check failed!"
fi
```

## Environment Variables

Override configuration with environment variables:

```bash
ADRI_STANDARDS_PATH=./my_standards
ADRI_LOG_LEVEL=DEBUG
ADRI_DEFAULT_MODE=warn
ADRI_MIN_SCORE=85
```

**Example:**
```bash
export ADRI_LOG_LEVEL=DEBUG
adri assess data.csv --standard my_standard
```

## Tips and Tricks

### 1. Shell Aliases

Create shortcuts for common commands:

```bash
# Add to ~/.bashrc or ~/.zshrc
alias adri-assess='adri assess --show-details'
alias adri-gen='adri generate-standard --strict'
alias adri-list='adri list-standards --verbose'
```

### 2. Auto-Completion

Enable shell auto-completion (if available):

```bash
# Bash
eval "$(_ADRI_COMPLETE=bash_source adri)"

# Zsh
eval "$(_ADRI_COMPLETE=zsh_source adri)"
```

### 3. Integration with Git Hooks

Pre-commit hook:

```bash
#!/bin/bash
# .git/hooks/pre-commit

adri assess data/latest.csv --standard production --min-score 90
if [ $? -ne 0 ]; then
  echo "Data quality check failed. Commit aborted."
  exit 1
fi
```

### 4. Scheduled Assessments

Cron job for regular checks:

```bash
# Check data quality daily at 2 AM
0 2 * * * /usr/local/bin/adri assess /path/to/data.csv --standard prod --output /var/log/adri/daily_$(date +\%Y\%m\%d).json
```

## Next Steps

- [Getting Started](GETTING_STARTED.md) - Hands-on tutorial
- [How It Works](HOW_IT_WORKS.md) - Understanding quality dimensions
- [API Reference](API_REFERENCE.md) - Programmatic usage
- [Examples](../examples/README.md) - Real-world examples

---

**Master ADRI's CLI tools for comprehensive data quality management.**
