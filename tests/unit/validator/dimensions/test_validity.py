"""Unit tests for ValidityAssessor dimension assessor."""

import pandas as pd
import pytest
from unittest.mock import Mock, patch

from src.adri.validator.dimensions.validity import ValidityAssessor


class TestValidityAssessor:
    """Test cases for ValidityAssessor class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.assessor = ValidityAssessor()

    def test_get_dimension_name(self):
        """Test that dimension name is correctly returned."""
        assert self.assessor.get_dimension_name() == "validity"

    def test_assess_with_non_dataframe_data(self):
        """Test assessment with non-DataFrame data returns default score."""
        requirements = {}
        score = self.assessor.assess("not a dataframe", requirements)
        assert score == 20.0

    def test_assess_basic_without_requirements(self):
        """Test basic assessment without field requirements."""
        data = pd.DataFrame({
            'email': ['test@example.com', 'invalid-email'],
            'age': [25, 150],
            'name': ['John', 'Jane']
        })
        requirements = {}

        score = self.assessor.assess(data, requirements)

        # Should use basic assessment which checks email and age patterns
        assert isinstance(score, float)
        assert 0.0 <= score <= 20.0

    def test_assess_with_field_requirements_simple(self):
        """Test assessment with field requirements but no rule weights."""
        data = pd.DataFrame({
            'name': ['John', 'Jane', 'Bob'],
            'age': [25, 30, 35]
        })

        requirements = {
            'field_requirements': {
                'name': {'type': 'string'},
                'age': {'type': 'integer', 'min_value': 0, 'max_value': 120}
            }
        }

        score = self.assessor.assess(data, requirements)

        # Should pass all validation rules
        assert isinstance(score, float)
        assert score > 15.0  # Should be a good score

    def test_assess_with_weighted_rules(self):
        """Test assessment with weighted rule configuration."""
        data = pd.DataFrame({
            'name': ['John', 'Jane', 'Bob'],
            'age': [25, 30, 35]
        })

        requirements = {
            'field_requirements': {
                'name': {'type': 'string'},
                'age': {'type': 'integer', 'min_value': 0, 'max_value': 120}
            },
            'scoring': {
                'rule_weights': {
                    'type': 0.5,
                    'numeric_bounds': 0.5
                },
                'field_overrides': {}
            }
        }

        score = self.assessor.assess(data, requirements)

        # Should pass all validation rules with weights
        assert isinstance(score, float)
        assert score > 15.0

    def test_assess_with_validation_failures(self):
        """Test assessment with data that fails validation."""
        data = pd.DataFrame({
            'name': [123, 'Jane', 'Bob'],  # First value is not a string
            'age': [25, 200, 35]  # Second value exceeds max
        })

        requirements = {
            'field_requirements': {
                'name': {'type': 'string'},
                'age': {'type': 'integer', 'min_value': 0, 'max_value': 120}
            }
        }

        score = self.assessor.assess(data, requirements)

        # Should have lower score due to failures
        assert isinstance(score, float)
        assert score < 18.0

    def test_is_valid_email(self):
        """Test email validation helper method."""
        assert self.assessor._is_valid_email('test@example.com') == True
        assert self.assessor._is_valid_email('user.name@domain.co.uk') == True
        assert self.assessor._is_valid_email('invalid-email') == False
        assert self.assessor._is_valid_email('test@') == False
        assert self.assessor._is_valid_email('@example.com') == False
        assert self.assessor._is_valid_email('test@@example.com') == False

    def test_compute_validity_rule_counts(self):
        """Test rule counting functionality."""
        data = pd.DataFrame({
            'name': ['John', 'Jane'],
            'email': ['john@example.com', 'jane@example.com']
        })

        field_requirements = {
            'name': {'type': 'string', 'min_length': 2, 'max_length': 10},
            'email': {'type': 'string', 'pattern': r'^[^@]+@[^@]+\.[^@]+$'}
        }

        counts, per_field_counts = self.assessor._compute_validity_rule_counts(
            data, field_requirements
        )

        # Verify counts structure
        assert isinstance(counts, dict)
        assert 'type' in counts
        assert 'length_bounds' in counts
        assert 'pattern' in counts

        # Verify per-field counts structure
        assert isinstance(per_field_counts, dict)
        assert 'name' in per_field_counts
        assert 'email' in per_field_counts

    def test_normalize_rule_weights(self):
        """Test rule weight normalization."""
        rule_weights_cfg = {
            'type': 0.5,
            'pattern': -0.1,  # Should be clamped to 0
            'unknown_rule': 0.3,  # Should be dropped
        }

        rule_keys = ['type', 'pattern', 'length_bounds']
        counts = {
            'type': {'total': 10, 'passed': 8},
            'pattern': {'total': 5, 'passed': 4},
            'length_bounds': {'total': 0, 'passed': 0}  # No evaluations
        }

        normalized = self.assessor._normalize_rule_weights(
            rule_weights_cfg, rule_keys, counts
        )

        # Should only include keys with evaluations and clamp negatives
        assert 'type' in normalized
        assert 'pattern' in normalized
        assert normalized['pattern'] == 0.0  # Clamped from negative
        assert 'unknown_rule' not in normalized
        assert 'length_bounds' not in normalized  # No evaluations

    def test_get_weight_default(self):
        """Test getting default weight from requirements."""
        requirements = {}
        weight = self.assessor.get_weight(requirements)
        assert weight == 1.0

    def test_get_weight_configured(self):
        """Test getting configured weight from requirements."""
        requirements = {'weight': 2.5}
        weight = self.assessor.get_weight(requirements)
        assert weight == 2.5

    def test_get_minimum_score_default(self):
        """Test getting default minimum score."""
        requirements = {}
        min_score = self.assessor.get_minimum_score(requirements)
        assert min_score == 15.0

    def test_get_minimum_score_configured(self):
        """Test getting configured minimum score."""
        requirements = {'minimum_score': 18.0}
        min_score = self.assessor.get_minimum_score(requirements)
        assert min_score == 18.0  # Should return configured value


class TestValidityAssessorIntegration:
    """Integration tests for ValidityAssessor."""

    def setup_method(self):
        """Set up test fixtures."""
        self.assessor = ValidityAssessor()

    def test_assess_invoice_data_example(self):
        """Test assessment with realistic invoice data."""
        data = pd.DataFrame({
            'invoice_id': ['INV-001', 'INV-002', 'INV-003'],
            'customer_email': ['customer1@example.com', 'customer2@example.com', 'invalid-email'],
            'amount': [1250.00, 875.50, -100.0],  # One negative amount
            'status': ['paid', 'paid', 'pending']
        })

        requirements = {
            'field_requirements': {
                'invoice_id': {'type': 'string', 'pattern': r'^INV-\d{3}$'},
                'customer_email': {'type': 'string', 'pattern': r'^[^@]+@[^@]+\.[^@]+$'},
                'amount': {'type': 'float', 'min_value': 0.0},
                'status': {'type': 'string', 'allowed_values': ['paid', 'pending', 'cancelled']}
            },
            'scoring': {
                'rule_weights': {
                    'type': 0.2,
                    'pattern': 0.3,
                    'numeric_bounds': 0.3,
                    'allowed_values': 0.2
                }
            }
        }

        score = self.assessor.assess(data, requirements)

        # Should detect the invalid email and negative amount
        assert isinstance(score, float)
        assert 0.0 <= score <= 20.0
        assert score < 20.0  # Should have some failures
