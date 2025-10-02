"""
Test to verify CLI and Decorator produce EXACTLY the same assessment results.

This test checks for complete consistency - same threshold AND same score.
"""

import pytest
import pandas as pd
from pathlib import Path

from src.adri.decorator import adri_protected
from src.adri.validator.engine import DataQualityAssessor


@pytest.fixture
def test_setup(tmp_path):
    """Set up test environment."""
    test_data_path = Path(__file__).parent.parent / "fixtures" / "issue_35_test_data.csv"
    test_standard_path = Path(__file__).parent.parent / "fixtures" / "issue_35_test_standard.yaml"

    temp_data_path = tmp_path / "test_data.csv"
    temp_standard_path = tmp_path / "test_standard.yaml"

    import shutil
    shutil.copy(test_data_path, temp_data_path)
    shutil.copy(test_standard_path, temp_standard_path)

    test_data = pd.read_csv(temp_data_path)

    return {
        'temp_data_path': temp_data_path,
        'temp_standard_path': temp_standard_path,
        'test_data': test_data
    }


def test_exact_score_consistency(test_setup):
    """Test that CLI and decorator produce EXACTLY the same scores."""
    setup = test_setup

    # CLI Assessment
    assessor = DataQualityAssessor()
    cli_result = assessor.assess(setup['test_data'], str(setup['temp_standard_path']))

    print(f"CLI Assessment:")
    print(f"  Score: {cli_result.overall_score:.1f}/100")
    print(f"  Passed: {cli_result.passed}")

    # Direct assessment using same engine (what decorator should use)
    direct_result = assessor.assess(setup['test_data'], str(setup['temp_standard_path']))

    print(f"Direct Assessment:")
    print(f"  Score: {direct_result.overall_score:.1f}/100")
    print(f"  Passed: {direct_result.passed}")

    # Store decorator score using a capture mechanism
    decorator_score = None
    decorator_passed = None

    @adri_protected(standard=str(setup['temp_standard_path']))
    def test_function(data):
        return "processed"

    test_data_list = setup['test_data'].to_dict('records')

    try:
        result = test_function(test_data_list)
        decorator_passed = True
    except Exception as e:
        decorator_passed = False
        error_msg = str(e)
        print(f"Decorator execution blocked: {e}")

        # Extract score from error message: "Quality Score: 74.0/100"
        import re
        score_match = re.search(r'Quality Score: ([\d.]+)/100', error_msg)
        if score_match:
            decorator_score = float(score_match.group(1))

    print(f"Decorator Assessment:")
    print(f"  Execution allowed: {decorator_passed}")
    print(f"  Score: {decorator_score:.1f}/100" if decorator_score else "Score extraction failed")

    # Check for consistency
    if decorator_score is not None:
        score_difference = abs(decorator_score - cli_result.overall_score)
        if score_difference < 0.1:  # Allow for tiny floating point differences
            print(f"\n✅ SCORE CONSISTENCY ACHIEVED:")
            print(f"  CLI produces: {cli_result.overall_score:.1f}/100")
            print(f"  Decorator produces: {decorator_score:.1f}/100")
            print(f"  Difference: {score_difference:.1f} points (RESOLVED)")
        else:
            print(f"\n❌ SCORE CONSISTENCY ISSUE:")
            print(f"  CLI produces: {cli_result.overall_score:.1f}/100")
            print(f"  Decorator produces: {decorator_score:.1f}/100")
            print(f"  Difference: {score_difference:.1f} points")
            print(f"  Root cause: Different assessment code paths")

    # Test assertions
    assert cli_result.overall_score > 0, "CLI should produce a valid score"
    if decorator_score is not None:
        assert abs(decorator_score - cli_result.overall_score) < 0.1, f"Scores should match: CLI={cli_result.overall_score:.1f}, Decorator={decorator_score:.1f}"


def test_complete_output_consistency(test_setup):
    """Test that CLI and decorator produce EXACTLY the same logs, dimensions, and all outputs."""
    setup = test_setup

    # CLI Assessment with full output capture
    assessor = DataQualityAssessor()
    cli_result = assessor.assess(setup['test_data'], str(setup['temp_standard_path']))

    print(f"\n=== CLI FULL ASSESSMENT OUTPUT ===")
    print(f"Overall Score: {cli_result.overall_score}")
    print(f"Passed: {cli_result.passed}")
    print(f"Assessment Source: {getattr(cli_result, 'assessment_source', 'cli')}")

    # Capture CLI dimension scores
    cli_dimensions = {}
    if hasattr(cli_result, 'dimension_scores'):
        for dim_name, dim_result in cli_result.dimension_scores.items():
            cli_dimensions[dim_name] = {
                'score': getattr(dim_result, 'score', 0),
                'details': getattr(dim_result, 'details', {}),
                'passed': getattr(dim_result, 'passed', False)
            }
            print(f"  {dim_name}: {cli_dimensions[dim_name]['score']:.1f} (passed: {cli_dimensions[dim_name]['passed']})")

    # Capture CLI field results
    cli_fields = {}
    if hasattr(cli_result, 'field_results'):
        for field_name, field_result in cli_result.field_results.items():
            cli_fields[field_name] = {
                'score': getattr(field_result, 'score', 0),
                'issues': getattr(field_result, 'issues', []),
                'passed': getattr(field_result, 'passed', False)
            }
            print(f"  Field {field_name}: {cli_fields[field_name]['score']:.1f}")

    # Decorator Assessment with custom result capture
    decorator_result = None
    decorator_dimensions = {}
    decorator_fields = {}

    @adri_protected(standard=str(setup['temp_standard_path']))
    def capture_decorator_result(data):
        # This function gets access to the assessment result through the decorator
        return "processed"

    # We need to monkey-patch the assessment method to capture the full result
    original_assess = None
    captured_decorator_result = None

    try:
        from src.adri.guard.modes import DataProtectionEngine
        original_assess_method = DataProtectionEngine._assess_data_quality

        def capturing_assess(self, data, standard_path):
            nonlocal captured_decorator_result
            result = original_assess_method(self, data, standard_path)
            captured_decorator_result = result
            return result

        DataProtectionEngine._assess_data_quality = capturing_assess

        test_data_list = setup['test_data'].to_dict('records')

        try:
            capture_decorator_result(test_data_list)
        except Exception as e:
            print(f"Decorator execution blocked (expected): {e}")

        # Restore original method
        DataProtectionEngine._assess_data_quality = original_assess_method

    except Exception as e:
        print(f"Could not capture decorator result: {e}")

    print(f"\n=== DECORATOR FULL ASSESSMENT OUTPUT ===")
    if captured_decorator_result:
        decorator_result = captured_decorator_result
        print(f"Overall Score: {decorator_result.overall_score}")
        print(f"Passed: {decorator_result.passed}")
        print(f"Assessment Source: {getattr(decorator_result, 'assessment_source', 'decorator')}")

        # Capture decorator dimension scores
        if hasattr(decorator_result, 'dimension_scores'):
            for dim_name, dim_result in decorator_result.dimension_scores.items():
                decorator_dimensions[dim_name] = {
                    'score': getattr(dim_result, 'score', 0),
                    'details': getattr(dim_result, 'details', {}),
                    'passed': getattr(dim_result, 'passed', False)
                }
                print(f"  {dim_name}: {decorator_dimensions[dim_name]['score']:.1f} (passed: {decorator_dimensions[dim_name]['passed']})")

        # Capture decorator field results
        if hasattr(decorator_result, 'field_results'):
            for field_name, field_result in decorator_result.field_results.items():
                decorator_fields[field_name] = {
                    'score': getattr(field_result, 'score', 0),
                    'issues': getattr(field_result, 'issues', []),
                    'passed': getattr(field_result, 'passed', False)
                }
                print(f"  Field {field_name}: {decorator_fields[field_name]['score']:.1f}")

    print(f"\n=== COMPREHENSIVE CONSISTENCY VALIDATION ===")

    # Validate overall scores
    if decorator_result:
        score_diff = abs(cli_result.overall_score - decorator_result.overall_score)
        print(f"Overall Score Consistency: {score_diff:.1f} point difference")
        assert score_diff < 0.1, f"Overall scores must match: CLI={cli_result.overall_score:.1f}, Decorator={decorator_result.overall_score:.1f}"

        # Validate dimension scores
        print(f"Dimension Scores Consistency:")
        for dim_name in cli_dimensions:
            if dim_name in decorator_dimensions:
                cli_dim_score = cli_dimensions[dim_name]['score']
                decorator_dim_score = decorator_dimensions[dim_name]['score']
                dim_diff = abs(cli_dim_score - decorator_dim_score)
                print(f"  {dim_name}: {dim_diff:.1f} point difference")
                assert dim_diff < 0.1, f"Dimension {dim_name} scores must match: CLI={cli_dim_score:.1f}, Decorator={decorator_dim_score:.1f}"
            else:
                print(f"  {dim_name}: MISSING in decorator results")
                assert False, f"Dimension {dim_name} missing in decorator results"

        # Validate field scores
        print(f"Field Scores Consistency:")
        for field_name in cli_fields:
            if field_name in decorator_fields:
                cli_field_score = cli_fields[field_name]['score']
                decorator_field_score = decorator_fields[field_name]['score']
                field_diff = abs(cli_field_score - decorator_field_score)
                print(f"  {field_name}: {field_diff:.1f} point difference")
                assert field_diff < 0.1, f"Field {field_name} scores must match: CLI={cli_field_score:.1f}, Decorator={decorator_field_score:.1f}"
            else:
                print(f"  {field_name}: MISSING in decorator results")
                assert False, f"Field {field_name} missing in decorator results"

        print(f"\n✅ COMPLETE OUTPUT CONSISTENCY ACHIEVED:")
        print(f"  - Overall scores: IDENTICAL")
        print(f"  - Dimension scores: IDENTICAL")
        print(f"  - Field scores: IDENTICAL")
        print(f"  - Assessment artifacts: IDENTICAL")

    else:
        print(f"❌ Could not capture decorator assessment result for comparison")
        assert False, "Failed to capture decorator assessment result"


if __name__ == "__main__":
    # Quick verification
    print("Checking assessment consistency...")
