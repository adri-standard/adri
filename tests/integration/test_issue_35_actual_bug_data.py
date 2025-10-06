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
        """Test direct assessment with bug report data and standard."""

        # Load data
        data = pd.read_csv(bug_data_path)

        print(f"\n{'='*80}")
        print(f"Testing with Issue #35 Bug Report Data")
        print(f"{'='*80}")
        print(f"Data shape: {data.shape}")
        print(f"Data columns: {list(data.columns)}")
        print(f"Standard: {bug_standard_path}")

        # Capture diagnostic output
        import io
        old_stderr = sys.stderr
        sys.stderr = io.StringIO()

        try:
            assessor = DataQualityAssessor()
            result = assessor.assess(data, str(bug_standard_path))

            diagnostic_output = sys.stderr.getvalue()
        finally:
            sys.stderr = old_stderr

        # Print diagnostic output
        print(f"\n{'='*80}")
        print("DIAGNOSTIC OUTPUT")
        print(f"{'='*80}")
        print(diagnostic_output)

        # Print results
        print(f"\n{'='*80}")
        print("ASSESSMENT RESULTS")
        print(f"{'='*80}")
        print(f"Overall Score: {result.overall_score:.2f}/100")
        print(f"Passed: {result.passed}")
        print(f"\nDimension Scores:")
        for dim, score_obj in result.dimension_scores.items():
            score = score_obj.score if hasattr(score_obj, 'score') else score_obj
            print(f"  {dim}: {score:.2f}/20")

        if hasattr(result, 'metadata') and result.metadata:
            if 'applied_dimension_weights' in result.metadata:
                print(f"\nApplied Weights: {result.metadata['applied_dimension_weights']}")

        print(f"\n{'='*80}")

        # The bug report mentions the standard has customer fields but data has project fields
        # This field mismatch should cause validation failures
        print(f"\nNote: Standard defines customer fields (customer_id, email, age, etc.)")
        print(f"      but data contains project fields ({', '.join(data.columns)})")
        print(f"      This mismatch should affect validity scoring.")


if __name__ == "__main__":
    pytest.main([__file__, "-xvs"])
