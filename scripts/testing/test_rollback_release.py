#!/usr/bin/env python3
"""
Test script for rollback_release.py.

This script tests the rollback functionality in various scenarios.
"""

import os
import sys
import unittest
from unittest.mock import patch

# Add the scripts directory to the path so we can import rollback_release
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rollback_release import ReleaseRollback


class TestReleaseRollback(unittest.TestCase):
    """Test cases for the ReleaseRollback class."""

    def setUp(self):
        """Set up test fixtures."""
        self.rollback = ReleaseRollback(
            tag_name="candidate-beta-minor-v0.3.0",
            reason="Test rollback",
            dry_run=True,
        )

    def test_convert_tag_format_candidate_beta(self):
        """Test conversion of candidate beta tags."""
        proper_tag, version = self.rollback._convert_tag_format(
            "candidate-beta-minor-v0.3.0"
        )
        self.assertEqual(proper_tag, "Pre-release.Minor.v0.3.0-beta.1")
        self.assertEqual(version, "0.3.0-beta.1")

    def test_convert_tag_format_candidate_regular(self):
        """Test conversion of regular candidate tags."""
        rollback = ReleaseRollback("candidate-minor-v0.3.0", dry_run=True)
        proper_tag, version = rollback._convert_tag_format("candidate-minor-v0.3.0")
        self.assertEqual(proper_tag, "Release.Minor.v0.3.0")
        self.assertEqual(version, "0.3.0")

    def test_convert_tag_format_proper_tag(self):
        """Test handling of already proper tags."""
        rollback = ReleaseRollback("Pre-release.Minor.v0.3.0-beta.1", dry_run=True)
        proper_tag, version = rollback._convert_tag_format(
            "Pre-release.Minor.v0.3.0-beta.1"
        )
        self.assertEqual(proper_tag, "Pre-release.Minor.v0.3.0-beta.1")
        self.assertEqual(version, "0.3.0-beta.1")

    @patch("subprocess.run")
    def test_analyze_publication_status_git_tag_exists(self, mock_run):
        """Test analysis when git tag exists."""
        mock_run.return_value.stdout = "candidate-beta-minor-v0.3.0\n"
        mock_run.return_value.returncode = 0

        with patch.dict(os.environ, {"GITHUB_TOKEN": "test_token"}):
            with patch("requests.get") as mock_get:
                mock_get.return_value.status_code = 404
                status = self.rollback.analyze_publication_status()

        self.assertTrue(status["git_tag_exists"])

    @patch("subprocess.run")
    def test_analyze_publication_status_no_git_tag(self, mock_run):
        """Test analysis when git tag doesn't exist."""
        mock_run.return_value.stdout = ""
        mock_run.return_value.returncode = 0

        with patch.dict(os.environ, {"GITHUB_TOKEN": "test_token"}):
            with patch("requests.get") as mock_get:
                mock_get.return_value.status_code = 404
                status = self.rollback.analyze_publication_status()

        self.assertFalse(status["git_tag_exists"])

    def test_determine_rollback_type_clean(self):
        """Test rollback type determination for clean rollback."""
        status = {
            "git_tag_exists": True,
            "github_release_exists": True,
            "testpypi_published": False,
            "pypi_published": False,
        }
        rollback_type = self.rollback.determine_rollback_type(status)
        self.assertEqual(rollback_type, "clean")

    def test_determine_rollback_type_partial(self):
        """Test rollback type determination for partial rollback."""
        status = {
            "git_tag_exists": True,
            "github_release_exists": True,
            "testpypi_published": True,
            "pypi_published": False,
        }
        rollback_type = self.rollback.determine_rollback_type(status)
        self.assertEqual(rollback_type, "partial")

    def test_determine_rollback_type_yank_with_force(self):
        """Test rollback type determination for yank with force."""
        rollback = ReleaseRollback(
            tag_name="candidate-beta-minor-v0.3.0",
            reason="Test rollback",
            force=True,
            dry_run=True,
        )
        status = {
            "git_tag_exists": True,
            "github_release_exists": True,
            "testpypi_published": True,
            "pypi_published": True,
        }
        rollback_type = rollback.determine_rollback_type(status)
        self.assertEqual(rollback_type, "yank")

    def test_determine_rollback_type_pypi_without_force(self):
        """Test rollback type determination for PyPI without force."""
        status = {
            "git_tag_exists": True,
            "github_release_exists": True,
            "testpypi_published": True,
            "pypi_published": True,
        }
        with self.assertRaises(SystemExit):
            self.rollback.determine_rollback_type(status)


def main():
    """Run the test suite."""
    # Suppress print output during tests
    with patch("builtins.print"):
        unittest.main(verbosity=2)


if __name__ == "__main__":
    main()
