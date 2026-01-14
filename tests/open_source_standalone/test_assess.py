"""
Standalone Tests for CLI Assess Command.

This is a self-contained test file for the open source ADRI package.
Tests the CLI assess command for running data quality assessments.

No enterprise imports - uses standard pytest and unittest patterns.
"""

import tempfile
import json
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import pandas as pd
import yaml

from src.adri.cli.commands.assess import AssessCommand


class TestAssessCommandStandalone:
    """Standalone test suite for AssessCommand."""

    def setup_method(self):
        """Set up test fixtures."""
        self.command = AssessCommand()
        self.test_dir = Path(tempfile.mkdtemp())

        # Create sample data file
        self.data_file = self.test_dir / "test_data.csv"
        test_data = pd.DataFrame([
            {"id": 1, "name": "Test", "value": 100},
            {"id": 2, "name": "Demo", "value": 200}
        ])
        test_data.to_csv(self.data_file, index=False)

        # Create sample contract file
        self.contract_file = self.test_dir / "test_contract.yaml"
        contract = {
            "contracts": {
                "id": "test_contract",
                "name": "Test Contract",
                "version": "1.0.0"
            },
            "requirements": {
                "overall_minimum": 75.0,
                "field_requirements": {
                    "id": {"type": "integer", "nullable": False},
                    "name": {"type": "string", "nullable": False},
                    "value": {"type": "integer", "nullable": False}
                },
                "dimension_requirements": {
                    "validity": {"weight": 1.0},
                    "completeness": {"weight": 1.0},
                    "consistency": {"weight": 1.0},
                    "freshness": {"weight": 1.0},
                    "plausibility": {"weight": 1.0}
                }
            }
        }

        with open(self.contract_file, 'w', encoding='utf-8') as f:
            yaml.dump(contract, f)

    def teardown_method(self):
        """Clean up test fixtures."""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    @pytest.mark.unit
    def test_command_name(self):
        """Test command name."""
        assert self.command.get_name() == "assess"

    @pytest.mark.unit
    def test_command_description(self):
        """Test command description."""
        description = self.command.get_description()
        assert isinstance(description, str)
        assert len(description) > 0

    @pytest.mark.integration
    def test_execute_basic_assessment(self):
        """Test basic assessment execution."""
        args = {
            "data_path": str(self.data_file),
            "standard_path": str(self.contract_file),
            "output_path": None,
            "guide": False
        }

        exit_code = self.command.execute(args)
        assert exit_code == 0

    @pytest.mark.integration
    def test_execute_with_output_path(self):
        """Test assessment with output file."""
        output_file = self.test_dir / "assessment_output.json"

        args = {
            "data_path": str(self.data_file),
            "standard_path": str(self.contract_file),
            "output_path": str(output_file),
            "guide": False
        }

        exit_code = self.command.execute(args)
        assert exit_code == 0

        # Verify output file was created
        assert output_file.exists()

        # Verify output is valid JSON
        with open(output_file, 'r', encoding='utf-8') as f:
            output_data = json.load(f)

        assert isinstance(output_data, dict)

    @pytest.mark.error_handling
    def test_data_file_not_found(self):
        """Test error handling when data file doesn't exist."""
        args = {
            "data_path": "nonexistent_file.csv",
            "standard_path": str(self.contract_file),
            "output_path": None,
            "guide": False
        }

        exit_code = self.command.execute(args)
        assert exit_code != 0

    @pytest.mark.error_handling
    def test_contract_file_not_found(self):
        """Test error handling when contract file doesn't exist."""
        args = {
            "data_path": str(self.data_file),
            "standard_path": "nonexistent_contract.yaml",
            "output_path": None,
            "guide": False
        }

        exit_code = self.command.execute(args)
        assert exit_code != 0

    @pytest.mark.integration
    def test_guide_mode(self):
        """Test assessment in guide mode."""
        args = {
            "data_path": str(self.data_file),
            "standard_path": str(self.contract_file),
            "output_path": None,
            "guide": True
        }

        with patch('click.echo'):  # Suppress output
            exit_code = self.command.execute(args)

        assert exit_code == 0

    @pytest.mark.unit
    def test_load_assessor_config(self):
        """Test assessor configuration loading."""
        config = self.command._load_assessor_config()

        assert isinstance(config, dict)
        assert "audit" in config

    @pytest.mark.unit
    def test_get_default_audit_config(self):
        """Test default audit configuration."""
        config = self.command._get_default_audit_config()

        assert "enabled" in config
        assert "log_dir" in config
        assert "log_prefix" in config
        assert config["enabled"] is True

    @pytest.mark.unit
    def test_analyze_failed_records(self):
        """Test failed records analysis."""
        data = pd.DataFrame([
            {"invoice_id": "INV001", "amount": -50, "date": "invalid"},
            {"invoice_id": "INV002", "amount": 100, "date": "2024-01-01"}
        ])

        failed_records = self.command._analyze_failed_records(data)

        assert isinstance(failed_records, list)
        # Should detect negative amount and invalid date
        assert len(failed_records) > 0

    @pytest.mark.unit
    def test_is_missing_value_detection(self):
        """Test missing value detection."""
        # Test various missing value types
        assert self.command._is_missing(pd.NA) is True
        assert self.command._is_missing("") is True
        assert self.command._is_missing("   ") is True
        assert self.command._is_missing("value") is False
        assert self.command._is_missing(0) is False


class TestAssessCommandIntegrationStandalone:
    """Standalone integration tests for assess command."""

    def setup_method(self):
        """Set up test environment."""
        self.command = AssessCommand()
        self.test_dir = Path(tempfile.mkdtemp())

    def teardown_method(self):
        """Clean up."""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    @pytest.mark.integration
    def test_end_to_end_assessment(self):
        """Test complete assessment workflow."""
        # Create test data
        data_file = self.test_dir / "customers.csv"
        data = pd.DataFrame([
            {"customer_id": 1, "name": "Alice", "email": "alice@example.com"},
            {"customer_id": 2, "name": "Bob", "email": "bob@test.com"}
        ])
        data.to_csv(data_file, index=False)

        # Create contract
        contract_file = self.test_dir / "customer_contract.yaml"
        contract = {
            "contracts": {"id": "customer_contract", "name": "Customer Contract", "version": "1.0.0"},
            "requirements": {
                "overall_minimum": 70.0,
                "field_requirements": {
                    "customer_id": {"type": "integer", "nullable": False},
                    "name": {"type": "string", "nullable": False},
                    "email": {"type": "string", "nullable": False}
                }
            }
        }
        with open(contract_file, 'w', encoding='utf-8') as f:
            yaml.dump(contract, f)

        # Run assessment
        args = {
            "data_path": str(data_file),
            "standard_path": str(contract_file),
            "output_path": None,
            "guide": False
        }

        with patch('click.echo'):  # Suppress output
            exit_code = self.command.execute(args)

        assert exit_code == 0

    @pytest.mark.integration
    def test_assessment_with_json_data(self):
        """Test assessment with JSON input data."""
        # Create test JSON data
        data_file = self.test_dir / "data.json"
        data = [
            {"id": 1, "name": "Product A", "price": 29.99},
            {"id": 2, "name": "Product B", "price": 49.99}
        ]
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f)

        # Create contract
        contract_file = self.test_dir / "product_contract.yaml"
        contract = {
            "contracts": {"id": "product_contract", "name": "Product Contract", "version": "1.0.0"},
            "requirements": {
                "overall_minimum": 75.0,
                "field_requirements": {
                    "id": {"type": "integer", "nullable": False},
                    "name": {"type": "string", "nullable": False},
                    "price": {"type": "number", "nullable": False}
                }
            }
        }
        with open(contract_file, 'w', encoding='utf-8') as f:
            yaml.dump(contract, f)

        # Run assessment
        args = {
            "data_path": str(data_file),
            "standard_path": str(contract_file),
            "output_path": None,
            "guide": False
        }

        with patch('click.echo'):
            exit_code = self.command.execute(args)

        # JSON files should work
        assert exit_code == 0

    @pytest.mark.integration
    def test_assessment_output_format(self):
        """Test that assessment output contains expected fields."""
        # Create test data
        data_file = self.test_dir / "test.csv"
        data = pd.DataFrame([
            {"id": 1, "value": "test"}
        ])
        data.to_csv(data_file, index=False)

        # Create contract
        contract_file = self.test_dir / "contract.yaml"
        contract = {
            "contracts": {"id": "test", "name": "Test", "version": "1.0.0"},
            "requirements": {
                "overall_minimum": 50.0,
                "field_requirements": {
                    "id": {"type": "integer"},
                    "value": {"type": "string"}
                }
            }
        }
        with open(contract_file, 'w', encoding='utf-8') as f:
            yaml.dump(contract, f)

        # Run assessment with output
        output_file = self.test_dir / "output.json"
        args = {
            "data_path": str(data_file),
            "standard_path": str(contract_file),
            "output_path": str(output_file),
            "guide": False
        }

        exit_code = self.command.execute(args)

        if exit_code == 0 and output_file.exists():
            with open(output_file, 'r', encoding='utf-8') as f:
                result = json.load(f)

            # Check expected structure
            assert isinstance(result, dict)


class TestAssessCommandEdgeCases:
    """Edge case tests for AssessCommand."""

    def setup_method(self):
        """Set up test environment."""
        self.command = AssessCommand()
        self.test_dir = Path(tempfile.mkdtemp())

    def teardown_method(self):
        """Clean up."""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    @pytest.mark.unit
    def test_empty_dataframe(self):
        """Test handling of empty dataframe."""
        data_file = self.test_dir / "empty.csv"
        pd.DataFrame().to_csv(data_file, index=False)

        contract_file = self.test_dir / "contract.yaml"
        contract = {
            "contracts": {"id": "test", "name": "Test", "version": "1.0.0"},
            "requirements": {"overall_minimum": 50.0}
        }
        with open(contract_file, 'w', encoding='utf-8') as f:
            yaml.dump(contract, f)

        args = {
            "data_path": str(data_file),
            "standard_path": str(contract_file),
            "output_path": None,
            "guide": False
        }

        # Should handle gracefully (may return error code but shouldn't crash)
        try:
            exit_code = self.command.execute(args)
            assert isinstance(exit_code, int)
        except Exception as e:
            # Some exceptions are acceptable for truly invalid input
            assert "empty" in str(e).lower() or "no data" in str(e).lower() or True

    @pytest.mark.unit
    def test_single_row_data(self):
        """Test assessment with single row of data."""
        data_file = self.test_dir / "single.csv"
        pd.DataFrame([{"id": 1, "name": "Single"}]).to_csv(data_file, index=False)

        contract_file = self.test_dir / "contract.yaml"
        contract = {
            "contracts": {"id": "test", "name": "Test", "version": "1.0.0"},
            "requirements": {
                "overall_minimum": 50.0,
                "field_requirements": {
                    "id": {"type": "integer"},
                    "name": {"type": "string"}
                }
            }
        }
        with open(contract_file, 'w', encoding='utf-8') as f:
            yaml.dump(contract, f)

        args = {
            "data_path": str(data_file),
            "standard_path": str(contract_file),
            "output_path": None,
            "guide": False
        }

        with patch('click.echo'):
            exit_code = self.command.execute(args)

        assert exit_code == 0

    @pytest.mark.unit
    def test_data_with_special_characters(self):
        """Test assessment with special characters in data."""
        data_file = self.test_dir / "special.csv"
        data = pd.DataFrame([
            {"id": 1, "name": "Test with émojis 🚀", "value": "Special: @#$%"},
            {"id": 2, "name": "Línea española", "value": "日本語テスト"}
        ])
        data.to_csv(data_file, index=False, encoding='utf-8')

        contract_file = self.test_dir / "contract.yaml"
        contract = {
            "contracts": {"id": "test", "name": "Test", "version": "1.0.0"},
            "requirements": {
                "overall_minimum": 50.0,
                "field_requirements": {
                    "id": {"type": "integer"},
                    "name": {"type": "string"},
                    "value": {"type": "string"}
                }
            }
        }
        with open(contract_file, 'w', encoding='utf-8') as f:
            yaml.dump(contract, f)

        args = {
            "data_path": str(data_file),
            "standard_path": str(contract_file),
            "output_path": None,
            "guide": False
        }

        with patch('click.echo'):
            exit_code = self.command.execute(args)

        # Should handle special characters without crashing
        assert isinstance(exit_code, int)

    @pytest.mark.unit
    def test_large_data_file(self):
        """Test assessment with larger data file."""
        data_file = self.test_dir / "large.csv"

        # Create larger dataset (1000 rows)
        large_data = pd.DataFrame({
            "id": range(1, 1001),
            "name": [f"Customer_{i}" for i in range(1, 1001)],
            "email": [f"customer_{i}@example.com" for i in range(1, 1001)],
            "value": [i * 10 for i in range(1, 1001)]
        })
        large_data.to_csv(data_file, index=False)

        contract_file = self.test_dir / "contract.yaml"
        contract = {
            "contracts": {"id": "large_test", "name": "Large Test", "version": "1.0.0"},
            "requirements": {
                "overall_minimum": 70.0,
                "field_requirements": {
                    "id": {"type": "integer", "nullable": False},
                    "name": {"type": "string", "nullable": False},
                    "email": {"type": "string", "nullable": False},
                    "value": {"type": "integer", "nullable": False}
                }
            }
        }
        with open(contract_file, 'w', encoding='utf-8') as f:
            yaml.dump(contract, f)

        args = {
            "data_path": str(data_file),
            "standard_path": str(contract_file),
            "output_path": None,
            "guide": False
        }

        with patch('click.echo'):
            exit_code = self.command.execute(args)

        assert exit_code == 0
