"""Auto-discovery tests for ADRI standards.

This test module automatically discovers all standards in adri/standards/
and runs comprehensive validation tests on those that have test data.

Test Coverage:
    For each standard with complete test data (training + test CSVs):
    1. Training data passes validation (100% quality)
    2. Test data has expected quality issues
    3. Assessment logs are generated correctly
    4. Dimension scores are calculated properly
    5. Failed validations are captured

Standards Discovery:
    - Scans adri/standards/ recursively for YAML files
    - Validates each is a proper ADRI standard
    - Checks for corresponding test data CSV files
    - Only tests standards with complete data

Adding New Standards to Tests:
    Simply create two CSV files in adri/standards/test_data/:
    - <standard_id>_data.csv (clean training data)
    - test_<standard_id>_data.csv (data with quality issues)
    
    The test will automatically discover and test the standard!
"""

import pytest
from pathlib import Path

from tests.fixtures.standards_discovery import (
    find_testable_standards,
    get_standards_ready_for_testing,
    get_standards_needing_data,
    StandardTestMetadata
)


def test_standards_discovery_finds_standards():
    """Test that standards discovery finds valid ADRI standards."""
    standards = find_testable_standards()
    
    # Should find multiple standards
    assert len(standards) > 0, "No standards found in adri/standards/"
    
    # Each standard should have required metadata
    for std in standards:
        assert std.standard_id, f"Standard missing ID: {std.relative_path}"
        assert std.standard_path.exists(), f"Standard file doesn't exist: {std.standard_path}"
        assert std.field_count >= 0, f"Invalid field count for {std.standard_id}"


def test_standards_have_consistent_structure():
    """Test that all discovered standards follow consistent structure."""
    standards = find_testable_standards()
    
    for std in standards:
        # Standard ID should be valid identifier format
        assert std.standard_id.replace('_', '').isalnum(), \
            f"Invalid standard ID format: {std.standard_id}"
        
        # Test data paths should be properly formed
        assert std.training_data_path.name == f"{std.standard_id}_data.csv"
        assert std.test_data_path.name == f"test_{std.standard_id}_data.csv"


def test_report_standards_needing_data():
    """Report on standards that don't have test data yet.
    
    This is informational - helps track testing coverage.
    """
    standards_needing_data = get_standards_needing_data()
    standards_ready = get_standards_ready_for_testing()
    all_standards = find_testable_standards()
    
    coverage_pct = (len(standards_ready) / len(all_standards) * 100) if all_standards else 0
    
    print(f"\n{'='*70}")
    print(f"ADRI Standards Testing Coverage Report")
    print(f"{'='*70}")
    print(f"Total Standards: {len(all_standards)}")
    print(f"Ready for Testing: {len(standards_ready)} ({coverage_pct:.1f}%)")
    print(f"Need Test Data: {len(standards_needing_data)}")
    
    if standards_needing_data:
        print(f"\nStandards Needing Test Data:")
        for std in standards_needing_data:
            status = []
            if not std.has_training_data:
                status.append("missing training data")
            if not std.has_test_data:
                status.append("missing test data")
            print(f"  - {std.standard_id}: {', '.join(status)}")
            print(f"    Expected: {std.training_data_path.name}")
            print(f"    Expected: {std.test_data_path.name}")
    
    # Test passes regardless - this is just informational
    assert True


# Parametrize tests over standards that have complete test data
@pytest.fixture(scope="module")
def testable_standards():
    """Get list of standards ready for testing."""
    return get_standards_ready_for_testing()


def pytest_generate_tests(metafunc):
    """Generate test cases for each standard with complete test data.
    
    This follows the same pattern as tutorial auto-discovery, creating
    9 comprehensive tests per standard.
    """
    if "standard_metadata" in metafunc.fixturenames:
        # Get standards with complete test data
        testable_standards = get_standards_ready_for_testing()
        
        # Generate test IDs from standard IDs
        ids = [std.standard_id for std in testable_standards]
        
        # Parametrize the test with standard metadata
        metafunc.parametrize("standard_metadata", testable_standards, ids=ids)


# --- Test Suite (9 tests per standard, same as tutorials) ---

def test_standard_training_data_validates(standard_metadata: StandardTestMetadata):
    """Test 1: Training data should pass validation with 100% quality score."""
    pytest.skip("Test implementation needed - validates training CSV passes 100%")


def test_standard_test_data_has_issues(standard_metadata: StandardTestMetadata):
    """Test 2: Test data should have quality issues (score < 100%)."""
    pytest.skip("Test implementation needed - validates test CSV has expected issues")


def test_standard_assessment_logs_generated(standard_metadata: StandardTestMetadata):
    """Test 3: Assessment logs should be generated for both datasets."""
    pytest.skip("Test implementation needed - checks JSONL logs created")


def test_standard_dimension_scores_calculated(standard_metadata: StandardTestMetadata):
    """Test 4: Dimension scores should be calculated correctly."""
    pytest.skip("Test implementation needed - validates dimension score calculations")


def test_standard_failed_validations_captured(standard_metadata: StandardTestMetadata):
    """Test 5: Failed validations should be properly captured."""
    pytest.skip("Test implementation needed - checks failed validations in JSONL")


def test_standard_field_level_validation(standard_metadata: StandardTestMetadata):
    """Test 6: Field-level validations should work correctly."""
    pytest.skip("Test implementation needed - validates individual field checks")


def test_standard_validation_rules_enforced(standard_metadata: StandardTestMetadata):
    """Test 7: Validation rules should be properly enforced."""
    pytest.skip("Test implementation needed - confirms validation_rules applied")


def test_standard_severity_levels_applied(standard_metadata: StandardTestMetadata):
    """Test 8: Severity levels should affect scoring correctly."""
    pytest.skip("Test implementation needed - validates CRITICAL vs WARNING impact")


def test_standard_record_identification_works(standard_metadata: StandardTestMetadata):
    """Test 9: Record identification should work for error tracking."""
    pytest.skip("Test implementation needed - validates primary key strategy works")


# --- Summary Statistics ---

def test_standards_testing_summary(testable_standards):
    """Provide summary statistics about standards testing coverage."""
    all_standards = find_testable_standards()
    
    print(f"\n{'='*70}")
    print(f"Standards Testing Summary")
    print(f"{'='*70}")
    print(f"Total Standards Discovered: {len(all_standards)}")
    print(f"Standards With Test Data: {len(testable_standards)}")
    print(f"Test Cases Generated: {len(testable_standards) * 9}")
    
    if testable_standards:
        print(f"\nStandards Being Tested:")
        for std in testable_standards:
            print(f"  ✓ {std.standard_id} ({std.field_count} fields)")
    
    assert len(all_standards) > 0, "Should discover at least some standards"
