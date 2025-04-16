"""
Common test fixtures for ADRI tests.

This module provides fixtures that can be used across all tests.
"""

import os
import tempfile
import pytest
import pandas as pd
from pathlib import Path

from adri.assessor import DataSourceAssessor
from adri.connectors import BaseConnector
from adri.dimensions import BaseDimensionAssessor


@pytest.fixture
def sample_data_path():
    """Create a temporary CSV file with sample data."""
    with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as temp:
        # Create a sample dataframe
        df = pd.DataFrame({
            'id': [1, 2, 3, 4, 5],
            'name': ['Alice', 'Bob', 'Charlie', 'David', 'Eve'],
            'age': [25, 30, 35, 40, 45],
            'score': [85.5, 90.0, 75.5, 95.0, 80.0]
        })
        
        # Write to the temp file
        df.to_csv(temp.name, index=False)
        
    yield temp.name
    
    # Clean up
    os.unlink(temp.name)


@pytest.fixture
def low_quality_data_path():
    """Create a temporary CSV file with low-quality sample data."""
    with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as temp:
        # Create a sample dataframe with quality issues
        df = pd.DataFrame({
            'id': [1, 2, None, 4, 5],
            'name': ['Alice', None, 'Charlie', 'David', None],
            'age': [250, -30, 35, None, 45],  # Invalid ages
            'score': [None, 90.0, 75.5, 95.0, -80.0]  # Negative score is invalid
        })
        
        # Write to the temp file
        df.to_csv(temp.name, index=False)
        
    yield temp.name
    
    # Clean up
    os.unlink(temp.name)


@pytest.fixture
def mock_connector():
    """Create a mock connector for testing dimensions."""
    class MockConnector(BaseConnector):
        def __init__(self, name="mock_source", data_type="mock"):
            self.name = name
            self.data_type = data_type
            self.metadata = {
                "record_count": 100,
                "field_count": 5,
                "last_updated": "2025-04-15T12:00:00Z"
            }
            
        def get_name(self):
            return self.name
            
        def get_type(self):
            return self.data_type
            
        def get_metadata(self):
            return self.metadata
            
        def get_schema(self):
            return {
                "fields": [
                    {"name": "id", "type": "integer"},
                    {"name": "name", "type": "string"},
                    {"name": "age", "type": "integer"},
                    {"name": "score", "type": "float"}
                ]
            }
            
        def sample_data(self, n=100):
            return [
                {"id": 1, "name": "Alice", "age": 25, "score": 85.5},
                {"id": 2, "name": "Bob", "age": 30, "score": 90.0}
            ][:n]
            
        def get_update_frequency(self):
            return "daily"
            
        def get_last_update_time(self):
            return "2025-04-15T12:00:00Z"
            
        def get_data_size(self):
            return 100
            
        def get_quality_metadata(self):
            return {}
            
        def supports_validation(self):
            return True
            
        def get_validation_results(self):
            return {
                "valid_overall": True,
                "rule_results": [
                    {"rule_name": "age_range", "field": "age", "valid": True}
                ]
            }
            
        def supports_completeness_check(self):
            return True
            
        def get_completeness_results(self):
            return {
                "has_explicit_completeness_info": True,
                "overall_completeness_percent": 98.5,
                "missing_value_markers": ["N/A", "NULL"],
                "completeness_metrics": {"available": True}
            }
            
        def supports_consistency_check(self):
            return True
            
        def get_consistency_results(self):
            return {
                "valid_overall": True,
                "rule_results": [
                    {"rule_name": "age_vs_score", "type": "relationship", "valid": True}
                ],
                "explicitly_communicated": True
            }
            
        def supports_freshness_check(self):
            return True
            
        def get_freshness_results(self):
            return {
                "has_explicit_freshness_info": True,
                "file_modified_time": "2025-04-15T12:00:00Z",
                "file_age_hours": 0.5,
                "max_age_hours": 24,
                "is_fresh": True
            }
            
        def supports_plausibility_check(self):
            return True
            
        def get_plausibility_results(self):
            return {
                "has_explicit_plausibility_info": True,
                "rule_results": [
                    {"rule_name": "age_range", "type": "range", "valid": True}
                ],
                "explicitly_communicated": True
            }
            
        def get_agent_accessibility(self):
            return {"format_machine_readable": True}
            
        def get_data_lineage(self):
            return None
            
        def get_governance_metadata(self):
            return None
    
    return MockConnector()


@pytest.fixture
def assessor():
    """Create a DataSourceAssessor instance."""
    return DataSourceAssessor()
