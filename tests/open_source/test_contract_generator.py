"""
Comprehensive tests for analysis_contract_generator feature.

Tests the ContractGenerator class that auto-generates ADRI contracts from data profiling.
"""

import unittest
import pandas as pd
import tempfile
import yaml
from pathlib import Path

from src.adri.analysis.contract_generator import ContractGenerator, generate_contract_from_data


class TestContractGenerator(unittest.TestCase):
    """Test contract generator core functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.generator = ContractGenerator()
        
        # Sample data for contract generation
        self.sample_data = pd.DataFrame([
            {"id": 1, "name": "Alice", "email": "alice@example.com", "age": 25, "score": 85.5},
            {"id": 2, "name": "Bob", "email": "bob@test.com", "age": 30, "score": 92.3},
            {"id": 3, "name": "Charlie", "email": "charlie@demo.org", "age": 28, "score": 78.9}
        ])
    
    def test_generate_basic_contract(self):
        """Test basic contract generation from DataFrame."""
        contract = self.generator.generate(self.sample_data, "test_data")
        
        # Verify top-level structure
        self.assertIn("requirements", contract)
        self.assertIn("field_requirements", contract["requirements"])
        
        # Verify fields were detected
        field_reqs = contract["requirements"]["field_requirements"]
        self.assertIn("id", field_reqs)
        self.assertIn("name", field_reqs)
        self.assertIn("email", field_reqs)
        self.assertIn("age", field_reqs)
        self.assertIn("score", field_reqs)
    
    def test_field_type_inference(self):
        """Test that field types are correctly inferred."""
        contract = self.generator.generate(self.sample_data, "test_data")
        field_reqs = contract["requirements"]["field_requirements"]
        
        # Check inferred types
        self.assertEqual(field_reqs["id"]["type"], "integer")
        self.assertEqual(field_reqs["name"]["type"], "string")
        self.assertEqual(field_reqs["age"]["type"], "integer")
        self.assertEqual(field_reqs["score"]["type"], "float")
    
    def test_nullable_inference(self):
        """Test that nullable fields are correctly identified."""
        # Data with null values
        data_with_nulls = pd.DataFrame([
            {"id": 1, "name": "Alice", "optional": "value"},
            {"id": 2, "name": "Bob", "optional": None},
            {"id": 3, "name": "Charlie", "optional": "another"}
        ])
        
        contract = self.generator.generate(data_with_nulls, "test_data")
        field_reqs = contract["requirements"]["field_requirements"]
        
        # id and name have no nulls - should be required
        self.assertFalse(field_reqs["id"]["nullable"])
        self.assertFalse(field_reqs["name"]["nullable"])
        
        # optional has nulls - should be nullable
        self.assertTrue(field_reqs["optional"]["nullable"])
    
    def test_training_pass_guarantee(self):
        """Test that generated contract passes on training data."""
        contract = self.generator.generate(self.sample_data, "test_data")
        
        # Save to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(contract, f)
            contract_path = f.name
        
        try:
            # Validate that training data passes the generated contract
            from src.adri.validator.engine import DataQualityAssessor
            
            assessor = DataQualityAssessor({})
            result = assessor.assess(self.sample_data, contract_path)
            
            # Training data should achieve high score
            self.assertGreater(result.overall_score, 90.0)
            self.assertTrue(result.passed)
        finally:
            Path(contract_path).unlink()
    
    def test_numeric_range_inference(self):
        """Test numeric range detection."""
        numeric_data = pd.DataFrame({
            "temperature": [20.5, 22.0, 21.8, 23.2, 19.5],
            "count": [10, 15, 12, 18, 14]
        })
        
        contract = self.generator.generate(numeric_data, "numeric_test")
        field_reqs = contract["requirements"]["field_requirements"]
        
        # Check numeric bounds were inferred
        self.assertIn("min_value", field_reqs["temperature"])
        self.assertIn("max_value", field_reqs["temperature"])
        self.assertIn("min_value", field_reqs["count"])
        self.assertIn("max_value", field_reqs["count"])
    
    def test_string_length_inference(self):
        """Test string length bounds detection."""
        string_data = pd.DataFrame({
            "code": ["ABC", "DEF", "GHI", "JKL"],
            "description": ["Short", "A longer description", "Medium text", "Brief"]
        })
        
        contract = self.generator.generate(string_data, "string_test")
        field_reqs = contract["requirements"]["field_requirements"]
        
        # Fixed-length field should have tight bounds
        self.assertEqual(field_reqs["code"]["min_length"], 3)
        self.assertEqual(field_reqs["code"]["max_length"], 3)
        
        # Variable-length field should have wider bounds
        self.assertIn("min_length", field_reqs["description"])
        self.assertIn("max_length", field_reqs["description"])
    
    def test_dimension_requirements_generated(self):
        """Test that dimension requirements are included."""
        contract = self.generator.generate(self.sample_data, "test_data")
        
        self.assertIn("dimension_requirements", contract["requirements"])
        dim_reqs = contract["requirements"]["dimension_requirements"]
        
        # Check all 5 dimensions present
        self.assertIn("validity", dim_reqs)
        self.assertIn("completeness", dim_reqs)
        self.assertIn("consistency", dim_reqs)
        self.assertIn("freshness", dim_reqs)
        self.assertIn("plausibility", dim_reqs)
    
    def test_convenience_function(self):
        """Test the convenience function wrapper."""
        contract = generate_contract_from_data(self.sample_data, "test_data")
        
        self.assertIn("requirements", contract)
        self.assertIn("field_requirements", contract["requirements"])
        
        # Should have same behavior as direct generator use
        direct_contract = self.generator.generate(self.sample_data, "test_data")
        self.assertEqual(
            len(contract["requirements"]["field_requirements"]),
            len(direct_contract["requirements"]["field_requirements"])
        )
    
    def test_contract_metadata(self):
        """Test that contract metadata is generated."""
        contract = self.generator.generate(self.sample_data, "test_data")
        
        # Should have contracts/metadata section (depending on schema version)
        self.assertTrue(
            "contracts" in contract or "metadata" in contract,
            "Contract should have metadata section"
        )
    
    def test_empty_dataframe_handling(self):
        """Test handling of empty DataFrame."""
        empty_data = pd.DataFrame()
        
        # Should not crash, should return minimal contract
        contract = self.generator.generate(empty_data, "empty_test")
        self.assertIn("requirements", contract)
    
    def test_mixed_data_types(self):
        """Test contract generation with mixed data types."""
        mixed_data = pd.DataFrame({
            "int_col": [1, 2, 3],
            "float_col": [1.5, 2.5, 3.5],
            "string_col": ["a", "b", "c"],
            "bool_col": [True, False, True]
        })
        
        contract = self.generator.generate(mixed_data, "mixed_test")
        field_reqs = contract["requirements"]["field_requirements"]
        
        # Verify each type was correctly identified
        self.assertEqual(field_reqs["int_col"]["type"], "integer")
        self.assertEqual(field_reqs["float_col"]["type"], "float")
        self.assertEqual(field_reqs["string_col"]["type"], "string")
        self.assertEqual(field_reqs["bool_col"]["type"], "boolean")


class TestContractGeneratorEdgeCases(unittest.TestCase):
    """Test edge cases and special scenarios."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.generator = ContractGenerator()
    
    def test_single_row_data(self):
        """Test contract generation from single row."""
        single_row = pd.DataFrame([{"field1": "value1", "field2": 100}])
        
        contract = self.generator.generate(single_row, "single_row_test")
        field_reqs = contract["requirements"]["field_requirements"]
        
        self.assertEqual(len(field_reqs), 2)
        self.assertIn("field1", field_reqs)
        self.assertIn("field2", field_reqs)
    
    def test_data_with_special_characters(self):
        """Test handling of special characters in data."""
        special_data = pd.DataFrame({
            "email": ["test@example.com", "user+tag@domain.org"],
            "path": ["/usr/local/bin", "C:\\Windows\\System32"],
            "unicode": ["café", "naïve"]
        })
        
        contract = self.generator.generate(special_data, "special_test")
        field_reqs = contract["requirements"]["field_requirements"]
        
        # Should handle special characters without error
        self.assertEqual(len(field_reqs), 3)
    
    def test_generation_with_custom_config(self):
        """Test contract generation with custom configuration."""
        config = {
            "overall_minimum": 85.0,
            "include_plausibility": True
        }
        
        data = pd.DataFrame({
            "value": [10, 20, 30, 40, 50]
        })
        
        contract = self.generator.generate(data, "config_test", generation_config=config)
        
        # Contract should be generated successfully
        self.assertIn("requirements", contract)


class TestContractBuilderIntegration(unittest.TestCase):
    """Test integration with modular components."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.generator = ContractGenerator()
    
    def test_uses_data_profiler(self):
        """Test that generator uses DataProfiler."""
        data = pd.DataFrame({
            "field1": [1, 2, 3, 4, 5],
            "field2": ["a", "b", "c", "d", "e"]
        })
        
        contract = self.generator.generate(data, "profiler_test")
        
        # Profiler should detect field characteristics
        self.assertIsNotNone(contract)
        self.assertIn("requirements", contract)
    
    def test_generates_valid_yaml_structure(self):
        """Test that generated contract is valid YAML."""
        data = pd.DataFrame({
            "test_field": [1, 2, 3]
        })
        
        contract = self.generator.generate(data, "yaml_test")
        
        # Should be serializable to YAML
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(contract, f)
            yaml_path = f.name
        
        try:
            # Should be loadable
            with open(yaml_path, 'r') as f:
                loaded = yaml.safe_load(f)
            
            self.assertIsNotNone(loaded)
            self.assertIn("requirements", loaded)
        finally:
            Path(yaml_path).unlink()


if __name__ == '__main__':
    unittest.main()
