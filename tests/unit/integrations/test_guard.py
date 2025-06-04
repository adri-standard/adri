"""
Tests for the ADRI guard decorator.
"""

import pytest
from unittest.mock import patch, MagicMock

from adri.integrations import adri_guarded


def test_guard_decorator_with_good_data(sample_data_path):
    """Test that the guard decorator allows functions to run with good data."""
    # Create a decorated function
    @adri_guarded(min_score=0)  # Set min_score to 0 to ensure it passes
    def process_data(data_source):
        return f"Processed {data_source}"
    
    # Call the function with good data
    result = process_data(sample_data_path)
    
    # Check the result
    assert result == f"Processed {sample_data_path}"


def test_guard_decorator_blocks_low_quality_data(low_quality_data_path):
    """Test that the guard decorator blocks functions with low-quality data."""
    # Create a decorated function
    @adri_guarded(min_score=80)  # Set min_score high to ensure it fails
    def process_data(data_source):
        return f"Processed {data_source}"
    
    # Call the function with low-quality data
    with pytest.raises(ValueError) as excinfo:
        process_data(low_quality_data_path)
    
    # Check the error message
    assert "Data quality insufficient" in str(excinfo.value)
    assert "ADRI Score:" in str(excinfo.value)


def test_guard_decorator_with_custom_parameter_name(sample_data_path):
    """Test that the guard decorator works with custom parameter names."""
    # Create a decorated function with a custom parameter name
    @adri_guarded(min_score=0, data_source_param="file_path")
    def process_file(file_path):
        return f"Processed {file_path}"
    
    # Call the function
    result = process_file(file_path=sample_data_path)
    
    # Check the result
    assert result == f"Processed {sample_data_path}"


def test_guard_decorator_with_positional_args(sample_data_path):
    """Test that the guard decorator works with positional arguments."""
    # Create a decorated function with multiple parameters
    @adri_guarded(min_score=0)
    def process_data(data_source, option="default"):
        return f"Processed {data_source} with option {option}"
    
    # Call the function with positional arguments
    result = process_data(sample_data_path, "custom")
    
    # Check the result
    assert result == f"Processed {sample_data_path} with option custom"


def test_guard_decorator_with_keyword_args(sample_data_path):
    """Test that the guard decorator works with keyword arguments."""
    # Create a decorated function with multiple parameters
    @adri_guarded(min_score=0)
    def process_data(data_source, option="default"):
        return f"Processed {data_source} with option {option}"
    
    # Call the function with keyword arguments
    result = process_data(data_source=sample_data_path, option="custom")
    
    # Check the result
    assert result == f"Processed {sample_data_path} with option custom"


def test_guard_decorator_missing_parameter():
    """Test that the guard decorator raises an error when the data source parameter is missing."""
    # Create a decorated function
    @adri_guarded(min_score=0)
    def process_data(data_source):
        return f"Processed {data_source}"
    
    # Call the function without the required parameter
    with pytest.raises(ValueError) as excinfo:
        process_data()  # Missing required parameter
    
    # Check the error message
    assert "Could not find data source parameter" in str(excinfo.value)


def test_guard_decorator_with_mocked_assessor():
    """Test the guard decorator with a mocked assessor."""
    # Create a mock report
    mock_report = MagicMock()
    mock_report.overall_score = 90
    mock_report.summary_findings = ["Finding 1", "Finding 2"]
    
    # Create a mock assessor
    mock_assessor = MagicMock()
    mock_assessor.assess_file.return_value = mock_report
    
    # Patch the DataSourceAssessor
    with patch("adri.integrations.guard.DataSourceAssessor", return_value=mock_assessor):
        # Create a decorated function
        @adri_guarded(min_score=80)
        def process_data(data_source):
            return f"Processed {data_source}"
        
        # Call the function
        result = process_data("dummy_path")
        
        # Check the result
        assert result == "Processed dummy_path"
        mock_assessor.assess_file.assert_called_once_with("dummy_path")


def test_guard_decorator_with_mocked_assessor_failing():
    """Test the guard decorator with a mocked assessor that fails."""
    # Create a mock report
    mock_report = MagicMock()
    mock_report.overall_score = 50
    mock_report.summary_findings = ["Finding 1", "Finding 2"]
    
    # Create a mock assessor
    mock_assessor = MagicMock()
    mock_assessor.assess_file.return_value = mock_report
    
    # Patch the DataSourceAssessor
    with patch("adri.integrations.guard.DataSourceAssessor", return_value=mock_assessor):
        # Create a decorated function
        @adri_guarded(min_score=80)
        def process_data(data_source):
            return f"Processed {data_source}"
        
        # Call the function
        with pytest.raises(ValueError) as excinfo:
            process_data("dummy_path")
        
        # Check the error message
        assert "Data quality insufficient" in str(excinfo.value)
        assert "50" in str(excinfo.value)
        assert "80" in str(excinfo.value)
        mock_assessor.assess_file.assert_called_once_with("dummy_path")
