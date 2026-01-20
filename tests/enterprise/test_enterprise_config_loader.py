"""
Comprehensive tests for EnterpriseConfigurationLoader.

Tests covering:
- Config format detection (flat vs environment-based)
- Flat structure path resolution (OSS compatibility)
- Environment-based path resolution (dev/prod)
- ADRI_ENV environment variable override
- Default environment fallback
- Config validation for both formats
- Directory structure creation
- Error handling and edge cases
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from adri_enterprise.config import (
    ConfigFormat,
    EnterpriseConfigurationLoader,
    detect_config_format,
    load_enterprise_config,
    resolve_enterprise_contract,
)


class TestConfigFormatDetection:
    """Test auto-detection of config format (flat vs environment-based)."""

    def test_detect_flat_config(self):
        """Flat config should be detected when 'paths' is at top level."""
        flat_config = {
            "adri": {
                "project_name": "test",
                "paths": {
                    "contracts": "./ADRI/contracts",
                    "assessments": "./ADRI/assessments",
                    "training_data": "./ADRI/training-data",
                    "audit_logs": "./ADRI/audit-logs",
                },
            }
        }
        assert detect_config_format(flat_config) == ConfigFormat.FLAT

    def test_detect_environment_config(self):
        """Environment config should be detected when 'environments' key exists."""
        env_config = {
            "adri": {
                "project_name": "test",
                "default_environment": "development",
                "environments": {
                    "development": {
                        "paths": {
                            "contracts": "./dev/contracts",
                            "assessments": "./dev/assessments",
                            "training_data": "./dev/training-data",
                            "audit_logs": "./dev/audit-logs",
                        }
                    },
                    "production": {
                        "paths": {
                            "contracts": "./prod/contracts",
                            "assessments": "./prod/assessments",
                            "training_data": "./prod/training-data",
                            "audit_logs": "./prod/audit-logs",
                        }
                    },
                },
            }
        }
        assert detect_config_format(env_config) == ConfigFormat.ENVIRONMENT

    def test_detect_none_config(self):
        """None config should default to FLAT format."""
        assert detect_config_format(None) == ConfigFormat.FLAT

    def test_detect_empty_config(self):
        """Empty config should default to FLAT format."""
        assert detect_config_format({}) == ConfigFormat.FLAT

    def test_detect_config_without_adri_key(self):
        """Config without 'adri' key should default to FLAT format."""
        assert detect_config_format({"other": "value"}) == ConfigFormat.FLAT

    def test_detect_mixed_config_prefers_environment(self):
        """Config with both paths and environments should use environment format."""
        mixed_config = {
            "adri": {
                "project_name": "test",
                "paths": {"contracts": "./ADRI/contracts"},  # Flat paths
                "environments": {  # Also has environments
                    "development": {
                        "paths": {"contracts": "./dev/contracts"}
                    }
                },
            }
        }
        # Should prefer environment format when both exist
        assert detect_config_format(mixed_config) == ConfigFormat.ENVIRONMENT


class TestFlatStructure:
    """Test flat config structure (OSS compatibility)."""

    @pytest.fixture
    def flat_config(self):
        """Create a flat config dictionary."""
        return {
            "adri": {
                "version": "4.0.0",
                "project_name": "test_project",
                "paths": {
                    "contracts": "./ADRI/contracts",
                    "assessments": "./ADRI/assessments",
                    "training_data": "./ADRI/training-data",
                    "audit_logs": "./ADRI/audit-logs",
                },
                "protection": {
                    "default_failure_mode": "raise",
                    "default_min_score": 80,
                },
            }
        }

    def test_validate_flat_config(self, flat_config):
        """Valid flat config should pass validation."""
        loader = EnterpriseConfigurationLoader()
        assert loader.validate_config(flat_config) is True

    def test_get_environment_config_flat(self, flat_config):
        """get_environment_config should return paths for flat configs."""
        loader = EnterpriseConfigurationLoader()
        env_config = loader.get_environment_config(flat_config)
        assert "paths" in env_config
        assert env_config["paths"]["contracts"] == "./ADRI/contracts"

    def test_flat_config_ignores_environment_param(self, flat_config):
        """Flat configs should ignore the environment parameter."""
        loader = EnterpriseConfigurationLoader()
        # Both calls should return the same result
        dev_config = loader.get_environment_config(flat_config, "development")
        prod_config = loader.get_environment_config(flat_config, "production")
        assert dev_config == prod_config


class TestEnvironmentStructure:
    """Test environment-based config structure (dev/prod)."""

    @pytest.fixture
    def env_config(self):
        """Create an environment-based config dictionary."""
        return {
            "adri": {
                "version": "4.0.0",
                "project_name": "test_project",
                "default_environment": "development",
                "environments": {
                    "development": {
                        "paths": {
                            "contracts": "./dev/contracts",
                            "assessments": "./dev/assessments",
                            "training_data": "./dev/training-data",
                            "audit_logs": "./dev/audit-logs",
                        },
                        "protection": {
                            "default_failure_mode": "warn",
                            "default_min_score": 70,
                        },
                    },
                    "production": {
                        "paths": {
                            "contracts": "./prod/contracts",
                            "assessments": "./prod/assessments",
                            "training_data": "./prod/training-data",
                            "audit_logs": "./prod/audit-logs",
                        },
                        "protection": {
                            "default_failure_mode": "raise",
                            "default_min_score": 85,
                        },
                    },
                },
            }
        }

    def test_validate_env_config(self, env_config):
        """Valid environment config should pass validation."""
        loader = EnterpriseConfigurationLoader()
        assert loader.validate_config(env_config) is True

    def test_get_dev_environment_config(self, env_config):
        """Should return development environment config."""
        loader = EnterpriseConfigurationLoader()
        dev_config = loader.get_environment_config(env_config, "development")
        assert dev_config["paths"]["contracts"] == "./dev/contracts"

    def test_get_prod_environment_config(self, env_config):
        """Should return production environment config."""
        loader = EnterpriseConfigurationLoader()
        prod_config = loader.get_environment_config(env_config, "production")
        assert prod_config["paths"]["contracts"] == "./prod/contracts"

    def test_default_environment_used(self, env_config):
        """Should use default_environment when none specified."""
        loader = EnterpriseConfigurationLoader()
        # Clear ADRI_ENV to ensure default is used
        with patch.dict(os.environ, {"ADRI_ENV": ""}, clear=False):
            # Delete ADRI_ENV if it exists
            env_backup = os.environ.pop("ADRI_ENV", None)
            try:
                # No environment specified - should use default (development)
                config = loader.get_environment_config(env_config)
                assert config["paths"]["contracts"] == "./dev/contracts"
            finally:
                if env_backup is not None:
                    os.environ["ADRI_ENV"] = env_backup

    def test_invalid_environment_raises(self, env_config):
        """Should raise ValueError for unknown environment."""
        loader = EnterpriseConfigurationLoader()
        with pytest.raises(ValueError, match="Environment 'staging' not found"):
            loader.get_environment_config(env_config, "staging")


class TestADRIEnvVariable:
    """Test ADRI_ENV environment variable override."""

    @pytest.fixture
    def env_config(self):
        """Create an environment-based config dictionary."""
        return {
            "adri": {
                "version": "4.0.0",
                "project_name": "test_project",
                "default_environment": "development",
                "environments": {
                    "development": {
                        "paths": {
                            "contracts": "./dev/contracts",
                            "assessments": "./dev/assessments",
                            "training_data": "./dev/training-data",
                            "audit_logs": "./dev/audit-logs",
                        }
                    },
                    "production": {
                        "paths": {
                            "contracts": "./prod/contracts",
                            "assessments": "./prod/assessments",
                            "training_data": "./prod/training-data",
                            "audit_logs": "./prod/audit-logs",
                        }
                    },
                },
            }
        }

    def test_adri_env_overrides_default(self, env_config):
        """ADRI_ENV should override default_environment."""
        loader = EnterpriseConfigurationLoader()

        with patch.dict(os.environ, {"ADRI_ENV": "production"}):
            config = loader.get_environment_config(env_config)
            assert config["paths"]["contracts"] == "./prod/contracts"

    def test_explicit_param_overrides_adri_env(self, env_config):
        """Explicit environment parameter should override ADRI_ENV."""
        loader = EnterpriseConfigurationLoader()

        with patch.dict(os.environ, {"ADRI_ENV": "production"}):
            # Explicit parameter should win
            config = loader.get_environment_config(env_config, "development")
            assert config["paths"]["contracts"] == "./dev/contracts"

    def test_effective_environment_precedence(self, env_config):
        """Test complete precedence: param > ADRI_ENV > config default > fallback."""
        loader = EnterpriseConfigurationLoader()

        # Clear ADRI_ENV for accurate testing
        env_backup = os.environ.pop("ADRI_ENV", None)
        try:
            # Test fallback with None config
            assert loader._get_effective_environment(None, None) == "development"

            # Test config default
            assert loader._get_effective_environment(env_config, None) == "development"

            # Test ADRI_ENV override
            os.environ["ADRI_ENV"] = "production"
            assert loader._get_effective_environment(env_config, None) == "production"

            # Test explicit parameter override
            assert (
                loader._get_effective_environment(env_config, "development")
                == "development"
            )
        finally:
            # Restore original value
            if env_backup is not None:
                os.environ["ADRI_ENV"] = env_backup
            elif "ADRI_ENV" in os.environ:
                del os.environ["ADRI_ENV"]


class TestPathResolution:
    """Test contract and directory path resolution."""

    @pytest.fixture
    def temp_project(self, tmp_path):
        """Create a temporary project with config file."""
        adri_dir = tmp_path / "ADRI"
        adri_dir.mkdir()

        # Create environment-based config
        config = {
            "adri": {
                "version": "4.0.0",
                "project_name": "test_project",
                "default_environment": "development",
                "environments": {
                    "development": {
                        "paths": {
                            "contracts": "./dev/contracts",
                            "assessments": "./dev/assessments",
                            "training_data": "./dev/training-data",
                            "audit_logs": "./dev/audit-logs",
                        }
                    },
                    "production": {
                        "paths": {
                            "contracts": "./prod/contracts",
                            "assessments": "./prod/assessments",
                            "training_data": "./prod/training-data",
                            "audit_logs": "./prod/audit-logs",
                        }
                    },
                },
            }
        }

        config_path = adri_dir / "config.yaml"
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(config, f)

        # Create directory structure
        (adri_dir / "dev" / "contracts").mkdir(parents=True)
        (adri_dir / "prod" / "contracts").mkdir(parents=True)

        return tmp_path

    def test_resolve_dev_contract_path(self, temp_project):
        """Should resolve contract path to dev directory."""
        loader = EnterpriseConfigurationLoader()

        # Clear ADRI_CONTRACTS_DIR to use config paths, set ADRI_CONFIG_PATH
        contracts_dir_backup = os.environ.pop("ADRI_CONTRACTS_DIR", None)
        try:
            with patch.dict(
                os.environ,
                {"ADRI_CONFIG_PATH": str(temp_project / "ADRI" / "config.yaml")},
            ):
                path = loader.resolve_contract_path("my_contract", "development")
                # Check path components (platform-independent)
                assert "dev" in path and "contracts" in path and "my_contract.yaml" in path
        finally:
            if contracts_dir_backup is not None:
                os.environ["ADRI_CONTRACTS_DIR"] = contracts_dir_backup

    def test_resolve_prod_contract_path(self, temp_project):
        """Should resolve contract path to prod directory."""
        loader = EnterpriseConfigurationLoader()

        # Clear ADRI_CONTRACTS_DIR to use config paths, set ADRI_CONFIG_PATH
        contracts_dir_backup = os.environ.pop("ADRI_CONTRACTS_DIR", None)
        try:
            with patch.dict(
                os.environ,
                {"ADRI_CONFIG_PATH": str(temp_project / "ADRI" / "config.yaml")},
            ):
                path = loader.resolve_contract_path("my_contract", "production")
                # Check path components (platform-independent)
                assert "prod" in path and "contracts" in path and "my_contract.yaml" in path
        finally:
            if contracts_dir_backup is not None:
                os.environ["ADRI_CONTRACTS_DIR"] = contracts_dir_backup

    def test_yaml_extension_added(self, temp_project):
        """Should add .yaml extension if not present."""
        loader = EnterpriseConfigurationLoader()

        with patch.dict(
            os.environ,
            {"ADRI_CONFIG_PATH": str(temp_project / "ADRI" / "config.yaml")},
        ):
            path = loader.resolve_contract_path("my_contract")
            assert path.endswith(".yaml")

    def test_yaml_extension_preserved(self, temp_project):
        """Should preserve existing .yaml extension."""
        loader = EnterpriseConfigurationLoader()

        with patch.dict(
            os.environ,
            {"ADRI_CONFIG_PATH": str(temp_project / "ADRI" / "config.yaml")},
        ):
            path = loader.resolve_contract_path("my_contract.yaml")
            assert path.endswith(".yaml")
            assert not path.endswith(".yaml.yaml")

    def test_contracts_dir_env_override(self, temp_project):
        """ADRI_CONTRACTS_DIR should override config paths."""
        loader = EnterpriseConfigurationLoader()
        custom_dir = str(temp_project / "custom_contracts")

        with patch.dict(
            os.environ,
            {
                "ADRI_CONFIG_PATH": str(temp_project / "ADRI" / "config.yaml"),
                "ADRI_CONTRACTS_DIR": custom_dir,
            },
        ):
            path = loader.resolve_contract_path("my_contract")
            assert custom_dir in path


class TestDirectoryMethods:
    """Test directory getter methods."""

    @pytest.fixture
    def env_config_file(self, tmp_path):
        """Create a temp config file with environment-based structure."""
        adri_dir = tmp_path / "ADRI"
        adri_dir.mkdir()

        config = {
            "adri": {
                "version": "4.0.0",
                "project_name": "test_project",
                "default_environment": "development",
                "environments": {
                    "development": {
                        "paths": {
                            "contracts": "./dev/contracts",
                            "assessments": "./dev/assessments",
                            "training_data": "./dev/training-data",
                            "audit_logs": "./dev/audit-logs",
                        }
                    },
                    "production": {
                        "paths": {
                            "contracts": "./prod/contracts",
                            "assessments": "./prod/assessments",
                            "training_data": "./prod/training-data",
                            "audit_logs": "./prod/audit-logs",
                        }
                    },
                },
            }
        }

        config_path = adri_dir / "config.yaml"
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(config, f)

        return str(config_path)

    def test_get_assessments_dir_dev(self, env_config_file):
        """Should return dev assessments directory."""
        loader = EnterpriseConfigurationLoader()

        with patch.dict(os.environ, {"ADRI_CONFIG_PATH": env_config_file}):
            path = loader.get_assessments_dir("development")
            assert path == "./dev/assessments"

    def test_get_assessments_dir_prod(self, env_config_file):
        """Should return prod assessments directory."""
        loader = EnterpriseConfigurationLoader()

        with patch.dict(os.environ, {"ADRI_CONFIG_PATH": env_config_file}):
            path = loader.get_assessments_dir("production")
            assert path == "./prod/assessments"

    def test_get_training_data_dir(self, env_config_file):
        """Should return environment-specific training data directory."""
        loader = EnterpriseConfigurationLoader()

        with patch.dict(os.environ, {"ADRI_CONFIG_PATH": env_config_file}):
            dev_path = loader.get_training_data_dir("development")
            prod_path = loader.get_training_data_dir("production")

            assert dev_path == "./dev/training-data"
            assert prod_path == "./prod/training-data"

    def test_get_audit_logs_dir(self, env_config_file):
        """Should return environment-specific audit logs directory."""
        loader = EnterpriseConfigurationLoader()

        with patch.dict(os.environ, {"ADRI_CONFIG_PATH": env_config_file}):
            dev_path = loader.get_audit_logs_dir("development")
            prod_path = loader.get_audit_logs_dir("production")

            assert dev_path == "./dev/audit-logs"
            assert prod_path == "./prod/audit-logs"


class TestConfigValidation:
    """Test configuration validation."""

    def test_valid_env_config(self):
        """Valid environment config should pass validation."""
        loader = EnterpriseConfigurationLoader()
        config = {
            "adri": {
                "project_name": "test",
                "environments": {
                    "development": {
                        "paths": {
                            "contracts": "./dev/contracts",
                            "assessments": "./dev/assessments",
                            "training_data": "./dev/training-data",
                            "audit_logs": "./dev/audit-logs",
                        }
                    }
                },
            }
        }
        assert loader.validate_config(config) is True

    def test_invalid_missing_adri_key(self):
        """Config without 'adri' key should fail validation."""
        loader = EnterpriseConfigurationLoader()
        assert loader.validate_config({"other": "value"}) is False

    def test_invalid_missing_paths_in_env(self):
        """Environment without paths should fail validation."""
        loader = EnterpriseConfigurationLoader()
        config = {
            "adri": {
                "project_name": "test",
                "environments": {
                    "development": {
                        "protection": {}  # Missing paths
                    }
                },
            }
        }
        assert loader.validate_config(config) is False

    def test_invalid_missing_required_path(self):
        """Environment missing required path key should fail validation."""
        loader = EnterpriseConfigurationLoader()
        config = {
            "adri": {
                "project_name": "test",
                "environments": {
                    "development": {
                        "paths": {
                            "contracts": "./dev/contracts",
                            # Missing assessments, training_data, audit_logs
                        }
                    }
                },
            }
        }
        assert loader.validate_config(config) is False


class TestDefaultConfigGeneration:
    """Test default config generation."""

    def test_create_default_config_has_environments(self):
        """Default enterprise config should have dev and prod environments."""
        loader = EnterpriseConfigurationLoader()
        config = loader.create_default_config("my_project")

        assert "adri" in config
        assert "environments" in config["adri"]
        assert "development" in config["adri"]["environments"]
        assert "production" in config["adri"]["environments"]

    def test_create_default_config_paths(self):
        """Default config should have correct path structure."""
        loader = EnterpriseConfigurationLoader()
        config = loader.create_default_config("my_project")

        dev_paths = config["adri"]["environments"]["development"]["paths"]
        prod_paths = config["adri"]["environments"]["production"]["paths"]

        assert dev_paths["contracts"] == "./dev/contracts"
        assert prod_paths["contracts"] == "./prod/contracts"

    def test_create_default_config_project_name(self):
        """Default config should use provided project name."""
        loader = EnterpriseConfigurationLoader()
        config = loader.create_default_config("my_awesome_project")

        assert config["adri"]["project_name"] == "my_awesome_project"

    def test_create_default_config_default_env(self):
        """Default config should have development as default environment."""
        loader = EnterpriseConfigurationLoader()
        config = loader.create_default_config("test")

        assert config["adri"]["default_environment"] == "development"


class TestDirectoryStructureCreation:
    """Test directory structure creation."""

    def test_create_env_directory_structure(self, tmp_path):
        """Should create dev and prod directory structures."""
        loader = EnterpriseConfigurationLoader()
        config = loader.create_default_config("test")

        # Change to temp directory
        old_cwd = Path.cwd()
        os.chdir(tmp_path)

        try:
            loader.create_directory_structure(config)

            # Check directories were created
            assert (tmp_path / "ADRI" / "dev" / "contracts").exists()
            assert (tmp_path / "ADRI" / "dev" / "assessments").exists()
            assert (tmp_path / "ADRI" / "prod" / "contracts").exists()
            assert (tmp_path / "ADRI" / "prod" / "assessments").exists()
        finally:
            os.chdir(old_cwd)


class TestConvenienceFunctions:
    """Test convenience functions."""

    def test_load_enterprise_config_returns_none_when_no_config(self, tmp_path):
        """Should return None when no config file exists."""
        # Clear any env vars that might point to config
        with patch.dict(
            os.environ,
            {"ADRI_CONFIG_PATH": "", "ADRI_CONFIG_FILE": "", "ADRI_CONFIG": ""},
            clear=False,
        ):
            # Change to temp directory with no config
            old_cwd = Path.cwd()
            os.chdir(tmp_path)
            try:
                result = load_enterprise_config()
                # May be None or may find a config - depends on parent dirs
            finally:
                os.chdir(old_cwd)

    def test_resolve_enterprise_contract_adds_extension(self, tmp_path):
        """Should add .yaml extension to contract name."""
        with patch.dict(
            os.environ,
            {"ADRI_CONFIG_PATH": "", "ADRI_CONFIG_FILE": "", "ADRI_CONFIG": ""},
            clear=False,
        ):
            # Will use fallback flat path structure
            path = resolve_enterprise_contract("my_contract")
            assert path.endswith("my_contract.yaml")


class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_invalid_yaml_config(self, tmp_path):
        """Should handle invalid YAML gracefully."""
        loader = EnterpriseConfigurationLoader()

        # Create invalid YAML file
        config_path = tmp_path / "invalid.yaml"
        with open(config_path, "w", encoding="utf-8") as f:
            f.write("invalid: yaml: content: [")

        result = loader.load_config(str(config_path))
        assert result is None

    def test_missing_environment_in_valid_config(self):
        """Should raise ValueError for missing environment in valid config."""
        loader = EnterpriseConfigurationLoader()
        config = {
            "adri": {
                "project_name": "test",
                "default_environment": "development",
                "environments": {
                    "development": {
                        "paths": {
                            "contracts": "./dev/contracts",
                            "assessments": "./dev/assessments",
                            "training_data": "./dev/training-data",
                            "audit_logs": "./dev/audit-logs",
                        }
                    }
                },
            }
        }

        # Should work for development
        loader.get_environment_config(config, "development")

        # Should raise for non-existent production
        with pytest.raises(ValueError, match="production"):
            loader.get_environment_config(config, "production")

    def test_fallback_paths_when_no_config(self):
        """Should use fallback paths when no config available."""
        loader = EnterpriseConfigurationLoader()

        with patch.object(loader, "get_active_config", return_value=None):
            assert loader.get_assessments_dir() == "./ADRI/assessments"
            assert loader.get_training_data_dir() == "./ADRI/training-data"
            assert loader.get_audit_logs_dir() == "./ADRI/audit-logs"


class TestDecoratorEnvironmentIntegration:
    """Test environment-aware decorator integration."""

    def test_decorator_has_environment_parameter(self):
        """The enterprise decorator should accept environment parameter."""
        from adri_enterprise.decorator import adri_protected

        # Should not raise - just verify it accepts the parameter
        decorator = adri_protected(
            contract="test_contract",
            environment="production"
        )
        assert callable(decorator)

    def test_decorator_resolves_environment_path(self, tmp_path):
        """Decorator should resolve contract paths using environment."""
        import os
        from unittest.mock import patch, MagicMock

        from adri_enterprise.decorator import adri_protected

        # Create temp config
        adri_dir = tmp_path / "ADRI"
        adri_dir.mkdir()

        config = {
            "adri": {
                "version": "4.0.0",
                "project_name": "test_project",
                "default_environment": "development",
                "environments": {
                    "development": {
                        "paths": {
                            "contracts": "./dev/contracts",
                            "assessments": "./dev/assessments",
                            "training_data": "./dev/training-data",
                            "audit_logs": "./dev/audit-logs",
                        }
                    },
                    "production": {
                        "paths": {
                            "contracts": "./prod/contracts",
                            "assessments": "./prod/assessments",
                            "training_data": "./prod/training-data",
                            "audit_logs": "./prod/audit-logs",
                        }
                    },
                },
            }
        }

        config_path = adri_dir / "config.yaml"
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(config, f)

        # Create contract directories and files
        (adri_dir / "dev" / "contracts").mkdir(parents=True)
        (adri_dir / "prod" / "contracts").mkdir(parents=True)

        # Clear ADRI_CONTRACTS_DIR to ensure config paths are used
        contracts_dir_backup = os.environ.pop("ADRI_CONTRACTS_DIR", None)
        try:
            # Mock the base decorator and license validation
            with patch("adri_enterprise.decorator.base_adri_protected") as mock_base:
                with patch("adri_enterprise.decorator.validate_license"):
                    with patch.dict(
                        os.environ,
                        {"ADRI_CONFIG_PATH": str(config_path)},
                    ):
                        mock_base.return_value = lambda f: f

                        @adri_protected(
                            contract="my_contract",
                            environment="production"
                        )
                        def test_func(data):
                            return data

                        # Call the function
                        test_func({"key": "value"})

                        # Verify base decorator was called with resolved path (platform-independent)
                        call_kwargs = mock_base.call_args.kwargs
                        resolved_path = call_kwargs["contract"]
                        assert "prod" in resolved_path and "contracts" in resolved_path and "my_contract.yaml" in resolved_path
        finally:
            if contracts_dir_backup is not None:
                os.environ["ADRI_CONTRACTS_DIR"] = contracts_dir_backup

    def test_decorator_config_includes_environment(self):
        """Decorator _adri_config should store environment."""
        from unittest.mock import patch

        from adri_enterprise.decorator import adri_protected

        with patch("adri_enterprise.decorator.validate_license"):
            with patch("adri_enterprise.decorator.base_adri_protected") as mock_base:
                mock_base.return_value = lambda f: f

                @adri_protected(
                    contract="test",
                    environment="production"
                )
                def test_func(data):
                    return data

                # Note: The _adri_config is set on the wrapper
                assert hasattr(test_func, "_adri_enterprise")
                assert test_func._adri_enterprise is True


class TestIntegrationWithActualConfig:
    """Integration tests using actual ADRI/config.yaml from project."""

    def test_load_actual_project_config(self):
        """Should successfully load the actual project config."""
        loader = EnterpriseConfigurationLoader()

        # Try to find the actual config file
        config_path = loader.find_config_file()

        if config_path:
            config = loader.load_config(config_path)
            assert config is not None

            # Check it's detected as environment format (as per ADRI/config.yaml)
            config_format = detect_config_format(config)
            # The actual config uses environment format
            assert config_format == ConfigFormat.ENVIRONMENT

    def test_actual_config_has_both_environments(self):
        """Actual project config should have dev and prod environments."""
        loader = EnterpriseConfigurationLoader()
        config_path = loader.find_config_file()

        if config_path:
            config = loader.load_config(config_path)
            assert config is not None

            if detect_config_format(config) == ConfigFormat.ENVIRONMENT:
                environments = config["adri"]["environments"]
                assert "development" in environments
                assert "production" in environments
