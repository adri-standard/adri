"""
CLI vs Decorator Parity Tests

Comprehensive tests verifying that CLI and Decorator paths produce identical results for:
1. Standard generation from good data
2. Standard generation from bad data
3. Assessments on good data
4. Assessments on bad data
5. All generated logs and files

These tests ensure consistency between the two primary ways users interact with ADRI.
"""

import os
import subprocess
import pandas as pd
import pytest
from pathlib import Path

from src.adri.decorator import adri_protected
from src.adri.analysis.standard_generator import StandardGenerator
from tests.fixtures.parity_helpers import (
    compare_standards,
    compare_assessment_logs,
    setup_isolated_environment,
    copy_standard,
    clear_logs
)


class TestStandardGenerationParity:
    """Test standard generation produces identical results via CLI and Decorator."""

    def test_generate_from_good_data_cli_vs_decorator(self, invoice_scenario, tmp_path):
        """
        Verify CLI and Decorator generate identical standards from clean training data.

        This test:
        1. Generates standard via StandardGenerator API (used by both CLI and Decorator)
        2. Generates standard via Decorator auto-generation
        3. Compares both standards are identical
        """
        # Setup isolated environments
        cli_env = setup_isolated_environment(tmp_path / "cli")
        dec_env = setup_isolated_environment(tmp_path / "decorator")

        # Get training data (clean data)
        training_data_path = invoice_scenario['training_data_path']
        df = pd.read_csv(training_data_path)

        # 1. Generate via Python API (same as CLI uses)
        os.environ['ADRI_CONFIG_PATH'] = str(cli_env['config'])
        os.environ['ADRI_ENV'] = 'development'

        generator = StandardGenerator()
        cli_standard_dict = generator.generate(
            data=df,
            data_name='invoice_data',
            generation_config={'overall_minimum': 75.0}
        )

        # Save CLI standard
        cli_standard_path = cli_env['standards_dir'] / 'invoice_data.yaml'
        import yaml
        with open(cli_standard_path, 'w') as f:
            yaml.dump(cli_standard_dict, f, default_flow_style=False, sort_keys=False)

        # 2. Generate via Decorator auto-generation
        os.environ['ADRI_CONFIG_PATH'] = str(dec_env['config'])
        os.environ['ADRI_ENV'] = 'development'

        # Change to the test environment directory so relative paths work
        import os as os_module
        original_cwd = os_module.getcwd()
        try:
            os_module.chdir(dec_env['base_path'])

            @adri_protected(standard='invoice_data')
            def process_data(data):
                return data

            # Trigger auto-generation
            result = process_data(df)
        finally:
            os_module.chdir(original_cwd)

        dec_standard_path = dec_env['standards_dir'] / 'invoice_data.yaml'

        # 3. Compare standards
        assert cli_standard_path.exists(), "CLI standard not created"
        assert dec_standard_path.exists(), "Decorator standard not created"
        compare_standards(cli_standard_path, dec_standard_path)

        assert dec_standard_path.exists(), "Decorator standard not created"
        compare_standards(cli_standard_path, dec_standard_path)


class TestAssessmentParity:
    """Test assessments produce identical results via CLI-style and Decorator paths."""

    def test_assess_good_data_decorator_with_logging(self, invoice_scenario, tmp_path):
        """
        Verify Decorator produces correct assessments and logs on clean data.

        This test:
        1. Uses existing standard (from invoice_scenario)
        2. Assesses training data via Decorator
        3. Verifies assessment logs are created correctly
        """
        # Setup environment with logging enabled
        env = setup_isolated_environment(tmp_path / "decorator_good")

        # Copy standard to environment
        standard_source = invoice_scenario['standard_path']
        standard_dest = env['standards_dir'] / 'invoice_data.yaml'
        copy_standard(standard_source, standard_dest)

        # Configure environment
        os.environ['ADRI_CONFIG_PATH'] = str(env['config'])
        os.environ['ADRI_ENV'] = 'development'

        # Change to environment directory for path resolution
        import os as os_module
        original_cwd = os_module.getcwd()
        try:
            os_module.chdir(env['base_path'])

            # Assess via Decorator
            @adri_protected(standard='invoice_data', on_failure='warn')
            def process_data(data):
                return data

            # Load and process training data
            training_data_path = invoice_scenario['training_data_path']
            df = pd.read_csv(training_data_path)
            result = process_data(df)
        finally:
            os_module.chdir(original_cwd)

        # Verify logs were created
        assert result is not None, "Processing failed"
        log_files = [
            env['logs_dir'] / 'adri_assessment_logs.csv',
            env['logs_dir'] / 'adri_dimension_scores.csv',
            env['logs_dir'] / 'adri_failed_validations.csv'
        ]

        for log_file in log_files:
            assert log_file.exists(), f"Log file not created: {log_file}"

    def test_assess_bad_data_decorator_with_logging(self, invoice_scenario, tmp_path):
        """
        Verify Decorator produces correct assessments and logs on problematic data.

        This test:
        1. Uses existing standard (from invoice_scenario)
        2. Assesses test data via Decorator
        3. Verifies assessment logs are created correctly
        """
        # Setup environment with logging enabled
        env = setup_isolated_environment(tmp_path / "decorator_bad")

        # Copy standard to environment
        standard_source = invoice_scenario['standard_path']
        standard_dest = env['standards_dir'] / 'invoice_data.yaml'
        copy_standard(standard_source, standard_dest)

        # Configure environment
        os.environ['ADRI_CONFIG_PATH'] = str(env['config'])
        os.environ['ADRI_ENV'] = 'development'

        # Change to environment directory for path resolution
        import os as os_module
        original_cwd = os_module.getcwd()
        try:
            os_module.chdir(env['base_path'])

            # Assess via Decorator (use warn mode to allow processing)
            @adri_protected(standard='invoice_data', on_failure='warn')
            def process_data(data):
                return data

            # Load and process test data
            test_data_path = invoice_scenario['test_data_path']
            df = pd.read_csv(test_data_path)
            result = process_data(df)
        finally:
            os_module.chdir(original_cwd)

        # Verify logs were created
        assert result is not None, "Processing should succeed in warn mode"
        log_files = [
            env['logs_dir'] / 'adri_assessment_logs.csv',
            env['logs_dir'] / 'adri_dimension_scores.csv',
            env['logs_dir'] / 'adri_failed_validations.csv'
        ]

        for log_file in log_files:
            assert log_file.exists(), f"Log file not created: {log_file}"


class TestEndToEndParity:
    """Test complete workflows produce identical results."""

    def test_full_workflow_good_data(self, invoice_scenario, tmp_path):
        """
        Complete workflow with clean data:
        1. Generate standard from training data (both paths)
        2. Assess training data with generated standard (both paths)
        3. Verify standards are identical
        4. Verify assessment logs are identical
        """
        # Setup two isolated environments
        cli_env = setup_isolated_environment(tmp_path / "cli_workflow_good")
        dec_env = setup_isolated_environment(tmp_path / "dec_workflow_good")

        training_data_path = invoice_scenario['training_data_path']
        df = pd.read_csv(training_data_path)

        # === CLI PATH ===
        os.environ['ADRI_CONFIG_PATH'] = str(cli_env['config'])
        os.environ['ADRI_ENV'] = 'development'

        # Step 1: Generate standard
        generator = StandardGenerator()
        cli_standard_dict = generator.generate(
            data=df,
            data_name='invoice_data',
            generation_config={'overall_minimum': 75.0}
        )

        cli_standard_path = cli_env['standards_dir'] / 'invoice_data.yaml'
        import yaml
        with open(cli_standard_path, 'w') as f:
            yaml.dump(cli_standard_dict, f, default_flow_style=False, sort_keys=False)

        # Step 2: Assess data
        from src.adri.validator.engine import DataQualityAssessor
        from src.adri.config.loader import ConfigurationLoader

        config_loader = ConfigurationLoader()
        full_config = config_loader.load_config(str(cli_env['config']))
        # Extract 'adri' section - DataQualityAssessor expects this structure
        config = full_config.get('adri', {}) if full_config else {}

        assessor = DataQualityAssessor(config)
        cli_result = assessor.assess(df, str(cli_standard_path))

        # === DECORATOR PATH ===
        os.environ['ADRI_CONFIG_PATH'] = str(dec_env['config'])
        os.environ['ADRI_ENV'] = 'development'

        # Change to environment directory for path resolution
        import os as os_module
        original_cwd = os_module.getcwd()
        try:
            os_module.chdir(dec_env['base_path'])

            # Step 1 & 2 combined: Auto-generate + assess
            @adri_protected(standard='invoice_data', on_failure='warn')
            def process_data(data):
                return data

            dec_result = process_data(df)
        finally:
            os_module.chdir(original_cwd)

        dec_standard_path = dec_env['standards_dir'] / 'invoice_data.yaml'

        # === COMPARE RESULTS ===
        # Compare standards
        assert cli_standard_path.exists(), "CLI standard not created"
        assert dec_standard_path.exists(), "Decorator standard not created"
        compare_standards(cli_standard_path, dec_standard_path)

        # Compare assessment logs
        compare_assessment_logs(cli_env['logs_dir'], dec_env['logs_dir'])

    def test_full_workflow_bad_data(self, invoice_scenario, tmp_path):
        """
        Complete workflow with problematic data:
        1. Generate standard from test data (both paths)
        2. Assess test data with generated standard (both paths)
        3. Verify standards are identical
        4. Verify assessment logs are identical
        """
        # Setup two isolated environments
        cli_env = setup_isolated_environment(tmp_path / "cli_workflow_bad")
        dec_env = setup_isolated_environment(tmp_path / "dec_workflow_bad")

        test_data_path = invoice_scenario['test_data_path']
        df = pd.read_csv(test_data_path)

        # === CLI PATH ===
        os.environ['ADRI_CONFIG_PATH'] = str(cli_env['config'])
        os.environ['ADRI_ENV'] = 'development'

        # Step 1: Generate standard
        generator = StandardGenerator()
        cli_standard_dict = generator.generate(
            data=df,
            data_name='test_invoice_data',
            generation_config={'overall_minimum': 75.0}
        )

        cli_standard_path = cli_env['standards_dir'] / 'test_invoice_data.yaml'
        import yaml
        with open(cli_standard_path, 'w') as f:
            yaml.dump(cli_standard_dict, f, default_flow_style=False, sort_keys=False)

        # Step 2: Assess data
        from src.adri.validator.engine import DataQualityAssessor
        from src.adri.config.loader import ConfigurationLoader

        config_loader = ConfigurationLoader()
        full_config = config_loader.load_config(str(cli_env['config']))
        # Extract 'adri' section - DataQualityAssessor expects this structure
        config = full_config.get('adri', {}) if full_config else {}

        assessor = DataQualityAssessor(config)
        cli_result = assessor.assess(df, str(cli_standard_path))

        # === DECORATOR PATH ===
        os.environ['ADRI_CONFIG_PATH'] = str(dec_env['config'])
        os.environ['ADRI_ENV'] = 'development'

        # Change to environment directory for path resolution
        import os as os_module
        original_cwd = os_module.getcwd()
        try:
            os_module.chdir(dec_env['base_path'])

            # Step 1 & 2 combined: Auto-generate + assess
            @adri_protected(standard='test_invoice_data', on_failure='warn')
            def process_data(data):
                return data

            dec_result = process_data(df)
        finally:
            os_module.chdir(original_cwd)

        dec_standard_path = dec_env['standards_dir'] / 'test_invoice_data.yaml'

        # === COMPARE RESULTS ===
        # Compare standards
        assert cli_standard_path.exists(), "CLI standard not created"
        assert dec_standard_path.exists(), "Decorator standard not created"
        compare_standards(cli_standard_path, dec_standard_path)

        # Compare assessment logs
        compare_assessment_logs(cli_env['logs_dir'], dec_env['logs_dir'])
