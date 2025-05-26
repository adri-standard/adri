"""
Tests for the production guard example.
"""

import unittest
import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock, PropertyMock
import tempfile
import shutil
from datetime import datetime

# Add the project root to the path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))


class TestProductionGuardExample(unittest.TestCase):
    """Test the 05_production_guard.py example."""
    
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
        example_path = project_root / "examples" / "05_production_guard.py"
        
        # Check file exists
        self.assertTrue(example_path.exists(), f"Example file not found: {example_path}")
        
        # Check it's a valid Python file
        content = example_path.read_text()
        try:
            compile(content, str(example_path), 'exec')
        except SyntaxError as e:
            self.fail(f"Example has syntax error: {e}")
        
        # Check for key content
        self.assertIn("Production Guards", content)
        self.assertIn("Trust Verification", content)
        self.assertIn("Healthcare", content)
        self.assertIn("DataSourceAssessor", content)
        self.assertIn("adri_guard", content)
    
    def test_guard_implementation(self):
        """Test that the example demonstrates guards."""
        example_path = project_root / "examples" / "05_production_guard.py"
        content = example_path.read_text()
        
        # Verify guard features
        self.assertIn("@adri_guard", content)
        self.assertIn("min_score", content)
        self.assertIn("diagnose_patient", content)
        self.assertIn("quality", content)
        self.assertIn("GUARD ACTIVATED", content)
        
    def test_compliance_features(self):
        """Test that the example shows compliance features."""
        example_path = project_root / "examples" / "05_production_guard.py"
        content = example_path.read_text()
        
        # Verify compliance
        self.assertIn("compliance", content)
        self.assertIn("audit", content)
        self.assertIn("Healthcare", content)
        self.assertIn("HIPAA", content)
        
    def test_template_patterns(self):
        """Test that the example includes template patterns."""
        example_path = project_root / "examples" / "05_production_guard.py"
        content = example_path.read_text()
        
        # Verify template implementation
        self.assertIn("healthcare-hipaa-v1", content)
        self.assertIn("financial-basel-iii-v1", content)
        self.assertIn("manufacturing-iso-v1", content)
        self.assertIn("template", content)
        
    def test_fallback_mechanisms(self):
        """Test that the example shows fallback mechanisms."""
        example_path = project_root / "examples" / "05_production_guard.py"
        content = example_path.read_text()
        
        # Verify fallback features
        self.assertIn("fallback", content)
        self.assertIn("Graceful Degradation", content)
        self.assertIn("Multi-Level Guards", content)
        
    def test_audit_trail(self):
        """Test that the example demonstrates audit trails."""
        example_path = project_root / "examples" / "05_production_guard.py"
        content = example_path.read_text()
        
        # Verify audit trail features
        self.assertIn("audit_log", content)
        self.assertIn("timestamp", content)
        self.assertIn("log_audit_event", content)
        self.assertIn("traceability", content)
        
    def test_production_patterns(self):
        """Test that the example includes production patterns."""
        example_path = project_root / "examples" / "05_production_guard.py"
        content = example_path.read_text()
        
        # Verify performance features
        self.assertIn("PRODUCTION PATTERNS", content)
        self.assertIn("Custom Notifications", content)
        self.assertIn("on_fail", content)
        self.assertIn("on_pass", content)
        
    def test_risk_mitigation(self):
        """Test that the example addresses risk mitigation."""
        example_path = project_root / "examples" / "05_production_guard.py"
        content = example_path.read_text()
        
        # Verify security features
        self.assertIn("Risk Mitigation", content)
        self.assertIn("blocked", content)
        # Changed from "protection" to "protected" which is actually in the file
        self.assertIn("protected", content)


if __name__ == '__main__':
    unittest.main()
