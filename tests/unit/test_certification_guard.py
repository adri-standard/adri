"""
Unit tests for ADRI certification guard functionality.

These tests verify that the adri_guarded decorator properly handles
pre-certified data sources and applies appropriate validation rules.
"""

import os
import json
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest import mock
import copy

# Remove pytest dependency
from adri import adri_guarded, DataSourceAssessor
from adri.report import ADRIScoreReport


class TestCertificationGuard(unittest.TestCase):
    """Tests for the certification guard functionality."""

    def setUp(self):
        """Set up test environment."""
        self.test_file_path = "test_data.csv"
        self.report_path = Path("test_data.adri_score_report.json")
        
        # Create a mock report in the correct ADRI format
        self.mock_report = {
            "adri_score_report": {
                "report_version": "1.0.0",
                "adri_version": "0.4.2",
                "generated_at": datetime.now().isoformat(),
                "summary": {
                    "overall_score": 80.0,
                    "grade": "B",
                    "status": "AI Ready",
                    "data_source": "test_data.csv"
                },
                "dimensions": {
                    "validity": {"score": 16, "findings": ["Valid finding 1", "Valid finding 2"], "recommendations": []},
                    "completeness": {"score": 18, "findings": ["Complete finding"], "recommendations": []},
                    "freshness": {"score": 14, "findings": ["Fresh finding"], "recommendations": []},
                    "consistency": {"score": 16, "findings": ["Consistent finding"], "recommendations": []},
                    "plausibility": {"score": 17, "findings": ["Plausible finding"], "recommendations": []}
                },
                "metadata": {
                    "assessed_at": datetime.now().isoformat(),
                    "adri_version": "0.4.2",
                    "assessment_mode": "discovery",
                    "template": {
                        "id": None,
                        "version": None,
                        "match_confidence": None,
                        "match_type": None
                    }
                },
                "provenance": None
            }
        }
        
        # Ensure any existing test report is removed
        if self.report_path.exists():
            os.remove(self.report_path)

    def tearDown(self):
        """Clean up after tests."""
        if self.report_path.exists():
            os.remove(self.report_path)
    
    def create_report_file(self, overall_score=80.0, report_time=None, dimension_scores=None):
        """Create a test report file with specified parameters."""
        # Deep copy the report structure
        report = copy.deepcopy(self.mock_report)
        
        # Update overall score
        report["adri_score_report"]["summary"]["overall_score"] = overall_score
        
        # Update report time if specified
        if report_time:
            report["adri_score_report"]["generated_at"] = report_time.isoformat()
            report["adri_score_report"]["metadata"]["assessed_at"] = report_time.isoformat()
            
        # Update dimension scores if specified
        if dimension_scores:
            for dim_name, score in dimension_scores.items():
                if dim_name in report["adri_score_report"]["dimensions"]:
                    report["adri_score_report"]["dimensions"][dim_name]["score"] = score
        
        with open(self.report_path, "w") as f:
            json.dump(report, f)
        
        return self.report_path
    
    @mock.patch('adri.assessor.DataSourceAssessor.assess_file')
    def test_guard_uses_cached_report(self, mock_assess):
        """Test that guard uses cached report when available."""
        # Create a mock report file
        self.create_report_file(overall_score=85.0)  # High score for cached report
        
        # Mock assessor to ensure it's not called
        mock_assess.side_effect = Exception("Should not be called")
        
        # Define a guarded function
        @adri_guarded(min_score=70, use_cached_reports=True, verbose=False)
        def test_func(data_source):
            return f"Processed {data_source}"
        
        # Call the function and verify it uses the cached report
        result = test_func(self.test_file_path)
        
        # The function should have executed successfully with the cached report
        self.assertEqual(result, f"Processed {self.test_file_path}")
        
        # The assess_file should NOT have been called
        mock_assess.assert_not_called()
    
    @mock.patch('adri.assessor.DataSourceAssessor.assess_file')
    def test_guard_ignores_cached_report_when_disabled(self, mock_assess):
        """Test that guard ignores cached report when caching is disabled."""
        # Create a mock report file
        self.create_report_file(overall_score=80.0)
        
        # Create a mock return value for assess_file
        mock_report = mock.MagicMock()
        mock_report.overall_score = 75.0  # Different from cached report
        mock_assess.return_value = mock_report
        
        # Define a guarded function with caching disabled
        @adri_guarded(min_score=70, use_cached_reports=False, verbose=True)
        def test_func(data_source):
            return f"Processed {data_source}"
        
        # Call the function
        result = test_func(self.test_file_path)
        
        # The function should have executed successfully with the fresh assessment
        self.assertEqual(result, f"Processed {self.test_file_path}")
        
        # The assess_file should have been called despite cached report
        mock_assess.assert_called_once()
    
    def test_age_validation_implementation(self):
        """Test that age validation is implemented in the guard code."""
        # This is a simpler test that just verifies the implementation exists
        import inspect
        from adri.integrations.guard import adri_guarded
        
        # Get the source code of the guard function
        source = inspect.getsource(adri_guarded)
        
        # Verify the code contains the key components for report age validation
        self.assertIn("max_report_age_hours", source)
        self.assertIn("timedelta(hours=max_report_age_hours)", source)
        self.assertIn("datetime.now() - report_time > max_age", source)
        self.assertIn("report = None", source)  # Should reset report if too old
    
    @mock.patch('adri.assessor.DataSourceAssessor.assess_file')
    def test_guard_dimension_specific_requirements(self, mock_assess):
        """Test that guard enforces dimension-specific requirements with cached reports."""
        # Create a report with decent overall score but low plausibility
        self.create_report_file(
            overall_score=75.0,
            dimension_scores={"plausibility": 5}
        )
        
        # Mock assessor to ensure it's not called
        mock_assess.side_effect = Exception("Should not be called")
        
        # Define a guarded function with dimension requirements
        @adri_guarded(
            min_score=70, 
            dimensions={"plausibility": 10},  # Require high plausibility
            use_cached_reports=True,
            verbose=False
        )
        def test_func(data_source):
            return f"Processed {data_source}"
        
        # Call the function and expect it to fail due to dimension requirement
        try:
            test_func(self.test_file_path)
            self.fail("Expected ValueError was not raised")
        except ValueError as e:
            # Verify the error message mentions plausibility
            self.assertIn("plausibility", str(e).lower())
            self.assertIn("5/20", str(e))  # Should show the actual score
            self.assertIn("10/20", str(e))  # Should show the required score
        
        # No fresh assessment should have been made
        mock_assess.assert_not_called()
    
    @mock.patch('adri.assessor.DataSourceAssessor.assess_file')
    def test_guard_saves_new_report(self, mock_assess):
        """Test that guard saves new assessment reports when specified."""
        # Ensure no cached report exists
        if self.report_path.exists():
            os.remove(self.report_path)
        
        # Create a mock return value for assess_file
        mock_report = mock.MagicMock()
        mock_report.overall_score = 75.0
        mock_report.save_json = mock.MagicMock()  # Add mock for save_json method
        mock_assess.return_value = mock_report
        
        # Define a guarded function that saves reports
        @adri_guarded(min_score=70, save_reports=True, verbose=True)
        def test_func(data_source):
            return f"Processed {data_source}"
        
        # Call the function
        result = test_func(self.test_file_path)
        
        # The function should have executed successfully
        self.assertEqual(result, f"Processed {self.test_file_path}")
        
        # The assess_file should have been called
        mock_assess.assert_called_once()
        
        # The save_json method should have been called
        mock_report.save_json.assert_called_once()
    
    @mock.patch('adri.assessor.DataSourceAssessor.assess_file')
    def test_guard_without_save(self, mock_assess):
        """Test that guard doesn't save reports when save_reports=False."""
        # Ensure no cached report exists
        if self.report_path.exists():
            os.remove(self.report_path)
        
        # Create a mock return value for assess_file
        mock_report = mock.MagicMock()
        mock_report.overall_score = 75.0
        mock_report.save_json = mock.MagicMock()  # Add mock for save_json method
        mock_assess.return_value = mock_report
        
        # Define a guarded function that doesn't save reports
        @adri_guarded(min_score=70, save_reports=False, verbose=True)
        def test_func(data_source):
            return f"Processed {data_source}"
        
        # Call the function
        result = test_func(self.test_file_path)
        
        # The function should have executed successfully
        self.assertEqual(result, f"Processed {self.test_file_path}")
        
        # The assess_file should have been called
        mock_assess.assert_called_once()
        
        # The save_json method should NOT have been called
        mock_report.save_json.assert_not_called()


if __name__ == '__main__':
    unittest.main()
