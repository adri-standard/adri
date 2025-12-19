"""
Test with actual Issue #35 bug report data.

This uses the real data and standard from the bug report to reproduce the issue.
"""

import sys
from pathlib import Path

import pandas as pd
import pytest

from adri.validator.engine import DataQualityAssessor


class TestIssue35ActualData:
    """Test with actual bug report data."""

    @pytest.fixture
    def bug_data_path(self):
        """Path to bug report data."""
        return Path(__file__).parent.parent / "fixtures" / "issue_35_test_data.csv"

    @pytest.fixture
    def bug_standard_path(self):
        """Path to bug report standard."""
        return Path(__file__).parent.parent / "fixtures" / "issue_35_test_standard.yaml"

    def test_direct_assessment_with_bug_data(self, bug_data_path, bug_standard_path):
        """Test direct assessment with bug report data and standard.
        
        Note: This test uses intentionally mismatched data (project fields) against
        a standard expecting customer fields. The new stricter schema validation
        correctly rejects this with 0% field match.
        """

        # Load data
        data = pd.read_csv(bug_data_path)

        print(f"\n{'='*80}")
        print(f"Testing with Issue #35 Bug Report Data")
        print(f"{'='*80}")
        print(f"Data shape: {data.shape}")
        print(f"Data columns: {list(data.columns)}")
        print(f"Standard: {bug_standard_path}")

        # The standard has customer fields (customer_id, email, age, etc.)
        # but data contains project fields (project_id, project_name, client, kpi, business_function)
        # The new stricter schema validation correctly rejects 0% field match
        assessor = DataQualityAssessor()
        
        with pytest.raises(ValueError) as exc_info:
            assessor.assess(data, str(bug_standard_path))
        
        # Verify the error message indicates schema validation failure
        error_message = str(exc_info.value)
        assert "Schema validation failed" in error_message or "field match" in error_message.lower()
        
        print(f"\n{'='*80}")
        print("EXPECTED BEHAVIOR: Schema validation correctly rejected mismatched fields")
        print(f"Error: {error_message}")
        print(f"{'='*80}")
        print(f"\nNote: Standard defines customer fields (customer_id, email, age, etc.)")
        print(f"      but data contains project fields ({', '.join(data.columns)})")
        print(f"      The stricter schema validation now correctly rejects 0% field match.")


if __name__ == "__main__":
    pytest.main([__file__, "-xvs"])
