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
from src.adri.config.loader import (
    ConfigurationLoader,
    load_adri_config,
    get_protection_settings,
    resolve_contract_file
)


class TestConfigurationLoader(unittest.TestCase):
    """Test the ConfigurationLoader class."""

    def setUp(self):
        """Set up test fixtures."""
        self.loader = ConfigurationLoader()
        self.temp_dir = tempfile.mkdtemp()
        # Robust directory handling for CI environments
        try:
            self.original_cwd = os.getcwd()
        except (OSError, FileNotFoundError):
            # Fallback to absolute path of project root if current dir doesn't exist
            self.original_cwd = str(Path(__file__).parent.parent.absolute())

        # Ensure temp directory exists and is accessible
        os.makedirs(self.temp_dir, exist_ok=True)
        os.chdir(self.temp_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        try:
            # Safely change back to original directory
            if os.path.exists(self.original_cwd):
                os.chdir(self.original_cwd)
            else:
                # Fallback to a safe directory if original doesn't exist
                os.chdir(str(Path(__file__).parent.parent.absolute()))
        except (OSError, FileNotFoundError):
            # If all else fails, go to a known safe directory
            os.chdir("/tmp" if os.path.exists("/tmp") else ".")

        # Clean up temp directory safely
        try:
            import shutil
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir, ignore_errors=True)
        except (OSError, PermissionError):
            # Ignore cleanup errors in CI environments
            pass

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
        adri_dir = Path("ADRI")
        adri_dir.mkdir(parents=True, exist_ok=True)
        config_file = adri_dir / "config.yaml"
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write("test: config")

        found_path = self.loader.find_config_file()
        expected_path = str(Path.cwd().resolve() / "ADRI" / "config.yaml")

        # Normalize both paths to resolve Windows short vs long path names
        found_normalized = str(Path(found_path).resolve()) if found_path else None
        expected_normalized = str(Path(expected_path).resolve())

        self.assertEqual(found_normalized, expected_normalized)

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
        adri_dir = Path("ADRI")
        adri_dir.mkdir(parents=True, exist_ok=True)
        self.loader.save_config(config, str(adri_dir / "config.yaml"))

        active_config = self.loader.get_active_config()
        self.assertEqual(active_config["adri"]["project_name"], "test")

    def test_get_environment_config_default(self):
        """Test getting environment config for default environment."""
        config = self.loader.create_default_config("test")
        env_config = self.loader.get_environment_config(config)

        # Should return development environment (default)
        self.assertIn("paths", env_config)
        self.assertEqual(env_config["paths"]["contracts"], "./ADRI/dev/contracts")

    def test_get_environment_config_specific(self):
        """Test getting environment config for specific environment."""
        config = self.loader.create_default_config("test")
        env_config = self.loader.get_environment_config(config, "production")

        self.assertIn("paths", env_config)
        self.assertEqual(env_config["paths"]["contracts"], "./ADRI/prod/contracts")

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

class TestConfigurationConvenienceFunctions(unittest.TestCase):
    """Test convenience functions for configuration."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        # Robust directory handling for CI environments
        try:
            self.original_cwd = os.getcwd()
        except (OSError, FileNotFoundError):
            # Fallback to absolute path of project root if current dir doesn't exist
            self.original_cwd = str(Path(__file__).parent.parent.absolute())

        # Ensure temp directory exists and is accessible
        os.makedirs(self.temp_dir, exist_ok=True)
        os.chdir(self.temp_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        try:
            # Safely change back to original directory
            if os.path.exists(self.original_cwd):
                os.chdir(self.original_cwd)
            else:
                # Fallback to a safe directory if original doesn't exist
                os.chdir(str(Path(__file__).parent.parent.absolute()))
        except (OSError, FileNotFoundError):
            # If all else fails, go to a known safe directory
            os.chdir("/tmp" if os.path.exists("/tmp") else ".")

        # Clean up temp directory safely
        try:
            import shutil
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir, ignore_errors=True)
        except (OSError, PermissionError):
            # Ignore cleanup errors in CI environments
            pass

    @patch('src.adri.config.loader.ConfigurationLoader')
    def test_load_adri_config(self, mock_loader_class):
        """Test load_adri_config convenience function."""
        mock_loader = Mock()
        mock_config = {"adri": {"project_name": "test"}}
        mock_loader.get_active_config.return_value = mock_config
        mock_loader_class.return_value = mock_loader

        result = load_adri_config("test-config.yaml")

        self.assertEqual(result, mock_config)
        mock_loader.get_active_config.assert_called_once_with("test-config.yaml")

    @patch('src.adri.config.loader.ConfigurationLoader')
    def test_get_protection_settings(self, mock_loader_class):
        """Test get_protection_settings convenience function."""
        mock_loader = Mock()
        mock_settings = {"default_min_score": 85}
        mock_loader.get_protection_config.return_value = mock_settings
        mock_loader_class.return_value = mock_loader

        result = get_protection_settings("production")

        self.assertEqual(result, mock_settings)
        mock_loader.get_protection_config.assert_called_once_with("production")

    @patch('src.adri.config.loader.ConfigurationLoader')
    def test_resolve_contract_file(self, mock_loader_class):
        """Test resolve_contract_file convenience function."""
        mock_loader = Mock()
        mock_path = "./ADRI/prod/contracts/test.yaml"
        mock_loader.resolve_contract_path.return_value = mock_path
        mock_loader_class.return_value = mock_loader

        result = resolve_contract_file("test", "production")

        self.assertEqual(result, mock_path)
        mock_loader.resolve_contract_path.assert_called_once_with("test", "production")


# ============================================================================
# Consolidated Tests (from test_config_loader.py and test_config_loader_comprehensive.py)
# ============================================================================


def safe_rmtree(path):
    """Windows-safe recursive directory removal."""
    if not os.path.exists(path):
        return

    import shutil
    import platform
    import time
    import gc

    def handle_remove_readonly(func, path, exc):
        """Error handler for Windows readonly file issues."""
        if os.path.exists(path):
            os.chmod(path, 0o777)
            func(path)

    # Multiple cleanup attempts
    for attempt in range(3):
        try:
            if attempt > 0:
                time.sleep(0.1)
                gc.collect()
            shutil.rmtree(path, onerror=handle_remove_readonly)
            return
        except (PermissionError, OSError) as e:
            if attempt == 2:
                if platform.system() != "Windows":
                    raise


def normalize_path(path_str):
    """Normalize paths for cross-platform compatibility."""
    return str(Path(path_str)).replace('\\', '/')


class TestConfigLoaderIntegration(unittest.TestCase):
    """Test complete configuration loading workflow integration."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)

    def tearDown(self):
        """Clean up test environment."""
        os.chdir(self.original_cwd)
        safe_rmtree(self.temp_dir)

    def test_complete_configuration_workflow(self):
        """Test end-to-end configuration creation, saving, and loading workflow."""
        loader = ConfigurationLoader()

        # Create and validate default config
        default_config = loader.create_default_config("integration_test_project")
        self.assertIn("adri", default_config)
        self.assertEqual(default_config["adri"]["project_name"], "integration_test_project")

        is_valid = loader.validate_config(default_config)
        self.assertTrue(is_valid)

        # Save and load
        config_file = "test_config.yaml"
        loader.save_config(default_config, config_file)
        self.assertTrue(Path(config_file).exists())

        loaded_config = loader.load_config(config_file)
        self.assertIsNotNone(loaded_config)
        self.assertEqual(loaded_config["adri"]["project_name"], "integration_test_project")

        # Create directory structure
        loader.create_directory_structure(loaded_config)

        expected_dirs = [
            "./ADRI/dev/contracts",
            "./ADRI/dev/assessments",
            "./ADRI/prod/contracts",
            "./ADRI/prod/assessments"
        ]

        for expected_dir in expected_dirs:
            self.assertTrue(Path(expected_dir).exists())

    def test_environment_configuration_workflow(self):
        """Test environment-specific configuration handling."""
        loader = ConfigurationLoader()

        config = {
            "adri": {
                "project_name": "multi_env_test",
                "version": "4.0.0",
                "default_environment": "staging",
                "environments": {
                    "development": {
                        "paths": {"contracts": "./dev/contracts", "assessments": "./dev/assessments", "training_data": "./dev/training"},
                        "protection": {"default_min_score": 70}
                    },
                    "staging": {
                        "paths": {"contracts": "./staging/standards", "assessments": "./staging/assessments", "training_data": "./staging/training"},
                        "protection": {"default_min_score": 80}
                    },
                    "production": {
                        "paths": {"contracts": "./prod/contracts", "assessments": "./prod/assessments", "training_data": "./prod/training"},
                        "protection": {"default_min_score": 90}
                    }
                }
            }
        }

        dev_config = loader.get_environment_config(config, "development")
        self.assertEqual(dev_config["protection"]["default_min_score"], 70)

        staging_config = loader.get_environment_config(config, "staging")
        self.assertEqual(staging_config["protection"]["default_min_score"], 80)


class TestConfigLoaderErrorHandling(unittest.TestCase):
    """Test comprehensive error handling scenarios."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)

    def tearDown(self):
        """Clean up test environment."""
        os.chdir(self.original_cwd)
        safe_rmtree(self.temp_dir)

    def test_invalid_configuration_structures(self):
        """Test validation of invalid configuration structures."""
        loader = ConfigurationLoader()

        invalid_configs = [
            {"project_name": "test"},  # Missing adri section
            {"adri": {"version": "4.0.0"}},  # Missing project_name
            {"adri": {"project_name": "test", "version": "4.0.0", "default_environment": "dev"}},  # Missing environments
        ]

        for invalid_config in invalid_configs:
            is_valid = loader.validate_config(invalid_config)
            self.assertFalse(is_valid)

    def test_file_operation_error_handling(self):
        """Test error handling for file operation failures."""
        loader = ConfigurationLoader()

        # Test loading non-existent file
        result = loader.load_config("nonexistent_config.yaml")
        self.assertIsNone(result)

        # Test loading corrupted YAML
        corrupted_file = "corrupted_config.yaml"
        with open(corrupted_file, 'w', encoding='utf-8') as f:
            f.write("invalid: yaml: content: [unclosed")

        result = loader.load_config(corrupted_file)
        self.assertIsNone(result)

    def test_missing_environment_error_handling(self):
        """Test error handling for missing environments."""
        loader = ConfigurationLoader()

        config = {
            "adri": {
                "project_name": "missing_env_test",
                "version": "4.0.0",
                "default_environment": "development",
                "environments": {
                    "development": {
                        "paths": {"contracts": "./dev/contracts", "assessments": "./dev/assessments", "training_data": "./dev/training"}
                    }
                }
            }
        }

        # Test accessing non-existent environment
        with self.assertRaises(ValueError) as cm:
            loader.get_environment_config(config, "nonexistent")
        self.assertIn("Environment 'nonexistent' not found", str(cm.exception))


if __name__ == '__main__':
    unittest.main()
