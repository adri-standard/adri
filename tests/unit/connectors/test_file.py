"""
Tests for the file connector.
"""

import os
import pytest
import pandas as pd
from pathlib import Path

from adri.connectors import ConnectorRegistry
from adri.connectors.file import FileConnector


def test_file_connector_registration():
    """Test that FileConnector is properly registered."""
    assert "file" in ConnectorRegistry.list_connectors()
    connector_class = ConnectorRegistry.get_connector("file")
    assert connector_class == FileConnector


def test_file_connector_initialization(sample_data_path):
    """Test that FileConnector initializes correctly."""
    # Create a connector
    connector = FileConnector(sample_data_path)
    
    # Check basic properties
    assert connector.get_name() == Path(sample_data_path).name
    assert connector.get_type() == "file-csv"
    assert isinstance(connector.df, pd.DataFrame)
    assert len(connector.df) > 0


def test_file_connector_metadata(sample_data_path):
    """Test that FileConnector provides correct metadata."""
    # Create a connector
    connector = FileConnector(sample_data_path)
    
    # Get metadata
    metadata = connector.get_metadata()
    
    # Check metadata
    assert "file_path" in metadata
    assert "file_type" in metadata
    assert "file_size_bytes" in metadata
    assert "created_time" in metadata
    assert "modified_time" in metadata
    assert "num_records" in metadata
    assert "num_columns" in metadata
    assert metadata["num_records"] == 5
    assert metadata["num_columns"] == 4


def test_file_connector_schema(sample_data_path):
    """Test that FileConnector provides correct schema."""
    # Create a connector
    connector = FileConnector(sample_data_path)
    
    # Get schema
    schema = connector.get_schema()
    
    # Check schema
    assert "fields" in schema
    assert len(schema["fields"]) == 4
    
    # Check field properties
    for field in schema["fields"]:
        assert "name" in field
        assert "type" in field
        assert "nullable" in field
        assert "unique_values" in field


def test_file_connector_sample_data(sample_data_path):
    """Test that FileConnector provides sample data."""
    # Create a connector
    connector = FileConnector(sample_data_path)
    
    # Get sample data
    sample = connector.sample_data(n=2)
    
    # Check sample
    assert isinstance(sample, list)
    assert len(sample) == 2
    assert isinstance(sample[0], dict)
    assert "id" in sample[0]
    assert "name" in sample[0]
    assert "age" in sample[0]
    assert "score" in sample[0]


def test_file_connector_completeness_results(sample_data_path):
    """Test that FileConnector provides completeness results."""
    # Create a connector
    connector = FileConnector(sample_data_path)
    
    # Get completeness results
    results = connector.get_completeness_results()
    
    # Check results
    assert isinstance(results, dict)
    assert "has_explicit_completeness_info" in results
    assert "overall_completeness_percent" in results
    assert results["overall_completeness_percent"] == 100.0  # Sample data is complete


def test_file_connector_freshness_results(sample_data_path):
    """Test that FileConnector provides freshness results."""
    # Create a connector
    connector = FileConnector(sample_data_path)
    
    # Get freshness results
    results = connector.get_freshness_results()
    
    # Check results
    assert isinstance(results, dict)
    assert "has_explicit_freshness_info" in results
    assert "file_modified_time" in results
    assert "file_age_hours" in results


def test_file_connector_with_low_quality_data(low_quality_data_path):
    """Test FileConnector with low-quality data."""
    # Create a connector
    connector = FileConnector(low_quality_data_path)
    
    # Get completeness results
    results = connector.get_completeness_results()
    
    # Check results
    assert results["overall_completeness_percent"] < 100.0  # Should have missing values
    
    # Check quality metadata
    quality_metadata = connector.get_quality_metadata()
    assert "missing_values" in quality_metadata
    assert "missing_values_percent" in quality_metadata
    assert len(quality_metadata["missing_values"]) > 0


def test_file_connector_agent_accessibility(sample_data_path):
    """Test that FileConnector provides agent accessibility information."""
    # Create a connector
    connector = FileConnector(sample_data_path)
    
    # Get agent accessibility
    accessibility = connector.get_agent_accessibility()
    
    # Check accessibility
    assert isinstance(accessibility, dict)
    assert "format_machine_readable" in accessibility
    assert accessibility["format_machine_readable"] is True
