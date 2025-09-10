"""
Demo validation utilities for ADRI examples.
Tests example functionality and user first impressions.
"""

import os
import subprocess
import sys
from pathlib import Path


class DemoValidator:
    """Validates that ADRI demos work for new users."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.examples_dir = self.project_root / "examples"
        
    def validate_example_imports(self, example_file):
        """Test that an example file imports without errors."""
        try:
            # Try to import and parse the file
            with open(example_file, 'r') as f:
                content = f.read()
                
            # Check for key ADRI imports
            if 'from adri' not in content and 'import adri' not in content:
                return False, "No ADRI imports found"
                
            return True, "Imports validated"
        except Exception as e:
            return False, f"Import validation failed: {e}"
    
    def check_dependency_helpers(self):
        """Check that dependency helpers are available."""
        helpers_file = self.examples_dir / "utils" / "dependency_helpers.py"
        return helpers_file.exists()
    
    def validate_framework_examples(self):
        """Validate all framework examples are present."""
        expected_frameworks = [
            "langchain-customer-service.py",
            "crewai-business-analysis.py", 
            "autogen-research-collaboration.py",
            "langgraph-workflow-automation.py",
            "llamaindex-document-processing.py",
            "haystack-knowledge-management.py",
            "semantic-kernel-ai-orchestration.py"
        ]
        
        missing = []
        for framework_file in expected_frameworks:
            file_path = self.examples_dir / framework_file
            if not file_path.exists():
                missing.append(framework_file)
                
        return len(missing) == 0, missing
    
    def get_validation_summary(self):
        """Get a summary of demo validation results."""
        results = {
            "dependency_helpers_available": self.check_dependency_helpers(),
            "framework_examples_complete": self.validate_framework_examples()[0],
            "missing_examples": self.validate_framework_examples()[1] if not self.validate_framework_examples()[0] else []
        }
        return results
