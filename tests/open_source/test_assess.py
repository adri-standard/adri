"""
Comprehensive tests for cli_assess_command feature.

Tests the CLI assess command for running data quality assessments.
"""

import unittest
import tempfile
import pandas as pd
import yaml
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.adri.cli.commands.assess import AssessCommand


class TestAssessCommand(unittest.TestCase):
    """Test assess command core functionality."""
    
    def setUp(self):
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
        
        with open(self.contract_file, 'w') as f:
            yaml.dump(contract, f)
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
    
    def test_command_name(self):
        """Test command name."""
        self.assertEqual(self.command.get_name(), "assess")
    
    def test_command_description(self):
        """Test command description."""
        description = self.command.get_description()
        self.assertIsInstance(description, str)
        self.assertGreater(len(description), 0)
    
    def test_execute_basic_assessment(self):
        """Test basic assessment execution."""
        args = {
            "data_path": str(self.data_file),
            "standard_path": str(self.contract_file),
            "output_path": None,
            "guide": False
        }
        
        exit_code = self.command.execute(args)
        self.assertEqual(exit_code, 0)
    
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
        self.assertEqual(exit_code, 0)
        
        # Verify output file was created
        self.assertTrue(output_file.exists())
        
        # Verify output is valid JSON
        import json
        with open(output_file, 'r') as f:
            output_data = json.load(f)
        
        self.assertIsInstance(output_data, dict)
    
    def test_data_file_not_found(self):
        """Test error handling when data file doesn't exist."""
        args = {
            "data_path": "nonexistent_file.csv",
            "standard_path": str(self.contract_file),
            "output_path": None,
            "guide": False
        }
        
        exit_code = self.command.execute(args)
        self.assertNotEqual(exit_code, 0)
    
    def test_contract_file_not_found(self):
        """Test error handling when contract file doesn't exist."""
        args = {
            "data_path": str(self.data_file),
            "standard_path": "nonexistent_contract.yaml",
            "output_path": None,
            "guide": False
        }
        
        exit_code = self.command.execute(args)
        self.assertNotEqual(exit_code, 0)
    
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
        
        self.assertEqual(exit_code, 0)
    
    def test_load_assessor_config(self):
        """Test assessor configuration loading."""
        config = self.command._load_assessor_config()
        
        self.assertIsInstance(config, dict)
        self.assertIn("audit", config)
    
    def test_get_default_audit_config(self):
        """Test default audit configuration."""
        config = self.command._get_default_audit_config()
        
        self.assertIn("enabled", config)
        self.assertIn("log_dir", config)
        self.assertIn("log_prefix", config)
        self.assertTrue(config["enabled"])
    
    def test_analyze_failed_records(self):
        """Test failed records analysis."""
        data = pd.DataFrame([
            {"invoice_id": "INV001", "amount": -50, "date": "invalid"},
            {"invoice_id": "INV002", "amount": 100, "date": "2024-01-01"}
        ])
        
        failed_records = self.command._analyze_failed_records(data)
        
        self.assertIsInstance(failed_records, list)
        # Should detect negative amount and invalid date
        self.assertGreater(len(failed_records), 0)
    
    def test_is_missing_value_detection(self):
        """Test missing value detection."""
        # Test various missing value types
        self.assertTrue(self.command._is_missing(pd.NA))
        self.assertTrue(self.command._is_missing(""))
        self.assertTrue(self.command._is_missing("   "))
        self.assertFalse(self.command._is_missing("value"))
        self.assertFalse(self.command._is_missing(0))


class TestAssessCommandIntegration(unittest.TestCase):
    """Integration tests for assess command."""
    
    def setUp(self):
        """Set up test environment."""
        self.command = AssessCommand()
        self.test_dir = Path(tempfile.mkdtemp())
    
    def tearDown(self):
        """Clean up."""
        import shutil
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
    
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
        with open(contract_file, 'w') as f:
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
        
        self.assertEqual(exit_code, 0)


if __name__ == '__main__':
    unittest.main()
