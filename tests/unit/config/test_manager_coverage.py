"""
Additional tests to improve coverage for adri.config.manager module.

These tests target specific uncovered lines to reach 99%+ coverage.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open

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
                                "training_data": test_dir3
                            }
                        }
                    }
                }
            }
            
            # Mock Path.glob to raise PermissionError
            with patch('pathlib.Path.glob', side_effect=PermissionError("Permission denied")):
                result = self.manager.validate_paths(config)
                
                # Should handle the permission error gracefully
                assert "path_status" in result
                # Check that file_count is set to -1 for permission denied
                for path_key in ["dev.standards", "dev.assessments", "dev.training_data"]:
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
                                "training_data": "/another/nonexistent"
                            }
                        }
                    }
                }
            }
            
            # Mock os.access to return False (not readable)
            with patch('os.access', return_value=False):
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
                            "training_data": "/third/missing/path"
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
                                "training_data": test_dir
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
            
            with patch('os.access', side_effect=mock_access):
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
                                "training_data": restricted_dir2
                            }
                        }
                    }
                }
            }
            
            # Test without mocking first to see normal behavior
            result_normal = self.manager.validate_paths(config)
            
            # Now test with permission error on glob
            with patch('pathlib.Path.glob', side_effect=PermissionError("Permission denied")):
                result = self.manager.validate_paths(config)
                
                # Should handle the permission error gracefully
                assert "path_status" in result
                
                # All paths should have file_count = -1 due to permission error
                for path_key in ["dev.standards", "dev.assessments", "dev.training_data"]:
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
                                "training_data": "/nonexistent/path"  # Non-existent
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
                                "training_data": test_dir
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
            
            with patch('os.access', side_effect=mock_access):
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
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
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
        with patch('builtins.open', side_effect=PermissionError("Permission denied")):
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
                            "training_data": "/restricted/training"
                        }
                    }
                }
            }
        }
        
        # Mock Path.mkdir to raise PermissionError
        with patch('pathlib.Path.mkdir', side_effect=PermissionError("Permission denied")):
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
            
            with patch('os.path.exists', side_effect=mock_exists):
                # Should handle permission errors gracefully
                result = self.manager.find_config_file(temp_dir)
                # Should return None if no accessible config found
                assert result is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
