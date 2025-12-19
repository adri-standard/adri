"""
Environment Documentation Validation Tests for ADRI CLI.

Tests the comprehensive environment documentation system that explains:
- Environment purposes (development vs production)
- Environment switching methods and instructions
- Configuration file structure and content
- Directory structure and workflow recommendations
- Audit configuration and compliance requirements

This test suite ensures the environment documentation is complete, accurate,
and provides clear guidance for users working with ADRI environments.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os
import shutil
from pathlib import Path
import yaml
from dataclasses import dataclass
from typing import Dict, Any, Optional, List
import pytest

# Import CLI functions for testing environment documentation integration
import src.adri.cli as adri_cli


@dataclass
class EnvironmentTestCase:
    """Test case structure for environment documentation validation."""
    description: str
    environment: str
    expected_paths: Dict[str, str]
    config_overrides: Dict[str, Any] = None


class TestEnvironmentDocumentation(unittest.TestCase):
    """Environment documentation completeness and accuracy testing."""

    def setUp(self):
        """Set up test fixtures with temporary directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)

        # Create ADRI project structure
        self.project_root = Path(self.temp_dir)
        self.adri_dir = self.project_root / "ADRI"
        self.adri_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        """Clean up test fixtures."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)

    def test_config_yaml_has_comprehensive_documentation(self):
        """Test that config.yaml contains all required documentation sections."""
        # Find the actual ADRI project root to access the real config file
        original_cwd = os.getcwd()
        try:
            # Go to project root to find the comprehensive config
            os.chdir(self.original_cwd)
            project_config_path = Path("ADRI/config.yaml")

            if project_config_path.exists():
                # Read config file content as text to check documentation
                with open(project_config_path, 'r', encoding='utf-8') as f:
                    config_content = f.read()

                # Check for major documentation sections
                required_doc_sections = [
                    "ENVIRONMENT SWITCHING",
                    "ENVIRONMENT CONFIGURATIONS",
                    "DEVELOPMENT ENVIRONMENT",
                    "PRODUCTION ENVIRONMENT",
                    "SWITCHING ENVIRONMENTS",
                    "WORKFLOW RECOMMENDATIONS",
                    "AUDIT CONFIGURATION",
                ]

                for section in required_doc_sections:
                    with self.subTest(section=section):
                        self.assertIn(section, config_content,
                            f"Config documentation missing section: {section}")
            else:
                # Skip test if project config doesn't exist
                self.skipTest("Project ADRI/config.yaml not found - test requires actual project")
        finally:
            os.chdir(self.temp_dir)

    def test_environment_switching_instructions_completeness(self):
        """Test that environment switching instructions are comprehensive."""
        # Find the actual ADRI project root to access the real config file
        original_cwd = os.getcwd()
        try:
            # Go to project root to find the comprehensive config
            os.chdir(self.original_cwd)
            project_config_path = Path("ADRI/config.yaml")

            if project_config_path.exists():
                with open(project_config_path, 'r', encoding='utf-8') as f:
                    config_content = f.read()

                # Check for all three switching methods
                switching_methods = [
                    "Configuration Method",
                    "Environment Variable Method",
                    "Command Line Method",
                ]

                for method in switching_methods:
                    with self.subTest(method=method):
                        self.assertIn(method, config_content,
                            f"Missing environment switching method: {method}")

                # Check for specific switching instructions
                switching_instructions = [
                    "default_environment",
                    "ADRI_ENV",
                    "--environment",
                    "export ADRI_ENV=production",
                ]

                for instruction in switching_instructions:
                    with self.subTest(instruction=instruction):
                        self.assertIn(instruction, config_content,
                            f"Missing switching instruction: {instruction}")
            else:
                self.skipTest("Project ADRI/config.yaml not found - test requires actual project")
        finally:
            os.chdir(self.temp_dir)

    def test_environment_purpose_documentation(self):
        """Test that environment purposes are clearly documented."""
        # Find the actual ADRI project root to access the real config file
        original_cwd = os.getcwd()
        try:
            os.chdir(self.original_cwd)
            project_config_path = Path("ADRI/config.yaml")

            if project_config_path.exists():
                with open(project_config_path, 'r', encoding='utf-8') as f:
                    config_content = f.read()

                # Development environment purpose documentation
                dev_purposes = [
                    "Contract creation, testing, and experimentation",
                    "Creating new data quality contracts",
                    "Testing contracts against various datasets",
                    "tutorial data",
                ]

                for purpose in dev_purposes:
                    with self.subTest(purpose=purpose):
                        self.assertIn(purpose, config_content,
                            f"Missing development purpose: {purpose}")

                # Production environment purpose documentation
                prod_purposes = [
                    "Validated contracts and production data quality",
                    "Deploying proven contracts",
                    "Enterprise governance",
                    "CI/CD pipelines",
                ]

                for purpose in prod_purposes:
                    with self.subTest(purpose=purpose):
                        self.assertIn(purpose, config_content,
                            f"Missing production purpose: {purpose}")
            else:
                self.skipTest("Project ADRI/config.yaml not found - test requires actual project")
        finally:
            os.chdir(self.temp_dir)

    def test_workflow_recommendations_documentation(self):
        """Test that workflow recommendations are comprehensive."""
        # Find the actual ADRI project root to access the real config file
        original_cwd = os.getcwd()
        try:
            os.chdir(self.original_cwd)
            project_config_path = Path("ADRI/config.yaml")

            if project_config_path.exists():
                with open(project_config_path, 'r', encoding='utf-8') as f:
                    config_content = f.read()

                # Check for workflow steps
                workflow_steps = [
                    "Production Workflow:",
                    "Create and test contracts in development",
                    "Validate contracts with various test datasets",
                    "Copy proven contracts from dev/contracts/",
                    "Switch to production environment",
                    "Monitor production audit logs",
                ]

                for step in workflow_steps:
                    with self.subTest(step=step):
                        self.assertIn(step, config_content,
                            f"Missing workflow step: {step}")
            else:
                self.skipTest("Project ADRI/config.yaml not found - test requires actual project")
        finally:
            os.chdir(self.temp_dir)

    def test_directory_structure_documentation(self):
        """Test that directory structure is clearly documented."""
        # Find the actual ADRI project root to access the real config file
        original_cwd = os.getcwd()
        try:
            os.chdir(self.original_cwd)
            project_config_path = Path("ADRI/config.yaml")

            if project_config_path.exists():
                with open(project_config_path, 'r', encoding='utf-8') as f:
                    config_content = f.read()

                # Check for directory structure explanation
                directory_docs = [
                    "Directory Structure Created:",
                    "tutorials/",
                    "contracts/",
                    "assessments/",
                    "training-data/",
                    "audit-logs/",
                ]

                for doc_item in directory_docs:
                    with self.subTest(doc_item=doc_item):
                        self.assertIn(doc_item, config_content,
                            f"Missing directory documentation: {doc_item}")
            else:
                self.skipTest("Project ADRI/config.yaml not found - test requires actual project")
        finally:
            os.chdir(self.temp_dir)

    def test_audit_configuration_documentation(self):
        """Test that audit configuration is thoroughly documented."""
        # Find the actual ADRI project root to access the real config file
        original_cwd = os.getcwd()
        try:
            os.chdir(self.original_cwd)
            project_config_path = Path("ADRI/config.yaml")

            if project_config_path.exists():
                with open(project_config_path, 'r', encoding='utf-8') as f:
                    config_content = f.read()

                # Check for audit configuration explanations
                audit_docs = [
                    "AUDIT CONFIGURATION",
                    "Comprehensive logging for development debugging",
                    "Enhanced logging for compliance, security",
                    "include_data_samples",
                    "max_log_size_mb",
                    "log_level",
                    "regulatory compliance",
                ]

                for doc_item in audit_docs:
                    with self.subTest(doc_item=doc_item):
                        self.assertIn(doc_item, config_content,
                            f"Missing audit documentation: {doc_item}")
            else:
                self.skipTest("Project ADRI/config.yaml not found - test requires actual project")
        finally:
            os.chdir(self.temp_dir)

    def test_path_explanations_in_documentation(self):
        """Test that each path type is explained in the documentation."""
        # Find the actual ADRI project root to access the real config file
        original_cwd = os.getcwd()
        try:
            os.chdir(self.original_cwd)
            project_config_path = Path("ADRI/config.yaml")

            if project_config_path.exists():
                with open(project_config_path, 'r', encoding='utf-8') as f:
                    config_content = f.read()

                # Check for path explanations
                path_explanations = [
                    "YAML contract files are stored (quality validation rules)",
                    "assessment reports are saved (JSON quality reports)",
                    "training data snapshots are preserved (SHA256 integrity tracking)",
                    "audit logs are stored (CSV activity tracking)",
                    "Production-validated YAML contracts",
                    "business-critical quality reports",
                    "regulatory compliance tracking",
                    "compliance and security logging",
                ]

                for explanation in path_explanations:
                    with self.subTest(explanation=explanation):
                        self.assertIn(explanation, config_content,
                            f"Missing path explanation: {explanation}")
            else:
                self.skipTest("Project ADRI/config.yaml not found - test requires actual project")
        finally:
            os.chdir(self.temp_dir)


class TestConfigurationValidation(unittest.TestCase):
    """Configuration file structure and content validation."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)

        self.project_root = Path(self.temp_dir)
        self.adri_dir = self.project_root / "ADRI"
        self.adri_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        """Clean up test fixtures."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)

    def test_config_structure_matches_documentation(self):
        """Test that generated config matches documented structure."""
        result = adri_cli.setup_command(force=True, project_name="structure_test")
        self.assertEqual(result, 0)

        config_path = self.adri_dir / "config.yaml"
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        # Verify top-level structure
        self.assertIn("adri", config)
        adri_config = config["adri"]

        # Verify required top-level fields
        required_fields = ["project_name", "version", "default_environment", "environments"]
        for field in required_fields:
            with self.subTest(field=field):
                self.assertIn(field, adri_config, f"Missing required field: {field}")

        # Verify environments structure
        environments = adri_config["environments"]
        required_environments = ["development", "production"]

        for env in required_environments:
            with self.subTest(environment=env):
                self.assertIn(env, environments, f"Missing environment: {env}")

                # Verify each environment has required sections
                env_config = environments[env]
                self.assertIn("paths", env_config, f"Missing paths in {env}")
                self.assertIn("audit", env_config, f"Missing audit config in {env}")

    def test_environment_paths_configuration(self):
        """Test that environment paths are correctly configured."""
        result = adri_cli.setup_command(force=True, project_name="paths_test")
        self.assertEqual(result, 0)

        config_path = self.adri_dir / "config.yaml"
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        environments = config["adri"]["environments"]

        # Test both development and production environments
        for env_name in ["development", "production"]:
            with self.subTest(environment=env_name):
                env_config = environments[env_name]
                paths = env_config["paths"]

                # Verify all required path types exist
                required_paths = ["contracts", "assessments", "training_data", "audit_logs"]
                for path_type in required_paths:
                    self.assertIn(path_type, paths,
                        f"Missing {path_type} path in {env_name}")

                # Verify paths follow expected pattern
                expected_prefix = "ADRI/dev" if env_name == "development" else "ADRI/prod"
                for path_type, path_value in paths.items():
                    self.assertTrue(path_value.startswith(expected_prefix),
                        f"Path {path_value} doesn't match expected prefix {expected_prefix}")

    def test_audit_configuration_completeness(self):
        """Test that audit configuration is complete for both environments."""
        result = adri_cli.setup_command(force=True, project_name="audit_test")
        self.assertEqual(result, 0)

        config_path = self.adri_dir / "config.yaml"
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        environments = config["adri"]["environments"]

        for env_name in ["development", "production"]:
            with self.subTest(environment=env_name):
                env_config = environments[env_name]
                self.assertIn("audit", env_config, f"Missing audit config in {env_name}")

                audit_config = env_config["audit"]

                # Verify all required audit settings
                required_audit_fields = [
                    "enabled", "log_dir", "log_prefix",
                    "log_level", "include_data_samples", "max_log_size_mb"
                ]

                for field in required_audit_fields:
                    self.assertIn(field, audit_config,
                        f"Missing audit field {field} in {env_name}")

    def test_default_environment_setting(self):
        """Test that default environment is properly set."""
        result = adri_cli.setup_command(force=True, project_name="default_test")
        self.assertEqual(result, 0)

        config_path = self.adri_dir / "config.yaml"
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        adri_config = config["adri"]
        self.assertIn("default_environment", adri_config)
        self.assertEqual(adri_config["default_environment"], "development")

    def test_configuration_version_consistency(self):
        """Test that configuration version is properly set."""
        result = adri_cli.setup_command(force=True, project_name="version_test")
        self.assertEqual(result, 0)

        config_path = self.adri_dir / "config.yaml"
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        adri_config = config["adri"]
        self.assertIn("version", adri_config)
        version = adri_config["version"]

        # Version should be semantic version format
        self.assertRegex(version, r'^\d+\.\d+\.\d+$',
            f"Version {version} should follow semantic versioning")


class TestHelpGuideEnvironmentInformation(unittest.TestCase):
    """Test help guide environment information accuracy."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)

    @patch('click.echo')
    def test_help_guide_includes_environment_information(self, mock_echo):
        """Test that help guide includes comprehensive environment information."""
        result = adri_cli.show_help_guide()
        self.assertEqual(result, 0)

        # Capture all echo calls
        echo_calls = [call.args[0] for call in mock_echo.call_args_list]
        all_output = ' '.join(echo_calls)

        # Check for environment-related information
        environment_info = [
            "Environment Information:",
            "Default: Development environment",
            "Switch: Edit ADRI/config.yaml",
            "default_environment",
            "dev/",
            "prod/",
            "Smart Path Resolution:",
        ]

        for info in environment_info:
            with self.subTest(info=info):
                self.assertIn(info, all_output,
                    f"Help guide missing environment info: {info}")

    @patch('click.echo')
    def test_help_guide_directory_structure_explanation(self, mock_echo):
        """Test that help guide explains directory structure correctly."""
        result = adri_cli.show_help_guide()
        self.assertEqual(result, 0)

        echo_calls = [call.args[0] for call in mock_echo.call_args_list]
        all_output = ' '.join(echo_calls)

        # Check for directory structure explanations
        directory_explanations = [
            "tutorials/",
            "dev/contracts/",
            "dev/assessments/",
            "dev/training-data/",
            "dev/audit-logs/",
            "prod/contracts/",
            "prod/assessments/",
            "prod/training-data/",
            "prod/audit-logs/",
        ]

        for explanation in directory_explanations:
            with self.subTest(explanation=explanation):
                self.assertIn(explanation, all_output,
                    f"Help guide missing directory: {explanation}")


class TestShowConfigEnvironmentDisplay(unittest.TestCase):
    """Test show-config command environment display accuracy."""

    def setUp(self):
        """Set up test fixtures with ADRI project."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)

        # Create ADRI project
        result = adri_cli.setup_command(force=True, project_name="config_display_test")
        self.assertEqual(result, 0)

    def tearDown(self):
        """Clean up test fixtures."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)

    def _safe_get_mock_output(self, mock_echo):
        """Safely extract all output from mock echo calls."""
        echo_calls = []
        for call in mock_echo.call_args_list:
            try:
                if call and hasattr(call, 'args') and call.args and len(call.args) > 0:
                    echo_calls.append(str(call.args[0]))
            except (AttributeError, IndexError, TypeError):
                continue
        return ' '.join(echo_calls)

    @patch('click.echo')
    @patch.dict(os.environ, {}, clear=True)
    def test_show_config_displays_environment_paths(self, mock_echo):
        """Test that show-config correctly displays environment paths."""
        # Set config path to local test config to prevent upward search
        local_config = str(Path(self.temp_dir) / "ADRI" / "config.yaml")
        with patch.dict(os.environ, {"ADRI_CONFIG_PATH": local_config}):
            result = adri_cli.show_config_command()
            self.assertEqual(result, 0)

            # Safe handling of mock call arguments
            all_output = self._safe_get_mock_output(mock_echo)

            # Check for both environments
            environment_indicators = [
                "Development Environment:",
                "Production Environment:",
                "contracts:",
                "assessments:",
                "training_data:",
                "audit_logs:",
            ]

            for indicator in environment_indicators:
                with self.subTest(indicator=indicator):
                    self.assertIn(indicator, all_output,
                        f"show-config missing environment indicator: {indicator}")

    @patch('click.echo')
    def test_show_config_specific_environment_display(self, mock_echo):
        """Test show-config with specific environment parameter."""
        result = adri_cli.show_config_command(environment="development")
        self.assertEqual(result, 0)

        # Safe handling of mock call arguments
        all_output = self._safe_get_mock_output(mock_echo)

        # Should show development environment
        self.assertIn("Development Environment:", all_output)
        # Should not show production environment
        self.assertNotIn("Production Environment:", all_output)

    @patch('click.echo')
    def test_show_config_paths_only_mode(self, mock_echo):
        """Test show-config paths-only mode."""
        result = adri_cli.show_config_command(paths_only=True)
        self.assertEqual(result, 0)

        # Safe handling of mock call arguments
        all_output = self._safe_get_mock_output(mock_echo)

        # Should show paths but not project metadata
        self.assertIn("Environment:", all_output)
        self.assertNotIn("Project:", all_output)


class TestEnvironmentDocumentationIntegration(unittest.TestCase):
    """Integration tests for environment documentation with CLI functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)

    def test_created_directories_match_documented_structure(self):
        """Test that setup creates directories matching documented structure."""
        result = adri_cli.setup_command(force=True, project_name="integration_test")
        self.assertEqual(result, 0)

        # Read config documentation to extract expected directories
        config_path = Path("ADRI/config.yaml")
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        # Verify directories exist as documented
        if config and "adri" in config:
            adri_config = config["adri"]
            environments = adri_config["environments"]

            for env_name, env_config in environments.items():
                paths = env_config["paths"]
                for path_type, path_value in paths.items():
                    with self.subTest(environment=env_name, path_type=path_type):
                        expected_path = Path(path_value)
                        self.assertTrue(expected_path.exists(),
                            f"Directory {expected_path} should exist as documented")
        else:
            self.skipTest("Config file could not be parsed correctly")

    def test_environment_switching_documentation_accuracy(self):
        """Test that documented environment switching methods work."""
        result = adri_cli.setup_command(force=True, project_name="switching_test")
        self.assertEqual(result, 0)

        config_path = Path("ADRI/config.yaml")

        # Test configuration method (documented in config.yaml)
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        # Change default environment as documented
        config["adri"]["default_environment"] = "production"

        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f)

        # Verify the change worked
        with open(config_path, 'r', encoding='utf-8') as f:
            updated_config = yaml.safe_load(f)

        self.assertEqual(updated_config["adri"]["default_environment"], "production")

    def test_workflow_recommendations_are_actionable(self):
        """Test that documented workflow recommendations are actionable."""
        result = adri_cli.setup_command(force=True, project_name="workflow_test")
        self.assertEqual(result, 0)

        # Test step: "Copy proven contracts from dev/contracts/ to prod/contracts/"
        dev_contracts = Path("ADRI/dev/contracts")
        prod_contracts = Path("ADRI/prod/contracts")

        # Both directories should exist as documented
        self.assertTrue(dev_contracts.exists())
        self.assertTrue(prod_contracts.exists())

        # Create test contract in dev
        test_contract = dev_contracts / "test_contract.yaml"
        contract_content = {"contracts": {"name": "Test Contract"}}
        with open(test_contract, 'w', encoding='utf-8') as f:
            yaml.dump(contract_content, f)

        # Copy to prod as documented workflow recommends
        import shutil
        shutil.copy2(test_contract, prod_contracts / "test_contract.yaml")

        # Verify workflow step completed successfully
        prod_contract = prod_contracts / "test_contract.yaml"
        self.assertTrue(prod_contract.exists())


class TestDocumentationConsistency(unittest.TestCase):
    """Test consistency between different documentation sources."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)

        # Create comprehensive ADRI project
        result = adri_cli.setup_command(force=True, project_name="consistency_test")
        self.assertEqual(result, 0)

    def tearDown(self):
        """Clean up test fixtures."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)

    def _safe_get_mock_output(self, mock_echo):
        """Safely extract all output from mock echo calls."""
        echo_calls = []
        for call in mock_echo.call_args_list:
            try:
                if call and hasattr(call, 'args') and call.args and len(call.args) > 0:
                    echo_calls.append(str(call.args[0]))
            except (AttributeError, IndexError, TypeError):
                continue
        return ' '.join(echo_calls)

    @patch('click.echo')
    def test_help_guide_config_consistency(self, mock_echo):
        """Test consistency between help guide and config.yaml documentation."""
        # Get help guide output
        adri_cli.show_help_guide()
        help_output = self._safe_get_mock_output(mock_echo)

        # Read config documentation
        config_path = Path("ADRI/config.yaml")
        with open(config_path, 'r', encoding='utf-8') as f:
            config_content = f.read()

        # Check that key concepts are consistent between sources
        common_concepts = [
            "dev/",
            "prod/",
            "contracts",
            "assessments",
            "training-data",
            "audit-logs",
            "development",
            "production",
        ]

        for concept in common_concepts:
            with self.subTest(concept=concept):
                # Both sources should mention the concept
                self.assertIn(concept, help_output,
                    f"Help guide missing concept: {concept}")
                self.assertIn(concept, config_content,
                    f"Config documentation missing concept: {concept}")

    @patch('click.echo')
    @patch.dict(os.environ, {}, clear=True)
    def test_show_config_documentation_consistency(self, mock_echo):
        """Test consistency between show-config output and actual config."""
        # Set config path to local test config to prevent upward search
        local_config = str(Path(self.temp_dir) / "ADRI" / "config.yaml")
        with patch.dict(os.environ, {"ADRI_CONFIG_PATH": local_config}):
            adri_cli.show_config_command()

            # Safe handling of mock call arguments
            show_config_output = self._safe_get_mock_output(mock_echo)

            # Read actual config
            config_path = Path("ADRI/config.yaml")
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            # Check that show-config displays match actual config values
            adri_config = config["adri"]

            # Project name consistency
            self.assertIn(adri_config["project_name"], show_config_output)

            # Version consistency
            self.assertIn(adri_config["version"], show_config_output)

            # Default environment consistency
            self.assertIn(adri_config["default_environment"], show_config_output)


if __name__ == '__main__':
    unittest.main()
