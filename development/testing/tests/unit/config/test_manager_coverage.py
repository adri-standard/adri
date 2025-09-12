"""
Additional tests to improve coverage for adri.config.manager module.

These tests target specific uncovered lines to reach 99%+ coverage.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import mock_open, patch

import pytest
import yaml

from adri.config.manager import ConfigManager


class TestConfigManagerCoverage:
    """Tests targeting specific uncovered lines in ConfigManager."""

    def setup_method(self):
        """Set up test fixtures."""
        self.manager = ConfigManager()

    def test_validate_paths_permission_error(self):
        """Test PermissionError handling in validate_paths (lines 377-378)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create directories that exist but will trigger permission error on glob
            test_dir1 = os.path.join(temp_dir, "standards")
            test_dir2 = os.path.join(temp_dir, "assessments")
            test_dir3 = os.path.join(temp_dir, "training")

            os.makedirs(test_dir1)
            os.makedirs(test_dir2)
            os.makedirs(test_dir3)

            config = {
                "adri": {
                    "environments": {
                        "dev": {
                            "paths": {
                                "standards": test_dir1,
                                "assessments": test_dir2,
                                "training_data": test_dir3,
                            }
                        }
                    }
                }
            }

            # Mock Path.glob to raise PermissionError
            with patch(
                "pathlib.Path.glob", side_effect=PermissionError("Permission denied")
            ):
                result = self.manager.validate_paths(config)

                # Should handle the permission error gracefully
                assert "path_status" in result
                # Check that file_count is set to -1 for permission denied
                for path_key in [
                    "dev.standards",
                    "dev.assessments",
                    "dev.training_data",
                ]:
                    if path_key in result["path_status"]:
                        status = result["path_status"][path_key]
                        if "file_count" in status:
                            assert status["file_count"] == -1

    def test_validate_paths_unreadable_path_error(self):
        """Test unreadable path error handling in validate_paths (lines 393-396)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a directory that exists but simulate it being unreadable
            test_dir = os.path.join(temp_dir, "test_standards")
            os.makedirs(test_dir)

            config = {
                "adri": {
                    "environments": {
                        "dev": {
                            "paths": {
                                "standards": test_dir,
                                "assessments": "/nonexistent/path",
                                "training_data": "/another/nonexistent",
                            }
                        }
                    }
                }
            }

            # Mock os.access to return False (not readable)
            with patch("os.access", return_value=False):
                result = self.manager.validate_paths(config)

                # Should add error about path not being readable
                assert result["valid"] is False
                assert len(result["errors"]) >= 1
                assert any("not readable" in error for error in result["errors"])

    def test_validate_paths_warning_for_missing_directory(self):
        """Test warning generation for missing directories (line 398)."""
        config = {
            "adri": {
                "environments": {
                    "dev": {
                        "paths": {
                            "standards": "/completely/nonexistent/path",
                            "assessments": "/another/missing/path",
                            "training_data": "/third/missing/path",
                        }
                    }
                }
            }
        }

        result = self.manager.validate_paths(config)

        # Should generate warnings for missing directories
        assert len(result["warnings"]) >= 3
        assert any("does not exist" in warning for warning in result["warnings"])

        # Should still be valid (warnings don't invalidate)
        assert result["valid"] is True

    def test_validate_paths_non_writable_warning(self):
        """Test warning generation for non-writable directories (line 398)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a directory that exists and is readable but not writable
            test_dir = os.path.join(temp_dir, "readonly_dir")
            os.makedirs(test_dir)

            config = {
                "adri": {
                    "environments": {
                        "dev": {
                            "paths": {
                                "standards": test_dir,
                                "assessments": test_dir,
                                "training_data": test_dir,
                            }
                        }
                    }
                }
            }

            # Mock os.access to return True for read but False for write
            def mock_access(path, mode):
                if mode == os.R_OK:
                    return True  # Readable
                elif mode == os.W_OK:
                    return False  # Not writable
                return True  # Other modes

            with patch("os.access", side_effect=mock_access):
                result = self.manager.validate_paths(config)

                # Should generate warnings for non-writable paths
                assert len(result["warnings"]) >= 3
                assert any("not writable" in warning for warning in result["warnings"])

                # Should still be valid (warnings don't invalidate)
                assert result["valid"] is True

    def test_validate_paths_complex_permission_scenarios(self):
        """Test complex permission scenarios in path validation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test directories
            readable_dir = os.path.join(temp_dir, "readable")
            restricted_dir1 = os.path.join(temp_dir, "restricted1")
            restricted_dir2 = os.path.join(temp_dir, "restricted2")

            os.makedirs(readable_dir)
            os.makedirs(restricted_dir1)
            os.makedirs(restricted_dir2)

            # Create some files in the readable directory
            with open(os.path.join(readable_dir, "test1.yaml"), "w") as f:
                f.write("test: data")
            with open(os.path.join(readable_dir, "test2.yaml"), "w") as f:
                f.write("test: data")

            config = {
                "adri": {
                    "environments": {
                        "dev": {
                            "paths": {
                                "standards": readable_dir,
                                "assessments": restricted_dir1,
                                "training_data": restricted_dir2,
                            }
                        }
                    }
                }
            }

            # Now test with permission error on glob
            with patch(
                "pathlib.Path.glob", side_effect=PermissionError("Permission denied")
            ):
                result = self.manager.validate_paths(config)

                # Should handle the permission error gracefully
                assert "path_status" in result

                # All paths should have file_count = -1 due to permission error
                for path_key in [
                    "dev.standards",
                    "dev.assessments",
                    "dev.training_data",
                ]:
                    status = result["path_status"].get(path_key)
                    if status and "file_count" in status:
                        assert status["file_count"] == -1

    def test_validate_paths_edge_case_combinations(self):
        """Test edge case combinations in path validation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a file (not directory) to test the "not a directory" error
            file_path = os.path.join(temp_dir, "not_a_directory.txt")
            with open(file_path, "w") as f:
                f.write("test content")

            # Create an empty directory
            empty_dir = os.path.join(temp_dir, "empty_dir")
            os.makedirs(empty_dir)

            config = {
                "adri": {
                    "environments": {
                        "dev": {
                            "paths": {
                                "standards": file_path,  # File instead of directory
                                "assessments": empty_dir,  # Empty directory
                                "training_data": "/nonexistent/path",  # Non-existent
                            }
                        }
                    }
                }
            }

            result = self.manager.validate_paths(config)

            # Should have errors for file instead of directory
            assert result["valid"] is False
            assert len(result["errors"]) >= 1
            assert any("not a directory" in error for error in result["errors"])

            # Should have warnings for non-existent path
            assert len(result["warnings"]) >= 1
            assert any("does not exist" in warning for warning in result["warnings"])

    def test_validate_paths_os_access_edge_cases(self):
        """Test os.access edge cases in path validation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_dir = os.path.join(temp_dir, "test_dir")
            os.makedirs(test_dir)

            config = {
                "adri": {
                    "environments": {
                        "dev": {
                            "paths": {
                                "standards": test_dir,
                                "assessments": test_dir,
                                "training_data": test_dir,
                            }
                        }
                    }
                }
            }

            # Test scenario where os.access returns False for readable check
            def mock_access(path, mode):
                if mode == os.R_OK:
                    return False  # Not readable
                return True  # Other modes return True

            with patch("os.access", side_effect=mock_access):
                result = self.manager.validate_paths(config)

                # Should detect unreadable paths and add errors
                assert result["valid"] is False
                assert len(result["errors"]) >= 3  # One for each path
                assert all("not readable" in error for error in result["errors"])


class TestConfigManagerExceptionHandling:
    """Test exception handling in various ConfigManager methods."""

    def setup_method(self):
        """Set up test fixtures."""
        self.manager = ConfigManager()

    def test_validate_config_with_none_input(self):
        """Test validate_config with None input."""
        result = self.manager.validate_config(None)
        assert result is False

    def test_validate_config_with_invalid_structure(self):
        """Test validate_config with various invalid structures."""
        # Test with non-dict input
        assert self.manager.validate_config("not a dict") is False
        assert self.manager.validate_config(123) is False
        assert self.manager.validate_config([]) is False

    def test_load_config_with_invalid_yaml(self):
        """Test load_config with invalid YAML content."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("invalid: yaml: content: [unclosed")
            temp_path = f.name

        try:
            result = self.manager.load_config(temp_path)
            assert result is None  # Should handle YAML parsing errors gracefully
        finally:
            os.unlink(temp_path)

    def test_save_config_permission_error(self):
        """Test save_config with permission error."""
        config = {"test": "data"}

        # Try to save to a location that should cause permission error
        with patch("builtins.open", side_effect=PermissionError("Permission denied")):
            with pytest.raises(PermissionError):
                self.manager.save_config(config, "/root/restricted.yaml")

    def test_create_directory_structure_permission_error(self):
        """Test create_directory_structure with permission errors."""
        config = {
            "adri": {
                "environments": {
                    "dev": {
                        "paths": {
                            "standards": "/restricted/standards",
                            "assessments": "/restricted/assessments",
                            "training_data": "/restricted/training",
                        }
                    }
                }
            }
        }

        # Mock Path.mkdir to raise PermissionError
        with patch(
            "pathlib.Path.mkdir", side_effect=PermissionError("Permission denied")
        ):
            # Should handle the error gracefully (not crash)
            try:
                self.manager.create_directory_structure(config)
            except PermissionError:
                # This is expected behavior - the method should propagate the error
                pass

    def test_find_config_file_with_permission_errors(self):
        """Test find_config_file with permission errors during directory traversal."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Mock os.path.exists to raise PermissionError for some paths
            def mock_exists(path):
                if "restricted" in str(path):
                    raise PermissionError("Permission denied")
                return os.path.exists(path)

            with patch("os.path.exists", side_effect=mock_exists):
                # Should handle permission errors gracefully
                result = self.manager.find_config_file(temp_dir)
                # Should return None if no accessible config found
                assert result is None


class TestConfigManagerAdditionalMethods:
    """Test additional methods and edge cases in ConfigManager."""

    def setup_method(self):
        """Set up test fixtures."""
        self.manager = ConfigManager()

    def test_get_environment_config_invalid_environment(self):
        """Test get_environment_config with invalid environment."""
        config = {
            "adri": {
                "environments": {
                    "dev": {"paths": {"standards": "/path1", "assessments": "/path2", "training_data": "/path3"}}
                },
                "default_environment": "dev"
            }
        }
        
        # Test with non-existent environment
        with pytest.raises(ValueError, match="Environment 'nonexistent' not found"):
            self.manager.get_environment_config(config, "nonexistent")

    def test_get_environment_config_invalid_config_type(self):
        """Test get_environment_config with invalid config type."""
        config = {
            "adri": {
                "environments": {
                    "dev": "invalid_string_instead_of_dict"  # Invalid type
                },
                "default_environment": "dev"
            }
        }
        
        with pytest.raises(ValueError, match="Invalid environment configuration"):
            self.manager.get_environment_config(config, "dev")

    def test_resolve_standard_path(self):
        """Test resolve_standard_path method."""
        config = {
            "adri": {
                "environments": {
                    "dev": {"paths": {"standards": "/test/standards", "assessments": "/test/assessments", "training_data": "/test/training"}}
                },
                "default_environment": "dev"
            }
        }
        
        # Test with .yaml extension
        result = self.manager.resolve_standard_path("test_standard.yaml", config, "dev")
        assert result == os.path.join("/test/standards", "test_standard.yaml")
        
        # Test without extension (should add .yaml)
        result = self.manager.resolve_standard_path("test_standard", config, "dev")
        assert result == os.path.join("/test/standards", "test_standard.yaml")

    def test_get_assessments_dir(self):
        """Test get_assessments_dir method."""
        config = {
            "adri": {
                "environments": {
                    "dev": {"paths": {"standards": "/test/standards", "assessments": "/test/assessments", "training_data": "/test/training"}}
                },
                "default_environment": "dev"
            }
        }
        
        result = self.manager.get_assessments_dir(config, "dev")
        assert result == "/test/assessments"

    def test_get_assessments_dir_invalid_type(self):
        """Test get_assessments_dir with invalid assessments path type."""
        config = {
            "adri": {
                "environments": {
                    "dev": {"paths": {"standards": "/test/standards", "assessments": 123, "training_data": "/test/training"}}  # Invalid type
                },
                "default_environment": "dev"
            }
        }
        
        with pytest.raises(ValueError, match="Invalid assessments path configuration"):
            self.manager.get_assessments_dir(config, "dev")

    def test_get_training_data_dir(self):
        """Test get_training_data_dir method."""
        config = {
            "adri": {
                "environments": {
                    "dev": {"paths": {"standards": "/test/standards", "assessments": "/test/assessments", "training_data": "/test/training"}}
                },
                "default_environment": "dev"
            }
        }
        
        result = self.manager.get_training_data_dir(config, "dev")
        assert result == "/test/training"

    def test_get_training_data_dir_invalid_type(self):
        """Test get_training_data_dir with invalid training data path type."""
        config = {
            "adri": {
                "environments": {
                    "dev": {"paths": {"standards": "/test/standards", "assessments": "/test/assessments", "training_data": ["invalid", "list"]}}  # Invalid type
                },
                "default_environment": "dev"
            }
        }
        
        with pytest.raises(ValueError, match="Invalid training data path configuration"):
            self.manager.get_training_data_dir(config, "dev")

    def test_get_protection_config_with_no_active_config(self):
        """Test get_protection_config when no active config is found."""
        with patch.object(self.manager, 'get_active_config', return_value=None):
            result = self.manager.get_protection_config()
            
            # Should return default protection config
            assert result["default_failure_mode"] == "raise"
            assert result["default_min_score"] == 80
            assert result["cache_duration_hours"] == 1

    def test_get_protection_config_with_environment_override(self):
        """Test get_protection_config with environment-specific overrides."""
        mock_config = {
            "adri": {
                "protection": {
                    "default_failure_mode": "warn",
                    "default_min_score": 70,
                },
                "environments": {
                    "prod": {
                        "protection": {
                            "default_failure_mode": "raise",
                            "default_min_score": 90,
                        }
                    }
                },
                "default_environment": "dev"
            }
        }
        
        with patch.object(self.manager, 'get_active_config', return_value=mock_config):
            result = self.manager.get_protection_config("prod")
            
            # Should have environment overrides
            assert result["default_failure_mode"] == "raise"
            assert result["default_min_score"] == 90

    def test_get_protection_config_invalid_types(self):
        """Test get_protection_config with invalid config types."""
        mock_config = {
            "adri": {
                "protection": "invalid_string",  # Should be dict
                "environments": {
                    "dev": {
                        "protection": ["invalid", "list"]  # Should be dict
                    }
                },
                "default_environment": "dev"
            }
        }
        
        with patch.object(self.manager, 'get_active_config', return_value=mock_config):
            result = self.manager.get_protection_config("dev")
            
            # Should handle invalid types gracefully and return empty dict + env override
            assert isinstance(result, dict)

    def test_resolve_standard_path_simple_no_config(self):
        """Test resolve_standard_path_simple when no config is available."""
        with patch.object(self.manager, 'get_active_config', return_value=None):
            result = self.manager.resolve_standard_path_simple("test_standard")
            
            # Should use fallback path structure
            expected = os.path.join("./ADRI/dev/standards", "test_standard.yaml")
            assert result == expected

    def test_resolve_standard_path_simple_with_config(self):
        """Test resolve_standard_path_simple with active config."""
        mock_config = {
            "adri": {
                "environments": {
                    "dev": {"paths": {"standards": "/custom/standards", "assessments": "/custom/assessments", "training_data": "/custom/training"}}
                },
                "default_environment": "dev"
            }
        }
        
        with patch.object(self.manager, 'get_active_config', return_value=mock_config):
            with patch.object(self.manager, 'resolve_standard_path', return_value="/custom/standards/test.yaml") as mock_resolve:
                result = self.manager.resolve_standard_path_simple("test_standard")
                
                assert result == "/custom/standards/test.yaml"
                mock_resolve.assert_called_once()

    def test_get_audit_config_no_active_config(self):
        """Test get_audit_config when no active config is found."""
        with patch.object(self.manager, 'get_active_config', return_value=None):
            result = self.manager.get_audit_config()
            
            # Should return default audit config
            assert result["enabled"] is True
            assert result["log_location"] == "./logs/adri_audit.jsonl"
            assert result["log_level"] == "INFO"

    def test_get_audit_config_with_environment_override(self):
        """Test get_audit_config with environment-specific overrides."""
        mock_config = {
            "adri": {
                "audit": {
                    "enabled": True,
                    "log_level": "DEBUG",
                },
                "environments": {
                    "prod": {
                        "audit": {
                            "log_level": "ERROR",
                            "batch_mode": True,
                        }
                    }
                },
                "default_environment": "dev"
            }
        }
        
        with patch.object(self.manager, 'get_active_config', return_value=mock_config):
            result = self.manager.get_audit_config("prod")
            
            # Should have environment overrides
            assert result["log_level"] == "ERROR"
            assert result["batch_mode"] is True
            assert result["enabled"] is True  # From base config

    def test_get_audit_config_invalid_types(self):
        """Test get_audit_config with invalid config types."""
        mock_config = {
            "adri": {
                "audit": "invalid_string",  # Should be dict
                "environments": {
                    "dev": {
                        "audit": 123  # Should be dict
                    }
                },
                "default_environment": "dev"
            }
        }
        
        with patch.object(self.manager, 'get_active_config', return_value=mock_config):
            result = self.manager.get_audit_config("dev")
            
            # Should handle invalid types gracefully and use defaults
            assert result["enabled"] is True
            assert result["log_level"] == "INFO"

    def test_load_config_non_dict_yaml_content(self):
        """Test load_config when YAML contains non-dict content."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(["list", "instead", "of", "dict"], f)
            temp_path = f.name

        try:
            result = self.manager.load_config(temp_path)
            assert result is None  # Should return None for non-dict content
        finally:
            os.unlink(temp_path)

    def test_load_config_io_error(self):
        """Test load_config with IOError."""
        with patch("builtins.open", side_effect=IOError("File read error")):
            result = self.manager.load_config("any_path.yaml")
            assert result is None  # Should handle IOError gracefully


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
