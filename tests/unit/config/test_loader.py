"""
Tests for the ConfigLoader module.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from adri.config.loader import ConfigLoader


class TestConfigLoader:
    """Test cases for ConfigLoader class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.loader = ConfigLoader()
        
        # Sample valid config
        self.valid_config = {
            "adri": {
                "project_name": "test_project",
                "version": "1.0.0",
                "environments": {
                    "dev": {"database_url": "dev_db"},
                    "prod": {"database_url": "prod_db"}
                }
            }
        }
        
        # Sample invalid config (missing required fields)
        self.invalid_config = {
            "adri": {
                "project_name": "test_project"
                # Missing version and environments
            }
        }

    def test_init_sets_default_paths(self):
        """Test that initialization sets correct default config paths."""
        expected_paths = [
            "adri-config.yaml",
            "ADRI/adri-config.yaml",
            ".adri/config.yaml",
        ]
        assert self.loader.default_config_paths == expected_paths

    def test_load_config_with_specific_path_success(self):
        """Test loading config from a specific file path."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(self.valid_config, f)
            config_path = f.name

        try:
            result = self.loader.load_config(config_path)
            assert result == self.valid_config
        finally:
            os.unlink(config_path)

    def test_load_config_with_specific_path_not_found(self):
        """Test loading config from non-existent file path."""
        result = self.loader.load_config("nonexistent_config.yaml")
        assert result is None

    def test_load_config_with_specific_path_invalid_yaml(self):
        """Test loading config from file with invalid YAML."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: content: [")
            config_path = f.name

        try:
            result = self.loader.load_config(config_path)
            assert result is None
        finally:
            os.unlink(config_path)

    def test_load_config_with_specific_path_non_dict_content(self):
        """Test loading config from file with non-dictionary content."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump("just a string", f)
            config_path = f.name

        try:
            result = self.loader.load_config(config_path)
            assert result is None
        finally:
            os.unlink(config_path)

    @patch('os.path.exists')
    def test_load_config_searches_default_paths(self, mock_exists):
        """Test that load_config searches default paths when no path specified."""
        # Mock that the second default path exists
        mock_exists.side_effect = lambda path: path == "ADRI/adri-config.yaml"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(self.valid_config, f)
            temp_path = f.name

        try:
            # Mock the file loading to return our temp file content
            with patch.object(self.loader, '_load_config_file') as mock_load:
                mock_load.return_value = self.valid_config
                
                result = self.loader.load_config()
                
                # Should call _load_config_file with the second default path
                mock_load.assert_called_once_with("ADRI/adri-config.yaml")
                assert result == self.valid_config
        finally:
            os.unlink(temp_path)

    @patch('os.path.exists')
    def test_load_config_no_default_paths_found(self, mock_exists):
        """Test load_config returns None when no default paths exist."""
        mock_exists.return_value = False
        
        result = self.loader.load_config()
        assert result is None

    def test_load_config_file_success(self):
        """Test _load_config_file with valid YAML file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(self.valid_config, f)
            config_path = f.name

        try:
            result = self.loader._load_config_file(config_path)
            assert result == self.valid_config
        finally:
            os.unlink(config_path)

    def test_load_config_file_invalid_yaml(self):
        """Test _load_config_file with invalid YAML."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: [unclosed")
            config_path = f.name

        try:
            result = self.loader._load_config_file(config_path)
            assert result is None
        finally:
            os.unlink(config_path)

    def test_load_config_file_non_dict(self):
        """Test _load_config_file with non-dictionary YAML content."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(["list", "instead", "of", "dict"], f)
            config_path = f.name

        try:
            result = self.loader._load_config_file(config_path)
            assert result is None
        finally:
            os.unlink(config_path)

    def test_load_config_file_file_not_found(self):
        """Test _load_config_file with non-existent file."""
        result = self.loader._load_config_file("nonexistent_file.yaml")
        assert result is None

    def test_load_config_file_permission_error(self):
        """Test _load_config_file handles permission errors gracefully."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(self.valid_config, f)
            config_path = f.name

        try:
            # Change permissions to make file unreadable
            os.chmod(config_path, 0o000)
            
            result = self.loader._load_config_file(config_path)
            assert result is None
        finally:
            # Restore permissions and clean up
            os.chmod(config_path, 0o644)
            os.unlink(config_path)

    def test_validate_config_structure_valid(self):
        """Test validate_config_structure with valid config."""
        result = self.loader.validate_config_structure(self.valid_config)
        assert result is True

    def test_validate_config_structure_missing_adri_section(self):
        """Test validate_config_structure with missing 'adri' section."""
        invalid_config = {"other_section": {"key": "value"}}
        result = self.loader.validate_config_structure(invalid_config)
        assert result is False

    def test_validate_config_structure_missing_project_name(self):
        """Test validate_config_structure with missing project_name."""
        invalid_config = {
            "adri": {
                "version": "1.0.0",
                "environments": {}
            }
        }
        result = self.loader.validate_config_structure(invalid_config)
        assert result is False

    def test_validate_config_structure_missing_version(self):
        """Test validate_config_structure with missing version."""
        invalid_config = {
            "adri": {
                "project_name": "test_project",
                "environments": {}
            }
        }
        result = self.loader.validate_config_structure(invalid_config)
        assert result is False

    def test_validate_config_structure_missing_environments(self):
        """Test validate_config_structure with missing environments."""
        invalid_config = {
            "adri": {
                "project_name": "test_project",
                "version": "1.0.0"
            }
        }
        result = self.loader.validate_config_structure(invalid_config)
        assert result is False

    def test_validate_config_structure_with_extra_fields(self):
        """Test validate_config_structure accepts configs with extra fields."""
        config_with_extras = {
            "adri": {
                "project_name": "test_project",
                "version": "1.0.0",
                "environments": {},
                "extra_field": "extra_value",
                "another_extra": {"nested": "value"}
            }
        }
        result = self.loader.validate_config_structure(config_with_extras)
        assert result is True

    def test_integration_load_and_validate(self):
        """Integration test: load config and validate structure."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(self.valid_config, f)
            config_path = f.name

        try:
            # Load the config
            loaded_config = self.loader.load_config(config_path)
            assert loaded_config is not None
            
            # Validate the structure
            is_valid = self.loader.validate_config_structure(loaded_config)
            assert is_valid is True
            
            # Check specific values
            assert loaded_config["adri"]["project_name"] == "test_project"
            assert loaded_config["adri"]["version"] == "1.0.0"
            assert "environments" in loaded_config["adri"]
        finally:
            os.unlink(config_path)

    def test_integration_load_invalid_and_validate(self):
        """Integration test: load invalid config and validate structure."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(self.invalid_config, f)
            config_path = f.name

        try:
            # Load the config
            loaded_config = self.loader.load_config(config_path)
            assert loaded_config is not None
            
            # Validate the structure (should fail)
            is_valid = self.loader.validate_config_structure(loaded_config)
            assert is_valid is False
        finally:
            os.unlink(config_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
