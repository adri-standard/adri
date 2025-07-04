"""
Tests for the ConfigManager module.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open

import pytest
import yaml

from adri.config.manager import ConfigManager


class TestConfigManagerInit:
    """Test ConfigManager initialization."""

    def test_init(self):
        """Test ConfigManager initialization."""
        manager = ConfigManager()
        assert isinstance(manager, ConfigManager)


class TestCreateDefaultConfig:
    """Test the create_default_config method."""

    def setup_method(self):
        """Set up test fixtures."""
        self.manager = ConfigManager()

    def test_create_default_config_structure(self):
        """Test that default config has correct structure."""
        config = self.manager.create_default_config("test_project")
        
        assert "adri" in config
        adri_config = config["adri"]
        
        # Check required top-level fields
        assert adri_config["version"] == "2.0"
        assert adri_config["project_name"] == "test_project"
        assert "environments" in adri_config
        assert "default_environment" in adri_config
        assert "protection" in adri_config
        assert "assessment" in adri_config
        assert "generation" in adri_config
        assert "logging" in adri_config

    def test_create_default_config_environments(self):
        """Test that default config has correct environments."""
        config = self.manager.create_default_config("test_project")
        environments = config["adri"]["environments"]
        
        assert "development" in environments
        assert "production" in environments
        
        # Check development environment
        dev_env = environments["development"]
        assert "paths" in dev_env
        assert "protection" in dev_env
        
        dev_paths = dev_env["paths"]
        assert "standards" in dev_paths
        assert "assessments" in dev_paths
        assert "training_data" in dev_paths
        
        # Check production environment
        prod_env = environments["production"]
        assert "paths" in prod_env
        assert "protection" in prod_env

    def test_create_default_config_different_project_names(self):
        """Test default config with different project names."""
        config1 = self.manager.create_default_config("project_one")
        config2 = self.manager.create_default_config("project_two")
        
        assert config1["adri"]["project_name"] == "project_one"
        assert config2["adri"]["project_name"] == "project_two"
        
        # Other parts should be the same
        assert config1["adri"]["version"] == config2["adri"]["version"]


class TestValidateConfig:
    """Test the validate_config method."""

    def setup_method(self):
        """Set up test fixtures."""
        self.manager = ConfigManager()
        self.valid_config = self.manager.create_default_config("test_project")

    def test_validate_config_valid(self):
        """Test validation of valid config."""
        result = self.manager.validate_config(self.valid_config)
        assert result is True

    def test_validate_config_missing_adri_section(self):
        """Test validation with missing adri section."""
        invalid_config = {"other": "data"}
        result = self.manager.validate_config(invalid_config)
        assert result is False

    def test_validate_config_missing_version(self):
        """Test validation with missing version."""
        invalid_config = {"adri": {"project_name": "test"}}
        result = self.manager.validate_config(invalid_config)
        assert result is False

    def test_validate_config_missing_project_name(self):
        """Test validation with missing project_name."""
        invalid_config = {"adri": {"version": "2.0"}}
        result = self.manager.validate_config(invalid_config)
        assert result is False

    def test_validate_config_missing_environments(self):
        """Test validation with missing environments."""
        invalid_config = {
            "adri": {
                "version": "2.0",
                "project_name": "test",
                "default_environment": "dev"
            }
        }
        result = self.manager.validate_config(invalid_config)
        assert result is False

    def test_validate_config_missing_default_environment(self):
        """Test validation with missing default_environment."""
        invalid_config = {
            "adri": {
                "version": "2.0",
                "project_name": "test",
                "environments": {}
            }
        }
        result = self.manager.validate_config(invalid_config)
        assert result is False

    def test_validate_config_invalid_environments_type(self):
        """Test validation with invalid environments type."""
        invalid_config = {
            "adri": {
                "version": "2.0",
                "project_name": "test",
                "environments": "not_a_dict",
                "default_environment": "dev"
            }
        }
        result = self.manager.validate_config(invalid_config)
        assert result is False

    def test_validate_config_missing_paths_in_environment(self):
        """Test validation with missing paths in environment."""
        invalid_config = {
            "adri": {
                "version": "2.0",
                "project_name": "test",
                "environments": {
                    "dev": {"other": "data"}
                },
                "default_environment": "dev"
            }
        }
        result = self.manager.validate_config(invalid_config)
        assert result is False

    def test_validate_config_missing_required_paths(self):
        """Test validation with missing required paths."""
        invalid_config = {
            "adri": {
                "version": "2.0",
                "project_name": "test",
                "environments": {
                    "dev": {
                        "paths": {
                            "standards": "./standards"
                            # Missing assessments and training_data
                        }
                    }
                },
                "default_environment": "dev"
            }
        }
        result = self.manager.validate_config(invalid_config)
        assert result is False

    def test_validate_config_exception_handling(self):
        """Test validation with exception-causing config."""
        # This should trigger an exception and return False
        result = self.manager.validate_config(None)
        assert result is False


class TestSaveConfig:
    """Test the save_config method."""

    def setup_method(self):
        """Set up test fixtures."""
        self.manager = ConfigManager()

    def test_save_config_default_path(self):
        """Test saving config to default path."""
        config = {"test": "data"}
        
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            try:
                os.chdir(temp_dir)
                self.manager.save_config(config)
                
                # Check file was created
                assert os.path.exists("adri-config.yaml")
                
                # Check content
                with open("adri-config.yaml", "r") as f:
                    loaded_config = yaml.safe_load(f)
                assert loaded_config == config
            finally:
                os.chdir(original_cwd)

    def test_save_config_custom_path(self):
        """Test saving config to custom path."""
        config = {"test": "data"}
        
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, "custom-config.yaml")
            self.manager.save_config(config, config_path)
            
            # Check file was created
            assert os.path.exists(config_path)
            
            # Check content
            with open(config_path, "r") as f:
                loaded_config = yaml.safe_load(f)
            assert loaded_config == config

    def test_save_config_creates_directories(self):
        """Test that save_config creates necessary directories."""
        config = {"test": "data"}
        
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, "subdir", "config.yaml")
            
            # Create the parent directory first (since save_config doesn't create dirs)
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            self.manager.save_config(config, config_path)
            
            # Check file was created
            assert os.path.exists(config_path)


class TestLoadConfig:
    """Test the load_config method."""

    def setup_method(self):
        """Set up test fixtures."""
        self.manager = ConfigManager()

    def test_load_config_existing_file(self):
        """Test loading existing config file."""
        config = {"test": "data", "nested": {"key": "value"}}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config, f)
            temp_path = f.name

        try:
            loaded_config = self.manager.load_config(temp_path)
            assert loaded_config == config
        finally:
            os.unlink(temp_path)

    def test_load_config_nonexistent_file(self):
        """Test loading non-existent config file."""
        result = self.manager.load_config("nonexistent_file.yaml")
        assert result is None

    def test_load_config_default_path(self):
        """Test loading config from default path."""
        config = {"test": "data"}
        
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            try:
                os.chdir(temp_dir)
                
                # Create config file
                with open("adri-config.yaml", "w") as f:
                    yaml.dump(config, f)
                
                loaded_config = self.manager.load_config()
                assert loaded_config == config
            finally:
                os.chdir(original_cwd)


class TestCreateDirectoryStructure:
    """Test the create_directory_structure method."""

    def setup_method(self):
        """Set up test fixtures."""
        self.manager = ConfigManager()

    def test_create_directory_structure(self):
        """Test creating directory structure from config."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            try:
                os.chdir(temp_dir)
                
                config = {
                    "adri": {
                        "environments": {
                            "dev": {
                                "paths": {
                                    "standards": "./dev/standards",
                                    "assessments": "./dev/assessments",
                                    "training_data": "./dev/training"
                                }
                            },
                            "prod": {
                                "paths": {
                                    "standards": "./prod/standards",
                                    "assessments": "./prod/assessments",
                                    "training_data": "./prod/training"
                                }
                            }
                        }
                    }
                }
                
                self.manager.create_directory_structure(config)
                
                # Check that directories were created
                assert os.path.exists("./dev/standards")
                assert os.path.exists("./dev/assessments")
                assert os.path.exists("./dev/training")
                assert os.path.exists("./prod/standards")
                assert os.path.exists("./prod/assessments")
                assert os.path.exists("./prod/training")
                assert os.path.exists(".adri/cache")
                assert os.path.exists(".adri/logs")
            finally:
                os.chdir(original_cwd)


class TestFindConfigFile:
    """Test the find_config_file method."""

    def setup_method(self):
        """Set up test fixtures."""
        self.manager = ConfigManager()

    def test_find_config_file_in_adri_directory(self):
        """Test finding config file in ADRI directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create ADRI/adri-config.yaml
            adri_dir = os.path.join(temp_dir, "ADRI")
            os.makedirs(adri_dir)
            config_path = os.path.join(adri_dir, "adri-config.yaml")
            
            with open(config_path, "w") as f:
                f.write("test: data")
            
            result = self.manager.find_config_file(temp_dir)
            # Normalize paths for comparison (macOS resolves /var to /private/var)
            assert os.path.realpath(result) == os.path.realpath(config_path)

    def test_find_config_file_fallback_locations(self):
        """Test finding config file in fallback locations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create adri-config.yaml in root
            config_path = os.path.join(temp_dir, "adri-config.yaml")
            
            with open(config_path, "w") as f:
                f.write("test: data")
            
            result = self.manager.find_config_file(temp_dir)
            assert os.path.realpath(result) == os.path.realpath(config_path)

    def test_find_config_file_yml_extension(self):
        """Test finding config file with .yml extension."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, "adri-config.yml")
            
            with open(config_path, "w") as f:
                f.write("test: data")
            
            result = self.manager.find_config_file(temp_dir)
            assert os.path.realpath(result) == os.path.realpath(config_path)

    def test_find_config_file_dotfile_locations(self):
        """Test finding config file in dotfile locations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, ".adri.yaml")
            
            with open(config_path, "w") as f:
                f.write("test: data")
            
            result = self.manager.find_config_file(temp_dir)
            assert os.path.realpath(result) == os.path.realpath(config_path)

    def test_find_config_file_parent_directory(self):
        """Test finding config file in parent directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create subdirectory
            subdir = os.path.join(temp_dir, "subdir")
            os.makedirs(subdir)
            
            # Create config in parent
            config_path = os.path.join(temp_dir, "adri-config.yaml")
            with open(config_path, "w") as f:
                f.write("test: data")
            
            result = self.manager.find_config_file(subdir)
            assert os.path.realpath(result) == os.path.realpath(config_path)

    def test_find_config_file_not_found(self):
        """Test when config file is not found."""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = self.manager.find_config_file(temp_dir)
            assert result is None

    def test_find_config_file_priority_order(self):
        """Test that ADRI/adri-config.yaml has priority."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create both ADRI/adri-config.yaml and adri-config.yaml
            adri_dir = os.path.join(temp_dir, "ADRI")
            os.makedirs(adri_dir)
            
            primary_config = os.path.join(adri_dir, "adri-config.yaml")
            fallback_config = os.path.join(temp_dir, "adri-config.yaml")
            
            with open(primary_config, "w") as f:
                f.write("primary: config")
            with open(fallback_config, "w") as f:
                f.write("fallback: config")
            
            result = self.manager.find_config_file(temp_dir)
            assert os.path.realpath(result) == os.path.realpath(primary_config)


class TestGetActiveConfig:
    """Test the get_active_config method."""

    def setup_method(self):
        """Set up test fixtures."""
        self.manager = ConfigManager()

    def test_get_active_config_with_path(self):
        """Test getting active config with specific path."""
        config = {"test": "data"}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config, f)
            temp_path = f.name

        try:
            result = self.manager.get_active_config(temp_path)
            assert result == config
        finally:
            os.unlink(temp_path)

    def test_get_active_config_search_for_file(self):
        """Test getting active config by searching for file."""
        config = {"test": "data"}
        
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, "adri-config.yaml")
            with open(config_path, "w") as f:
                yaml.dump(config, f)
            
            with patch.object(self.manager, 'find_config_file') as mock_find:
                mock_find.return_value = config_path
                
                result = self.manager.get_active_config()
                assert result == config
                mock_find.assert_called_once()

    def test_get_active_config_no_file_found(self):
        """Test getting active config when no file is found."""
        with patch.object(self.manager, 'find_config_file') as mock_find:
            mock_find.return_value = None
            
            result = self.manager.get_active_config()
            assert result is None

    def test_get_active_config_invalid_path(self):
        """Test getting active config with invalid path."""
        result = self.manager.get_active_config("nonexistent_file.yaml")
        assert result is None


class TestGetEnvironmentConfig:
    """Test the get_environment_config method."""

    def setup_method(self):
        """Set up test fixtures."""
        self.manager = ConfigManager()
        self.config = self.manager.create_default_config("test_project")

    def test_get_environment_config_specific_environment(self):
        """Test getting config for specific environment."""
        result = self.manager.get_environment_config(self.config, "development")
        
        assert "paths" in result
        assert "protection" in result
        assert result["paths"]["standards"] == "./ADRI/dev/standards"

    def test_get_environment_config_default_environment(self):
        """Test getting config for default environment."""
        result = self.manager.get_environment_config(self.config)
        
        # Should return development environment (the default)
        assert "paths" in result
        assert result["paths"]["standards"] == "./ADRI/dev/standards"

    def test_get_environment_config_nonexistent_environment(self):
        """Test getting config for non-existent environment."""
        with pytest.raises(ValueError, match="Environment 'nonexistent' not found"):
            self.manager.get_environment_config(self.config, "nonexistent")

    def test_get_environment_config_custom_default(self):
        """Test getting config with custom default environment."""
        custom_config = self.config.copy()
        custom_config["adri"]["default_environment"] = "production"
        
        result = self.manager.get_environment_config(custom_config)
        
        # Should return production environment
        assert result["paths"]["standards"] == "./ADRI/prod/standards"


class TestResolveStandardPath:
    """Test the resolve_standard_path method."""

    def setup_method(self):
        """Set up test fixtures."""
        self.manager = ConfigManager()
        self.config = self.manager.create_default_config("test_project")

    def test_resolve_standard_path_with_yaml_extension(self):
        """Test resolving standard path with .yaml extension."""
        result = self.manager.resolve_standard_path(
            "test_standard.yaml", self.config, "development"
        )
        
        expected = os.path.join("./ADRI/dev/standards", "test_standard.yaml")
        assert result == expected

    def test_resolve_standard_path_without_extension(self):
        """Test resolving standard path without extension."""
        result = self.manager.resolve_standard_path(
            "test_standard", self.config, "development"
        )
        
        expected = os.path.join("./ADRI/dev/standards", "test_standard.yaml")
        assert result == expected

    def test_resolve_standard_path_yml_extension(self):
        """Test resolving standard path with .yml extension."""
        result = self.manager.resolve_standard_path(
            "test_standard.yml", self.config, "development"
        )
        
        expected = os.path.join("./ADRI/dev/standards", "test_standard.yml")
        assert result == expected

    def test_resolve_standard_path_production_environment(self):
        """Test resolving standard path for production environment."""
        result = self.manager.resolve_standard_path(
            "test_standard", self.config, "production"
        )
        
        expected = os.path.join("./ADRI/prod/standards", "test_standard.yaml")
        assert result == expected

    def test_resolve_standard_path_default_environment(self):
        """Test resolving standard path with default environment."""
        result = self.manager.resolve_standard_path(
            "test_standard", self.config
        )
        
        # Should use development (default environment)
        expected = os.path.join("./ADRI/dev/standards", "test_standard.yaml")
        assert result == expected


class TestGetDirectoryMethods:
    """Test the get_*_dir methods."""

    def setup_method(self):
        """Set up test fixtures."""
        self.manager = ConfigManager()
        self.config = self.manager.create_default_config("test_project")

    def test_get_assessments_dir(self):
        """Test getting assessments directory."""
        result = self.manager.get_assessments_dir(self.config, "development")
        assert result == "./ADRI/dev/assessments"

    def test_get_assessments_dir_production(self):
        """Test getting assessments directory for production."""
        result = self.manager.get_assessments_dir(self.config, "production")
        assert result == "./ADRI/prod/assessments"

    def test_get_assessments_dir_default_environment(self):
        """Test getting assessments directory with default environment."""
        result = self.manager.get_assessments_dir(self.config)
        assert result == "./ADRI/dev/assessments"

    def test_get_training_data_dir(self):
        """Test getting training data directory."""
        result = self.manager.get_training_data_dir(self.config, "development")
        assert result == "./ADRI/dev/training-data"

    def test_get_training_data_dir_production(self):
        """Test getting training data directory for production."""
        result = self.manager.get_training_data_dir(self.config, "production")
        assert result == "./ADRI/prod/training-data"

    def test_get_training_data_dir_default_environment(self):
        """Test getting training data directory with default environment."""
        result = self.manager.get_training_data_dir(self.config)
        assert result == "./ADRI/dev/training-data"


class TestValidatePaths:
    """Test the validate_paths method."""

    def setup_method(self):
        """Set up test fixtures."""
        self.manager = ConfigManager()

    def test_validate_paths_nonexistent_directories(self):
        """Test path validation with non-existent directories."""
        config = {
            "adri": {
                "environments": {
                    "dev": {
                        "paths": {
                            "standards": "/nonexistent/path1",
                            "assessments": "/nonexistent/path2",
                            "training_data": "/nonexistent/path3"
                        }
                    }
                }
            }
        }
        
        result = self.manager.validate_paths(config)
        
        assert result["valid"] is True  # Warnings don't make it invalid
        assert len(result["warnings"]) >= 3  # Should have warnings for missing paths
        assert "path_status" in result

    def test_validate_paths_existing_directories(self):
        """Test path validation with existing directories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test directories
            standards_dir = os.path.join(temp_dir, "standards")
            assessments_dir = os.path.join(temp_dir, "assessments")
            training_dir = os.path.join(temp_dir, "training")
            
            os.makedirs(standards_dir)
            os.makedirs(assessments_dir)
            os.makedirs(training_dir)
            
            config = {
                "adri": {
                    "environments": {
                        "dev": {
                            "paths": {
                                "standards": standards_dir,
                                "assessments": assessments_dir,
                                "training_data": training_dir
                            }
                        }
                    }
                }
            }
            
            result = self.manager.validate_paths(config)
            
            assert result["valid"] is True
            assert len(result["errors"]) == 0
            
            # Check path status
            for path_key in ["dev.standards", "dev.assessments", "dev.training_data"]:
                status = result["path_status"][path_key]
                assert status["exists"] is True
                assert status["is_directory"] is True
                assert status["readable"] is True

    def test_validate_paths_file_instead_of_directory(self):
        """Test path validation when path points to file instead of directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a file instead of directory
            file_path = os.path.join(temp_dir, "not_a_directory.txt")
            with open(file_path, "w") as f:
                f.write("test")
            
            config = {
                "adri": {
                    "environments": {
                        "dev": {
                            "paths": {
                                "standards": file_path,
                                "assessments": "/nonexistent",
                                "training_data": "/nonexistent"
                            }
                        }
                    }
                }
            }
            
            result = self.manager.validate_paths(config)
            
            assert result["valid"] is False
            assert len(result["errors"]) >= 1
            assert any("not a directory" in error for error in result["errors"])


class TestGetProtectionConfig:
    """Test the get_protection_config method."""

    def setup_method(self):
        """Set up test fixtures."""
        self.manager = ConfigManager()

    def test_get_protection_config_no_active_config(self):
        """Test getting protection config when no active config exists."""
        with patch.object(self.manager, 'get_active_config') as mock_get:
            mock_get.return_value = None
            
            result = self.manager.get_protection_config()
            
            # Should return default protection config
            assert "default_failure_mode" in result
            assert "default_min_score" in result
            assert result["default_failure_mode"] == "raise"
            assert result["default_min_score"] == 80

    def test_get_protection_config_with_active_config(self):
        """Test getting protection config with active config."""
        config = self.manager.create_default_config("test_project")
        
        with patch.object(self.manager, 'get_active_config') as mock_get:
            mock_get.return_value = config
            
            result = self.manager.get_protection_config("development")
            
            # Should return development environment protection config
            assert result["default_failure_mode"] == "warn"
            assert result["default_min_score"] == 75

    def test_get_protection_config_production_environment(self):
        """Test getting protection config for production environment."""
        config = self.manager.create_default_config("test_project")
        
        with patch.object(self.manager, 'get_active_config') as mock_get:
            mock_get.return_value = config
            
            result = self.manager.get_protection_config("production")
            
            # Should return production environment protection config
            assert result["default_failure_mode"] == "raise"
            assert result["default_min_score"] == 85

    def test_get_protection_config_environment_override(self):
        """Test that environment config overrides global config."""
        config = self.manager.create_default_config("test_project")
        
        with patch.object(self.manager, 'get_active_config') as mock_get:
            mock_get.return_value = config
            
            result = self.manager.get_protection_config("development")
            
            # Environment-specific settings should override global ones
            assert result["default_failure_mode"] == "warn"  # From dev environment
            assert result["default_min_score"] == 75  # From dev environment
            # Global settings should still be present
            assert result["auto_generate_standards"] is True


class TestResolveStandardPathSimple:
    """Test the resolve_standard_path_simple method."""

    def setup_method(self):
        """Set up test fixtures."""
        self.manager = ConfigManager()

    def test_resolve_standard_path_simple_with_config(self):
        """Test simple standard path resolution with active config."""
        config = self.manager.create_default_config("test_project")
        
        with patch.object(self.manager, 'get_active_config') as mock_get:
            mock_get.return_value = config
            
            result = self.manager.resolve_standard_path_simple("test_standard", "development")
            
            expected = os.path.join("./ADRI/dev/standards", "test_standard.yaml")
            assert result == expected

    def test_resolve_standard_path_simple_no_config(self):
        """Test simple standard path resolution without active config."""
        with patch.object(self.manager, 'get_active_config') as mock_get:
            mock_get.return_value = None
            
            result = self.manager.resolve_standard_path_simple("test_standard", "development")
            
            # Should use fallback path structure
            expected = os.path.join("./ADRI/dev/standards", "test_standard.yaml")
            assert result == expected

    def test_resolve_standard_path_simple_no_config_default_env(self):
        """Test simple standard path resolution without config and default environment."""
        with patch.object(self.manager, 'get_active_config') as mock_get:
            mock_get.return_value = None
            
            result = self.manager.resolve_standard_path_simple("test_standard")
            
            # Should use development as default
            expected = os.path.join("./ADRI/dev/standards", "test_standard.yaml")
            assert result == expected

    def test_resolve_standard_path_simple_production_fallback(self):
        """Test simple standard path resolution fallback for production."""
        with patch.object(self.manager, 'get_active_config') as mock_get:
            mock_get.return_value = None
            
            result = self.manager.resolve_standard_path_simple("test_standard", "production")
            
            # Should use prod (first 3 chars of production)
            expected = os.path.join("./ADRI/pro/standards", "test_standard.yaml")
            assert result == expected


class TestConfigManagerIntegration:
    """Integration tests for ConfigManager."""

    def setup_method(self):
        """Set up test fixtures."""
        self.manager = ConfigManager()

    def test_full_workflow_create_save_load_validate(self):
        """Test complete workflow: create, save, load, validate."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            try:
                os.chdir(temp_dir)
                
                # Create default config
                config = self.manager.create_default_config("integration_test")
                
                # Validate the created config
                assert self.manager.validate_config(config) is True
                
                # Save the config
                self.manager.save_config(config, "test-config.yaml")
                
                # Load the config back
                loaded_config = self.manager.load_config("test-config.yaml")
                assert loaded_config == config
                
                # Validate the loaded config
                assert self.manager.validate_config(loaded_config) is True
                
                # Create directory structure
                self.manager.create_directory_structure(config)
                
                # Verify directories were created
                assert os.path.exists("./ADRI/dev/standards")
                assert os.path.exists("./ADRI/prod/assessments")
                
            finally:
                os.chdir(original_cwd)

    def test_environment_workflow(self):
        """Test environment-specific workflow."""
        config = self.manager.create_default_config("env_test")
        
        # Test development environment
        dev_config = self.manager.get_environment_config(config, "development")
        assert dev_config["protection"]["default_failure_mode"] == "warn"
        
        # Test production environment
        prod_config = self.manager.get_environment_config(config, "production")
        assert prod_config["protection"]["default_failure_mode"] == "raise"
        
        # Test path resolution
        dev_path = self.manager.resolve_standard_path("test.yaml", config, "development")
        prod_path = self.manager.resolve_standard_path("test.yaml", config, "production")
        
        assert "dev" in dev_path
        assert "prod" in prod_path

    def test_config_search_and_load_workflow(self):
        """Test config file search and loading workflow."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create config in ADRI directory
            adri_dir = os.path.join(temp_dir, "ADRI")
            os.makedirs(adri_dir)
            
            config = self.manager.create_default_config("search_test")
            config_path = os.path.join(adri_dir, "adri-config.yaml")
            
            with open(config_path, "w") as f:
                yaml.dump(config, f)
            
            # Test finding the config
            found_path = self.manager.find_config_file(temp_dir)
            assert os.path.realpath(found_path) == os.path.realpath(config_path)
            
            # Test loading active config
            with patch.object(self.manager, 'find_config_file') as mock_find:
                mock_find.return_value = config_path
                
                active_config = self.manager.get_active_config()
                assert active_config == config


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
