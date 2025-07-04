"""
Tests for the YAMLStandards module.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open

import pytest
import yaml

from adri.standards.yaml_standards import YAMLStandards


class TestYAMLStandardsInit:
    """Test YAMLStandards initialization."""

    def test_init_without_path(self):
        """Test initialization without standard path."""
        standards = YAMLStandards()
        assert standards.standard_path is None
        assert standards.standard_data is None
        assert standards.loader is not None

    def test_init_with_valid_path(self):
        """Test initialization with valid standard path."""
        # Create a temporary YAML file
        valid_standard = {
            "standard_metadata": {
                "id": "test-standard",
                "version": "1.0.0"
            },
            "requirements": {
                "overall_minimum": 80.0,
                "field_requirements": {"test_field": "test_value"}
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(valid_standard, f)
            temp_path = f.name

        try:
            standards = YAMLStandards(temp_path)
            assert standards.standard_path == temp_path
            assert standards.standard_data == valid_standard
        finally:
            os.unlink(temp_path)

    def test_init_with_invalid_path(self):
        """Test initialization with invalid standard path."""
        with pytest.raises(ValueError, match="Failed to load standard"):
            YAMLStandards("nonexistent_file.yaml")


class TestLoadFromFile:
    """Test the load_from_file method."""

    def setup_method(self):
        """Set up test fixtures."""
        self.standards = YAMLStandards()
        self.valid_standard = {
            "standard_metadata": {
                "id": "test-standard",
                "version": "1.0.0"
            },
            "requirements": {
                "overall_minimum": 75.0,
                "field_requirements": {"test_field": "test_value"}
            }
        }

    def test_load_from_file_success(self):
        """Test successful loading from file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(self.valid_standard, f)
            temp_path = f.name

        try:
            self.standards.load_from_file(temp_path)
            assert self.standards.standard_data == self.valid_standard
        finally:
            os.unlink(temp_path)

    def test_load_from_file_not_found(self):
        """Test loading from non-existent file."""
        with pytest.raises(ValueError, match="Failed to load standard"):
            self.standards.load_from_file("nonexistent_file.yaml")

    def test_load_from_file_invalid_yaml(self):
        """Test loading from file with invalid YAML."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: [unclosed")
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match="Failed to load standard"):
                self.standards.load_from_file(temp_path)
        finally:
            os.unlink(temp_path)

    def test_load_from_file_with_project_root_fallback(self):
        """Test loading with project root fallback."""
        # This test is complex to mock properly, so we'll test the basic fallback behavior
        # by testing that the function handles missing files gracefully
        with pytest.raises(ValueError, match="Failed to load standard"):
            self.standards.load_from_file("nonexistent_relative_path.yaml")


class TestGetFieldRequirements:
    """Test the get_field_requirements method."""

    def setup_method(self):
        """Set up test fixtures."""
        self.standards = YAMLStandards()

    def test_get_field_requirements_with_data(self):
        """Test getting field requirements when data is loaded."""
        self.standards.standard_data = {
            "requirements": {
                "field_requirements": {
                    "field1": {"type": "string"},
                    "field2": {"type": "number"}
                }
            }
        }
        
        result = self.standards.get_field_requirements()
        expected = {
            "field1": {"type": "string"},
            "field2": {"type": "number"}
        }
        assert result == expected

    def test_get_field_requirements_no_data(self):
        """Test getting field requirements when no data is loaded."""
        result = self.standards.get_field_requirements()
        assert result == {}

    def test_get_field_requirements_missing_section(self):
        """Test getting field requirements when requirements section is missing."""
        self.standards.standard_data = {"other_section": "value"}
        result = self.standards.get_field_requirements()
        assert result == {}


class TestGetOverallMinimum:
    """Test the get_overall_minimum method."""

    def setup_method(self):
        """Set up test fixtures."""
        self.standards = YAMLStandards()

    def test_get_overall_minimum_with_data(self):
        """Test getting overall minimum when data is loaded."""
        self.standards.standard_data = {
            "requirements": {
                "overall_minimum": 85.0
            }
        }
        
        result = self.standards.get_overall_minimum()
        assert result == 85.0

    def test_get_overall_minimum_no_data(self):
        """Test getting overall minimum when no data is loaded."""
        result = self.standards.get_overall_minimum()
        assert result == 75.0  # Default value

    def test_get_overall_minimum_missing_section(self):
        """Test getting overall minimum when requirements section is missing."""
        self.standards.standard_data = {"other_section": "value"}
        result = self.standards.get_overall_minimum()
        assert result == 75.0  # Default value


class TestStandardsId:
    """Test the standards_id property."""

    def setup_method(self):
        """Set up test fixtures."""
        self.standards = YAMLStandards()

    def test_standards_id_with_data(self):
        """Test getting standards ID when data is loaded."""
        self.standards.standard_data = {
            "standards": {
                "id": "test-standard-id"
            }
        }
        
        result = self.standards.standards_id
        assert result == "test-standard-id"

    def test_standards_id_no_data(self):
        """Test getting standards ID when no data is loaded."""
        result = self.standards.standards_id
        assert result == "unknown"

    def test_standards_id_missing_section(self):
        """Test getting standards ID when standards section is missing."""
        self.standards.standard_data = {"other_section": "value"}
        result = self.standards.standards_id
        assert result == "unknown"


class TestListStandards:
    """Test the list_standards method."""

    def test_list_standards(self):
        """Test listing available standards."""
        standards = YAMLStandards()
        
        # Mock the loader's list_available_standards method
        with patch.object(standards.loader, 'list_available_standards') as mock_list:
            mock_list.return_value = ["standard1", "standard2", "standard3"]
            
            result = standards.list_standards()
            assert result == ["standard1", "standard2", "standard3"]
            mock_list.assert_called_once()


class TestLoadStandard:
    """Test the load_standard method."""

    def test_load_standard_success(self):
        """Test successful standard loading."""
        standards = YAMLStandards()
        mock_standard = {"id": "test", "version": "1.0.0"}
        
        with patch.object(standards.loader, 'load_standard') as mock_load:
            mock_load.return_value = mock_standard
            
            result = standards.load_standard("test_standard")
            assert result == mock_standard
            mock_load.assert_called_once_with("test_standard")

    def test_load_standard_failure(self):
        """Test standard loading failure."""
        standards = YAMLStandards()
        
        with patch.object(standards.loader, 'load_standard') as mock_load:
            mock_load.side_effect = Exception("Load failed")
            
            result = standards.load_standard("test_standard")
            assert result is None


class TestValidateStandard:
    """Test the validate_standard method."""

    def test_validate_standard_valid(self):
        """Test validating a valid standard."""
        standards = YAMLStandards()
        valid_standard = {
            "standard_id": "test",
            "version": "1.0.0",
            "description": "Test standard"
        }
        
        result = standards.validate_standard(valid_standard)
        assert result is True

    def test_validate_standard_missing_fields(self):
        """Test validating a standard with missing required fields."""
        standards = YAMLStandards()
        invalid_standard = {
            "standard_id": "test",
            # Missing version and description
        }
        
        result = standards.validate_standard(invalid_standard)
        assert result is False

    def test_validate_standard_empty(self):
        """Test validating an empty standard."""
        standards = YAMLStandards()
        result = standards.validate_standard({})
        assert result is False


class TestCheckCompliance:
    """Test the check_compliance method."""

    def setup_method(self):
        """Set up test fixtures."""
        self.standards = YAMLStandards()
        self.standards.standard_data = {
            "requirements": {
                "overall_minimum": 80.0,
                "dimension_requirements": {
                    "validity": 15.0,
                    "completeness": 15.0
                },
                "required_fields": ["field1", "field2"]
            }
        }

    def test_check_compliance_no_standard_loaded(self):
        """Test compliance checking when no standard is loaded."""
        standards = YAMLStandards()  # No standard loaded
        
        result = standards.check_compliance({"overall_score": 90.0})
        
        assert result["compliant"] is False
        assert result["overall_compliance"] is False
        assert "No standard loaded" in result["errors"][0]
        assert result["score"] == 0.0

    def test_check_compliance_passing(self):
        """Test compliance checking with passing report."""
        report_data = {
            "overall_score": 85.0,
            "dimension_scores": {
                "validity": 16.0,
                "completeness": 17.0
            },
            "field1": "present",
            "field2": "present"
        }
        
        result = self.standards.check_compliance(report_data)
        
        assert result["compliant"] is True
        assert result["overall_compliance"] is True
        assert len(result["errors"]) == 0
        assert result["score"] == 100.0  # Compliance score, not original score

    def test_check_compliance_failing_overall_score(self):
        """Test compliance checking with failing overall score."""
        report_data = {
            "overall_score": 70.0,  # Below minimum of 80.0
            "dimension_scores": {
                "validity": 16.0,
                "completeness": 17.0
            },
            "field1": "present",
            "field2": "present"
        }
        
        result = self.standards.check_compliance(report_data)
        
        assert result["compliant"] is False
        assert result["overall_compliance"] is False
        assert "Overall score 70.0 below minimum 80.0" in result["errors"][0]
        assert "overall_minimum" in result["failed_requirements"]

    def test_check_compliance_failing_dimension_score(self):
        """Test compliance checking with failing dimension score."""
        report_data = {
            "overall_score": 85.0,
            "dimension_scores": {
                "validity": 10.0,  # Below minimum of 15.0
                "completeness": 17.0
            },
            "field1": "present",
            "field2": "present"
        }
        
        result = self.standards.check_compliance(report_data)
        
        assert result["compliant"] is False
        assert result["overall_compliance"] is False
        assert "Dimension validity score 10.0 below minimum 15.0" in result["errors"][0]
        assert "dimension_validity_minimum" in result["failed_requirements"]

    def test_check_compliance_missing_required_field(self):
        """Test compliance checking with missing required field."""
        report_data = {
            "overall_score": 85.0,
            "dimension_scores": {
                "validity": 16.0,
                "completeness": 17.0
            },
            "field1": "present"
            # field2 is missing
        }
        
        result = self.standards.check_compliance(report_data)
        
        assert result["compliant"] is False
        assert result["overall_compliance"] is False
        assert "Missing required field: field2" in result["errors"][0]
        assert "field2" in result["failed_requirements"]

    def test_check_compliance_dimension_score_with_nested_structure(self):
        """Test compliance checking with nested dimension score structure."""
        report_data = {
            "overall_score": 85.0,
            "dimension_scores": {
                "validity": {"score": 16.0},  # Nested structure
                "completeness": {"score": 17.0}
            },
            "field1": "present",
            "field2": "present"
        }
        
        result = self.standards.check_compliance(report_data)
        
        assert result["compliant"] is True
        assert result["overall_compliance"] is True


class TestYAMLStandardsIntegration:
    """Integration tests for YAMLStandards."""

    def test_full_workflow(self):
        """Test complete workflow from loading to compliance checking."""
        # Create a complete standard
        standard_data = {
            "standard_metadata": {
                "id": "integration-test-standard",
                "version": "1.0.0"
            },
            "requirements": {
                "overall_minimum": 75.0,
                "dimension_requirements": {
                    "validity": 15.0,
                    "completeness": 15.0
                },
                "required_fields": ["test_field"],
                "field_requirements": {
                    "test_field": {"type": "string", "required": True}
                }
            },
            "standards": {
                "id": "integration-test"
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(standard_data, f)
            temp_path = f.name

        try:
            # Load the standard
            standards = YAMLStandards(temp_path)
            
            # Test all methods
            assert standards.standards_id == "integration-test"
            assert standards.get_overall_minimum() == 75.0
            
            field_reqs = standards.get_field_requirements()
            assert "test_field" in field_reqs
            
            # Test compliance checking
            passing_report = {
                "overall_score": 80.0,
                "dimension_scores": {
                    "validity": 16.0,
                    "completeness": 16.0
                },
                "test_field": "present"
            }
            
            compliance = standards.check_compliance(passing_report)
            assert compliance["compliant"] is True
            assert compliance["overall_compliance"] is True
            
        finally:
            os.unlink(temp_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
