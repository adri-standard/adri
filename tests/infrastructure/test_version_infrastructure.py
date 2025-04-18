"""
Infrastructure tests for the version management system.

These tests verify the infrastructure components of the version management system,
including the GitHub workflow configuration and publishing scripts.
"""

import os
import re
import unittest
from pathlib import Path

from adri.version import __version__


class TestVersionInfrastructure(unittest.TestCase):
    """Test the infrastructure components of the version management system."""

    def test_github_workflow_config(self):
        """Test that GitHub workflow is properly configured for version checks."""
        # Check if GitHub workflow file exists
        workflow_path = Path(__file__).parent.parent.parent / ".github" / "workflows" / "publish.yml"
        self.assertTrue(workflow_path.exists(), f"GitHub workflow file should exist at {workflow_path}")
        
        # Read the workflow file
        with open(workflow_path, "r") as f:
            workflow_content = f.read()
        
        # Check that workflow contains version checks
        self.assertIn("Verify version matches tag", workflow_content,
                      "Workflow should verify version matches tag")
        self.assertIn("PACKAGE_VERSION", workflow_content,
                      "Workflow should extract package version")
        self.assertIn("FILE_VERSION", workflow_content,
                      "Workflow should extract file version")
        self.assertIn("TAG_VERSION", workflow_content,
                      "Workflow should extract tag version")
        self.assertIn("CHANGELOG", workflow_content,
                      "Workflow should verify CHANGELOG contains version")

    def test_publish_script(self):
        """Test that the publish script is properly configured."""
        # Check if publish script exists
        script_path = Path(__file__).parent.parent.parent / "scripts" / "publish_pypi.sh"
        self.assertTrue(script_path.exists(), f"Publish script should exist at {script_path}")
        
        # Read the script
        with open(script_path, "r") as f:
            script_content = f.read()
        
        # Check that script contains version checks
        self.assertIn("VERSION=", script_content,
                      "Script should extract version from pyproject.toml")
        self.assertIn("Check version in package", script_content,
                      "Script should verify package version")
        self.assertIn("Check CHANGELOG.md", script_content,
                      "Script should check CHANGELOG for version")

    def test_version_files_exist(self):
        """Test that all version-related files exist."""
        root_dir = Path(__file__).parent.parent.parent
        
        # Check that version files exist
        self.assertTrue((root_dir / "VERSIONS.md").exists(),
                        "VERSIONS.md should exist")
        self.assertTrue((root_dir / "CHANGELOG.md").exists(),
                        "CHANGELOG.md should exist")
        self.assertTrue((root_dir / "RELEASING.md").exists(),
                        "RELEASING.md should exist")
        self.assertTrue((root_dir / "adri" / "version.py").exists(),
                        "adri/version.py should exist")

    def test_version_consistency_with_pyproject(self):
        """Test that version in version.py matches pyproject.toml."""
        root_dir = Path(__file__).parent.parent.parent
        
        # Read pyproject.toml
        with open(root_dir / "pyproject.toml", "r") as f:
            pyproject_content = f.read()
        
        # Extract version
        match = re.search(r'version\s*=\s*"([^"]+)"', pyproject_content)
        self.assertIsNotNone(match, "Should find version in pyproject.toml")
        
        pyproject_version = match.group(1)
        self.assertEqual(pyproject_version, __version__,
                         f"Version in pyproject.toml ({pyproject_version}) should match __version__ ({__version__})")

    def test_versions_md_contains_current_version(self):
        """Test that VERSIONS.md contains the current version."""
        root_dir = Path(__file__).parent.parent.parent
        
        # Read VERSIONS.md
        with open(root_dir / "VERSIONS.md", "r") as f:
            versions_content = f.read()
        
        # Check for current version
        self.assertIn(__version__, versions_content,
                      f"VERSIONS.md should contain current version {__version__}")

    def test_release_documentation_structure(self):
        """Test that release documentation contains required sections."""
        root_dir = Path(__file__).parent.parent.parent
        
        # Read RELEASING.md
        with open(root_dir / "RELEASING.md", "r") as f:
            releasing_content = f.read()
        
        # Check for required sections
        required_sections = [
            "# Release Process",
            "Version Number",
            "Update Version Information",
            "Update Documentation",
            "Create a Pull Request",
            "Merge and Tag",
            "GitHub Release",
            "Verify the Release"
        ]
        
        for section in required_sections:
            self.assertIn(section, releasing_content,
                          f"RELEASING.md should contain {section} section")


if __name__ == "__main__":
    unittest.main()
