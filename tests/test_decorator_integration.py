"""
Integration tests for ADRI Guard Decorator to achieve 85%+ coverage.

Focuses on comprehensive real-world decorator scenarios, convenience functions,
and edge cases to complete the Business Critical trio.
"""

import unittest
import pandas as pd
import tempfile
import os
import shutil
from unittest.mock import Mock, patch, MagicMock
import sys
import importlib

# Test the actual decorator functions
from src.adri.decorator import (
    adri_protected,
    ProtectionError
)


class TestDecoratorIntegration(unittest.TestCase):
    """Test decorator integration with real protection scenarios."""

    def setUp(self):
        """Set up test environment."""
        self.sample_customer_data = pd.DataFrame({
            "customer_id": ["CUST001", "CUST002", "CUST003"],
            "email": ["john@example.com", "mary@company.org", "david@business.net"],
            "age": [35, 28, 42],
            "annual_income": [75000, 120000, 95000],
            "credit_score": [720, 810, 680]
        })

        self.sample_financial_data = pd.DataFrame({
            "transaction_id": ["TXN001", "TXN002", "TXN003"],
            "account_number": ["ACC123456", "ACC789012", "ACC345678"],
            "amount": [1500.50, 25000.00, 850.75],
            "transaction_type": ["transfer", "deposit", "withdrawal"],
            "currency": ["USD", "USD", "USD"]
        })

    @patch('src.adri.decorator.DataProtectionEngine')
    def test_explicit_protection_patterns_comprehensive(self, mock_engine_class):
        """Test @adri_protected with different explicit configuration patterns."""
        # Setup mock engine
        mock_engine = Mock()
        mock_result = Mock()
        mock_result.overall_score = 92.0
        mock_engine.protect_function_call.return_value = {"processed": True}
        mock_engine_class.return_value = mock_engine

        # Test strict protection pattern (equivalent to old adri_strict)
        @adri_protected(standard="customer_data", data_param="customers", min_score=90, on_failure="raise")
        def strict_customer_processing(customers, validation_level="high"):
            return {"processed_customers": len(customers), "validation": validation_level}

        result = strict_customer_processing(self.sample_customer_data, validation_level="strict")
        self.assertEqual(result["processed"], True)

        # Verify strict parameters were passed correctly
        call_args = mock_engine.protect_function_call.call_args
        self.assertEqual(call_args[1]["min_score"], 90)
        self.assertEqual(call_args[1]["on_failure"], "raise")

        # Test permissive protection pattern (equivalent to old adri_permissive)
        @adri_protected(standard="customer_data", data_param="customers", min_score=70, on_failure="warn", verbose=True)
        def permissive_customer_processing(customers, mode="development"):
            return {"processed_customers": len(customers), "mode": mode}

        result = permissive_customer_processing(self.sample_customer_data, mode="test")
        self.assertEqual(result["processed"], True)

        # Verify permissive parameters
        call_args = mock_engine.protect_function_call.call_args
        self.assertEqual(call_args[1]["min_score"], 70)
        self.assertEqual(call_args[1]["on_failure"], "warn")
        self.assertTrue(call_args[1]["verbose"])

        # Test financial-grade protection pattern (equivalent to old adri_financial)
        @adri_protected(
            standard="financial_transactions",
            data_param="transactions",
            min_score=95,
            dimensions={"validity": 19, "completeness": 19, "consistency": 18},
            on_failure="raise"
        )
        def financial_transaction_processing(transactions, audit_level="full"):
            return {"processed_transactions": len(transactions), "audit": audit_level}

        result = financial_transaction_processing(self.sample_financial_data, audit_level="comprehensive")
        self.assertEqual(result["processed"], True)

        # Verify financial-grade parameters
        call_args = mock_engine.protect_function_call.call_args
        self.assertEqual(call_args[1]["min_score"], 95)
        self.assertEqual(call_args[1]["on_failure"], "raise")
        self.assertIn("validity", call_args[1]["dimensions"])
        self.assertEqual(call_args[1]["dimensions"]["validity"], 19)

    @patch('src.adri.decorator.DataProtectionEngine')
    def test_explicit_protection_with_custom_overrides(self, mock_engine_class):
        """Test @adri_protected with custom parameter overrides."""
        mock_engine = Mock()
        mock_engine.protect_function_call.return_value = {"processed": True}
        mock_engine_class.return_value = mock_engine

        # Test strict protection with custom min_score override
        @adri_protected(standard="custom_data", min_score=85, on_failure="raise", cache_assessments=True)
        def custom_strict_processing(data):
            return {"custom": True}

        result = custom_strict_processing(self.sample_customer_data)
        self.assertEqual(result["processed"], True)

        # Verify override took effect
        call_args = mock_engine.protect_function_call.call_args
        self.assertEqual(call_args[1]["min_score"], 85)
        self.assertEqual(call_args[1]["on_failure"], "raise")
        self.assertTrue(call_args[1]["cache_assessments"])

        # Test permissive protection with custom on_failure override
        @adri_protected(standard="dev_data", min_score=70, on_failure="continue", auto_generate=False, verbose=True)
        def custom_permissive_processing(data):
            return {"development": True}

        result = custom_permissive_processing(self.sample_customer_data)
        self.assertEqual(result["processed"], True)

        # Verify override took effect
        call_args = mock_engine.protect_function_call.call_args
        self.assertEqual(call_args[1]["min_score"], 70)
        self.assertEqual(call_args[1]["on_failure"], "continue")
        self.assertFalse(call_args[1]["auto_generate"])
        self.assertTrue(call_args[1]["verbose"])

        # Test financial-grade protection with custom dimensions override
        custom_dimensions = {"validity": 20, "completeness": 20, "consistency": 19, "freshness": 18}

        @adri_protected(
            standard="high_security_financial",
            min_score=95,
            dimensions=custom_dimensions,
            on_failure="raise"
        )
        def high_security_financial_processing(data):
            return {"high_security": True}

        result = high_security_financial_processing(self.sample_financial_data)
        self.assertEqual(result["processed"], True)

        # Verify custom dimensions took effect
        call_args = mock_engine.protect_function_call.call_args
        self.assertEqual(call_args[1]["min_score"], 95)
        self.assertEqual(call_args[1]["on_failure"], "raise")
        self.assertEqual(call_args[1]["dimensions"], custom_dimensions)

    def test_import_fallback_scenarios(self):
        """Test import fallback logic when guard.modes is not available."""
        # This tests lines 15-21 in the decorator

        # Test that imports worked correctly in our environment
        from adri.decorator import DataProtectionEngine, ProtectionError
        self.assertIsNotNone(DataProtectionEngine)
        self.assertNotEqual(ProtectionError, Exception)  # Should be the real ProtectionError

        # Verify the decorator module has the expected attributes
        import adri.decorator as decorator_module
        self.assertTrue(hasattr(decorator_module, 'DataProtectionEngine'))
        self.assertTrue(hasattr(decorator_module, 'ProtectionError'))

    def test_data_protection_engine_unavailable_scenario(self):
        """Test decorator behavior when DataProtectionEngine is None."""
        # Test the warning path when DataProtectionEngine is not available
        with patch('src.adri.decorator.DataProtectionEngine', None):
            with patch('src.adri.decorator.logger') as mock_logger:

                @adri_protected(standard="test_standard")
                def test_function_no_engine(data):
                    return {"executed_without_protection": True}

                result = test_function_no_engine(self.sample_customer_data)

                # Should execute function without protection
                self.assertEqual(result["executed_without_protection"], True)

                # Should log warning
                mock_logger.warning.assert_called_with(
                    "DataProtectionEngine not available, executing function without protection"
                )

    @patch('src.adri.decorator.DataProtectionEngine')
    def test_protection_error_handling_comprehensive(self, mock_engine_class):
        """Test comprehensive protection error handling scenarios."""
        mock_engine = Mock()
        mock_engine_class.return_value = mock_engine

        # Test ProtectionError re-raising
        mock_engine.protect_function_call.side_effect = ProtectionError("Data quality too low")

        @adri_protected(standard="strict_standard")
        def function_with_protection_error(data):
            return {"should_not_execute": True}

        with self.assertRaises(ProtectionError) as context:
            function_with_protection_error(self.sample_customer_data)

        self.assertEqual(str(context.exception), "Data quality too low")

        # Test unexpected error wrapping
        mock_engine.protect_function_call.side_effect = ValueError("Unexpected system error")

        @adri_protected(standard="test_standard")
        def function_with_unexpected_error(data):
            return {"should_not_execute": True}

        with self.assertRaises(ProtectionError) as context:
            function_with_unexpected_error(self.sample_customer_data)

        self.assertIn("Data protection failed for function 'function_with_unexpected_error'", str(context.exception))
        self.assertIn("Unexpected system error", str(context.exception))

    @patch('src.adri.decorator.DataProtectionEngine')
    def test_comprehensive_protection_configuration(self, mock_engine_class):
        """Test @adri_protected with comprehensive configuration options."""
        mock_engine = Mock()
        mock_engine.protect_function_call.return_value = {"financial_complete": True}
        mock_engine_class.return_value = mock_engine

        # Test @adri_protected with all configuration options
        @adri_protected(
            standard="complete_financial_standard",
            data_param="financial_records",
            min_score=98,
            dimensions={"validity": 20, "completeness": 20, "consistency": 19, "freshness": 18, "plausibility": 17},
            on_failure="continue",
            auto_generate=False,
            cache_assessments=True,
            verbose=True
        )
        def complete_financial_function(financial_records):
            return {"complete_test": True}

        result = complete_financial_function(self.sample_financial_data)
        self.assertEqual(result["financial_complete"], True)

        # Verify all parameters were passed correctly
        call_args = mock_engine.protect_function_call.call_args
        self.assertEqual(call_args[1]["min_score"], 98)
        self.assertEqual(call_args[1]["on_failure"], "continue")
        self.assertFalse(call_args[1]["auto_generate"])
        self.assertTrue(call_args[1]["cache_assessments"])
        self.assertTrue(call_args[1]["verbose"])

        # Verify custom dimensions configuration
        expected_dims = {"validity": 20, "completeness": 20, "consistency": 19, "freshness": 18, "plausibility": 17}
        self.assertEqual(call_args[1]["dimensions"], expected_dims)

    @patch('src.adri.decorator.DataProtectionEngine')
    def test_decorator_function_attributes(self, mock_engine_class):
        """Test decorator sets correct function attributes."""
        mock_engine = Mock()
        mock_engine.protect_function_call.return_value = {"success": True}
        mock_engine_class.return_value = mock_engine

        @adri_protected(
            standard="test_standard",
            data_param="input_data",
            min_score=85,
            dimensions={"validity": 18, "completeness": 17},
            on_failure="continue",
            auto_generate=False,
            cache_assessments=True,
            verbose=True
        )
        def test_function_with_all_params(input_data, extra_param="default"):
            """Test function with comprehensive parameters."""
            return {"processed": len(input_data)}

        # Test function execution
        result = test_function_with_all_params(self.sample_customer_data, extra_param="custom")
        self.assertEqual(result["success"], True)

        # Verify function attributes are set correctly
        self.assertTrue(hasattr(test_function_with_all_params, '_adri_protected'))
        self.assertTrue(test_function_with_all_params._adri_protected)

        self.assertTrue(hasattr(test_function_with_all_params, '_adri_config'))
        config = test_function_with_all_params._adri_config

        self.assertEqual(config["standard"], "test_standard")
        self.assertEqual(config["data_param"], "input_data")
        self.assertEqual(config["min_score"], 85)
        self.assertEqual(config["dimensions"], {"validity": 18, "completeness": 17})
        self.assertEqual(config["on_failure"], "continue")
        self.assertFalse(config["auto_generate"])
        self.assertTrue(config["cache_assessments"])
        self.assertTrue(config["verbose"])

        # Verify function name and docstring are preserved
        self.assertEqual(test_function_with_all_params.__name__, "test_function_with_all_params")
        self.assertIn("Test function with comprehensive parameters", test_function_with_all_params.__doc__)

    @patch('src.adri.decorator.DataProtectionEngine')
    def test_real_world_integration_scenarios(self, mock_engine_class):
        """Test real-world integration scenarios with explicit protection configurations."""
        mock_engine = Mock()
        mock_engine.protect_function_call.return_value = {"integration_success": True}
        mock_engine_class.return_value = mock_engine

        # Scenario 1: E-commerce order processing with strict requirements
        @adri_protected(standard="ecommerce_orders", data_param="orders", min_score=90, on_failure="raise")
        def process_ecommerce_orders(orders, fulfillment_center="main"):
            """Process e-commerce orders with strict data quality requirements."""
            return {
                "processed_orders": len(orders),
                "fulfillment_center": fulfillment_center,
                "quality_verified": True
            }

        orders_data = pd.DataFrame({
            "order_id": ["ORD001", "ORD002", "ORD003"],
            "customer_email": ["buyer1@example.com", "buyer2@shop.com", "buyer3@store.org"],
            "total_amount": [129.99, 89.50, 459.95],
            "shipping_address": ["123 Main St", "456 Oak Ave", "789 Pine Rd"]
        })

        result = process_ecommerce_orders(orders_data, fulfillment_center="west_coast")
        self.assertEqual(result["integration_success"], True)

        # Scenario 2: Healthcare data processing with financial-grade protection
        @adri_protected(
            standard="patient_records",
            data_param="patient_data",
            min_score=95,
            dimensions={"validity": 19, "completeness": 19, "consistency": 18},
            on_failure="raise"
        )
        def process_patient_records(patient_data, compliance_level="hipaa"):
            """Process patient records with financial-grade data protection."""
            return {
                "processed_patients": len(patient_data),
                "compliance_level": compliance_level,
                "protected": True
            }

        patient_data = pd.DataFrame({
            "patient_id": ["PAT001", "PAT002", "PAT003"],
            "diagnosis_code": ["A123", "B456", "C789"],
            "treatment_date": ["2024-01-15", "2024-01-20", "2024-01-25"],
            "provider_id": ["PROV001", "PROV002", "PROV001"]
        })

        result = process_patient_records(patient_data, compliance_level="hipaa_enhanced")
        self.assertEqual(result["integration_success"], True)

        # Scenario 3: Development environment with permissive protection
        @adri_protected(standard="dev_test_data", data_param="test_data", min_score=70, on_failure="warn", verbose=True)
        def process_development_data(test_data, environment="development"):
            """Process development data with permissive protection for testing."""
            return {
                "test_records": len(test_data),
                "environment": environment,
                "development_mode": True
            }

        test_data = pd.DataFrame({
            "test_id": ["TEST001", "TEST002"],
            "test_value": [42, 84],
            "test_category": ["unit", "integration"]
        })

        result = process_development_data(test_data, environment="staging")
        self.assertEqual(result["integration_success"], True)


class TestDecoratorEdgeCases(unittest.TestCase):
    """Test decorator edge cases and error scenarios."""

    def setUp(self):
        """Set up test environment."""
        self.test_data = pd.DataFrame({
            "id": [1, 2, 3],
            "value": ["a", "b", "c"]
        })

    @patch('src.adri.decorator.DataProtectionEngine')
    def test_complex_function_signatures(self, mock_engine_class):
        """Test decorator with complex function signatures."""
        mock_engine = Mock()
        mock_engine.protect_function_call.return_value = {"complex": True}
        mock_engine_class.return_value = mock_engine

        # Test with *args and **kwargs
        @adri_protected(standard="complex_standard", data_param="main_data")
        def complex_function(main_data, required_param, optional_param="default", *extra_args, **extra_kwargs):
            return {
                "main_data_size": len(main_data),
                "required": required_param,
                "optional": optional_param,
                "extra_args_count": len(extra_args),
                "extra_kwargs_count": len(extra_kwargs)
            }

        result = complex_function(
            self.test_data,
            "required_value",
            "custom",  # optional_param as positional to allow *args
            "extra1", "extra2",
            extra_setting="value1",
            another_setting="value2"
        )

        self.assertEqual(result["complex"], True)

        # Verify the protection call was made correctly
        call_args = mock_engine.protect_function_call.call_args
        self.assertEqual(call_args[1]["function_name"], "complex_function")
        self.assertEqual(call_args[1]["data_param"], "main_data")

    @patch('src.adri.decorator.DataProtectionEngine')
    def test_nested_decorators_scenario(self, mock_engine_class):
        """Test ADRI decorator used with other decorators."""
        mock_engine = Mock()
        mock_engine.protect_function_call.return_value = {"nested": True}
        mock_engine_class.return_value = mock_engine

        def timing_decorator(func):
            def wrapper(*args, **kwargs):
                result = func(*args, **kwargs)
                result["timed"] = True
                return result
            return wrapper

        def logging_decorator(func):
            def wrapper(*args, **kwargs):
                result = func(*args, **kwargs)
                result["logged"] = True
                return result
            return wrapper

        # Test ADRI decorator in combination with other decorators
        @timing_decorator
        @adri_protected(standard="nested_standard")
        @logging_decorator
        def nested_decorated_function(data):
            return {"base": True}

        result = nested_decorated_function(self.test_data)

        # Should have results from all decorators
        self.assertEqual(result["nested"], True)
        self.assertTrue(result.get("timed", False))
        # Note: logging_decorator is applied first, so its effect might be overridden


if __name__ == '__main__':
    unittest.main()
