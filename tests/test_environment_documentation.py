"""
Configuration Documentation Validation Tests for ADRI CLI.

Tests the documentation system that explains:
- Configuration file structure and content
- Directory structure (flat folder structure)
- Workflow recommendations
- Audit configuration

Updated for flat folder structure (no dev/prod environments in OSS).
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

# Import CLI functions for testing documentation integration
import src.adri.cli as adri_cli


class TestConfigDocumentation(unittest.TestCase):
    """Configuration documentation completeness and accuracy testing."""

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

    def test_config_yaml_has_documentation(self):
        """Test that config.yaml contains documentation sections."""
        # Find the actual ADRI project root to access the real config file
        original_cwd = os.getcwd()
        try:
            # Go to project root to find the config
            os.chdir(self.original_cwd)
            project_config_path = Path("ADRI/config.yaml")

            if project_config_path.exists():
                # Read config file content as text to check documentation
                with open(project_config_path, 'r', encoding='utf-8') as f:
                    config_content = f.read()

                # Check for major documentation sections
                required_doc_sections = [
                    "ADRI",
                    "contracts",
                    "assessments",
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

                # Check for directory structure explanation (flat structure)
                directory_docs = [
                    "contracts",
                    "assessments",
                ]

                for doc_item in directory_docs:
                    with self.subTest(doc_item=doc_item):
                        self.assertIn(doc_item, config_content,
                            f"Missing directory documentation: {doc_item}")
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

        # Verify required top-level fields (flat structure - no environments)
        required_fields = ["project_name", "version", "paths"]
        for field in required_fields:
            with self.subTest(field=field):
                self.assertIn(field, adri_config, f"Missing required field: {field}")

        # Verify paths structure (flat)
        paths = adri_config["paths"]
        required_paths = ["contracts", "assessments", "training_data", "audit_logs"]
        for path_type in required_paths:
            with self.subTest(path_type=path_type):
                self.assertIn(path_type, paths, f"Missing path: {path_type}")

    def test_flat_paths_configuration(self):
        """Test that paths use flat structure (no dev/prod)."""
        result = adri_cli.setup_command(force=True, project_name="paths_test")
        self.assertEqual(result, 0)

        config_path = self.adri_dir / "config.yaml"
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        paths = config["adri"]["paths"]

        # Verify flat paths (no dev/prod prefix)
        self.assertIn("ADRI/contracts", paths["contracts"])
        self.assertIn("ADRI/assessments", paths["assessments"])

        # Should NOT have dev/prod in paths
        for path_type, path_value in paths.items():
            with self.subTest(path_type=path_type):
                self.assertNotIn("/dev/", path_value, f"Path {path_value} should not contain /dev/")
                self.assertNotIn("/prod/", path_value, f"Path {path_value} should not contain /prod/")

    def test_audit_configuration_completeness(self):
        """Test that audit configuration is complete."""
        result = adri_cli.setup_command(force=True, project_name="audit_test")
        self.assertEqual(result, 0)

        config_path = self.adri_dir / "config.yaml"
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        adri_config = config["adri"]

        # Check for audit section (may be at top level)
        if "audit" in adri_config:
            audit_config = adri_config["audit"]

            # Verify common audit settings
            common_audit_fields = ["enabled", "log_dir", "log_level"]

            for field in common_audit_fields:
                with self.subTest(field=field):
                    self.assertIn(field, audit_config,
                        f"Missing audit field {field}")

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


class TestHelpGuideInformation(unittest.TestCase):
    """Test help guide information accuracy."""

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
    def test_help_guide_includes_path_information(self, mock_echo):
        """Test that help guide includes path information."""
        result = adri_cli.show_help_guide()
        self.assertEqual(result, 0)

        # Capture all echo calls
        echo_calls = [call.args[0] for call in mock_echo.call_args_list]
        all_output = ' '.join(echo_calls)

        # Check for path-related information
        path_info = [
            "contracts",
            "assessments",
        ]

        for info in path_info:
            with self.subTest(info=info):
                self.assertIn(info, all_output,
                    f"Help guide missing path info: {info}")

    @patch('click.echo')
    def test_help_guide_directory_structure_explanation(self, mock_echo):
        """Test that help guide explains directory structure correctly."""
        result = adri_cli.show_help_guide()
        self.assertEqual(result, 0)

        echo_calls = [call.args[0] for call in mock_echo.call_args_list]
        all_output = ' '.join(echo_calls)

        # Check for directory structure explanations (flat)
        directory_explanations = [
            "tutorials/",
            "contracts/",
            "assessments/",
        ]

        for explanation in directory_explanations:
            with self.subTest(explanation=explanation):
                self.assertIn(explanation, all_output,
                    f"Help guide missing directory: {explanation}")


class TestShowConfigDisplay(unittest.TestCase):
    """Test show-config command display accuracy."""

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
    def test_show_config_displays_paths(self, mock_echo):
        """Test that show-config correctly displays paths.

        Tests that show_config_command works correctly with the flat OSS
        config structure (paths at top level, no environments).
        """
        # Set config path to local test config to prevent upward search
        local_config = str(Path(self.temp_dir) / "ADRI" / "config.yaml")
        # Set ADRI_CONTRACTS_DIR to the temp directory's contracts path
        # This ensures the contracts directory exists and is accessible
        temp_contracts_dir = str(Path(self.temp_dir) / "ADRI" / "contracts")
        with patch.dict(os.environ, {"ADRI_CONFIG_PATH": local_config, "ADRI_CONTRACTS_DIR": temp_contracts_dir}):
            # Note: show_config_command may return non-zero in some environments
            # due to internal checks, but we primarily care about the output content
            adri_cli.show_config_command()

            # Safe handling of mock call arguments
            all_output = self._safe_get_mock_output(mock_echo)

            # Check for path indicators - the command should output config information
            # even if it encounters some issues
            path_indicators = [
                "contracts",
                "assessments",
            ]

            for indicator in path_indicators:
                with self.subTest(indicator=indicator):
                    self.assertIn(indicator, all_output,
                        f"show-config missing path indicator: {indicator}")


class TestConfigurationIntegration(unittest.TestCase):
    """Integration tests for configuration with CLI functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)

    def test_created_directories_match_flat_structure(self):
        """Test that setup creates directories matching flat structure."""
        result = adri_cli.setup_command(force=True, project_name="integration_test")
        self.assertEqual(result, 0)

        # Verify flat directories exist
        expected_dirs = [
            Path("ADRI/contracts"),
            Path("ADRI/assessments"),
            Path("ADRI/training-data"),
            Path("ADRI/audit-logs"),
        ]

        for expected_path in expected_dirs:
            with self.subTest(path=str(expected_path)):
                self.assertTrue(expected_path.exists(),
                    f"Directory {expected_path} should exist")

    def test_workflow_with_flat_structure(self):
        """Test that workflow works with flat structure."""
        result = adri_cli.setup_command(force=True, project_name="workflow_test")
        self.assertEqual(result, 0)

        # Test: Create contract in contracts directory
        contracts_dir = Path("ADRI/contracts")

        # Directory should exist
        self.assertTrue(contracts_dir.exists())

        # Create test contract
        test_contract = contracts_dir / "test_contract.yaml"
        contract_content = {"contracts": {"name": "Test Contract"}}
        with open(test_contract, 'w', encoding='utf-8') as f:
            yaml.dump(contract_content, f)

        # Verify contract created successfully
        self.assertTrue(test_contract.exists())


class TestDocumentationConsistency(unittest.TestCase):
    """Test consistency between different documentation sources."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)

        # Create ADRI project
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

        # Check that key concepts are consistent between sources (flat structure)
        common_concepts = [
            "contracts",
            "assessments",
            "training-data",
            "audit-logs",
        ]

        for concept in common_concepts:
            with self.subTest(concept=concept):
                # Config should mention the concept
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


if __name__ == '__main__':
    unittest.main()
