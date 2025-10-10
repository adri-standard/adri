"""
Test CLI vs Decorator Scoring Parity - Issue #35 Regression Test.

This test verifies that CLI and Decorator produce identical scores when assessing
the same data against the same standard. This prevents regression of Issue #35.
"""

import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd
import pytest

from adri.validator.engine import DataQualityAssessor


class TestCLIDecoratorParity:
    """Test suite for CLI/Decorator scoring parity."""

    @pytest.fixture
    def test_data(self):
        """Create test data for parity checks."""
        return pd.DataFrame([
            {"invoice_id": "INV001", "amount": 100.0, "date": "2025-01-15"},
            {"invoice_id": "INV002", "amount": 200.0, "date": "2025-01-16"},
            {"invoice_id": "INV003", "amount": 150.0, "date": "2025-01-17"},
        ])

    @pytest.fixture
    def test_standard_path(self, tmp_path):
        """Create a test standard file."""
        standard_content = """
metadata:
  name: Test Invoice Standard
  version: 1.0.0
  description: Test standard for parity validation

requirements:
  overall_minimum: 75.0

  dimension_requirements:
    validity:
      weight: 1.0
      scoring:
        rule_weights:
          type: 1.0

    completeness:
      weight: 1.0

    consistency:
      weight: 1.0

    freshness:
      weight: 1.0

    plausibility:
      weight: 1.0

  field_requirements:
    invoice_id:
      type: string
      nullable: false

    amount:
      type: number
      nullable: false
      min_value: 0

    date:
      type: string
      nullable: false
"""
        standard_path = tmp_path / "test_standard.yaml"
        standard_path.write_text(standard_content)
        return str(standard_path)

    def test_decorator_assessment_direct(self, test_data, test_standard_path, tmp_path, monkeypatch):
        """Test decorator assessment directly using DataQualityAssessor."""
        print("\n" + "="*80)
        print("DECORATOR ASSESSMENT (Direct DataQualityAssessor)")
        print("="*80)

        # Set working directory to tmp_path to ensure clean config state
        monkeypatch.chdir(tmp_path)

        # Redirect stderr to capture diagnostic logs
        import io
        old_stderr = sys.stderr
        sys.stderr = io.StringIO()

        try:
            # Pass empty config to avoid config file lookups
            assessor = DataQualityAssessor(config={})
            result = assessor.assess(test_data, test_standard_path)

            # Get diagnostic output
            diagnostic_output = sys.stderr.getvalue()

        finally:
            sys.stderr = old_stderr

        # Print diagnostic output
        print(diagnostic_output)

        print(f"\nDecorator Result:")
        print(f"  Overall Score: {result.overall_score:.2f}/100")
        print(f"  Passed: {result.passed}")
        print(f"  Dimension Scores:")
        for dim, score_obj in result.dimension_scores.items():
            score = score_obj.score if hasattr(score_obj, 'score') else score_obj
            print(f"    {dim}: {score:.2f}/20")

        if hasattr(result, 'metadata') and result.metadata:
            if 'applied_dimension_weights' in result.metadata:
                print(f"  Applied Weights: {result.metadata['applied_dimension_weights']}")

        return result

    def test_cli_assessment(self, test_data, test_standard_path, tmp_path):
        """Test CLI assessment using subprocess."""
        print("\n" + "="*80)
        print("CLI ASSESSMENT (via adri assess command)")
        print("="*80)

        # Save test data to CSV
        data_path = tmp_path / "test_data.csv"
        test_data.to_csv(data_path, index=False)

        # Run CLI assessment using the adri command
        cmd = [
            "adri",
            "assess",
            str(data_path),
            "--standard", test_standard_path
        ]

        print(f"Running command: {' '.join(cmd)}")

        # Run from project root to find ADRI config
        project_root = Path(__file__).parent.parent.parent
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(project_root)
        )

        print(f"\nCLI stdout:")
        print(result.stdout)

        print(f"\nCLI stderr (diagnostic logs):")
        print(result.stderr)

        print(f"\nCLI return code: {result.returncode}")

        # Parse score from output
        score = None
        for line in result.stdout.split('\n'):
            if 'Score:' in line:
                # Extract score (format: "Score: 75.5/100")
                parts = line.split('Score:')[1].strip().split('/')[0].strip()
                score = float(parts)
                break

        return score, result.stderr

    def test_parity_direct_comparison(self, test_data, test_standard_path, tmp_path, monkeypatch):
        """Test that Decorator and CLI produce identical scores."""

        # Run decorator assessment
        decorator_result = self.test_decorator_assessment_direct(test_data, test_standard_path, tmp_path, monkeypatch)

        # Run CLI assessment
        cli_score, cli_diagnostic = self.test_cli_assessment(test_data, test_standard_path, tmp_path)

        print("\n" + "="*80)
        print("PARITY COMPARISON")
        print("="*80)
        print(f"Decorator Score: {decorator_result.overall_score:.2f}/100")
        print(f"CLI Score:       {cli_score:.2f}/100")
        print(f"Difference:      {abs(decorator_result.overall_score - cli_score):.2f} points")

        # Assert parity (within 0.1 points tolerance)
        assert abs(decorator_result.overall_score - cli_score) < 0.1, \
            f"CLI/Decorator parity FAILED: CLI={cli_score:.2f}, Decorator={decorator_result.overall_score:.2f}"

        print("\n✅ PARITY TEST PASSED - Scores match within tolerance")

    def test_parity_with_real_bug_report_data(self, tmp_path, monkeypatch):
        """Test parity using actual bug report data if available."""

        # Set working directory to tmp_path to ensure clean config state
        monkeypatch.chdir(tmp_path)

        # Check if bug report fixtures exist
        fixtures_dir = Path(__file__).parent.parent / "fixtures"
        bug_data_path = fixtures_dir / "issue_35_test_data.csv"

        if not bug_data_path.exists():
            pytest.skip("Bug report data not available")

        # Load bug report data
        test_data = pd.read_csv(bug_data_path)

        # Create bug report standard
        standard_content = """
metadata:
  name: Bug Report Standard
  version: 1.0.0

requirements:
  overall_minimum: 75.0

  dimension_requirements:
    validity:
      weight: 1.0
    completeness:
      weight: 1.0
    consistency:
      weight: 1.0
    freshness:
      weight: 1.0
    plausibility:
      weight: 1.0

  field_requirements:
    {}
"""

        # Generate field requirements from data - detect actual types
        field_reqs = {}
        for col in test_data.columns:
            # Infer type from pandas dtype
            dtype = test_data[col].dtype
            if pd.api.types.is_integer_dtype(dtype):
                field_type = "integer"
            elif pd.api.types.is_float_dtype(dtype):
                field_type = "number"
            elif pd.api.types.is_bool_dtype(dtype):
                field_type = "string"  # Treat bools as strings for simplicity
            else:
                field_type = "string"

            field_reqs[col] = {
                "type": field_type,
                "nullable": True
            }

        # Save standard
        import yaml
        standard_path = tmp_path / "bug_report_standard.yaml"
        with open(standard_path, 'w', encoding='utf-8') as f:
            yaml.dump({
                "metadata": {
                    "name": "Bug Report Standard",
                    "version": "1.0.0"
                },
                "requirements": {
                    "overall_minimum": 75.0,
                    "dimension_requirements": {
                        "validity": {"weight": 1.0},
                        "completeness": {"weight": 1.0},
                        "consistency": {"weight": 1.0},
                        "freshness": {"weight": 1.0},
                        "plausibility": {"weight": 1.0}
                    },
                    "field_requirements": field_reqs
                }
            }, f)

        # Run parity test
        decorator_result = self.test_decorator_assessment_direct(test_data, str(standard_path), tmp_path, monkeypatch)
        cli_score, _ = self.test_cli_assessment(test_data, str(standard_path), tmp_path)

        print("\n" + "="*80)
        print("BUG REPORT DATA PARITY COMPARISON")
        print("="*80)
        print(f"Decorator Score: {decorator_result.overall_score:.2f}/100")
        print(f"CLI Score:       {cli_score:.2f}/100")
        print(f"Difference:      {abs(decorator_result.overall_score - cli_score):.2f} points")

        # Assert parity (strict tolerance - CLI and Decorator must match)
        assert abs(decorator_result.overall_score - cli_score) < 0.1, \
            f"Bug report parity FAILED: CLI={cli_score:.2f}, Decorator={decorator_result.overall_score:.2f}"


if __name__ == "__main__":
    # Run tests directly for debugging
    import sys
    sys.exit(pytest.main([__file__, "-v", "-s"]))
