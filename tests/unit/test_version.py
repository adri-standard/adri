"""
Unit tests for the version management functionality.

This module tests the version tracking, compatibility checking, and
version-related functionality in reports.
"""

import unittest
import warnings
from datetime import datetime
from unittest.mock import patch

from adri.version import (
    __version__,
    __min_compatible_version__,
    __score_compatible_versions__,
    is_version_compatible,
    get_score_compatibility_message
)
from adri.report import AssessmentReport


class TestVersionManagement(unittest.TestCase):
    """Test cases for version management functionality."""

    def test_version_constants(self):
        """Test that version constants exist and have correct format."""
        # Check that version follows semver format
        version_parts = __version__.split('.')
        self.assertEqual(len(version_parts), 3, "Version should have three parts (MAJOR.MINOR.PATCH)")
        
        # Check that each part is a number
        for part in version_parts:
            self.assertTrue(part.isdigit(), f"Version part '{part}' should be a number")
        
        # Check min compatible version
        self.assertIsNotNone(__min_compatible_version__, "Min compatible version should be defined")
        
        # Check score compatible versions list
        self.assertIsInstance(__score_compatible_versions__, list, "Score compatible versions should be a list")
        self.assertIn(__version__, __score_compatible_versions__, 
                      "Current version should be in score compatible versions list")

    def test_version_compatibility_checking(self):
        """Test the version compatibility checking function."""
        # Current version should be compatible with itself
        self.assertTrue(is_version_compatible(__version__))
        
        # Same major version should be compatible
        major = __version__.split('.')[0]
        minor_patch_variants = ["0", "1", "99"]
        
        for minor in minor_patch_variants:
            for patch in minor_patch_variants:
                version = f"{major}.{minor}.{patch}"
                self.assertTrue(is_version_compatible(version), 
                                f"Version {version} should be compatible with {__version__}")
        
        # Different major version should not be compatible
        if int(major) > 0:
            smaller_major = str(int(major) - 1)
            self.assertFalse(is_version_compatible(f"{smaller_major}.0.0"),
                             "Smaller major version should not be compatible")
        
        larger_major = str(int(major) + 1)
        self.assertFalse(is_version_compatible(f"{larger_major}.0.0"),
                         "Larger major version should not be compatible")
        
        # Explicitly marked compatible versions should be compatible
        for version in __score_compatible_versions__:
            self.assertTrue(is_version_compatible(version),
                           f"Version {version} in score_compatible_versions should be compatible")

    def test_compatibility_message(self):
        """Test the compatibility message function."""
        # Message for current version
        current_message = get_score_compatibility_message(__version__)
        self.assertIn("fully compatible", current_message, 
                      "Current version should be fully compatible")
        
        # Message for explicitly compatible version
        for version in __score_compatible_versions__:
            message = get_score_compatibility_message(version)
            self.assertIn("fully compatible", message, 
                          f"Compatible version {version} should be fully compatible")
        
        # Message for incompatible version
        major = int(__version__.split('.')[0])
        incompatible_version = f"{major + 1}.0.0"
        message = get_score_compatibility_message(incompatible_version)
        self.assertIn("incompatible", message, 
                      f"Version {incompatible_version} should be incompatible")

    def test_report_version_embedding(self):
        """Test that reports embed version information correctly."""
        # Create a report with default version (current version)
        report = AssessmentReport(
            source_name="Test Source",
            source_type="test",
            source_metadata={}
        )
        
        # Check that version was embedded
        self.assertEqual(report.adri_version, __version__, 
                         "Report should embed current version by default")
        
        # Check that version appears in dictionary representation
        report_dict = report.to_dict()
        self.assertEqual(report_dict["adri_version"], __version__,
                         "Version should be included in report dictionary")

    def test_report_version_loading(self):
        """Test report loading with version compatibility checks."""
        # Create a test report with incompatible version
        report_data = {
            "source_name": "Test Source",
            "source_type": "test",
            "source_metadata": {},
            "assessment_time": datetime.now().isoformat(),
            "adri_version": "99.0.0",  # Incompatible version
            "overall_score": 75,
            "readiness_level": "Proficient",
            "dimension_results": {},
            "summary_findings": [],
            "summary_recommendations": []
        }
        
        # Check that loading with incompatible version raises warning
        with warnings.catch_warnings(record=True) as recorded_warnings:
            # Ensure warnings are always triggered
            warnings.simplefilter("always")
            
            # Patch open and json.load to return our test data
            with patch("builtins.open"), patch("json.load", return_value=report_data):
                report = AssessmentReport.load_json("fake_path.json")
                
                # Check that a warning was raised
                self.assertTrue(len(recorded_warnings) > 0, 
                              "Loading incompatible version should raise warning")
                
                # Check warning message
                warning_message = str(recorded_warnings[0].message)
                self.assertIn("incompatible version", warning_message.lower(),
                             "Warning should mention incompatible version")
                
                # Check report still loaded
                self.assertEqual(report.adri_version, "99.0.0",
                                "Report should still load with original version")


if __name__ == "__main__":
    unittest.main()
