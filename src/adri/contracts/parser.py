# @ADRI_FEATURE[contracts_parser, scope=OPEN_SOURCE]
# Description: YAML contract parsing and validation for ADRI data quality contracts
"""
ADRI Contracts Parser.

YAML contract parsing and validation functionality, migrated from adri/contracts/loader.py.
Provides offline-first loading of ADRI contracts from bundled contracts directory.
No network requests are made, ensuring enterprise-friendly operation and air-gap compatibility.
"""

import os
import threading
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

# Updated imports for new structure - with fallbacks during migration
try:
    from ..contracts.exceptions import (
        InvalidStandardError,
        StandardNotFoundError,
        StandardsDirectoryNotFoundError,
    )
except ImportError:
    try:
        from adri.contracts.exceptions import (
            InvalidStandardError,
            StandardNotFoundError,
            StandardsDirectoryNotFoundError,
        )
    except ImportError:
        # Fallback exception classes
        class StandardsDirectoryNotFoundError(Exception):
            """Exception raised when contracts directory is not found."""

        class StandardNotFoundError(Exception):
            """Exception raised when a contract is not found."""

        class InvalidStandardError(Exception):
            """Exception raised when a contract is invalid."""


class ContractsParser:
    """
    Parses and loads ADRI contracts from bundled contracts directory.

    This parser provides fast, offline access to all contracts
    without any network dependencies. All contracts are validated on
    loading to ensure they conform to the ADRI contract format.
    """

    def __init__(self):
        """Initialize the contracts parser."""

        self._lock = threading.RLock()
        self._contracts_path = self._get_contracts_path()
        self._validate_contracts_directory()

    @property
    def contracts_path(self) -> Path:
        """Get the path to the contracts directory."""

        return self._contracts_path

    def _get_contracts_path(self) -> Path:
        """Resolve contracts directory path from environment parameter only."""

        # Use consistent variable name: ADRI_CONTRACTS_DIR
        env_path = os.getenv("ADRI_CONTRACTS_DIR")
        if not env_path:
            raise StandardsDirectoryNotFoundError(
                "ADRI_CONTRACTS_DIR environment variable must be set. "
                "Set it to point to your contracts directory."
            )

        env_dir = Path(env_path)
        if not env_dir.exists():
            raise StandardsDirectoryNotFoundError(
                f"Contracts directory does not exist: {env_path}"
            )

        if not env_dir.is_dir():
            raise StandardsDirectoryNotFoundError(
                f"Contracts path is not a directory: {env_path}"
            )

        return env_dir.resolve()

    def _validate_contracts_directory(self):
        """Validate that the contracts directory exists."""

        if not self._contracts_path.exists():
            raise StandardsDirectoryNotFoundError(str(self._contracts_path))

        if not self._contracts_path.is_dir():
            raise StandardsDirectoryNotFoundError(
                f"Contracts path is not a directory: {self._contracts_path}"
            )

    @lru_cache(maxsize=128)
    def parse_contract(self, contract_name: str) -> dict[str, Any]:
        """
        Parse a contract by name.

        Args:
            contract_name: Name of the contract to parse (without .yaml extension)

        Returns:
            dict: The parsed and validated contract

        Raises:
            StandardNotFoundError: If the contract is not found
            InvalidStandardError: If the contract is invalid
        """

        with self._lock:
            # Construct the file path
            contract_file = self._contracts_path / f"{contract_name}.yaml"

            # Check if the file exists
            if not contract_file.exists():
                raise StandardNotFoundError(contract_name)

            try:
                # Load and parse the YAML file
                with open(contract_file, encoding="utf-8") as f:
                    contract_content = yaml.safe_load(f)

                # Validate the contract structure
                self._validate_contract_structure(contract_content, contract_name)

                # Ensure we return the correct type
                if isinstance(contract_content, dict):
                    return contract_content
                else:
                    raise InvalidStandardError(
                        "Contract content must be a dictionary", contract_name
                    )

            except yaml.YAMLError as e:
                raise InvalidStandardError(f"YAML parsing error: {e}", contract_name)
            except Exception as e:
                raise InvalidStandardError(
                    f"Error loading contract: {e}", contract_name
                )

    def _validate_contract_structure(
        self, contract: dict[str, Any], contract_name: str
    ):
        """
        Validate that a contract has the required structure using ContractValidator.

        Args:
            contract: The contract dictionary to validate
            contract_name: Name of the contract for error messages

        Raises:
            InvalidStandardError: If the contract structure is invalid
        """
        try:
            from adri.contracts.exceptions import SchemaValidationError
            from adri.contracts.validator import get_validator

            validator = get_validator()
            result = validator.validate_contract(contract, use_cache=False)

            if not result.is_valid:
                # Collect all error messages
                error_messages = [err.message for err in result.errors]
                raise InvalidStandardError(
                    f"Contract validation failed: {'; '.join(error_messages)}",
                    contract_name,
                )
        except SchemaValidationError as e:
            raise InvalidStandardError(str(e), contract_name)
        except ImportError:
            # Fallback to basic validation if new validator not available
            if not isinstance(contract, dict):
                raise InvalidStandardError(
                    "Contract must be a dictionary", contract_name
                )

            # Check for required top-level sections
            required_sections = ["standards", "requirements"]
            for section in required_sections:
                if section not in contract:
                    raise InvalidStandardError(
                        f"Missing required section: {section}", contract_name
                    )

    def list_available_contracts(self) -> list[str]:
        """
        List all available contracts.

        Returns:
            list: List of contract names (without .yaml extension)
        """

        with self._lock:
            contracts = []

            # Find all .yaml files in the contracts directory
            for yaml_file in self._contracts_path.glob("*.yaml"):
                # Remove the .yaml extension to get the contract name
                contract_name = yaml_file.stem
                contracts.append(contract_name)

            return sorted(contracts)

    def contract_exists(self, contract_name: str) -> bool:
        """
        Check if a contract exists in the contracts directory.

        Args:
            contract_name: Name of the contract to check

        Returns:
            bool: True if the contract exists, False otherwise
        """

        contract_file = self._contracts_path / f"{contract_name}.yaml"
        return contract_file.exists()

    def get_contract_metadata(self, contract_name: str) -> dict[str, Any]:
        """
        Get metadata for a contract without loading the full content.

        Args:
            contract_name: Name of the contract

        Returns:
            dict: Contract metadata including name, version, description, file_path

        Raises:
            StandardNotFoundError: If the contract is not found
        """

        if not self.contract_exists(contract_name):
            raise StandardNotFoundError(contract_name)

        # Parse the contract to get metadata
        contract = self.parse_contract(contract_name)
        standards_section = contract["contracts"]

        metadata = {
            "name": standards_section.get("name", contract_name),
            "version": standards_section.get("version", "unknown"),
            "description": standards_section.get(
                "description", "No description available"
            ),
            "file_path": str(self._contracts_path / f"{contract_name}.yaml"),
            "id": standards_section.get("id", contract_name),
        }

        return metadata

    def clear_cache(self):
        """Clear the internal cache of parsed contracts."""

        self.parse_contract.cache_clear()

    def get_cache_info(self):
        """Get information about the internal cache."""

        return self.parse_contract.cache_info()

    def validate_contract_file(self, contract_path: str) -> dict[str, Any]:
        """
        Validate a YAML contract file and return detailed results.

        Args:
            contract_path: Path to YAML contract file

        Returns:
            Dict containing validation results
        """

        validation_result = {
            "file_path": contract_path,
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "passed_checks": [],
        }

        try:
            # Check if file exists
            if not os.path.exists(contract_path):
                validation_result["errors"].append(f"File not found: {contract_path}")
                validation_result["is_valid"] = False
                return validation_result

            # Load YAML content
            try:
                with open(contract_path, encoding="utf-8") as f:
                    yaml_content = yaml.safe_load(f)
                validation_result["passed_checks"].append("Valid YAML syntax")
            except yaml.YAMLError as e:
                validation_result["errors"].append(f"Invalid YAML syntax: {e}")
                validation_result["is_valid"] = False
                return validation_result

            # Validate using existing structure validation
            try:
                self._validate_contract_structure(
                    yaml_content, os.path.basename(contract_path)
                )
                validation_result["passed_checks"].append(
                    "Valid ADRI contract structure"
                )
            except InvalidStandardError as e:
                validation_result["errors"].append(str(e))
                validation_result["is_valid"] = False

        except Exception as e:
            validation_result["errors"].append(
                f"Unexpected error during validation: {e}"
            )
            validation_result["is_valid"] = False

        return validation_result


# Convenience functions for backward compatibility
def load_bundled_contract(contract_name: str) -> dict[str, Any]:
    """
    Load a contract using the default parser.

    Args:
        contract_name: Name of the contract to load

    Returns:
        dict: The loaded contract
    """

    parser = ContractsParser()
    return parser.parse_contract(contract_name)


def list_bundled_contracts() -> list[str]:
    """
    List all available contracts.

    Returns:
        list: List of contract names
    """

    parser = ContractsParser()
    return parser.list_available_contracts()


# Backward compatibility aliases
ContractsLoader = ContractsParser
StandardsParser = ContractsParser  # For migration compatibility
# @ADRI_FEATURE_END[contracts_parser]
