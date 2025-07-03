"""
Tests for ADRI CLI listing commands.
"""

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from adri.cli.commands import (
    clean_cache_command,
    list_assessments_command,
    list_standards_command,
    list_training_data_command,
)


class TestListStandardsCommand(unittest.TestCase):
    """Test the list-standards command."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, "adri-config.yaml")
        self.standards_dir = os.path.join(self.temp_dir, "standards")
        os.makedirs(self.standards_dir)

        # Create mock config
        self.mock_config = {
            "adri": {
                "project_name": "test-project",
                "version": "2.0.0",
                "default_environment": "development",
                "environments": {
                    "development": {
                        "paths": {
                            "standards": self.standards_dir,
                            "training_data": os.path.join(
                                self.temp_dir, "training_data"
                            ),
                            "assessments": os.path.join(self.temp_dir, "assessments"),
                        }
                    }
                },
            }
        }

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch("adri.cli.commands.ConfigManager")
    def test_list_standards_no_config(self, mock_config_manager):
        """Test list-standards command with no configuration."""
        mock_manager = MagicMock()
        mock_manager.get_active_config.return_value = None
        mock_config_manager.return_value = mock_manager

        result = list_standards_command()

        self.assertEqual(result, 1)
        mock_manager.get_active_config.assert_called_once()

    @patch("adri.cli.commands.ConfigManager")
    def test_list_standards_no_directory(self, mock_config_manager):
        """Test list-standards command with no standards directory."""
        mock_manager = MagicMock()
        mock_manager.get_active_config.return_value = self.mock_config
        mock_manager.get_environment_config.return_value = self.mock_config["adri"][
            "environments"
        ]["development"]
        mock_config_manager.return_value = mock_manager

        # Remove standards directory
        os.rmdir(self.standards_dir)

        result = list_standards_command()

        self.assertEqual(result, 0)

    @patch("adri.cli.commands.ConfigManager")
    def test_list_standards_with_files(self, mock_config_manager):
        """Test list-standards command with standard files."""
        mock_manager = MagicMock()
        mock_manager.get_active_config.return_value = self.mock_config
        mock_manager.get_environment_config.return_value = self.mock_config["adri"][
            "environments"
        ]["development"]
        mock_config_manager.return_value = mock_manager

        # Create test standard files
        standard1_path = os.path.join(self.standards_dir, "test_standard1.yaml")
        standard2_path = os.path.join(self.standards_dir, "test_standard2.yml")

        with open(standard1_path, "w") as f:
            f.write(
                """
standards:
  id: test-standard-1
  name: Test Standard 1
  version: 1.0.0
  authority: Test Authority
requirements:
  overall_minimum: 80.0
"""
            )

        with open(standard2_path, "w") as f:
            f.write(
                """
standards:
  id: test-standard-2
  name: Test Standard 2
  version: 2.0.0
  authority: Test Authority
requirements:
  overall_minimum: 85.0
"""
            )

        result = list_standards_command()

        self.assertEqual(result, 0)


class TestListTrainingDataCommand(unittest.TestCase):
    """Test the list-training-data command."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.training_data_dir = os.path.join(self.temp_dir, "training_data")
        os.makedirs(self.training_data_dir)

        # Create mock config
        self.mock_config = {
            "adri": {
                "project_name": "test-project",
                "version": "2.0.0",
                "default_environment": "development",
                "environments": {
                    "development": {
                        "paths": {
                            "standards": os.path.join(self.temp_dir, "standards"),
                            "training_data": self.training_data_dir,
                            "assessments": os.path.join(self.temp_dir, "assessments"),
                        }
                    }
                },
            }
        }

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch("adri.cli.commands.ConfigManager")
    def test_list_training_data_with_files(self, mock_config_manager):
        """Test list-training-data command with data files."""
        mock_manager = MagicMock()
        mock_manager.get_active_config.return_value = self.mock_config
        mock_manager.get_environment_config.return_value = self.mock_config["adri"][
            "environments"
        ]["development"]
        mock_config_manager.return_value = mock_manager

        # Create test data files
        csv_path = os.path.join(self.training_data_dir, "test_data.csv")
        json_path = os.path.join(self.training_data_dir, "test_data.json")

        with open(csv_path, "w") as f:
            f.write("id,name,value\n1,test,100\n2,test2,200\n")

        with open(json_path, "w") as f:
            json.dump([{"id": 1, "name": "test", "value": 100}], f)

        result = list_training_data_command()

        self.assertEqual(result, 0)

    @patch("adri.cli.commands.ConfigManager")
    def test_list_training_data_no_files(self, mock_config_manager):
        """Test list-training-data command with no data files."""
        mock_manager = MagicMock()
        mock_manager.get_active_config.return_value = self.mock_config
        mock_manager.get_environment_config.return_value = self.mock_config["adri"][
            "environments"
        ]["development"]
        mock_config_manager.return_value = mock_manager

        result = list_training_data_command()

        self.assertEqual(result, 0)


class TestListAssessmentsCommand(unittest.TestCase):
    """Test the list-assessments command."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.assessments_dir = os.path.join(self.temp_dir, "assessments")
        os.makedirs(self.assessments_dir)

        # Create mock config
        self.mock_config = {
            "adri": {
                "project_name": "test-project",
                "version": "2.0.0",
                "default_environment": "development",
                "environments": {
                    "development": {
                        "paths": {
                            "standards": os.path.join(self.temp_dir, "standards"),
                            "training_data": os.path.join(
                                self.temp_dir, "training_data"
                            ),
                            "assessments": self.assessments_dir,
                        }
                    }
                },
            }
        }

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch("adri.cli.commands.ConfigManager")
    def test_list_assessments_with_files(self, mock_config_manager):
        """Test list-assessments command with assessment files."""
        mock_manager = MagicMock()
        mock_manager.get_active_config.return_value = self.mock_config
        mock_manager.get_environment_config.return_value = self.mock_config["adri"][
            "environments"
        ]["development"]
        mock_config_manager.return_value = mock_manager

        # Create test assessment files
        assessment1_path = os.path.join(self.assessments_dir, "assessment1.json")
        assessment2_path = os.path.join(self.assessments_dir, "assessment2.json")

        assessment_data = {
            "overall_score": 85.5,
            "passed": True,
            "dimension_scores": {
                "validity": {"score": 18.0},
                "completeness": {"score": 17.0},
                "consistency": {"score": 16.5},
                "freshness": {"score": 19.0},
                "plausibility": {"score": 15.0},
            },
            "metadata": {
                "data_source": "test_data.csv",
                "standard_name": "test_standard.yaml",
            },
        }

        with open(assessment1_path, "w") as f:
            json.dump(assessment_data, f)

        with open(assessment2_path, "w") as f:
            json.dump(assessment_data, f)

        result = list_assessments_command(recent=5)

        self.assertEqual(result, 0)


class TestCleanCacheCommand(unittest.TestCase):
    """Test the clean-cache command."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()

        # Create mock config
        self.mock_config = {
            "adri": {
                "project_name": "test-project",
                "version": "2.0.0",
                "default_environment": "development",
                "environments": {
                    "development": {
                        "paths": {
                            "standards": os.path.join(self.temp_dir, "standards"),
                            "training_data": os.path.join(
                                self.temp_dir, "training_data"
                            ),
                            "assessments": os.path.join(self.temp_dir, "assessments"),
                        }
                    }
                },
            }
        }

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch("adri.cli.commands.ConfigManager")
    def test_clean_cache_dry_run(self, mock_config_manager):
        """Test clean-cache command with dry run."""
        mock_manager = MagicMock()
        mock_manager.get_active_config.return_value = self.mock_config
        mock_manager.get_environment_config.return_value = self.mock_config["adri"][
            "environments"
        ]["development"]
        mock_config_manager.return_value = mock_manager

        # Create some cache files
        cache_dir = os.path.join(self.temp_dir, "__pycache__")
        os.makedirs(cache_dir)

        cache_file = os.path.join(cache_dir, "test.pyc")
        with open(cache_file, "w") as f:
            f.write("test cache content")

        result = clean_cache_command(dry_run=True)

        self.assertEqual(result, 0)
        # File should still exist after dry run
        self.assertTrue(os.path.exists(cache_file))

    @patch("adri.cli.commands.ConfigManager")
    def test_clean_cache_no_files(self, mock_config_manager):
        """Test clean-cache command with no cache files."""
        mock_manager = MagicMock()
        mock_manager.get_active_config.return_value = self.mock_config
        mock_manager.get_environment_config.return_value = self.mock_config["adri"][
            "environments"
        ]["development"]
        mock_config_manager.return_value = mock_manager

        result = clean_cache_command()

        self.assertEqual(result, 0)


if __name__ == "__main__":
    unittest.main()
