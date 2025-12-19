"""
Comprehensive tests for ADRI guard decorator.

Tests the @adri_protected decorator and convenience aliases using real ADRI components.
No mocking of our own code - tests real functionality and integration.
"""

import unittest
import pandas as pd
import tempfile
import os
from pathlib import Path

# Updated imports for new src/ layout
from src.adri.decorator import (
    adri_protected,
    ProtectionError
)


class TestAdriProtectedDecorator(unittest.TestCase):
    """Test the main @adri_protected decorator with real functionality."""

    def setUp(self):
        """Set up test fixtures with real data and standards."""
        self.test_dir = tempfile.mkdtemp()

        # Create sample data that should pass quality checks
        self.good_data = pd.DataFrame([
            {"customer_id": 123, "email": "test@example.com", "age": 25, "score": 85.5},
            {"customer_id": 456, "email": "user@domain.com", "age": 35, "score": 92.3},
            {"customer_id": 789, "email": "admin@company.org", "age": 28, "score": 78.9}
        ])

        # Create sample data with quality issues
        self.poor_data = pd.DataFrame([
            {"customer_id": None, "email": "invalid-email", "age": -5, "score": None},
            {"customer_id": "", "email": "", "age": 999, "score": "invalid"}
        ])

        # Change to test directory for standard generation
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        os.chdir(self.original_cwd)
        import shutil
        shutil.rmtree(self.test_dir)

    def test_basic_decorator_functionality(self):
        """Test basic decorator application with real data assessment."""

        @adri_protected(contract="customer_standard")
        def process_customers(data):
            return f"Processed {len(data)} customers"

        # Test with good data - should pass
        result = process_customers(self.good_data)
        self.assertEqual(result, "Processed 3 customers")

        # Verify decorator attributes are set
        self.assertTrue(hasattr(process_customers, '_adri_protected'))
        self.assertTrue(process_customers._adri_protected)
        self.assertTrue(hasattr(process_customers, '_adri_config'))

        config = process_customers._adri_config
        self.assertEqual(config['contract'], "customer_standard")
        self.assertEqual(config['data_param'], "data")

    def test_custom_parameters(self):
        """Test decorator with custom parameters."""

        @adri_protected(
            contract="custom_standard",
            data_param="customer_info",
            min_score=70,
            verbose=True
        )
        def analyze_customers(customer_info, analysis_type="basic"):
            return f"Analysis: {analysis_type} on {len(customer_info)} records"

        result = analyze_customers(self.good_data, analysis_type="detailed")
        self.assertEqual(result, "Analysis: detailed on 3 records")

        # Check configuration
        config = analyze_customers._adri_config
        self.assertEqual(config['data_param'], "customer_info")
        self.assertEqual(config['min_score'], 70)
        self.assertTrue(config['verbose'])

class TestExplicitProtectionPatterns(unittest.TestCase):
    """Test explicit protection patterns with real functionality."""

    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)

        # Ultra high quality data designed to meet 95%+ standards
        self.excellent_data = pd.DataFrame([
            {
                "transaction_id": f"TXN_{i:04d}",
                "amount": round(100.0 + i * 10.5, 2),  # Precise amounts
                "currency": "USD",
                "timestamp": f"2023-01-{i+1:02d}T10:{i*10:02d}:00Z",  # Varied valid timestamps
                "status": "completed",
                "account_id": f"ACC_{i+1000:04d}",  # Additional structured field
                "verification_score": 98.5 + i * 0.3  # High verification scores
            }
            for i in range(5)
        ])

    def tearDown(self):
        """Clean up."""
        os.chdir(self.original_cwd)
        import shutil
        shutil.rmtree(self.test_dir)

    def test_permissive_protection_pattern(self):
        """Test permissive protection pattern (equivalent to old adri_permissive)."""

        @adri_protected(contract="permissive_standard", min_score=70, on_failure="warn", verbose=True)
        def permissive_function(data):
            return f"Permissive processing: {len(data)} records"

        result = permissive_function(self.excellent_data)
        self.assertEqual(result, "Permissive processing: 5 records")

        # Check configuration
        config = permissive_function._adri_config
        self.assertEqual(config['min_score'], 70)
        self.assertEqual(config['on_failure'], "warn")
        self.assertTrue(config['verbose'])


class TestDecoratorIntegration(unittest.TestCase):
    """Integration tests for decorators with various scenarios."""

    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)

        # Create test data with different quality levels
        self.high_quality_data = pd.DataFrame([
            {"id": i, "name": f"Item_{i}", "value": 100.0 + i, "status": "active"}
            for i in range(1, 6)
        ])

        self.mixed_quality_data = pd.DataFrame([
            {"id": 1, "name": "Good_Item", "value": 150.0, "status": "active"},
            {"id": 2, "name": "", "value": 200.0, "status": "active"},  # Missing name
            {"id": None, "name": "Bad_Item", "value": -10.0, "status": ""},  # Multiple issues
            {"id": 4, "name": "OK_Item", "value": 175.5, "status": "inactive"}
        ])

    def tearDown(self):
        """Clean up."""
        os.chdir(self.original_cwd)
        import shutil
        shutil.rmtree(self.test_dir)

    def test_protection_with_selective_mode(self):
        """Test decorator with selective mode - continues despite issues."""

        @adri_protected(contract="selective_standard", on_failure="continue", min_score=80)
        def selective_processor(data):
            return f"Processed {len(data)} items with selective mode"

        # Even with mixed quality data, should continue execution
        result = selective_processor(self.mixed_quality_data)
        self.assertEqual(result, "Processed 4 items with selective mode")

    def test_protection_with_warn_only_mode(self):
        """Test decorator with warn-only mode - always continues."""

        @adri_protected(contract="warn_standard", on_failure="warn", min_score=90)
        def warn_only_processor(data):
            return f"Processed {len(data)} items with warnings"

        # Should continue regardless of quality
        result = warn_only_processor(self.mixed_quality_data)
        self.assertEqual(result, "Processed 4 items with warnings")

    def test_complex_function_signatures(self):
        """Test decorator with complex function signatures."""

        @adri_protected(contract="complex_standard", data_param="input_data")
        def complex_function(arg1, input_data, arg2="default", *args, **kwargs):
            return {
                "arg1": arg1,
                "data_rows": len(input_data),
                "arg2": arg2,
                "extra_args": len(args),
                "extra_kwargs": len(kwargs)
            }

        result = complex_function(
            "first_arg",
            self.high_quality_data,
            "custom_value",  # This will be arg2 positionally
            "extra1", "extra2",  # Additional positional args
            custom_param="test",
            another_param=42
        )

        expected = {
            "arg1": "first_arg",
            "data_rows": 5,
            "arg2": "custom_value",
            "extra_args": 2,
            "extra_kwargs": 2
        }
        self.assertEqual(result, expected)

    def test_dimension_requirements(self):
        """Test decorator with dimension-specific requirements."""

        @adri_protected(
            contract="dimension_standard",
            min_score=60,  # Lower overall score
            dimensions={"validity": 18, "completeness": 17}  # But specific dimension requirements
        )
        def dimension_processor(data):
            return f"Processed with dimension checks: {len(data)} rows"

        # High quality data should pass all dimension checks
        result = dimension_processor(self.high_quality_data)
        self.assertEqual(result, "Processed with dimension checks: 5 rows")

    def test_metadata_preservation(self):
        """Test that function metadata is preserved."""

        @adri_protected(contract="metadata_test")
        def documented_function(data):
            """This is a well-documented function.

            Args:
                data: Input data to process

            Returns:
                str: Processing result
            """
            return "processed"

        # Verify metadata preservation
        self.assertEqual(documented_function.__name__, "documented_function")
        self.assertIn("well-documented function", documented_function.__doc__)

        # Verify decorator attributes
        self.assertTrue(hasattr(documented_function, '_adri_protected'))
        self.assertTrue(documented_function._adri_protected)

    def test_nested_decorators(self):
        """Test ADRI decorator works with other decorators."""

        def timing_decorator(func):
            """Simple timing decorator for testing."""
            def wrapper(*args, **kwargs):
                import time
                start = time.time()
                result = func(*args, **kwargs)
                duration = time.time() - start
                return {"result": result, "duration_ms": round(duration * 1000, 2)}
            return wrapper

        @timing_decorator
        @adri_protected(contract="nested_standard")
        def nested_function(data):
            return f"Nested processing of {len(data)} items"

        result = nested_function(self.high_quality_data)

        # Should get timing wrapper result
        self.assertIn("result", result)
        self.assertIn("duration_ms", result)
        self.assertEqual(result["result"], "Nested processing of 5 items")
        self.assertIsInstance(result["duration_ms"], float)


class TestDecoratorErrorScenarios(unittest.TestCase):
    """Test decorator behavior in error scenarios."""

    def test_missing_contract_parameter(self):
        """Test that missing contract parameter raises appropriate error."""

        with self.assertRaises(ValueError) as context:
            @adri_protected()  # Missing required contract parameter
            def invalid_function(data):
                return "should not work"

        # Verify the helpful error message is provided
        error_msg = str(context.exception)
        self.assertIn("Missing required 'contract' parameter", error_msg)
        self.assertIn("@adri_protected(contract=", error_msg)

    def test_protection_engine_fallback(self):
        """Test decorator behavior when protection engine is unavailable."""

        # Temporarily disable DataProtectionEngine
        import adri.decorator as decorator_module
        original_engine = decorator_module.DataProtectionEngine

        try:
            decorator_module.DataProtectionEngine = None

            @decorator_module.adri_protected(contract="fallback_test")
            def fallback_function(data):
                return "executed without protection"

            # Should execute without protection
            result = fallback_function({"test": "data"})
            self.assertEqual(result, "executed without protection")

        finally:
            # Restore original
            decorator_module.DataProtectionEngine = original_engine

    def test_data_parameter_not_found(self):
        """Test error when specified data parameter is not found."""

        @adri_protected(contract="param_test", data_param="missing_param")
        def param_test_function(other_param):
            return "should not reach here"

        with self.assertRaises(ProtectionError) as context:
            param_test_function("some_value")

        self.assertIn("Could not find data parameter 'missing_param'", str(context.exception))


class TestAssessmentCallback(unittest.TestCase):
    """Test assessment callback functionality."""

    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)

        # Create high-quality test data
        self.test_data = pd.DataFrame([
            {"id": i, "name": f"Item_{i}", "value": 100.0 + i * 10, "status": "active"}
            for i in range(1, 6)
        ])

        # Storage for callback results
        self.callback_results = []

    def tearDown(self):
        """Clean up."""
        os.chdir(self.original_cwd)
        import shutil
        shutil.rmtree(self.test_dir)

    def test_callback_receives_assessment_result(self):
        """Test that callback receives correct assessment result."""
        captured_result = []

        def capture_assessment(result):
            captured_result.append(result)

        @adri_protected(contract="callback_test", on_assessment=capture_assessment)
        def process_data(data):
            return f"Processed {len(data)} items"

        result = process_data(self.test_data)

        # Verify function executed
        self.assertEqual(result, "Processed 5 items")

        # Verify callback was invoked
        self.assertEqual(len(captured_result), 1)

        # Verify assessment result has expected attributes
        assessment = captured_result[0]
        self.assertTrue(hasattr(assessment, 'overall_score'))
        self.assertTrue(hasattr(assessment, 'passed'))
        self.assertTrue(hasattr(assessment, 'dimension_scores'))
        self.assertIsInstance(assessment.overall_score, (int, float))

    def test_callback_captures_assessment_id(self):
        """Test capturing assessment ID via callback."""
        captured_ids = []

        def capture_id(result):
            if hasattr(result, 'assessment_id'):
                captured_ids.append(result.assessment_id)

        @adri_protected(contract="id_test", on_assessment=capture_id)
        def process_with_id(data):
            return "processed"

        process_with_id(self.test_data)

        # Verify assessment ID was captured
        self.assertEqual(len(captured_ids), 1)
        self.assertIsNotNone(captured_ids[0])
        self.assertIsInstance(captured_ids[0], str)
        # Assessment ID should follow expected format
        self.assertGreater(len(captured_ids[0]), 0)

    def test_callback_is_optional(self):
        """Test backward compatibility - callback is optional."""

        @adri_protected(contract="no_callback_test")
        def process_without_callback(data):
            return f"Processed {len(data)} items"

        # Should work without callback
        result = process_without_callback(self.test_data)
        self.assertEqual(result, "Processed 5 items")

    def test_callback_exception_handling(self):
        """Test that callback exceptions don't break decorator."""

        def failing_callback(result):
            raise ValueError("Intentional callback error")

        @adri_protected(contract="error_test", on_assessment=failing_callback)
        def process_with_failing_callback(data):
            return f"Processed {len(data)} items"

        # Function should still execute despite callback failure
        result = process_with_failing_callback(self.test_data)
        self.assertEqual(result, "Processed 5 items")

    def test_callback_with_different_modes(self):
        """Test callback works with different protection modes."""
        callback_invocations = []

        def track_callback(result):
            callback_invocations.append({
                'score': result.overall_score,
                'passed': result.passed
            })

        # Test with fail-fast mode (on_failure="raise")
        @adri_protected(contract="mode_test_raise", on_failure="raise", on_assessment=track_callback)
        def process_failfast(data):
            return "failfast"

        process_failfast(self.test_data)
        self.assertEqual(len(callback_invocations), 1)

        # Test with warn mode
        @adri_protected(contract="mode_test_warn", on_failure="warn", on_assessment=track_callback)
        def process_warn(data):
            return "warn"

        process_warn(self.test_data)
        self.assertEqual(len(callback_invocations), 2)

        # Test with continue mode
        @adri_protected(contract="mode_test_continue", on_failure="continue", on_assessment=track_callback)
        def process_continue(data):
            return "continue"

        process_continue(self.test_data)
        self.assertEqual(len(callback_invocations), 3)

    def test_callback_receives_full_result_object(self):
        """Test callback receives complete AssessmentResult with all fields."""
        captured_results = []

        def capture_full_result(result):
            captured_results.append({
                'has_overall_score': hasattr(result, 'overall_score'),
                'has_passed': hasattr(result, 'passed'),
                'has_dimension_scores': hasattr(result, 'dimension_scores'),
                'has_assessment_id': hasattr(result, 'assessment_id'),
                'has_standard_id': hasattr(result, 'standard_id'),
                'has_standard_path': hasattr(result, 'standard_path'),
                'overall_score': getattr(result, 'overall_score', None),
                'passed': getattr(result, 'passed', None)
            })

        @adri_protected(contract="full_result_test", on_assessment=capture_full_result)
        def process_full(data):
            return "full result test"

        process_full(self.test_data)

        # Verify callback was invoked
        self.assertEqual(len(captured_results), 1)

        # Verify all expected fields are present
        result_info = captured_results[0]
        self.assertTrue(result_info['has_overall_score'])
        self.assertTrue(result_info['has_passed'])
        self.assertTrue(result_info['has_dimension_scores'])
        self.assertTrue(result_info['has_assessment_id'])
        self.assertIsNotNone(result_info['overall_score'])
        self.assertIsInstance(result_info['passed'], bool)

    def test_callback_invoked_before_pass_fail_check(self):
        """Test that callback is invoked even if assessment would fail."""
        callback_invoked = []

        def track_invocation(result):
            callback_invoked.append(True)

        # Create data that might not meet high standards
        marginal_data = pd.DataFrame([
            {"id": 1, "name": "Item", "value": 100.0},
            {"id": None, "name": "", "value": -50.0}  # Some issues
        ])

        @adri_protected(
            contract="fail_test",
            min_score=95,  # Very high threshold
            on_failure="warn",  # Don't raise error
            on_assessment=track_invocation
        )
        def process_marginal(data):
            return "processed"

        process_marginal(marginal_data)

        # Callback should be invoked regardless of pass/fail
        self.assertTrue(len(callback_invoked) > 0)

    def test_callback_with_workflow_context(self):
        """Test callback works alongside workflow context tracking."""
        captured_assessments = []

        def capture_with_context(result):
            captured_assessments.append({
                'assessment_id': getattr(result, 'assessment_id', None),
                'score': result.overall_score
            })

        workflow_context = {
            "run_id": "test_run_123",
            "workflow_id": "test_workflow",
            "step_id": "callback_test_step"
        }

        @adri_protected(
            contract="workflow_callback_test",
            workflow_context=workflow_context,
            on_assessment=capture_with_context
        )
        def process_with_workflow(data):
            return "workflow test"

        process_with_workflow(self.test_data)

        # Verify callback was invoked
        self.assertEqual(len(captured_assessments), 1)
        self.assertIsNotNone(captured_assessments[0]['assessment_id'])
        self.assertIsInstance(captured_assessments[0]['score'], (int, float))

    def test_multiple_invocations_separate_callbacks(self):
        """Test that each function invocation triggers callback separately."""
        invocation_count = []

        def count_invocations(result):
            invocation_count.append(result.overall_score)

        @adri_protected(contract="multi_invoke_test", on_assessment=count_invocations)
        def process_multiple(data):
            return f"Processed {len(data)}"

        # Invoke multiple times
        process_multiple(self.test_data)
        process_multiple(self.test_data)
        process_multiple(self.test_data)

        # Should have three separate callback invocations
        self.assertEqual(len(invocation_count), 3)


if __name__ == '__main__':
    unittest.main()
