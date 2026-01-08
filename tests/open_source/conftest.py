"""
Open Source Test Configuration for ADRI.

This is a minimal, self-contained conftest.py for the open source ADRI package.
It provides essential fixtures without depending on enterprise test utilities.
"""

import os
import sys
from pathlib import Path
from typing import Any, Dict

import pytest
import pandas as pd

# Ensure src directory is in path
src_path = Path(__file__).parent.parent.parent / "src"
if src_path.exists():
    sys.path.insert(0, str(src_path))

# Set up test environment
os.environ["ADRI_ENV"] = "TEST"
os.environ["ADRI_LOG_LEVEL"] = "DEBUG"


# ============================================================================
# Core Data Fixtures
# ============================================================================

@pytest.fixture
def sample_data():
    """Provide sample data for testing."""
    return pd.DataFrame({
        "id": [1, 2, 3, 4, 5],
        "name": ["Alice", "Bob", "Charlie", "Diana", "Eve"],
        "email": ["alice@example.com", "bob@example.com", "charlie@example.com",
                  "diana@example.com", "eve@example.com"],
        "age": [25, 30, 35, 28, 32],
        "active": [True, True, False, True, True]
    })


@pytest.fixture
def sample_data_dict(sample_data):
    """Provide sample data as list of dicts."""
    return sample_data.to_dict('records')


@pytest.fixture
def high_quality_data():
    """Provide high-quality sample data for testing."""
    return pd.DataFrame({
        "id": [1, 2, 3, 4, 5],
        "name": ["Alice Smith", "Bob Jones", "Charlie Brown", "Diana Prince", "Eve Wilson"],
        "email": ["alice@company.com", "bob@company.com", "charlie@company.com",
                  "diana@company.com", "eve@company.com"],
        "department": ["Engineering", "Marketing", "Sales", "Engineering", "Marketing"],
        "salary": [75000, 65000, 55000, 80000, 70000],
        "hire_date": pd.to_datetime(["2020-01-15", "2019-06-01", "2021-03-10",
                                      "2018-09-20", "2022-01-05"]),
        "active": [True, True, True, True, True]
    })


@pytest.fixture
def low_quality_data():
    """Provide low-quality sample data for testing validation failures."""
    return pd.DataFrame({
        "id": [1, None, 3, 4, 5],
        "name": ["Alice", "", None, "Diana", "Eve"],
        "email": ["invalid-email", "bob@example.com", "charlie", "", "eve@example.com"],
        "age": [-5, 30, 200, None, 32],
        "active": [True, "yes", False, None, True]
    })


# ============================================================================
# Standard/Contract Fixtures
# ============================================================================

@pytest.fixture
def sample_standard():
    """Provide a sample ADRI standard for testing."""
    return {
        "contracts": {
            "id": "test_standard",
            "name": "Test Standard",
            "version": "1.0.0",
            "authority": "ADRI Framework"
        },
        "schema": {
            "type": "object",
            "properties": {
                "id": {"type": "integer"},
                "name": {"type": "string"},
                "email": {"type": "string", "format": "email"},
                "age": {"type": "integer", "minimum": 0, "maximum": 150}
            },
            "required": ["id", "name"]
        },
        "requirements": {
            "overall_minimum": 75.0,
            "dimension_requirements": {
                "validity": {"minimum": 15},
                "completeness": {"minimum": 15},
                "consistency": {"minimum": 15}
            }
        }
    }


@pytest.fixture
def comprehensive_standard():
    """Provide a comprehensive ADRI standard with all dimensions."""
    return {
        "contracts": {
            "id": "comprehensive_standard",
            "name": "Comprehensive Test Standard",
            "version": "2.0.0",
            "authority": "ADRI Framework"
        },
        "schema": {
            "type": "object",
            "properties": {
                "id": {"type": "integer"},
                "name": {"type": "string", "minLength": 1, "maxLength": 100},
                "email": {"type": "string", "format": "email"},
                "department": {"type": "string", "enum": ["Engineering", "Marketing", "Sales", "HR"]},
                "salary": {"type": "number", "minimum": 0},
                "hire_date": {"type": "string", "format": "date"},
                "active": {"type": "boolean"}
            },
            "required": ["id", "name", "email"]
        },
        "requirements": {
            "overall_minimum": 80.0,
            "dimension_requirements": {
                "validity": {"minimum": 16},
                "completeness": {"minimum": 16},
                "consistency": {"minimum": 16},
                "freshness": {"minimum": 14},
                "plausibility": {"minimum": 14}
            }
        }
    }


# ============================================================================
# Configuration Fixtures
# ============================================================================

@pytest.fixture
def complete_config():
    """Provide complete ADRI configuration."""
    return {
        "adri": {
            "version": "1.0",
            "environment": "test"
        },
        "logging": {
            "enabled": True,
            "log_dir": "./test_logs",
            "flush_interval": 60
        },
        "validation": {
            "min_score": 75,
            "on_failure": "raise",
            "verbose": True
        }
    }


@pytest.fixture
def temp_workspace(tmp_path):
    """Provide temporary workspace directory."""
    workspace = tmp_path / "adri_workspace"
    workspace.mkdir(parents=True, exist_ok=True)

    # Create standard subdirectories
    (workspace / "contracts").mkdir()
    (workspace / "logs").mkdir()
    (workspace / "config").mkdir()

    return workspace


# ============================================================================
# Environment & Isolation Fixtures
# ============================================================================

@pytest.fixture
def isolated_working_dir(tmp_path):
    """Provide isolated working directory with automatic cleanup."""
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
    """Ensure working directory is valid before and after each test."""
    project_root = Path(__file__).parent.parent.absolute()

    try:
        os.getcwd()
    except (OSError, FileNotFoundError):
        os.chdir(str(project_root))

    original_cwd = os.getcwd()

    yield

    try:
        os.getcwd()
    except (OSError, FileNotFoundError):
        os.chdir(str(project_root))
    else:
        try:
            if os.path.exists(original_cwd):
                os.chdir(original_cwd)
            else:
                os.chdir(str(project_root))
        except (OSError, FileNotFoundError):
            os.chdir(str(project_root))


@pytest.fixture(autouse=True)
def clean_adri_env_vars():
    """Clean up ADRI environment variables after each test."""
    preserved_vars = {
        'ADRI_ENV': os.environ.get('ADRI_ENV'),
        'ADRI_LOG_LEVEL': os.environ.get('ADRI_LOG_LEVEL'),
    }

    yield

    for key in list(os.environ.keys()):
        if key.startswith('ADRI_'):
            os.environ.pop(key, None)

    for key, value in preserved_vars.items():
        if value is not None:
            os.environ[key] = value


# ============================================================================
# Test Utility Functions
# ============================================================================

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


# ============================================================================
# Pytest Configuration
# ============================================================================

def pytest_configure(config):
    """Configure pytest for ADRI testing."""
    config.addinivalue_line("markers", "unit: Unit test")
    config.addinivalue_line("markers", "integration: Integration test")
    config.addinivalue_line("markers", "performance: Performance test")
    config.addinivalue_line("markers", "slow: Slow running test")


def pytest_sessionstart(session):
    """Initialize test session."""
    print(f"\n=== ADRI Open Source Test Suite ===")


def pytest_sessionfinish(session, exitstatus):
    """Finalize test session."""
    if exitstatus == 0:
        print(f"\n✓ All tests passed")
    else:
        print(f"\n✗ Some tests failed")
