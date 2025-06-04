"""
Tests for the metadata generation example.
"""

import unittest
import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile
import shutil

# Add the project root to the path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))


class TestMetadataGenerationExample(unittest.TestCase):
    """Test the 06_metadata_generation.py example."""
    
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
        example_path = project_root / "examples" / "advanced" / "06_metadata_generation.py"
        
        # Check file exists
        self.assertTrue(example_path.exists(), f"Example file not found: {example_path}")
        
        # Check it's a valid Python file
        content = example_path.read_text()
        try:
            compile(content, str(example_path), 'exec')
        except SyntaxError as e:
            self.fail(f"Example has syntax error: {e}")
        
        # Check for key content
        self.assertIn("Automatic Metadata Generation", content)
        self.assertIn("adri init", content)
        self.assertIn("metadata overhead", content)
        self.assertIn("MetadataGenerator", content)
        self.assertIn("subprocess.run", content)
    
    def test_example_demonstrates_init_command(self):
        """Test that the example demonstrates the init command."""
        example_path = project_root / "examples" / "advanced" / "06_metadata_generation.py"
        content = example_path.read_text()
        
        # Verify init command features
        self.assertIn("adri init", content)
        self.assertIn("--output-dir", content)
        self.assertIn("test_init_data.csv", content)
        self.assertIn("generated_metadata", content)
        
    def test_example_shows_time_savings(self):
        """Test that the example highlights time savings."""
        example_path = project_root / "examples" / "advanced" / "06_metadata_generation.py"
        content = example_path.read_text()
        
        # Verify time savings claims
        self.assertIn("Time Savings", content)
        self.assertIn("2-4 hours", content)
        self.assertIn("5 minutes", content)
        self.assertIn("95% reduction", content)
        
    def test_example_covers_all_dimensions(self):
        """Test that the example covers all ADRI dimensions."""
        example_path = project_root / "examples" / "advanced" / "06_metadata_generation.py"
        content = example_path.read_text()
        
        # Verify all dimensions are mentioned
        dimensions = ['validity', 'completeness', 'freshness', 'consistency', 'plausibility']
        for dimension in dimensions:
            self.assertIn(dimension, content)
        
        # Verify single combined metadata file is used
        self.assertIn("test_init_data.adri_metadata.json", content)
        self.assertIn("Metadata contains all 5 dimensions", content)
            
    def test_example_shows_metadata_content(self):
        """Test that the example shows generated metadata content."""
        example_path = project_root / "examples" / "advanced" / "06_metadata_generation.py"
        content = example_path.read_text()
        
        # Verify metadata content examples
        self.assertIn("Detected column types", content)
        self.assertIn("Overall completeness", content)
        self.assertIn("Detected timestamp columns", content)
        self.assertIn("outliers", content)
        self.assertIn("TODO", content)
        
    def test_example_includes_benefits(self):
        """Test that the example lists key benefits."""
        example_path = project_root / "examples" / "advanced" / "06_metadata_generation.py"
        content = example_path.read_text()
        
        # Verify benefits section
        self.assertIn("Key Benefits", content)
        self.assertIn("Auto-detected data types", content)
        self.assertIn("Statistical analysis", content)
        self.assertIn("Pre-filled metadata", content)
        self.assertIn("Domain-specific placeholders", content)
        
    def test_example_includes_next_steps(self):
        """Test that the example provides next steps."""
        example_path = project_root / "examples" / "advanced" / "06_metadata_generation.py"
        content = example_path.read_text()
        
        # Verify next steps
        self.assertIn("Next Steps", content)
        self.assertIn("Review the generated files", content)
        self.assertIn("Fill in the TODO sections", content)
        self.assertIn("Customize thresholds", content)
        self.assertIn("Run 'adri assess'", content)
        
    def test_test_data_file_exists(self):
        """Test that the example test data file exists."""
        test_data_path = project_root / "examples" / "test_init_data.csv"
        
        self.assertTrue(test_data_path.exists(), f"Test data file not found: {test_data_path}")
        
        # Verify it's a valid CSV
        content = test_data_path.read_text()
        self.assertIn("date", content)
        self.assertIn("product", content)
        self.assertIn("quantity", content)
        self.assertIn("price", content)
        self.assertIn("category", content)
        
    def test_example_executable_structure(self):
        """Test that the example has proper executable structure."""
        example_path = project_root / "examples" / "advanced" / "06_metadata_generation.py"
        content = example_path.read_text()
        
        # Check for main function
        self.assertIn("def main():", content)
        self.assertIn('if __name__ == "__main__":', content)
        self.assertIn("main()", content)
        
    def test_example_imports(self):
        """Test that the example has necessary imports."""
        example_path = project_root / "examples" / "advanced" / "06_metadata_generation.py"
        content = example_path.read_text()
        
        # Check required imports
        self.assertIn("import os", content)
        self.assertIn("import json", content)
        self.assertIn("import subprocess", content)
        self.assertIn("from pathlib import Path", content)


if __name__ == '__main__':
    unittest.main()
