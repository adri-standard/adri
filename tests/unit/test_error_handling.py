"""
Unit tests for error handling in ADRI guard and certification functionality.

These tests verify proper error handling for various edge cases and failure scenarios.
"""

import os
import json
import unittest
from unittest import mock
from pathlib import Path
import tempfile

from adri import adri_guarded, DataSourceAssessor
from adri.report import ADRIScoreReport


class TestCertificationGuardErrorHandling(unittest.TestCase):
    """Tests for error handling in the certification guard."""

    def setUp(self):
        """Set up test environment."""
        self.test_file_path = "test_data.csv"
        self.report_path = Path("test_data.report.adri_score_report.json")
        
        # Create a mock report
        self.mock_report = {
            "source_name": "test_data.csv",
            "source_type": "file-csv",
            "source_metadata": {"rows": 100, "columns": 5},
            "assessment_time": "2025-05-22T14:30:00.000000",
            "adri_version": "1.0.0",
            "assessment_config": {},
            "overall_score": 80.0,
            "readiness_level": "Advanced - Ready for critical agentic applications",
            "dimension_results": {
                "validity": {"score": 16, "findings": ["Valid finding 1"], "recommendations": []},
                "completeness": {"score": 18, "findings": ["Complete finding"], "recommendations": []},
                "freshness": {"score": 14, "findings": ["Fresh finding"], "recommendations": []},
                "consistency": {"score": 16, "findings": ["Consistent finding"], "recommendations": []},
                "plausibility": {"score": 17, "findings": ["Plausible finding"], "recommendations": []}
            },
            "summary_findings": ["Finding 1", "Finding 2"],
            "summary_recommendations": ["Recommendation 1"]
        }
        
        # Ensure any existing test report is removed
        if self.report_path.exists():
            os.remove(self.report_path)

    def tearDown(self):
        """Clean up after tests."""
        if self.report_path.exists():
            os.remove(self.report_path)
    
    def test_handle_corrupted_report(self):
        """Test handling of corrupted (malformed JSON) report files."""
        # Create an invalid JSON file
        with open(self.report_path, "w") as f:
            f.write("{invalid json content")
        
        # Mock assess_file to track if it gets called
        with mock.patch('adri.assessor.DataSourceAssessor.assess_file') as mock_assess:
            # Create a mock return value for assess_file
            mock_report = mock.MagicMock()
            mock_report.overall_score = 75.0
            mock_assess.return_value = mock_report
            
            # Define a guarded function
            @adri_guarded(min_score=70, use_cached_reports=True, verbose=True)
            def test_func(data_source):
                return f"Processed {data_source}"
            
            # Call the function - it should fall back to fresh assessment despite corrupt report
            result = test_func(self.test_file_path)
            
            # The function should have executed successfully
            self.assertEqual(result, f"Processed {self.test_file_path}")
            
            # Fresh assessment should have been performed
            mock_assess.assert_called_once()
    
    def test_handle_incompatible_report(self):
        """Test handling of incompatible report format (missing required fields)."""
        # Create a report file missing essential fields
        with open(self.report_path, "w") as f:
            json.dump({"source_name": "test_data.csv"}, f)  # Missing most fields
        
        # Mock assess_file to track if it gets called
        with mock.patch('adri.assessor.DataSourceAssessor.assess_file') as mock_assess:
            # Create a mock return value for assess_file
            mock_report = mock.MagicMock()
            mock_report.overall_score = 75.0
            mock_assess.return_value = mock_report
            
            # Define a guarded function
            @adri_guarded(min_score=70, use_cached_reports=True, verbose=True)
            def test_func(data_source):
                return f"Processed {data_source}"
            
            # Call the function - it should fall back to fresh assessment
            result = test_func(self.test_file_path)
            
            # The function should have executed successfully
            self.assertEqual(result, f"Processed {self.test_file_path}")
            
            # Fresh assessment should have been performed
            mock_assess.assert_called_once()
    
    def test_missing_data_source_parameter(self):
        """Test error handling when data source parameter is missing."""
        with mock.patch('adri.assessor.DataSourceAssessor.assess_file') as mock_assess:
            # Create a mock return value for assess_file
            mock_report = mock.MagicMock()
            mock_report.overall_score = 75.0
            mock_assess.return_value = mock_report
            
            # Define a guarded function with a parameter name that doesn't match
            @adri_guarded(min_score=70, data_source_param="source_path")
            def test_func(data_source):
                return f"Processed {data_source}"
            
            # Call the function with a parameter that doesn't match the expected name
            with self.assertRaises(ValueError) as context:
                test_func(self.test_file_path)
            
            # Check that the error message mentions the missing parameter
            self.assertIn("source_path", str(context.exception))
            
            # Test with kwargs instead, which is more reliable for testing
            @adri_guarded(min_score=70, data_source_param="source_path")
            def test_func2(regular_param, source_path):
                return f"Processed {source_path}"
            
            # This should work when we provide the expected named parameter
            result = test_func2(regular_param="dummy", source_path=self.test_file_path)
            self.assertEqual(result, f"Processed {self.test_file_path}")
            
            # But this should fail because we don't provide the expected parameter name
            with self.assertRaises(ValueError):
                test_func2(regular_param="dummy", wrong_param=self.test_file_path)
    
    def test_save_failure_handling(self):
        """Test graceful handling of report save failures."""
        # Create a mock for AssessmentReport with a save_json method that raises an exception
        mock_report = mock.MagicMock()
        mock_report.overall_score = 75.0
        mock_report.save_json.side_effect = PermissionError("Permission denied")
        
        with mock.patch('adri.assessor.DataSourceAssessor.assess_file', return_value=mock_report):
            # Define a guarded function
            @adri_guarded(min_score=70, save_reports=True, verbose=True)
            def test_func(data_source):
                return f"Processed {data_source}"
            
            # Call the function - it should succeed despite save failure
            result = test_func(self.test_file_path)
            
            # The function should have executed successfully despite save error
            self.assertEqual(result, f"Processed {self.test_file_path}")
            
            # Verify save was attempted
            mock_report.save_json.assert_called_once()
    
    def test_multiple_dimension_requirements(self):
        """Test handling of multiple dimension requirements."""
        # Create a report with mixed dimension scores
        report_data = self.mock_report.copy()
        report_data["dimension_results"]["validity"]["score"] = 18  # Pass
        report_data["dimension_results"]["completeness"]["score"] = 8  # Fail
        report_data["dimension_results"]["freshness"]["score"] = 16  # Pass
        
        with open(self.report_path, "w") as f:
            json.dump(report_data, f)
        
        # Define a guarded function with multiple dimension requirements
        @adri_guarded(
            min_score=70,
            dimensions={
                "validity": 15,
                "completeness": 15,  # This one will fail
                "freshness": 15
            },
            use_cached_reports=True
        )
        def test_func(data_source):
            return f"Processed {data_source}"
        
        # Call the function and expect failure due to completeness
        try:
            test_func(self.test_file_path)
            self.fail("Expected ValueError was not raised")
        except ValueError as e:
            # Verify the error message mentions completeness specifically
            self.assertIn("completeness", str(e).lower())
            self.assertIn("8/20", str(e))  # Should show the actual score
            self.assertIn("15/20", str(e))  # Should show the required score
    
    def test_missing_dimension_handling(self):
        """Test handling of missing dimensions in requirements."""
        # Create a report missing a dimension
        report_data = self.mock_report.copy()
        del report_data["dimension_results"]["plausibility"]  # Remove plausibility
        
        with open(self.report_path, "w") as f:
            json.dump(report_data, f)
        
        # Define a guarded function requiring the missing dimension
        @adri_guarded(
            min_score=70,
            dimensions={"plausibility": 15},  # This dimension is missing
            use_cached_reports=True
        )
        def test_func(data_source):
            return f"Processed {data_source}"
        
        # Call the function and expect failure due to missing dimension
        with self.assertRaises(ValueError) as context:
            test_func(self.test_file_path)
        
        # Check that the error message mentions the missing dimension
        self.assertIn("plausibility", str(context.exception).lower())
        self.assertIn("not found", str(context.exception).lower())


if __name__ == '__main__':
    unittest.main()
