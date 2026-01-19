# Tutorial Scenarios Documentation

This document catalogs all available tutorial-based test scenarios and provides usage examples.

## Overview

Tutorial scenarios provide realistic test fixtures based on actual ADRI tutorial workflows. Each scenario:

1. **Copies tutorial data** from `ADRI/tutorials/` to test project
2. **Generates standards** using actual ADRI CLI commands
3. **Returns metadata** for easy test integration
4. **Uses development environment** (no special test environment)

## Design Principles

### Tutorial Data as Foundation
- Sample data from `ADRI/tutorials/` seeds standard generation
- Follows the same workflow users experience in tutorials
- Ensures tests validate real-world usage patterns

### Full ADRI Workflow
- Standards are **generated**, not pre-built templates
- Uses actual CLI: `adri generate-standard --data <csv>`
- Mimics how users create their own standards

### Development Environment Only
- Tests use `development` environment from config
- No special `testing` environment needed
- Name-only standard resolution: `standard="invoice_data"`

### Name-Only Resolution
All generated standards use name-only format for realistic testing:
```python
# ✅ Correct: Name only (as users would do)
@adri_protected(contract="invoice_data")
def process_invoices(data):
    return data

# ❌ Wrong: Full path (not user-friendly)
@adri_protected(contract="ADRI/dev/contracts/invoice_data.yaml")
def process_invoices(data):
    return data
```

## Available Scenarios

### Invoice Processing

**Scenario Name:** `invoice_processing`

**Description:** Invoice data validation with quality checks

**Fixture:** `invoice_scenario`

**Data Files:**
- `invoice_data.csv` - Clean training data
- `test_invoice_data.csv` - Test data with quality issues

**Generated Standard:** `invoice_data`

**Standard Location:** `ADRI/dev/contracts/invoice_data.yaml`

**Usage Example:**

```python
def test_invoice_validation(invoice_scenario):
    """Test invoice processing with tutorial-generated standard."""
    import pandas as pd
    from src.adri.decorator import adri_protected

    # Use name-only resolution
    @adri_protected(contract=invoice_scenario['generated_standard_name'])
    def validate_invoices(df):
        return df

    # Test with clean training data
    clean_data = pd.read_csv(invoice_scenario['training_data_path'])
    result = validate_invoices(clean_data)
    assert result is not None

    # Test with problematic data
    test_data = pd.read_csv(invoice_scenario['test_data_path'])
    # This should raise or warn based on data quality issues
```

**Scenario Metadata:**

```python
{
    'name': 'invoice_processing',
    'tutorial_dir': Path('ADRI/tutorials/invoice_processing'),
    'training_data_path': Path('ADRI/tutorials/invoice_processing/invoice_data.csv'),
    'test_data_path': Path('ADRI/tutorials/invoice_processing/test_invoice_data.csv'),
    'generated_standard_name': 'invoice_data',
    'standard_path': Path('ADRI/dev/contracts/invoice_data.yaml'),
    'description': 'Invoice processing tutorial with data quality validation'
}
```

## Fixtures Reference

### tutorial_project

**Type:** Pytest fixture

**Returns:** `Path` - Project root directory

**Purpose:** Creates test project with complete ADRI structure

**Setup:**
1. Copies `tests/test_adri_config.yaml` to project root
2. Creates `ADRI/dev/` directories (standards, assessments, training-data)
3. Creates `ADRI/prod/` directories (standards, assessments, training-data)
4. Creates `ADRI/tutorials/` directory
5. Sets environment variables (`ADRI_ENV=development`)

**Usage:**

```python
def test_something(tutorial_project):
    """Test using tutorial project structure."""
    # Project has full ADRI directory structure
    config = tutorial_project / "adri-config.yaml"
    assert config.exists()

    # Development directories ready for use
    standards_dir = tutorial_project / "ADRI" / "dev" / "standards"
    assert standards_dir.exists()
```

### invoice_scenario

**Type:** Pytest fixture

**Returns:** `TutorialScenario` - Complete scenario metadata

**Depends On:** `tutorial_project`

**Purpose:** Sets up complete invoice processing scenario

**Setup:**
1. Creates `ADRI/tutorials/invoice_processing/` directory
2. Copies tutorial data files from source
3. Generates standard using ADRI CLI
4. Returns scenario metadata

**Usage:**

```python
def test_invoice_processing(invoice_scenario):
    """Test with invoice scenario."""
    # Access all scenario components
    assert invoice_scenario['name'] == 'invoice_processing'
    assert invoice_scenario['training_data_path'].exists()
    assert invoice_scenario['test_data_path'].exists()
    assert invoice_scenario['standard_path'].exists()

    # Use generated standard by name
    standard_name = invoice_scenario['generated_standard_name']
    # standard_name == 'invoice_data'
```

## Utility Classes

### TutorialScenarios

**Purpose:** Static methods for scenario setup and data management

**Key Methods:**

#### copy_tutorial_data(source_tutorial, dest_dir)

Copies tutorial CSV files to test location.

**Parameters:**
- `source_tutorial` (str): Tutorial name (e.g., "invoice_processing")
- `dest_dir` (Path): Destination directory

**Returns:** `Tuple[Path, Path]` - (training_data_path, test_data_path)

**Example:**

```python
from tests.fixtures.tutorial_scenarios import TutorialScenarios

training, test = TutorialScenarios.copy_tutorial_data(
    source_tutorial="invoice_processing",
    dest_dir=project_root / "data"
)
```

#### generate_standard_from_data(project_root, config)

Generates ADRI standard using actual CLI.

**Parameters:**
- `project_root` (Path): Test project root
- `config` (StandardGenConfig): Generation configuration

**Returns:** `str` - Standard name (no extension)

**Example:**

```python
from tests.fixtures.tutorial_scenarios import TutorialScenarios, StandardGenConfig

config: StandardGenConfig = {
    'source_data': Path('data/invoices.csv'),
    'output_name': 'invoice_standard',
    'threshold': 75.0,
    'include_plausibility': True
}

standard_name = TutorialScenarios.generate_standard_from_data(
    project_root=project_root,
    config=config
)
# Returns: 'invoice_standard'
```

#### setup_invoice_processing(project_root)

Complete invoice scenario setup.

**Parameters:**
- `project_root` (Path): Test project root with ADRI structure

**Returns:** `TutorialScenario` - Complete scenario metadata

**Example:**

```python
from tests.fixtures.tutorial_scenarios import TutorialScenarios

scenario = TutorialScenarios.setup_invoice_processing(project_root)
assert scenario['generated_standard_name'] == 'invoice_data'
```

### StandardTemplates

**Purpose:** Load generated standards as dictionaries

**Key Methods:**

#### from_tutorial(tutorial_name, project_root)

Loads standard template from tutorial scenario.

**Parameters:**
- `tutorial_name` (str): Tutorial name (e.g., "invoice_processing")
- `project_root` (Path): Project root path

**Returns:** `Dict[str, Any]` - Standard content

**Example:**

```python
from tests.fixtures.tutorial_scenarios import StandardTemplates

standard_dict = StandardTemplates.from_tutorial(
    tutorial_name="invoice_processing",
    project_root=project_root
)

# Inspect standard content
assert 'metadata' in standard_dict or 'name' in standard_dict
```

#### invoice_processing_standard(project_root)

Shortcut for loading invoice processing standard.

**Parameters:**
- `project_root` (Path): Project root path

**Returns:** `Dict[str, Any]` - Invoice standard content

**Example:**

```python
from tests.fixtures.tutorial_scenarios import StandardTemplates

standard = StandardTemplates.invoice_processing_standard(project_root)
```

## Type Definitions

### TutorialScenario

Complete scenario metadata structure.

```python
from typing import TypedDict
from pathlib import Path

class TutorialScenario(TypedDict):
    name: str                       # Scenario identifier
    tutorial_dir: Path              # Tutorial directory path
    training_data_path: Path        # Clean training CSV
    test_data_path: Path            # Test CSV with issues
    generated_standard_name: str    # Standard name (no extension)
    standard_path: Path             # Full path to standard YAML
    description: str                # Human-readable description
```

### StandardGenConfig

Standard generation configuration.

```python
from typing import TypedDict
from pathlib import Path

class StandardGenConfig(TypedDict):
    source_data: Path               # CSV file to analyze
    output_name: str                # Standard name (no .yaml)
    threshold: float                # Overall minimum score
    include_plausibility: bool      # Include plausibility rules
```

## Common Patterns

### Basic Scenario Usage

```python
def test_with_scenario(invoice_scenario):
    """Most common pattern - use scenario directly."""
    @adri_protected(contract=invoice_scenario['generated_standard_name'])
    def process_data(df):
        return df

    data = pd.read_csv(invoice_scenario['training_data_path'])
    result = process_data(data)
    assert result is not None
```

### Manual Scenario Setup

```python
def test_manual_setup(tutorial_project):
    """Set up scenario manually for custom configuration."""
    scenario = TutorialScenarios.setup_invoice_processing(tutorial_project)

    # Now use scenario as needed
    assert scenario['standard_path'].exists()
```

### Custom Standard Generation

```python
def test_custom_standard(tutorial_project):
    """Generate custom standard from tutorial data."""
    # Copy data first
    training, test = TutorialScenarios.copy_tutorial_data(
        source_tutorial="invoice_processing",
        dest_dir=tutorial_project / "custom_data"
    )

    # Generate with custom config
    config: StandardGenConfig = {
        'source_data': training,
        'output_name': 'custom_invoice_standard',
        'threshold': 90.0,  # Higher threshold
        'include_plausibility': False
    }

    standard_name = TutorialScenarios.generate_standard_from_data(
        project_root=tutorial_project,
        config=config
    )

    assert standard_name == 'custom_invoice_standard'
```

### Inspecting Generated Standards

```python
def test_inspect_standard(invoice_scenario, tutorial_project):
    """Examine generated standard content."""
    from tests.fixtures.tutorial_scenarios import StandardTemplates

    standard = StandardTemplates.from_tutorial(
        tutorial_name="invoice_processing",
        project_root=tutorial_project
    )

    # Inspect standard structure
    assert 'metadata' in standard or 'name' in standard
    # Add more specific assertions based on your needs
```

## Migration from Legacy Fixtures

### Old Pattern (Legacy)

```python
from tests.fixtures.modern_fixtures import ModernFixtures

def test_old_way(test_project):
    """Legacy fixture pattern."""
    standard = ModernFixtures.create_minimal_standard(
        project_root=test_project,
        name="test_standard"
    )
    # Standard is a hardcoded template
```

### New Pattern (Tutorial-Based)

```python
def test_new_way(invoice_scenario):
    """Tutorial-based pattern."""
    # Standard is generated from real data
    standard_name = invoice_scenario['generated_standard_name']

    @adri_protected(contract=standard_name)
    def process_data(df):
        return df

    data = pd.read_csv(invoice_scenario['training_data_path'])
    result = process_data(data)
```

### Benefits of Migration

1. **Realistic Testing**: Uses actual tutorial data and workflow
2. **Maintainability**: Standards auto-generated, not hardcoded
3. **User Alignment**: Tests match user experience
4. **Name Resolution**: Tests name-only standard lookup
5. **Environment Accuracy**: Uses development environment properly

## Future Scenarios

Additional tutorial scenarios can be added following the same pattern:

### Customer Management (Planned)

```python
@pytest.fixture
def customer_scenario(tutorial_project):
    """Customer management scenario (future)."""
    return TutorialScenarios.setup_customer_management(tutorial_project)
```

### Product Catalog (Planned)

```python
@pytest.fixture
def product_scenario(tutorial_project):
    """Product catalog scenario (future)."""
    return TutorialScenarios.setup_product_catalog(tutorial_project)
```

## Troubleshooting

### Standard Not Found

**Problem:** `FileNotFoundError: Standard not found`

**Solution:** Ensure scenario setup completed successfully:

```python
def test_debug(invoice_scenario):
    # Check scenario was set up
    assert invoice_scenario['standard_path'].exists()

    # Verify environment
    import os
    assert os.environ.get('ADRI_ENV') == 'development'
```

### CLI Command Fails

**Problem:** `subprocess.CalledProcessError` during standard generation

**Solution:** Check that ADRI CLI is installed and accessible:

```bash
# Verify CLI is available
which adri

# Test CLI command manually
adri generate-standard --help
```

### Data Files Not Found

**Problem:** Tutorial data files missing

**Solution:** Ensure tutorial data exists in source location:

```bash
# Check tutorial data exists
ls -la ADRI/tutorials/invoice_processing/
# Should show: invoice_data.csv, test_invoice_data.csv
```

## Best Practices

1. **Use Name-Only Resolution**: Always use standard names without paths
2. **Test Both Data Sets**: Use training data (passes) and test data (fails/warns)
3. **Validate Metadata**: Assert scenario paths exist before using them
4. **Check Environment**: Verify development environment is active
5. **Clean Fixtures**: Let pytest handle fixture cleanup automatically

## See Also

- [Tutorial-Based Testing Implementation Plan](../tutorial_based_testing_implementation_plan.md)
- [Modern Fixtures](./modern_fixtures.py)
- [Test Config Template](../test_adri_config.yaml)
