"""
Shared pytest configuration and fixtures for ADRI Validator tests.
"""

import os
import sys
import pytest
import tempfile
from pathlib import Path
from typing import Generator

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import test utilities
from tests.test_utils import OutputLimiter, TestDataGenerator


# Register custom markers
def pytest_configure(config):
    """Register custom markers for test categorization."""
    config.addinivalue_line(
        "markers", "quick: Fast tests that can run frequently"
    )
    config.addinivalue_line(
        "markers", "performance: Performance tests with large datasets"
    )
    config.addinivalue_line(
        "markers", "stress: Stress tests with extreme conditions"
    )
    config.addinivalue_line(
        "markers", "ci_only: Tests that should only run in CI environments"
    )
    config.addinivalue_line(
        "markers", "audit: Tests for audit logging functionality"
    )
    config.addinivalue_line(
        "markers", "csv_output: Tests for CSV output functionality"
    )


# Configure output limiting for all tests
@pytest.fixture(autouse=True)
def limit_test_output(monkeypatch):
    """Automatically limit output for all tests to prevent token explosion."""
    # Set conservative defaults if not already set
    if 'ADRI_TEST_MAX_OUTPUT' not in os.environ:
        monkeypatch.setenv('ADRI_TEST_MAX_OUTPUT', '1000')
    if 'ADRI_TEST_MAX_DF_ROWS' not in os.environ:
        monkeypatch.setenv('ADRI_TEST_MAX_DF_ROWS', '10')
    if 'ADRI_TEST_MAX_LIST_ITEMS' not in os.environ:
        monkeypatch.setenv('ADRI_TEST_MAX_LIST_ITEMS', '10')


# Shared fixtures
@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def sample_dataframe():
    """Generate a small sample DataFrame for quick tests."""
    return TestDataGenerator.generate_dataset(100, 5, test_type='quick')


@pytest.fixture
def output_limiter():
    """Provide output limiter for tests."""
    return OutputLimiter


@pytest.fixture
def test_data_generator():
    """Provide test data generator for tests."""
    return TestDataGenerator


# Performance test specific configuration
@pytest.fixture(scope="session", autouse=True)
def configure_performance_tests():
    """Configure settings for performance tests."""
    if os.environ.get('ADRI_RUN_PERFORMANCE_TESTS'):
        # Allow larger datasets for explicit performance testing
        os.environ['ADRI_TEST_MAX_ROWS'] = '50000'
    else:
        # Limit dataset sizes by default
        os.environ['ADRI_TEST_MAX_ROWS'] = '1000'


# Hook to skip expensive tests by default
def pytest_collection_modifyitems(config, items):
    """Modify test collection to skip expensive tests by default."""
    skip_performance = pytest.mark.skip(reason="Performance test - run with --performance")
    skip_stress = pytest.mark.skip(reason="Stress test - run with --stress")
    
    for item in items:
        # Skip performance tests unless explicitly requested
        if "performance" in item.keywords and not config.getoption("--performance", default=False):
            item.add_marker(skip_performance)
        
        # Skip stress tests unless explicitly requested
        if "stress" in item.keywords and not config.getoption("--stress", default=False):
            item.add_marker(skip_stress)


def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--performance",
        action="store_true",
        default=False,
        help="Run performance tests"
    )
    parser.addoption(
        "--stress",
        action="store_true",
        default=False,
        help="Run stress tests"
    )
    parser.addoption(
        "--all-tests",
        action="store_true",
        default=False,
        help="Run all tests including performance and stress"
    )
