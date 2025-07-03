"""
Test suite for 'adri setup' command.

Following TDD methodology:
1. RED: These tests will fail initially (no implementation yet)
2. GREEN: We'll implement minimal code to make them pass
3. REFACTOR: We'll improve the implementation while keeping tests green
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

# These imports will fail initially - that's expected in TDD
try:
    from adri.cli.commands import setup_command
    from adri.config.manager import ConfigManager
except ImportError:
    # Expected during TDD - we haven't implemented these yet
    setup_command = None
    ConfigManager = None


class TestSetupCommand:
    """Test cases for the 'adri setup' command."""

    def test_setup_creates_config_file(self, tmp_path):
        """
        RED: Test that 'adri setup' creates adri-config.yaml

        This test defines the expected behavior:
        - Running setup should create a config file
        - Config file should be named 'adri-config.yaml'
        - Config file should exist in current directory
        """
        # Arrange
        os.chdir(tmp_path)

        # Act
        if setup_command:
            result = setup_command()
        else:
            pytest.skip("setup_command not implemented yet")

        # Assert
        config_file = tmp_path / "adri-config.yaml"
        assert config_file.exists(), "adri-config.yaml should be created"
        assert result == 0, "setup command should return success (0)"

    def test_setup_creates_directory_structure(self, tmp_path):
        """
        RED: Test that 'adri setup' creates the expected directory structure

        Expected structure:
        ADRI/
        ├── dev/
        │   ├── standards/
        │   ├── assessments/
        │   └── training-data/
        ├── prod/
        │   ├── standards/
        │   ├── assessments/
        │   └── training-data/
        └── .adri/cache/
        """
        # Arrange
        os.chdir(tmp_path)

        # Act
        if setup_command:
            result = setup_command()
        else:
            pytest.skip("setup_command not implemented yet")

        # Assert - Check all expected directories exist
        expected_dirs = [
            "ADRI/dev/standards",
            "ADRI/dev/assessments",
            "ADRI/dev/training-data",
            "ADRI/prod/standards",
            "ADRI/prod/assessments",
            "ADRI/prod/training-data",
            ".adri/cache",
        ]

        for dir_path in expected_dirs:
            full_path = tmp_path / dir_path
            assert full_path.exists(), f"Directory {dir_path} should be created"
            assert full_path.is_dir(), f"{dir_path} should be a directory"

    def test_setup_creates_valid_config_content(self, tmp_path):
        """
        RED: Test that the generated config file has valid YAML structure
        and contains expected configuration sections.
        """
        # Arrange
        os.chdir(tmp_path)

        # Act
        if setup_command:
            result = setup_command()
        else:
            pytest.skip("setup_command not implemented yet")

        # Assert
        config_file = tmp_path / "adri-config.yaml"
        assert config_file.exists()

        # Load and validate YAML structure
        with open(config_file, "r") as f:
            config = yaml.safe_load(f)

        # Check required top-level structure
        assert "adri" in config, "Config should have 'adri' root section"
        adri_config = config["adri"]

        # Check required sections
        assert "version" in adri_config, "Config should specify version"
        assert "project_name" in adri_config, "Config should have project_name"
        assert "environments" in adri_config, "Config should have environments"
        assert (
            "default_environment" in adri_config
        ), "Config should have default_environment"

        # Check environments structure
        environments = adri_config["environments"]
        assert "development" in environments, "Should have development environment"
        assert "production" in environments, "Should have production environment"

        # Check environment paths
        dev_env = environments["development"]
        assert "paths" in dev_env, "Development environment should have paths"
        dev_paths = dev_env["paths"]
        assert "standards" in dev_paths, "Should have standards path"
        assert "assessments" in dev_paths, "Should have assessments path"
        assert "training_data" in dev_paths, "Should have training_data path"

    def test_setup_handles_existing_config(self, tmp_path):
        """
        RED: Test that 'adri setup' handles existing configuration appropriately

        Expected behavior:
        - If config exists, should exit with error message
        - Should suggest using --force to overwrite
        - Should not modify existing config without --force
        """
        # Arrange
        os.chdir(tmp_path)
        existing_config = tmp_path / "adri-config.yaml"
        existing_content = "existing: config\ndata: should_not_change"
        existing_config.write_text(existing_content)

        # Act
        if setup_command:
            result = setup_command()
        else:
            pytest.skip("setup_command not implemented yet")

        # Assert
        assert result != 0, "Should return error code when config exists"

        # Config should be unchanged
        assert (
            existing_config.read_text() == existing_content
        ), "Existing config should not be modified"

    def test_setup_force_overwrites_existing_config(self, tmp_path):
        """
        RED: Test that 'adri setup --force' overwrites existing configuration
        """
        # Arrange
        os.chdir(tmp_path)
        existing_config = tmp_path / "adri-config.yaml"
        existing_config.write_text("old: config")

        # Act
        if setup_command:
            result = setup_command(force=True)
        else:
            pytest.skip("setup_command not implemented yet")

        # Assert
        assert result == 0, "Should succeed with --force"

        # Config should be replaced with new content
        with open(existing_config, "r") as f:
            new_config = yaml.safe_load(f)

        assert "adri" in new_config, "Should have new ADRI config structure"
        assert "old" not in new_config, "Old config should be replaced"
        assert new_config["adri"]["version"] == "2.0", "Should have new config version"

    def test_setup_custom_project_name(self, tmp_path):
        """
        RED: Test that 'adri setup --project-name' sets custom project name
        """
        # Arrange
        os.chdir(tmp_path)
        custom_name = "my-custom-project"

        # Act
        if setup_command:
            result = setup_command(project_name=custom_name)
        else:
            pytest.skip("setup_command not implemented yet")

        # Assert
        config_file = tmp_path / "adri-config.yaml"
        with open(config_file, "r") as f:
            config = yaml.safe_load(f)

        assert (
            config["adri"]["project_name"] == custom_name
        ), "Should use custom project name"

    def test_setup_default_project_name_from_directory(self, tmp_path):
        """
        RED: Test that setup uses current directory name as default project name
        """
        # Arrange
        project_dir = tmp_path / "test-project-dir"
        project_dir.mkdir()
        os.chdir(project_dir)

        # Act
        if setup_command:
            result = setup_command()
        else:
            pytest.skip("setup_command not implemented yet")

        # Assert
        config_file = project_dir / "adri-config.yaml"
        with open(config_file, "r") as f:
            config = yaml.safe_load(f)

        assert (
            config["adri"]["project_name"] == "test-project-dir"
        ), "Should use directory name as default project name"

    def test_setup_permission_error_handling(self, tmp_path):
        """
        RED: Test that setup handles permission errors gracefully
        """
        # Arrange - Create a read-only directory
        readonly_dir = tmp_path / "readonly"
        readonly_dir.mkdir()
        os.chdir(readonly_dir)
        readonly_dir.chmod(0o444)  # Read-only

        try:
            # Act
            if setup_command:
                result = setup_command()
            else:
                pytest.skip("setup_command not implemented yet")

            # Assert
            assert result != 0, "Should return error code for permission issues"

        finally:
            # Cleanup - restore permissions
            readonly_dir.chmod(0o755)


class TestConfigManager:
    """Test cases for the ConfigManager class."""

    def test_config_manager_creates_default_config(self):
        """
        RED: Test that ConfigManager can create a default configuration
        """
        if ConfigManager:
            manager = ConfigManager()
            config = manager.create_default_config("test-project")
        else:
            pytest.skip("ConfigManager not implemented yet")

        # Assert structure
        assert isinstance(config, dict)
        assert "adri" in config
        assert config["adri"]["project_name"] == "test-project"
        assert config["adri"]["version"] == "2.0"

    def test_config_manager_validates_config(self):
        """
        RED: Test that ConfigManager validates configuration structure
        """
        if ConfigManager:
            manager = ConfigManager()

            # Valid config should pass
            valid_config = {
                "adri": {
                    "version": "2.0",
                    "project_name": "test",
                    "environments": {
                        "development": {
                            "paths": {
                                "standards": "./ADRI/dev/standards",
                                "assessments": "./ADRI/dev/assessments",
                                "training_data": "./ADRI/dev/training-data",
                            }
                        }
                    },
                    "default_environment": "development",
                }
            }

            assert manager.validate_config(valid_config) == True

            # Invalid config should fail
            invalid_config = {"invalid": "structure"}
            assert manager.validate_config(invalid_config) == False
        else:
            pytest.skip("ConfigManager not implemented yet")


# Test fixtures and utilities
@pytest.fixture
def sample_config():
    """Fixture providing a sample valid configuration."""
    return {
        "adri": {
            "version": "2.0",
            "project_name": "test-project",
            "environments": {
                "development": {
                    "paths": {
                        "standards": "./ADRI/dev/standards",
                        "assessments": "./ADRI/dev/assessments",
                        "training_data": "./ADRI/dev/training-data",
                    }
                },
                "production": {
                    "paths": {
                        "standards": "./ADRI/prod/standards",
                        "assessments": "./ADRI/prod/assessments",
                        "training_data": "./ADRI/prod/training-data",
                    }
                },
            },
            "default_environment": "development",
        }
    }


if __name__ == "__main__":
    # Run tests with: python -m pytest tests/unit/cli/test_setup_command.py -v
    pytest.main([__file__, "-v"])
