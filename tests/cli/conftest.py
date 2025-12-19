"""Pytest configuration for CLI tests.

This module provides fixtures and configuration specific to CLI testing,
including safe temporary directory management and command registry mocking.
"""

import tempfile
from pathlib import Path
from typing import Dict, Any
from unittest.mock import Mock, patch

import pytest
import yaml

from src.adri.cli.registry import get_command
from src.adri.core.registry import get_global_registry


@pytest.fixture
def safe_temp_dir():
    """Create a safe temporary directory with absolute path management.

    This fixture provides proper cleanup and avoids path resolution issues
    that occur with os.getcwd() in CI environments.
    """
    temp_dir = tempfile.mkdtemp()
    temp_path = Path(temp_dir).resolve()  # Ensure absolute path
    yield temp_path

    # Clean up
    import shutil
    try:
        shutil.rmtree(temp_path)
    except (OSError, PermissionError):
        # If cleanup fails, it's not critical for tests
        pass


@pytest.fixture
def test_workspace(safe_temp_dir):
    """Create a test ADRI workspace with proper directory structure.

    This fixture provides a complete ADRI project structure for testing
    CLI commands in isolation.
    """
    workspace = TestWorkspace(safe_temp_dir)
    workspace.setup()
    return workspace


@pytest.fixture
def mock_registry():
    """Create a mock command registry for testing.

    This fixture provides controlled command execution for unit testing
    without executing actual CLI commands.
    """
    registry = Mock()

    # Create mock commands
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

    registry.get_command.side_effect = lambda name: mock_commands.get(name)
    registry.list_commands.return_value = list(mock_commands.keys())

    return registry, mock_commands


@pytest.fixture
def sample_data():
    """Provide sample data for testing CLI commands."""
    return [
        {"invoice_id": "INV-001", "customer_id": "CUST-101", "amount": 1250.00, "status": "paid"},
        {"invoice_id": "INV-002", "customer_id": "CUST-102", "amount": 875.50, "status": "pending"},
        {"invoice_id": "INV-003", "customer_id": "CUST-103", "amount": 2100.75, "status": "paid"},
    ]


@pytest.fixture
def sample_standard():
    """Provide a sample ADRI standard for testing."""
    return {
        "contracts": {
            "id": "test_data_standard",
            "name": "Test Data Standard",
            "version": "1.0.0",
            "description": "Test standard for CLI testing"
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
            "primary_key_fields": ["invoice_id"],
            "strategy": "primary_key_with_fallback"
        },
        "metadata": {
            "created_by": "ADRI Framework",
            "generation_method": "auto_generated",
            "created_date": "2024-01-01T00:00:00Z",
            "tags": ["test", "cli_testing"]
        }
    }


class TestWorkspace:
    """Test workspace helper for CLI testing.

    This class provides utilities to create and manage test ADRI workspaces
    with proper directory structure and sample files.
    """

    def __init__(self, root_path: Path):
        self.root = root_path
        self.adri_config = root_path / "ADRI" / "config.yaml"
        self.standards_dir = root_path / "ADRI" / "dev" / "standards"
        self.assessments_dir = root_path / "ADRI" / "dev" / "assessments"
        self.training_data_dir = root_path / "ADRI" / "dev" / "training-data"
        self.audit_logs_dir = root_path / "ADRI" / "dev" / "audit-logs"
        self.tutorials_dir = root_path / "ADRI" / "tutorials" / "invoice_processing"

    def setup(self):
        """Set up the complete workspace structure."""
        self._create_directories()
        self._create_config()
        self._create_sample_files()

    def _create_directories(self):
        """Create the ADRI directory structure."""
        directories = [
            self.standards_dir,
            self.assessments_dir,
            self.training_data_dir,
            self.audit_logs_dir,
            self.tutorials_dir,
            self.root / "ADRI" / "prod" / "standards",
            self.root / "ADRI" / "prod" / "assessments",
            self.root / "ADRI" / "prod" / "training-data",
            self.root / "ADRI" / "prod" / "audit-logs",
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    def _create_config(self):
        """Create the ADRI configuration file."""
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

        with open(self.adri_config, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False)

    def _create_sample_files(self):
        """Create sample data files for testing."""
        # Create training data
        training_data = """invoice_id,customer_id,amount,date,status,payment_method
INV-001,CUST-101,1250.00,2024-01-15,paid,credit_card
INV-002,CUST-102,875.50,2024-01-16,paid,bank_transfer
INV-003,CUST-103,2100.75,2024-01-17,paid,credit_card"""

        training_file = self.tutorials_dir / "invoice_data.csv"
        with open(training_file, 'w', encoding='utf-8') as f:
            f.write(training_data)

        # Create test data with quality issues
        test_data = """invoice_id,customer_id,amount,date,status,payment_method
INV-101,CUST-201,1350.00,2024-02-15,paid,credit_card
INV-102,,925.50,2024-02-16,paid,bank_transfer
INV-103,CUST-203,-150.75,2024-02-17,invalid,credit_card"""

        test_file = self.tutorials_dir / "test_invoice_data.csv"
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(test_data)

    def create_standard(self, name: str, content: Dict[str, Any]) -> str:
        """Create a standard file and return name for name-only resolution.

        This method supports the governance model that enforces name-only standard
        resolution. The standard file is created in the configured location, but only
        the standard name is returned.

        Args:
            name: Standard name (without .yaml extension)
            content: Standard content dictionary

        Returns:
            Standard name only (not the path)
        """
        standard_path = self.standards_dir / f"{name}.yaml"
        with open(standard_path, 'w', encoding='utf-8') as f:
            yaml.dump(content, f, default_flow_style=False)
        return name  # Return name only, not path

    def create_data_file(self, name: str, content: str, directory: Path = None):
        """Create a data file in the workspace."""
        if directory is None:
            directory = self.tutorials_dir

        data_path = directory / name
        data_path.parent.mkdir(parents=True, exist_ok=True)
        with open(data_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return data_path
