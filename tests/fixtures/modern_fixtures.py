"""
Modern Fixtures Framework for ADRI Test Suite.

Provides comprehensive, standardized fixtures for testing all ADRI components
without any legacy backward compatibility. Supports multi-dimensional quality
testing with error simulation, performance monitoring, and component-specific
test data generation.

Replaces legacy patterns with modern pytest fixtures optimized for:
- Business Critical Components (90%+ quality targets)
- System Infrastructure Components (80%+ quality targets)
- Data Processing Components (75%+ quality targets)

# Tutorial-Based Testing Framework

For realistic end-to-end testing that mirrors actual user workflows, see:
- tests/fixtures/tutorial_scenarios.py - Tutorial-based fixtures and scenarios
- tests/fixtures/TUTORIAL_SCENARIOS.md - Complete documentation and usage examples

The tutorial framework provides:
- Real ADRI tutorial data as test foundation
- CLI-based standard generation (mimics user workflow)
- Name-only standard resolution testing
- Development environment configuration

Example tutorial fixture usage:
    def test_invoice_validation(invoice_scenario):
        # invoice_scenario provides tutorial data and generated standards
        @adri_protected(contract=invoice_scenario['generated_standard_name'])
        def process_invoices(data):
            return data

        clean_data = pd.read_csv(invoice_scenario['training_data_path'])
        result = process_invoices(clean_data)

This module (modern_fixtures.py) focuses on synthetic data generation and
component-level testing, while tutorial_scenarios.py provides realistic
workflow testing with actual tutorial data.
"""

import os
import json
import tempfile
import random
import shutil
import time
import gc
import platform
from pathlib import Path
from typing import Any, Dict, List, Optional, Generator, Tuple
from contextlib import contextmanager
import pandas as pd
import pytest
import yaml

from tests.quality_framework import TestCategory, performance_monitor


class ModernFixtures:
    """Centralized modern fixture definitions for comprehensive testing."""

    @staticmethod
    def create_comprehensive_mock_data(
        rows: int = 100,
        quality_level: str = "high",
        include_edge_cases: bool = True
    ) -> pd.DataFrame:
        """Create comprehensive test data with configurable quality levels."""

        # Base data structure
        data = []

        for i in range(rows):
            # High quality data (90%+ valid)
            if quality_level == "high":
                null_probability = 0.02  # 2% nulls
                invalid_email_prob = 0.01  # 1% invalid emails
                invalid_age_prob = 0.005  # 0.5% invalid ages

            # Medium quality data (70-80% valid)
            elif quality_level == "medium":
                null_probability = 0.1   # 10% nulls
                invalid_email_prob = 0.05  # 5% invalid emails
                invalid_age_prob = 0.02   # 2% invalid ages

            # Low quality data (40-60% valid)
            elif quality_level == "low":
                null_probability = 0.25  # 25% nulls
                invalid_email_prob = 0.15  # 15% invalid emails
                invalid_age_prob = 0.1   # 10% invalid ages

            else:
                raise ValueError(f"Unknown quality level: {quality_level}")

            # Generate record
            row = {
                "customer_id": i + 1,
                "name": None if random.random() < null_probability else f"Customer {i+1}",
                "email": (
                    None if random.random() < null_probability else
                    "invalid-email" if random.random() < invalid_email_prob else
                    f"customer{i+1}@example.com"
                ),
                "age": (
                    None if random.random() < null_probability else
                    -5 if random.random() < invalid_age_prob else
                    random.randint(18, 80)
                ),
                "salary": (
                    None if random.random() < null_probability else
                    random.randint(30000, 150000)
                ),
                "registration_date": (
                    None if random.random() < null_probability else
                    f"2023-{random.randint(1,12):02d}-{random.randint(1,28):02d}"
                ),
                "status": (
                    None if random.random() < null_probability else
                    random.choice(["active", "inactive", "pending", "suspended"])
                )
            }

            # Add edge cases if requested
            if include_edge_cases and i < 10:
                edge_cases = {
                    0: {"name": "", "age": 0},  # Empty name, zero age
                    1: {"name": "A" * 1000, "salary": 0},  # Very long name, zero salary
                    2: {"email": "test@", "age": 150},  # Malformed email, extreme age
                    3: {"customer_id": -1, "status": "invalid_status"},  # Negative ID, invalid status
                    4: {"name": "Special-Char!@#$%", "email": "test@domain"},  # Special characters
                }

                if i in edge_cases:
                    row.update(edge_cases[i])

            data.append(row)

        return pd.DataFrame(data)

    @staticmethod
    def create_standards_data(standard_type: str = "comprehensive") -> Dict[str, Any]:
        """Create various types of ADRI standards for testing."""

        base_standard = {
            "contracts": {
                "id": f"test_{standard_type}_standard",
                "name": f"Test {standard_type.title()} Standard",
                "version": "1.0.0",
                "authority": "ADRI Test Framework",
                "description": f"Test standard for {standard_type} testing scenarios"
            }
        }

        if standard_type == "comprehensive":
            base_standard["requirements"] = {
                "overall_minimum": 75.0,
                "field_requirements": {
                    "customer_id": {
                        "type": "integer",
                        "nullable": False,
                        "min_value": 1
                    },
                    "name": {
                        "type": "string",
                        "nullable": False,
                        "min_length": 1,
                        "max_length": 100
                    },
                    "email": {
                        "type": "string",
                        "nullable": False,
                        "pattern": r"^[^@]+@[^@]+\.[^@]+$"
                    },
                    "age": {
                        "type": "integer",
                        "nullable": False,
                        "min_value": 0,
                        "max_value": 120
                    },
                    "salary": {
                        "type": "integer",
                        "nullable": False,
                        "min_value": 0
                    },
                    "status": {
                        "type": "string",
                        "nullable": False,
                        "allowed_values": ["active", "inactive", "pending", "suspended"]
                    }
                },
                "dimension_requirements": {
                    "validity": {"minimum_score": 15.0, "weight": 3},
                    "completeness": {"minimum_score": 15.0, "weight": 3},
                    "consistency": {"minimum_score": 12.0, "weight": 3},
                    "freshness": {"minimum_score": 15.0, "weight": 3},
                    "plausibility": {"minimum_score": 12.0, "weight": 3}
                }
            }

        elif standard_type == "minimal":
            base_standard["requirements"] = {
                "overall_minimum": 50.0,
                "field_requirements": {},
                "dimension_requirements": {
                    "validity": {"minimum_score": 10.0, "weight": 1}
                }
            }

        elif standard_type == "strict":
            base_standard["requirements"] = {
                "overall_minimum": 95.0,
                "field_requirements": {
                    "customer_id": {
                        "type": "integer",
                        "nullable": False,
                        "min_value": 1
                    }
                },
                "dimension_requirements": {
                    "validity": {"minimum_score": 19.0, "weight": 5},
                    "completeness": {"minimum_score": 19.0, "weight": 5},
                    "consistency": {"minimum_score": 19.0, "weight": 5},
                    "freshness": {"minimum_score": 19.0, "weight": 5},
                    "plausibility": {"minimum_score": 19.0, "weight": 5}
                }
            }

        return base_standard

    @staticmethod
    def create_configuration_data(config_type: str = "complete") -> Dict[str, Any]:
        """Create ADRI configuration data for testing."""

        base_config = {
            "adri": {
                "version": "4.0.0",
                "project_name": f"test_project_{config_type}",
                "default_environment": "development"
            }
        }

        if config_type == "complete":
            base_config["adri"]["environments"] = {
                "development": {
                    "paths": {
                        "contracts": "/tmp/test/standards",
                        "assessments": "/tmp/test/assessments",
                        "training_data": "/tmp/test/training-data",
                        "audit_logs": "/tmp/test/audit-logs"
                    },
                    "protection": {
                        "default_failure_mode": "warn",
                        "default_min_score": 75
                    },
                    "logging": {
                        "level": "DEBUG",
                        "file_rotation": True
                    }
                },
                "production": {
                    "paths": {
                        "contracts": "/prod/contracts",
                        "assessments": "/prod/assessments",
                        "training_data": "/prod/training-data",
                        "audit_logs": "/prod/audit-logs"
                    },
                    "protection": {
                        "default_failure_mode": "raise",
                        "default_min_score": 85
                    },
                    "logging": {
                        "level": "INFO",
                        "file_rotation": True
                    }
                }
            }

        elif config_type == "minimal":
            base_config["adri"]["environments"] = {
                "test": {
                    "paths": {},
                    "protection": {}
                }
            }

        return base_config


class ErrorSimulator:
    """Comprehensive error condition simulation for testing error handling."""

    @staticmethod
    @contextmanager
    def simulate_file_system_error(error_type: str = "permission"):
        """Simulate various file system errors."""
        if error_type == "permission":
            # Simulate permission denied
            original_open = open
            def mock_open(*args, **kwargs):
                raise PermissionError("Permission denied")

            import builtins
            builtins.open = mock_open
            try:
                yield
            finally:
                builtins.open = original_open

        elif error_type == "not_found":
            # Simulate file not found
            original_exists = os.path.exists
            os.path.exists = lambda x: False
            try:
                yield
            finally:
                os.path.exists = original_exists

        elif error_type == "disk_full":
            # Simulate disk full error
            original_write = open
            def mock_write(*args, **kwargs):
                raise OSError("No space left on device")

            import builtins
            builtins.open = mock_write
            try:
                yield
            finally:
                builtins.open = original_write
        else:
            yield

    @staticmethod
    @contextmanager
    def simulate_network_error(error_type: str = "timeout"):
        """Simulate network errors for enterprise logging testing."""
        if error_type == "timeout":
            import socket
            original_create_connection = socket.create_connection

            def mock_connection(*args, **kwargs):
                raise socket.timeout("Connection timed out")

            socket.create_connection = mock_connection
            try:
                yield
            finally:
                socket.create_connection = original_create_connection

        elif error_type == "connection_refused":
            import socket
            original_create_connection = socket.create_connection

            def mock_connection(*args, **kwargs):
                raise ConnectionRefusedError("Connection refused")

            socket.create_connection = mock_connection
            try:
                yield
            finally:
                socket.create_connection = original_create_connection
        else:
            yield

    @staticmethod
    @contextmanager
    def simulate_memory_pressure():
        """Simulate memory pressure for performance testing."""
        # Create a large object to simulate memory pressure
        large_objects = []
        try:
            # Allocate significant memory
            for _ in range(100):
                large_objects.append([0] * 100000)
            yield
        finally:
            # Clean up
            large_objects.clear()

    @staticmethod
    @contextmanager
    def simulate_processing_delay(delay_seconds: float = 0.1):
        """Simulate processing delays for performance testing."""
        import time

        original_time = time.time
        start_time = original_time()

        def mock_time():
            return original_time() + delay_seconds

        time.time = mock_time
        try:
            yield
        finally:
            time.time = original_time


# Pytest Fixtures

@pytest.fixture
def high_quality_data():
    """Provide high-quality test data (90%+ valid)."""
    return ModernFixtures.create_comprehensive_mock_data(
        rows=100,
        quality_level="high"
    )


@pytest.fixture
def medium_quality_data():
    """Provide medium-quality test data (70-80% valid)."""
    return ModernFixtures.create_comprehensive_mock_data(
        rows=100,
        quality_level="medium"
    )


@pytest.fixture
def low_quality_data():
    """Provide low-quality test data (40-60% valid)."""
    return ModernFixtures.create_comprehensive_mock_data(
        rows=100,
        quality_level="low"
    )


@pytest.fixture
def edge_case_data():
    """Provide data with comprehensive edge cases."""
    return ModernFixtures.create_comprehensive_mock_data(
        rows=20,
        quality_level="high",
        include_edge_cases=True
    )


@pytest.fixture
def comprehensive_standard():
    """Provide comprehensive ADRI standard for testing."""
    return ModernFixtures.create_standards_data("comprehensive")


@pytest.fixture
def minimal_standard():
    """Provide minimal ADRI standard for testing."""
    return ModernFixtures.create_standards_data("minimal")


@pytest.fixture
def strict_standard():
    """Provide strict ADRI standard for testing."""
    return ModernFixtures.create_standards_data("strict")


@pytest.fixture
def complete_config():
    """Provide complete ADRI configuration for testing."""
    return ModernFixtures.create_configuration_data("complete")


@pytest.fixture
def minimal_config():
    """Provide minimal ADRI configuration for testing."""
    return ModernFixtures.create_configuration_data("minimal")


def safe_rmtree(path):
    """Windows-safe recursive directory removal with enhanced cleanup strategies."""
    if not os.path.exists(path):
        return

    def handle_remove_readonly(func, path, exc):
        """Error handler for Windows readonly file issues."""
        if os.path.exists(path):
            os.chmod(path, 0o777)
            func(path)

    def windows_rmdir_fallback(path):
        """Fallback using Windows rmdir command for stubborn directories."""
        if platform.system() == "Windows":
            try:
                import subprocess
                subprocess.run(['rmdir', '/s', '/q', path],
                              shell=True, check=False,
                              capture_output=True, timeout=30)
            except Exception:
                pass  # Silent fallback failure

    # Multiple cleanup attempts with different strategies
    for attempt in range(5):
        try:
            if attempt > 0:
                time.sleep(0.1 * (attempt + 1))  # Progressive delay
                gc.collect()  # Force garbage collection to release handles

            if attempt >= 2:
                # Try to close any remaining file handles
                try:
                    for root, dirs, files in os.walk(path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            try:
                                os.chmod(file_path, 0o777)
                            except Exception:
                                pass
                except Exception:
                    pass

            # Attempt removal
            shutil.rmtree(path, onerror=handle_remove_readonly)
            return  # Success!

        except (PermissionError, OSError) as e:
            if attempt == 4:  # Last attempt
                if platform.system() == "Windows":
                    windows_rmdir_fallback(path)
                else:
                    raise


@pytest.fixture
def temp_workspace():
    """Provide temporary workspace with proper structure and Windows-safe cleanup."""
    temp_dir = tempfile.mkdtemp()
    try:
        workspace = Path(temp_dir)

        # Create ADRI directory structure
        adri_dir = workspace / "ADRI"
        for env in ["dev", "prod", "test"]:
            for subdir in ["standards", "assessments", "training-data", "audit-logs"]:
                (adri_dir / env / subdir).mkdir(parents=True)

        # Create config file
        config = ModernFixtures.create_configuration_data("complete")
        config_file = workspace / "ADRI" / "config.yaml"
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config, f)

        yield workspace
    finally:
        # Windows-safe cleanup
        safe_rmtree(temp_dir)


@pytest.fixture
def sample_csv_file(temp_workspace, high_quality_data):
    """Create temporary CSV file with high-quality test data."""
    csv_file = temp_workspace / "test_data.csv"
    high_quality_data.to_csv(csv_file, index=False)
    return str(csv_file)


@pytest.fixture
def sample_json_file(temp_workspace, high_quality_data):
    """Create temporary JSON file with high-quality test data."""
    json_file = temp_workspace / "test_data.json"
    high_quality_data.to_dict('records')
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(high_quality_data.to_dict('records'), f)
    return str(json_file)


@pytest.fixture
def sample_standard_name(temp_workspace, comprehensive_standard):
    """Create temporary standard file and return name for name-only resolution.

    This fixture supports the governance model that enforces name-only standard
    resolution. The standard file is created in the configured location, but only
    the standard name is returned for use with the decorator and engine.
    """
    # Ensure standards directory exists
    standards_dir = temp_workspace / "ADRI" / "dev" / "standards"
    standards_dir.mkdir(parents=True, exist_ok=True)

    # Create standard file in configured location
    standard_file = standards_dir / "test_standard.yaml"
    with open(standard_file, 'w', encoding='utf-8') as f:
        yaml.dump(comprehensive_standard, f)

    # Return name only (without .yaml extension, without path)
    return "test_standard"


@pytest.fixture
def error_simulator():
    """Provide error simulation utilities."""
    return ErrorSimulator()


@pytest.fixture
def performance_context():
    """Provide performance monitoring context."""
    return performance_monitor


@pytest.fixture
def clean_test_environment():
    """Ensure clean test environment without side effects."""
    # Store original environment
    original_env = os.environ.copy()
    original_cwd = os.getcwd()

    # Set test environment variables
    os.environ["ADRI_ENV"] = "TEST"
    os.environ["ADRI_LOG_LEVEL"] = "DEBUG"

    yield

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)
    os.chdir(original_cwd)


@pytest.fixture
def mock_assessment_result():
    """Provide realistic mock assessment result."""
    class MockDimensionScore:
        def __init__(self, score: float):
            self.score = score
            self.details = {}

        def to_dict(self):
            return {"score": self.score, "details": self.details}

    class MockAssessmentResult:
        def __init__(self, overall_score: float = 82.5, passed: bool = True):
            self.overall_score = overall_score
            self.passed = passed
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
            self.assessment_timestamp = "2025-01-01T00:00:00Z"

        def to_dict(self):
            return {
                "overall_score": self.overall_score,
                "passed": self.passed,
                "dimension_scores": {k: v.to_dict() for k, v in self.dimension_scores.items()},
                "standard_id": self.standard_id,
                "assessment_timestamp": self.assessment_timestamp
            }

        def to_standard_dict(self):
            return self.to_dict()

    return MockAssessmentResult()


# Performance Testing Utilities

class PerformanceTester:
    """Performance testing utilities for benchmarking components."""

    @staticmethod
    def create_large_dataset(rows: int = 10000) -> pd.DataFrame:
        """Create large dataset for performance testing."""
        return ModernFixtures.create_comprehensive_mock_data(
            rows=rows,
            quality_level="high",
            include_edge_cases=False
        )

    @staticmethod
    def create_wide_dataset(cols: int = 100, rows: int = 1000) -> pd.DataFrame:
        """Create wide dataset for performance testing."""
        data = {}
        for i in range(cols):
            data[f"field_{i}"] = [f"value_{i}_{j}" for j in range(rows)]
        return pd.DataFrame(data)

    @staticmethod
    @contextmanager
    def memory_monitor():
        """Monitor memory usage during testing."""
        import psutil
        process = psutil.Process()

        memory_before = process.memory_info().rss
        yield
        memory_after = process.memory_info().rss

        memory_delta = memory_after - memory_before
        print(f"Memory delta: {memory_delta / 1024 / 1024:.2f} MB")


@pytest.fixture
def performance_tester():
    """Provide performance testing utilities."""
    return PerformanceTester()
