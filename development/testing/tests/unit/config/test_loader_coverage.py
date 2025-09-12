"""
Comprehensive test coverage for adri.config.loader module.
Tests all methods and edge cases to achieve 85%+ coverage.
"""

import os
import tempfile
import pytest
from unittest.mock import patch, mock_open

from adri.config.loader import ConfigLoader


class TestConfigLoader:
    """Test cases for ConfigLoader class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.loader = ConfigLoader()

    def test_init_sets_default_paths(self):
        """Test that initialization sets correct default paths."""
        expected_paths = [
            "adri-config.yaml",
            "ADRI/adri-config.yaml", 
            ".adri/config.yaml",
        ]
        assert self.loader.default_config_paths == expected_paths

    def test_load_config_with_specific_path_success(self):
        """Test loading config from specific path successfully."""
        config_content = """
adri:
  project_name: "test_project"
  version: "1.0.0"
  environments: ["dev", "prod"]
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            f.flush()
            
            try:
                result = self.loader.load_config(f.name)
                assert result is not None
                assert result["adri"]["project_name"] == "test_project"
                assert result["adri"]["version"] == "1.0.0"
                assert result["adri"]["environments"] == ["dev", "prod"]
            finally:
                os.unlink(f.name)

    def test_load_config_with_specific_path_not_found(self):
        """Test loading config from non-existent specific path."""
        result = self.loader.load_config("/nonexistent/path.yaml")
        assert result is None

    def test_load_config_with_specific_path_invalid_yaml(self):
        """Test loading config from file with invalid YAML."""
        invalid_yaml = "invalid: yaml: content: [\n  unclosed"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(invalid_yaml)
            f.flush()
            
            try:
                result = self.loader.load_config(f.name)
                assert result is None
            finally:
                os.unlink(f.name)

    def test_load_config_with_specific_path_non_dict_content(self):
        """Test loading config from file with non-dictionary content."""
        non_dict_yaml = "- item1\n- item2\n- item3"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(non_dict_yaml)
            f.flush()
            
            try:
                result = self.loader.load_config(f.name)
                assert result is None
            finally:
                os.unlink(f.name)

    @patch('os.path.exists')
    def test_load_config_default_paths_first_found(self, mock_exists):
        """Test loading config from first existing default path."""
        # Mock that first path exists
        mock_exists.side_effect = lambda path: path == "adri-config.yaml"
        
        config_content = """
adri:
  project_name: "default_project"
  version: "2.0.0"
  environments: ["staging"]
"""
        
        with patch('builtins.open', mock_open(read_data=config_content)):
            with patch('yaml.safe_load') as mock_yaml:
                mock_yaml.return_value = {
                    "adri": {
                        "project_name": "default_project",
                        "version": "2.0.0", 
                        "environments": ["staging"]
                    }
                }
                
                result = self.loader.load_config()
                assert result is not None
                assert result["adri"]["project_name"] == "default_project"

    @patch('os.path.exists')
    def test_load_config_default_paths_second_found(self, mock_exists):
        """Test loading config from second default path when first doesn't exist."""
        # Mock that second path exists
        mock_exists.side_effect = lambda path: path == "ADRI/adri-config.yaml"
        
        config_content = """
adri:
  project_name: "adri_project"
  version: "3.0.0"
  environments: ["production"]
"""
        
        with patch('builtins.open', mock_open(read_data=config_content)):
            with patch('yaml.safe_load') as mock_yaml:
                mock_yaml.return_value = {
                    "adri": {
                        "project_name": "adri_project",
                        "version": "3.0.0",
                        "environments": ["production"]
                    }
                }
                
                result = self.loader.load_config()
                assert result is not None
                assert result["adri"]["project_name"] == "adri_project"

    @patch('os.path.exists')
    def test_load_config_default_paths_none_found(self, mock_exists):
        """Test loading config when no default paths exist."""
        mock_exists.return_value = False
        
        result = self.loader.load_config()
        assert result is None

    def test_load_config_file_success(self):
        """Test _load_config_file with valid file."""
        config_content = """
adri:
  project_name: "test_file"
  version: "1.5.0"
  environments: ["test"]
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            f.flush()
            
            try:
                result = self.loader._load_config_file(f.name)
                assert result is not None
                assert result["adri"]["project_name"] == "test_file"
            finally:
                os.unlink(f.name)

    def test_load_config_file_exception(self):
        """Test _load_config_file handles exceptions gracefully."""
        result = self.loader._load_config_file("/nonexistent/file.yaml")
        assert result is None

    def test_load_config_file_yaml_exception(self):
        """Test _load_config_file handles YAML parsing exceptions."""
        invalid_yaml = "invalid: yaml: content: [\n  unclosed"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(invalid_yaml)
            f.flush()
            
            try:
                result = self.loader._load_config_file(f.name)
                assert result is None
            finally:
                os.unlink(f.name)

    def test_validate_config_structure_valid(self):
        """Test validate_config_structure with valid configuration."""
        valid_config = {
            "adri": {
                "project_name": "test_project",
                "version": "1.0.0",
                "environments": ["dev", "staging", "prod"]
            }
        }
        
        result = self.loader.validate_config_structure(valid_config)
        assert result is True

    def test_validate_config_structure_missing_adri_key(self):
        """Test validate_config_structure with missing adri key."""
        invalid_config = {
            "other_key": {
                "project_name": "test_project",
                "version": "1.0.0",
                "environments": ["dev"]
            }
        }
        
        result = self.loader.validate_config_structure(invalid_config)
        assert result is False

    def test_validate_config_structure_missing_project_name(self):
        """Test validate_config_structure with missing project_name."""
        invalid_config = {
            "adri": {
                "version": "1.0.0",
                "environments": ["dev"]
            }
        }
        
        result = self.loader.validate_config_structure(invalid_config)
        assert result is False

    def test_validate_config_structure_missing_version(self):
        """Test validate_config_structure with missing version."""
        invalid_config = {
            "adri": {
                "project_name": "test_project",
                "environments": ["dev"]
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
        """Test validate_config_structure with extra fields (should still pass)."""
        config_with_extras = {
            "adri": {
                "project_name": "test_project",
                "version": "1.0.0",
                "environments": ["dev"],
                "extra_field": "extra_value",
                "another_extra": 123
            },
            "other_top_level": "value"
        }
        
        result = self.loader.validate_config_structure(config_with_extras)
        assert result is True

    def test_integration_load_and_validate(self):
        """Integration test: load config and validate structure."""
        config_content = """
adri:
  project_name: "integration_test"
  version: "2.5.0"
  environments: ["local", "staging", "production"]
  additional_setting: "value"
other_section:
  some_other_config: "data"
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            f.flush()
            
            try:
                # Load the config
                config = self.loader.load_config(f.name)
                assert config is not None
                
                # Validate its structure
                is_valid = self.loader.validate_config_structure(config)
                assert is_valid is True
                
                # Verify content
                assert config["adri"]["project_name"] == "integration_test"
                assert config["adri"]["version"] == "2.5.0"
                assert len(config["adri"]["environments"]) == 3
                
            finally:
                os.unlink(f.name)
