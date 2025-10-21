"""Tests for severity defaults configuration loader.

Tests loading and retrieving severity defaults from configuration.
"""

import pytest
import tempfile
import os
from pathlib import Path

from src.adri.config.severity_loader import SeverityDefaultsLoader
from src.adri.core.severity import Severity


class TestSeverityDefaultsLoader:
    """Test severity defaults configuration loader."""

    def setup_method(self):
        """Reset singleton before each test."""
        SeverityDefaultsLoader._instance = None
        SeverityDefaultsLoader._config = None

    def teardown_method(self):
        """Clean up singleton after each test."""
        SeverityDefaultsLoader._instance = None
        SeverityDefaultsLoader._config = None

    def test_loader_singleton(self):
        """Test that loader implements singleton pattern."""
        loader1 = SeverityDefaultsLoader()
        loader2 = SeverityDefaultsLoader()

        assert loader1 is loader2

    def test_get_severity_validity_type(self):
        """Test getting CRITICAL severity for validity type rule."""
        loader = SeverityDefaultsLoader()
        severity = loader.get_severity("validity", "type")

        assert severity == Severity.CRITICAL

    def test_get_severity_validity_pattern(self):
        """Test getting WARNING severity for validity pattern rule."""
        loader = SeverityDefaultsLoader()
        severity = loader.get_severity("validity", "pattern")

        assert severity == Severity.WARNING

    def test_get_severity_completeness_not_null(self):
        """Test getting CRITICAL severity for completeness not_null rule."""
        loader = SeverityDefaultsLoader()
        severity = loader.get_severity("completeness", "not_null")

        assert severity == Severity.CRITICAL

    def test_get_severity_consistency_format(self):
        """Test getting WARNING severity for consistency format rule."""
        loader = SeverityDefaultsLoader()
        severity = loader.get_severity("consistency", "format")

        assert severity == Severity.WARNING

    def test_get_severity_consistency_primary_key(self):
        """Test getting CRITICAL severity for consistency primary_key rule."""
        loader = SeverityDefaultsLoader()
        severity = loader.get_severity("consistency", "primary_key")

        assert severity == Severity.CRITICAL

    def test_get_severity_freshness_recency(self):
        """Test getting INFO severity for freshness recency rule."""
        loader = SeverityDefaultsLoader()
        severity = loader.get_severity("freshness", "recency")

        assert severity == Severity.INFO

    def test_get_severity_plausibility_statistical_outlier(self):
        """Test getting INFO severity for plausibility statistical_outlier rule."""
        loader = SeverityDefaultsLoader()
        severity = loader.get_severity("plausibility", "statistical_outlier")

        assert severity == Severity.INFO

    def test_get_severity_unknown_rule_type_uses_default(self):
        """Test that unknown rule types use the provided default."""
        loader = SeverityDefaultsLoader()
        severity = loader.get_severity("validity", "unknown_rule", default="WARNING")

        assert severity == Severity.WARNING

    def test_get_severity_unknown_dimension_uses_default(self):
        """Test that unknown dimensions use the provided default."""
        loader = SeverityDefaultsLoader()
        severity = loader.get_severity("unknown_dimension", "type", default="CRITICAL")

        assert severity == Severity.CRITICAL

    def test_get_all_defaults(self):
        """Test getting all default severities."""
        loader = SeverityDefaultsLoader()
        defaults = loader.get_all_defaults()

        assert "validity" in defaults
        assert "completeness" in defaults
        assert "consistency" in defaults
        assert "freshness" in defaults
        assert "plausibility" in defaults

        # Verify some specific values
        assert defaults["validity"]["type"] == "CRITICAL"
        assert defaults["consistency"]["format"] == "WARNING"
        assert defaults["plausibility"]["statistical_outlier"] == "INFO"

    def test_config_loading_resilience(self):
        """Test that loader handles missing config gracefully."""
        # Create a new loader instance with invalid env var
        os.environ["ADRI_SEVERITY_CONFIG"] = "/nonexistent/path/config.yaml"

        try:
            # Force reload
            loader = SeverityDefaultsLoader()
            loader.reload_config()

            # Should still work with hardcoded defaults
            severity = loader.get_severity("validity", "type")
            assert severity == Severity.CRITICAL
        finally:
            # Clean up environment
            if "ADRI_SEVERITY_CONFIG" in os.environ:
                del os.environ["ADRI_SEVERITY_CONFIG"]
            # Reset singleton
            SeverityDefaultsLoader._instance = None
            SeverityDefaultsLoader._config = None


class TestSeverityDefaultsMapping:
    """Test specific severity default mappings."""

    def test_critical_rule_types(self):
        """Test that data quality rules are CRITICAL by default."""
        loader = SeverityDefaultsLoader()

        critical_rules = [
            ("validity", "type"),
            ("validity", "allowed_values"),
            ("validity", "numeric_bounds"),
            ("validity", "date_bounds"),
            ("validity", "length_bounds"),
            ("completeness", "not_null"),
            ("completeness", "not_empty"),
            ("consistency", "uniqueness"),
            ("consistency", "primary_key"),
            ("plausibility", "business_rule"),
        ]

        for dimension, rule_type in critical_rules:
            severity = loader.get_severity(dimension, rule_type)
            assert severity == Severity.CRITICAL, \
                f"{dimension}.{rule_type} should be CRITICAL"

    def test_warning_rule_types(self):
        """Test that style/preference rules are WARNING by default."""
        loader = SeverityDefaultsLoader()

        warning_rules = [
            ("validity", "pattern"),
            ("consistency", "format"),
            ("consistency", "case"),
            ("consistency", "cross_field"),
            ("freshness", "age_check"),
            ("plausibility", "range_check"),
            ("plausibility", "categorical_frequency"),
        ]

        for dimension, rule_type in warning_rules:
            severity = loader.get_severity(dimension, rule_type)
            assert severity == Severity.WARNING, \
                f"{dimension}.{rule_type} should be WARNING"

    def test_info_rule_types(self):
        """Test that informational rules are INFO by default."""
        loader = SeverityDefaultsLoader()

        info_rules = [
            ("freshness", "recency"),
            ("freshness", "staleness"),
            ("plausibility", "statistical_outlier"),
        ]

        for dimension, rule_type in info_rules:
            severity = loader.get_severity(dimension, rule_type)
            assert severity == Severity.INFO, \
                f"{dimension}.{rule_type} should be INFO"
