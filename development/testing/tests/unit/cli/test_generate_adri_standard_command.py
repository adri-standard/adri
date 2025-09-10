"""
Unit tests for the generate-adri-standard CLI command.

This module tests the CLI command implementation using TDD approach.
"""

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import yaml

from adri.cli.commands import generate_adri_standard_command
from adri.config.manager import ConfigManager


class TestGenerateAdriStandardCommand(unittest.TestCase):
    """Test cases for generate-adri-standard command."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.test_dir, "adri-config.yaml")
        self.data_path = os.path.join(self.test_dir, "test_data.csv")
        self.standards_dir = os.path.join(self.test_dir, "standards")

        # Create test directories
        os.makedirs(self.standards_dir, exist_ok=True)

        # Create test configuration
        self.test_config = {
            "adri": {
                "version": "2.0",
                "project_name": "Test Project",
                "default_environment": "development",
                "environments": {
                    "development": {
                        "paths": {
                            "standards": self.standards_dir,
                            "training_data": self.test_dir,
                            "assessments": self.test_dir,
                        }
                    }
                },
                "assessment": {"performance": {"max_rows": 1000000}},
                "generation": {
                    "default_thresholds": {
                        "completeness_min": 85,
                        "validity_min": 90,
                        "consistency_min": 80,
                        "freshness_max_age": "7d",
                        "plausibility_outlier_threshold": 3.0,
                    }
                },
            }
        }

        with open(self.config_path, "w") as f:
            yaml.dump(self.test_config, f)

        # Create test CSV data
        self.test_csv_content = """customer_id,name,email,age,registration_date,account_balance
1,John Doe,john.doe@email.com,25,2023-01-15,1500.50
2,Jane Smith,jane.smith@email.com,30,2023-02-20,2750.00
3,Bob Johnson,bob.johnson@email.com,35,2023-03-10,500.25
4,Alice Brown,alice.brown@email.com,28,2023-04-05,3200.75
5,Charlie Wilson,charlie.wilson@email.com,42,2023-05-12,1800.00"""

        with open(self.data_path, "w") as f:
            f.write(self.test_csv_content)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_generate_adri_standard_command_success(self):
        """Test successful generation of ADRI standard."""
        # Test that the command runs successfully
        result = generate_adri_standard_command(
            data_path="test_data.csv",
            force=False,
            verbose=False,
            environment=None,
            config_path=self.config_path,
        )

        # Should return 0 for success
        self.assertEqual(result, 0)

        # Check that output file was created
        expected_output = os.path.join(
            self.standards_dir, "test_data_ADRI_standard.yaml"
        )
        self.assertTrue(os.path.exists(expected_output))

        # Verify the generated YAML is valid
        with open(expected_output, "r") as f:
            generated_standard = yaml.safe_load(f)

        # Check basic structure
        self.assertIn("standards", generated_standard)
        self.assertIn("requirements", generated_standard)
        self.assertIn("metadata", generated_standard)

        # Check standards metadata
        standards_meta = generated_standard["standards"]
        self.assertIn("id", standards_meta)
        self.assertIn("name", standards_meta)
        self.assertIn("version", standards_meta)
        self.assertIn("authority", standards_meta)

        # Check requirements structure
        requirements = generated_standard["requirements"]
        self.assertIn("overall_minimum", requirements)
        self.assertIn("field_requirements", requirements)

    def test_generate_adri_standard_command_file_not_found(self):
        """Test command with non-existent data file."""
        result = generate_adri_standard_command(
            data_path="nonexistent.csv",
            force=False,
            verbose=False,
            environment=None,
            config_path=self.config_path,
        )

        # Should return 1 for error
        self.assertEqual(result, 1)

    def test_generate_adri_standard_command_no_config(self):
        """Test command with no configuration."""
        result = generate_adri_standard_command(
            data_path="test_data.csv",
            force=False,
            verbose=False,
            environment=None,
            config_path="nonexistent_config.yaml",
        )

        # Should return 1 for error
        self.assertEqual(result, 1)

    def test_generate_adri_standard_command_force_overwrite(self):
        """Test command with force overwrite."""
        # Create existing standard file
        existing_standard_path = os.path.join(
            self.standards_dir, "test_data_ADRI_standard.yaml"
        )
        with open(existing_standard_path, "w") as f:
            f.write("existing: content")

        # Run command with force=True
        result = generate_adri_standard_command(
            data_path="test_data.csv",
            force=True,
            verbose=False,
            environment=None,
            config_path=self.config_path,
        )

        # Should succeed
        self.assertEqual(result, 0)

        # File should be overwritten
        with open(existing_standard_path, "r") as f:
            content = f.read()

        # Should not contain the old content
        self.assertNotIn("existing: content", content)

    def test_generate_adri_standard_command_no_force_existing_file(self):
        """Test command without force when file exists."""
        # Create existing standard file
        existing_standard_path = os.path.join(
            self.standards_dir, "test_data_ADRI_standard.yaml"
        )
        with open(existing_standard_path, "w") as f:
            f.write("existing: content")

        # Run command with force=False
        result = generate_adri_standard_command(
            data_path="test_data.csv",
            force=False,
            verbose=False,
            environment=None,
            config_path=self.config_path,
        )

        # Should fail
        self.assertEqual(result, 1)

        # File should not be overwritten
        with open(existing_standard_path, "r") as f:
            content = f.read()

        # Should still contain the old content
        self.assertIn("existing: content", content)

    def test_generate_adri_standard_command_verbose_output(self):
        """Test command with verbose output."""
        # This test would check that verbose output is produced
        # For now, we'll just verify it doesn't crash
        result = generate_adri_standard_command(
            data_path="test_data.csv",
            force=False,
            verbose=True,
            environment=None,
            config_path=self.config_path,
        )

        self.assertEqual(result, 0)

    def test_generate_adri_standard_command_specific_environment(self):
        """Test command with specific environment."""
        result = generate_adri_standard_command(
            data_path="test_data.csv",
            force=False,
            verbose=False,
            environment="development",
            config_path=self.config_path,
        )

        self.assertEqual(result, 0)


if __name__ == "__main__":
    unittest.main()
