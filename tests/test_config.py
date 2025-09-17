"""
Tests for ADRI configuration functionality.

Tests the ConfigurationLoader and configuration management.
Consolidated from tests/unit/config/test_*.py with updated imports for src/ layout.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os
from pathlib import Path
import yaml

# Updated imports for new src/ layout
from adri.config.loader import (
    ConfigurationLoader,
    load_adri_config,
    get_protection_settings,
    resolve_standard_file
)


class TestConfigurationLoader(unittest.TestCase):
    """Test the ConfigurationLoader class."""

    def setUp(self):
        """Set up test fixtures."""
        self.loader = ConfigurationLoader()
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        os.chdir(self.original_cwd)
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_create_default_config(self):
        """Test creating default configuration."""
        config = self.loader.create_default_config("test_project")

        self.assertIn("adri", config)
        self.assertEqual(config["adri"]["project_name"], "test_project")
        self.assertEqual(config["adri"]["version"], "4.0.0")
        self.assertIn("environments", config["adri"])
        self.assertIn("development", config["adri"]["environments"])
        self.assertIn("production", config["adri"]["environments"])

    def test_validate_config_valid(self):
        """Test configuration validation with valid config."""
        valid_config = self.loader.create_default_config("test")
        result = self.loader.validate_config(valid_config)
        self.assertTrue(result)

    def test_validate_config_missing_adri_section(self):
        """Test configuration validation with missing adri section."""
        invalid_config = {"other": "section"}
        result = self.loader.validate_config(invalid_config)
        self.assertFalse(result)

    def test_validate_config_missing_environments(self):
        """Test configuration validation with missing environments."""
        invalid_config = {
            "adri": {
                "project_name": "test",
                "default_environment": "development"
                # Missing environments
            }
        }
        result = self.loader.validate_config(invalid_config)
        self.assertFalse(result)

    def test_save_and_load_config(self):
        """Test saving and loading configuration."""
        config = self.loader.create_default_config("test_project")
        config_path = "test-config.yaml"

        # Save config
        self.loader.save_config(config, config_path)
        self.assertTrue(os.path.exists(config_path))

        # Load config
        loaded_config = self.loader.load_config(config_path)
        self.assertEqual(loaded_config["adri"]["project_name"], "test_project")

    def test_load_config_nonexistent_file(self):
        """Test loading nonexistent config file."""
        result = self.loader.load_config("nonexistent.yaml")
        self.assertIsNone(result)

    def test_find_config_file_current_directory(self):
        """Test finding config file in current directory."""
        # Create config file
        with open("adri-config.yaml", 'w') as f:
            f.write("test: config")

        found_path = self.loader.find_config_file()
        self.assertEqual(found_path, str(Path.cwd() / "adri-config.yaml"))

    def test_find_config_file_not_found(self):
        """Test when config file is not found."""
        result = self.loader.find_config_file()
        self.assertIsNone(result)

    def test_get_active_config_with_path(self):
        """Test getting active config with specific path."""
        config = self.loader.create_default_config("test")
        config_path = "test-config.yaml"
        self.loader.save_config(config, config_path)

        active_config = self.loader.get_active_config(config_path)
        self.assertEqual(active_config["adri"]["project_name"], "test")

    def test_get_active_config_search(self):
        """Test getting active config by searching."""
        config = self.loader.create_default_config("test")
        self.loader.save_config(config, "adri-config.yaml")

        active_config = self.loader.get_active_config()
        self.assertEqual(active_config["adri"]["project_name"], "test")

    def test_get_environment_config_default(self):
        """Test getting environment config for default environment."""
        config = self.loader.create_default_config("test")
        env_config = self.loader.get_environment_config(config)

        # Should return development environment (default)
        self.assertIn("paths", env_config)
        self.assertEqual(env_config["paths"]["standards"], "./ADRI/dev/standards")

    def test_get_environment_config_specific(self):
        """Test getting environment config for specific environment."""
        config = self.loader.create_default_config("test")
        env_config = self.loader.get_environment_config(config, "production")

        self.assertIn("paths", env_config)
        self.assertEqual(env_config["paths"]["standards"], "./ADRI/prod/standards")

    def test_get_environment_config_invalid_environment(self):
        """Test getting environment config for invalid environment."""
        config = self.loader.create_default_config("test")

        with self.assertRaises(ValueError) as context:
            self.loader.get_environment_config(config, "invalid_env")

        self.assertIn("Environment 'invalid_env' not found", str(context.exception))

    def test_get_protection_config_no_config_file(self):
        """Test getting protection config when no config file exists."""
        with patch.object(self.loader, 'get_active_config', return_value=None):
            protection_config = self.loader.get_protection_config()

        # Should return defaults
        self.assertEqual(protection_config["default_failure_mode"], "raise")
        self.assertEqual(protection_config["default_min_score"], 80)

    def test_get_protection_config_with_overrides(self):
        """Test getting protection config with environment overrides."""
        config = self.loader.create_default_config("test")
        # Add environment-specific protection config
        config["adri"]["environments"]["development"]["protection"]["default_min_score"] = 70

        with patch.object(self.loader, 'get_active_config', return_value=config):
            protection_config = self.loader.get_protection_config("development")

        self.assertEqual(protection_config["default_min_score"], 70)  # Should be overridden

    def test_resolve_standard_path_no_config(self):
        """Test resolving standard path when no config exists."""
        with patch.object(self.loader, 'get_active_config', return_value=None):
            path = self.loader.resolve_standard_path("test_standard")

        # Should return fallback path
        self.assertEqual(path, "./ADRI/dev/standards/test_standard.yaml")

    def test_resolve_standard_path_with_config(self):
        """Test resolving standard path with active config."""
        config = self.loader.create_default_config("test")

        with patch.object(self.loader, 'get_active_config', return_value=config):
            path = self.loader.resolve_standard_path("test_standard", "production")

        self.assertEqual(path, "./ADRI/prod/standards/test_standard.yaml")


class TestConfigurationConvenienceFunctions(unittest.TestCase):
    """Test convenience functions for configuration."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        os.chdir(self.original_cwd)
        import shutil
        shutil.rmtree(self.temp_dir)

    @patch('adri.config.loader.ConfigurationLoader')
    def test_load_adri_config(self, mock_loader_class):
        """Test load_adri_config convenience function."""
        mock_loader = Mock()
        mock_config = {"adri": {"project_name": "test"}}
        mock_loader.get_active_config.return_value = mock_config
        mock_loader_class.return_value = mock_loader

        result = load_adri_config("test-config.yaml")

        self.assertEqual(result, mock_config)
        mock_loader.get_active_config.assert_called_once_with("test-config.yaml")

    @patch('adri.config.loader.ConfigurationLoader')
    def test_get_protection_settings(self, mock_loader_class):
        """Test get_protection_settings convenience function."""
        mock_loader = Mock()
        mock_settings = {"default_min_score": 85}
        mock_loader.get_protection_config.return_value = mock_settings
        mock_loader_class.return_value = mock_loader

        result = get_protection_settings("production")

        self.assertEqual(result, mock_settings)
        mock_loader.get_protection_config.assert_called_once_with("production")

    @patch('adri.config.loader.ConfigurationLoader')
    def test_resolve_standard_file(self, mock_loader_class):
        """Test resolve_standard_file convenience function."""
        mock_loader = Mock()
        mock_path = "./ADRI/prod/standards/test.yaml"
        mock_loader.resolve_standard_path.return_value = mock_path
        mock_loader_class.return_value = mock_loader

        result = resolve_standard_file("test", "production")

        self.assertEqual(result, mock_path)
        mock_loader.resolve_standard_path.assert_called_once_with("test", "production")


if __name__ == '__main__':
    unittest.main()
