"""
Tests for the multi-source data example.
"""

import unittest
import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open, call
import tempfile
import shutil
import pandas as pd

# Add the project root to the path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))


class TestMultiSourceExample(unittest.TestCase):
    """Test the 04_multi_source.py example."""
    
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
        example_path = project_root / "examples" / "advanced" / "04_multi_source.py"
        
        # Check file exists
        self.assertTrue(example_path.exists(), f"Example file not found: {example_path}")
        
        # Check it's a valid Python file
        content = example_path.read_text()
        try:
            compile(content, str(example_path), 'exec')
        except SyntaxError as e:
            self.fail(f"Example has syntax error: {e}")
        
        # Check for key content
        self.assertIn("Multi-Source Data", content)
        self.assertIn("ADRI WAY", content)
        self.assertIn("vendor", content)
        self.assertIn("DataSourceAssessor", content)
    
    def test_multi_source_assessment_features(self):
        """Test that the example demonstrates multi-source assessment."""
        example_path = project_root / "examples" / "advanced" / "04_multi_source.py"
        content = example_path.read_text()
        
        # Verify multi-source features
        self.assertIn("DataSourceSimulator", content)
        self.assertIn("data_sources", content)
        self.assertIn("CRM", content)
        self.assertIn("Modern Data Platform", content)
        self.assertIn("Partner API", content)
        
    def test_data_independence(self):
        """Test that the example shows data source independence."""
        example_path = project_root / "examples" / "advanced" / "04_multi_source.py"
        content = example_path.read_text()
        
        # Verify data independence concepts
        self.assertIn("source-agnostic", content)
        self.assertIn("vendor lock-in", content)
        self.assertIn("plug", content)
        self.assertIn("standard", content)
        
    def test_unified_standards(self):
        """Test that the example includes unified standards."""
        example_path = project_root / "examples" / "advanced" / "04_multi_source.py"
        content = example_path.read_text()
        
        # Verify unified standards elements
        self.assertIn("CUSTOMER_360_STANDARD", content)
        self.assertIn("meets_standard", content)
        self.assertIn("required_standard", content)
        
    def test_source_comparison(self):
        """Test that the example shows source comparison."""
        example_path = project_root / "examples" / "advanced" / "04_multi_source.py"
        content = example_path.read_text()
        
        # Verify comparison features
        self.assertIn("ACCEPTED", content)
        self.assertIn("REJECTED", content)
        self.assertIn("Issues:", content)
        
    def test_cost_optimization(self):
        """Test that the example demonstrates cost optimization."""
        example_path = project_root / "examples" / "advanced" / "04_multi_source.py"
        content = example_path.read_text()
        
        # Verify cost optimization messaging
        self.assertIn("Cost Optimization", content)
        self.assertIn("$", content)
        self.assertIn("Save", content)
        
    def test_business_impact_analysis(self):
        """Test that the example includes business impact analysis."""
        example_path = project_root / "examples" / "advanced" / "04_multi_source.py"
        content = example_path.read_text()
        
        # Verify business impact
        self.assertIn("BENEFITS", content)
        self.assertIn("Vendor Negotiations", content)
        self.assertIn("Rapid Prototyping", content)
        self.assertIn("Disaster Recovery", content)


if __name__ == '__main__':
    unittest.main()
