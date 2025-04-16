# Implementation Guide

This guide explains how to use the Agent Data Readiness Index (ADRI) to assess your organization's data sources for agent readiness.

## Getting Started

### Prerequisites

- Python 3.8+
- Access to the data sources you wish to evaluate
- Permissions to read metadata about these data sources

### Installation

```bash
# Install from PyPI
pip install adri

# Or install from source
git clone https://github.com/verodat/agent-data-readiness-index.git
cd agent-data-readiness-index
pip install -e .
```

## Basic Usage

### Command Line Interface

The simplest way to run an assessment is through the CLI:

```bash
# Run assessment on a CSV file
adri assess --source my_data.csv --output report.json

# Run assessment on a database
adri assess --source "postgresql://user:pass@host/db" --table my_table --output report.json

# Run assessment on multiple sources via config
adri assess --config sources.yaml --output report_dir
```
*(Note: Outputting multiple reports usually requires an output directory)*

### Python API

You can also use ADRI programmatically:

```python
from adri import DataSourceAssessor

# Assess a single file
assessor = DataSourceAssessor()
report = assessor.assess_file("my_data.csv")
print(f"Overall score: {report.overall_score}")

# Assess a database table
# Ensure database dependencies are installed: pip install adri[database]
report_db = assessor.assess_database("postgresql://user:pass@host/db", "my_table")

# Assess an API
# Ensure API dependencies are installed: pip install adri[api]
report_api = assessor.assess_api("https://api.example.com/data")

# Save the report
report.save_json("report.json")
report.save_html("report.html")
```

## Assessment Configuration

### Source Configuration (using YAML)

Configure multiple data sources in a YAML file (e.g., `sources.yaml`):

```yaml
sources:
  - name: Customer Data
    type: database
    connection: "postgresql://user:pass@host/db"
    table: customers
    description: "Main customer database"
    
  - name: Product Catalog
    type: file
    path: "/data/products.csv"
    description: "Product information"
    
  - name: Transaction History
    type: api
    endpoint: "https://api.example.com/transactions"
    auth: "Bearer ${API_TOKEN}" # Environment variables can be used
    description: "Customer transaction history"
```

Run assessment using the config:
```bash
adri assess --config sources.yaml --output reports/
```

### Customizing Assessment Parameters

You can customize the assessment process via the same YAML configuration or directly in code:

```yaml
# Example config.yaml
assessment_defaults: # Optional: Apply to all sources unless overridden
  dimensions: [validity, completeness, freshness] # Only assess these

sources:
  - name: Customer Data
    type: database
    # ... connection details ...
    assessment_config: # Specific config for this source
      dimensions: # Override default dimensions
        validity:
          weight: 1.0 # Default weight
          thresholds: # Optional: Custom thresholds for this source
            basic: 5
            intermediate: 10
            advanced: 15
        freshness:
          weight: 1.5 # Emphasize freshness more for this source
        # Other dimensions...
      custom_checks: # Optional: Add custom checks
        - name: "Customer ID format check"
          dimension: "validity"
          script: "./custom_checks/customer_id_check.py"

  - name: Product Catalog
    type: file
    # ... path details ...
    # Inherits assessment_defaults if assessment_config not specified
```

Pass this config to the assessor:
```python
import yaml
from adri import DataSourceAssessor

with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Assessor uses defaults from config
assessor = DataSourceAssessor(config=config.get('assessment_defaults', {}))

# Assess specific source using its config
source_config = config['sources'][0]
source_assessment_config = source_config.get('assessment_config', {})
# You might need to merge defaults and source-specific config here
# ... then potentially create a new assessor instance or pass config to assess methods ...
# (Note: Current assessor might need refinement to handle per-source config overrides easily)

# Or assess all from config file (handles config internally)
reports = assessor.assess_from_config('config.yaml')
```

## Understanding Results

### Report Structure

The assessment generates a comprehensive report (JSON and optionally HTML) with:

- Overall ADRI score (0-100)
- Dimension scores (0-20 for each dimension)
- Detailed findings for each dimension
- Recommendations for improvement
- Data source metadata
- ADRI version and assessment configuration used
- Visualizations (Radar chart in HTML report)

### Interpreting Scores

The overall score translates to a readiness level:

- **80-100**: Advanced - Ready for critical agentic applications
- **60-79**: Proficient - Suitable for most production agent uses
- **40-59**: Basic - Requires caution in agent applications
- **20-39**: Limited - Significant agent blindness risk
- **0-19**: Inadequate - Not recommended for agentic use

Focus on the scores and recommendations for individual dimensions to pinpoint specific areas of "agent blindness".

### Sample Report Snippet (JSON)

```json
{
  "source_name": "Customer Data",
  "source_type": "database",
  "source_metadata": { /* ... */ },
  "assessment_time": "2025-04-16T13:20:00.123Z",
  "adri_version": "0.1.0",
  "assessment_config": { /* ... config used ... */ },
  "overall_score": 68.0,
  "readiness_level": "Proficient - Suitable for most production agent uses",
  "dimension_results": {
    "validity": {
      "score": 16.0,
      "findings": [
        "Data types are well-defined and communicated",
        "Range validation exists but not exposed to agents",
        "Format violations are logged but not explicitly flagged"
      ],
      "recommendations": [
        "Expose validation errors in a machine-readable format",
        "Add explicit signals when validation checks are skipped"
      ]
    },
    "completeness": { /* ... */ },
    "freshness": { /* ... */ },
    "consistency": { /* ... */ },
    "plausibility": { /* ... */ }
  },
  "summary_findings": [ /* ... */ ],
  "summary_recommendations": [ /* ... */ ]
}
```

## Best Practices

1.  **Start Small**: Begin with a few critical data sources used by your agents.
2.  **Involve Stakeholders**: Share ADRI reports with data providers, AI engineers, and business owners to create shared understanding.
3.  **Prioritize Improvements**: Focus on dimensions with the lowest scores or those most critical for your agent's function. Use the recommendations as a guide.
4.  **Integrate Early & Often**: Add ADRI checks to your data pipelines or CI/CD processes for continuous monitoring. Use the framework integrations (Guard, LangChain, etc.).
5.  **Benchmark**: Compare your scores over time and potentially against the community catalog for similar datasets.
6.  **Document Configuration**: Keep your assessment configuration files (`config.yaml`) under version control.

## Next Steps

After completing your assessment:
1. Review the detailed findings and recommendations in your report(s).
2. Prioritize improvements based on agent impact and implementation effort.
3. Implement changes to data sources or surrounding systems to expose quality signals.
4. Re-assess periodically to track progress and ensure continued readiness.
5. Consider contributing your anonymized assessment of public datasets to the community catalog! (See [CONTRIBUTING.md](CONTRIBUTING.md))
