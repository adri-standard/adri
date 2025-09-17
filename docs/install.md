# ADRI Installation Guide

## Quick Installation

```bash
pip install adri
```

## Development Installation (src/ layout)

```bash
git clone https://github.com/adri-standard/adri.git
cd adri
pip install -e .
```

## Verify Installation

```bash
# Test import
python -c "import adri; print(f'ADRI {adri.__version__} installed successfully!')"

# Test CLI
adri --version
adri --help
```

## Initialize Your Project

```bash
# Initialize ADRI in your project
adri setup --project-name "my-ai-project"

# Verify setup
adri show-config
```

## Requirements

- Python 3.10+
- pandas>=1.5.0
- pyyaml>=6.0
- click>=8.0
- pyarrow>=14.0.0 (for Parquet support)
- requests>=2.28.0 (for Verodat integration)

## Optional Dependencies

### For Enterprise Logging
```bash
pip install requests  # Verodat API integration
```

### For Development
```bash
pip install adri[dev]  # Includes testing and development tools
```

## Environment Variables

```bash
# Required for standards loading
export ADRI_STANDARDS_PATH="./examples/standards"

# Optional environment indicator
export ADRI_ENV="DEVELOPMENT"  # or PRODUCTION

# For Verodat enterprise logging
export VERODAT_API_KEY="your-api-key"
```

## Quick Start

```python
from adri import adri_protected

@adri_protected(standard="customer_data_standard")
def process_customers(customer_data):
    # Your AI agent logic here
    return analyze_customers(customer_data)
```

## Troubleshooting

### Import Errors
- Ensure you're importing from the new structure: `from adri import adri_protected`
- Not: `from adri.decorators.guard import adri_protected` (legacy)

### Standards Not Found
- Set `ADRI_STANDARDS_PATH` environment variable
- Run `adri list-standards` to see available standards
- Generate standards: `adri generate-standard your-data.csv`

### Configuration Issues  
- Run `adri show-config` to check current settings
- Verify directory structure exists: `ls ADRI/dev/`
- Re-initialize if needed: `adri setup --force`

For more detailed information, see the [main documentation](../README.md).
