"""
Tests for the core DataSourceAssessor class.
"""

import os
import pytest
from unittest.mock import patch, MagicMock

from adri.assessor import DataSourceAssessor
from adri.report import ADRIScoreReport
from adri.dimensions import DimensionRegistry


def test_assessor_initialization():
    """Test that DataSourceAssessor initializes correctly."""
    # Create an assessor with default config
    assessor = DataSourceAssessor()
    
    # Check that dimensions are loaded
    assert len(assessor.dimensions) > 0
    
    # Check that all registered dimensions are loaded
    for dim_name in DimensionRegistry.list_dimensions():
        assert dim_name in assessor.dimensions


def test_assessor_initialization_with_config():
    """Test that DataSourceAssessor initializes correctly with custom config."""
    # Create a custom config
    config = {
        "validity": {"weight": 2.0},
        "completeness": {"threshold": 0.9}
    }
    
    # Create an assessor with custom config
    assessor = DataSourceAssessor(config)
    
    # Check that config is stored
    assert assessor.config == config


def test_assessor_initialization_with_dimensions():
    """Test that DataSourceAssessor initializes correctly with specific dimensions."""
    # Create an assessor with specific dimensions
    assessor = DataSourceAssessor(dimensions=["validity", "completeness"])
    
    # Check that only specified dimensions are loaded
    assert len(assessor.dimensions) == 2
    assert "validity" in assessor.dimensions
    assert "completeness" in assessor.dimensions
    assert "freshness" not in assessor.dimensions


def test_assess_file(sample_data_path):
    """Test that assess_file method works correctly."""
    # Create an assessor
    assessor = DataSourceAssessor()
    
    # Assess a file
    report = assessor.assess_file(sample_data_path)
    
    # Check the report
    assert isinstance(report, ADRIScoreReport)
    assert report.source_name == os.path.basename(sample_data_path)
    assert report.source_type == "file-csv"
    assert report.overall_score >= 0
    assert report.dimension_results is not None
    assert len(report.dimension_results) > 0


def test_assess_with_connector():
    """Test that assess_with_connector method works correctly."""
    # Create a mock connector
    connector_class = MagicMock()
    connector_instance = MagicMock()
    
    # Configure the mock to return proper data
    import pandas as pd
    mock_df = pd.DataFrame({
        'col1': [1, 2, 3],
        'col2': ['a', 'b', 'c']
    })
    connector_instance.get_data.return_value = mock_df
    connector_instance.get_metadata.return_value = {"rows": 3, "columns": 2}
    connector_instance.get_name.return_value = "mock_source"
    connector_instance.get_type.return_value = "mock"
    
    # Configure the mock to handle completeness results
    connector_instance.get_completeness_results.return_value = {
        "has_explicit_completeness_info": True,
        "overall_completeness_percent": 100.0
    }
    connector_class.return_value = connector_instance
    
    # Mock the connector registry
    with patch("adri.connectors.ConnectorRegistry.get_connector", return_value=connector_class):
        # Create an assessor
        assessor = DataSourceAssessor()
        
        # Assess with a connector
        report = assessor.assess_with_connector("mock", "arg1", arg2="value")
        
        # Check that the connector was created correctly
        connector_class.assert_called_once_with("arg1", arg2="value")
        
        # Check that assess_source was called
        assert isinstance(report, ADRIScoreReport)


def test_assess_source():
    """Test that assess_source method works correctly."""
    # Create a mock connector with proper data
    import pandas as pd
    mock_connector = MagicMock()
    mock_df = pd.DataFrame({
        'col1': [1, 2, 3],
        'col2': ['a', 'b', 'c']
    })
    mock_connector.get_data.return_value = mock_df
    mock_connector.get_name.return_value = "mock_source"
    mock_connector.get_type.return_value = "mock"
    mock_connector.get_metadata.return_value = {"rows": 3, "columns": 2}
    
    # Create an assessor
    assessor = DataSourceAssessor()
    
    # Assess the source
    report = assessor.assess_source(mock_connector)
    
    # Check the report
    assert isinstance(report, ADRIScoreReport)
    assert report.source_name == "mock_source"
    assert report.source_type == "mock"
    assert report.overall_score >= 0
    assert report.overall_score <= 100
    
    # Check that all dimensions were assessed
    assert len(report.dimension_results) > 0
    for dim_name in report.dimension_results:
        assert "score" in report.dimension_results[dim_name]
        assert "findings" in report.dimension_results[dim_name]
        assert "recommendations" in report.dimension_results[dim_name]


def test_assess_from_config():
    """Test that assess_from_config method works correctly."""
    # Create a temporary config file
    import tempfile
    import yaml
    
    config = {
        "sources": [
            {
                "name": "Sample CSV",
                "type": "file",
                "path": "sample_data.csv"
            }
        ]
    }
    
    with tempfile.NamedTemporaryFile(suffix='.yaml', mode='w', delete=False) as temp:
        yaml.dump(config, temp, default_flow_style=False)
        temp_path = temp.name
    
    # Mock the assess_file method
    mock_report = MagicMock()
    
    with patch.object(DataSourceAssessor, 'assess_file', return_value=mock_report) as mock_assess:
        # Create an assessor
        assessor = DataSourceAssessor()
        
        # Assess from config
        reports = assessor.assess_from_config(temp_path)
        
        # Check that assess_file was called
        mock_assess.assert_called_once()
        
        # Check the reports
        assert isinstance(reports, dict)
        assert "Sample CSV" in reports
        assert reports["Sample CSV"] == mock_report
    
    # Clean up
    import os
    os.unlink(temp_path)
