"""
Tests for the data team contract example that demonstrates communication bridging.
"""

import unittest
import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import tempfile
import shutil
from datetime import datetime

# Add the project root to the path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))


class TestDataTeamContractExample(unittest.TestCase):
    """Test the 03_data_team_contract.py example."""
    
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
        example_path = project_root / "examples" / "03_data_team_contract.py"
        
        # Check file exists
        self.assertTrue(example_path.exists(), f"Example file not found: {example_path}")
        
        # Check it's a valid Python file
        content = example_path.read_text()
        try:
            compile(content, str(example_path), 'exec')
        except SyntaxError as e:
            self.fail(f"Example has syntax error: {e}")
        
        # Check for key content
        self.assertIn("Data Team Contract", content)
        self.assertIn("Communication Bridge", content)
        self.assertIn("SCENARIO", content)
        self.assertIn("DataSourceAssessor", content)
    
    def test_business_language_translation(self):
        """Test that the example demonstrates business language translation."""
        example_path = project_root / "examples" / "03_data_team_contract.py"
        content = example_path.read_text()
        
        # Verify business language elements
        self.assertIn("AI Engineer", content)
        self.assertIn("Data Team", content)
        self.assertIn("Management", content)
        self.assertIn("fraud", content)
        self.assertIn("production", content)
        
    def test_stakeholder_communication_features(self):
        """Test that the example shows stakeholder communication features."""
        example_path = project_root / "examples" / "03_data_team_contract.py"
        content = example_path.read_text()
        
        # Verify communication features
        self.assertIn("AI Engineer View", content)
        self.assertIn("Data Engineer View", content)
        self.assertIn("Management View", content)
        self.assertIn("progress", content)
        self.assertIn("readiness", content)
        
    def test_automated_reporting_structure(self):
        """Test that the example includes automated reporting."""
        example_path = project_root / "examples" / "03_data_team_contract.py"
        content = example_path.read_text()
        
        # Verify automated reporting elements
        self.assertIn("score", content)
        self.assertIn("threshold", content)
        self.assertIn("notification", content)
        self.assertIn("alert", content)
        
    def test_collaboration_patterns(self):
        """Test that the example shows collaboration patterns."""
        example_path = project_root / "examples" / "03_data_team_contract.py"
        content = example_path.read_text()
        
        # Verify collaboration elements
        self.assertIn("Sprint Planning", content)
        self.assertIn("Debugging Sessions", content)
        self.assertIn("Quality Reviews", content)
        
    def test_sla_monitoring(self):
        """Test that the example includes SLA monitoring."""
        example_path = project_root / "examples" / "03_data_team_contract.py"
        content = example_path.read_text()
        
        # Verify SLA monitoring features
        self.assertIn("SLA", content)
        self.assertIn("accountability", content)
        self.assertIn("Monitoring", content)
        
    def test_visual_reporting(self):
        """Test that the example demonstrates visual reporting."""
        example_path = project_root / "examples" / "03_data_team_contract.py"
        content = example_path.read_text()
        
        # Verify visual elements
        self.assertIn("Dashboard", content)
        self.assertIn("█", content)  # Progress bar character
        self.assertIn("🟢", content)  # Status indicators


if __name__ == '__main__':
    unittest.main()
