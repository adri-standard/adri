"""
pytest configuration for enterprise testing.

Provides fixtures and setup for enterprise-specific test scenarios including
API mocking, license validation, and CI/CD environment preparation.
"""

import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from adri_enterprise.license import LicenseInfo


@pytest.fixture
def mock_api_key():
    """Provide a mock API key for testing."""
    return "test-api-key-12345"


@pytest.fixture
def mock_license_info():
    """Provide mock license info for successful validation."""
    return LicenseInfo(
        is_valid=True,
        api_key="test-api-key-12345",
        validated_at=datetime.now(),
        expires_at=datetime.now() + timedelta(hours=24),
        account_id=91,
        username="test@example.com",
        error_message=None
    )


@pytest.fixture
def mock_expired_license_info():
    """Provide mock license info for expired/invalid validation."""
    return LicenseInfo(
        is_valid=False,
        api_key="expired-key",
        validated_at=datetime.now() - timedelta(hours=25),
        expires_at=datetime.now() - timedelta(hours=1),
        account_id=None,
        username=None,
        error_message="API key has expired"
    )


@pytest.fixture
def mock_verodat_api_success():
    """Mock successful Verodat API responses."""
    with patch('requests.post') as mock_post, patch('requests.get') as mock_get:
        # Mock license validation endpoint
        mock_get_response = MagicMock()
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = {
            "accountId": 91,
            "username": "test@example.com",
            "valid": True
        }
        mock_get.return_value = mock_get_response

        # Mock data upload endpoint
        mock_post_response = MagicMock()
        mock_post_response.status_code = 200
        mock_post_response.json.return_value = {"success": True}
        mock_post.return_value = mock_post_response

        yield {
            'get': mock_get,
            'post': mock_post,
            'get_response': mock_get_response,
            'post_response': mock_post_response
        }


@pytest.fixture
def mock_verodat_api_failure():
    """Mock failed Verodat API responses."""
    with patch('requests.post') as mock_post, patch('requests.get') as mock_get:
        # Mock license validation failure
        mock_get_response = MagicMock()
        mock_get_response.status_code = 401
        mock_get_response.text = "Invalid API key"
        mock_get.return_value = mock_get_response

        # Mock data upload failure
        mock_post_response = MagicMock()
        mock_post_response.status_code = 500
        mock_post_response.text = "Internal server error"
        mock_post.return_value = mock_post_response

        yield {
            'get': mock_get,
            'post': mock_post,
            'get_response': mock_get_response,
            'post_response': mock_post_response
        }


@pytest.fixture
def mock_verodat_api_timeout():
    """Mock Verodat API timeout scenarios."""
    import requests
    with patch('requests.post') as mock_post, patch('requests.get') as mock_get:
        mock_get.side_effect = requests.Timeout("Request timed out")
        mock_post.side_effect = requests.Timeout("Request timed out")
        yield {'get': mock_get, 'post': mock_post}


@pytest.fixture
def temp_log_dir():
    """Provide a temporary directory for log file testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        log_path = Path(temp_dir) / "logs"
        log_path.mkdir()
        yield log_path


@pytest.fixture
def temp_config_dir():
    """Provide a temporary directory with enterprise config files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        config_path = Path(temp_dir)

        # Create ADRI directory structure
        adri_dir = config_path / "ADRI"
        adri_dir.mkdir()

        # Create dev and prod directories
        (adri_dir / "dev" / "contracts").mkdir(parents=True)
        (adri_dir / "prod" / "contracts").mkdir(parents=True)
        (adri_dir / "dev" / "assessments").mkdir(parents=True)
        (adri_dir / "prod" / "assessments").mkdir(parents=True)

        # Create enterprise config file
        config_data = {
            "adri": {
                "version": "4.0.0",
                "project_name": "test_enterprise_project",
                "default_environment": "development",
                "environments": {
                    "development": {
                        "paths": {
                            "contracts": "./dev/contracts",
                            "assessments": "./dev/assessments",
                            "training_data": "./dev/training-data",
                            "audit_logs": "./dev/audit-logs",
                        },
                        "protection": {
                            "default_failure_mode": "warn",
                            "default_min_score": 70,
                        },
                    },
                    "production": {
                        "paths": {
                            "contracts": "./prod/contracts",
                            "assessments": "./prod/assessments",
                            "training_data": "./prod/training-data",
                            "audit_logs": "./prod/audit-logs",
                        },
                        "protection": {
                            "default_failure_mode": "raise",
                            "default_min_score": 85,
                        },
                    },
                },
            }
        }

        config_file = adri_dir / "config.yaml"
        with open(config_file, "w", encoding="utf-8") as f:
            yaml.dump(config_data, f)

        yield {
            'config_path': config_path,
            'config_file': str(config_file),
            'adri_dir': adri_dir
        }


@pytest.fixture
def enterprise_env_vars():
    """Set up enterprise environment variables for testing."""
    original_env = {}
    test_vars = {
        'VERODAT_API_KEY': 'test-api-key-for-ci',
        'VERODAT_API_URL': 'https://api-test.verodat.com/api/v1',
        'ADRI_ENV': 'development'
    }

    # Save original values
    for key in test_vars:
        if key in os.environ:
            original_env[key] = os.environ[key]

    # Set test values
    for key, value in test_vars.items():
        os.environ[key] = value

    yield test_vars

    # Restore original values
    for key in test_vars:
        if key in original_env:
            os.environ[key] = original_env[key]
        else:
            os.environ.pop(key, None)


@pytest.fixture
def clean_license_cache():
    """Clean license validation cache before and after tests."""
    from adri_enterprise.license import get_validator

    # Clear cache before test
    validator = get_validator()
    validator.clear_cache()

    yield

    # Clear cache after test
    validator.clear_cache()


@pytest.fixture
def mock_reasoning_data():
    """Provide mock reasoning step data for testing."""
    return {
        'prompt': {
            'system': 'You are a data quality analyst.',
            'user': 'Analyze this data for quality issues.',
            'data_preview': 'customer_id,name,score\n1,Alice,85\n2,Bob,90'
        },
        'response': {
            'analysis': 'The data appears to be well-structured with no missing values.',
            'quality_score': 88.5,
            'recommendations': ['Consider adding email validation', 'Check for duplicate customer IDs']
        },
        'llm_config': {
            'model': 'claude-3-5-sonnet',
            'temperature': 0.1,
            'seed': 42,
            'max_tokens': 1000
        },
        'assessment_id': 'test_assessment_001',
        'function_name': 'analyze_customer_data'
    }


@pytest.fixture
def mock_workflow_context():
    """Provide mock workflow context for testing."""
    return {
        'run_id': 'run_test_20250116_134500_abc123',
        'workflow_id': 'data_quality_pipeline',
        'workflow_version': '2.1.0',
        'step_id': 'customer_validation',
        'step_sequence': 3,
        'run_at_utc': '2025-01-16T13:45:00Z',
        'orchestrator': 'pytest'
    }


@pytest.fixture
def mock_data_provenance():
    """Provide mock data provenance for testing."""
    return {
        'source_type': 'verodat_query',
        'verodat_query_id': 12345,
        'verodat_account_id': 91,
        'verodat_workspace_id': 161,
        'dataset_id': 4203,
        'record_count': 150,
        'extracted_at': '2025-01-16T13:30:00Z',
        'query_hash': 'sha256:abc123def456'
    }


@pytest.fixture(autouse=True)
def setup_test_logging():
    """Setup test logging configuration."""
    import logging

    # Set logging level for enterprise modules
    enterprise_loggers = [
        'adri_enterprise.decorator',
        'adri_enterprise.license',
        'adri_enterprise.logging.verodat',
        'adri_enterprise.logging.reasoning',
        'adri_enterprise.config.loader'
    ]

    for logger_name in enterprise_loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.DEBUG)

        # Add console handler if not already present
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

    yield

    # Cleanup handlers after test
    for logger_name in enterprise_loggers:
        logger = logging.getLogger(logger_name)
        logger.handlers.clear()


@pytest.fixture
def performance_baseline():
    """Provide performance baseline expectations for enterprise features."""
    return {
        'license_validation_max_time': 5.0,  # seconds
        'license_cache_hit_max_time': 0.1,   # seconds
        'reasoning_log_write_max_time': 0.5, # seconds
        'verodat_api_call_max_time': 10.0,   # seconds
        'decorator_overhead_max_time': 0.1   # seconds
    }


# Pytest configuration
def pytest_configure(config):
    """Configure pytest for enterprise testing."""
    config.addinivalue_line(
        "markers", "enterprise: mark test as enterprise-specific"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as performance test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test items for enterprise testing."""
    # Add enterprise marker to all tests in enterprise directory
    for item in items:
        if "enterprise" in str(item.fspath):
            item.add_marker(pytest.mark.enterprise)
