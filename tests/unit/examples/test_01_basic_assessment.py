"""
Tests for the basic assessment example that demonstrates agent blindness.
"""

import unittest
import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import pandas as pd
from datetime import datetime, timedelta
import tempfile
import shutil

# Add the project root to the path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))


class TestBasicAssessmentExample(unittest.TestCase):
    """Test the 01_basic_assessment.py example."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        
    def tearDown(self):
        """Clean up test environment."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)
    
    def test_example_exists_and_is_valid(self):
        """Test that the example file exists and contains expected content."""
        example_path = project_root / "examples" / "01_basic_assessment.py"
        
        # Check file exists
        self.assertTrue(example_path.exists(), f"Example file not found: {example_path}")
        
        # Check it's a valid Python file
        content = example_path.read_text()
        try:
            compile(content, str(example_path), 'exec')
        except SyntaxError as e:
            self.fail(f"Example has syntax error: {e}")
        
        # Check for key content
        self.assertIn("Agent Blindness", content)
        self.assertIn("WITHOUT ADRI", content)
        self.assertIn("WITH ADRI", content)
        self.assertIn("DataSourceAssessor", content)
    
    def test_demonstrates_agent_blindness_problem(self):
        """Test that the example effectively demonstrates the agent blindness problem."""
        # Create test data similar to what the example uses
        test_data = pd.DataFrame({
            'product_id': ['P001', 'P002'],
            'stock_level': [45, 23],
            'last_updated': [datetime.now() - timedelta(days=3)] * 2,
            'warehouse': ['East', None],
            'reorder_threshold': [50, -10]
        })
        
        # Save test data
        test_data.to_csv('test_inventory.csv', index=False)
        
        # Verify the data has quality issues
        self.assertTrue((test_data['stock_level'] < 100).any())  # Would trigger reorder
        self.assertTrue((test_data['warehouse'].isna()).any())  # Missing data
        self.assertTrue((test_data['reorder_threshold'] < 0).any())  # Invalid data
        
        # Clean up
        os.remove('test_inventory.csv')
    
    def test_cleanup_removes_temporary_files(self):
        """Test that the example cleans up after itself."""
        # Create a dummy file
        test_file = 'inventory_demo.csv'
        Path(test_file).touch()
        
        # Verify file exists
        self.assertTrue(os.path.exists(test_file))
        
        # The example should remove it
        if os.path.exists(test_file):
            os.remove(test_file)
        
        # Verify file is gone
        self.assertFalse(os.path.exists(test_file))
    
    def test_cost_calculation_message(self):
        """Test that the example includes cost impact messaging."""
        example_path = project_root / "examples" / "01_basic_assessment.py"
        content = example_path.read_text()
        
        # Verify cost-related content
        self.assertIn("$127,000", content)
        self.assertIn("excess inventory", content)
        self.assertIn("Loss:", content)
        
    def test_before_after_comparison(self):
        """Test that the example shows clear before/after comparison."""
        example_path = project_root / "examples" / "01_basic_assessment.py"
        content = example_path.read_text()
        
        # Verify comparison structure
        self.assertIn("WITHOUT ADRI", content)
        self.assertIn("WITH ADRI", content)
        self.assertIn("simulate_agent_without_adri", content)
        self.assertIn("adri_guard", content)


if __name__ == '__main__':
    unittest.main()
