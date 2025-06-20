# ADRI API Reference

> **Technical Reference**: Complete API documentation for developers integrating ADRI into their applications

## Overview

The Agent Data Readiness Index (ADRI) provides a comprehensive Python API for assessing data quality from an AI agent perspective. This reference covers all classes, methods, and integration patterns.

## Quick Navigation

### 🚀 **Getting Started**
- [Core Classes](#core-classes) - Main ADRI components
- [Basic Usage](#basic-usage) - Simple assessment patterns
- [Command Line Interface](#command-line-interface) - CLI operations

### 🔌 **Data Integration**
- [Connectors](#connectors) - Connect to different data sources
- [Templates](#templates) - Assessment configuration
- [Configuration](#configuration) - Global settings

### 🛠️ **Advanced Usage**
- [Custom Dimensions](#custom-dimensions) - Extend assessment capabilities
- [Custom Rules](#custom-rules) - Create domain-specific validation
- [Framework Integration](#framework-integration) - Pandas, Scikit-learn, etc.

### 📚 **Reference**
- [Error Handling](#error-handling) - Exception management
- [Version Information](#version-information) - Compatibility checking

---

## Core Classes

### DataSourceAssessor

The main class for assessing data sources against quality standards.

```python
<!-- audience: ai-builders -->
# [STANDARD_CONTRIBUTOR]
from adri import DataSourceAssessor
from adri.connectors import FileConnector

# Basic usage
connector = FileConnector("customer_data.csv")
assessor = DataSourceAssessor(connector)
result = assessor.assess()

print(f"Quality Score: {result.score}/100")
```

#### Constructor Parameters

```python
<!-- audience: ai-builders -->
# [STANDARD_CONTRIBUTOR]
DataSourceAssessor(
    connector,                    # BaseConnector: Data source connector
    template=None,               # dict, optional: Assessment template
    mode=AssessmentMode.AUTO,    # AssessmentMode: Assessment mode
    dimension_weights=None,      # dict, optional: Custom dimension weights
    config=None                  # dict, optional: Additional configuration
)
```

**Parameters:**
- **`connector`** (BaseConnector): Data source connector instance
- **`template`** (dict, optional): Assessment template configuration
- **`mode`** (AssessmentMode, optional): Assessment mode (AUTO, DISCOVERY, VALIDATION)
- **`dimension_weights`** (dict, optional): Custom weights for quality dimensions
- **`config`** (dict, optional): Additional configuration options

#### Core Methods

##### assess()

Perform a complete quality assessment of the data source.

```python
<!-- audience: ai-builders -->
# [STANDARD_CONTRIBUTOR]
result = assessor.assess()

# Access overall score
print(f"Overall Score: {result.score}/100")

# Access dimension scores
for dimension, score in result.dimension_scores.items():
    print(f"{dimension}: {score}/20")
```

**Returns:** `AssessmentResult` - Complete assessment results

##### assess_with_template(template)

Assess data source against a specific template configuration.

```python
<!-- audience: ai-builders -->
# [STANDARD_CONTRIBUTOR]
custom_template = {
    "template": {"name": "custom-v1.0", "version": "1.0.0"},
    "dimensions": {
        "validity": {"weight": 0.30},
        "completeness": {"weight": 0.25},
        "freshness": {"weight": 0.20},
        "consistency": {"weight": 0.15},
        "plausibility": {"weight": 0.10}
    }
}

result = assessor.assess_with_template(custom_template)
```

**Parameters:**
- **`template`** (dict): Template configuration dictionary

**Returns:** `AssessmentResult` - Assessment results using specified template

##### get_dimension_scores()

Get individual scores for each quality dimension.

```python
<!-- audience: ai-builders -->
# [STANDARD_CONTRIBUTOR]
dimension_scores = assessor.get_dimension_scores()

# Example output: {'validity': 18, 'completeness': 16, 'freshness': 19, ...}
for dimension, score in dimension_scores.items():
    status = "✅" if score >= 16 else "⚠️" if score >= 12 else "❌"
    print(f"{status} {dimension}: {score}/20")
```

**Returns:** `dict` - Dictionary mapping dimension names to scores

### AssessmentResult

Contains comprehensive results from a data quality assessment.

#### Properties

```python
<!-- audience: ai-builders -->
# [STANDARD_CONTRIBUTOR]
# Access result properties
print(f"Overall Score: {result.score}")                    # float: 0-100
print(f"Source: {result.source_name}")                     # str: Data source name
print(f"Type: {result.source_type}")                       # str: Data source type
print(f"Assessed: {result.assessment_date}")               # datetime: Assessment timestamp
print(f"Template: {result.template_name}")                 # str: Template used
print(f"ADRI Version: {result.adri_version}")              # str: ADRI version
print(f"Dimensions: {result.dimension_scores}")            # dict: Dimension scores
```

#### Core Methods

##### save_report(filename)

Save assessment results as a structured JSON report.

```python
<!-- audience: ai-builders -->
# [STANDARD_CONTRIBUTOR]
# Save detailed JSON report
result.save_report("quality_assessment.json")

# The saved file contains:
# {
#   "assessment": {
#     "score": 82.5,
#     "source_name": "customer_data.csv",
#     "assessment_date": "2025-06-20T15:30:00Z",
#     "dimension_scores": {...},
#     "issues": [...],
#     "recommendations": [...]
#   }
# }
```

**Parameters:**
- **`filename`** (str): Path where the JSON report will be saved

##### save_html_report(filename)

Generate a comprehensive HTML report with visualizations.

```python
<!-- audience: ai-builders -->
# [STANDARD_CONTRIBUTOR]
# Generate interactive HTML report
result.save_html_report("quality_dashboard.html")

# Creates an HTML file with:
# - Quality score visualization
# - Dimension breakdown charts
# - Issue summary tables
# - Improvement recommendations
# - Data profiling insights
```

**Parameters:**
- **`filename`** (str): Path where the HTML report will be saved

##### get_summary()

Get a human-readable text summary of assessment results.

```python
<!-- audience: ai-builders -->
# [STANDARD_CONTRIBUTOR]
summary = result.get_summary()
print(summary)

# Example output:
# """
# ADRI Assessment Summary
# ======================
# Overall Score: 82/100 (Good)
# 
# Dimension Scores:
# ✅ Validity: 18/20 (Excellent)
# ⚠️  Completeness: 14/20 (Needs Improvement)
# ✅ Freshness: 19/20 (Excellent)
# ✅ Consistency: 17/20 (Good)
# ✅ Plausibility: 16/20 (Good)
# 
# Top Issues:
# - Missing values in 'phone' column (15% missing)
# - Inconsistent date formats in 'signup_date'
# """
```

**Returns:** `str` - Formatted text summary

##### get_issues()

Get a structured list of all identified data quality issues.

```python
<!-- audience: ai-builders -->
# [STANDARD_CONTRIBUTOR]
issues = result.get_issues()

for issue in issues:
    print(f"🔍 {issue['dimension']}: {issue['description']}")
    print(f"   Severity: {issue['severity']}")
    print(f"   Affected: {issue['affected_records']} records")
    if 'recommendation' in issue:
        print(f"   Fix: {issue['recommendation']}")
    print()

# Example issue structure:
# {
#   "dimension": "completeness",
#   "description": "Missing values in required field",
#   "severity": "high",
#   "affected_records": 150,
#   "column": "email",
#   "recommendation": "Implement email validation at data entry"
# }
```

**Returns:** `list` - List of issue dictionaries with details and recommendations

##### get_issues_by_dimension(dimension)

Get issues filtered by a specific quality dimension.

```python
<!-- audience: ai-builders -->
# [STANDARD_CONTRIBUTOR]
# Get only validity issues
validity_issues = result.get_issues_by_dimension("validity")

for issue in validity_issues:
    print(f"Validity Issue: {issue['description']}")
    print(f"Column: {issue.get('column', 'N/A')}")
    print(f"Fix: {issue.get('recommendation', 'Manual review required')}")

# Common dimension names: 'validity', 'completeness', 'freshness', 'consistency', 'plausibility'
```

**Parameters:**
- **`dimension`** (str): Dimension name to filter by

**Returns:** `list` - List of issues for the specified dimension

### AssessmentMode

Enumeration defining different assessment approaches.

```python
<!-- audience: ai-builders -->
# [STANDARD_CONTRIBUTOR]
from adri import AssessmentMode

# Available assessment modes
AssessmentMode.AUTO       # Automatically choose mode based on available metadata
AssessmentMode.DISCOVERY  # Analyze raw data and suggest quality improvements
AssessmentMode.VALIDATION # Verify compliance with existing metadata/templates

# Usage examples
assessor_discovery = DataSourceAssessor(connector, mode=AssessmentMode.DISCOVERY)
assessor_validation = DataSourceAssessor(connector, mode=AssessmentMode.VALIDATION)

# Discovery mode: Best for new data sources
discovery_result = assessor_discovery.assess()
print("Discovery insights:", discovery_result.get_summary())

# Validation mode: Best for production data with established standards
validation_result = assessor_validation.assess()
print("Compliance status:", validation_result.get_summary())
```

**Mode Descriptions:**
- **`AUTO`**: Automatically selects DISCOVERY or VALIDATION based on available metadata
- **`DISCOVERY`**: Analyzes raw data patterns and suggests quality improvements
- **`VALIDATION`**: Verifies data compliance against established templates and metadata

---

## Connectors

Connectors provide standardized interfaces to different data sources.

### FileConnector

Connect to file-based data sources (CSV, Excel, JSON, Parquet).

```python
<!-- audience: ai-builders -->
# [STANDARD_CONTRIBUTOR]
from adri.connectors import FileConnector

# CSV file with custom settings
csv_connector = FileConnector(
    file_path="customer_data.csv",
    encoding="utf-8",
    delimiter=",",
    header=0
)

# Excel file with specific sheet
excel_connector = FileConnector(
    file_path="sales_data.xlsx",
    sheet_name="Q4_2024",
    header=1  # Skip first row
)

# JSON file
json_connector = FileConnector(
    file_path="api_response.json",
    file_type="json"
)

# Auto-detect file type
auto_connector = FileConnector("data_file.parquet")  # Type auto-detected
```

#### Constructor Parameters

```python
<!-- audience: ai-builders -->
# [STANDARD_CONTRIBUTOR]
FileConnector(
    file_path,                   # str: Path to the data file
    file_type=None,             # str, optional: File type ('csv', 'excel', 'json', 'parquet')
    encoding="utf-8",           # str: File encoding
    delimiter=",",              # str: Delimiter for CSV files
    sheet_name=0,               # str/int: Sheet name or index for Excel files
    header=0                    # int: Row number to use as header
)
```

#### Methods

##### get_data()

Load data as a pandas DataFrame.

```python
<!-- audience: ai-builders -->
# [STANDARD_CONTRIBUTOR]
connector = FileConnector("customer_data.csv")
df = connector.get_data()

print(f"Loaded {len(df)} rows and {len(df.columns)} columns")
print(f"Columns: {list(df.columns)}")
print(f"Data types:\n{df.dtypes}")
```

**Returns:** `pandas.DataFrame` - Data loaded from the file

##### get_schema()

Get structural information about the data source.

```python
<!-- audience: ai-builders -->
# [STANDARD_CONTRIBUTOR]
schema = connector.get_schema()

print("Schema Information:")
for column, info in schema.items():
    print(f"  {column}: {info['type']} (nullable: {info['nullable']})")

# Example schema structure:
# {
#   "customer_id": {"type": "string", "nullable": False},
#   "email": {"type": "string", "nullable": True},
#   "age": {"type": "integer", "nullable": True},
#   "signup_date": {"type": "datetime", "nullable": False}
# }
```

**Returns:** `dict` - Schema information with column types and constraints

##### get_metadata()

Get comprehensive metadata about the data source.

```python
<!-- audience: ai-builders -->
# [STANDARD_CONTRIBUTOR]
metadata = connector.get_metadata()

print("Data Source Metadata:")
print(f"  File size: {metadata['file_size']} bytes")
print(f"  Last modified: {metadata['last_modified']}")
print(f"  Row count: {metadata['row_count']}")
print(f"  Column count: {metadata['column_count']}")
print(f"  Encoding: {metadata['encoding']}")
```

**Returns:** `dict` - Comprehensive metadata including file properties and data statistics

### DatabaseConnector

Connect to database data sources (PostgreSQL, MySQL, SQLite, etc.).

```python
<!-- audience: ai-builders -->
# [STANDARD_CONTRIBUTOR]
from adri.connectors import DatabaseConnector

# PostgreSQL connection
pg_connector = DatabaseConnector(
    connection_string="postgresql://user:password@localhost:5432/database",
    table_name="customers",
    schema_name="public"
)

# Custom SQL query
query_connector = DatabaseConnector(
    connection_string="postgresql://user:password@localhost:5432/database",
    query="""
        SELECT customer_id, email, signup_date, last_order_date
        FROM customers 
        WHERE signup_date >= '2024-01-01'
        AND status = 'active'
    """
)

# SQLite connection
sqlite_connector = DatabaseConnector(
    connection_string="sqlite:///local_database.db",
    table_name="sales_data"
)
```

#### Constructor Parameters

```python
<!-- audience: ai-builders -->
# [STANDARD_CONTRIBUTOR]
DatabaseConnector(
    connection_string,          # str: Database connection string
    query=None,                # str, optional: SQL query to execute
    table_name=None,           # str, optional: Table name (if no query)
    schema_name="public",      # str: Schema name
    database_type=None         # str, optional: Database type (auto-detected)
)
```

### APIConnector

Connect to REST API data sources.

```python
<!-- audience: ai-builders -->
# [STANDARD_CONTRIBUTOR]
from adri.connectors import APIConnector

# Simple GET request
api_connector = APIConnector(
    url="https://api.example.com/customers",
    method="GET",
    headers={"Authorization": "Bearer your-token-here"}
)

# POST request with data
post_connector = APIConnector(
    url="https://api.example.com/search",
    method="POST",
    headers={"Content-Type": "application/json"},
    data={"query": "active_customers", "limit": 1000}
)

# API with authentication
auth_connector = APIConnector(
    url="https://api.example.com/data",
    auth=("username", "password"),
    params={"format": "json", "page_size": 500}
)
```

#### Constructor Parameters

```python
<!-- audience: ai-builders -->
# [STANDARD_CONTRIBUTOR]
APIConnector(
    url,                        # str: API endpoint URL
    method="GET",              # str: HTTP method
    headers=None,              # dict, optional: HTTP headers
    params=None,               # dict, optional: Query parameters
    data=None,                 # dict, optional: Request body
    auth=None,                 # tuple/object, optional: Authentication
    response_format="json"     # str: Expected response format
)
```

---

## Templates

Templates define assessment criteria and quality standards.

### Template Functions

```python
<!-- audience: ai-builders -->
# [STANDARD_CONTRIBUTOR]
from adri.templates import load_template, save_template, list_templates, validate_template
```

#### load_template(template_name_or_path)

Load a template by name or from a file path.

```python
<!-- audience: ai-builders -->
# [STANDARD_CONTRIBUTOR]
# Load built-in template
standard_template = load_template("standard-v1.0.0")

# Load custom template from file
custom_template = load_template("/path/to/my-template.yaml")

# Use template for assessment
connector = FileConnector("data.csv")
assessor = DataSourceAssessor(connector, template=custom_template)
result = assessor.assess()
```

**Parameters:**
- **`template_name_or_path`** (str): Built-in template name or file path

**Returns:** `dict` - Template configuration dictionary

#### save_template(template, path)

Save a template configuration to a file.

```python
<!-- audience: ai-builders -->
# [STANDARD_CONTRIBUTOR]
# Create custom template
custom_template = {
    "template": {
        "name": "financial-data-v1.0",
        "version": "1.0.0",
        "description": "Template for financial transaction data"
    },
    "dimensions": {
        "validity": {
            "weight": 0.25,
            "rules": [
                {
                    "rule": "email_format",
                    "weight": 0.20,
                    "columns": ["customer_email"]
                },
                {
                    "rule": "currency_format", 
                    "weight": 0.30,
                    "columns": ["transaction_amount"]
                }
            ]
        },
        "completeness": {
            "weight": 0.25,
            "required_fields": ["transaction_id", "customer_id", "amount", "date"]
        }
    }
}

# Save template
save_template(custom_template, "financial-template.yaml")
```

**Parameters:**
- **`template`** (dict): Template configuration
- **`path`** (str): File path to save the template

#### list_templates()

List all available built-in templates.

```python
<!-- audience: ai-builders -->
# [STANDARD_CONTRIBUTOR]
templates = list_templates()

print("Available Templates:")
for template in templates:
    print(f"  📋 {template.name} (v{template.version})")
    print(f"     {template.description}")
    print(f"     Use cases: {', '.join(template.use_cases)}")
    print()

# Example output:
# Available Templates:
#   📋 standard-v1.0.0 (v1.0.0)
#      General-purpose data quality assessment
#      Use cases: general, exploratory, baseline
#
#   📋 financial-v1.0.0 (v1.0.0)
#      Financial data with regulatory compliance
#      Use cases: banking, fintech, compliance
```

**Returns:** `list` - List of template information objects

#### validate_template(template_or_path)

Validate a template configuration.

```python
<!-- audience: ai-builders -->
# [STANDARD_CONTRIBUTOR]
# Validate template file
result = validate_template("my-template.yaml")

if result["valid"]:
    print("✅ Template is valid")
    print(f"Template name: {result['template_info']['name']}")
    print(f"Version: {result['template_info']['version']}")
else:
    print("❌ Template validation failed:")
    for error in result["errors"]:
        print(f"  - {error}")

# Validate template dictionary
template_dict = load_template("standard-v1.0.0")
validation = validate_template(template_dict)
```

**Parameters:**
- **`template_or_path`** (dict/str): Template configuration or file path

**Returns:** `dict` - Validation result with "valid" boolean and optional "errors" list

---

## Configuration

### Global Configuration

Configure ADRI behavior globally using configuration files or environment variables.

#### Configuration File

Create `~/.adri/config.yaml`:

```yaml
# [STANDARD_CONTRIBUTOR]
# ~/.adri/config.yaml
templates:
  directory: "/path/to/custom/templates"
  default: "standard-v1.0.0"
  
reporting:
  default_format: "html"
  output_directory: "/path/to/reports"
  include_recommendations: true
  
assessment:
  default_mode: "discovery"
  cache_results: true
  cache_duration_hours: 24
  
logging:
  level: "info"
  file: "/path/to/adri.log"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  
performance:
  max_memory_usage_mb: 1024
  parallel_processing: true
  max_workers: 4
```

#### Environment Variables

```bash
# [STANDARD_CONTRIBUTOR]
# Set environment variables for ADRI configuration
export ADRI_TEMPLATES_DIR="/path/to/templates"
export ADRI_DEFAULT_TEMPLATE="standard-v1.0.0"
export ADRI_DEFAULT_MODE="discovery"
export ADRI_LOG_LEVEL="debug"
export ADRI_CACHE_RESULTS="true"
export ADRI_MAX_WORKERS="8"
```

#### Programmatic Configuration

```python
<!-- audience: ai-builders -->
# [STANDARD_CONTRIBUTOR]
from adri import configure

# Configure ADRI programmatically
configure(
    templates_dir="/path/to/templates",
    default_template="standard-v1.0.0",
    default_mode="discovery",
    log_level="info",
    cache_results=True,
    max_workers=4
)

# Verify configuration
from adri.config import get_config
config = get_config()
print(f"Templates directory: {config['templates']['directory']}")
print(f"Default mode: {config['assessment']['default_mode']}")
```

---

## Command Line Interface

ADRI provides a comprehensive CLI for common operations.

### Basic Usage

```bash
# [STANDARD_CONTRIBUTOR]
# Basic assessment
adri assess --source data.csv

# Assessment with template
adri assess --source data.csv --template standard-v1.0.0

# Generate HTML report
adri assess --source data.csv --html-report quality_report.html

# Discovery mode assessment
adri assess --source data.csv --mode discovery --verbose
```

### Commands Reference

#### assess

Assess a data source for quality.

```bash
# [STANDARD_CONTRIBUTOR]
adri assess --source PATH [options]

# Options:
#   --source PATH              Path to data source (required)
#   --template NAME           Template name to use
#   --template-file PATH      Path to custom template file
#   --mode {auto,discovery,validation}  Assessment mode
#   --report PATH             Save JSON report to file
#   --html-report PATH        Save HTML report to file
#   --output-dir PATH         Directory for output files
#   --verbose                 Show detailed output
#   --quiet                   Suppress non-error output
#   --config PATH             Custom configuration file

# Examples:
adri assess --source customer_data.csv --template financial-v1.0.0 --html-report report.html
adri assess --source "postgresql://user:pass@host/db" --table customers --mode validation
```

#### templates

Manage assessment templates.

```bash
# [STANDARD_CONTRIBUTOR]
# List available templates
adri templates list

# Show template details
adri templates show standard-v1.0.0

# Validate template file
adri templates validate my-template.yaml

# Create template from assessment
adri templates create --from-assessment assessment.json --name my-template
```

#### init

Initialize a new ADRI project.

```bash
# [STANDARD_CONTRIBUTOR]
# Initialize in current directory
adri init

# Initialize in specific directory
adri init /path/to/project

# Initialize with template
adri init --template financial-v1.0.0 --name "Financial Data Quality Project"
```

#### config

Manage ADRI configuration.

```bash
# [STANDARD_CONTRIBUTOR]
# Show current configuration
adri config show

# Set configuration value
adri config set templates.default "custom-v1.0.0"

# Reset to defaults
adri config reset
```

---

## Custom Dimensions

Extend ADRI with custom quality dimensions for domain-specific requirements.

### Creating Custom Dimensions

```python
<!-- audience: ai-builders -->
# [STANDARD_CONTRIBUTOR]
from adri.dimensions import BaseDimensionAssessor, DimensionRegistry

class SecurityDimensionAssessor(BaseDimensionAssessor):
    """Custom dimension for assessing data security aspects"""
    
    def __init__(self, connector, config=None):
        super().__init__(connector, config)
        self.name = "security"
        self.description = "Assesses data security and privacy aspects"
        self.max_score = 20  # Score out of 20 points
    
    def assess(self):
        """Perform security assessment"""
        data = self.connector.get_data()
        
        # Calculate security score
        encryption_score = self._assess_encryption(data)
        pii_score = self._assess_pii_handling(data)
        access_score = self._assess_access_patterns(data)
        
        total_score = (encryption_score + pii_score + access_score) / 3
        
        # Identify security issues
        issues = []
        if encryption_score < 15:
            issues.append("Unencrypted sensitive data detected")
        if pii_score < 15:
            issues.append("PII data without proper anonymization")
        if access_score < 15:
            issues.append("Unrestricted access to sensitive fields")
        
        return {
            "score": total_score,
            "issues": issues,
            "details": {
                "encryption_level": encryption_score,
                "pii_protection": pii_score,
                "access_control": access_score,
                "sensitive_fields": self._identify_sensitive_fields(data)
            }
        }
    
    def _assess_encryption(self, data):
        """Assess encryption level of sensitive data"""
        # Implementation for encryption assessment
        sensitive_columns = ['ssn', 'credit_card', 'password']
        encrypted_count = 0
        
        for col in sensitive_columns:
            if col in data.columns:
                # Check if data appears encrypted (simplified check)
                sample_values = data[col].dropna().head(10)
                if self._appears_encrypted(sample_values):
                    encrypted_count += 1
        
        return min(20, encrypted_count * 7)  # Max 20 points
    
    def _assess_pii_handling(self, data):
        """Assess PII data handling"""
        pii_columns = ['email', 'phone', 'address', 'name']
        anonymized_count = 0
        
        for col in pii_columns:
            if col in data.columns:
                if self._is_anonymized(data[col]):
                    anonymized_count += 1
        
        return min(20, anonymized_count * 5)
    
    def _assess_access_patterns(self, data):
        """Assess data access control patterns"""
        # Simplified assessment - in practice, this would check
        # access logs, permissions, etc.
        return 18  # Placeholder score
    
    def _appears_encrypted(self, values):
        """Check if values appear to be encrypted"""
        # Simplified check - look for base64-like patterns
        import re
        pattern = r'^[A-Za-z0-9+/=]+$'
        return any(re.match(pattern, str(val)) for val in values)
    
    def _is_anonymized(self, series):
        """Check if PII data is anonymized"""
        # Simplified check - look for masked patterns
        sample = series.dropna().head(10)
        masked_count = sum(1 for val in sample if '*' in str(val) or 'xxx' in str(val).lower())
        return masked_count > len(sample) * 0.5
    
    def _identify_sensitive_fields(self, data):
        """Identify potentially sensitive data fields"""
        sensitive_patterns = {
            'ssn': r'\d{3}-\d{2}-\d{4}',
            'credit_card': r'\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}',
            'email': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
            'phone': r'\d{3}[-.]?\d{3}[-.]?\d{4}'
        }
        
        sensitive_fields = []
        for col in data.columns:
            for pattern_name, pattern in sensitive_patterns.items():
                if data[col].astype(str).str.contains(pattern, regex=True).any():
                    sensitive_fields.append({
                        'column': col,
                        'type': pattern_name,
                        'sample_count': data[col].astype(str).str.contains(pattern, regex=True).sum()
                    })
        
        return sensitive_fields

# Register the custom dimension
DimensionRegistry.register("security", SecurityDimensionAssessor)
```

### Using Custom Dimensions

```python
<!-- audience: ai-builders -->
# [STANDARD_CONTRIBUTOR]
from adri import DataSourceAssessor
from adri.connectors import FileConnector

# Use assessor with custom dimension
connector = FileConnector("sensitive_data.csv")
assessor = DataSourceAssessor(
    connector,
    dimension_weights={
        "validity": 0.15,
        "completeness": 0.15,
        "freshness": 0.15,
        "consistency": 0.15,
        "plausibility": 0.15,
        "security": 0.25  # Custom dimension with higher weight
    }
)

result = assessor.assess()

# Access custom dimension results
security_score = result.dimension_scores.get('security', 0)
print(f"Security Score: {security_score}/20")

# Get security-specific issues
security_issues = result.get_issues_by_dimension('security')
for issue in security_issues:
    print(f"Security Issue: {issue['description']}")
```

---

## Custom Rules

Create domain-specific validation rules for specialized assessment needs.

### Creating Custom Rules

```python
<!-- audience: ai-builders -->
# [STANDARD_CONTRIBUTOR]
from adri.rules import DiagnosticRule, RuleRegistry

class BusinessEmailRule(DiagnosticRule):
    """Rule to validate business email addresses"""
    
    def __init__(self, allowed_domains=None, blocked_domains=None):
        super().__init__()
        self.name = "business_email_validation"
        self.description = "Validates business email addresses against domain policies"
        self.allowed_domains = set(allowed_domains or [])
        self.blocked_domains = set(blocked_domains or [])
    
    def evaluate(self, data, column_name):
        """Evaluate email addresses in the specified column"""
        if column_name not in data.columns:
            return {
                "score": 0.0,
                "issues": [f"Column '{column_name}' not found in data"],
                "details": {"evaluated_count": 0}
            }
        
        email_series = data[column_name].dropna()
        total_emails = len(email_series)
        
        if total_emails == 0:
            return {
                "score": 0.0,
                "issues": ["No email addresses found to validate"],
                "details": {"evaluated_count": 0}
            }
        
        valid_count = 0
        issues = []
        domain_stats = {}
        
        for idx, email in enumerate(email_series):
            email_str = str(email).strip().lower()
            
            # Basic email format validation
            if '@' not in email_str or '.' not in email_str.split('@')[-1]:
                issues.append(f"Invalid email format at row {idx}: {email}")
                continue
            
            domain = email_str.split('@')[1]
            domain_stats[domain] = domain_stats.get(domain, 0) + 1
            
            # Domain validation
            if self.blocked_domains and domain in self.blocked_domains:
                issues.append(f"Blocked domain at row {idx}: {domain}")
                continue
            
            if self.allowed_domains and domain not in self.allowed_domains:
                issues.append(f"Unauthorized domain at row {idx}: {domain}")
                continue
            
            valid_count += 1
        
        # Calculate score based on percentage of valid emails
        score = valid_count / total_emails if total_emails > 0 else 0.0
        
        return {
            "score": score,
            "issues": issues,
            "details": {
                "valid_count": valid_count,
                "total_count": total_emails,
                "domain_distribution": domain_stats,
                "allowed_domains": list(self.allowed_domains),
                "blocked_domains": list(self.blocked_domains)
            }
        }

# Register the custom rule
RuleRegistry.register("business_email_validation", BusinessEmailRule)
```

### Using Custom Rules

```python
<!-- audience: ai-builders -->
# [STANDARD_CONTRIBUTOR]
# Create template with custom rule
template = {
    "template": {
        "name": "company-email-template",
        "version": "1.0.0",
        "description": "Template with business email validation"
    },
    "dimensions": {
        "validity": {
            "weight": 0.20,
            "rules": [
                {
                    "rule": "business_email_validation",
                    "weight": 0.40,
                    "parameters": {
                        "allowed_domains": ["company.com", "subsidiary.com"],
                        "blocked_domains": ["gmail.com", "yahoo.com", "hotmail.com"]
                    },
                    "columns": ["email", "contact_email"]
                }
            ]
        }
    }
}

# Use template with custom rule
from adri import DataSourceAssessor
from adri.connectors import FileConnector
from adri.templates import save_template

# Save and use the template
save_template(template, "company-email-template.yaml")

connector = FileConnector("employees.csv")
assessor = DataSourceAssessor(connector, template=template)
result = assessor.assess()

# Check business email validation results
validity_issues = result.get_issues_by_dimension("validity")
for issue in validity_issues:
    if "business_email_validation" in issue.get("rule", ""):
        print(f"Email Issue: {issue['description']}")
```

---

## Framework Integration

### Pandas Integration

```python
<!-- audience: ai-builders -->
# [STANDARD_CONTRIBUTOR]
import pandas as pd
from adri import DataSourceAssessor
from adri.connectors import DataFrameConnector

# Create and preprocess DataFrame
df = pd.read_csv("customer_data.csv")

# Data preprocessing
df['age'] = pd.to_numeric(df['age'], errors='coerce')
df['email'] = df['email'].str.lower().str.strip()
df['signup_date'] = pd.to_datetime(df['signup_date'])

# Assess the preprocessed DataFrame
connector = DataFrameConnector(df)
assessor = DataSourceAssessor(connector)
result = assessor.assess()

# Convert results to DataFrame for analysis
issues_df = pd.DataFrame(result.get_issues())
print("Issues by dimension:")
print(issues_df.groupby('dimension').size())

# Quality score by column
dimension_scores = pd.Series(result.dimension_scores)
print("\nDimension scores:")
print(dimension_scores.sort_values(ascending=False))
```

### Scikit-learn Integration

```python
<!-- audience: ai-builders -->
# [STANDARD_CONTRIBUTOR]
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from adri import DataSourceAssessor
from adri.connectors import DataFrameConnector

class ADRIQualityCheck:
    """Scikit-learn compatible transformer for data quality validation"""
    
    def __init__(self, minimum_score=70, fail_on_low_quality=False):
        self.minimum_score = minimum_score
        self.fail_on_low_quality = fail_on_low_quality
        self.last_assessment = None
    
    def fit(self, X, y=None):
        """Fit the quality checker (no-op for this transformer)"""
        return self
    
    def transform(self, X):
        """Check data quality and optionally fail pipeline"""
        # Assess data quality
        connector = DataFrameConnector(X)
        assessor = DataSourceAssessor(connector)
        result = assessor.assess()
        
        self.last_assessment = result
        
        # Check quality threshold
        if result.score < self.minimum_score:
            message = f"Data quality score ({result.score:.1f}) below threshold ({self.minimum_score})"
            
            if self.fail_on_low_quality:
                raise ValueError(f"Quality check failed: {message}")
            else:
                print(f"Warning: {message}")
                print("Top issues:")
                for issue in result.get_issues()[:3]:
                    print(f"  - {issue['dimension']}: {issue['description']}")
        
        return X
    
    def get_quality_report(self):
        """Get the last quality assessment report"""
        return self.last_assessment

# Create pipeline with quality check
pipeline = Pipeline([
    ('quality_check', ADRIQualityCheck(minimum_score=75)),
    ('scaler', StandardScaler()),
    ('classifier', RandomForestClassifier(random_state=42))
])

# Use pipeline with quality validation
# pipeline.fit(X_train, y_train)
# predictions = pipeline.predict(X_test)

# Access quality report
# quality_checker = pipeline.named_steps['quality_check']
# quality_report = quality_checker.get_quality_report()
# print(f"Training data quality: {quality_report.score}/100")
```

### Apache Airflow Integration

```python
<!-- audience: ai-builders -->
# [STANDARD_CONTRIBUTOR]
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.exceptions import AirflowException
from datetime import datetime, timedelta
from adri import DataSourceAssessor
from adri.connectors import FileConnector

def assess_data_quality(**context):
    """Airflow task to assess data quality"""
    
    # Get file path from context
    file_path = context['params']['file_path']
    min_score = context['params'].get('min_score', 70)
    
    # Assess data quality
    connector = FileConnector(file_path)
    assessor = DataSourceAssessor(connector)
    result = assessor.assess()
    
    # Save assessment report
    report_path = f"{file_path}_quality_report.json"
    result.save_report(report_path)
    
    # Check quality threshold
    if result.score < min_score:
        raise AirflowException(
            f"Data quality check failed: {result.score:.1f} < {min_score}. "
            f"Report saved to {report_path}"
        )
    
    # Push quality score to XCom for downstream tasks
    context['task_instance'].xcom_push(
        key='quality_score',
        value=result.score
    )
    
    print(f"✅ Data quality check passed: {result.score:.1f}/100")
    return result.score

# Define DAG
dag = DAG(
    'data_quality_pipeline',
    default_args={
        'owner': 'data-team',
        'depends_on_past': False,
        'start_date': datetime(2025, 1, 1),
        'email_on_failure': True,
        'email_on_retry': False,
        'retries': 1,
        'retry_delay': timedelta(minutes=5)
    },
    description='Data pipeline with quality gates',
    schedule_interval=timedelta(hours=6),
    catchup=False
)

# Quality check task
quality_check = PythonOperator(
    task_id='assess_data_quality',
    python_callable=assess_data_quality,
    params={
        'file_path': '/data/customer_data.csv',
        'min_score': 80
    },
    dag=dag
)

# Downstream processing task (only runs if quality check passes)
def process_data(**context):
    quality_score = context['task_instance'].xcom_pull(
        task_ids='assess_data_quality',
        key='quality_score'
    )
    print(f"Processing data with quality score: {quality_score}")
    # Data processing logic here

process_task = PythonOperator(
    task_id='process_data',
    python_callable=process_data,
    dag=dag
)

# Set task dependencies
quality_check >> process_task
```

---

## Error Handling

ADRI provides specific exceptions for different error conditions.

### Exception Hierarchy

```python
<!-- audience: ai-builders -->
# [STANDARD_CONTRIBUTOR]
from adri.exceptions import (
    ADRIError,                # Base exception for all ADRI errors
    TemplateError,            # Template-related errors
    ConnectorError,           # Data connector errors
    AssessmentError,          # Assessment process errors
    ValidationError,          # Data validation errors
    ConfigurationError        # Configuration errors
)

# Comprehensive error handling
try:
    connector = FileConnector("data.csv")
    assessor = DataSourceAssessor(connector)
    result = assessor.assess()
    
except ConnectorError as e:
    print(f"❌ Data connection failed: {e}")
    print("Check file path, permissions, and format")
    
except TemplateError as e:
    print(f"❌ Template error: {e}")
    print("Verify template format and required fields")
    
except AssessmentError as e:
    print(f"❌ Assessment failed: {e}")
    print("Check data format and assessment configuration")
    
except ValidationError as e:
    print(f"❌ Validation error: {e}")
    print("Review data validation rules and constraints")
    
except ConfigurationError as e:
    print(f"❌ Configuration error: {e}")
    print("Check ADRI configuration settings")
    
except ADRIError as e:
    print(f"❌ General ADRI error: {e}")
    print("Check ADRI installation and dependencies")
    
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    print("Contact support with error details")
```

### Error Recovery Patterns

```python
<!-- audience: ai-builders -->
# [STANDARD_CONTRIBUTOR]
from adri.exceptions import ConnectorError, AssessmentError
import logging

def robust_assessment(file_path, fallback_template=None):
    """Perform assessment with error recovery"""
    
    logger = logging.getLogger(__name__)
    
    try:
        # Primary assessment attempt
        connector = FileConnector(file_path)
        assessor = DataSourceAssessor(connector)
        result = assessor.assess()
        
        logger.info(f"✅ Assessment successful: {result.score}/100")
        return result
        
    except ConnectorError as e:
        logger.warning(f"Connector failed: {e}")
        
        # Try alternative file formats
        for file_type in ['csv', 'excel', 'json']:
            try:
                connector = FileConnector(file_path, file_type=file_type)
                assessor = DataSourceAssessor(connector)
                result = assessor.assess()
                
                logger.info(f"✅ Assessment successful with {file_type} format")
                return result
                
            except ConnectorError:
                continue
        
        logger.error("❌ All connector attempts failed")
        raise
        
    except AssessmentError as e:
        logger.warning(f"Assessment failed: {e}")
        
        if fallback_template:
            try:
                # Try with fallback template
                assessor = DataSourceAssessor(connector, template=fallback_template)
                result = assessor.assess()
                
                logger.info("✅ Assessment successful with fallback template")
                return result
                
            except AssessmentError:
                logger.error("❌ Fallback assessment also failed")
                raise
        
        raise

# Usage with error recovery
try:
    result = robust_assessment(
        "problematic_data.csv",
        fallback_template="standard-v1.0.0"
    )
    print(f"Quality Score: {result.score}/100")
    
except Exception as e:
    print(f"Assessment failed completely: {e}")
```

---

## Version Information

### Version Checking

```python
<!-- audience: ai-builders -->
# [STANDARD_CONTRIBUTOR]
from adri.version import __version__, is_version_compatible, get_version_info

# Get current version
print(f"ADRI version: {__version__}")

# Check compatibility with specific version
if is_version_compatible("0.3.0"):
    print("✅ Version 0.3.0 is compatible")
else:
    print("❌ Version 0.3.0 is not compatible")

# Get detailed version information
version_info = get_version_info()
print(f"Version: {version_info['version']}")
print(f"Build date: {version_info['build_date']}")
print(f"Git commit: {version_info['git_commit']}")
print(f"Python version: {version_info['python_version']}")
```

### Compatibility Checking

```python
<!-- audience: ai-builders -->
# [STANDARD_CONTRIBUTOR]
from adri.version import check_dependencies, validate_environment

# Check all dependencies
deps_status = check_dependencies()
for dep, status in deps_status.items():
    icon = "✅" if status['compatible'] else "❌"
    print(f"{icon} {dep}: {status['version']} (required: {status['required']})")

# Validate complete environment
env_status = validate_environment()
if env_status['valid']:
    print("✅ Environment is valid for ADRI")
else:
    print("❌ Environment issues detected:")
    for issue in env_status['issues']:
        print(f"  - {issue}")
```

---

## Performance Optimization

### Caching and Performance

```python
<!-- audience: ai-builders -->
# [STANDARD_CONTRIBUTOR]
from adri import DataSourceAssessor, configure
from adri.connectors import FileConnector

# Configure performance settings
configure(
    cache_results=True,
    cache_duration_hours=24,
    max_workers=8,
    parallel_processing=True,
    max_memory_usage_mb=2048
)

# Use caching for repeated assessments
connector = FileConnector("large_dataset.csv")
assessor = DataSourceAssessor(connector)

# First assessment (will be cached)
result1 = assessor.assess()
print(f"First assessment: {result1.score}/100")

# Second assessment (will use cache if data unchanged)
result2 = assessor.assess()
print(f"Cached assessment: {result2.score}/100")

# Force fresh assessment
result3 = assessor.assess(use_cache=False)
print(f"Fresh assessment: {result3.score}/100")
```

### Batch Processing

```python
<!-- audience: ai-builders -->
# [STANDARD_CONTRIBUTOR]
from adri.batch import BatchAssessor
from concurrent.futures import ThreadPoolExecutor
import os

def assess_multiple_files(file_paths, template=None, max_workers=4):
    """Assess multiple files in parallel"""
    
    def assess_single_file(file_path):
        try:
            connector = FileConnector(file_path)
            assessor = DataSourceAssessor(connector, template=template)
            result = assessor.assess()
            
            return {
                'file': file_path,
                'score': result.score,
                'status': 'success',
                'issues_count': len(result.get_issues())
            }
        except Exception as e:
            return {
                'file': file_path,
                'score': 0,
                'status': 'error',
                'error': str(e)
            }
    
    # Process files in parallel
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(assess_single_file, file_paths))
    
    return results

# Example usage
data_files = [
    "customer_data_2024_01.csv",
    "customer_data_2024_02.csv", 
    "customer_data_2024_03.csv"
]

batch_results = assess_multiple_files(data_files, max_workers=3)

for result in batch_results:
    status_icon = "✅" if result['status'] == 'success' else "❌"
    print(f"{status_icon} {result['file']}: {result['score']}/100")
    if result['status'] == 'error':
        print(f"   Error: {result['error']}")
```

---

## Next Steps

### 📚 **Learn More**
- **[Understanding Quality Dimensions →](../dimensions/)** - Deep dive into quality assessment
- **[Template Development →](../templates/)** - Create custom assessment templates
- **[Integration Patterns →](../../examples/)** - Real-world integration examples

### 🛠️ **Extend ADRI**
- **[Custom Dimensions Guide →](standard-contributors/extending-dimensions.md)** - Add new quality dimensions
- **[Custom Rules Guide →](standard-contributors/extending-rules.md)** - Create validation rules
- **[Connector Development →](standard-contributors/creating-connectors.md)** - Support new data sources

### 🤝 **Get Help**
- **[Community Forum →](https://github.com/adri-ai/adri/discussions)** - Ask questions
- **[Discord Chat →](https://discord.gg/adri)** - Real-time help
- **[Issue Tracker →](https://github.com/adri-ai/adri/issues)** - Report bugs

---

## Purpose & Test Coverage

**Why this file exists**: Provides comprehensive technical reference for developers integrating ADRI into their applications, covering all API classes, methods, and advanced usage patterns.

**Key responsibilities**:
- Document all public API classes and methods with examples
- Provide integration patterns for popular frameworks
- Show error handling and performance optimization techniques
- Guide advanced customization through custom dimensions and rules

**Test coverage**: All code examples tested with STANDARD_CONTRIBUTOR audience validation rules, ensuring they demonstrate proper API usage patterns for technical integrators.
