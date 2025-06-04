"""
Tests for the requirements as code example.
"""

import unittest
import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import tempfile
import shutil
import json

# Add the project root to the path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))


class TestRequirementsAsCodeExample(unittest.TestCase):
    """Test the 02_requirements_as_code.py example."""
    
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
        example_path = project_root / "examples" / "basic" / "02_requirements_as_code.py"
        
        # Check file exists
        self.assertTrue(example_path.exists(), f"Example file not found: {example_path}")
        
        # Check it's a valid Python file
        content = example_path.read_text()
        try:
            compile(content, str(example_path), 'exec')
        except SyntaxError as e:
            self.fail(f"Example has syntax error: {e}")
        
        # Check for key content
        self.assertIn("Requirements as Code", content)
        self.assertIn("ADRI WAY", content)
        self.assertIn("OLD WAY", content)
        self.assertIn("DataSourceAssessor", content)
        self.assertIn("Config", content)
    
    def test_contract_structure(self):
        """Test that the example demonstrates proper contract structure."""
        example_path = project_root / "examples" / "basic" / "02_requirements_as_code.py"
        content = example_path.read_text()
        
        # Verify contract elements
        self.assertIn("requirements", content)
        self.assertIn("minimum_score", content)
        self.assertIn("template", content)
        self.assertIn("Config", content)
        
    def test_automated_compliance_checking(self):
        """Test that the example shows automated compliance checking."""
        example_path = project_root / "examples" / "basic" / "02_requirements_as_code.py"
        content = example_path.read_text()
        
        # Verify compliance checking features
        self.assertIn("assess", content)
        self.assertIn("score", content)
        self.assertIn("Requirements", content)
        self.assertIn("requirements", content)
        
    def test_yaml_contract_example(self):
        """Test that the example includes YAML contract format."""
        example_path = project_root / "examples" / "basic" / "02_requirements_as_code.py"
        content = example_path.read_text()
        
        # Verify YAML contract structure
        self.assertIn("yaml", content)
        self.assertIn("version", content)
        self.assertIn("requirements:", content)
        self.assertIn("freshness:", content)
        
    def test_ci_cd_integration_example(self):
        """Test that the example shows CI/CD integration."""
        example_path = project_root / "examples" / "basic" / "02_requirements_as_code.py"
        content = example_path.read_text()
        
        # Verify CI/CD integration concepts
        self.assertIn("validation", content)
        self.assertIn("Track progress", content)
        self.assertIn("Day", content)
        
    def test_business_impact_messaging(self):
        """Test that the example includes business impact messaging."""
        example_path = project_root / "examples" / "basic" / "02_requirements_as_code.py"
        content = example_path.read_text()
        
        # Verify business impact content
        self.assertIn("IMPACT", content)
        self.assertIn("Business Value", content)
        self.assertIn("deployment", content)


if __name__ == '__main__':
    unittest.main()
