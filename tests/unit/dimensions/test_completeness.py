"""
Tests for the completeness dimension assessor.
"""

import pytest
from unittest.mock import MagicMock, patch

from adri.dimensions import DimensionRegistry
from adri.dimensions.completeness import CompletenessAssessor


def test_completeness_registration():
    """Test that CompletenessAssessor is properly registered."""
    assert "completeness" in DimensionRegistry.list_dimensions()
    dimension_class = DimensionRegistry.get_dimension("completeness")
    assert dimension_class == CompletenessAssessor


def test_completeness_assessment_with_good_data(mock_connector):
    """Test completeness assessment with good data."""
    # Create the assessor
    assessor = CompletenessAssessor()
    
    # Run the assessment
    score, findings, recommendations = assessor.assess(mock_connector)
    
    # Check the results
    assert 0 <= score <= 20
    assert isinstance(findings, list)
    assert isinstance(recommendations, list)
    assert score > 0  # Should have a positive score with good data
    
    # Check that the findings include the completeness percentage
    completeness_finding = next((f for f in findings if "completeness" in f.lower()), None)
    assert completeness_finding is not None


def test_completeness_assessment_with_no_data():
    """Test completeness assessment with no completeness data."""
    # Create a mock connector with no completeness data
    connector = MagicMock()
    connector.get_name.return_value = "test_connector"
    connector.get_completeness_results.return_value = None
    
    # Create the assessor
    assessor = CompletenessAssessor()
    
    # Run the assessment
    score, findings, recommendations = assessor.assess(connector)
    
    # Check the results
    assert score == 0  # Should have zero score with no data
    assert "No completeness information is available" in findings
    assert len(recommendations) > 0  # Should have recommendations for improvement


def test_completeness_assessment_with_partial_data():
    """Test completeness assessment with partial completeness data."""
    # Create a mock connector with partial completeness data
    connector = MagicMock()
    connector.get_name.return_value = "test_connector"
    connector.get_completeness_results.return_value = {
        "has_explicit_completeness_info": False,
        "overall_completeness_percent": 75.0
    }
    
    # Create the assessor
    assessor = CompletenessAssessor()
    
    # Run the assessment
    score, findings, recommendations = assessor.assess(connector)
    
    # Check the results
    assert 0 < score < 20  # Should have a partial score
    assert any("75.0%" in f for f in findings)
    assert any("explicit" in r.lower() for r in recommendations)


def test_completeness_assessment_with_full_data():
    """Test completeness assessment with full completeness data."""
    # Create a mock connector with full completeness data
    connector = MagicMock()
    connector.get_name.return_value = "test_connector"
    connector.get_completeness_results.return_value = {
        "has_explicit_completeness_info": True,
        "overall_completeness_percent": 98.5,
        "missing_value_markers": ["N/A", "NULL"],
        "completeness_metrics": {"available": True},
        "section_completeness": {
            "section1": 99.0,
            "section2": 97.5
        }
    }
    
    # Create the assessor
    assessor = CompletenessAssessor()
    
    # Run the assessment
    score, findings, recommendations = assessor.assess(connector)
    
    # Check the results
    assert score == 20  # Should have maximum score with full data
    assert any("98.5%" in f for f in findings)
    assert any("explicit" in f.lower() for f in findings)
    assert any("section" in f.lower() for f in findings)
    assert len(recommendations) == 0  # Should have no recommendations with perfect score
