"""
Config Loader Comprehensive Tests - Multi-Dimensional Quality Framework
Tests configuration loading and management functionality with comprehensive coverage (85%+ line coverage target).
Applies multi-dimensional quality framework: Integration (30%), Error Handling (25%), Performance (15%), Line Coverage (30%).
"""

import unittest
import tempfile
import os
import shutil
import yaml
import time
import threading
from pathlib import Path
from unittest.mock import patch, Mock, MagicMock
import pytest

from src.adri.config.loader import (
    ConfigurationLoader,
    load_adri_config,
    get_protection_settings,
    resolve_standard_file,
    ConfigManager
)


class TestConfigLoaderIntegration(unittest.TestCase):
    """Test complete configuration loader workflow integration (30% weight in quality score)."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)

    def tearDown(self):
        """Clean up test environment."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)

    def test_complete_configuration_workflow(self):
        """Test end-to-end configuration management workflow."""
        loader = ConfigurationLoader()

        # Test default configuration creation
        default_config = loader.create_default_config("integration_test_project")

        # Verify default configuration structure
        self.assertIn("adri", default_config)
        self.assertEqual(default_config["adri"]["project_name"], "integration_test_project")
        self.assertEqual(default_config["adri"]["version"], "4.0.0")
        self.assertEqual(default_config["adri"]["default_environment"], "development")

        # Verify environments are properly structured
        environments = default_config["adri"]["environments"]
        self.assertIn("development", environments)
        self.assertIn("production", environments)

        # Verify development environment
        dev_env = environments["development"]
        self.assertIn("paths", dev_env)
        self.assertEqual(dev_env["paths"]["standards"], "./ADRI/dev/standards")
        self.assertEqual(dev_env["paths"]["assessments"], "./ADRI/dev/assessments")
        self.assertEqual(dev_env["protection"]["default_failure_mode"], "warn")
        self.assertEqual(dev_env["protection"]["default_min_score"], 75)

        # Verify production environment
        prod_env = environments["production"]
        self.assertEqual(prod_env["paths"]["standards"], "./ADRI/prod/standards")
        self.assertEqual(prod_env["protection"]["default_failure_mode"], "raise")
        self.assertEqual(prod_env["protection"]["default_min_score"], 85)

        # Test configuration validation
        is_valid = loader.validate_config(default_config)
        self.assertTrue(is_valid)

        # Test configuration saving
        config_file = "test_config.yaml"
        loader.save_config(default_config, config_file)
        self.assertTrue(Path(config_file).exists())

        # Test configuration loading
        loaded_config = loader.load_config(config_file)
        self.assertIsNotNone(loaded_config)
        self.assertEqual(loaded_config["adri"]["project_name"], "integration_test_project")

        # Test active configuration retrieval
        active_config = loader.get_active_config(config_file)
        self.assertEqual(active_config, loaded_config)

        # Test environment configuration retrieval
        dev_config = loader.get_environment_config(loaded_config, "development")
        self.assertEqual(dev_config["paths"]["standards"], "./ADRI/dev/standards")

        prod_config = loader.get_environment_config(loaded_config, "production")
        self.assertEqual(prod_config["paths"]["standards"], "./ADRI/prod/standards")

        # Test default environment (no explicit environment specified)
        default_env_config = loader.get_environment_config(loaded_config)
        self.assertEqual(default_env_config, dev_config)  # Should use development as default

    def test_directory_structure_creation_workflow(self):
        """Test directory structure creation workflow."""
        loader = ConfigurationLoader()

        # Create configuration with custom paths
        config = {
            "adri": {
                "project_name": "directory_test",
                "default_environment": "development",
                "environments": {
                    "development": {
                        "paths": {
                            "standards": "./custom/dev/standards",
                            "assessments": "./custom/dev/assessments",
                            "training_data": "./custom/dev/training-data"
                        }
                    },
                    "staging": {
                        "paths": {
                            "standards": "./custom/staging/standards",
                            "assessments": "./custom/staging/assessments",
                            "training_data": "./custom/staging/training-data"
                        }
                    },
                    "production": {
                        "paths": {
                            "standards": "./custom/prod/standards",
                            "assessments": "./custom/prod/assessments",
                            "training_data": "./custom/prod/training-data"
                        }
                    }
                }
            }
        }

        # Test directory creation
        loader.create_directory_structure(config)

        # Verify all directories were created
        expected_dirs = [
            "./custom/dev/standards",
            "./custom/dev/assessments",
            "./custom/dev/training-data",
            "./custom/staging/standards",
            "./custom/staging/assessments",
            "./custom/staging/training-data",
            "./custom/prod/standards",
            "./custom/prod/assessments",
            "./custom/prod/training-data"
        ]

        for dir_path in expected_dirs:
            self.assertTrue(Path(dir_path).exists(), f"Directory {dir_path} was not created")
            self.assertTrue(Path(dir_path).is_dir(), f"Path {dir_path} is not a directory")

    def test_config_file_discovery_workflow(self):
        """Test configuration file discovery across directory tree."""
        loader = ConfigurationLoader()

        # Create nested directory structure
        deep_dir = Path("level1/level2/level3/level4")
        deep_dir.mkdir(parents=True)

        # Create config files in different locations
        config_locations = [
            "ADRI/config.yaml",  # Root level, new location
            "level1/adri-config.yaml",  # One level deep, legacy
            "level1/level2/.adri.yaml"  # Two levels deep, hidden
        ]

        config_content = {
            "adri": {
                "project_name": "discovery_test",
                "default_environment": "development",
                "environments": {
                    "development": {
                        "paths": {
                            "standards": "./ADRI/dev/standards",
                            "assessments": "./ADRI/dev/assessments",
                            "training_data": "./ADRI/dev/training-data"
                        }
                    }
                }
            }
        }

        for config_path in config_locations:
            Path(config_path).parent.mkdir(parents=True, exist_ok=True)
            with open(config_path, "w") as f:
                yaml.dump(config_content, f)

        # Test discovery from different starting points

        # From root - should find ADRI/config.yaml (highest priority)
        found_config = loader.find_config_file(".")
        self.assertEqual(found_config, str(Path("ADRI/config.yaml").resolve()))

        # From level1 - should find level1/adri-config.yaml
        os.chdir("level1")
        found_config = loader.find_config_file(".")
        self.assertIn("adri-config.yaml", found_config)
        os.chdir("..")

        # From deep directory - should search up and find config
