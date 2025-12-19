"""Tutorial-based test scenario management.

This module provides fixtures and utilities for creating test scenarios based on
the actual ADRI tutorial workflow. Tests use tutorial data to seed standard
generation, mirroring how real users would interact with ADRI.

Key Features:
- Tutorial data as foundation (ADRI/tutorials/)
- Full workflow: sample data → CLI generation → standards
- Development environment only (no special test environment)
- Name-only standard resolution for realistic testing

Example Usage:
    def test_invoice_validation(invoice_scenario):
        # invoice_scenario provides:
        # - training_data_path: clean CSV
        # - test_data_path: CSV with issues
        # - generated_standard_name: "invoice_data"
        # - standard_path: ADRI/dev/contracts/invoice_data.yaml

        @adri_protected(contract=invoice_scenario['generated_standard_name'])
        def process_invoices(data):
            return data

        # Test passes with clean data
        clean_data = pd.read_csv(invoice_scenario['training_data_path'])
        result = process_invoices(clean_data)
        assert result is not None
"""

import os
import shutil
import subprocess
import yaml
from pathlib import Path
from typing import Any, Dict, List, Tuple, TypedDict

import pytest

from tests.fixtures.tutorial_discovery import (
    find_tutorial_directories,
    TutorialMetadata
)


# Type Definitions
class TutorialScenario(TypedDict):
    """Tutorial scenario metadata structure.

    Attributes:
        name: Scenario identifier (e.g., "invoice_processing")
        tutorial_dir: Source tutorial directory in ADRI/tutorials/
        training_data_path: Path to clean training CSV
        test_data_path: Path to test CSV with quality issues
        generated_standard_name: Standard name for name-only resolution
        standard_path: Full path to generated standard YAML
        description: Human-readable scenario description
    """
    name: str
    tutorial_dir: Path
    training_data_path: Path
    test_data_path: Path
    generated_standard_name: str
    standard_path: Path
    description: str


class StandardGenConfig(TypedDict):
    """Standard generation configuration.

    Attributes:
        source_data: CSV file to analyze
        output_name: Standard name (no .yaml extension)
        threshold: Overall minimum score
        include_plausibility: Whether to include plausibility rules
    """
    source_data: Path
    output_name: str
    threshold: float
    include_plausibility: bool


class TutorialScenarios:
    """Tutorial-based test scenario management.

    This class provides static methods for setting up test scenarios based on
    ADRI tutorials. Each scenario:
    1. Copies tutorial data to test project
    2. Generates standards using actual ADRI CLI
    3. Returns metadata for test usage
    """

    @staticmethod
    def copy_tutorial_data(
        source_tutorial: str,
        dest_dir: Path
    ) -> Tuple[Path, Path]:
        """Copy existing tutorial CSV files to test location.

        Args:
            source_tutorial: Tutorial name (e.g., "invoice_processing")
            dest_dir: Destination directory for copied files

        Returns:
            Tuple of (training_data_path, test_data_path)

        Raises:
            FileNotFoundError: If tutorial directory doesn't exist
        """
        # Find ADRI project root (this file is in tests/fixtures/)
        current_file = Path(__file__)
        project_root = current_file.parent.parent.parent

        source_dir = project_root / "ADRI" / "tutorials" / source_tutorial

        if not source_dir.exists():
            raise FileNotFoundError(
                f"Tutorial directory not found: {source_dir}"
            )

        # Create destination directory
        dest_dir.mkdir(parents=True, exist_ok=True)

        # Copy training data (clean CSV)
        training_src = source_dir / "invoice_data.csv"
        training_dest = dest_dir / "invoice_data.csv"

        if not training_src.exists():
            raise FileNotFoundError(
                f"Training data not found: {training_src}"
            )

        shutil.copy2(training_src, training_dest)

        # Copy test data (CSV with issues)
        test_src = source_dir / "test_invoice_data.csv"
        test_dest = dest_dir / "test_invoice_data.csv"

        if not test_src.exists():
            raise FileNotFoundError(
                f"Test data not found: {test_src}"
            )

        shutil.copy2(test_src, test_dest)

        return (training_dest, test_dest)

    @staticmethod
    def generate_standard_from_data(
        project_root: Path,
        config: StandardGenConfig
    ) -> str:
        """Generate ADRI standard from sample data using Python API.

        This mimics the real user workflow from tutorials, using the
        ADRI standard generation functionality to create standards from
        training data.

        Args:
            project_root: Test project root directory
            config: Standard generation configuration

        Returns:
            Standard name (for name-only resolution)

        Raises:
            FileNotFoundError: If source data doesn't exist
            Exception: If standard generation fails
        """
        # Ensure source data exists
        if not config['source_data'].exists():
            raise FileNotFoundError(
                f"Source data not found: {config['source_data']}"
            )

        # Import ADRI components
        import pandas as pd
        from src.adri.analysis.contract_generator import ContractGenerator

        # Set environment for development
        os.environ['ADRI_ENV'] = 'development'
        os.environ['ADRI_CONFIG_PATH'] = str(project_root / 'ADRI' / 'config.yaml')

        # Load data
        df = pd.read_csv(config['source_data'])

        # Generate standard using Python API
        generator = ContractGenerator()

        # Build generation config
        generation_config = {
            'overall_minimum': config['threshold'],
            'include_plausibility': config['include_plausibility']
        }

        standard_dict = generator.generate(
            data=df,
            data_name=config['output_name'],
            generation_config=generation_config
        )

        # Ensure output directory exists
        output_dir = project_root / "ADRI" / "dev" / "contracts"
        output_dir.mkdir(parents=True, exist_ok=True)

        # Write standard to file
        standard_path = output_dir / f"{config['output_name']}.yaml"
        with open(standard_path, 'w', encoding='utf-8') as f:
            yaml.dump(standard_dict, f, default_flow_style=False, sort_keys=False)

        return config['output_name']

    @staticmethod
    def setup_invoice_processing(project_root: Path) -> TutorialScenario:
        """Setup invoice processing tutorial scenario.

        Creates complete invoice processing scenario:
        1. Creates tutorial directory structure
        2. Copies training and test data from existing tutorial
        3. Generates standard from training data using ADRI CLI
        4. Returns scenario metadata

        Args:
            project_root: Test project root with ADRI structure

        Returns:
            TutorialScenario with all paths and metadata

        Example:
            scenario = TutorialScenarios.setup_invoice_processing(tmp_path)
            assert scenario['generated_standard_name'] == 'invoice_data'
            assert scenario['standard_path'].exists()
        """
        # Create tutorial directory
        tutorial_dir = project_root / "ADRI" / "tutorials" / "invoice_processing"
        tutorial_dir.mkdir(parents=True, exist_ok=True)

        # Copy tutorial data
        training_data_path, test_data_path = TutorialScenarios.copy_tutorial_data(
            source_tutorial="invoice_processing",
            dest_dir=tutorial_dir
        )

        # Generate standard from training data
        standard_name = "invoice_data"
        gen_config: StandardGenConfig = {
            'source_data': training_data_path,
            'output_name': standard_name,
            'threshold': 75.0,
            'include_plausibility': True
        }

        TutorialScenarios.generate_standard_from_data(
            project_root=project_root,
            config=gen_config
        )

        # Build standard path
        standard_path = project_root / "ADRI" / "dev" / "contracts" / f"{standard_name}.yaml"

        # Return scenario metadata
        scenario: TutorialScenario = {
            'name': 'invoice_processing',
            'tutorial_dir': tutorial_dir,
            'training_data_path': training_data_path,
            'test_data_path': test_data_path,
            'generated_standard_name': standard_name,
            'standard_path': standard_path,
            'description': 'Invoice processing tutorial with data quality validation'
        }

        return scenario

    @staticmethod
    def discover_all_tutorials() -> List[str]:
        """Discover all valid tutorials in ADRI/tutorials/ directory.

        Scans the ADRI/tutorials/ directory for tutorial subdirectories that
        match the required file naming convention. Returns a list of tutorial
        names that can be used for parametrized testing.

        Returns:
            List of tutorial names (use case identifiers) for discovered tutorials.
            Empty list if no tutorials found.

        Example:
            tutorials = TutorialScenarios.discover_all_tutorials()
            # Returns: ['invoice', 'customer_support', ...]

            @pytest.mark.parametrize("tutorial_name", TutorialScenarios.discover_all_tutorials())
            def test_all_tutorials(tutorial_name):
                # Test runs for each discovered tutorial
                pass
        """
        tutorial_metadata_list = find_tutorial_directories()
        return [meta.use_case_name for meta in tutorial_metadata_list]

    @staticmethod
    def setup_tutorial_from_directory(
        tutorial_metadata: TutorialMetadata,
        project_root: Path
    ) -> TutorialScenario:
        """Setup tutorial scenario from discovered tutorial metadata.

        Generic setup function that works for any tutorial following the
        naming convention. Copies data files and generates standard from
        training data.

        Args:
            tutorial_metadata: Metadata from tutorial discovery
            project_root: Test project root with ADRI structure

        Returns:
            TutorialScenario with all paths and metadata

        Example:
            tutorials = find_tutorial_directories()
            for meta in tutorials:
                scenario = TutorialScenarios.setup_tutorial_from_directory(
                    meta, project_root
                )
                assert scenario['training_data_path'].exists()
        """
        # Create tutorial directory in test project
        tutorial_dir = project_root / "ADRI" / "tutorials" / tutorial_metadata.directory_name
        tutorial_dir.mkdir(parents=True, exist_ok=True)

        # Copy training data
        training_dest = tutorial_dir / tutorial_metadata.training_data_path.name
        shutil.copy2(tutorial_metadata.training_data_path, training_dest)

        # Copy test data
        test_dest = tutorial_dir / tutorial_metadata.test_data_path.name
        shutil.copy2(tutorial_metadata.test_data_path, test_dest)

        # Generate standard from training data
        standard_name = f"{tutorial_metadata.use_case_name}_data"
        gen_config: StandardGenConfig = {
            'source_data': training_dest,
            'output_name': standard_name,
            'threshold': 75.0,
            'include_plausibility': True
        }

        TutorialScenarios.generate_standard_from_data(
            project_root=project_root,
            config=gen_config
        )

        # Build standard path
        standard_path = project_root / "ADRI" / "dev" / "contracts" / f"{standard_name}.yaml"

        # Return scenario metadata
        scenario: TutorialScenario = {
            'name': tutorial_metadata.directory_name,
            'tutorial_dir': tutorial_dir,
            'training_data_path': training_dest,
            'test_data_path': test_dest,
            'generated_standard_name': standard_name,
            'standard_path': standard_path,
            'description': f'{tutorial_metadata.use_case_name} tutorial with auto-generated standard'
        }

        return scenario

    @staticmethod
    def setup_autogen_scenario(project_root: Path, clean_existing: bool = True):
        """Setup scenario for testing decorator auto-generation equivalence.

        Creates a test environment where both CLI and decorator generation
        can be tested and compared. Optionally cleans existing standards
        to force regeneration.

        Args:
            project_root: Test project root with ADRI structure
            clean_existing: If True, removes existing standards to force regeneration

        Returns:
            Dict with scenario metadata including paths for both generation methods

        Example:
            scenario = TutorialScenarios.setup_autogen_scenario(tmp_path)
            # Use scenario['training_data_path'] for generation
            # Compare scenario['cli_generated_standard_path'] vs decorator path
        """
        from typing import Dict, Any

        # Create tutorial directory
        tutorial_dir = project_root / "ADRI" / "tutorials" / "invoice_processing"
        tutorial_dir.mkdir(parents=True, exist_ok=True)

        # Copy tutorial data
        training_data_path, test_data_path = TutorialScenarios.copy_tutorial_data(
            source_tutorial="invoice_processing",
            dest_dir=tutorial_dir
        )

        # Setup standard paths
        standard_dir = project_root / "ADRI" / "dev" / "contracts"
        standard_dir.mkdir(parents=True, exist_ok=True)

        cli_standard_name = "autogen_cli_invoice"
        decorator_standard_name = "autogen_decorator_invoice"

        cli_standard_path = standard_dir / f"{cli_standard_name}.yaml"
        decorator_standard_path = standard_dir / f"{decorator_standard_name}.yaml"

        # Clean existing standards if requested
        if clean_existing:
            if cli_standard_path.exists():
                cli_standard_path.unlink()
            if decorator_standard_path.exists():
                decorator_standard_path.unlink()

        # Build scenario metadata
        scenario: Dict[str, Any] = {
            'name': 'decorator_autogen_equivalence',
            'training_data_path': training_data_path,
            'test_data_path': test_data_path,
            'cli_generated_standard_path': cli_standard_path,
            'decorator_generated_standard_path': decorator_standard_path,
            'standard_name': cli_standard_name,
            'expected_fields': [
                'Invoice Number', 'Invoice Date', 'Customer Name',
                'Total Amount', 'Tax Amount', 'Payment Status'
            ]
        }

        return scenario


# Pytest Fixtures

@pytest.fixture
def tutorial_project(tmp_path: Path) -> Path:
    """Test project with tutorial structure using development environment.

    Setup:
    1. Copies test_adri_config.yaml to ADRI/config.yaml
    2. Creates ADRI/dev/ and ADRI/prod/ directory structure
    3. Creates ADRI/tutorials/ directory
    4. Sets environment variables for development mode

    Args:
        tmp_path: Pytest temporary directory

    Returns:
        Project root path with complete ADRI structure

    Example:
        def test_something(tutorial_project):
            config = tutorial_project / "ADRI" / "config.yaml"
            assert config.exists()

            standards_dir = tutorial_project / "ADRI" / "dev" / "standards"
            assert standards_dir.exists()
    """
    # Find test config template
    current_file = Path(__file__)
    tests_dir = current_file.parent.parent
    config_template = tests_dir / "test_adri_config.yaml"

    if not config_template.exists():
        raise FileNotFoundError(
            f"Test config template not found: {config_template}"
        )

    # Copy config to ADRI directory
    project_root = tmp_path / "test_project"
    project_root.mkdir(parents=True, exist_ok=True)

    # Create ADRI directory first
    adri_dir = project_root / "ADRI"
    adri_dir.mkdir(parents=True, exist_ok=True)

    config_dest = adri_dir / "config.yaml"
    shutil.copy2(config_template, config_dest)

    # Create ADRI directory structure
    adri_root = project_root / "ADRI"

    # Development environment directories
    (adri_root / "dev" / "contracts").mkdir(parents=True, exist_ok=True)
    (adri_root / "dev" / "assessments").mkdir(parents=True, exist_ok=True)
    (adri_root / "dev" / "training-data").mkdir(parents=True, exist_ok=True)

    # Production environment directories
    (adri_root / "prod" / "contracts").mkdir(parents=True, exist_ok=True)
    (adri_root / "prod" / "assessments").mkdir(parents=True, exist_ok=True)
    (adri_root / "prod" / "training-data").mkdir(parents=True, exist_ok=True)

    # Tutorials directory
    (adri_root / "tutorials").mkdir(parents=True, exist_ok=True)

    # Set environment variables
    os.environ['ADRI_ENV'] = 'development'
    os.environ['ADRI_CONFIG_PATH'] = str(config_dest)

    return project_root


@pytest.fixture
def invoice_scenario(tutorial_project: Path) -> TutorialScenario:
    """Invoice processing scenario with generated standard.

    Uses:
    - Existing ADRI/tutorials/invoice_processing/ data
    - ADRI CLI to generate standard (real workflow!)
    - Development environment paths

    Args:
        tutorial_project: Project root from tutorial_project fixture

    Returns:
        Complete scenario metadata including paths and standard name

    Example:
        def test_invoice_validation(invoice_scenario):
            # Use generated standard by name
            @adri_protected(contract=invoice_scenario['generated_standard_name'])
            def validate_data(df):
                return df

            # Load clean training data
            data = pd.read_csv(invoice_scenario['training_data_path'])
            result = validate_data(data)
            assert result is not None
    """
    return TutorialScenarios.setup_invoice_processing(tutorial_project)


# Standard Templates (for backward compatibility)

class StandardTemplates:
    """Pre-built standard templates from tutorial examples.

    Provides access to generated standards as dictionaries for tests that
    need to inspect standard content directly.
    """

    @staticmethod
    def from_tutorial(tutorial_name: str, project_root: Path) -> Dict[str, Any]:
        """Load standard template from tutorial scenario.

        Args:
            tutorial_name: Name of tutorial (e.g., "invoice_processing")
            project_root: Project root path

        Returns:
            Standard content as dictionary

        Raises:
            FileNotFoundError: If standard file doesn't exist
        """
        if tutorial_name == "invoice_processing":
            standard_path = project_root / "ADRI" / "dev" / "contracts" / "invoice_data.yaml"
        else:
            raise ValueError(f"Unknown tutorial: {tutorial_name}")

        if not standard_path.exists():
            raise FileNotFoundError(
                f"Standard not found: {standard_path}. "
                "Ensure scenario setup has completed."
            )

        with open(standard_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    @staticmethod
    def invoice_processing_standard(project_root: Path) -> Dict[str, Any]:
        """Load invoice processing standard template.

        Args:
            project_root: Project root path

        Returns:
            Invoice processing standard as dictionary
        """
        return StandardTemplates.from_tutorial("invoice_processing", project_root)
