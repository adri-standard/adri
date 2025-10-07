"""
Unit tests for ReasoningValidator.

Tests AI/LLM output validation against reasoning standards.
"""

import pandas as pd
import pytest

from adri.standards.reasoning_validator import ReasoningValidator


class TestReasoningValidator:
    """Test ReasoningValidator functionality."""

    @pytest.fixture
    def validator(self):
        """Create ReasoningValidator instance."""
        return ReasoningValidator()

    @pytest.fixture
    def sample_ai_output(self):
        """Create sample AI output data."""
        return pd.DataFrame([
            {
                "project_id": "P001",
                "ai_risk_level": "HIGH",
                "ai_confidence_score": 0.85,
                "ai_recommendations": "Increase oversight"
            },
            {
                "project_id": "P002",
                "ai_risk_level": "MEDIUM",
                "ai_confidence_score": 0.72,
                "ai_recommendations": "Monitor closely"
            },
            {
                "project_id": "P003",
                "ai_risk_level": "LOW",
                "ai_confidence_score": 0.91,
                "ai_recommendations": "Standard review"
            },
        ])

    def test_validator_initialization(self, validator):
        """Test validator initializes correctly."""
        assert validator is not None
        assert hasattr(validator, 'assessor')
        assert hasattr(validator, 'config')

    def test_validate_confidence_scores_valid(self, validator, sample_ai_output):
        """Test validation of valid confidence scores."""
        from adri.validator.engine import AssessmentResult

        # Create a mock assessment result
        result = AssessmentResult(
            overall_score=85.0,
            passed=True,
            dimension_scores={},
        )

        # Should not raise any errors
        validator._validate_confidence_scores(sample_ai_output, result)

    def test_validate_confidence_scores_invalid(self, validator):
        """Test validation detects invalid confidence scores."""
        # Create data with invalid scores
        invalid_data = pd.DataFrame([
            {"ai_confidence_score": 1.5},  # Over 1.0
            {"ai_confidence_score": -0.2},  # Negative
            {"ai_confidence_score": 150},   # Over 100
        ])

        from adri.validator.engine import AssessmentResult
        result = AssessmentResult(
            overall_score=85.0,
            passed=True,
            dimension_scores={},
        )

        # Should log warnings but not fail
        validator._validate_confidence_scores(invalid_data, result)

    def test_validate_risk_levels_valid(self, validator, sample_ai_output):
        """Test validation of valid risk levels."""
        from adri.validator.engine import AssessmentResult

        result = AssessmentResult(
            overall_score=85.0,
            passed=True,
            dimension_scores={},
        )

        # Should not raise any errors
        validator._validate_risk_levels(sample_ai_output, result)

    def test_validate_risk_levels_invalid(self, validator):
        """Test validation detects invalid risk levels."""
        invalid_data = pd.DataFrame([
            {"ai_risk_level": "SUPER_HIGH"},  # Invalid
            {"ai_risk_level": "low"},         # Valid (lowercase)
            {"ai_risk_level": "UNKNOWN"},     # Invalid
        ])

        from adri.validator.engine import AssessmentResult
        result = AssessmentResult(
            overall_score=85.0,
            passed=True,
            dimension_scores={},
        )

        # Should log warnings but not fail
        validator._validate_risk_levels(invalid_data, result)

    def test_check_ai_field_requirements_allowed_values(self, validator):
        """Test checking AI field requirements with allowed values."""
        data = pd.DataFrame([
            {"risk_level": "HIGH"},
            {"risk_level": "MEDIUM"},
            {"risk_level": "INVALID"},  # Invalid
        ])

        requirements = {
            "risk_level": {
                "allowed_values": ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
            }
        }

        issues = validator.check_ai_field_requirements(data, requirements)

        # Should find 1 issue
        assert len(issues) == 1
        assert issues[0]["field"] == "risk_level"
        assert issues[0]["issue"] == "invalid_values"
        assert issues[0]["affected_rows"] == 1

    def test_check_ai_field_requirements_min_max(self, validator):
        """Test checking AI field requirements with min/max values."""
        data = pd.DataFrame([
            {"confidence": 0.5},
            {"confidence": 0.8},
            {"confidence": 1.2},  # Over max
            {"confidence": -0.1},  # Below min
        ])

        requirements = {
            "confidence": {
                "min_value": 0.0,
                "max_value": 1.0,
            }
        }

        issues = validator.check_ai_field_requirements(data, requirements)

        # Should find 2 issues (over max and below min)
        assert len(issues) == 2
        assert any(i["issue"] == "above_maximum" for i in issues)
        assert any(i["issue"] == "below_minimum" for i in issues)

    def test_validate_reasoning_completeness(self, validator):
        """Test validation of reasoning completeness."""
        data = pd.DataFrame([
            {"field1": "value1", "field2": "value2", "field3": "value3"},
            {"field1": "value1", "field2": None, "field3": "value3"},
            {"field1": None, "field2": None, "field3": None},
        ])

        required_fields = ["field1", "field2", "field3"]

        result = validator.validate_reasoning_completeness(data, required_fields)

        # Should calculate completeness score
        assert hasattr(result, 'score')
        assert 0 <= result.score <= 20

        # Check details
        assert result.details["total_required_cells"] == 9  # 3 rows * 3 fields
        assert result.details["missing_cells"] == 4  # Count of None values

    def test_validate_reasoning_completeness_no_requirements(self, validator):
        """Test validation with no required fields."""
        data = pd.DataFrame([{"field1": "value1"}])

        result = validator.validate_reasoning_completeness(data, [])

        # Should return perfect score
        assert result.score == 20.0

    def test_validate_reasoning_completeness_missing_field(self, validator):
        """Test validation when required field is completely missing."""
        data = pd.DataFrame([
            {"field1": "value1"},
            {"field1": "value2"},
        ])

        required_fields = ["field1", "field2"]  # field2 doesn't exist

        result = validator.validate_reasoning_completeness(data, required_fields)

        # Should count all missing field2 values
        assert result.details["missing_cells"] == 2  # Both rows missing field2


class TestReasoningValidatorIntegration:
    """Integration tests for ReasoningValidator with real standards."""

    @pytest.fixture
    def validator(self):
        """Create validator with config."""
        config = {
            "audit": {
                "enabled": False  # Disable logging for tests
            }
        }
        return ReasoningValidator(config)

    def test_validate_ai_output_basic(self, validator, tmp_path):
        """Test basic AI output validation with a standard."""
        # Create a simple standard
        standard_path = tmp_path / "ai_output_standard.yaml"
        standard_content = """
metadata:
  name: "AI Output Standard"
  version: "1.0.0"

requirements:
  overall_minimum: 75.0

  field_requirements:
    ai_risk_level:
      type: "string"
      nullable: false
      allowed_values: ["LOW", "MEDIUM", "HIGH", "CRITICAL"]

    ai_confidence_score:
      type: "number"
      nullable: false
      min_value: 0.0
      max_value: 1.0
"""
        standard_path.write_text(standard_content)

        # Create test data
        data = pd.DataFrame([
            {
                "ai_risk_level": "HIGH",
                "ai_confidence_score": 0.85,
            },
            {
                "ai_risk_level": "MEDIUM",
                "ai_confidence_score": 0.72,
            },
        ])

        # Validate
        result = validator.validate_ai_output(data, str(standard_path))

        # Should pass validation
        assert result is not None
        assert hasattr(result, 'overall_score')
