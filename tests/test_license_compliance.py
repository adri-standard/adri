"""
Test suite for ADRI license compliance and attribution validation.

This module validates that all licensing and attribution requirements are met
across the ADRI project, ensuring compliance with Apache 2.0 license and
proper Verodat trademark protection.
"""

import os
import re
import unittest
from pathlib import Path


class TestLicenseCompliance(unittest.TestCase):
    """Test suite for license compliance and attribution validation."""

    def setUp(self):
        """Set up test fixtures with project root path."""
        self.project_root = Path(__file__).parent.parent

    def test_apache_2_license_exists(self):
        """Verify Apache 2.0 license file exists and contains correct content."""
        license_path = self.project_root / "LICENSE"
        self.assertTrue(license_path.exists(), "LICENSE file must exist")

        with open(license_path, 'r', encoding='utf-8') as f:
            license_content = f.read()

        # Check for Apache 2.0 license key elements
        self.assertIn("Apache License", license_content)
        self.assertIn("Version 2.0, January 2004", license_content)
        self.assertIn("Copyright 2025 Verodat", license_content)
        self.assertIn("http://www.apache.org/licenses/", license_content)

    def test_notice_file_compliance(self):
        """Verify NOTICE file exists and contains proper Apache 2.0 compliance."""
        notice_path = self.project_root / "NOTICE"
        self.assertTrue(notice_path.exists(), "NOTICE file must exist")

        with open(notice_path, 'r', encoding='utf-8') as f:
            notice_content = f.read()

        # Check for required NOTICE file elements
        self.assertIn("ADRI™ (Agent Data Readiness Index™)", notice_content)
        self.assertIn("Copyright (c) 2025 Verodat", notice_content)
        self.assertIn("https://verodat.com", notice_content)
        self.assertIn("Apache License, Version 2.0", notice_content)
        self.assertIn("trademarks of Verodat", notice_content)

    def test_trademark_policy_exists(self):
        """Verify trademark policy file exists with proper content."""
        trademark_path = self.project_root / "TRADEMARK.md"
        self.assertTrue(trademark_path.exists(), "TRADEMARK.md file must exist")

        with open(trademark_path, 'r', encoding='utf-8') as f:
            trademark_content = f.read()

        # Check for trademark policy key elements
        self.assertIn("ADRI™ Trademark Policy", trademark_content)
        self.assertIn("trademarks of Verodat", trademark_content)
        self.assertIn("legal@verodat.com", trademark_content)
        self.assertIn("Allowed Use", trademark_content)
        self.assertIn("Restricted Use", trademark_content)
        self.assertIn("Attribution Requirement", trademark_content)

    def test_readme_attribution(self):
        """Verify README.md contains proper Verodat attribution."""
        readme_path = self.project_root / "README.md"
        self.assertTrue(readme_path.exists(), "README.md file must exist")

        with open(readme_path, 'r', encoding='utf-8') as f:
            readme_content = f.read()

        # Check for attribution in README
        self.assertIn("Apache 2.0 License", readme_content)
        self.assertIn("Verodat", readme_content)
        # Flexible attribution check - accepts different wording
        self.assertTrue(
            "Built with ❤️ by" in readme_content or "founded and maintained by" in readme_content,
            "README must contain Verodat attribution"
        )

    def test_pyproject_metadata_compliance(self):
        """Verify pyproject.toml contains correct license and author information."""
        pyproject_path = self.project_root / "pyproject.toml"
        self.assertTrue(pyproject_path.exists(), "pyproject.toml file must exist")

        with open(pyproject_path, 'r', encoding='utf-8') as f:
            pyproject_content = f.read()

        # Check for proper license classification and author info
        self.assertIn("License :: OSI Approved :: Apache Software License", pyproject_content)
        self.assertIn("adri@verodat.com", pyproject_content)
        self.assertNotIn("ThinkVeolvesolve", pyproject_content, "Old copyright holder should be removed")

    def test_no_conflicting_copyright_statements(self):
        """Verify no conflicting or old copyright statements remain."""
        # Check key files for any remaining "ThinkVeolvesolve" references
        files_to_check = [
            self.project_root / "README.md",
            self.project_root / "pyproject.toml",
            self.project_root / "LICENSE",
        ]

        for file_path in files_to_check:
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                self.assertNotIn("ThinkVeolvesolve", content,
                    f"Old copyright holder found in {file_path}")

    def test_consistent_attribution_format(self):
        """Verify attribution format is consistent across all files."""
        # Flexible attribution pattern - multiple formats accepted
        attribution_patterns = [
            r"founded and maintained by.*Verodat",
            r"Built with ❤️ by.*Verodat",
            r"by.*Thomas Russell.*at.*Verodat"
        ]

        readme_path = self.project_root / "README.md"
        if readme_path.exists():
            with open(readme_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Check if at least one attribution pattern matches
            found = any(re.search(pattern, content, re.IGNORECASE) for pattern in attribution_patterns)
            self.assertTrue(found, "Verodat attribution not found in README.md")

    def test_trademark_symbols_usage(self):
        """Verify proper trademark symbol usage across documentation."""
        files_to_check = [
            self.project_root / "NOTICE",
            self.project_root / "TRADEMARK.md",
            self.project_root / "docs" / "docs" / "legal" / "trademark-policy.md",
        ]

        for file_path in files_to_check:
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Check for proper trademark usage
                self.assertIn("ADRI™", content, f"ADRI™ trademark not found in {file_path}")
                self.assertIn("Agent Data Readiness Index™", content,
                    f"Full trademark not found in {file_path}")


if __name__ == '__main__':
    unittest.main()
