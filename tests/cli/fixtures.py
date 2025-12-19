"""Modern test fixtures and utilities for CLI testing.

This module provides reusable fixtures, base classes, and utilities that
support the modernized CLI test suite with proper path resolution and
command registry pattern testing.
"""

import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from unittest.mock import Mock, patch

import pytest
import yaml

from src.adri.cli.registry import get_command


class ModernCLITestBase:
    """Base class for CLI tests with modern fixtures and utilities.

    This class provides common functionality for CLI testing including
    safe workspace management, command registry access, and proper
    path handling that works from any directory.
    """

    def __init__(self):
        self.temp_workspace: Optional[Path] = None
        self.mock_registry: Optional[Mock] = None
        self.sample_data: Dict[str, Any] = {}
        self.sample_standard: Dict[str, Any] = {}

    def setup_method(self):
        """Set up method called before each test method."""
        self.temp_workspace = self.create_test_workspace()
        # Change to the test workspace to ensure consistent behavior
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_workspace)

    def teardown_method(self):
        """Tear down method called after each test method."""
        try:
            os.chdir(self.original_cwd)
        except (OSError, FileNotFoundError):
            # If original directory no longer exists, fallback to home
            os.chdir(Path.home())

        if self.temp_workspace and self.temp_workspace.exists():
            import shutil
            try:
                shutil.rmtree(self.temp_workspace)
            except (OSError, PermissionError):
                # If cleanup fails, it's not critical for tests
                pass

    def create_test_workspace(self) -> Path:
        """Create a safe test workspace with absolute path management.

        Returns:
            Path to the created workspace
        """
        return create_test_workspace()

    def setup_mock_commands(self) -> Dict[str, Mock]:
        """Set up mock commands for testing.

        Returns:
            Dictionary of mock commands by name
        """
        return setup_mock_commands()


def create_test_workspace() -> Path:
    """Create a test workspace with proper ADRI structure.

    This function creates a temporary directory with the complete
    ADRI project structure needed for CLI testing.

    Returns:
        Path to the workspace root directory
    """
    temp_dir = tempfile.mkdtemp()
    workspace_root = Path(temp_dir).resolve()

    # Create ADRI directory structure
    directories = [
        "ADRI/dev/contracts",
        "ADRI/dev/assessments",
        "ADRI/dev/training-data",
        "ADRI/dev/audit-logs",
        "ADRI/prod/contracts",
        "ADRI/prod/assessments",
        "ADRI/prod/training-data",
        "ADRI/prod/audit-logs",
        "ADRI/tutorials/invoice_processing",
        "ADRI/tutorials/customer_service",
    ]

    for directory in directories:
        (workspace_root / directory).mkdir(parents=True, exist_ok=True)

    # Create configuration file
    config = {
        "adri": {
            "project_name": "test_project",
            "version": "4.0.0",
            "default_environment": "development",
            "environments": {
                "development": {
                    "paths": {
                        "contracts": "ADRI/dev/contracts",
                        "assessments": "ADRI/dev/assessments",
                        "training_data": "ADRI/dev/training-data",
                        "audit_logs": "ADRI/dev/audit-logs",
                    },
                    "audit": {
                        "enabled": True,
                        "log_dir": "ADRI/dev/audit-logs",
                        "log_prefix": "adri",
                        "log_level": "INFO",
                        "include_data_samples": True,
                        "max_log_size_mb": 100,
                    },
                },
                "production": {
                    "paths": {
                        "contracts": "ADRI/prod/contracts",
                        "assessments": "ADRI/prod/assessments",
                        "training_data": "ADRI/prod/training-data",
                        "audit_logs": "ADRI/prod/audit-logs",
                    },
                    "audit": {
                        "enabled": True,
                        "log_dir": "ADRI/prod/audit-logs",
                        "log_prefix": "adri",
                        "log_level": "INFO",
                        "include_data_samples": True,
                        "max_log_size_mb": 100,
                    },
                },
            },
        }
    }

    config_path = workspace_root / "ADRI" / "config.yaml"
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, default_flow_style=False)

    # Create sample data files
    _create_sample_data_files(workspace_root)

    return workspace_root


def _create_sample_data_files(workspace_root: Path) -> None:
    """Create sample data files for testing.

    Args:
        workspace_root: Root directory of the workspace
    """
    # Create invoice processing tutorial data
    invoice_dir = workspace_root / "ADRI" / "tutorials" / "invoice_processing"

    training_data = """invoice_id,customer_id,amount,date,status,payment_method
INV-001,CUST-101,1250.00,2024-01-15,paid,credit_card
INV-002,CUST-102,875.50,2024-01-16,paid,bank_transfer
INV-003,CUST-103,2100.75,2024-01-17,paid,credit_card
INV-004,CUST-104,450.00,2024-01-18,pending,cash
INV-005,CUST-105,1800.25,2024-01-19,paid,bank_transfer"""

    with open(invoice_dir / "invoice_data.csv", 'w', encoding='utf-8') as f:
        f.write(training_data)

    # Create test data with quality issues
    test_data = """invoice_id,customer_id,amount,date,status,payment_method
INV-101,CUST-201,1350.00,2024-02-15,paid,credit_card
INV-102,,925.50,2024-02-16,paid,bank_transfer
INV-103,CUST-203,-150.75,2024-02-17,invalid,credit_card
INV-104,CUST-204,0,invalid_date,pending,cash
,CUST-205,1950.25,,paid,unknown_method"""

    with open(invoice_dir / "test_invoice_data.csv", 'w', encoding='utf-8') as f:
        f.write(test_data)

    # Create customer service tutorial data
    customer_dir = workspace_root / "ADRI" / "tutorials" / "customer_service"
    customer_data = """customer_id,name,email,phone,registration_date
CUST-001,John Doe,john@example.com,555-0123,2024-01-01
CUST-002,Jane Smith,jane@example.com,555-0124,2024-01-02
CUST-003,Bob Johnson,bob@example.com,555-0125,2024-01-03"""

    with open(customer_dir / "customer_data.csv", 'w', encoding='utf-8') as f:
        f.write(customer_data)


def create_safe_temp_dir() -> Path:
    """Create a safe temporary directory with absolute path management.

    This function creates a temporary directory that avoids path resolution
    issues in CI environments by using absolute paths.

    Returns:
        Absolute path to the temporary directory
    """
    temp_dir = tempfile.mkdtemp()
    return Path(temp_dir).resolve()


def setup_mock_commands() -> Dict[str, Mock]:
    """Set up mock commands for registry testing.

    Returns:
        Dictionary of mock command objects by command name
    """
    mock_commands = {}

    command_names = [
        "setup", "assess", "generate-contract", "list-assessments",
        "list-contracts", "view-logs", "show-config", "validate-contract",
        "show-contract", "scoring-explain", "scoring-preset-apply"
    ]

    for name in command_names:
        mock_cmd = Mock()
        mock_cmd.execute.return_value = 0  # Success by default
        mock_cmd.get_name.return_value = name
        mock_cmd.get_description.return_value = f"Mock {name} command"
        mock_commands[name] = mock_cmd

    return mock_commands


def mock_command_registry() -> Mock:
    """Create a mock command registry for testing.

    Returns:
        Mock registry object with command access methods
    """
    registry = Mock()
    mock_commands = setup_mock_commands()

    def get_command_side_effect(name: str):
        if name in mock_commands:
            return mock_commands[name]
        raise KeyError(f"Command '{name}' not found")

    registry.get_command.side_effect = get_command_side_effect
    registry.list_commands.return_value = list(mock_commands.keys())

    return registry


class MockCommandResult:
    """Mock command execution result.

    This class represents the result of executing a CLI command,
    including exit code, output, and error information.
    """

    def __init__(self, exit_code: int = 0, output: str = "", stderr: str = ""):
        self.exit_code = exit_code
        self.output = output
        self.stderr = stderr

    def __str__(self):
        return f"MockCommandResult(exit_code={self.exit_code}, output_length={len(self.output)})"

    def __repr__(self):
        return self.__str__()


def create_sample_standard(
    name: str = "test_standard",
    version: str = "1.0.0"
) -> Dict[str, Any]:
    """Create a sample ADRI standard for testing.

    Args:
        name: Name of the standard
        version: Version of the standard

    Returns:
        Dictionary containing standard structure
    """
    return {
        "contracts": {
            "id": f"{name}_id",
            "name": name.replace("_", " ").title(),
            "version": version,
            "description": f"Test standard for {name}"
        },
        "requirements": {
            "overall_minimum": 75.0,
            "dimension_weights": {
                "completeness": 0.3,
                "validity": 0.3,
                "consistency": 0.2,
                "plausibility": 0.2
            }
        },
        "record_identification": {
            "primary_key_fields": ["id"],
            "strategy": "primary_key_with_fallback"
        },
        "metadata": {
            "created_by": "ADRI Framework",
            "generation_method": "auto_generated",
            "created_date": "2024-01-01T00:00:00Z",
            "tags": ["test", "cli_testing", name]
        },
        "training_data_lineage": {
            "source_path": f"test_data/{name}.csv",
            "timestamp": "2024-01-01T00:00:00Z",
            "file_hash": "abc12345",
            "snapshot_path": f"ADRI/dev/training-data/{name}_abc12345.csv",
            "snapshot_hash": "abc12345"
        }
    }


def create_sample_data(data_type: str = "invoice") -> List[Dict[str, Any]]:
    """Create sample data for testing.

    Args:
        data_type: Type of data to create ("invoice", "customer", "generic")

    Returns:
        List of sample data records
    """
    if data_type == "invoice":
        return [
            {"invoice_id": "INV-001", "customer_id": "CUST-101", "amount": 1250.00, "status": "paid"},
            {"invoice_id": "INV-002", "customer_id": "CUST-102", "amount": 875.50, "status": "pending"},
            {"invoice_id": "INV-003", "customer_id": "CUST-103", "amount": 2100.75, "status": "paid"},
            {"invoice_id": "INV-004", "customer_id": "CUST-104", "amount": 450.00, "status": "pending"},
        ]
    elif data_type == "customer":
        return [
            {"customer_id": "CUST-001", "name": "John Doe", "email": "john@example.com", "status": "active"},
            {"customer_id": "CUST-002", "name": "Jane Smith", "email": "jane@example.com", "status": "active"},
            {"customer_id": "CUST-003", "name": "Bob Johnson", "email": "bob@example.com", "status": "inactive"},
        ]
    else:  # generic
        return [
            {"id": "001", "name": "Test Item 1", "value": 100.0, "category": "A"},
            {"id": "002", "name": "Test Item 2", "value": 200.0, "category": "B"},
            {"id": "003", "name": "Test Item 3", "value": 150.0, "category": "A"},
        ]


def assert_workspace_structure(workspace_path: Path) -> None:
    """Assert that a workspace has the correct ADRI structure.

    Args:
        workspace_path: Path to the workspace to validate

    Raises:
        AssertionError: If workspace structure is invalid
    """
    required_dirs = [
        "ADRI",
        "ADRI/dev",
        "ADRI/dev/contracts",
        "ADRI/dev/assessments",
        "ADRI/dev/training-data",
        "ADRI/dev/audit-logs",
        "ADRI/prod",
        "ADRI/prod/contracts",
        "ADRI/prod/assessments",
        "ADRI/prod/training-data",
        "ADRI/prod/audit-logs",
        "ADRI/tutorials",
    ]

    for directory in required_dirs:
        dir_path = workspace_path / directory
        assert dir_path.exists(), f"Required directory {directory} does not exist"
        assert dir_path.is_dir(), f"Required path {directory} is not a directory"

    # Check config file exists
    config_path = workspace_path / "ADRI" / "config.yaml"
    assert config_path.exists(), "ADRI/config.yaml does not exist"
    assert config_path.is_file(), "ADRI/config.yaml is not a file"


def cleanup_temp_workspace(workspace_path: Path) -> None:
    """Clean up a temporary workspace safely.

    Args:
        workspace_path: Path to the workspace to clean up
    """
    if workspace_path and workspace_path.exists():
        import shutil
        try:
            shutil.rmtree(workspace_path)
        except (OSError, PermissionError):
            # If cleanup fails, it's not critical for tests
            pass


def with_temp_workspace(func):
    """Decorator to provide a temporary workspace for a test function.

    This decorator creates a temporary workspace, changes to it for the
    duration of the test, and cleans up afterwards.
    """
    def wrapper(*args, **kwargs):
        workspace = create_test_workspace()
        original_cwd = os.getcwd()

        try:
            os.chdir(workspace)
            return func(workspace, *args, **kwargs)
        finally:
            try:
                os.chdir(original_cwd)
            except (OSError, FileNotFoundError):
                # If original directory no longer exists, fallback to home
                os.chdir(Path.home())
            cleanup_temp_workspace(workspace)

    return wrapper
