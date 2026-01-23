# @ADRI_FEATURE[test_package_context_resolution, scope=OPEN_SOURCE]
# Description: Unit tests for package-local contract resolution feature
"""
Unit tests for Package Context Resolution feature.

Tests the new package_context parameter that enables resolution of contracts
from package-local directories (e.g., playbooks with their own adri/ folders).
"""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from adri.config.loader import ConfigurationLoader
from adri.config.types import ContractResolutionResult, ResolutionConfig, ResolutionStrategy


class TestResolutionStrategy:
    """Tests for ResolutionStrategy enum."""

    def test_strategy_values(self):
        """Test that all expected strategy values exist."""
        assert ResolutionStrategy.FLAT.value == "flat"
        assert ResolutionStrategy.PACKAGE_LOCAL.value == "package_local"
        assert ResolutionStrategy.HYBRID.value == "hybrid"

    def test_strategy_from_string(self):
        """Test creating strategy from string value."""
        assert ResolutionStrategy("flat") == ResolutionStrategy.FLAT
        assert ResolutionStrategy("package_local") == ResolutionStrategy.PACKAGE_LOCAL
        assert ResolutionStrategy("hybrid") == ResolutionStrategy.HYBRID


class TestContractResolutionResult:
    """Tests for ContractResolutionResult dataclass."""

    def test_basic_result(self):
        """Test creating a basic result."""
        result = ContractResolutionResult(
            path="/path/to/contract.yaml",
            source="package_local",
        )
        assert result.path == "/path/to/contract.yaml"
        assert result.source == "package_local"
        assert result.package_context is None
        assert result.exists is False
        assert result.strategy_used is None

    def test_full_result(self):
        """Test creating a result with all fields."""
        result = ContractResolutionResult(
            path="/path/to/playbook/adri/contract.yaml",
            source="package_local",
            package_context="/path/to/playbook",
            exists=True,
            strategy_used=ResolutionStrategy.HYBRID,
        )
        assert result.path == "/path/to/playbook/adri/contract.yaml"
        assert result.source == "package_local"
        assert result.package_context == "/path/to/playbook"
        assert result.exists is True
        assert result.strategy_used == ResolutionStrategy.HYBRID


class TestResolutionConfig:
    """Tests for ResolutionConfig dataclass."""

    def test_default_config(self):
        """Test default configuration values."""
        config = ResolutionConfig()
        assert config.strategy == ResolutionStrategy.HYBRID
        assert config.package_subdirectory == "adri"
        assert config.fallback_enabled is True

    def test_custom_config(self):
        """Test custom configuration."""
        config = ResolutionConfig(
            strategy=ResolutionStrategy.PACKAGE_LOCAL,
            package_subdirectory="contracts",
            fallback_enabled=False,
        )
        assert config.strategy == ResolutionStrategy.PACKAGE_LOCAL
        assert config.package_subdirectory == "contracts"
        assert config.fallback_enabled is False


class TestConfigurationLoaderPackageContext:
    """Tests for package context resolution in ConfigurationLoader."""

    def test_get_resolution_config_default(self):
        """Test default resolution configuration."""
        loader = ConfigurationLoader()
        config = loader.get_resolution_config()

        assert isinstance(config, ResolutionConfig)
        assert config.strategy == ResolutionStrategy.HYBRID
        assert config.package_subdirectory == "adri"

    @patch.dict(os.environ, {"ADRI_RESOLUTION_STRATEGY": "package_local"})
    def test_get_resolution_config_from_env(self):
        """Test resolution config from environment variable."""
        loader = ConfigurationLoader()
        config = loader.get_resolution_config()

        assert config.strategy == ResolutionStrategy.PACKAGE_LOCAL

    @patch.dict(os.environ, {"ADRI_PACKAGE_SUBDIRECTORY": "contracts"})
    def test_get_subdirectory_from_env(self):
        """Test package subdirectory from environment variable."""
        loader = ConfigurationLoader()
        config = loader.get_resolution_config()

        assert config.package_subdirectory == "contracts"


class TestPackageLocalResolution:
    """Tests for package-local contract resolution."""

    def test_resolve_with_package_context_existing_contract(self):
        """Test resolution when contract exists in package directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Resolve symlinks (macOS /var -> /private/var)
            tmpdir = str(Path(tmpdir).resolve())

            # Create package with adri/ directory
            package_dir = Path(tmpdir) / "my_playbook"
            adri_dir = package_dir / "adri"
            adri_dir.mkdir(parents=True)

            # Use unique contract name to avoid conflicts with fixtures
            contract_name = "unique_test_contract_xyz123"
            contract_path = adri_dir / f"{contract_name}.yaml"
            contract_path.write_text(yaml.dump({
                "standard": {
                    "name": contract_name,
                    "fields": [{"name": "result", "type": "string"}]
                }
            }))

            # Clear env override to ensure package context takes priority
            with patch.dict(os.environ, {}, clear=False):
                # Remove ADRI_CONTRACTS_DIR if it exists
                env_copy = os.environ.copy()
                if "ADRI_CONTRACTS_DIR" in env_copy:
                    del env_copy["ADRI_CONTRACTS_DIR"]

                with patch.dict(os.environ, env_copy, clear=True):
                    loader = ConfigurationLoader()
                    resolved_path = loader.resolve_contract_path(
                        contract_name,
                        package_context=str(package_dir),
                    )

                    # Resolve both to handle macOS symlinks
                    assert Path(resolved_path).resolve() == contract_path.resolve()

    def test_resolve_with_package_context_fallback_to_centralized(self):
        """Test that package_context returns package-local path even when contract missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create package without the contract
            package_dir = Path(tmpdir) / "my_playbook"
            adri_dir = package_dir / "adri"
            adri_dir.mkdir(parents=True)

            # Clear config path to avoid picking up project config
            env_copy = os.environ.copy()
            env_copy.pop("ADRI_CONFIG_PATH", None)
            env_copy.pop("ADRI_CONTRACTS_DIR", None)

            with patch.dict(os.environ, env_copy, clear=True):
                loader = ConfigurationLoader()
                resolved_path = loader.resolve_contract_path(
                    "nonexistent_contract",
                    package_context=str(package_dir),
                )

                # With package_context provided, should return package-local path (not centralized)
                assert "nonexistent_contract.yaml" in resolved_path
                # Resolve both paths for macOS symlink comparison
                assert Path(package_dir).resolve() in Path(resolved_path).resolve().parents
                assert "adri" in resolved_path

    def test_resolve_without_package_context(self):
        """Test resolution without package context uses centralized."""
        loader = ConfigurationLoader()
        resolved_path = loader.resolve_contract_path("customer_data")

        # Should use centralized path
        assert "customer_data.yaml" in resolved_path
        # Centralized paths typically contain ADRI/contracts or similar
        assert "adri" in resolved_path.lower() or "ADRI" in resolved_path

    def test_resolve_adds_yaml_extension(self):
        """Test that .yaml extension is added if missing."""
        loader = ConfigurationLoader()
        resolved_path = loader.resolve_contract_path("my_contract")

        assert resolved_path.endswith(".yaml")

    def test_resolve_preserves_yaml_extension(self):
        """Test that existing .yaml extension is preserved."""
        loader = ConfigurationLoader()
        resolved_path = loader.resolve_contract_path("my_contract.yaml")

        assert resolved_path.endswith(".yaml")
        assert not resolved_path.endswith(".yaml.yaml")


class TestResolutionWithMetadata:
    """Tests for resolution with metadata (debugging support)."""

    def test_resolve_with_metadata_package_local(self):
        """Test resolution with metadata for package-local contract."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create package with contract
            package_dir = Path(tmpdir) / "my_playbook"
            adri_dir = package_dir / "adri"
            adri_dir.mkdir(parents=True)

            # Use unique name to avoid conflicts
            contract_name = "unique_metadata_test_abc789"
            contract_path = adri_dir / f"{contract_name}.yaml"
            contract_path.write_text(yaml.dump({"standard": {"name": contract_name}}))

            # Clear env override
            env_copy = os.environ.copy()
            if "ADRI_CONTRACTS_DIR" in env_copy:
                del env_copy["ADRI_CONTRACTS_DIR"]

            with patch.dict(os.environ, env_copy, clear=True):
                loader = ConfigurationLoader()
                result = loader.resolve_contract_path_with_metadata(
                    contract_name,
                    package_context=str(package_dir),
                )

                assert isinstance(result, ContractResolutionResult)
                assert result.source == "package_local"
                assert result.package_context == str(package_dir)
                assert result.exists is True

    @pytest.mark.skipif(sys.platform == "win32", reason="Windows path normalization (RUNNER~1 vs runneradmin)")
    def test_resolve_with_metadata_centralized_fallback(self):
        """Test resolution with metadata returns package-local when contract missing.
        
        NOTE: Skipped on Windows - path normalization differences (8.3 short names)
        cause false failures. Test passes on Unix/macOS."""
        with tempfile.TemporaryDirectory() as tmpdir:
            package_dir = Path(tmpdir) / "my_playbook"
            adri_dir = package_dir / "adri"
            adri_dir.mkdir(parents=True)
            # No contract file created - use unique name

            # Clear env override
            env_copy = os.environ.copy()
            if "ADRI_CONTRACTS_DIR" in env_copy:
                del env_copy["ADRI_CONTRACTS_DIR"]

            with patch.dict(os.environ, env_copy, clear=True):
                loader = ConfigurationLoader()
                result = loader.resolve_contract_path_with_metadata(
                    "totally_nonexistent_contract_xyz",
                    package_context=str(package_dir),
                )

                assert isinstance(result, ContractResolutionResult)
                # With package_context, source is "package_local" even when contract doesn't exist
                assert result.source == "package_local"
                assert result.exists is False
                assert str(package_dir) in result.path


class TestCustomSubdirectory:
    """Tests for custom package subdirectory."""

    def test_custom_subdirectory_via_env(self):
        """Test using custom subdirectory via environment variable."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Resolve symlinks (macOS /var -> /private/var)
            tmpdir = str(Path(tmpdir).resolve())

            # Create package with custom contracts/ directory
            package_dir = Path(tmpdir) / "my_playbook"
            contracts_dir = package_dir / "contracts"
            contracts_dir.mkdir(parents=True)

            # Use unique name to avoid conflicts
            contract_name = "unique_subdir_test_qrs456"
            contract_path = contracts_dir / f"{contract_name}.yaml"
            contract_path.write_text(yaml.dump({"standard": {"name": contract_name}}))

            # Clear env override and set custom subdirectory
            env_copy = os.environ.copy()
            if "ADRI_CONTRACTS_DIR" in env_copy:
                del env_copy["ADRI_CONTRACTS_DIR"]
            env_copy["ADRI_PACKAGE_SUBDIRECTORY"] = "contracts"

            with patch.dict(os.environ, env_copy, clear=True):
                loader = ConfigurationLoader()
                resolved_path = loader.resolve_contract_path(
                    contract_name,
                    package_context=str(package_dir),
                )

                # Resolve both to handle macOS symlinks
                assert Path(resolved_path).resolve() == contract_path.resolve()


class TestBackwardCompatibility:
    """Tests ensuring backward compatibility."""

    def test_no_package_context_works_same_as_before(self):
        """Test that calls without package_context work identically to before."""
        loader = ConfigurationLoader()

        # This should work exactly as before the feature was added
        resolved_path = loader.resolve_contract_path("customer_data")

        assert "customer_data.yaml" in resolved_path

    def test_none_package_context_same_as_no_context(self):
        """Test that explicit None package_context is same as omitting it."""
        loader = ConfigurationLoader()

        path_without = loader.resolve_contract_path("customer_data")
        path_with_none = loader.resolve_contract_path("customer_data", package_context=None)

        assert path_without == path_with_none


# @ADRI_FEATURE_END[test_package_context_resolution]
