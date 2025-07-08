#!/usr/bin/env python3
"""
Test suite for the rollback_release.py script.

This test suite validates the rollback functionality without making actual changes.
"""

import os
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, Mock, patch

# Add the scripts directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rollback_release import ReleaseRollback


class TestReleaseRollback(unittest.TestCase):
    """Test cases for the ReleaseRollback class."""

    def setUp(self):
        """Set up test fixtures."""
        self.rollback = ReleaseRollback(
            tag_name="candidate-beta-minor-v0.3.0",
            reason="Test rollback",
            force=False,
            dry_run=True,
        )

    def test_tag_conversion_candidate_beta(self):
        """Test conversion of candidate beta tags."""
        rollback = ReleaseRollback("candidate-beta-minor-v0.3.0", dry_run=True)
        self.assertEqual(rollback.proper_tag, "Pre-release.Minor.v0.3.0-beta.1")
        self.assertEqual(rollback.version, "0.3.0-beta.1")

    def test_tag_conversion_candidate_production(self):
        """Test conversion of candidate production tags."""
        rollback = ReleaseRollback("candidate-minor-v0.3.0", dry_run=True)
        self.assertEqual(rollback.proper_tag, "Release.Minor.v0.3.0")
        self.assertEqual(rollback.version, "0.3.0")

    def test_tag_conversion_proper_tag(self):
        """Test handling of already proper tags."""
        rollback = ReleaseRollback("Pre-release.Minor.v0.3.0-beta.1", dry_run=True)
        self.assertEqual(rollback.proper_tag, "Pre-release.Minor.v0.3.0-beta.1")
        self.assertEqual(rollback.version, "0.3.0-beta.1")

    @patch("subprocess.run")
    def test_analyze_publication_status_git_tag_exists(self, mock_run):
        """Test analysis when Git tag exists."""
        mock_run.return_value = Mock(
            stdout="candidate-beta-minor-v0.3.0\n", returncode=0
        )

        with patch("requests.get") as mock_get:
            mock_get.return_value = Mock(status_code=404)

            status = self.rollback.analyze_publication_status()

            self.assertTrue(status["git_tag_exists"])
            self.assertFalse(status["pypi_published"])
            self.assertFalse(status["testpypi_published"])

    @patch("subprocess.run")
    def test_analyze_publication_status_git_tag_missing(self, mock_run):
        """Test analysis when Git tag is missing."""
        mock_run.return_value = Mock(stdout="", returncode=0)

        with patch("requests.get") as mock_get:
            mock_get.return_value = Mock(status_code=404)

            status = self.rollback.analyze_publication_status()

            self.assertFalse(status["git_tag_exists"])

    @patch("requests.get")
    def test_analyze_publication_status_pypi_published(self, mock_get):
        """Test analysis when package is published to PyPI."""

        def mock_requests_get(url, **kwargs):
            if "pypi.org" in url:
                return Mock(status_code=200)
            else:
                return Mock(status_code=404)

        mock_get.side_effect = mock_requests_get

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(stdout="", returncode=0)

            status = self.rollback.analyze_publication_status()

            self.assertTrue(status["pypi_published"])
            self.assertFalse(status["testpypi_published"])

    @patch("requests.get")
    def test_analyze_publication_status_testpypi_published(self, mock_get):
        """Test analysis when package is published to TestPyPI only."""

        def mock_requests_get(url, **kwargs):
            if "test.pypi.org" in url:
                return Mock(status_code=200)
            else:
                return Mock(status_code=404)

        mock_get.side_effect = mock_requests_get

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(stdout="", returncode=0)

            status = self.rollback.analyze_publication_status()

            self.assertFalse(status["pypi_published"])
            self.assertTrue(status["testpypi_published"])

    def test_determine_rollback_type_clean(self):
        """Test rollback type determination for clean rollback."""
        status = {
            "pypi_published": False,
            "testpypi_published": False,
            "git_tag_exists": True,
            "github_release_exists": True,
        }

        rollback_type = self.rollback.determine_rollback_type(status)
        self.assertEqual(rollback_type, "clean")

    def test_determine_rollback_type_partial(self):
        """Test rollback type determination for partial rollback."""
        status = {
            "pypi_published": False,
            "testpypi_published": True,
            "git_tag_exists": True,
            "github_release_exists": True,
        }

        rollback_type = self.rollback.determine_rollback_type(status)
        self.assertEqual(rollback_type, "partial")

    def test_determine_rollback_type_yank_with_force(self):
        """Test rollback type determination for yank rollback with force."""
        rollback = ReleaseRollback(
            tag_name="candidate-beta-minor-v0.3.0",
            reason="Test rollback",
            force=True,
            dry_run=True,
        )

        status = {
            "pypi_published": True,
            "testpypi_published": True,
            "git_tag_exists": True,
            "github_release_exists": True,
        }

        rollback_type = rollback.determine_rollback_type(status)
        self.assertEqual(rollback_type, "yank")

    def test_determine_rollback_type_yank_without_force_fails(self):
        """Test rollback type determination fails for PyPI published without force."""
        status = {
            "pypi_published": True,
            "testpypi_published": True,
            "git_tag_exists": True,
            "github_release_exists": True,
        }

        with self.assertRaises(SystemExit):
            self.rollback.determine_rollback_type(status)

    @patch("subprocess.run")
    def test_execute_rollback_dry_run(self, mock_run):
        """Test rollback execution in dry run mode."""
        status = {
            "pypi_published": False,
            "testpypi_published": False,
            "git_tag_exists": True,
            "github_release_exists": True,
        }

        # Should not call any subprocess commands in dry run
        self.rollback.execute_rollback("clean", status)
        mock_run.assert_not_called()

    @patch("subprocess.run")
    def test_execute_rollback_clean(self, mock_run):
        """Test clean rollback execution."""
        rollback = ReleaseRollback(
            tag_name="candidate-beta-minor-v0.3.0",
            reason="Test rollback",
            force=False,
            dry_run=False,
        )

        status = {
            "pypi_published": False,
            "testpypi_published": False,
            "git_tag_exists": True,
            "github_release_exists": True,
        }

        mock_run.return_value = Mock(returncode=0)

        with patch.dict(os.environ, {"GITHUB_TOKEN": "test-token"}):
            rollback.execute_rollback("clean", status)

        # Should have called git commands for tag deletion
        self.assertTrue(mock_run.called)

    def test_cleanup_candidate_releases_for_candidate_tag(self):
        """Test cleanup when tag is already a candidate."""
        actions_taken = []
        self.rollback._cleanup_candidate_releases(actions_taken)

        # Should not add any actions for candidate tags
        self.assertEqual(len(actions_taken), 0)

    @patch("subprocess.run")
    def test_cleanup_candidate_releases_for_proper_tag(self, mock_run):
        """Test cleanup of candidate releases for proper tags."""
        rollback = ReleaseRollback(
            tag_name="Pre-release.Minor.v0.3.0-beta.1",
            reason="Test rollback",
            force=False,
            dry_run=False,
        )

        mock_run.return_value = Mock(returncode=0, stdout="")

        actions_taken = []
        with patch.dict(os.environ, {"GITHUB_TOKEN": "test-token"}):
            rollback._cleanup_candidate_releases(actions_taken)

        # Should have attempted to check for candidate releases
        self.assertTrue(mock_run.called)

    def test_generate_rollback_summary(self):
        """Test rollback summary generation."""
        actions_taken = ["Git tags deleted", "GitHub release deleted"]

        # Should not raise any exceptions
        self.rollback._generate_rollback_summary("clean", actions_taken)

    @patch("rollback_release.ReleaseRollback.analyze_publication_status")
    @patch("rollback_release.ReleaseRollback.determine_rollback_type")
    @patch("rollback_release.ReleaseRollback.execute_rollback")
    def test_run_success(self, mock_execute, mock_determine, mock_analyze):
        """Test successful rollback run."""
        mock_analyze.return_value = {"pypi_published": False}
        mock_determine.return_value = "clean"

        # Should complete without exceptions
        self.rollback.run()

        mock_analyze.assert_called_once()
        mock_determine.assert_called_once()
        mock_execute.assert_called_once()

    @patch("rollback_release.ReleaseRollback.analyze_publication_status")
    def test_run_keyboard_interrupt(self, mock_analyze):
        """Test rollback run with keyboard interrupt."""
        mock_analyze.side_effect = KeyboardInterrupt()

        with self.assertRaises(SystemExit):
            self.rollback.run()

    @patch("rollback_release.ReleaseRollback.analyze_publication_status")
    def test_run_exception(self, mock_analyze):
        """Test rollback run with exception."""
        mock_analyze.side_effect = Exception("Test error")

        with self.assertRaises(SystemExit):
            self.rollback.run()


class TestRollbackScript(unittest.TestCase):
    """Test cases for the rollback script main function."""

    @patch(
        "sys.argv", ["rollback_release.py", "candidate-beta-minor-v0.3.0", "--dry-run"]
    )
    @patch("rollback_release.ReleaseRollback")
    def test_main_with_dry_run(self, mock_rollback_class):
        """Test main function with dry run."""
        mock_rollback = Mock()
        mock_rollback_class.return_value = mock_rollback

        from rollback_release import main

        main()

        mock_rollback_class.assert_called_once_with(
            tag_name="candidate-beta-minor-v0.3.0", reason="", force=False, dry_run=True
        )
        mock_rollback.run.assert_called_once()

    @patch(
        "sys.argv",
        [
            "rollback_release.py",
            "Pre-release.Minor.v0.3.0-beta.1",
            "--reason",
            "Critical bug",
            "--force",
        ],
    )
    @patch("rollback_release.ReleaseRollback")
    def test_main_with_force(self, mock_rollback_class):
        """Test main function with force option."""
        mock_rollback = Mock()
        mock_rollback_class.return_value = mock_rollback

        from rollback_release import main

        main()

        mock_rollback_class.assert_called_once_with(
            tag_name="Pre-release.Minor.v0.3.0-beta.1",
            reason="Critical bug",
            force=True,
            dry_run=False,
        )
        mock_rollback.run.assert_called_once()

    @patch("sys.argv", ["rollback_release.py", "test-tag", "--dry-run"])
    @patch("subprocess.run")
    def test_main_git_check_success(self, mock_run):
        """Test main function git availability check success."""
        mock_run.return_value = Mock(returncode=0)

        with patch("rollback_release.ReleaseRollback") as mock_rollback_class:
            mock_rollback = Mock()
            mock_rollback_class.return_value = mock_rollback

            from rollback_release import main

            main()

            # Should proceed to create rollback instance
            mock_rollback_class.assert_called_once()

    @patch("sys.argv", ["rollback_release.py", "test-tag"])
    @patch("subprocess.run")
    def test_main_git_check_failure(self, mock_run):
        """Test main function git availability check failure."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "git")

        with self.assertRaises(SystemExit):
            from rollback_release import main

            main()

    @patch("sys.argv", ["rollback_release.py", "test-tag"])
    @patch("subprocess.run")
    def test_main_git_not_found(self, mock_run):
        """Test main function when git is not found."""
        mock_run.side_effect = FileNotFoundError()

        with self.assertRaises(SystemExit):
            from rollback_release import main

            main()


class TestIntegration(unittest.TestCase):
    """Integration tests for the rollback system."""

    def test_candidate_tag_workflow(self):
        """Test complete workflow for candidate tag rollback."""
        rollback = ReleaseRollback(
            tag_name="candidate-beta-minor-v0.3.0",
            reason="Integration test",
            force=False,
            dry_run=True,
        )

        # Test tag conversion
        self.assertEqual(rollback.proper_tag, "Pre-release.Minor.v0.3.0-beta.1")
        self.assertEqual(rollback.version, "0.3.0-beta.1")

        # Test status analysis (mocked)
        with patch("subprocess.run") as mock_run, patch("requests.get") as mock_get:
            mock_run.return_value = Mock(stdout="", returncode=0)
            mock_get.return_value = Mock(status_code=404)

            status = rollback.analyze_publication_status()
            rollback_type = rollback.determine_rollback_type(status)

            self.assertEqual(rollback_type, "clean")

    def test_proper_tag_workflow(self):
        """Test complete workflow for proper tag rollback."""
        rollback = ReleaseRollback(
            tag_name="Release.Minor.v0.3.0",
            reason="Integration test",
            force=False,
            dry_run=True,
        )

        # Test tag handling
        self.assertEqual(rollback.proper_tag, "Release.Minor.v0.3.0")
        self.assertEqual(rollback.version, "0.3.0")

        # Test status analysis (mocked)
        with patch("subprocess.run") as mock_run, patch("requests.get") as mock_get:
            mock_run.return_value = Mock(stdout="Release.Minor.v0.3.0\n", returncode=0)
            mock_get.return_value = Mock(status_code=404)

            status = rollback.analyze_publication_status()
            rollback_type = rollback.determine_rollback_type(status)

            self.assertEqual(rollback_type, "clean")


if __name__ == "__main__":
    # Set up test environment
    os.environ.pop("GITHUB_TOKEN", None)  # Remove token for testing

    # Run tests
    unittest.main(verbosity=2)
