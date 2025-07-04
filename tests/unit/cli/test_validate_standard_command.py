"""
Tests for the validate-standard CLI command.
"""

import json
import os
import tempfile
import unittest
from pathlib import Path

from adri.cli.commands import validate_standard_command, validate_yaml_standard


class TestValidateStandardCommand(unittest.TestCase):
    """Test cases for validate-standard command."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = Path(__file__).parent.parent.parent
        self.valid_standard_path = (
            self.test_dir / "fixtures" / "standards" / "customer_standard.yaml"
        )
        # Create a temporary invalid standard for testing
        self.temp_dir = tempfile.mkdtemp()
        self.invalid_standard_path = Path(self.temp_dir) / "invalid_standard.yaml"
        self.invalid_standard_path.write_text("""
standards:
  id: ""  # Empty required field
  name: "Invalid Standard"
  # Missing version and authority

requirements:
  overall_minimum: 150.0  # Invalid value > 100
  
  dimension_requirements:
    invalid_dimension:  # Unknown dimension
      minimum_score: 25.0  # Invalid score > 20
      
  field_requirements:
    test_field:
      type: "invalid_type"  # Invalid type
      pattern: "[unclosed"  # Invalid regex
""")

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        if hasattr(self, 'temp_dir') and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_validate_standard_command_valid_standard(self):
        """Test validate-standard command with valid standard."""
        result = validate_standard_command(str(self.valid_standard_path))
        self.assertEqual(result, 0)  # Success exit code

    def test_validate_standard_command_invalid_standard(self):
        """Test validate-standard command with invalid standard."""
        result = validate_standard_command(str(self.invalid_standard_path))
        self.assertEqual(result, 1)  # Error exit code

    def test_validate_standard_command_nonexistent_file(self):
        """Test validate-standard command with nonexistent file."""
        result = validate_standard_command("nonexistent.yaml")
        self.assertEqual(result, 1)  # Error exit code

    def test_validate_standard_command_with_output(self):
        """Test validate-standard command with JSON output."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            output_path = f.name

        try:
            result = validate_standard_command(
                str(self.valid_standard_path), output_path=output_path
            )
            self.assertEqual(result, 0)

            # Check that output file was created
            self.assertTrue(os.path.exists(output_path))

            # Check output content
            with open(output_path, "r") as f:
                report = json.load(f)

            self.assertTrue(report["is_valid"])
            self.assertEqual(report["standard_name"], "Customer Data Quality Standard")
            self.assertEqual(report["standard_version"], "1.0.0")
            self.assertEqual(report["authority"], "ADRI Test Suite")

        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_validate_yaml_standard_valid(self):
        """Test validate_yaml_standard function with valid standard."""
        result = validate_yaml_standard(str(self.valid_standard_path))

        self.assertTrue(result["is_valid"])
        self.assertEqual(len(result["errors"]), 0)
        self.assertEqual(result["standard_name"], "Customer Data Quality Standard")
        self.assertEqual(result["standard_version"], "1.0.0")
        self.assertEqual(result["authority"], "ADRI Test Suite")

        # Check that all expected validation checks passed
        expected_checks = [
            "Valid YAML syntax",
            "Root dictionary structure",
            "Required section 'standards' present",
            "Required section 'requirements' present",
            "YAMLStandards instantiation successful",
        ]

        for check in expected_checks:
            self.assertIn(check, result["passed_checks"])

    def test_validate_yaml_standard_invalid(self):
        """Test validate_yaml_standard function with invalid standard."""
        result = validate_yaml_standard(str(self.invalid_standard_path))

        self.assertFalse(result["is_valid"])
        self.assertGreater(len(result["errors"]), 0)

        # Check for specific expected errors
        error_messages = result["errors"]
        error_text = " ".join(error_messages)

        self.assertIn("Missing required field", error_text)
        self.assertIn("overall_minimum must be between 0 and 100", error_text)
        self.assertIn("Unknown dimension", error_text)
        self.assertIn("Invalid type", error_text)
        self.assertIn("Invalid regex pattern", error_text)

    def test_validate_yaml_standard_malformed_yaml(self):
        """Test validate_yaml_standard with malformed YAML."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("invalid: yaml: content: [unclosed")
            malformed_path = f.name

        try:
            result = validate_yaml_standard(malformed_path)

            self.assertFalse(result["is_valid"])
            self.assertGreater(len(result["errors"]), 0)

            # Should contain YAML syntax error
            error_text = " ".join(result["errors"])
            self.assertIn("Invalid YAML syntax", error_text)

        finally:
            os.unlink(malformed_path)

    def test_validate_yaml_standard_missing_sections(self):
        """Test validate_yaml_standard with missing required sections."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(
                """
standards:
  id: "test"
  name: "Test"
  version: "1.0.0"
  authority: "Test Authority"
# Missing requirements section
"""
            )
            missing_sections_path = f.name

        try:
            result = validate_yaml_standard(missing_sections_path)

            self.assertFalse(result["is_valid"])

            # Should contain missing section error
            error_text = " ".join(result["errors"])
            self.assertIn("Missing required section: 'requirements'", error_text)

        finally:
            os.unlink(missing_sections_path)

    def test_validate_yaml_standard_empty_fields(self):
        """Test validate_yaml_standard with empty required fields."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(
                """
standards:
  id: ""  # Empty field
  name: "Test"
  version: "1.0.0"
  authority: "Test Authority"

requirements:
  overall_minimum: 80.0
"""
            )
            empty_fields_path = f.name

        try:
            result = validate_yaml_standard(empty_fields_path)

            self.assertFalse(result["is_valid"])

            # Should contain empty field error
            error_text = " ".join(result["errors"])
            self.assertIn("Empty value for required field: 'id'", error_text)

        finally:
            os.unlink(empty_fields_path)

    def test_validate_yaml_standard_dimension_requirements(self):
        """Test validate_yaml_standard with dimension requirements."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(
                """
standards:
  id: "test-standard"
  name: "Test Standard"
  version: "1.0.0"
  authority: "Test Authority"

requirements:
  overall_minimum: 80.0
  
  dimension_requirements:
    validity:
      minimum_score: 15.0
    completeness:
      minimum_score: 18.0
"""
            )
            dim_reqs_path = f.name

        try:
            result = validate_yaml_standard(dim_reqs_path)

            self.assertTrue(result["is_valid"])

            # Should pass dimension validation checks
            passed_text = " ".join(result["passed_checks"])
            self.assertIn("Valid dimension: 'validity'", passed_text)
            self.assertIn("Valid dimension: 'completeness'", passed_text)
            self.assertIn("Valid minimum_score for validity: 15.0", passed_text)
            self.assertIn("Valid minimum_score for completeness: 18.0", passed_text)

        finally:
            os.unlink(dim_reqs_path)


if __name__ == "__main__":
    unittest.main()
