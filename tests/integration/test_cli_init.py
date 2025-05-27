"""
Integration tests for the `adri init` CLI command.

This module tests the end-to-end functionality of the metadata
generation command, including file I/O and error handling.
"""

import unittest
import tempfile
import shutil
import json
from pathlib import Path
import subprocess
import sys
import pandas as pd

# Add the project root to the path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from adri.cli import main as cli_main


class TestCLIInit(unittest.TestCase):
    """Test the CLI init command integration."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.test_data_path = self.temp_dir / "test_data.csv"
        
        # Create test CSV file
        test_df = pd.DataFrame({
            'id': ['ID001', 'ID002', 'ID003', 'ID004', 'ID005'],
            'name': ['Product A', 'Product B', 'Product C', 'Product D', 'Product E'],
            'price': [19.99, 29.99, 39.99, 49.99, 59.99],
            'quantity': [100, 200, 150, 80, 120],
            'category': ['Electronics', 'Electronics', 'Clothing', 'Clothing', 'Electronics'],
            'last_updated': ['2024-01-15', '2024-01-16', '2024-01-17', '2024-01-18', '2024-01-19'],
            'in_stock': [True, True, False, True, True]
        })
        test_df.to_csv(self.test_data_path, index=False)
        
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)
        
    def test_init_command_basic(self):
        """Test basic init command functionality."""
        # Run the init command
        result = subprocess.run([
            sys.executable, '-m', 'adri', 'init', 
            str(self.test_data_path)
        ], capture_output=True, text=True)
        
        # Check command succeeded
        self.assertEqual(result.returncode, 0, f"Command failed: {result.stderr}")
        
        # Check output messages
        self.assertIn("Analyzing data source:", result.stdout)
        self.assertIn("Generating metadata files", result.stdout)
        self.assertIn("✓ Generated validity metadata", result.stdout)
        self.assertIn("✓ Generated completeness metadata", result.stdout)
        self.assertIn("✓ Generated freshness metadata", result.stdout)
        self.assertIn("✓ Generated consistency metadata", result.stdout)
        self.assertIn("✓ Generated plausibility metadata", result.stdout)
        self.assertIn("✅ Metadata files generated successfully!", result.stdout)
        
        # Check all metadata files were created
        for dimension in ['validity', 'completeness', 'freshness', 'consistency', 'plausibility']:
            metadata_file = self.test_data_path.parent / f"test_data.{dimension}.json"
            self.assertTrue(metadata_file.exists(), f"{dimension} metadata file not created")
            
            # Verify it's valid JSON
            with open(metadata_file, 'r') as f:
                data = json.load(f)
                self.assertIsInstance(data, dict)
                
    def test_init_command_with_output_dir(self):
        """Test init command with custom output directory."""
        output_dir = Path(self.temp_dir) / "metadata_output"
        
        result = subprocess.run([
            sys.executable, '-m', 'adri', 'init', 
            str(self.test_data_path),
            '--output-dir', str(output_dir)
        ], capture_output=True, text=True)
        
        self.assertEqual(result.returncode, 0)
        
        # Check files were created in output directory
        for dimension in ['validity', 'completeness', 'freshness', 'consistency', 'plausibility']:
            metadata_file = output_dir / f"test_data.{dimension}.json"
            self.assertTrue(metadata_file.exists(), f"{dimension} metadata file not in output dir")
            
    def test_init_command_specific_dimensions(self):
        """Test init command with specific dimensions only."""
        result = subprocess.run([
            sys.executable, '-m', 'adri', 'init', 
            str(self.test_data_path),
            '--dimensions', 'validity', 'completeness'
        ], capture_output=True, text=True)
        
        self.assertEqual(result.returncode, 0)
        
        # Check only requested dimensions were created
        validity_file = self.test_data_path.parent / "test_data.validity.json"
        completeness_file = self.test_data_path.parent / "test_data.completeness.json"
        freshness_file = self.test_data_path.parent / "test_data.freshness.json"
        
        self.assertTrue(validity_file.exists())
        self.assertTrue(completeness_file.exists())
        self.assertFalse(freshness_file.exists())
        
    def test_init_command_file_not_found(self):
        """Test init command with non-existent file."""
        result = subprocess.run([
            sys.executable, '-m', 'adri', 'init', 
            str(self.temp_dir / "nonexistent.csv")
        ], capture_output=True, text=True)
        
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Error: Source file not found", result.stdout)
        
    def test_init_command_invalid_file_format(self):
        """Test init command with unsupported file format."""
        # Create a non-data file
        invalid_file = Path(self.temp_dir) / "invalid.txt"
        invalid_file.write_text("This is not a data file")
        
        result = subprocess.run([
            sys.executable, '-m', 'adri', 'init', 
            str(invalid_file)
        ], capture_output=True, text=True)
        
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Error generating metadata", result.stdout)
        
    def test_metadata_content_validity(self):
        """Test that generated metadata has correct content."""
        # Run init command
        subprocess.run([
            sys.executable, '-m', 'adri', 'init', 
            str(self.test_data_path)
        ], capture_output=True, text=True)
        
        # Check validity metadata content
        validity_file = self.test_data_path.parent / "test_data.validity.json"
        with open(validity_file, 'r') as f:
            validity_data = json.load(f)
            
        self.assertTrue(validity_data['has_explicit_validity_info'])
        self.assertIn('type_definitions', validity_data)
        self.assertIn('id', validity_data['type_definitions'])
        self.assertIn('price', validity_data['type_definitions'])
        
        # Check that numeric field has range
        price_def = validity_data['type_definitions']['price']
        self.assertIn('range', price_def)
        self.assertEqual(price_def['range'], [19.99, 59.99])
        
        # Check categorical field has allowed values
        category_def = validity_data['type_definitions']['category']
        self.assertIn('allowed_values', category_def)
        self.assertSetEqual(
            set(category_def['allowed_values']), 
            {'Clothing', 'Electronics'}
        )
        
    def test_metadata_content_completeness(self):
        """Test completeness metadata content."""
        subprocess.run([
            sys.executable, '-m', 'adri', 'init', 
            str(self.test_data_path)
        ], capture_output=True, text=True)
        
        completeness_file = self.test_data_path.parent / "test_data.completeness.json"
        with open(completeness_file, 'r') as f:
            completeness_data = json.load(f)
            
        self.assertTrue(completeness_data['has_explicit_completeness_info'])
        self.assertEqual(completeness_data['overall_completeness'], 1.0)  # No missing values
        
        # All fields should be 100% complete
        for field, info in completeness_data['fields'].items():
            self.assertEqual(info['completeness'], 1.0)
            self.assertEqual(info['missing_count'], 0)
            
    def test_metadata_content_freshness(self):
        """Test freshness metadata content."""
        subprocess.run([
            sys.executable, '-m', 'adri', 'init', 
            str(self.test_data_path)
        ], capture_output=True, text=True)
        
        freshness_file = self.test_data_path.parent / "test_data.freshness.json"
        with open(freshness_file, 'r') as f:
            freshness_data = json.load(f)
            
        self.assertTrue(freshness_data['has_explicit_freshness_info'])
        
        # Should detect last_updated as timestamp field
        self.assertIn('last_updated', freshness_data['fields'])
        self.assertTrue(freshness_data['fields']['last_updated']['timestamp_field'])
        self.assertIn('last_updated', freshness_data['_detected_timestamp_columns'])
        
    def test_init_with_json_file(self):
        """Test init command with JSON input file."""
        json_file = Path(self.temp_dir) / "test_data.json"
        
        # Create JSON test data
        test_data = [
            {"id": 1, "value": 100, "status": "active"},
            {"id": 2, "value": 200, "status": "inactive"},
            {"id": 3, "value": 150, "status": "active"}
        ]
        
        with open(json_file, 'w') as f:
            json.dump(test_data, f)
            
        result = subprocess.run([
            sys.executable, '-m', 'adri', 'init', 
            str(json_file)
        ], capture_output=True, text=True)
        
        self.assertEqual(result.returncode, 0)
        
        # Check metadata was generated
        validity_file = json_file.parent / "test_data.validity.json"
        self.assertTrue(validity_file.exists())
        
    def test_init_with_excel_file(self):
        """Test init command with Excel input file."""
        excel_file = Path(self.temp_dir) / "test_data.xlsx"
        
        # Create Excel test data
        test_df = pd.DataFrame({
            'product': ['A', 'B', 'C'],
            'sales': [1000, 2000, 1500],
            'region': ['North', 'South', 'North']
        })
        test_df.to_excel(excel_file, index=False)
        
        result = subprocess.run([
            sys.executable, '-m', 'adri', 'init', 
            str(excel_file)
        ], capture_output=True, text=True)
        
        self.assertEqual(result.returncode, 0)
        
        # Check metadata was generated
        validity_file = excel_file.parent / "test_data.validity.json"
        self.assertTrue(validity_file.exists())
        
    def test_init_command_through_cli_main(self):
        """Test init command through the CLI main function."""
        # This tests the internal CLI routing
        import sys
        from io import StringIO
        
        # Capture stdout
        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()
        
        try:
            # Run through internal CLI
            result = cli_main(['init', str(self.test_data_path)])
            self.assertEqual(result, 0)
            
            output = captured_output.getvalue()
            self.assertIn("Analyzing data source:", output)
            self.assertIn("✅ Metadata files generated successfully!", output)
            
        finally:
            sys.stdout = old_stdout
            
    def test_init_with_missing_values(self):
        """Test init with data containing missing values."""
        # Create data with missing values
        test_df = pd.DataFrame({
            'id': [1, 2, 3, 4, 5],
            'value': [10, None, 30, None, 50],
            'description': ['A', 'B', None, None, 'E']
        })
        
        missing_data_file = Path(self.temp_dir) / "missing_data.csv"
        test_df.to_csv(missing_data_file, index=False)
        
        result = subprocess.run([
            sys.executable, '-m', 'adri', 'init', 
            str(missing_data_file)
        ], capture_output=True, text=True)
        
        self.assertEqual(result.returncode, 0)
        
        # Check completeness metadata reflects missing values
        completeness_file = missing_data_file.parent / "missing_data.completeness.json"
        with open(completeness_file, 'r') as f:
            completeness_data = json.load(f)
            
        # Value field should show 60% completeness (3/5)
        self.assertEqual(completeness_data['fields']['value']['completeness'], 0.6)
        self.assertEqual(completeness_data['fields']['value']['missing_count'], 2)
        
        # Description field should show 60% completeness
        self.assertEqual(completeness_data['fields']['description']['completeness'], 0.6)
        self.assertEqual(completeness_data['fields']['description']['missing_count'], 2)


if __name__ == '__main__':
    unittest.main()
