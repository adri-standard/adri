"""
Shared test configuration for ADRI tests.

Provides common fixtures, utilities, and configuration for all ADRI tests.
Supports both the legacy adri/ imports and new src/adri/ imports during migration.
"""

import os
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
import pytest
import yaml

# Add src directory to Python path for testing the new structure
src_path = Path(__file__).parent.parent / "src"
if src_path.exists():
    sys.path.insert(0, str(src_path))

# Set up test environment variables
os.environ["ADRI_ENV"] = "TEST"
os.environ["ADRI_STANDARDS_PATH"] = str(Path(__file__).parent / "fixtures" / "standards")


@pytest.fixture
def sample_data():
    """Provide sample data for testing."""
    return pd.DataFrame({
        "name": ["Alice", "Bob", "Charlie", None],
        "age": [25, 30, 35, 28],
        "email": ["alice@test.com", "bob@test.com", "invalid-email", "charlie@test.com"],
        "salary": [50000, 60000, 70000, 55000]
    })


@pytest.fixture
def sample_data_dict():
    """Provide sample data as list of dictionaries."""
    return [
        {"name": "Alice", "age": 25, "email": "alice@test.com", "salary": 50000},
        {"name": "Bob", "age": 30, "email": "bob@test.com", "salary": 60000},
        {"name": "Charlie", "age": 35, "email": "invalid-email", "salary": 70000},
        {"name": None, "age": 28, "email": "charlie@test.com", "salary": 55000}
    ]


@pytest.fixture
def sample_standard():
    """Provide a sample ADRI standard."""
    return {
        "standards": {
            "id": "test_standard",
            "name": "Test Standard",
            "version": "1.0.0",
            "authority": "ADRI Framework",
            "description": "Test standard for unit tests"
        },
        "requirements": {
            "overall_minimum": 75.0,
            "field_requirements": {
                "name": {
                    "type": "string",
                    "nullable": False
                },
                "age": {
                    "type": "integer",
                    "nullable": False,
                    "min_value": 0,
                    "max_value": 120
                },
                "email": {
                    "type": "string",
                    "nullable": False,
                    "pattern": r"^[^@]+@[^@]+\.[^@]+$"
                },
                "salary": {
                    "type": "integer",
                    "nullable": False,
                    "min_value": 0
                }
            },
            "dimension_requirements": {
                "validity": {"minimum_score": 15.0},
                "completeness": {"minimum_score": 15.0},
                "consistency": {"minimum_score": 12.0},
                "freshness": {"minimum_score": 15.0},
                "plausibility": {"minimum_score": 12.0}
            }
        }
    }


@pytest.fixture
def sample_standard_file(tmp_path, sample_standard):
    """Create a temporary standard file."""
    standard_file = tmp_path / "test_standard.yaml"
    with open(standard_file, 'w') as f:
        yaml.dump(sample_standard, f)
    return str(standard_file)


@pytest.fixture
def sample_csv_file(tmp_path, sample_data):
    """Create a temporary CSV file with sample data."""
    csv_file = tmp_path / "test_data.csv"
    sample_data.to_csv(csv_file, index=False)
    return str(csv_file)


@pytest.fixture
def sample_json_file(tmp_path, sample_data_dict):
    """Create a temporary JSON file with sample data."""
    json_file = tmp_path / "test_data.json"
    import json
    with open(json_file, 'w') as f:
        json.dump(sample_data_dict, f)
    return str(json_file)


@pytest.fixture
def temp_config_dir(tmp_path):
    """Create a temporary configuration directory."""
    config_dir = tmp_path / "config_test"
    config_dir.mkdir()

    # Create ADRI subdirectories
    for env in ["dev", "prod"]:
        for subdir in ["standards", "assessments", "training-data"]:
            (config_dir / "ADRI" / env / subdir).mkdir(parents=True)

    return config_dir


@pytest.fixture
def sample_config(temp_config_dir):
    """Create a sample ADRI configuration."""
    config = {
        "adri": {
            "version": "4.0.0",
            "project_name": "test_project",
            "default_environment": "development",
            "environments": {
                "development": {
                    "paths": {
                        "standards": str(temp_config_dir / "ADRI" / "dev" / "standards"),
                        "assessments": str(temp_config_dir / "ADRI" / "dev" / "assessments"),
                        "training_data": str(temp_config_dir / "ADRI" / "dev" / "training-data"),
                    },
                    "protection": {
                        "default_failure_mode": "warn",
                        "default_min_score": 75,
                    },
                },
                "production": {
                    "paths": {
                        "standards": str(temp_config_dir / "ADRI" / "prod" / "standards"),
                        "assessments": str(temp_config_dir / "ADRI" / "prod" / "assessments"),
                        "training_data": str(temp_config_dir / "ADRI" / "prod" / "training-data"),
                    },
                    "protection": {
                        "default_failure_mode": "raise",
                        "default_min_score": 85,
                    },
                }
            }
        }
    }

    config_file = temp_config_dir / "adri-config.yaml"
    with open(config_file, 'w') as f:
        yaml.dump(config, f)

    return config


@pytest.fixture
def mock_assessment_result():
    """Provide a mock assessment result for testing."""
    class MockDimensionScore:
        def __init__(self, score):
            self.score = score

    class MockAssessmentResult:
        def __init__(self):
            self.overall_score = 82.5
            self.passed = True
            self.dimension_scores = {
                "validity": MockDimensionScore(16.5),
                "completeness": MockDimensionScore(18.0),
                "consistency": MockDimensionScore(16.0),
                "freshness": MockDimensionScore(17.0),
                "plausibility": MockDimensionScore(15.0)
            }
            self.standard_id = "test_standard"
            self.rule_execution_log = []
            self.field_analysis = {}

        def to_dict(self):
            return {
                "overall_score": self.overall_score,
                "passed": self.passed,
                "dimension_scores": {
                    k: v.score for k, v in self.dimension_scores.items()
                }
            }

        def to_standard_dict(self):
            return self.to_dict()

    return MockAssessmentResult()


@pytest.fixture(autouse=True)
def clean_environment():
    """Clean up environment before and after each test."""
    # Setup
    original_env = os.environ.copy()

    yield

    # Cleanup - restore original environment
    os.environ.clear()
    os.environ.update(original_env)


# Test utilities
def create_test_dataframe(rows: int = 100, include_nulls: bool = True) -> pd.DataFrame:
    """Create a test DataFrame with optional null values."""
    import random

    data = []
    for i in range(rows):
        row = {
            "id": i + 1,
            "name": f"Person_{i+1}" if not (include_nulls and random.random() < 0.1) else None,
            "age": random.randint(18, 80) if not (include_nulls and random.random() < 0.05) else None,
            "email": f"person{i+1}@test.com" if not (include_nulls and random.random() < 0.08) else None,
            "score": random.uniform(0, 100) if not (include_nulls and random.random() < 0.03) else None,
        }
        data.append(row)

    return pd.DataFrame(data)


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
        "standards": {
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


class TestDataHelper:
    """Helper class for creating test data."""

    @staticmethod
    def create_quality_data(rows: int = 50) -> pd.DataFrame:
        """Create high-quality test data."""
        return pd.DataFrame({
            "customer_id": range(1, rows + 1),
            "name": [f"Customer {i}" for i in range(1, rows + 1)],
            "email": [f"customer{i}@example.com" for i in range(1, rows + 1)],
            "age": [25 + (i % 50) for i in range(rows)],
            "balance": [1000.0 + (i * 100) for i in range(rows)]
        })

    @staticmethod
    def create_poor_quality_data(rows: int = 50) -> pd.DataFrame:
        """Create poor-quality test data with issues."""
        data = []
        for i in range(rows):
            row = {
                "customer_id": i + 1,
                "name": None if i % 5 == 0 else f"Customer {i}",  # 20% missing
                "email": "invalid-email" if i % 4 == 0 else f"customer{i}@example.com",  # 25% invalid
                "age": -5 if i % 10 == 0 else (25 + (i % 50)),  # 10% invalid ages
                "balance": None if i % 8 == 0 else (1000.0 + (i * 100))  # 12.5% missing
            }
            data.append(row)

        return pd.DataFrame(data)
