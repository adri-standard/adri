"""
Modern Test Configuration for ADRI Test Suite.

Provides comprehensive test configuration with multi-dimensional quality measurement,
modern fixtures integration, and production-ready testing infrastructure.

No backward compatibility - uses only src/adri/* imports and modern patterns.
Supports 80% coverage target and component-specific quality requirements.
"""

import os
import sys
from pathlib import Path
from typing import Any, Dict

import pytest

# Ensure src directory is in path for modern imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

# Import modern fixtures and quality framework
from tests.quality_framework import QualityFramework, ComponentTester, quality_framework
from tests.fixtures.modern_fixtures import *  # Import all modern fixtures
from tests.fixtures.tutorial_scenarios import tutorial_project, invoice_scenario  # Import tutorial fixtures
from tests.fixtures.standards_cache_cleanup import clear_standards_cache  # Import cache cleanup fixture

# Set up modern test environment
os.environ["ADRI_ENV"] = "TEST"
os.environ["ADRI_LOG_LEVEL"] = "DEBUG"
os.environ["ADRI_CONTRACTS_DIR"] = str(Path(__file__).parent / "fixtures" / "standards")  # Single unified standards directory
os.environ["ADRI_COVERAGE_TARGET"] = "80"  # Production coverage target


# Quality Framework Integration

@pytest.fixture(scope="session")
def global_quality_framework():
    """Provide global quality framework for test session."""
    return quality_framework


@pytest.fixture
def component_tester():
    """Factory fixture for creating component testers."""
    def _create_tester(component_name: str):
        return ComponentTester(component_name, quality_framework)
    return _create_tester


# Legacy compatibility fixtures (delegated to modern_fixtures.py)
# These provide backward compatibility for existing tests during migration

@pytest.fixture
def sample_data(high_quality_data):
    """Legacy compatibility - use high_quality_data."""
    return high_quality_data


@pytest.fixture
def sample_data_dict(high_quality_data):
    """Legacy compatibility - convert to dict format."""
    return high_quality_data.to_dict('records')


@pytest.fixture
def sample_standard(comprehensive_standard):
    """Legacy compatibility - use comprehensive_standard."""
    return comprehensive_standard


@pytest.fixture
def temp_config_dir(temp_workspace):
    """Legacy compatibility - use temp_workspace."""
    return temp_workspace


@pytest.fixture
def sample_config(complete_config):
    """Legacy compatibility - use complete_config."""
    return complete_config


# Modern Test Utilities

@pytest.fixture
def safe_temp_directory():
    """Create a safe temporary directory with robust cleanup for CI environments."""
    import tempfile
    import shutil
    import time
    import gc

    temp_dir = tempfile.mkdtemp(prefix="adri_test_")
    original_cwd = None

    try:
        # Store original directory safely
        try:
            original_cwd = os.getcwd()
        except (OSError, FileNotFoundError):
            original_cwd = str(Path(__file__).parent.parent.absolute())

        yield temp_dir
    finally:
        # Safe cleanup and restoration
        try:
            if original_cwd and os.path.exists(original_cwd):
                os.chdir(original_cwd)
            else:
                os.chdir(str(Path(__file__).parent.parent.absolute()))
        except (OSError, FileNotFoundError):
            # Fallback to a safe directory
            os.chdir("/tmp" if os.path.exists("/tmp") else ".")

        # Enhanced Windows-safe cleanup
        if os.path.exists(temp_dir):
            # Force garbage collection to release file handles on Windows
            gc.collect()

            # Give Windows time to release file handles
            time.sleep(0.1)

            # Multiple cleanup attempts for Windows
            for attempt in range(3):
                try:
                    # First try: standard removal
                    shutil.rmtree(temp_dir, ignore_errors=False)
                    break
                except (OSError, PermissionError):
                    if attempt < 2:  # Not the last attempt
                        time.sleep(0.2)  # Wait longer between attempts
                        gc.collect()  # Try to release handles again
                    else:
                        # Final attempt: force removal with ignore_errors
                        try:
                            shutil.rmtree(temp_dir, ignore_errors=True)
                        except:
                            pass  # Ultimate fallback - ignore all errors


@pytest.fixture
def isolated_working_directory(safe_temp_directory):
    """Provide an isolated working directory for tests that change cwd."""
    original_cwd = None

    try:
        # Store and change to temp directory
        try:
            original_cwd = os.getcwd()
        except (OSError, FileNotFoundError):
            original_cwd = str(Path(__file__).parent.parent.absolute())

        os.chdir(safe_temp_directory)
        yield safe_temp_directory
    finally:
        # Restore original directory
        try:
            if original_cwd and os.path.exists(original_cwd):
                os.chdir(original_cwd)
            else:
                os.chdir(str(Path(__file__).parent.parent.absolute()))
        except (OSError, FileNotFoundError):
            os.chdir("/tmp" if os.path.exists("/tmp") else ".")


@pytest.fixture
def isolated_working_dir(tmp_path):
    """Provide isolated working directory with automatic cleanup.

    This fixture ensures working directory changes are always cleaned up,
    even if tests fail. Uses pytest's built-in tmp_path for isolation.
    """
    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        yield tmp_path
    finally:
        try:
            os.chdir(original_cwd)
        except Exception:
            pass


@pytest.fixture(autouse=True)
def ensure_valid_cwd():
    """Ensure working directory is valid before and after each test.

    This fixture prevents test pollution from os.chdir() usage across the suite.
    """
    # Get project root as a safe fallback
    project_root = Path(__file__).parent.parent.absolute()

    # Before test: ensure we're in a valid directory
    try:
        os.getcwd()
    except (OSError, FileNotFoundError):
        os.chdir(str(project_root))

    original_cwd = os.getcwd()

    yield

    # After test: restore to a valid directory
    try:
        os.getcwd()
    except (OSError, FileNotFoundError):
        os.chdir(str(project_root))
    else:
        # Try to restore original, but don't fail if it doesn't exist
        try:
            if os.path.exists(original_cwd):
                os.chdir(original_cwd)
            else:
                os.chdir(str(project_root))
        except (OSError, FileNotFoundError):
            os.chdir(str(project_root))


@pytest.fixture(autouse=True)
def clean_adri_env_vars():
    """Clean up ADRI environment variables after each test.

    This fixture prevents environment variable pollution across tests
    by removing any ADRI_* variables that tests may have set.
    Preserves the test environment variables set in conftest.py.
    """
    # Store initial test environment variables
    preserved_vars = {
        'ADRI_ENV': os.environ.get('ADRI_ENV'),
        'ADRI_LOG_LEVEL': os.environ.get('ADRI_LOG_LEVEL'),
        'ADRI_CONTRACTS_DIR': os.environ.get('ADRI_CONTRACTS_DIR'),
        'ADRI_COVERAGE_TARGET': os.environ.get('ADRI_COVERAGE_TARGET'),
    }

    yield

    # Cleanup: Remove all ADRI_* environment variables
    for key in list(os.environ.keys()):
        if key.startswith('ADRI_'):
            os.environ.pop(key, None)

    # Restore preserved test environment variables
    for key, value in preserved_vars.items():
        if value is not None:
            os.environ[key] = value


@pytest.fixture
def ci_environment_detector():
    """Detect and adapt to CI environment characteristics."""
    def is_ci():
        return any(key in os.environ for key in [
            'CI', 'CONTINUOUS_INTEGRATION', 'GITHUB_ACTIONS',
            'TRAVIS', 'CIRCLECI', 'JENKINS_URL', 'GITLAB_CI'
        ])

    def get_parallel_workers():
        """Get number of parallel test workers in CI."""
        if 'PYTEST_XDIST_WORKER' in os.environ:
            return os.environ.get('PYTEST_XDIST_WORKER_COUNT', '1')
        return '1'

    return {
        'is_ci': is_ci(),
        'parallel_workers': get_parallel_workers(),
        'worker_id': os.environ.get('PYTEST_XDIST_WORKER', 'main')
    }


def assert_dimension_scores_valid(dimension_scores: Dict[str, Any]):
    """Assert that dimension scores are in valid format."""
    expected_dimensions = ["validity", "completeness", "consistency", "freshness", "plausibility"]

    for dim in expected_dimensions:
        assert dim in dimension_scores, f"Missing dimension: {dim}"

        score_obj = dimension_scores[dim]
        if hasattr(score_obj, "score"):
            score = score_obj.score
        else:
            score = score_obj

        assert 0 <= score <= 20, f"Score for {dim} out of range: {score}"


def assert_quality_target_met(component_name: str, metrics: Dict[str, float]):
    """Assert that component meets quality targets."""
    from tests.quality_framework import QualityMetrics

    quality_metrics: QualityMetrics = {
        "line_coverage": metrics.get("line_coverage", 0.0),
        "integration_tests": metrics.get("integration_tests", 0.0),
        "error_handling": metrics.get("error_handling", 0.0),
        "performance": metrics.get("performance", 0.0),
        "overall_score": metrics.get("overall_score", 0.0)
    }

    assert quality_framework.validate_component_quality(component_name, quality_metrics), \
        f"Component {component_name} does not meet quality targets"


def create_minimal_standard(name: str = "test") -> Dict[str, Any]:
    """Create a minimal valid ADRI standard."""
    return {
        "contracts": {
            "id": f"{name}_standard",
            "name": f"{name.title()} Standard",
            "version": "1.0.0",
            "authority": "ADRI Framework"
        },
        "requirements": {
            "overall_minimum": 75.0,
            "field_requirements": {},
            "dimension_requirements": {}
        }
    }


# Pytest Configuration

def pytest_configure(config):
    """Configure pytest for modern ADRI testing."""
    # Add custom markers for quality dimensions
    config.addinivalue_line("markers", "unit: Unit test - individual component functionality")
    config.addinivalue_line("markers", "integration: Integration test - component interactions")
    config.addinivalue_line("markers", "performance: Performance test - speed and efficiency")
    config.addinivalue_line("markers", "error_handling: Error handling test - failure scenarios")
    config.addinivalue_line("markers", "end_to_end: End-to-end test - complete workflows")

    # Component type markers
    config.addinivalue_line("markers", "business_critical: Business critical component (90%+ target)")
    config.addinivalue_line("markers", "system_infrastructure: System infrastructure component (80%+ target)")
    config.addinivalue_line("markers", "data_processing: Data processing component (75%+ target)")


def pytest_collection_modifyitems(config, items):
    """Modify test collection for quality framework integration."""
    for item in items:
        # Auto-mark tests based on path
        if "test_decorator" in str(item.fspath) or "test_guard" in str(item.fspath) or "test_validator_engine" in str(item.fspath):
            item.add_marker(pytest.mark.business_critical)
        elif "test_config" in str(item.fspath) or "test_standards" in str(item.fspath) or "test_cli" in str(item.fspath):
            item.add_marker(pytest.mark.system_infrastructure)
        elif "test_analysis" in str(item.fspath) or "test_logging" in str(item.fspath):
            item.add_marker(pytest.mark.data_processing)


def pytest_sessionstart(session):
    """Initialize quality framework for test session."""
    print(f"\n=== ADRI Test Framework Modernization ===")
    print(f"Coverage Target: 80% (Production Ready)")
    print(f"Quality Framework: Multi-dimensional measurement enabled")
    print(f"Legacy Compatibility: Disabled - Modern patterns only")


def pytest_sessionfinish(session, exitstatus):
    """Generate quality report at end of test session."""
    if quality_framework.test_results:
        print(f"\n=== Quality Framework Report ===")
        report = quality_framework.generate_quality_report()

        print(f"Overall Coverage: {report['overall_coverage']}%")
        print(f"Components Tested: {report['components_tested']}")
        print(f"Components Passing: {report['components_passing']}")
        print(f"Pass Rate: {report['summary']['pass_rate']}%")
        print(f"Production Ready: {report['summary']['production_ready']}")

        if not report['summary']['production_ready']:
            print(f"\n⚠️  Quality targets not met - see component details for gaps")
