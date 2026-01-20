"""
End-to-end integration tests for enterprise components.

Tests covering:
- Complete enterprise decorator workflow with all components
- License validation + reasoning logging + Verodat API integration
- Enterprise configuration with environment-aware contract resolution
- Complex data processing workflows with enterprise features
- Error propagation and recovery across enterprise systems
"""

import os
import tempfile
import time
from pathlib import Path
from unittest.mock import patch, MagicMock
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
import pytest

from adri_enterprise.decorator import adri_protected
from adri_enterprise.config import EnterpriseConfigurationLoader
from adri_enterprise.license import get_validator, LicenseValidationError
from adri_enterprise.logging.reasoning import ReasoningLogger
from adri_enterprise.logging.verodat import VerodatLogger


@pytest.mark.integration
class TestCompleteEnterpriseWorkflow:
    """Test suite for complete end-to-end enterprise workflows."""

    def test_full_enterprise_decorator_workflow(
        self,
        temp_config_dir,
        temp_log_dir,
        mock_workflow_context,
        mock_data_provenance,
        mock_verodat_api_success,
        clean_license_cache
    ):
        """Test complete enterprise decorator workflow with all features."""
        # Setup test data
        test_data = pd.DataFrame({
            "customer_id": [1, 2, 3, 4, 5],
            "name": ["Alice", "Bob", "Charlie", "Dana", "Eve"],
            "email": ["alice@example.com", "bob@example.com", "charlie@example.com", "dana@example.com", "eve@example.com"],
            "score": [85.5, 92.3, 78.1, 96.7, 88.9],
            "status": ["active", "active", "inactive", "active", "active"]
        })

        with patch.dict(os.environ, {
            'VERODAT_API_KEY': 'full-workflow-test-key',
            'ADRI_CONFIG_PATH': temp_config_dir['config_file'],
            'ADRI_ENV': 'production'
        }):
            # Mock license validation success
            with patch('adri_enterprise.decorator.validate_license') as mock_validate:
                mock_validate.return_value = MagicMock(is_valid=True)

                @adri_protected(
                    contract="test_full_workflow_contract",
                    environment="production",
                    reasoning_mode=True,
                    workflow_context=mock_workflow_context,
                    data_provenance=mock_data_provenance,
                    min_score=80,
                    on_failure="raise",
                    verbose=True,
                    auto_generate=True
                )
                def process_enterprise_data(data):
                    """Process data with full enterprise protection."""
                    # Simulate processing
                    processed = data.copy()
                    processed['processed_at'] = pd.Timestamp.now()
                    processed['quality_score'] = processed['score'] * 1.1
                    return processed

                # Execute the workflow
                result = process_enterprise_data(test_data)

                # Verify results
                assert len(result) == 5
                assert 'processed_at' in result.columns
                assert 'quality_score' in result.columns
                assert all(result['quality_score'] > result['score'])

                # Verify license validation was called
                mock_validate.assert_called_once()

                # Verify function has enterprise markers
                assert hasattr(process_enterprise_data, '_adri_protected')
                assert hasattr(process_enterprise_data, '_adri_enterprise')
                assert process_enterprise_data._adri_enterprise is True

    def test_enterprise_decorator_with_reasoning_logging(
        self,
        temp_log_dir,
        mock_reasoning_data,
        clean_license_cache,
        mock_verodat_api_success
    ):
        """Test enterprise decorator with reasoning step logging."""
        test_data = pd.DataFrame({
            "id": [1, 2, 3],
            "value": [10, 20, 30]
        })

        with patch.dict(os.environ, {'VERODAT_API_KEY': 'reasoning-test-key'}):

            # Mock reasoning logger creation in decorator
            with patch('adri_enterprise.logging.reasoning.ReasoningLogger') as MockReasoningLogger:
                mock_logger = MagicMock()
                mock_logger.log_reasoning_step.return_value = ("prompt_123", "response_456")
                MockReasoningLogger.return_value = mock_logger

                @adri_protected(
                    contract="test_reasoning_contract",
                    reasoning_mode=True,
                    store_prompt=True,
                    store_response=True,
                    llm_config=mock_reasoning_data['llm_config'],
                    verbose=True,
                    auto_generate=True
                )
                def analyze_with_reasoning(data):
                    """Analyze data with AI reasoning."""
                    return {
                        'analysis': 'Data appears well-structured',
                        'quality_score': 88.5,
                        'recommendations': ['Add validation', 'Check duplicates']
                    }

                # Execute function
                result = analyze_with_reasoning(test_data)

                # Verify analysis result
                assert result['quality_score'] == 88.5
                assert 'analysis' in result
                assert len(result['recommendations']) == 2

    def test_environment_aware_contract_resolution_integration(
        self,
        temp_config_dir,
        clean_license_cache,
        mock_verodat_api_success
    ):
        """Test environment-aware contract resolution in enterprise workflow."""
        test_data = pd.DataFrame({
            "transaction_id": [1, 2, 3],
            "amount": [100.50, 250.00, 175.25]
        })

        with patch.dict(os.environ, {
            'VERODAT_API_KEY': 'env-resolution-test-key',
            'ADRI_CONFIG_PATH': temp_config_dir['config_file']
        }):

            # Test with development environment
            with patch.dict(os.environ, {'ADRI_ENV': 'development'}):

                @adri_protected(
                    contract="test_env_contract",
                    environment="development",  # Should use dev paths
                    min_score=70,  # Dev has lower threshold
                    on_failure="warn",  # Dev uses warn mode
                    verbose=True,
                    auto_generate=True
                )
                def process_dev_data(data):
                    return len(data)

                dev_result = process_dev_data(test_data)
                assert dev_result == 3

            # Test with production environment
            with patch.dict(os.environ, {'ADRI_ENV': 'production'}):

                @adri_protected(
                    contract="test_env_contract",
                    environment="production",  # Should use prod paths
                    min_score=85,  # Prod has higher threshold
                    on_failure="raise",  # Prod uses raise mode
                    verbose=True,
                    auto_generate=True
                )
                def process_prod_data(data):
                    return len(data)

                prod_result = process_prod_data(test_data)
                assert prod_result == 3

    def test_enterprise_workflow_with_all_logging_components(
        self,
        temp_log_dir,
        mock_workflow_context,
        mock_data_provenance,
        mock_reasoning_data,
        clean_license_cache,
        mock_verodat_api_success
    ):
        """Test complete workflow with all logging components active."""
        test_data = pd.DataFrame({
            "project_id": [1, 2],
            "risk_score": [75, 82]
        })

        # Setup all loggers
        reasoning_logger = ReasoningLogger(log_dir=temp_log_dir)
        verodat_logger = VerodatLogger("https://test.api.com", "all-logging-key")

        with patch.dict(os.environ, {'VERODAT_API_KEY': 'all-logging-test-key'}):

            @adri_protected(
                contract="test_all_logging_contract",
                reasoning_mode=True,
                workflow_context=mock_workflow_context,
                data_provenance=mock_data_provenance,
                store_prompt=True,
                store_response=True,
                llm_config=mock_reasoning_data['llm_config'],
                verbose=True,
                auto_generate=True
            )
            def comprehensive_analysis(data):
                """Comprehensive analysis with all enterprise features."""
                # Log reasoning step manually (simulating what decorator does)
                prompt_id, response_id = reasoning_logger.log_reasoning_step(
                    prompt="Analyze project risk data",
                    response="Risk analysis complete",
                    assessment_id="comprehensive_test_001"
                )

                # Log to Verodat (simulating what decorator does)
                assessment_data = {
                    "assessment_id": "comprehensive_test_001",
                    "overall_score": data['risk_score'].mean(),
                    "reasoning_prompt_id": prompt_id,
                    "reasoning_response_id": response_id
                }

                with patch('requests.post') as mock_post:
                    mock_response = MagicMock()
                    mock_response.status_code = 200
                    mock_post.return_value = mock_response

                    verodat_logger.log_assessment(
                        assessment_data=assessment_data,
                        workflow_context=mock_workflow_context,
                        data_provenance=mock_data_provenance
                    )

                return {
                    'mean_risk_score': data['risk_score'].mean(),
                    'prompt_id': prompt_id,
                    'response_id': response_id
                }

            # Execute comprehensive workflow
            result = comprehensive_analysis(test_data)

            # Verify all components worked
            assert result['mean_risk_score'] == 78.5
            assert result['prompt_id'].startswith('prompt_')
            assert result['response_id'].startswith('response_')

            # Verify reasoning logs were created
            assert reasoning_logger.prompt_log_file.exists()
            assert reasoning_logger.response_log_file.exists()

    def test_enterprise_error_propagation_and_recovery(
        self,
        clean_license_cache
    ):
        """Test error propagation and recovery across enterprise systems."""
        test_data = pd.DataFrame({"id": [1, 2, 3]})

        # Test license validation failure propagation
        with patch.dict(os.environ, {}, clear=True):  # No API key
            # Mock validate_license to raise the error
            with patch('adri_enterprise.decorator.validate_license') as mock_validate:
                mock_validate.side_effect = LicenseValidationError("No API key provided")

                @adri_protected(
                    contract="test_error_propagation",
                    reasoning_mode=True,
                    auto_generate=True
                )
                def failing_function(data):
                    return len(data)

                with pytest.raises(LicenseValidationError):
                    failing_function(test_data)

        # Test recovery after license validation success
        with patch.dict(os.environ, {'VERODAT_API_KEY': 'recovery-test-key'}):
            with patch('adri_enterprise.decorator.validate_license') as mock_validate:
                mock_validate.return_value = MagicMock(is_valid=True)

                @adri_protected(
                    contract="test_error_recovery",
                    auto_generate=True
                )
                def recovering_function(data):
                    return len(data)

                # Should work now with valid license
                result = recovering_function(test_data)
                assert result == 3

    def test_concurrent_enterprise_workflows(
        self,
        clean_license_cache,
        mock_verodat_api_success
    ):
        """Test multiple concurrent enterprise workflows."""
        test_data = pd.DataFrame({
            "user_id": [1, 2, 3, 4, 5],
            "activity_score": [85, 90, 78, 95, 82]
        })

        with patch.dict(os.environ, {'VERODAT_API_KEY': 'concurrent-test-key'}):

            @adri_protected(
                contract="test_concurrent_workflow",
                reasoning_mode=True,
                verbose=False,  # Reduce logging in concurrent tests
                auto_generate=True
            )
            def concurrent_analysis(data, analysis_id):
                """Analyze data concurrently."""
                time.sleep(0.1)  # Simulate processing time
                return {
                    'analysis_id': analysis_id,
                    'mean_score': data['activity_score'].mean(),
                    'record_count': len(data)
                }

            def run_concurrent_analysis(analysis_id):
                return concurrent_analysis(test_data, f"concurrent_{analysis_id}")

            # Run multiple analyses concurrently
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = [
                    executor.submit(run_concurrent_analysis, i)
                    for i in range(10)
                ]
                results = [future.result() for future in as_completed(futures)]

            # Verify all analyses completed successfully
            assert len(results) == 10
            for result in results:
                assert result['mean_score'] == test_data['activity_score'].mean()
                assert result['record_count'] == 5
                assert 'concurrent_' in result['analysis_id']


@pytest.mark.integration
class TestEnterpriseConfigurationIntegration:
    """Integration tests for enterprise configuration system."""

    def test_configuration_loader_with_decorator_integration(
        self,
        temp_config_dir,
        clean_license_cache,
        mock_verodat_api_success
    ):
        """Test configuration loader integration with decorator."""
        loader = EnterpriseConfigurationLoader()

        with patch.dict(os.environ, {
            'ADRI_CONFIG_PATH': temp_config_dir['config_file'],
            'VERODAT_API_KEY': 'config-integration-key'
        }):
            # Clear any existing contracts directory override
            with patch.dict(os.environ, {'ADRI_CONTRACTS_DIR': ''}, clear=False):
                # Test contract path resolution
                dev_path = loader.resolve_contract_path("integration_test", "development")
                prod_path = loader.resolve_contract_path("integration_test", "production")

                # Should resolve to environment-specific paths (platform-independent)
                assert ("dev" in dev_path and "contracts" in dev_path) or "development" in dev_path
                assert ("prod" in prod_path and "contracts" in prod_path) or "production" in prod_path
                assert dev_path != prod_path

                # Test decorator uses resolved paths
                test_data = pd.DataFrame({"id": [1, 2], "value": [10, 20]})

                @adri_protected(
                    contract="integration_test",
                    environment="development",
                    auto_generate=True
                )
                def test_config_integration(data):
                    return len(data)

                result = test_config_integration(test_data)
                assert result == 2

    def test_environment_switching_integration(
        self,
        temp_config_dir,
        clean_license_cache,
        mock_verodat_api_success
    ):
        """Test dynamic environment switching in workflows."""
        test_data = pd.DataFrame({"metric": [1, 2, 3]})

        with patch.dict(os.environ, {
            'ADRI_CONFIG_PATH': temp_config_dir['config_file'],
            'VERODAT_API_KEY': 'env-switching-key'
        }):

            # Function that switches environments
            def process_in_environment(env_name):
                @adri_protected(
                    contract="env_switching_test",
                    environment=env_name,
                    auto_generate=True
                )
                def env_specific_processing(data):
                    return {
                        'environment': env_name,
                        'record_count': len(data),
                        'processed': True
                    }

                return env_specific_processing(test_data)

            # Test processing in different environments
            dev_result = process_in_environment("development")
            prod_result = process_in_environment("production")

            assert dev_result['environment'] == "development"
            assert prod_result['environment'] == "production"
            assert dev_result['record_count'] == prod_result['record_count'] == 3

    def test_configuration_validation_integration(
        self,
        temp_config_dir,
        clean_license_cache,
        mock_verodat_api_success
    ):
        """Test configuration validation in enterprise workflows."""
        loader = EnterpriseConfigurationLoader()

        with patch.dict(os.environ, {
            'ADRI_CONFIG_PATH': temp_config_dir['config_file'],
            'VERODAT_API_KEY': 'config-validation-key'
        }):

            # Load and validate configuration
            config = loader.load_config(temp_config_dir['config_file'])
            assert loader.validate_config(config) is True

            # Test that invalid environment raises error
            with pytest.raises(ValueError, match="staging"):
                loader.get_environment_config(config, "staging")  # Non-existent env

            # Test valid environments work
            dev_config = loader.get_environment_config(config, "development")
            prod_config = loader.get_environment_config(config, "production")

            assert dev_config['paths']['contracts'] == "./dev/contracts"
            assert prod_config['paths']['contracts'] == "./prod/contracts"


@pytest.mark.integration
class TestEnterpriseLoggingIntegration:
    """Integration tests for enterprise logging systems."""

    def test_reasoning_and_verodat_logging_coordination(
        self,
        temp_log_dir,
        mock_reasoning_data,
        mock_workflow_context,
        mock_data_provenance
    ):
        """Test coordination between reasoning logger and Verodat logger."""
        reasoning_logger = ReasoningLogger(log_dir=temp_log_dir)
        verodat_logger = VerodatLogger("https://test.api.com", "coordination-key", batch_size=1)

        # Log reasoning step
        prompt_id, response_id = reasoning_logger.log_reasoning_step(
            prompt=mock_reasoning_data['prompt'],
            response=mock_reasoning_data['response'],
            assessment_id="coordination_test_001",
            function_name="test_coordination"
        )

        # Send coordinated assessment to Verodat
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response

            assessment_data = {
                "assessment_id": "coordination_test_001",
                "function_name": "test_coordination",
                "reasoning_prompt_id": prompt_id,
                "reasoning_response_id": response_id,
                "local_reasoning_logs": True
            }

            result = verodat_logger.log_assessment(
                assessment_data=assessment_data,
                workflow_context=mock_workflow_context,
                data_provenance=mock_data_provenance
            )

            assert result is True

            # Verify reasoning IDs were linked
            sent_data = mock_post.call_args[1]["json"]
            batch_data = sent_data["batch"][0]
            assert batch_data["reasoning_prompt_id"] == prompt_id
            assert batch_data["reasoning_response_id"] == response_id

        # Verify local reasoning logs exist
        assert reasoning_logger.prompt_log_file.exists()
        assert reasoning_logger.response_log_file.exists()

        # Verify reasoning history can be retrieved
        history = reasoning_logger.get_reasoning_history(
            assessment_id="coordination_test_001"
        )
        assert len(history) >= 2  # At least prompt and response

    def test_logging_failure_isolation(
        self,
        temp_log_dir,
        clean_license_cache,
        mock_verodat_api_success
    ):
        """Test that logging failures don't break main workflow."""
        test_data = pd.DataFrame({"id": [1, 2, 3], "value": [10, 20, 30]})

        with patch.dict(os.environ, {'VERODAT_API_KEY': 'isolation-test-key'}):

            # Mock reasoning logger to fail
            with patch('adri_enterprise.logging.reasoning.ReasoningLogger') as MockReasoningLogger:
                mock_logger = MagicMock()
                mock_logger.log_reasoning_step.side_effect = Exception("Logging failed")
                MockReasoningLogger.return_value = mock_logger

                @adri_protected(
                    contract="test_logging_isolation",
                    reasoning_mode=True,
                    verbose=False,  # Reduce error output in tests
                    auto_generate=True
                )
                def resilient_function(data):
                    """Function that should work despite logging failures."""
                    return data.sum().sum()

                # Should still work despite logging failure
                result = resilient_function(test_data)
                assert result == 66  # Sum of all values

    def test_batch_logging_performance_integration(
        self,
        temp_log_dir
    ):
        """Test performance of integrated logging systems."""
        reasoning_logger = ReasoningLogger(log_dir=temp_log_dir)
        verodat_logger = VerodatLogger("https://test.api.com", "batch-perf-key", batch_size=10)

        # Simulate processing multiple assessments
        assessments = []
        reasoning_ids = []

        start_time = time.time()

        for i in range(25):
            # Log reasoning step
            prompt_id, response_id = reasoning_logger.log_reasoning_step(
                prompt=f"Batch analysis prompt {i}",
                response=f"Batch analysis response {i}",
                assessment_id=f"batch_perf_{i:03d}"
            )
            reasoning_ids.append((prompt_id, response_id))

            # Prepare assessment for Verodat
            assessment = {
                "assessment_id": f"batch_perf_{i:03d}",
                "overall_score": 80 + (i % 20),
                "reasoning_prompt_id": prompt_id,
                "reasoning_response_id": response_id
            }
            assessments.append(assessment)

        # Send all assessments to Verodat
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response

            for assessment in assessments:
                verodat_logger.log_assessment(assessment)

            # Flush remaining batch
            verodat_logger.close()

        end_time = time.time()

        # Verify performance
        total_time = end_time - start_time
        assessments_per_second = len(assessments) / total_time

        # Should process at least 5 assessments per second
        assert assessments_per_second >= 5.0

        # Verify all reasoning IDs were generated
        assert len(reasoning_ids) == 25
        for prompt_id, response_id in reasoning_ids:
            assert prompt_id.startswith("prompt_")
            assert response_id.startswith("response_")


@pytest.mark.integration
class TestEnterpriseLicenseIntegration:
    """Integration tests for license validation with other systems."""

    def test_license_validation_caching_across_workflows(
        self,
        clean_license_cache,
        mock_verodat_api_success
    ):
        """Test license caching across multiple enterprise workflows."""
        test_data = pd.DataFrame({"metric": [1, 2, 3]})

        with patch.dict(os.environ, {'VERODAT_API_KEY': 'caching-test-key'}):

            # First workflow - should validate license
            @adri_protected(
                contract="test_caching_workflow_1",
                auto_generate=True
            )
            def first_workflow(data):
                return len(data)

            # Second workflow - should use cached license
            @adri_protected(
                contract="test_caching_workflow_2",
                auto_generate=True
            )
            def second_workflow(data):
                return data.sum().sum()

            # Execute both workflows
            result1 = first_workflow(test_data)
            result2 = second_workflow(test_data)

            assert result1 == 3
            assert result2 == 6

            # License should only be validated once (cached for second use)
            validator = get_validator()
            assert validator.is_validated is True

            # API should only be called once due to caching
            assert mock_verodat_api_success['get'].call_count == 1

    def test_license_expiration_and_revalidation_integration(
        self,
        clean_license_cache,
        mock_verodat_api_success
    ):
        """Test license expiration and automatic revalidation."""
        from datetime import timedelta
        test_data = pd.DataFrame({"value": [10, 20, 30]})

        with patch.dict(os.environ, {'VERODAT_API_KEY': 'expiration-test-key'}):

            # Set very short cache duration for testing
            validator = get_validator()
            original_duration = validator._validation_cache_duration
            validator._validation_cache_duration = timedelta(milliseconds=100)

            try:
                @adri_protected(
                    contract="test_expiration_workflow",
                    auto_generate=True
                )
                def workflow_with_expiration(data):
                    return data.mean().iloc[0]

                # First execution
                result1 = workflow_with_expiration(test_data)
                assert result1 == 20.0
                assert mock_verodat_api_success['get'].call_count == 1

                # Wait for cache to expire
                time.sleep(0.2)

                # Second execution - should revalidate
                result2 = workflow_with_expiration(test_data)
                assert result2 == 20.0
                assert mock_verodat_api_success['get'].call_count == 2  # Revalidated

            finally:
                # Restore original duration
                validator._validation_cache_duration = original_duration

    def test_license_failure_recovery_integration(
        self,
        clean_license_cache
    ):
        """Test recovery from license validation failures."""
        test_data = pd.DataFrame({"id": [1, 2]})

        # First attempt - no API key (should fail)
        with patch.dict(os.environ, {}, clear=True):

            @adri_protected(
                contract="test_failure_recovery",
                auto_generate=True
            )
            def recovery_workflow(data):
                return len(data)

            with pytest.raises(LicenseValidationError):
                recovery_workflow(test_data)

        # Second attempt - valid API key (should recover)
        with patch.dict(os.environ, {'VERODAT_API_KEY': 'recovery-key'}):
            with patch('requests.get') as mock_get:
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.json.return_value = {"accountId": 91, "username": "test"}
                mock_get.return_value = mock_response

                # Should work now
                result = recovery_workflow(test_data)
                assert result == 2

                # License should be validated
                validator = get_validator()
                assert validator.is_validated is True


@pytest.mark.performance
class TestEnterpriseIntegrationPerformance:
    """Performance tests for integrated enterprise systems."""

    def test_end_to_end_performance_baseline(
        self,
        performance_baseline,
        clean_license_cache,
        mock_verodat_api_success
    ):
        """Test end-to-end enterprise workflow performance."""
        # Create moderately sized test data
        test_data = pd.DataFrame({
            "id": range(100),
            "score": [80 + (i % 20) for i in range(100)],
            "category": [f"cat_{i % 5}" for i in range(100)]
        })

        with patch.dict(os.environ, {'VERODAT_API_KEY': 'performance-baseline-key'}):

            @adri_protected(
                contract="test_performance_baseline",
                reasoning_mode=False,  # Disable for baseline performance
                verbose=False,  # Reduce logging overhead
                auto_generate=True
            )
            def baseline_workflow(data):
                """Baseline enterprise workflow."""
                processed = data.copy()
                processed['processed_score'] = processed['score'] * 1.1
                processed['quality_flag'] = processed['score'] > 85
                return processed.groupby('category')['score'].mean()

            # Measure performance
            start_time = time.time()
            result = baseline_workflow(test_data)
            end_time = time.time()

            # Verify results
            assert len(result) == 5  # 5 categories
            assert all(result > 0)

            # Verify performance meets baseline
            execution_time = end_time - start_time
            # Use decorator overhead baseline (should complete within that time)
            assert execution_time < performance_baseline['decorator_overhead_max_time'] * 10

    def test_concurrent_enterprise_workflows_performance(
        self,
        clean_license_cache,
        mock_verodat_api_success
    ):
        """Test performance with concurrent enterprise workflows."""
        test_data = pd.DataFrame({
            "transaction_id": range(50),
            "amount": [100 + (i * 5) for i in range(50)]
        })

        with patch.dict(os.environ, {'VERODAT_API_KEY': 'concurrent-perf-key'}):

            @adri_protected(
                contract="test_concurrent_performance",
                verbose=False,
                auto_generate=True
            )
            def concurrent_workflow(data, workflow_id):
                """Workflow for concurrent performance testing."""
                time.sleep(0.05)  # Simulate processing
                return {
                    'workflow_id': workflow_id,
                    'mean_amount': data['amount'].mean(),
                    'transaction_count': len(data)
                }

            def run_workflow(workflow_id):
                return concurrent_workflow(test_data, workflow_id)

            # Run concurrent workflows
            start_time = time.time()

            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = [
                    executor.submit(run_workflow, f"perf_test_{i}")
                    for i in range(20)
                ]
                results = [future.result() for future in as_completed(futures)]

            end_time = time.time()

            # Verify all workflows completed
            assert len(results) == 20
            for result in results:
                assert result['mean_amount'] > 0
                assert result['transaction_count'] == 50
                assert 'perf_test_' in result['workflow_id']

            # Performance should benefit from concurrency and license caching
            total_time = end_time - start_time
            assert total_time < 5.0  # Should complete within 5 seconds

            # License should only be validated once (shared across all workflows)
            assert mock_verodat_api_success['get'].call_count == 1
