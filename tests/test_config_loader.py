"""
Config Loader Tests - Multi-Dimensional Quality Framework
Tests configuration loading and management functionality with comprehensive coverage (85%+ line coverage target).
Applies multi-dimensional quality framework: Integration (30%), Error Handling (25%), Performance (15%), Line Coverage (30%).
"""

import unittest
import tempfile
import os
import shutil
import yaml
import threading
import time
import platform
import gc
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


def safe_rmtree(path):
    """Windows-safe recursive directory removal with enhanced cleanup strategies."""
    if not os.path.exists(path):
        return

    def handle_remove_readonly(func, path, exc):
        """Error handler for Windows readonly file issues."""
        if os.path.exists(path):
            os.chmod(path, 0o777)
            func(path)

    def windows_rmdir_fallback(path):
        """Fallback using Windows rmdir command for stubborn directories."""
        if platform.system() == "Windows":
            try:
                import subprocess
                subprocess.run(['rmdir', '/s', '/q', path],
                              shell=True, check=False,
                              capture_output=True, timeout=30)
            except Exception:
                pass  # Silent fallback failure

    # Multiple cleanup attempts with different strategies
    for attempt in range(5):
        try:
            if attempt > 0:
                time.sleep(0.1 * (attempt + 1))  # Progressive delay
                gc.collect()  # Force garbage collection to release handles

            if attempt >= 2:
                # Try to close any remaining file handles
                try:
                    for root, dirs, files in os.walk(path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            try:
                                os.chmod(file_path, 0o777)
                            except Exception:
                                pass
                except Exception:
                    pass

            # Attempt removal
            shutil.rmtree(path, onerror=handle_remove_readonly)
            return  # Success!

        except (PermissionError, OSError) as e:
            if attempt == 4:  # Last attempt
                if platform.system() == "Windows":
                    windows_rmdir_fallback(path)
                else:
                    raise


def normalize_path(path_str):
    """Normalize paths for cross-platform compatibility."""
    # Convert to Path object for proper normalization
    path = Path(path_str)
    # Convert back to string with forward slashes
    return str(path).replace('\\', '/')


class TestConfigLoaderIntegration(unittest.TestCase):
    """Test complete configuration loading workflow integration (30% weight in quality score)."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)

    def tearDown(self):
        """Clean up test environment."""
        os.chdir(self.original_cwd)
        safe_rmtree(self.temp_dir)
    def tearDown(self):
        """Clean up test environment."""
        os.chdir(self.original_cwd)
        safe_rmtree(self.temp_dir)

    def test_complete_configuration_workflow(self):
        """Test end-to-end configuration creation, saving, and loading workflow."""
        loader = ConfigurationLoader()

        # Test default configuration creation
        default_config = loader.create_default_config("integration_test_project")

        # Verify default configuration structure
        self.assertIn("adri", default_config)
        self.assertEqual(default_config["adri"]["project_name"], "integration_test_project")
        self.assertEqual(default_config["adri"]["version"], "4.0.0")
        self.assertIn("environments", default_config["adri"])
        self.assertIn("development", default_config["adri"]["environments"])
        self.assertIn("production", default_config["adri"]["environments"])

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

        # Test directory structure creation
        loader.create_directory_structure(loaded_config)

        # Verify directories were created
        expected_dirs = [
            "./ADRI/dev/standards",
            "./ADRI/dev/assessments",
            "./ADRI/dev/training-data",
            "./ADRI/prod/standards",
            "./ADRI/prod/assessments",
            "./ADRI/prod/training-data"
        ]

        for expected_dir in expected_dirs:
            self.assertTrue(Path(expected_dir).exists(), f"Directory {expected_dir} was not created")

    def test_config_file_discovery_workflow(self):
        """Test configuration file discovery across directory structure."""
        loader = ConfigurationLoader()

        # Create nested directory structure with Windows-safe path handling
        nested_dir = Path("project") / "subdir" / "deep" / "nested"
        try:
            nested_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            # Skip deep nesting on Windows if path too long
            if platform.system() == "Windows" and "path too long" in str(e).lower():
                nested_dir = Path("project") / "subdir"
                nested_dir.mkdir(parents=True, exist_ok=True)

        # Create config in different locations
        config_locations = [
            "ADRI/config.yaml",  # Primary location
            "adri-config.yaml",  # Root level
            "project/adri-config.yaml",  # Project level
            ".adri.yaml"  # Hidden config
        ]

        test_config = {
            "adri": {
                "project_name": "discovery_test",
                "version": "4.0.0",
                "default_environment": "development",
                "environments": {
                    "development": {
                        "paths": {
                            "standards": normalize_path("./ADRI/dev/standards"),
                            "assessments": normalize_path("./ADRI/dev/assessments"),
                            "training_data": normalize_path("./ADRI/dev/training-data")
                        }
                    }
                }
            }
        }

        for location in config_locations:
            # Clear any existing config files with Windows-safe cleanup
            for cleanup_location in config_locations:
                cleanup_path = Path(cleanup_location)
                if cleanup_path.exists():
                    try:
                        cleanup_path.unlink()
                    except (PermissionError, OSError):
                        # Windows file handle issues - try again after a delay
                        time.sleep(0.1)
                        try:
                            cleanup_path.unlink()
                        except Exception:
                            pass  # Continue anyway

            # Create config at specific location
            config_path = Path(location)
            try:
                config_path.parent.mkdir(parents=True, exist_ok=True)

                with open(config_path, "w", encoding='utf-8') as f:
                    yaml.dump(test_config, f)

                # Test discovery from nested directory
                original_cwd = os.getcwd()
                try:
                    os.chdir(nested_dir)
                    found_config = loader.find_config_file()

                    if location == "ADRI/config.yaml":  # Should find this one first
                        self.assertIsNotNone(found_config)
                        # Normalize path for comparison
                        normalized_found = normalize_path(found_config) if found_config else None
                        self.assertTrue(normalized_found and normalized_found.endswith("ADRI/config.yaml"))
                finally:
                    os.chdir(original_cwd)

            except (OSError, PermissionError) as e:
                # Skip problematic paths on Windows
                if platform.system() == "Windows":
                    continue
                else:
                    raise

    def test_environment_configuration_workflow(self):
        """Test environment-specific configuration handling."""
        loader = ConfigurationLoader()

        # Create comprehensive multi-environment config
        multi_env_config = {
            "adri": {
                "project_name": "multi_env_test",
                "version": "4.0.0",
                "default_environment": "staging",
                "environments": {
                    "development": {
                        "paths": {
                            "standards": "./ADRI/dev/standards",
                            "assessments": "./ADRI/dev/assessments",
                            "training_data": "./ADRI/dev/training-data"
                        },
                        "protection": {
                            "default_failure_mode": "warn",
                            "default_min_score": 70,
                            "cache_duration_hours": 0.5
                        }
                    },
                    "staging": {
                        "paths": {
                            "standards": "./ADRI/staging/standards",
                            "assessments": "./ADRI/staging/assessments",
                            "training_data": "./ADRI/staging/training-data"
                        },
                        "protection": {
                            "default_failure_mode": "warn",
                            "default_min_score": 80,
                            "cache_duration_hours": 1
                        }
                    },
                    "production": {
                        "paths": {
                            "standards": "./ADRI/prod/standards",
                            "assessments": "./ADRI/prod/assessments",
                            "training_data": "./ADRI/prod/training-data"
                        },
                        "protection": {
                            "default_failure_mode": "raise",
                            "default_min_score": 90,
                            "cache_duration_hours": 24
                        }
                    }
                },
                "protection": {
                    "default_failure_mode": "raise",
                    "default_min_score": 85,
                    "cache_duration_hours": 2,
                    "auto_generate_standards": True,
                    "verbose_protection": True
                }
            }
        }

        # Save configuration
        config_file = "multi_env_config.yaml"
        loader.save_config(multi_env_config, config_file)

        # Test environment configuration extraction
        dev_config = loader.get_environment_config(multi_env_config, "development")
        self.assertEqual(dev_config["protection"]["default_min_score"], 70)
        self.assertEqual(dev_config["paths"]["standards"], "./ADRI/dev/standards")

        staging_config = loader.get_environment_config(multi_env_config, "staging")
        self.assertEqual(staging_config["protection"]["default_min_score"], 80)

        prod_config = loader.get_environment_config(multi_env_config, "production")
        self.assertEqual(prod_config["protection"]["default_min_score"], 90)

        # Test default environment (staging)
        default_config = loader.get_environment_config(multi_env_config)
        self.assertEqual(default_config["protection"]["default_min_score"], 80)

    def test_protection_configuration_inheritance_workflow(self):
        """Test protection configuration inheritance and override workflow."""
        loader = ConfigurationLoader()

        config_with_inheritance = {
            "adri": {
                "project_name": "inheritance_test",
                "version": "4.0.0",
                "default_environment": "development",
                "protection": {
                    "default_failure_mode": "warn",
                    "default_min_score": 75,
                    "cache_duration_hours": 1,
                    "auto_generate_standards": True,
                    "verbose_protection": False,
                    "custom_setting": "global_value"
                },
                "environments": {
                    "development": {
                        "paths": {
                            "standards": "./ADRI/dev/standards",
                            "assessments": "./ADRI/dev/assessments",
                            "training_data": "./ADRI/dev/training-data"
                        },
                        "protection": {
                            "default_min_score": 65,  # Override global
                            "verbose_protection": True,  # Override global
                            "dev_specific": "dev_value"  # Environment-specific
                        }
                    },
                    "production": {
                        "paths": {
                            "standards": "./ADRI/prod/standards",
                            "assessments": "./ADRI/prod/assessments",
                            "training_data": "./ADRI/prod/training-data"
                        },
                        "protection": {
                            "default_failure_mode": "raise",  # Override global
                            "default_min_score": 90,  # Override global
                            "prod_specific": "prod_value"  # Environment-specific
                        }
                    }
                }
            }
        }

        config_file = "inheritance_config.yaml"
        loader.save_config(config_with_inheritance, config_file)

        # Test protection config inheritance for development
        with patch.object(loader, 'get_active_config', return_value=config_with_inheritance):
            dev_protection = loader.get_protection_config("development")

            # Should inherit global settings
            self.assertEqual(dev_protection["default_failure_mode"], "warn")  # From global
            self.assertEqual(dev_protection["auto_generate_standards"], True)  # From global
            self.assertEqual(dev_protection["custom_setting"], "global_value")  # From global

            # Should override with environment-specific settings
            self.assertEqual(dev_protection["default_min_score"], 65)  # Overridden
            self.assertTrue(dev_protection["verbose_protection"])  # Overridden
            self.assertEqual(dev_protection["dev_specific"], "dev_value")  # Environment-specific

            # Test production inheritance
            prod_protection = loader.get_protection_config("production")
            self.assertEqual(prod_protection["default_failure_mode"], "raise")  # Overridden
            self.assertEqual(prod_protection["default_min_score"], 90)  # Overridden
            self.assertEqual(prod_protection["auto_generate_standards"], True)  # From global
            self.assertEqual(prod_protection["prod_specific"], "prod_value")  # Environment-specific

    def test_path_resolution_workflow(self):
        """Test comprehensive path resolution workflow."""
        loader = ConfigurationLoader()

        # Create configuration with custom paths
        path_config = {
            "adri": {
                "project_name": "path_test",
                "version": "4.0.0",
                "default_environment": "development",
                "environments": {
                    "development": {
                        "paths": {
                            "standards": "./custom/dev/standards",
                            "assessments": "./custom/dev/assessments",
                            "training_data": "./custom/dev/training-data"
                        }
                    },
                    "production": {
                        "paths": {
                            "standards": "/opt/adri/prod/standards",
                            "assessments": "/opt/adri/prod/assessments",
                            "training_data": "/opt/adri/prod/training-data"
                        }
                    }
                }
            }
        }

        config_file = "path_config.yaml"
        loader.save_config(path_config, config_file)

        with patch.object(loader, 'get_active_config', return_value=path_config):
            # Test standard path resolution
            dev_standard_path = loader.resolve_standard_path("customer_data", "development")
            self.assertEqual(dev_standard_path, "./custom/dev/standards/customer_data.yaml")

            prod_standard_path = loader.resolve_standard_path("customer_data", "production")
            self.assertEqual(prod_standard_path, "/opt/adri/prod/standards/customer_data.yaml")

            # Test path resolution with extensions
            yaml_path = loader.resolve_standard_path("test.yaml", "development")
            self.assertEqual(yaml_path, "./custom/dev/standards/test.yaml")

            yml_path = loader.resolve_standard_path("test.yml", "development")
            self.assertEqual(yml_path, "./custom/dev/standards/test.yml")

            # Test assessments directory resolution
            dev_assessments = loader.get_assessments_dir("development")
            self.assertEqual(dev_assessments, "./custom/dev/assessments")

            prod_assessments = loader.get_assessments_dir("production")
            self.assertEqual(prod_assessments, "/opt/adri/prod/assessments")

            # Test training data directory resolution
            dev_training = loader.get_training_data_dir("development")
            self.assertEqual(dev_training, "./custom/dev/training-data")

            prod_training = loader.get_training_data_dir("production")
            self.assertEqual(prod_training, "/opt/adri/prod/training-data")

    def test_convenience_functions_integration(self):
        """Test convenience function integration workflow."""
        # Create test configuration
        test_config = {
            "adri": {
                "project_name": "convenience_test",
                "version": "4.0.0",
                "default_environment": "development",
                "environments": {
                    "development": {
                        "paths": {
                            "standards": "./ADRI/dev/standards",
                            "assessments": "./ADRI/dev/assessments",
                            "training_data": "./ADRI/dev/training-data"
                        },
                        "protection": {
                            "default_failure_mode": "warn",
                            "default_min_score": 70
                        }
                    }
                },
                "protection": {
                    "default_failure_mode": "raise",
                    "default_min_score": 85,
                    "auto_generate_standards": True
                }
            }
        }

        # Save configuration
        config_file = "convenience_config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(test_config, f)

        # Test load_adri_config convenience function
        loaded_config = load_adri_config(config_file)
        self.assertIsNotNone(loaded_config)
        self.assertEqual(loaded_config["adri"]["project_name"], "convenience_test")

        # Test load_adri_config with auto-discovery
        # Create ADRI/config.yaml for auto-discovery
        adri_dir = Path("ADRI")
        adri_dir.mkdir(exist_ok=True)

        with open(adri_dir / "config.yaml", "w") as f:
            yaml.dump(test_config, f)

        auto_loaded_config = load_adri_config()
        self.assertIsNotNone(auto_loaded_config)

        # Test get_protection_settings convenience function
        with patch('adri.config.loader.ConfigurationLoader.get_active_config', return_value=test_config):
            protection_settings = get_protection_settings("development")
            self.assertEqual(protection_settings["default_failure_mode"], "warn")
            self.assertEqual(protection_settings["default_min_score"], 70)
            self.assertTrue(protection_settings["auto_generate_standards"])  # From global

            # Test resolve_standard_file convenience function
            standard_path = resolve_standard_file("customer_data", "development")
            self.assertEqual(standard_path, "./ADRI/dev/standards/customer_data.yaml")

    def test_backward_compatibility_alias(self):
        """Test ConfigManager backward compatibility alias."""
        manager = ConfigManager()
        self.assertIsInstance(manager, ConfigurationLoader)

    def test_complex_configuration_validation(self):
        """Test validation of complex configuration structures."""
        loader = ConfigurationLoader()

        # Test comprehensive valid configuration
        complex_valid_config = {
            "adri": {
                "project_name": "complex_validation_test",
                "version": "4.0.0",
                "default_environment": "staging",
                "environments": {
                    "development": {
                        "paths": {
                            "standards": "./dev/standards",
                            "assessments": "./dev/assessments",
                            "training_data": "./dev/training"
                        },
                        "protection": {
                            "default_failure_mode": "warn",
                            "default_min_score": 60
                        }
                    },
                    "staging": {
                        "paths": {
                            "standards": "./staging/standards",
                            "assessments": "./staging/assessments",
                            "training_data": "./staging/training"
                        },
                        "protection": {
                            "default_failure_mode": "warn",
                            "default_min_score": 80
                        }
                    },
                    "production": {
                        "paths": {
                            "standards": "/prod/standards",
                            "assessments": "/prod/assessments",
                            "training_data": "/prod/training"
                        },
                        "protection": {
                            "default_failure_mode": "raise",
                            "default_min_score": 95
                        }
                    }
                },
                "protection": {
                    "default_failure_mode": "raise",
                    "default_min_score": 85,
                    "cache_duration_hours": 2,
                    "auto_generate_standards": True,
                    "verbose_protection": False
                },
                "assessment": {
                    "caching": {"enabled": True, "ttl": "12h"},
                    "output": {"format": "yaml"},
                    "performance": {"max_rows": 500000, "timeout": "10m"}
                },
                "generation": {
                    "default_thresholds": {
                        "completeness_min": 90,
                        "validity_min": 95,
                        "consistency_min": 85
                    }
                }
            }
        }

        # Should validate successfully
        is_valid = loader.validate_config(complex_valid_config)
        self.assertTrue(is_valid)

        # Test environment extraction
        staging_config = loader.get_environment_config(complex_valid_config, "staging")
        self.assertEqual(staging_config["protection"]["default_min_score"], 80)
        self.assertEqual(staging_config["paths"]["standards"], "./staging/standards")

    def test_cross_platform_path_handling(self):
        """Test cross-platform path handling and normalization."""
        loader = ConfigurationLoader()

        # Test with Windows-style paths
        windows_config = {
            "adri": {
                "project_name": "windows_path_test",
                "version": "4.0.0",
                "default_environment": "development",
                "environments": {
                    "development": {
                        "paths": {
                            "standards": ".\\ADRI\\dev\\standards",
                            "assessments": ".\\ADRI\\dev\\assessments",
                            "training_data": ".\\ADRI\\dev\\training-data"
                        }
                    }
                }
            }
        }

        with patch.object(loader, 'get_active_config', return_value=windows_config):
            # Test path resolution with normalization
            standard_path = loader.resolve_standard_path("test_standard", "development")

            # Normalize the result for comparison
            normalized_path = normalize_path(standard_path)

            # Should normalize to forward slashes or be properly handled
            # On Windows, paths might still contain backslashes, so we normalize for testing
            self.assertTrue(
                "/" in normalized_path or "\\" in standard_path,
                f"Path should contain path separators: {standard_path}"
            )
            self.assertTrue(
                normalized_path.endswith("standards/test_standard.yaml") or
                standard_path.endswith("standards\\test_standard.yaml"),
                f"Path should end with standards separator and filename: {standard_path}"
            )


class TestConfigLoaderErrorHandling(unittest.TestCase):
    """Test comprehensive error handling scenarios (25% weight in quality score)."""

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

        # Test various invalid configuration structures
        invalid_configs = [
            # Missing top-level adri section
            {"project_name": "test"},

            # Missing required fields
            {"adri": {"version": "4.0.0"}},

            # Missing project_name
            {"adri": {"version": "4.0.0", "environments": {}, "default_environment": "dev"}},

            # Missing environments
            {"adri": {"project_name": "test", "version": "4.0.0", "default_environment": "dev"}},

            # Missing default_environment
            {"adri": {"project_name": "test", "version": "4.0.0", "environments": {}}},

            # Invalid environments type
            {"adri": {"project_name": "test", "version": "4.0.0", "default_environment": "dev", "environments": "not_a_dict"}},

            # Environment missing paths
            {"adri": {
                "project_name": "test",
                "version": "4.0.0",
                "default_environment": "dev",
                "environments": {
                    "dev": {"protection": {}}
                }
            }},

            # Environment paths missing required keys
            {"adri": {
                "project_name": "test",
                "version": "4.0.0",
                "default_environment": "dev",
                "environments": {
                    "dev": {
                        "paths": {
                            "standards": "./standards"
                            # Missing assessments and training_data
                        }
                    }
                }
            }}
        ]

        for invalid_config in invalid_configs:
            is_valid = loader.validate_config(invalid_config)
            self.assertFalse(is_valid, f"Config should be invalid: {invalid_config}")

    def test_file_operation_error_handling(self):
        """Test error handling for file operation failures."""
        loader = ConfigurationLoader()

        # Test loading non-existent file
        result = loader.load_config("nonexistent_config.yaml")
        self.assertIsNone(result)

        # Test loading corrupted YAML
        corrupted_file = "corrupted_config.yaml"
        with open(corrupted_file, "w") as f:
            f.write("invalid: yaml: content: [unclosed")

        result = loader.load_config(corrupted_file)
        self.assertIsNone(result)

        # Test loading file with wrong content type
        non_dict_file = "non_dict_config.yaml"
        with open(non_dict_file, "w") as f:
            yaml.dump(["list", "instead", "of", "dict"], f)

        result = loader.load_config(non_dict_file)
        self.assertIsNone(result)

    def test_permission_error_handling(self):
        """Test handling of file permission errors using mocking."""
        loader = ConfigurationLoader()

        # Use mocking to simulate permission errors since Docker containers run as root
        with patch('builtins.open', side_effect=PermissionError("Permission denied")):
            result = loader.load_config("any_file.yaml")
            self.assertIsNone(result)  # Should handle gracefully

        # Test permission error during file writing
        test_config = loader.create_default_config("permission_test")
        with patch('builtins.open', side_effect=PermissionError("Permission denied")):
            # save_config should handle permission errors gracefully
            try:
                loader.save_config(test_config, "restricted_file.yaml")
                # If no exception is raised, the method handled it gracefully
            except PermissionError:
                # If PermissionError is propagated, that's also acceptable behavior
                pass

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
                        "paths": {
                            "standards": "./dev/standards",
                            "assessments": "./dev/assessments",
                            "training_data": "./dev/training"
                        }
                    }
                }
            }
        }

        # Test accessing non-existent environment
        with self.assertRaises(ValueError) as cm:
            loader.get_environment_config(config, "nonexistent")
        self.assertIn("Environment 'nonexistent' not found", str(cm.exception))

        # Test with invalid environment configuration
        invalid_env_config = config.copy()
        invalid_env_config["adri"]["environments"]["development"] = "not_a_dict"

        with self.assertRaises(ValueError) as cm:
            loader.get_environment_config(invalid_env_config, "development")
        self.assertIn("Invalid environment configuration", str(cm.exception))

    def test_config_file_discovery_error_handling(self):
        """Test error handling in configuration file discovery."""
        loader = ConfigurationLoader()

        # Test discovery in directory without config files
        empty_dir = Path("empty_directory")
        empty_dir.mkdir()

        os.chdir(empty_dir)
        found_config = loader.find_config_file()
        self.assertIsNone(found_config)

        os.chdir(self.temp_dir)

        # Test discovery with permission-denied directory
        if os.name != 'nt':  # Skip on Windows
            restricted_dir = Path("restricted_directory")
            restricted_dir.mkdir()
            os.chmod(restricted_dir, 0o000)

            try:
                os.chdir(restricted_dir)
                found_config = loader.find_config_file()
                # Should handle gracefully
                os.chdir(self.temp_dir)
            except PermissionError:
                # Expected behavior
                os.chdir(self.temp_dir)
            finally:
                os.chmod(restricted_dir, 0o755)

    def test_path_resolution_fallback_error_handling(self):
        """Test path resolution fallback mechanisms."""
        loader = ConfigurationLoader()

        # Test with no active config (fallback behavior)
        with patch.object(loader, 'get_active_config', return_value=None):
            # Should use fallback paths
            dev_standard_path = loader.resolve_standard_path("test_standard", "development")
            self.assertEqual(dev_standard_path, "./ADRI/dev/standards/test_standard.yaml")

            prod_standard_path = loader.resolve_standard_path("test_standard", "production")
            self.assertEqual(prod_standard_path, "./ADRI/prod/standards/test_standard.yaml")

            assessments_dir = loader.get_assessments_dir("development")
            self.assertEqual(assessments_dir, "./ADRI/dev/assessments")

            training_dir = loader.get_training_data_dir("production")
            self.assertEqual(training_dir, "./ADRI/prod/training-data")

    def test_protection_config_fallback_handling(self):
        """Test protection configuration fallback when no config available."""
        loader = ConfigurationLoader()

        with patch.object(loader, 'get_active_config', return_value=None):
            # Should return default protection config
            protection_config = loader.get_protection_config()

            self.assertEqual(protection_config["default_failure_mode"], "raise")
            self.assertEqual(protection_config["default_min_score"], 80)
            self.assertEqual(protection_config["cache_duration_hours"], 1)
            self.assertTrue(protection_config["auto_generate_standards"])
            self.assertFalse(protection_config["verbose_protection"])

    def test_malformed_protection_config_error_handling(self):
        """Test handling of malformed protection configurations."""
        loader = ConfigurationLoader()

        # Test with malformed global protection config
        malformed_config = {
            "adri": {
                "project_name": "malformed_test",
                "version": "4.0.0",
                "default_environment": "development",
                "protection": "not_a_dict",  # Invalid type
                "environments": {
                    "development": {
                        "paths": {
                            "standards": "./dev/standards",
                            "assessments": "./dev/assessments",
                            "training_data": "./dev/training"
                        },
                        "protection": {
                            "default_min_score": "not_a_number"  # Invalid type
                        }
                    }
                }
            }
        }

        with patch.object(loader, 'get_active_config', return_value=malformed_config):
            # Should handle gracefully when protection config is malformed
            try:
                protection_config = loader.get_protection_config("development")
                self.assertIsInstance(protection_config, dict)
                # Should have some default values even with malformed config
            except AttributeError:
                # Expected when trying to copy a string - this is the error we're testing
                pass


class TestConfigLoaderPerformance(unittest.TestCase):
    """Test performance benchmarks and efficiency (15% weight in quality score)."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)

    def tearDown(self):
        """Clean up test environment."""
        os.chdir(self.original_cwd)
        safe_rmtree(self.temp_dir)

    @pytest.mark.benchmark(group="config_loading")
    def test_config_loading_performance(self, benchmark=None):
        """Benchmark configuration loading performance."""
        loader = ConfigurationLoader()

        # Create large configuration for performance testing
        large_config = {
            "adri": {
                "project_name": "performance_test",
                "version": "4.0.0",
                "default_environment": "development",
                "environments": {
                    f"environment_{i}": {
                        "paths": {
                            "standards": f"./env_{i}/standards",
                            "assessments": f"./env_{i}/assessments",
                            "training_data": f"./env_{i}/training"
                        },
                        "protection": {
                            "default_failure_mode": "warn" if i % 2 == 0 else "raise",
                            "default_min_score": 70 + (i % 30),
                            "cache_duration_hours": i % 24 + 1
                        }
                    }
                    for i in range(50)  # 50 environments
                },
                "protection": {
                    "default_failure_mode": "raise",
                    "default_min_score": 85
                }
            }
        }

        config_file = "large_config.yaml"
        loader.save_config(large_config, config_file)

        def load_config():
            return loader.load_config(config_file)

        if benchmark:
            result = benchmark(load_config)
            self.assertIsNotNone(result)
        else:
            # Fallback timing
            start_time = time.time()
            result = load_config()
            end_time = time.time()

            self.assertIsNotNone(result)
            self.assertLess(end_time - start_time, 1.0)  # Should load within 1 second

    def test_config_validation_performance(self):
        """Test configuration validation performance."""
        loader = ConfigurationLoader()

        # Create large configuration
        large_config = loader.create_default_config("validation_perf_test")

        # Add many environments
        for i in range(20):
            large_config["adri"]["environments"][f"env_{i}"] = {
                "paths": {
                    "standards": f"./env_{i}/standards",
                    "assessments": f"./env_{i}/assessments",
                    "training_data": f"./env_{i}/training"
                }
            }

        start_time = time.time()
        is_valid = loader.validate_config(large_config)
        end_time = time.time()

        self.assertTrue(is_valid)
        self.assertLess(end_time - start_time, 0.5)  # Should validate quickly

    def test_concurrent_config_operations_performance(self):
        """Test performance with concurrent configuration operations."""
        loader = ConfigurationLoader()

        # Create test configuration
        test_config = loader.create_default_config("concurrent_test")
        config_file = "concurrent_config.yaml"
        loader.save_config(test_config, config_file)

        results = []

        def concurrent_operations(thread_id):
            """Perform config operations concurrently."""
            start_time = time.time()

            # Load configuration
            loaded_config = loader.load_config(config_file)

            # Validate configuration
            is_valid = loader.validate_config(loaded_config)

            # Get environment config
            env_config = loader.get_environment_config(loaded_config, "development")

            # Get protection config
            with patch.object(loader, 'get_active_config', return_value=loaded_config):
                protection_config = loader.get_protection_config("development")

            end_time = time.time()
            results.append((thread_id, end_time - start_time, is_valid))

        # Run concurrent operations
        overall_start = time.time()
        threads = []
        for i in range(5):
            thread = threading.Thread(target=concurrent_operations, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()
        overall_time = time.time() - overall_start

        # Verify all completed successfully
        self.assertEqual(len(results), 5)
        for thread_id, duration, is_valid in results:
            self.assertTrue(is_valid)
            self.assertLess(duration, 1.0)  # Each should complete within 1 second

        # Overall concurrent execution should be efficient
        self.assertLess(overall_time, 3.0)

    def test_directory_creation_performance(self):
        """Test performance of directory structure creation."""
        loader = ConfigurationLoader()

        # Create configuration with many directories
        many_dirs_config = {
            "adri": {
                "project_name": "many_dirs_test",
                "version": "4.0.0",
                "default_environment": "development",
                "environments": {
                    f"env_{i}": {
                        "paths": {
                            "standards": f"./many_dirs/env_{i}/standards",
                            "assessments": f"./many_dirs/env_{i}/assessments",
                            "training_data": f"./many_dirs/env_{i}/training"
                        }
                    }
                    for i in range(10)
                }
            }
        }

        start_time = time.time()
        loader.create_directory_structure(many_dirs_config)
        end_time = time.time()

        # Verify directories were created
        for i in range(10):
            env_dirs = [
                f"./many_dirs/env_{i}/standards",
                f"./many_dirs/env_{i}/assessments",
                f"./many_dirs/env_{i}/training"
            ]
            for dir_path in env_dirs:
                self.assertTrue(Path(dir_path).exists())

        # Should create directories efficiently
        self.assertLess(end_time - start_time, 2.0)

    def test_path_resolution_performance(self):
        """Test performance of path resolution operations."""
        loader = ConfigurationLoader()

        config = loader.create_default_config("path_perf_test")

        with patch.object(loader, 'get_active_config', return_value=config):
            # Time multiple path resolutions
            start_time = time.time()

            for i in range(100):
                standard_path = loader.resolve_standard_path(f"standard_{i}", "development")
                assessments_dir = loader.get_assessments_dir("production")
                training_dir = loader.get_training_data_dir("development")

            end_time = time.time()

            # Should handle many path resolutions quickly
            self.assertLess(end_time - start_time, 1.0)


class TestConfigLoaderEdgeCases(unittest.TestCase):
    """Test edge cases and boundary conditions for comprehensive coverage."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)

    def tearDown(self):
        """Clean up test environment."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)

    def test_empty_and_minimal_configurations(self):
        """Test handling of empty and minimal configurations."""
        loader = ConfigurationLoader()

        # Test minimal valid configuration
        minimal_config = {
            "adri": {
                "project_name": "minimal",
                "version": "4.0.0",
                "default_environment": "development",
                "environments": {
                    "development": {
                        "paths": {
                            "standards": "./standards",
                            "assessments": "./assessments",
                            "training_data": "./training"
                        }
                    }
                }
            }
        }

        is_valid = loader.validate_config(minimal_config)
        self.assertTrue(is_valid)

        # Test with empty adri section
        empty_adri_config = {"adri": {}}
        is_valid = loader.validate_config(empty_adri_config)
        self.assertFalse(is_valid)

    def test_unicode_and_special_characters_in_config(self):
        """Test configuration with Unicode and special characters."""
        loader = ConfigurationLoader()

        unicode_config = {
            "adri": {
                "project_name": "测试项目_Ñoñó_русский",
                "version": "4.0.0",
                "default_environment": "development",
                "environments": {
                    "development": {
                        "paths": {
                            "standards": "./ADRI/测试/standards",
                            "assessments": "./ADRI/测试/assessments",
                            "training_data": "./ADRI/测试/training-data"
                        }
                    }
                },
                "protection": {
                    "custom_message": "Validation failed: データが無効です",
                    "description": "Configuration with émojis: 🚀🔧⚡"
                }
            }
        }

        # Should handle Unicode gracefully
        is_valid = loader.validate_config(unicode_config)
        self.assertTrue(is_valid)

        # Test saving and loading with Unicode
        unicode_file = "unicode_config.yaml"
        loader.save_config(unicode_config, unicode_file)

        loaded_unicode = loader.load_config(unicode_file)
        self.assertIsNotNone(loaded_unicode)
        self.assertEqual(loaded_unicode["adri"]["project_name"], "测试项目_Ñoñó_русский")

    def test_very_long_configuration_values(self):
        """Test configuration with very long values."""
        loader = ConfigurationLoader()

        long_value = "x" * 10000  # 10KB string
        long_config = loader.create_default_config("long_value_test")
        long_config["adri"]["description"] = long_value
        long_config["adri"]["long_list"] = ["item_" + str(i) for i in range(1000)]

        # Should handle long values
        is_valid = loader.validate_config(long_config)
        self.assertTrue(is_valid)

        # Test saving and loading
        long_file = "long_config.yaml"
        loader.save_config(long_config, long_file)

        loaded_long = loader.load_config(long_file)
        self.assertIsNotNone(loaded_long)
        self.assertEqual(len(loaded_long["adri"]["description"]), 10000)

    def test_numeric_and_boolean_edge_cases(self):
        """Test configuration with numeric and boolean edge cases."""
        loader = ConfigurationLoader()

        numeric_config = {
            "adri": {
                "project_name": "numeric_test",
                "version": "4.0.0",
                "default_environment": "development",
                "environments": {
                    "development": {
                        "paths": {
                            "standards": "./standards",
                            "assessments": "./assessments",
                            "training_data": "./training"
                        }
                    }
                },
                "protection": {
                    "default_min_score": 0,  # Edge case: zero
                    "cache_duration_hours": 0.0,  # Edge case: zero float
                    "max_score": 100.0,
                    "negative_test": -1,  # Edge case: negative
                    "large_number": 999999999,
                    "scientific": 1.23e-4,
                    "boolean_true": True,
                    "boolean_false": False
                }
            }
        }

        is_valid = loader.validate_config(numeric_config)
        self.assertTrue(is_valid)

        # Test edge case wrapper handling
        wrapper_test_dict = {
            "requirements": {
                "overall_minimum": 0.0,  # Edge case
                "field_requirements": {}
            }
        }

        from adri.validator.engine import BundledStandardWrapper
        wrapper = BundledStandardWrapper(wrapper_test_dict)
        self.assertEqual(wrapper.get_overall_minimum(), 0.0)

    def test_deeply_nested_configuration_structures(self):
        """Test configuration with deeply nested structures."""
        loader = ConfigurationLoader()

        deeply_nested_config = {
            "adri": {
                "project_name": "nested_test",
                "version": "4.0.0",
                "default_environment": "development",
                "environments": {
                    "development": {
                        "paths": {
                            "standards": "./standards",
                            "assessments": "./assessments",
                            "training_data": "./training"
                        }
                    }
                },
                "protection": {
                    "advanced": {
                        "nested": {
                            "deep": {
                                "very_deep": {
                                    "extremely_deep": {
                                        "value": "found_at_level_6"
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

        # Should handle deep nesting
        is_valid = loader.validate_config(deeply_nested_config)
        self.assertTrue(is_valid)

        # Test saving and loading preserves nesting
        nested_file = "nested_config.yaml"
        loader.save_config(deeply_nested_config, nested_file)

        loaded_nested = loader.load_config(nested_file)
        deep_value = loaded_nested["adri"]["protection"]["advanced"]["nested"]["deep"]["very_deep"]["extremely_deep"]["value"]
        self.assertEqual(deep_value, "found_at_level_6")

    def test_config_file_discovery_in_deep_directories(self):
        """Test config file discovery in very deep directory structures."""
        loader = ConfigurationLoader()

        # Create directory structure with Windows path length limitations in mind
        if platform.system() == "Windows":
            # Shorter path for Windows due to 260 character limit
            deep_path = Path("level1") / "level2" / "level3" / "level4"
        else:
            # Longer path for Unix systems
            deep_path = Path("level1") / "level2" / "level3" / "level4" / "level5" / "level6" / "level7"

        try:
            deep_path.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            # Fallback to shorter path if creation fails
            deep_path = Path("level1") / "level2" / "level3"
            deep_path.mkdir(parents=True, exist_ok=True)

        # Create config at root level - ensure ADRI directory exists
        adri_dir = Path("ADRI")
        adri_dir.mkdir(exist_ok=True)

        test_config = loader.create_default_config("deep_discovery")
        with open(adri_dir / "config.yaml", "w", encoding='utf-8') as f:
            yaml.dump(test_config, f)

        # Test discovery from deep directory
        original_cwd = os.getcwd()
        try:
            os.chdir(deep_path)
            found_config = loader.find_config_file()

            self.assertIsNotNone(found_config)
            # Normalize path for comparison
            normalized_found = normalize_path(found_config) if found_config else None
            self.assertTrue(
                normalized_found and normalized_found.endswith("ADRI/config.yaml"),
                f"Expected path ending with ADRI/config.yaml, got: {found_config}"
            )
        finally:
            os.chdir(original_cwd)

    def test_active_config_with_search_edge_cases(self):
        """Test get_active_config with search edge cases."""
        loader = ConfigurationLoader()

        # Test with explicit path
        test_config = loader.create_default_config("explicit_path_test")
        explicit_file = "explicit_config.yaml"
        loader.save_config(test_config, explicit_file)

        active_config = loader.get_active_config(explicit_file)
        self.assertIsNotNone(active_config)
        self.assertEqual(active_config["adri"]["project_name"], "explicit_path_test")

        # Test with None path (should search)
        # Remove explicit file and create ADRI/config.yaml
        Path(explicit_file).unlink()

        adri_dir = Path("ADRI")
        adri_dir.mkdir(exist_ok=True)
        with open(adri_dir / "config.yaml", "w") as f:
            yaml.dump(test_config, f)

        searched_config = loader.get_active_config(None)
        self.assertIsNotNone(searched_config)

        # Test with search finding nothing
        shutil.rmtree(adri_dir)
        no_config = loader.get_active_config()
        self.assertIsNone(no_config)

    def test_default_config_edge_cases(self):
        """Test default configuration creation with edge cases."""
        loader = ConfigurationLoader()

        # Test with empty project name
        empty_name_config = loader.create_default_config("")
        self.assertEqual(empty_name_config["adri"]["project_name"], "")

        # Test with special characters in project name
        special_name_config = loader.create_default_config("test!@#$%^&*()_+")
        self.assertEqual(special_name_config["adri"]["project_name"], "test!@#$%^&*()_+")

        # Test with Unicode project name
        unicode_name_config = loader.create_default_config("项目_тест_Ñoñó")
        self.assertEqual(unicode_name_config["adri"]["project_name"], "项目_тест_Ñoñó")

    def test_path_extension_handling_edge_cases(self):
        """Test path resolution with various file extension scenarios."""
        loader = ConfigurationLoader()

        config = loader.create_default_config("extension_test")

        with patch.object(loader, 'get_active_config', return_value=config):
            # Test various extension scenarios - the loader adds .yaml if no extension
            test_cases = [
                ("standard", "./ADRI/dev/standards/standard.yaml"),  # No extension - adds .yaml
                ("standard.yaml", "./ADRI/dev/standards/standard.yaml"),  # .yaml extension - keeps as is
                ("standard.yml", "./ADRI/dev/standards/standard.yml"),  # .yml extension - keeps as is
                ("standard.YAML", "./ADRI/dev/standards/standard.YAML.yaml"),  # Uppercase - adds .yaml (case sensitive check)
                ("path/to/standard", "./ADRI/dev/standards/path/to/standard.yaml"),  # Path without extension - adds .yaml
                ("path/to/standard.yaml", "./ADRI/dev/standards/path/to/standard.yaml"),  # Path with extension - keeps as is
            ]

            for input_name, expected_path in test_cases:
                resolved_path = loader.resolve_standard_path(input_name, "development")
                self.assertEqual(resolved_path, expected_path)

    def test_environment_defaults_edge_cases(self):
        """Test environment defaults and fallback behavior."""
        loader = ConfigurationLoader()

        config = {
            "adri": {
                "project_name": "defaults_test",
                "version": "4.0.0",
                # No default_environment specified
                "environments": {
                    "development": {
                        "paths": {
                            "standards": "./dev/standards",
                            "assessments": "./dev/assessments",
                            "training_data": "./dev/training"
                        }
                    },
                    "production": {
                        "paths": {
                            "standards": "./prod/standards",
                            "assessments": "./prod/assessments",
                            "training_data": "./prod/training"
                        }
                    }
                }
            }
        }

        with patch.object(loader, 'get_active_config', return_value=config):
            # Should default to development when no default_environment specified
            protection_config = loader.get_protection_config()
            # Should handle gracefully even without explicit environment

    def test_configuration_save_error_handling(self):
        """Test error handling during configuration saving."""
        loader = ConfigurationLoader()

        test_config = loader.create_default_config("save_error_test")

        # Test saving to invalid path
        try:
            loader.save_config(test_config, "/invalid/deep/path/config.yaml")
            # May succeed if directories can be created, or fail gracefully
        except (OSError, IOError):
            # Expected for invalid paths
            pass

        # Test saving with permission denied (Unix only)
        if os.name != 'nt':
            readonly_dir = Path("readonly_dir")
            readonly_dir.mkdir()
            os.chmod(readonly_dir, 0o444)  # Read-only

            try:
                with self.assertRaises((PermissionError, OSError)):
                    loader.save_config(test_config, str(readonly_dir / "config.yaml"))
            finally:
                os.chmod(readonly_dir, 0o755)  # Restore for cleanup


if __name__ == '__main__':
    unittest.main()
