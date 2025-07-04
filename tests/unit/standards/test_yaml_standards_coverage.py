"""
Tests to improve coverage for adri.standards.yaml_standards module.

These tests target specific uncovered lines to reach 100% coverage.
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, mock_open
from adri.standards.yaml_standards import YAMLStandards


class TestYAMLStandardsCoverage:
    """Tests targeting specific uncovered lines in yaml_standards.py."""

    def test_load_standard_exception_handling(self):
        """Test the exception handling in load_standard method (line 46)."""
        yaml_standards = YAMLStandards()
        
        # Mock the loader to raise an exception
        with patch.object(yaml_standards.loader, 'load_standard', side_effect=Exception("Test exception")):
            result = yaml_standards.load_standard("test_standard")
            # Should return None when exception occurs (line 46)
            assert result is None

    def test_load_from_file_with_project_root_fallback(self):
        """Test load_from_file with project root fallback logic (line 46)."""
        yaml_standards = YAMLStandards()
        
        # Create a temporary file structure without pyproject.toml to trigger fallback
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create a standard file in the temp directory
            standard_file = temp_path / "test_standard.yaml"
            standard_content = """
standards:
  id: test_standard
  version: "1.0"
requirements:
  overall_minimum: 80.0
"""
            standard_file.write_text(standard_content)
            
            # Mock Path.cwd() to return our temp directory (this triggers line 46)
            with patch('pathlib.Path.cwd', return_value=temp_path):
                # Mock __file__ to be in a directory structure without pyproject.toml
                with patch('adri.standards.yaml_standards.__file__', str(temp_path / "fake_module.py")):
                    # This should trigger the fallback to Path.cwd() (line 46)
                    yaml_standards.load_from_file("test_standard.yaml")
                    assert yaml_standards.standard_data is not None
                    assert yaml_standards.standard_data["standards"]["id"] == "test_standard"

    def test_load_from_file_file_not_found_error(self):
        """Test load_from_file when file is not found anywhere."""
        yaml_standards = YAMLStandards()
        
        with pytest.raises(ValueError, match="Failed to load standard"):
            yaml_standards.load_from_file("nonexistent_file.yaml")

    def test_load_from_file_yaml_parsing_error(self):
        """Test load_from_file with invalid YAML content."""
        yaml_standards = YAMLStandards()
        
        # Create a temporary file with invalid YAML
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: content: [unclosed")
            temp_file = f.name
        
        try:
            with pytest.raises(ValueError, match="Failed to load standard"):
                yaml_standards.load_from_file(temp_file)
        finally:
            os.unlink(temp_file)

    def test_check_compliance_with_dimension_score_dict(self):
        """Test check_compliance when dimension scores are dictionaries."""
        standard_content = {
            "standards": {"id": "test"},
            "requirements": {
                "overall_minimum": 75.0,
                "dimension_requirements": {
                    "validity": 80.0,
                    "completeness": 85.0
                }
            }
        }
        
        yaml_standards = YAMLStandards()
        yaml_standards.standard_data = standard_content
        
        # Test with dimension scores as dictionaries
        report_data = {
            "overall_score": 90.0,
            "dimension_scores": {
                "validity": {"score": 85.0, "details": "good"},
                "completeness": {"score": 90.0, "details": "excellent"}
            }
        }
        
        result = yaml_standards.check_compliance(report_data)
        assert result["compliant"] is True
        assert result["overall_compliance"] is True

    def test_check_compliance_with_failing_dimension_scores(self):
        """Test check_compliance with failing dimension scores."""
        standard_content = {
            "standards": {"id": "test"},
            "requirements": {
                "overall_minimum": 75.0,
                "dimension_requirements": {
                    "validity": 80.0,
                    "completeness": 85.0
                }
            }
        }
        
        yaml_standards = YAMLStandards()
        yaml_standards.standard_data = standard_content
        
        # Test with failing dimension scores
        report_data = {
            "overall_score": 90.0,
            "dimension_scores": {
                "validity": 70.0,  # Below minimum of 80
                "completeness": 80.0  # Below minimum of 85
            }
        }
        
        result = yaml_standards.check_compliance(report_data)
        assert result["compliant"] is False
        assert result["overall_compliance"] is False
        assert len(result["errors"]) == 2
        assert "validity score 70.0 below minimum 80.0" in result["errors"][0]
        assert "completeness score 80.0 below minimum 85.0" in result["errors"][1]

    def test_check_compliance_with_missing_required_fields(self):
        """Test check_compliance with missing required fields."""
        standard_content = {
            "standards": {"id": "test"},
            "requirements": {
                "overall_minimum": 75.0,
                "required_fields": ["field1", "field2", "field3"]
            }
        }
        
        yaml_standards = YAMLStandards()
        yaml_standards.standard_data = standard_content
        
        # Test with missing required fields
        report_data = {
            "overall_score": 90.0,
            "field1": "present",
            # field2 and field3 are missing
        }
        
        result = yaml_standards.check_compliance(report_data)
        assert result["compliant"] is False
        assert result["overall_compliance"] is False
        assert len(result["errors"]) == 2
        assert "Missing required field: field2" in result["errors"]
        assert "Missing required field: field3" in result["errors"]

    def test_validate_standard_with_missing_fields(self):
        """Test validate_standard with missing required fields."""
        yaml_standards = YAMLStandards()
        
        # Test with missing required fields
        incomplete_standard = {
            "standard_id": "test",
            # Missing "version" and "description"
        }
        
        result = yaml_standards.validate_standard(incomplete_standard)
        assert result is False
        
        # Test with all required fields
        complete_standard = {
            "standard_id": "test",
            "version": "1.0",
            "description": "Test standard"
        }
        
        result = yaml_standards.validate_standard(complete_standard)
        assert result is True

    def test_methods_with_no_standard_data(self):
        """Test various methods when no standard data is loaded."""
        yaml_standards = YAMLStandards()
        
        # Test methods with no standard data
        assert yaml_standards.get_field_requirements() == {}
        assert yaml_standards.get_overall_minimum() == 75.0
        assert yaml_standards.standards_id == "unknown"
        
        # Test compliance check with no standard data
        result = yaml_standards.check_compliance({"test": "data"})
        assert result["compliant"] is False
        assert result["overall_compliance"] is False
        assert "No standard loaded" in result["errors"][0]
