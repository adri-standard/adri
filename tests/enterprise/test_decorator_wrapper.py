"""
Tests for enterprise decorator wrapper.

Verifies that the enterprise decorator:
1. Wraps the base open source decorator correctly
2. Accepts enterprise parameters (reasoning_mode, workflow_context, data_provenance)
3. Delegates core functionality to base decorator
4. Maintains backward compatibility
"""

import pytest
from unittest.mock import patch, MagicMock
import pandas as pd
from adri_enterprise.decorator import adri_protected
from adri.guard.modes import ProtectionError
from adri_enterprise.license import LicenseInfo


@pytest.fixture(autouse=True)
def mock_license_validation():
    """Mock license validation for all tests in this module.
    
    This fixture runs automatically for all tests and mocks the validate_license
    function to avoid requiring a real VERODAT_API_KEY in CI environments.
    """
    from datetime import datetime
    mock_license_info = LicenseInfo(
        is_valid=True,
        api_key="test-api-key-for-ci",
        validated_at=datetime.now(),
        expires_at=None,
        account_id=91,
        username="test@example.com",
        error_message=None
    )
    with patch('adri_enterprise.decorator.validate_license', return_value=mock_license_info):
        with patch('adri_enterprise.decorator._license_validated', True):
            yield mock_license_info


class TestEnterpriseDecoratorWrapper:
    """Test suite for enterprise decorator wrapper functionality."""

    def test_basic_enterprise_decorator(self, tmp_path):
        """Test basic enterprise decorator functionality."""
        # Create test data
        test_data = pd.DataFrame({
            "customer_id": [1, 2, 3],
            "name": ["Alice", "Bob", "Charlie"],
            "score": [85, 90, 88]
        })

        # Decorator should work with base parameters only
        @adri_protected(contract="test_customer_data")
        def process_customers(data):
            return len(data)

        result = process_customers(test_data)
        assert result == 3

    def test_enterprise_decorator_with_reasoning_mode(self, tmp_path):
        """Test enterprise decorator with reasoning_mode parameter."""
        test_data = pd.DataFrame({
            "customer_id": [1, 2, 3],
            "name": ["Alice", "Bob", "Charlie"]
        })

        @adri_protected(
            contract="test_customer_data_reasoning",
            reasoning_mode=True,
            verbose=True,
            auto_generate=True  # Auto-generate contract from data
        )
        def analyze_customers(data):
            return f"Analyzed {len(data)} customers"

        result = analyze_customers(test_data)
        assert "Analyzed 3 customers" in result

    def test_enterprise_decorator_with_workflow_context(self, tmp_path):
        """Test enterprise decorator with workflow_context parameter."""
        test_data = pd.DataFrame({
            "transaction_id": [1, 2, 3],
            "amount": [100, 200, 150]
        })

        workflow_ctx = {
            "run_id": "run_test_001",
            "workflow_id": "transaction_workflow",
            "workflow_version": "1.0.0",
            "step_id": "validation",
            "step_sequence": 1,
            "run_at_utc": "2025-01-10T10:00:00Z"
        }

        @adri_protected(
            contract="test_transactions_workflow",
            workflow_context=workflow_ctx,
            verbose=True,
            auto_generate=True  # Auto-generate contract from data
        )
        def process_transactions(data):
            return data["amount"].sum()

        result = process_transactions(test_data)
        assert result == 450

    def test_enterprise_decorator_with_data_provenance(self, tmp_path):
        """Test enterprise decorator with data_provenance parameter."""
        test_data = pd.DataFrame({
            "order_id": [1, 2, 3],
            "customer_id": [101, 102, 103]
        })

        provenance = {
            "source_type": "verodat_query",
            "verodat_query_id": 12345,
            "verodat_account_id": 91,
            "verodat_workspace_id": 161,
            "record_count": 3
        }

        @adri_protected(
            contract="test_orders_provenance",
            data_provenance=provenance,
            verbose=True,
            auto_generate=True  # Auto-generate contract from data
        )
        def process_orders(data):
            return len(data)

        result = process_orders(test_data)
        assert result == 3

    def test_enterprise_decorator_with_all_enterprise_params(self, tmp_path):
        """Test enterprise decorator with all enterprise parameters combined."""
        test_data = pd.DataFrame({
            "project_id": [1, 2],
            "risk_score": [75, 82]
        })

        workflow_ctx = {
            "run_id": "run_test_full_002",
            "workflow_id": "risk_assessment",
            "step_id": "analysis"
        }

        provenance = {
            "source_type": "database",
            "database_name": "production_db"
        }

        llm_config = {
            "model": "claude-3-5-sonnet",
            "temperature": 0.1,
            "seed": 42
        }

        @adri_protected(
            contract="test_projects_all_params",
            reasoning_mode=True,
            store_prompt=True,
            store_response=True,
            llm_config=llm_config,
            workflow_context=workflow_ctx,
            data_provenance=provenance,
            verbose=True,
            auto_generate=True  # Auto-generate contract from data
        )
        def assess_project_risk(data):
            return data["risk_score"].mean()

        result = assess_project_risk(test_data)
        assert result == 78.5

    def test_enterprise_decorator_delegates_to_base(self, tmp_path):
        """Test that enterprise decorator properly delegates to base decorator."""
        # Test that base decorator functionality works through enterprise wrapper
        good_data = pd.DataFrame({
            "id": [1, 2, 3],
            "value": [10, 20, 30]
        })

        @adri_protected(
            contract="test_delegation_base",
            min_score=70,
            on_failure="raise",
            auto_generate=True  # Auto-generate contract from data
        )
        def process_data(data):
            return len(data)

        # Should successfully process data via base decorator
        result = process_data(good_data)
        assert result == 3
        
        # Verify that the function has both enterprise and base markers
        assert hasattr(process_data, "_adri_protected")
        assert hasattr(process_data, "_adri_enterprise")

    def test_enterprise_decorator_maintains_function_metadata(self):
        """Test that enterprise decorator preserves function metadata."""
        @adri_protected(contract="test_metadata")
        def example_function(data):
            """Example docstring."""
            return data

        # Check that function metadata is preserved
        assert example_function.__name__ == "example_function"
        assert "Example docstring" in example_function.__doc__
        assert hasattr(example_function, "_adri_protected")
        assert hasattr(example_function, "_adri_enterprise")
        assert example_function._adri_protected is True
        assert example_function._adri_enterprise is True

    def test_enterprise_decorator_config_attribute(self):
        """Test that enterprise decorator sets config attributes correctly."""
        workflow_ctx = {"run_id": "test"}
        provenance = {"source_type": "test"}

        @adri_protected(
            contract="test_config",
            min_score=85,
            reasoning_mode=True,
            workflow_context=workflow_ctx,
            data_provenance=provenance
        )
        def example_function(data):
            return data

        config = example_function._adri_config
        assert config["contract"] == "test_config"
        assert config["min_score"] == 85
        assert config["reasoning_mode"] is True
        assert config["workflow_context"] == workflow_ctx
        assert config["data_provenance"] == provenance

    def test_enterprise_decorator_backward_compatibility(self, tmp_path):
        """Test that enterprise decorator maintains backward compatibility."""
        # Test that all base decorator parameters work
        test_data = pd.DataFrame({
            "field1": [1, 2, 3],
            "field2": ["a", "b", "c"]
        })

        @adri_protected(
            contract="test_compat",
            data_param="data",
            min_score=70,
            dimensions={"validity": 15},
            on_failure="warn",
            auto_generate=True,
            verbose=False
        )
        def process_data(data):
            return len(data)

        result = process_data(test_data)
        assert result == 3
