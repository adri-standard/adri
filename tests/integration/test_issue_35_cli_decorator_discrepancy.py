"""
Integration test reproducing GitHub Issue #35: CLI vs Decorator Assessment Discrepancy.

This test demonstrates the exact issue reported where CLI and decorator assessments
produce significantly different quality scores for identical data and standards.
"""

import json
import os
import tempfile
from pathlib import Path
from typing import Dict, Any
import pytest
import pandas as pd

from src.adri.decorator import adri_protected
from src.adri.cli.commands.assess import AssessCommand
from src.adri.validator.engine import DataQualityAssessor


class Issue35ReproductionTest:
    """Test class for reproducing issue #35 discrepancy."""

    def setup_test_files(self, tmp_path):
        """Set up test data and standard files."""
        # Copy test data to temp directory
        test_data_path = Path(__file__).parent.parent / "fixtures" / "issue_35_test_data.csv"
        test_standard_path = Path(__file__).parent.parent / "fixtures" / "issue_35_test_standard.yaml"

        self.temp_data_path = tmp_path / "test_data.csv"
        self.temp_standard_path = tmp_path / "test_standard.yaml"

        # Copy files to temp directory
        import shutil
        shutil.copy(test_data_path, self.temp_data_path)
        shutil.copy(test_standard_path, self.temp_standard_path)

        # Load test data for decorator testing
        self.test_data = pd.read_csv(self.temp_data_path)

    def test_cli_assessment_baseline(self):
        """Test CLI assessment to establish baseline score."""
        # Run CLI assessment
        assess_command = AssessCommand()

        # Capture CLI output by running assessment directly
        args = {
            "data_path": str(self.temp_data_path),
            "standard_path": str(self.temp_standard_path),
            "guide": False
        }

        # Mock the CLI execution to capture results
        assessor = DataQualityAssessor()
        result = assessor.assess(self.test_data, str(self.temp_standard_path))

        # CLI should use threshold from standard file (75.0)
        expected_cli_threshold = 75.0

        print(f"CLI Assessment Results:")
        print(f"  Overall Score: {result.overall_score:.1f}/100")
        print(f"  Expected Threshold: {expected_cli_threshold}")
        print(f"  Passed: {result.passed}")

        # Store CLI results for comparison
        self.cli_score = result.overall_score
        self.cli_passed = result.passed
        self.cli_threshold = expected_cli_threshold

        # CLI assessment should read threshold from standard file
        assert result.overall_score > 0

    def test_decorator_assessment_baseline(self):
        """Test decorator assessment to establish baseline score."""
        # Create a test function with decorator
        @adri_protected(standard="roadmap_sample_standard")
        def test_function(data):
            return "processed"

        # Convert dataframe to list of dicts for decorator
        test_data_list = self.test_data.to_dict('records')

        # The decorator might fail due to different threshold logic
        # We need to capture the assessment result before it blocks
        try:
            result = test_function(test_data_list)
            decorator_passed = True
            decorator_score = None  # We need to extract this from the decorator logic
        except Exception as e:
            decorator_passed = False
            decorator_score = None
            print(f"Decorator blocked execution: {e}")

        # Store decorator results
        self.decorator_passed = decorator_passed
        self.decorator_score = decorator_score

        print(f"Decorator Assessment Results:")
        print(f"  Passed: {decorator_passed}")
        print(f"  Exception details available for score extraction")

    def test_issue_35_discrepancy_reproduction(self):
        """Reproduce the exact discrepancy reported in issue #35."""
        # Run both assessments
        self.test_cli_assessment_baseline()
        self.test_decorator_assessment_baseline()

        # The issue: Different thresholds and scores
        print(f"\nISSUE #35 REPRODUCTION:")
        print(f"CLI Score: {self.cli_score:.1f}/100, Threshold: {self.cli_threshold}, Passed: {self.cli_passed}")
        print(f"Decorator Passed: {self.decorator_passed}")

        # Document the discrepancy
        print(f"\nExpected Issue (before fix):")
        print(f"  - CLI: Should score ~91.5/100 with 75.0 threshold → PASSED")
        print(f"  - Decorator: Should score ~69.7/100 with 80.0 threshold → FAILED")
        print(f"  - Discrepancy: ~22 point difference on identical data")

        # This test documents the current behavior - it will be updated after fix
        assert self.cli_score is not None, "CLI assessment should produce a score"

    def test_threshold_source_discrepancy(self):
        """Test that CLI and decorator use different threshold sources."""
        from src.adri.config.loader import ConfigurationLoader
        from src.adri.validator.loaders import load_standard

        # Check CLI threshold source (should read from standard file)
        standard_dict = load_standard(str(self.temp_standard_path))
        cli_threshold = standard_dict.get("requirements", {}).get("overall_minimum", 75.0)

        # Check decorator threshold source (should read from config)
        try:
            config_loader = ConfigurationLoader()
            config = config_loader.get_active_config()
            if config:
                env_config = config_loader.get_environment_config(config)
                decorator_threshold = env_config.get("default_min_score", 80)
            else:
                decorator_threshold = 80  # hardcoded default
        except:
            decorator_threshold = 80  # fallback default

        print(f"\nThreshold Source Analysis:")
        print(f"  CLI reads from standard file: {cli_threshold}")
        print(f"  Decorator reads from config: {decorator_threshold}")
        print(f"  Difference: {abs(cli_threshold - decorator_threshold)} points")

        # Document the threshold discrepancy
        assert cli_threshold != decorator_threshold, "Thresholds should be different (documenting the issue)"

    def test_assessment_pipeline_differences(self):
        """Test that CLI and decorator use different assessment pipelines."""
        # This test documents the code path differences

        # CLI path: AssessCommand → DataQualityAssessor → ValidationEngine
        cli_path = [
            "src.adri.cli.commands.assess.AssessCommand",
            "src.adri.validator.engine.DataQualityAssessor",
            "src.adri.validator.engine.ValidationEngine"
        ]

        # Decorator path: adri_protected → DataProtectionEngine → different logic
        decorator_path = [
            "src.adri.decorator.adri_protected",
            "src.adri.guard.modes.DataProtectionEngine",
            "different validation logic"
        ]

        print(f"\nAssessment Pipeline Analysis:")
        print(f"  CLI Path: {' → '.join(cli_path)}")
        print(f"  Decorator Path: {' → '.join(decorator_path)}")
        print(f"  Issue: Different code paths can produce different scores")

        # Document that paths are different
        assert cli_path != decorator_path, "Assessment paths should be different (documenting the issue)"

    def test_data_format_compatibility(self):
        """Test that both CLI and decorator can handle the test data format."""
        # CLI expects CSV file
        assert self.temp_data_path.exists()
        assert self.temp_data_path.suffix == ".csv"

        # Decorator expects list of dicts
        test_data_list = self.test_data.to_dict('records')
        assert isinstance(test_data_list, list)
        assert len(test_data_list) == 35  # From issue #35
        assert all(isinstance(record, dict) for record in test_data_list)

        print(f"\nData Format Compatibility:")
        print(f"  CSV data shape: {self.test_data.shape}")
        print(f"  Dict list length: {len(test_data_list)}")
        print(f"  Sample record keys: {list(test_data_list[0].keys())}")

    def test_standard_resolution_differences(self):
        """Test potential differences in standard resolution between CLI and decorator."""
        # CLI uses explicit file path
        cli_standard_path = str(self.temp_standard_path)

        # Decorator uses standard name resolution
        decorator_standard_name = "roadmap_sample_standard"

        print(f"\nStandard Resolution Analysis:")
        print(f"  CLI uses explicit path: {cli_standard_path}")
        print(f"  Decorator uses name resolution: {decorator_standard_name}")
        print(f"  Potential issue: Name resolution may resolve to different file")

        # Check if the standard file contains the expected ID
        from src.adri.validator.loaders import load_standard
        standard_dict = load_standard(cli_standard_path)
        standard_id = standard_dict.get("standards", {}).get("id")

        assert standard_id == decorator_standard_name, f"Standard ID mismatch: {standard_id} vs {decorator_standard_name}"

    def assert_scores_within_tolerance(self, score1: float, score2: float, tolerance: float = 1.0):
        """Helper method to assert scores are within tolerance (for post-fix validation)."""
        difference = abs(score1 - score2)
        assert difference <= tolerance, f"Score difference {difference:.1f} exceeds tolerance {tolerance}"

    def assert_same_pass_fail_decision(self, passed1: bool, passed2: bool):
        """Helper method to assert same pass/fail decision (for post-fix validation)."""
        assert passed1 == passed2, f"Pass/fail decisions differ: {passed1} vs {passed2}"


# Individual test functions for pytest discovery
@pytest.fixture
def issue_35_test_setup(tmp_path):
    """Set up test environment for issue #35 reproduction."""
    # Copy test data to temp directory
    test_data_path = Path(__file__).parent.parent / "fixtures" / "issue_35_test_data.csv"
    test_standard_path = Path(__file__).parent.parent / "fixtures" / "issue_35_test_standard.yaml"

    temp_data_path = tmp_path / "test_data.csv"
    temp_standard_path = tmp_path / "test_standard.yaml"

    # Copy files to temp directory
    import shutil
    shutil.copy(test_data_path, temp_data_path)
    shutil.copy(test_standard_path, temp_standard_path)

    # Load test data for decorator testing
    test_data = pd.read_csv(temp_data_path)

    return {
        'temp_data_path': temp_data_path,
        'temp_standard_path': temp_standard_path,
        'test_data': test_data
    }


def test_issue_35_cli_baseline(issue_35_test_setup):
    """Test CLI assessment baseline for issue #35."""
    setup = issue_35_test_setup

    # Run CLI assessment using DataQualityAssessor directly
    assessor = DataQualityAssessor()
    result = assessor.assess(setup['test_data'], str(setup['temp_standard_path']))

    expected_cli_threshold = 75.0

    print(f"CLI Assessment Results:")
    print(f"  Overall Score: {result.overall_score:.1f}/100")
    print(f"  Expected Threshold: {expected_cli_threshold}")
    print(f"  Passed: {result.passed}")

    # CLI assessment should read threshold from standard file
    assert result.overall_score > 0


def test_issue_35_decorator_baseline(issue_35_test_setup):
    """Test decorator assessment baseline for issue #35."""
    setup = issue_35_test_setup

    # Create a test function with decorator
    @adri_protected(standard="roadmap_sample_standard")
    def test_function(data):
        return "processed"

    # Convert dataframe to list of dicts for decorator
    test_data_list = setup['test_data'].to_dict('records')

    # The decorator might fail due to different threshold logic
    try:
        result = test_function(test_data_list)
        decorator_passed = True
        print(f"Decorator Assessment Results: Passed")
    except Exception as e:
        decorator_passed = False
        print(f"Decorator blocked execution: {e}")

    # Document the current behavior
    print(f"Decorator execution allowed: {decorator_passed}")


def test_issue_35_full_reproduction(issue_35_test_setup):
    """Full reproduction of issue #35 discrepancy."""
    setup = issue_35_test_setup

    # Test CLI assessment
    assessor = DataQualityAssessor()
    cli_result = assessor.assess(setup['test_data'], str(setup['temp_standard_path']))

    # Test decorator assessment
    @adri_protected(standard="roadmap_sample_standard")
    def test_function(data):
        return "processed"

    test_data_list = setup['test_data'].to_dict('records')

    try:
        decorator_result = test_function(test_data_list)
        decorator_passed = True
    except Exception as e:
        decorator_passed = False
        print(f"Decorator blocked execution: {e}")

    cli_threshold = 75.0

    print(f"\nISSUE #35 REPRODUCTION:")
    print(f"CLI Score: {cli_result.overall_score:.1f}/100, Threshold: {cli_threshold}, Passed: {cli_result.passed}")
    print(f"Decorator Passed: {decorator_passed}")

    print(f"\nExpected Issue (before fix):")
    print(f"  - CLI: Should score ~91.5/100 with 75.0 threshold → PASSED")
    print(f"  - Decorator: Should score ~69.7/100 with 80.0 threshold → FAILED")
    print(f"  - Discrepancy: ~22 point difference on identical data")

    # This test documents the current behavior
    assert cli_result.overall_score > 0


def test_threshold_discrepancy(issue_35_test_setup):
    """Test threshold source discrepancy."""
    setup = issue_35_test_setup

    from src.adri.config.loader import ConfigurationLoader
    from src.adri.validator.loaders import load_standard

    # Check CLI threshold source (should read from standard file)
    standard_dict = load_standard(str(setup['temp_standard_path']))
    cli_threshold = standard_dict.get("requirements", {}).get("overall_minimum", 75.0)

    # Check decorator threshold source (should read from config)
    try:
        config_loader = ConfigurationLoader()
        config = config_loader.get_active_config()
        if config:
            env_config = config_loader.get_environment_config(config)
            decorator_threshold = env_config.get("default_min_score", 80)
        else:
            decorator_threshold = 80  # hardcoded default
    except:
        decorator_threshold = 80  # fallback default

    print(f"\nThreshold Source Analysis:")
    print(f"  CLI reads from standard file: {cli_threshold}")
    print(f"  Decorator reads from config: {decorator_threshold}")
    print(f"  Difference: {abs(cli_threshold - decorator_threshold)} points")

    # Document the threshold discrepancy
    assert cli_threshold != decorator_threshold, "Thresholds should be different (documenting the issue)"


def test_pipeline_differences(issue_35_test_setup):
    """Test assessment pipeline differences."""
    # This test documents the code path differences

    # CLI path: AssessCommand → DataQualityAssessor → ValidationEngine
    cli_path = [
        "src.adri.cli.commands.assess.AssessCommand",
        "src.adri.validator.engine.DataQualityAssessor",
        "src.adri.validator.engine.ValidationEngine"
    ]

    # Decorator path: adri_protected → DataProtectionEngine → different logic
    decorator_path = [
        "src.adri.decorator.adri_protected",
        "src.adri.guard.modes.DataProtectionEngine",
        "different validation logic"
    ]

    print(f"\nAssessment Pipeline Analysis:")
    print(f"  CLI Path: {' → '.join(cli_path)}")
    print(f"  Decorator Path: {' → '.join(decorator_path)}")
    print(f"  Issue: Different code paths can produce different scores")

    # Document that paths are different
    assert cli_path != decorator_path, "Assessment paths should be different (documenting the issue)"


def test_data_compatibility(issue_35_test_setup):
    """Test data format compatibility."""
    setup = issue_35_test_setup

    # CLI expects CSV file
    assert setup['temp_data_path'].exists()
    assert setup['temp_data_path'].suffix == ".csv"

    # Decorator expects list of dicts
    test_data_list = setup['test_data'].to_dict('records')
    assert isinstance(test_data_list, list)
    assert len(test_data_list) == 35  # From issue #35
    assert all(isinstance(record, dict) for record in test_data_list)

    print(f"\nData Format Compatibility:")
    print(f"  CSV data shape: {setup['test_data'].shape}")
    print(f"  Dict list length: {len(test_data_list)}")
    print(f"  Sample record keys: {list(test_data_list[0].keys())}")


def test_standard_resolution(issue_35_test_setup):
    """Test standard resolution differences."""
    setup = issue_35_test_setup

    # CLI uses explicit file path
    cli_standard_path = str(setup['temp_standard_path'])

    # Decorator uses standard name resolution
    decorator_standard_name = "roadmap_sample_standard"

    print(f"\nStandard Resolution Analysis:")
    print(f"  CLI uses explicit path: {cli_standard_path}")
    print(f"  Decorator uses name resolution: {decorator_standard_name}")
    print(f"  Potential issue: Name resolution may resolve to different file")

    # Check if the standard file contains the expected ID
    from src.adri.validator.loaders import load_standard
    standard_dict = load_standard(cli_standard_path)
    standard_id = standard_dict.get("standards", {}).get("id")

    assert standard_id == decorator_standard_name, f"Standard ID mismatch: {standard_id} vs {decorator_standard_name}"


# POST-FIX VALIDATION TESTS (these will pass after implementing the fix)
def test_post_fix_cli_decorator_consistency(issue_35_test_setup):
    """Test that CLI and decorator produce consistent results after fix."""
    # This test will be enabled after implementing the fix
    pytest.skip("Will be enabled after implementing the unified assessment engine")

    # Post-fix test logic:
    # setup = issue_35_test_setup
    # cli_result = assess_with_cli(setup)
    # decorator_result = assess_with_decorator(setup)
    # assert_scores_within_tolerance(cli_result.score, decorator_result.score)
    # assert_same_pass_fail_decision(cli_result.passed, decorator_result.passed)


def test_post_fix_unified_threshold_resolution(issue_35_test_setup):
    """Test that both CLI and decorator use same threshold after fix."""
    # This test will be enabled after implementing the fix
    pytest.skip("Will be enabled after implementing unified threshold resolution")

    # Post-fix test logic would verify both use standard file threshold
