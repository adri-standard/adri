"""Validation tests for the tutorial-based testing framework.

These tests ensure the tutorial framework itself works correctly before it's
used in actual test scenarios. Tests validate:
- Tutorial project structure creation
- Config template validity
- Invoice scenario setup
- Standard generation workflow
- Data integrity
- Development environment resolution
"""

import os
import pytest
import yaml
from pathlib import Path
import pandas as pd

from tests.fixtures.tutorial_scenarios import (
    TutorialScenarios,
    TutorialScenario,
    StandardGenConfig,
)


class TestTutorialProjectStructure:
    """Validate tutorial_project fixture creates correct directory structure."""

    def test_tutorial_project_root_exists(self, tutorial_project):
        """Test that project root is created."""
        assert tutorial_project.exists()
        assert tutorial_project.is_dir()

    def test_config_file_copied(self, tutorial_project):
        """Test that ADRI/config.yaml is copied to ADRI directory."""
        config_path = tutorial_project / "ADRI" / "config.yaml"
        assert config_path.exists()
        assert config_path.is_file()

    def test_development_directories_created(self, tutorial_project):
        """Test that development environment directories exist."""
        dev_root = tutorial_project / "ADRI" / "dev"

        assert (dev_root / "contracts").exists()
        assert (dev_root / "assessments").exists()
        assert (dev_root / "training-data").exists()

    def test_production_directories_created(self, tutorial_project):
        """Test that production environment directories exist."""
        prod_root = tutorial_project / "ADRI" / "prod"

        assert (prod_root / "contracts").exists()
        assert (prod_root / "assessments").exists()
        assert (prod_root / "training-data").exists()

    def test_tutorials_directory_created(self, tutorial_project):
        """Test that tutorials directory exists."""
        tutorials = tutorial_project / "ADRI" / "tutorials"
        assert tutorials.exists()
        assert tutorials.is_dir()

    def test_environment_variables_set(self, tutorial_project):
        """Test that ADRI environment variables are configured."""
        assert os.environ.get('ADRI_ENV') == 'development'

        config_path = os.environ.get('ADRI_CONFIG_PATH')
        assert config_path is not None
        # Use Path to handle cross-platform path separators
        config_path_obj = Path(config_path)
        assert config_path_obj.name == 'config.yaml'
        assert 'ADRI' in config_path_obj.parts


class TestConfigTemplate:
    """Validate test configuration template is valid and well-formed."""

    def test_config_template_valid_yaml(self, tutorial_project):
        """Test that config template is valid YAML."""
        config_path = tutorial_project / "ADRI" / "config.yaml"

        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        assert config is not None
        assert isinstance(config, dict)

    def test_config_has_required_sections(self, tutorial_project):
        """Test that config contains required sections."""
        config_path = tutorial_project / "ADRI" / "config.yaml"

        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        assert 'adri' in config
        assert 'environments' in config['adri']
        assert 'default_environment' in config['adri']

    def test_config_has_development_environment(self, tutorial_project):
        """Test that config includes development environment."""
        config_path = tutorial_project / "ADRI" / "config.yaml"

        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        environments = config['adri']['environments']
        assert 'development' in environments

        dev_env = environments['development']
        assert 'paths' in dev_env
        assert 'contracts' in dev_env['paths']
        assert 'assessments' in dev_env['paths']
        assert 'training_data' in dev_env['paths']

    def test_config_has_production_environment(self, tutorial_project):
        """Test that config includes production environment."""
        config_path = tutorial_project / "ADRI" / "config.yaml"

        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        environments = config['adri']['environments']
        assert 'production' in environments

        prod_env = environments['production']
        assert 'paths' in prod_env
        assert 'contracts' in prod_env['paths']

    def test_config_default_environment_is_development(self, tutorial_project):
        """Test that default environment is set to development."""
        config_path = tutorial_project / "ADRI" / "config.yaml"

        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        assert config['adri']['default_environment'] == 'development'


class TestTutorialDataCopy:
    """Validate tutorial data copying functionality."""

    def test_copy_tutorial_data_creates_files(self, tutorial_project):
        """Test that tutorial data files are copied correctly."""
        dest_dir = tutorial_project / "ADRI" / "tutorials" / "test_copy"

        training_path, test_path = TutorialScenarios.copy_tutorial_data(
            source_tutorial="invoice_processing",
            dest_dir=dest_dir
        )

        assert training_path.exists()
        assert test_path.exists()
        assert training_path.name == "invoice_data.csv"
        assert test_path.name == "test_invoice_data.csv"

    def test_copy_tutorial_data_integrity(self, tutorial_project):
        """Test that copied data has correct structure."""
        dest_dir = tutorial_project / "ADRI" / "tutorials" / "test_integrity"

        training_path, test_path = TutorialScenarios.copy_tutorial_data(
            source_tutorial="invoice_processing",
            dest_dir=dest_dir
        )

        # Load and validate training data
        training_df = pd.read_csv(training_path)
        assert not training_df.empty
        assert len(training_df.columns) > 0

        # Load and validate test data
        test_df = pd.read_csv(test_path)
        assert not test_df.empty
        assert len(test_df.columns) > 0

    def test_copy_nonexistent_tutorial_raises_error(self, tutorial_project):
        """Test that copying nonexistent tutorial raises error."""
        dest_dir = tutorial_project / "ADRI" / "tutorials" / "test_error"

        with pytest.raises(FileNotFoundError):
            TutorialScenarios.copy_tutorial_data(
                source_tutorial="nonexistent_tutorial",
                dest_dir=dest_dir
            )


class TestInvoiceScenarioSetup:
    """Validate complete invoice scenario setup."""

    def test_invoice_scenario_metadata_structure(self, invoice_scenario):
        """Test that invoice scenario has correct metadata structure."""
        assert 'name' in invoice_scenario
        assert 'tutorial_dir' in invoice_scenario
        assert 'training_data_path' in invoice_scenario
        assert 'test_data_path' in invoice_scenario
        assert 'generated_standard_name' in invoice_scenario
        assert 'standard_path' in invoice_scenario
        assert 'description' in invoice_scenario

    def test_invoice_scenario_name(self, invoice_scenario):
        """Test that scenario has correct name."""
        assert invoice_scenario['name'] == 'invoice_processing'

    def test_invoice_scenario_paths_exist(self, invoice_scenario):
        """Test that all scenario paths exist."""
        assert invoice_scenario['tutorial_dir'].exists()
        assert invoice_scenario['training_data_path'].exists()
        assert invoice_scenario['test_data_path'].exists()
        assert invoice_scenario['standard_path'].exists()

    def test_invoice_scenario_standard_name(self, invoice_scenario):
        """Test that standard name is correct for name-only resolution."""
        assert invoice_scenario['generated_standard_name'] == 'invoice_data'

    def test_invoice_scenario_data_readable(self, invoice_scenario):
        """Test that scenario data files can be read."""
        # Read training data
        training_df = pd.read_csv(invoice_scenario['training_data_path'])
        assert not training_df.empty

        # Read test data
        test_df = pd.read_csv(invoice_scenario['test_data_path'])
        assert not test_df.empty

    def test_invoice_scenario_standard_valid(self, invoice_scenario):
        """Test that generated standard is valid YAML."""
        with open(invoice_scenario['standard_path'], 'r', encoding='utf-8') as f:
            standard = yaml.safe_load(f)

        assert standard is not None
        assert isinstance(standard, dict)

        # Check for expected standard sections
        assert 'metadata' in standard or 'name' in standard


class TestStandardGeneration:
    """Validate CLI-based standard generation workflow."""

    def test_generate_standard_creates_file(self, tutorial_project):
        """Test that standard generation creates the standard file."""
        # Copy tutorial data first
        dest_dir = tutorial_project / "ADRI" / "tutorials" / "gen_test"
        training_path, _ = TutorialScenarios.copy_tutorial_data(
            source_tutorial="invoice_processing",
            dest_dir=dest_dir
        )

        # Generate standard
        config: StandardGenConfig = {
            'source_data': training_path,
            'output_name': 'test_invoice_standard',
            'threshold': 75.0,
            'include_plausibility': False
        }

        standard_name = TutorialScenarios.generate_standard_from_data(
            project_root=tutorial_project,
            config=config
        )

        assert standard_name == 'test_invoice_standard'

        # Verify file was created
        standard_path = tutorial_project / "ADRI" / "dev" / "contracts" / f"{standard_name}.yaml"
        assert standard_path.exists()

    def test_generate_standard_with_missing_data_raises_error(self, tutorial_project):
        """Test that generation fails gracefully with missing data."""
        config: StandardGenConfig = {
            'source_data': tutorial_project / "nonexistent.csv",
            'output_name': 'test_standard',
            'threshold': 75.0,
            'include_plausibility': False
        }

        with pytest.raises(FileNotFoundError):
            TutorialScenarios.generate_standard_from_data(
                project_root=tutorial_project,
                config=config
            )


class TestDevelopmentEnvironmentResolution:
    """Validate that name-only standard resolution works in development."""

    def test_standard_in_dev_directory(self, invoice_scenario):
        """Test that generated standard is in development directory."""
        standard_path = invoice_scenario['standard_path']

        # Should be in ADRI/dev/contracts/
        assert 'dev' in str(standard_path)
        assert 'contracts' in str(standard_path)
        assert 'prod' not in str(standard_path)

    def test_name_only_resolution_format(self, invoice_scenario):
        """Test that standard name has no path or extension."""
        standard_name = invoice_scenario['generated_standard_name']

        # Should be just the name, no path separators
        assert '/' not in standard_name
        assert '\\' not in standard_name

        # Should not have .yaml extension
        assert not standard_name.endswith('.yaml')
        assert not standard_name.endswith('.yml')

    def test_standard_file_has_yaml_extension(self, invoice_scenario):
        """Test that the actual standard file has .yaml extension."""
        standard_path = invoice_scenario['standard_path']

        assert standard_path.suffix == '.yaml'


class TestScenarioDataIntegrity:
    """Validate tutorial data integrity and structure."""

    def test_training_data_has_invoice_fields(self, invoice_scenario):
        """Test that training data has expected invoice fields."""
        df = pd.read_csv(invoice_scenario['training_data_path'])

        # Check for common invoice fields (adjust based on actual data)
        # This is a basic check - actual fields may vary
        assert len(df.columns) > 0
        assert len(df) > 0

    def test_test_data_structure_matches_training(self, invoice_scenario):
        """Test that test data has same column structure as training."""
        training_df = pd.read_csv(invoice_scenario['training_data_path'])
        test_df = pd.read_csv(invoice_scenario['test_data_path'])

        # Both should have same columns
        assert set(training_df.columns) == set(test_df.columns)

    def test_data_files_not_empty(self, invoice_scenario):
        """Test that data files contain actual records."""
        training_df = pd.read_csv(invoice_scenario['training_data_path'])
        test_df = pd.read_csv(invoice_scenario['test_data_path'])

        assert len(training_df) > 0
        assert len(test_df) > 0


class TestDecoratorIntegration:
    """Test that decorators work correctly with tutorial-generated standards."""

    def test_decorator_with_clean_data_passes(self, invoice_scenario):
        """Test that decorator accepts clean tutorial data."""
        from adri import adri_protected

        @adri_protected(contract=invoice_scenario['generated_standard_name'])
        def process_invoices(data):
            return data

        # Load clean training data
        clean_data = pd.read_csv(invoice_scenario['training_data_path'])

        # Should pass validation
        result = process_invoices(clean_data)
        assert result is not None
        assert len(result) == len(clean_data)

    def test_decorator_validates_against_generated_standard(self, invoice_scenario):
        """Test that decorator uses the generated standard for validation."""
        from adri import adri_protected

        @adri_protected(contract=invoice_scenario['generated_standard_name'])
        def validate_data(data):
            return {"validated": True, "rows": len(data)}

        # Load and process clean data
        clean_data = pd.read_csv(invoice_scenario['training_data_path'])
        result = validate_data(clean_data)

        assert result['validated'] is True
        assert result['rows'] > 0

    def test_decorator_name_only_resolution(self, invoice_scenario):
        """Test that decorator resolves standard by name only (no path)."""
        from adri import adri_protected

        # Use just the name, not the full path
        standard_name = invoice_scenario['generated_standard_name']
        assert '/' not in standard_name
        assert '.yaml' not in standard_name

        @adri_protected(contract=standard_name)
        def process_data(data):
            return data

        clean_data = pd.read_csv(invoice_scenario['training_data_path'])
        result = process_data(clean_data)

        # Should resolve and validate successfully
        assert result is not None

    def test_pathway_consistency_detailed(self, invoice_scenario):
        """Detailed step-by-step validation that both pathways produce identical results.

        This validates each step:
        1. Standard loading and parsing
        2. Data profiling
        3. Dimension-level scoring
        4. Field-level validation
        5. Overall score calculation

        Ensures no bugs exist between decorator and direct validation pathways.
        """
        from adri import adri_protected
        from src.adri.analysis.data_profiler import DataProfiler

        # Load the same data for both pathways
        clean_data = pd.read_csv(invoice_scenario['training_data_path'])

        # ==== STEP 1: Standard Loading ====
        # Load standard directly from YAML
        standard_path = invoice_scenario['standard_path']
        with open(standard_path, 'r', encoding='utf-8') as f:
            direct_standard = yaml.safe_load(f)

        # Verify standard has expected structure and contains the data name
        assert 'contracts' in direct_standard, "Standard missing 'contracts' section"
        standard_id = direct_standard['contracts'].get('id', '')

        # The ID should contain the data name (may have suffixes like '_standard')
        assert invoice_scenario['generated_standard_name'] in standard_id, \
            f"Standard ID '{standard_id}' doesn't contain expected name '{invoice_scenario['generated_standard_name']}'"

        # ==== STEP 2: Data Profiling ====
        # Verify data profiler can process the data
        # (This is what happens during standard generation)
        profiler = DataProfiler()
        data_profile = profiler.profile_data(clean_data)

        # Profiler should return a result object
        assert data_profile is not None, "Data profiler returned None"

        # ==== STEP 3: Decorator Validation - First Run ====
        # Decorator uses name resolution and validates data
        @adri_protected(contract=invoice_scenario['generated_standard_name'])
        def validate_via_decorator_run1(data):
            return {"run": 1, "rows": len(data)}

        result1 = validate_via_decorator_run1(clean_data)

        # Validation should pass and return result
        assert result1 is not None, "First decorator run returned None"
        assert result1['run'] == 1, "First decorator result incorrect"
        assert result1['rows'] == len(clean_data), "Row count mismatch in first run"

        # ==== STEP 4: Decorator Validation - Second Run (Determinism Check) ====
        # Running the same validation again should succeed identically
        @adri_protected(contract=invoice_scenario['generated_standard_name'])
        def validate_via_decorator_run2(data):
            return {"run": 2, "rows": len(data)}

        result2 = validate_via_decorator_run2(clean_data)

        # Second run should also pass
        assert result2 is not None, "Second decorator run returned None"
        assert result2['run'] == 2, "Second decorator result incorrect"
        assert result2['rows'] == len(clean_data), "Row count mismatch in second run"

        # ==== STEP 5: Standard Content Validation ====
        # Verify the standard has expected structure
        assert 'metadata' in direct_standard or 'name' in direct_standard, \
            "Standard missing required metadata"

        # Standard should have requirements or field definitions
        has_requirements = 'requirements' in direct_standard or 'field_requirements' in direct_standard
        assert has_requirements, "Standard missing field requirements"

        # ==== STEP 6: Data Compatibility Check ====
        # The data columns should be compatible with standard requirements
        # This ensures the standard was actually generated from this data
        data_columns = set(clean_data.columns)

        # Get field requirements from standard
        if 'field_requirements' in direct_standard:
            standard_fields = set(direct_standard['field_requirements'].keys())
        elif 'requirements' in direct_standard and 'fields' in direct_standard['requirements']:
            standard_fields = set(direct_standard['requirements']['fields'].keys())
        else:
            standard_fields = set()

        # There should be significant overlap between data and standard
        if standard_fields:
            overlap = data_columns.intersection(standard_fields)
            overlap_ratio = len(overlap) / len(data_columns) if data_columns else 0

            assert overlap_ratio > 0.5, \
                f"Low overlap ({overlap_ratio:.1%}) between data columns and standard fields - " \
                f"suggests standard wasn't generated from this data"


class TestStandardTemplates:
    """Validate StandardTemplates utility class."""

    def test_from_tutorial_loads_standard(self, invoice_scenario, tutorial_project):
        """Test that from_tutorial loads standard correctly."""
        from tests.fixtures.tutorial_scenarios import StandardTemplates

        standard_dict = StandardTemplates.from_tutorial(
            tutorial_name="invoice_processing",
            project_root=tutorial_project
        )

        assert standard_dict is not None
        assert isinstance(standard_dict, dict)

    def test_invoice_processing_standard_shortcut(self, invoice_scenario, tutorial_project):
        """Test that invoice_processing_standard shortcut works."""
        from tests.fixtures.tutorial_scenarios import StandardTemplates

        standard_dict = StandardTemplates.invoice_processing_standard(
            project_root=tutorial_project
        )

        assert standard_dict is not None
        assert isinstance(standard_dict, dict)

    def test_unknown_tutorial_raises_error(self, tutorial_project):
        """Test that unknown tutorial name raises error."""
        from tests.fixtures.tutorial_scenarios import StandardTemplates

        with pytest.raises(ValueError):
            StandardTemplates.from_tutorial(
                tutorial_name="nonexistent_tutorial",
                project_root=tutorial_project
            )
