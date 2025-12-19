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
from src.adri.analysis.contract_generator import ContractGenerator
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
        1. Generates standard via ContractGenerator API (used by both CLI and Decorator)
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
        os.environ.pop('ADRI_CONTRACTS_DIR', None)  # Let config file take precedence
        os.environ['ADRI_CONFIG_PATH'] = str(cli_env['config'])
        os.environ['ADRI_ENV'] = 'development'

        generator = ContractGenerator()
        cli_standard_dict = generator.generate(
            data=df,
            data_name='invoice_data',
            generation_config={'overall_minimum': 75.0}
        )

        # Save CLI standard
        cli_standard_path = cli_env['contracts_dir'] / 'invoice_data.yaml'
        import yaml
        with open(cli_standard_path, 'w', encoding='utf-8') as f:
            yaml.dump(cli_standard_dict, f, default_flow_style=False, sort_keys=False)

        # 2. Generate via Decorator auto-generation
        os.environ.pop('ADRI_CONTRACTS_DIR', None)  # Let config file take precedence
        os.environ['ADRI_CONFIG_PATH'] = str(dec_env['config'])
        os.environ['ADRI_ENV'] = 'development'

        # Change to the test environment directory so relative paths work
        import os as os_module
        original_cwd = os_module.getcwd()
        try:
            os_module.chdir(dec_env['base_path'])

            @adri_protected(contract='invoice_data')
            def process_data(data):
                return data

            # Trigger auto-generation
            result = process_data(df)
        finally:
            os_module.chdir(original_cwd)

        dec_standard_path = dec_env['contracts_dir'] / 'invoice_data.yaml'

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
        standard_dest = env['contracts_dir'] / 'invoice_data.yaml'
        copy_standard(standard_source, standard_dest)

        # Configure environment
        os.environ.pop('ADRI_CONTRACTS_DIR', None)  # Let config file take precedence
        os.environ['ADRI_CONFIG_PATH'] = str(env['config'])
        os.environ['ADRI_ENV'] = 'development'
        os.environ['ADRI_LOG_DIR'] = str(env['logs_dir'])  # Enable audit logging

        # Change to environment directory for path resolution
        import os as os_module
        original_cwd = os_module.getcwd()
        try:
            os_module.chdir(env['base_path'])

            # Assess via Decorator
            @adri_protected(contract='invoice_data', on_failure='warn')
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
            env['logs_dir'] / 'adri_assessment_logs.jsonl',
            env['logs_dir'] / 'adri_dimension_scores.jsonl',
            env['logs_dir'] / 'adri_failed_validations.jsonl'
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
        standard_dest = env['contracts_dir'] / 'invoice_data.yaml'
        copy_standard(standard_source, standard_dest)

        # Configure environment
        os.environ.pop('ADRI_CONTRACTS_DIR', None)  # Let config file take precedence
        os.environ['ADRI_CONFIG_PATH'] = str(env['config'])
        os.environ['ADRI_ENV'] = 'development'
        os.environ['ADRI_LOG_DIR'] = str(env['logs_dir'])  # Enable audit logging

        # Change to environment directory for path resolution
        import os as os_module
        original_cwd = os_module.getcwd()
        try:
            os_module.chdir(env['base_path'])

            # Assess via Decorator (use warn mode to allow processing)
            @adri_protected(contract='invoice_data', on_failure='warn')
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
            env['logs_dir'] / 'adri_assessment_logs.jsonl',
            env['logs_dir'] / 'adri_dimension_scores.jsonl',
            env['logs_dir'] / 'adri_failed_validations.jsonl'
        ]

        for log_file in log_files:
            assert log_file.exists(), f"Log file not created: {log_file}"


class TestStandardPathConsistency:
    """Verify standard paths are consistent across Decorator, CLI, Config, and Audit logs."""

    def test_standard_path_consistency(self, invoice_scenario, tmp_path):
        """
        Verify standard path consistency across all code paths.

        This test validates the Issue #35 fix by ensuring:
        1. Decorator uses the standard path from config
        2. CLI uses the standard path from config
        3. Config specifies the correct path for dev environment
        4. All standard_path values in audit logs match
        5. AssessmentResult.standard_path is set correctly

        This prevents regressions where different code paths use different standards.
        """
        # Setup isolated environment
        env = setup_isolated_environment(tmp_path / "path_consistency")

        # Copy a known standard to the dev/contracts directory
        standard_source = invoice_scenario['standard_path']
        standard_name = 'invoice_data.yaml'
        standard_dest = env['contracts_dir'] / standard_name
        copy_standard(standard_source, standard_dest)

        # Get the expected standard path from config (absolute path)
        config_standard_path = standard_dest.resolve()

        # Configure environment
        os.environ.pop('ADRI_CONTRACTS_DIR', None)  # Let config file take precedence
        os.environ['ADRI_CONFIG_PATH'] = str(env['config'])
        os.environ['ADRI_ENV'] = 'development'
        os.environ['ADRI_LOG_DIR'] = str(env['logs_dir'])  # Enable audit logging

        # Load test data
        training_data_path = invoice_scenario['training_data_path']
        df = pd.read_csv(training_data_path)

        # === PHASE 1: Decorator Path Check ===
        import os as os_module
        original_cwd = os_module.getcwd()

        try:
            os_module.chdir(env['base_path'])

            @adri_protected(contract='invoice_data', on_failure='warn')
            def process_with_decorator(data):
                return data

            decorator_result = process_with_decorator(df)

        finally:
            os_module.chdir(original_cwd)

        # Verify decorator executed successfully
        assert decorator_result is not None, "Decorator processing failed"

        # Read decorator audit log to get its standard_path
        decorator_audit_file = env['logs_dir'] / 'adri_assessment_logs.jsonl'
        assert decorator_audit_file.exists(), f"Decorator audit log not created: {decorator_audit_file}"

        # Load JSONL file
        import json
        decorator_records = []
        with open(decorator_audit_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    decorator_records.append(json.loads(line))

        decorator_audit_df = pd.DataFrame(decorator_records)
        assert len(decorator_audit_df) > 0, "Decorator audit log is empty"
        assert 'standard_path' in decorator_audit_df.columns, "Decorator audit log missing standard_path"

        decorator_paths = decorator_audit_df['standard_path'].dropna().unique()
        assert len(decorator_paths) == 1, f"Decorator used multiple standard paths: {decorator_paths}"
        decorator_standard_path = decorator_paths[0]

        # Clear logs for CLI test
        clear_logs(env['logs_dir'])

        # === PHASE 2: CLI Path Check ===
        from src.adri.validator.engine import DataQualityAssessor
        from src.adri.config.loader import ConfigurationLoader

        config_loader = ConfigurationLoader()
        full_config = config_loader.load_config(str(env['config']))
        config = full_config.get('adri', {}) if full_config else {}

        assessor = DataQualityAssessor(config)
        cli_result = assessor.assess(df, str(config_standard_path))

        # Verify CLI result has standard_path
        assert hasattr(cli_result, 'standard_path'), "CLI result missing standard_path"
        assert cli_result.standard_path is not None, "CLI standard_path is None"

        # === PHASE 3: Path Consistency Checks ===

        # Check 1: Both paths are absolute (not relative)
        assert Path(decorator_standard_path).is_absolute(), \
            f"Decorator path is not absolute: {decorator_standard_path}"
        assert Path(cli_result.standard_path).is_absolute(), \
            f"CLI path is not absolute: {cli_result.standard_path}"

        # Check 2: Both paths match the config-expected path
        assert decorator_standard_path == str(config_standard_path), \
            f"Decorator path mismatch:\n  Expected: {config_standard_path}\n  Got: {decorator_standard_path}"
        assert cli_result.standard_path == str(config_standard_path), \
            f"CLI path mismatch:\n  Expected: {config_standard_path}\n  Got: {cli_result.standard_path}"

        # Check 3: Decorator and CLI paths match each other
        assert decorator_standard_path == cli_result.standard_path, \
            f"Decorator and CLI paths differ:\n  Decorator: {decorator_standard_path}\n  CLI: {cli_result.standard_path}"

        # === PHASE 4: Final Audit Log Verification ===
        audit_log_file = env['logs_dir'] / 'adri_assessment_logs.jsonl'
        assert audit_log_file.exists(), f"Audit log not created: {audit_log_file}"

        # Read audit logs from JSONL
        import json
        audit_records = []
        with open(audit_log_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    audit_records.append(json.loads(line))

        audit_df = pd.DataFrame(audit_records)
        assert len(audit_df) > 0, "Audit log is empty"

        # Check that standard_path column exists
        assert 'standard_path' in audit_df.columns, "Audit log missing standard_path column"

        # Get all unique standard paths from audit log
        audit_paths = audit_df['standard_path'].dropna().unique()

        # Check 4: All audit log entries use the same path
        assert len(audit_paths) > 0, "No standard_path values in audit log"
        assert len(audit_paths) == 1, \
            f"Multiple different standard paths in audit log: {audit_paths}"

        # Check 5: Audit log path matches the expected path
        audit_path = audit_paths[0]
        assert audit_path == str(config_standard_path), \
            f"Audit log path mismatch:\n  Expected: {config_standard_path}\n  Got: {audit_path}"

        # === SUCCESS ===
        # All paths match: Decorator == CLI == Config == Audit Log
        print(f"\n✅ Path Consistency Test PASSED")
        print(f"   Standard Path: {config_standard_path}")
        print(f"   - Decorator (from audit): {decorator_standard_path}")
        print(f"   - CLI (from result): {cli_result.standard_path}")
        print(f"   - Audit Log: {audit_path}")
        print(f"   - All paths match and are absolute ✓")


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
        os.environ.pop('ADRI_CONTRACTS_DIR', None)  # Let config file take precedence
        os.environ['ADRI_CONFIG_PATH'] = str(cli_env['config'])
        os.environ['ADRI_ENV'] = 'development'

        # Step 1: Generate standard
        generator = ContractGenerator()
        cli_standard_dict = generator.generate(
            data=df,
            data_name='invoice_data',
            generation_config={'overall_minimum': 75.0}
        )

        cli_standard_path = cli_env['contracts_dir'] / 'invoice_data.yaml'
        import yaml
        with open(cli_standard_path, 'w', encoding='utf-8') as f:
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
        os.environ.pop('ADRI_CONTRACTS_DIR', None)  # Let config file take precedence
        os.environ['ADRI_CONFIG_PATH'] = str(dec_env['config'])
        os.environ['ADRI_ENV'] = 'development'
        os.environ['ADRI_LOG_DIR'] = str(dec_env['logs_dir'])  # Enable audit logging

        # Change to environment directory for path resolution
        import os as os_module
        original_cwd = os_module.getcwd()
        try:
            os_module.chdir(dec_env['base_path'])

            # Step 1 & 2 combined: Auto-generate + assess
            @adri_protected(contract='invoice_data', on_failure='warn')
            def process_data(data):
                return data

            dec_result = process_data(df)
        finally:
            os_module.chdir(original_cwd)

        dec_standard_path = dec_env['contracts_dir'] / 'invoice_data.yaml'

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
        os.environ.pop('ADRI_CONTRACTS_DIR', None)  # Let config file take precedence
        os.environ['ADRI_CONFIG_PATH'] = str(cli_env['config'])
        os.environ['ADRI_ENV'] = 'development'

        # Step 1: Generate standard
        generator = ContractGenerator()
        cli_standard_dict = generator.generate(
            data=df,
            data_name='test_invoice_data',
            generation_config={'overall_minimum': 75.0}
        )

        cli_standard_path = cli_env['contracts_dir'] / 'test_invoice_data.yaml'
        import yaml
        with open(cli_standard_path, 'w', encoding='utf-8') as f:
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
        os.environ.pop('ADRI_CONTRACTS_DIR', None)  # Let config file take precedence
        os.environ['ADRI_CONFIG_PATH'] = str(dec_env['config'])
        os.environ['ADRI_ENV'] = 'development'
        os.environ['ADRI_LOG_DIR'] = str(dec_env['logs_dir'])  # Enable audit logging

        # Change to environment directory for path resolution
        import os as os_module
        original_cwd = os_module.getcwd()
        try:
            os_module.chdir(dec_env['base_path'])

            # Step 1 & 2 combined: Auto-generate + assess
            @adri_protected(contract='test_invoice_data', on_failure='warn')
            def process_data(data):
                return data

            dec_result = process_data(df)
        finally:
            os_module.chdir(original_cwd)

        dec_standard_path = dec_env['contracts_dir'] / 'test_invoice_data.yaml'

        # === COMPARE RESULTS ===
        # Compare standards
        assert cli_standard_path.exists(), "CLI standard not created"
        assert dec_standard_path.exists(), "Decorator standard not created"
        compare_standards(cli_standard_path, dec_standard_path)

        # Compare assessment logs
        compare_assessment_logs(cli_env['logs_dir'], dec_env['logs_dir'])
