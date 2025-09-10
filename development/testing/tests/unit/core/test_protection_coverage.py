"""
Tests to improve coverage for adri.core.protection module.

These tests target specific uncovered lines to reach 100% coverage.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest

from adri.core.protection import DataProtectionEngine, ProtectionError


class TestProtectionCoverage:
    """Tests targeting specific uncovered lines in protection.py."""

    def test_format_quality_success_with_yaml_parsing_error(self):
        """Test _format_quality_success when YAML parsing fails (lines 688-689)."""
        engine = DataProtectionEngine()

        # Create a mock assessment result
        mock_assessment = MagicMock()
        mock_assessment.overall_score = 85.0
        mock_assessment.dimension_scores = {
            "validity": MagicMock(score=18.0),
            "completeness": MagicMock(score=17.0),
        }

        # Create a temporary standard file with invalid YAML
        with tempfile.NamedTemporaryFile(
            mode="w", suffix="_standard.yaml", delete=False
        ) as f:
            f.write("invalid: yaml: content: [unclosed")
            temp_standard_path = f.name

        try:
            # Mock os.path.exists to return True for the standard file
            with patch("os.path.exists", return_value=True):
                # This should trigger the YAML parsing exception (lines 688-689)
                result = engine._format_quality_success(
                    assessment_result=mock_assessment,
                    min_score=80.0,
                    standard=temp_standard_path,
                    function_name="test_function",
                    verbose=True,
                )

                # Should still work despite YAML parsing error
                assert "ADRI Protection: ALLOWED ✅" in result
                assert "85.0/100" in result
                # Should use default version since YAML parsing failed
                assert "v1.0.0" in result

        finally:
            os.unlink(temp_standard_path)

    def test_format_quality_success_with_yaml_parsing_success(self):
        """Test _format_quality_success when YAML parsing succeeds."""
        engine = DataProtectionEngine()

        # Create a mock assessment result
        mock_assessment = MagicMock()
        mock_assessment.overall_score = 92.0
        mock_assessment.dimension_scores = {
            "validity": MagicMock(score=19.0),
            "completeness": MagicMock(score=18.5),
        }

        # Create a temporary standard file with valid YAML
        standard_content = """
standards:
  id: test_standard
  version: "2.1.0"
  name: "Test Standard"
requirements:
  overall_minimum: 80.0
"""

        with tempfile.NamedTemporaryFile(
            mode="w", suffix="_standard.yaml", delete=False
        ) as f:
            f.write(standard_content)
            temp_standard_path = f.name

        try:
            # Mock os.path.exists to return True for the standard file
            with patch("os.path.exists", return_value=True):
                result = engine._format_quality_success(
                    assessment_result=mock_assessment,
                    min_score=80.0,
                    standard=temp_standard_path,
                    function_name="test_function",
                    verbose=True,
                )

                # Should work and extract version from YAML
                assert "ADRI Protection: ALLOWED ✅" in result
                assert "92.0/100" in result
                # Should use version from YAML file
                assert "v2.1.0" in result

        finally:
            os.unlink(temp_standard_path)

    def test_format_quality_success_with_nonexistent_standard_file(self):
        """Test _format_quality_success with nonexistent standard file."""
        engine = DataProtectionEngine()

        # Create a mock assessment result
        mock_assessment = MagicMock()
        mock_assessment.overall_score = 88.0
        mock_assessment.dimension_scores = {}

        # Use a nonexistent file path
        nonexistent_path = "/path/to/nonexistent_standard.yaml"

        result = engine._format_quality_success(
            assessment_result=mock_assessment,
            min_score=75.0,
            standard=nonexistent_path,
            function_name="test_function",
            verbose=False,
        )

        # Should work with default version
        assert "ADRI Protection: ALLOWED ✅" in result
        assert "88.0/100" in result
        assert "v1.0.0" in result

    def test_format_quality_success_with_bundled_standard(self):
        """Test _format_quality_success with bundled standard dict."""
        engine = DataProtectionEngine()

        # Create a mock assessment result
        mock_assessment = MagicMock()
        mock_assessment.overall_score = 95.0
        mock_assessment.dimension_scores = {
            "validity": MagicMock(score=20.0),
            "completeness": MagicMock(score=19.5),
            "consistency": MagicMock(score=18.0),
        }

        # Create a bundled standard dict
        bundled_standard = {
            "standards": {
                "id": "customer_data_standard",
                "name": "Customer Data Standard",
                "version": "3.2.1",
            },
            "requirements": {"overall_minimum": 85.0},
        }

        result = engine._format_quality_success(
            assessment_result=mock_assessment,
            min_score=85.0,
            standard=bundled_standard,
            function_name="process_customers",
            verbose=True,
        )

        # Should work with bundled standard
        assert "ADRI Protection: ALLOWED ✅" in result
        assert "95.0/100" in result
        assert "v3.2.1" in result
        assert "Customer Data Standard" in result

    def test_format_minimal_success_vs_verbose_success(self):
        """Test the difference between minimal and verbose success messages."""
        engine = DataProtectionEngine()

        # Create a mock assessment result
        mock_assessment = MagicMock()
        mock_assessment.overall_score = 87.5
        mock_assessment.dimension_scores = {
            "validity": MagicMock(score=17.5),
            "completeness": MagicMock(score=18.0),
        }

        # Test minimal success (verbose=False)
        minimal_result = engine._format_quality_success(
            assessment_result=mock_assessment,
            min_score=80.0,
            standard="test_standard.yaml",
            function_name="test_function",
            verbose=False,
        )

        # Test verbose success (verbose=True)
        verbose_result = engine._format_quality_success(
            assessment_result=mock_assessment,
            min_score=80.0,
            standard="test_standard.yaml",
            function_name="test_function",
            verbose=True,
        )

        # Both should contain basic success info
        assert "ADRI Protection: ALLOWED ✅" in minimal_result
        assert "ADRI Protection: ALLOWED ✅" in verbose_result
        assert "87.5/100" in minimal_result
        assert "87.5/100" in verbose_result

        # Verbose should be longer and contain more details
        assert len(verbose_result) > len(minimal_result)
        assert "Dimension Details:" in verbose_result
        assert "Learn More:" in verbose_result

        # Minimal should be concise
        assert "Dimension Details:" not in minimal_result
        assert "Learn More:" not in minimal_result

    def test_was_standard_just_created_edge_cases(self):
        """Test _was_standard_just_created with various edge cases."""
        engine = DataProtectionEngine()

        # Test with None path
        assert engine._was_standard_just_created(None) is False

        # Test with nonexistent file
        assert engine._was_standard_just_created("/nonexistent/file.yaml") is False

        # Test with existing file that's old
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_file = f.name

        try:
            # Mock os.path.getctime to return an old timestamp
            with patch("os.path.getctime", return_value=0):  # Very old file
                assert engine._was_standard_just_created(temp_file) is False

            # Mock os.path.getctime to return a recent timestamp
            import time

            recent_time = time.time() - 2  # 2 seconds ago
            with patch("os.path.getctime", return_value=recent_time):
                assert engine._was_standard_just_created(temp_file) is True

            # Test exception handling in getctime
            with patch("os.path.getctime", side_effect=OSError("Permission denied")):
                assert engine._was_standard_just_created(temp_file) is False

        finally:
            os.unlink(temp_file)

    def test_format_quality_success_with_new_standard_indicator(self):
        """Test _format_quality_success with new standard creation indicator."""
        engine = DataProtectionEngine()

        # Create a mock assessment result
        mock_assessment = MagicMock()
        mock_assessment.overall_score = 90.0
        mock_assessment.dimension_scores = {}

        # Create a temporary file and mock it as "just created"
        with tempfile.NamedTemporaryFile(
            mode="w", suffix="_standard.yaml", delete=False
        ) as f:
            f.write("standards:\n  version: '1.0.0'\n")
            temp_file = f.name

        try:
            # Mock _was_standard_just_created to return True
            with patch.object(engine, "_was_standard_just_created", return_value=True):
                result = engine._format_quality_success(
                    assessment_result=mock_assessment,
                    min_score=80.0,
                    standard=temp_file,
                    function_name="test_function",
                    verbose=True,
                )

                # Should indicate new standard
                assert "(NEW)" in result
                assert "Since this is a NEW standard:" in result
                assert "Customize Your Standard:" in result

            # Mock _was_standard_just_created to return False
            with patch.object(engine, "_was_standard_just_created", return_value=False):
                result = engine._format_quality_success(
                    assessment_result=mock_assessment,
                    min_score=80.0,
                    standard=temp_file,
                    function_name="test_function",
                    verbose=True,
                )

                # Should not indicate new standard
                assert "(NEW)" not in result
                assert "Since this is a NEW standard:" not in result
                assert "Learn More:" in result

        finally:
            os.unlink(temp_file)
