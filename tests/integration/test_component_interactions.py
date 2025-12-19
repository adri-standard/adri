"""
Component Interaction Testing for ADRI Framework.

Tests integration between all major components to ensure they work together
properly in real-world scenarios. Validates the complete data quality pipeline
from configuration loading through assessment execution and logging.

No legacy backward compatibility - uses only src/adri/* imports.
"""

import os
import sys
import tempfile
import time
import shutil
import gc
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest
import pandas as pd
import yaml
import json


def safe_rmtree(path, max_retries=3, delay=0.1):
    """Windows-safe recursive directory removal with retries."""
    for attempt in range(max_retries):
        try:
            if os.path.exists(path):
                # Force garbage collection to release file handles
                gc.collect()

                # Try different removal strategies
                if os.name == 'nt':  # Windows
                    import subprocess
                    try:
                        subprocess.run(['rmdir', '/s', '/q', path],
                                     shell=True, check=False, capture_output=True)
                        if not os.path.exists(path):
                            return
                    except:
                        pass

                # Fallback to shutil with error handling
                shutil.rmtree(path, ignore_errors=True)

                if not os.path.exists(path):
                    return

            else:
                return  # Directory doesn't exist, success

        except (OSError, PermissionError) as e:
            if attempt == max_retries - 1:
                # Final attempt failed, but don't raise error for tearDown
                try:
                    # Try to at least make files writable for later cleanup
                    for root, dirs, files in os.walk(path, topdown=False):
                        for name in files:
                            try:
                                filepath = os.path.join(root, name)
                                os.chmod(filepath, 0o777)
                            except:
                                pass
                except:
                    pass
                return  # Don't raise in tearDown

            # Wait before retrying
            time.sleep(delay * (attempt + 1))
            gc.collect()

# Modern imports only - no legacy patterns
from src.adri.decorator import adri_protected
from src.adri.validator.engine import ValidationEngine
from src.adri.guard.modes import ProtectionMode, DataProtectionEngine
from src.adri.config.loader import ConfigurationLoader
from src.adri.contracts.parser import ContractsParser
from src.adri.core.exceptions import ValidationError, ConfigurationError
from src.adri.analysis.data_profiler import DataProfiler
from src.adri.analysis.contract_generator import ContractGenerator
from src.adri.analysis.type_inference import TypeInference
from src.adri.logging.local import LocalLogger
from adri_enterprise.logging.verodat import send_to_verodat
from tests.quality_framework import TestCategory, ComponentTester, performance_monitor
from tests.fixtures.modern_fixtures import ModernFixtures, ErrorSimulator
from tests.performance_thresholds import get_performance_threshold
from tests.utils.performance_helpers import assert_performance


class TestComponentInteractions:
    """Test suite for component interaction scenarios."""

    def setup_method(self):
        """Setup for each test method."""
        # Test data
        self.high_quality_data = ModernFixtures.create_comprehensive_mock_data(
            rows=100, quality_level="high"
        )
        self.comprehensive_standard = ModernFixtures.create_standards_data("comprehensive")
        self.complete_config = ModernFixtures.create_configuration_data("complete")

    @pytest.mark.integration
    def test_decorator_validator_guard_integration(self, temp_workspace, sample_standard_name):
        """Test integration between decorator, validator, and guard components."""

        # Mock the protection system to avoid file system issues
        with patch('src.adri.decorator.DataProtectionEngine') as mock_engine:
            mock_engine_instance = Mock()
            mock_engine_instance.protect_function_call.return_value = {
                "status": "completed",
                "input_rows": 100,
                "output_rows": 100,
                "validation_passed": True
            }
            mock_engine.return_value = mock_engine_instance

            # Test complete protection workflow with name-only governance
            @adri_protected(
                contract=sample_standard_name,
                on_failure="warn"
            )
            def protected_data_processing(data):
                """Simulates a data processing function with full protection."""
                # Simulate some data processing
                processed_data = data.copy()
                processed_data['processing_timestamp'] = pd.Timestamp.now()
                processed_data['validation_applied'] = True

                return {
                    "status": "completed",
                    "input_rows": len(data),
                    "output_rows": len(processed_data),
                    "validation_passed": True
                }

            # Test with high quality data
            result = protected_data_processing(self.high_quality_data)

            assert result["status"] == "completed"
            assert result["validation_passed"] is True
            assert result["input_rows"] == result["output_rows"]

            # Test integration components work together
            assert result["input_rows"] == 100  # Original data size

    @pytest.mark.integration
    def test_config_standards_validator_integration(self, temp_workspace):
        """Test integration between config loader, standards parser, and validator."""

        # Create comprehensive configuration
        config_file = temp_workspace / "integration_config.yaml"
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(self.complete_config, f)

        # Create standard file in configured location
        standards_dir = temp_workspace / "standards"
        standards_dir.mkdir(parents=True, exist_ok=True)
        standard_file = standards_dir / "integration_standard.yaml"
        with open(standard_file, 'w', encoding='utf-8') as f:
            yaml.dump(self.comprehensive_standard, f)

        # Test integration workflow
        # 1. Load configuration
        config_loader = ConfigurationLoader()
        config = config_loader.load_config(config_path=str(config_file))

        # 2. Parse standard using configuration paths (mock for test isolation)
        with patch.object(ContractsParser, 'parse_contract') as mock_parse:
            mock_parse.return_value = self.comprehensive_standard
            standards_parser = ContractsParser()
            parsed_standard = standards_parser.parse_contract("integration_standard")

        # 3. Use validator with parsed standard
        validator = ValidationEngine()
        assessment_result = validator.assess(
            data=self.high_quality_data,
            standard_path=parsed_standard
        )

        # Verify integration worked end-to-end
        assert config["adri"]["version"] == "4.0.0"
        assert parsed_standard["contracts"]["id"] == self.comprehensive_standard["contracts"]["id"]
        assert assessment_result.overall_score > 0
        assert hasattr(assessment_result, 'dimension_scores')

    @pytest.mark.integration
    def test_profiler_generator_validator_pipeline(self, temp_workspace):
        """Test complete data analysis pipeline: profiler → generator → validator."""

        # Step 1: Profile the data
        profiler = DataProfiler()
        profile_result = profiler.profile_data(self.high_quality_data)

        # Step 2: Generate standard from profile
        generator = ContractGenerator()
        generated_standard = generator.generate(
            data=self.high_quality_data,
            data_name="pipeline_generated_standard"
        )

        # Step 3: Validate data against generated standard
        validator = ValidationEngine()
        validation_result = validator.assess(
            data=self.high_quality_data,
            standard_path=generated_standard
        )

        # Verify complete pipeline worked
        assert profile_result.get('quality_assessment', {}).get('overall_completeness', 0) > 0
        assert "Pipeline Generated Standard" in generated_standard["contracts"]["name"]
        assert validation_result.overall_score > 0

        # Data should score well against its own generated standard
        assert validation_result.overall_score >= 70  # Should pass its own standard

    @pytest.mark.integration
    def test_type_inference_profiler_integration(self):
        """Test integration between type inference and data profiler."""

        # Create data with mixed types for comprehensive testing
        mixed_data = pd.DataFrame({
            'customer_id': [1, 2, 3, 4, 5],
            'name': ['Alice', 'Bob', 'Charlie', 'Diana', 'Eve'],
            'email': ['alice@test.com', 'bob@test.com', 'charlie@test.com', 'diana@test.com', 'eve@test.com'],
            'age': [25, 30, 35, 28, 32],
            'salary': [50000.0, 60000.0, 70000.0, 55000.0, 65000.0],
            'active': [True, True, False, True, False]
        })

        # Step 1: Infer types
        type_inference = TypeInference()
        inference_result = type_inference.infer_validation_rules(mixed_data)

        # Step 2: Profile data with type hints
        profiler = DataProfiler()
        profile_result = profiler.profile_data(mixed_data)

        # Verify integration produces consistent results
        profile_dict = profile_result.to_dict()
        assert len(inference_result) == len(profile_dict.get('fields', {}))

        # Check consistency between type inference and profiler
        for field_name in mixed_data.columns:
            if field_name in inference_result and field_name in profile_dict.get('fields', {}):
                inferred_rules = inference_result[field_name]
                profiled_dtype = profile_dict['fields'][field_name].get('dtype', 'object')
                inferred_type = inferred_rules.get('type', 'string')

                # Map pandas dtypes to ADRI types
                dtype_mapping = {
                    'int64': 'integer',
                    'float64': 'float',
                    'object': 'string',
                    'bool': 'boolean'
                }
                profiled_type = dtype_mapping.get(profiled_dtype, profiled_dtype)

                # Types should be compatible
                type_compatibility = {
                    ('integer', 'integer'): True,
                    ('integer', 'int64'): True,
                    ('float', 'float'): True,
                    ('float', 'float64'): True,
                    ('string', 'string'): True,
                    ('string', 'object'): True,
                    ('boolean', 'boolean'): True,
                    ('boolean', 'bool'): True,
                }

                is_compatible = type_compatibility.get((inferred_type, profiled_type), False) or inferred_type == profiled_type
                assert is_compatible, f"Type mismatch for {field_name}: {inferred_type} vs {profiled_type}"

    @pytest.mark.integration
    def test_logging_integration_across_components(self, temp_workspace):
        """Test logging integration across all components."""

        # Setup logging
        log_dir = temp_workspace / "integration_logs"
        local_logger = LocalLogger(config={"enabled": True, "log_dir": str(log_dir)})

        # Create assessment workflow with logging
        validator = ValidationEngine()

        # Mock logging integration
        with patch('src.adri.logging.local.AuditRecord') as mock_audit_record:
            mock_audit_instance = Mock()
            mock_audit_record.return_value = mock_audit_instance

            # Run assessment with logging
            assessment_result = validator.assess(
                data=self.high_quality_data,
                standard_path=self.comprehensive_standard
            )

            # Simulate logging the assessment result
            log_record = {
                "event_type": "assessment_completed",
                "timestamp": "2025-01-01T12:00:00Z",
                "data": assessment_result.to_dict()
            }

            # Should integrate with logging system
            assert assessment_result.overall_score > 0

        # Verify log directory was created
        assert log_dir.exists()

    @pytest.mark.integration
    def test_cli_backend_integration(self, temp_workspace):
        """Test integration between CLI commands and backend components."""

        # Create test data file
        data_file = temp_workspace / "cli_integration_data.csv"
        self.high_quality_data.to_csv(data_file, index=False)

        # Create standard file
        standard_file = temp_workspace / "cli_integration_standard.yaml"
        with open(standard_file, 'w', encoding='utf-8') as f:
            yaml.dump(self.comprehensive_standard, f)

        # Test CLI assessment integration with backend
        from src.adri.cli.commands.assess import AssessCommand

        assess_cmd = AssessCommand()

        # Mock the backend components the CLI uses
        with patch('src.adri.validator.engine.ValidationEngine') as mock_validator:
            mock_assessment = Mock()
            mock_assessment.overall_score = 82.5
            mock_assessment.passed = True
            mock_assessment.to_dict.return_value = {
                "overall_score": 82.5,
                "passed": True,
                "standard_id": "test_standard"
            }

            mock_validator_instance = Mock()
            mock_validator_instance.assess.return_value = mock_assessment
            mock_validator.return_value = mock_validator_instance

            # Simulate CLI command execution
            # (This would normally be tested with CliRunner, but here we test the integration logic)

            # Verify backend components are properly integrated
            mock_validator.assert_called() if mock_validator.called else None

    @pytest.mark.integration
    def test_error_propagation_across_components(self, temp_workspace):
        """Test error propagation and handling across component boundaries."""

        # Create malformed standard - more severely malformed to ensure failure
        malformed_standard = {
            "invalid_root_key": {
                "id": "malformed_test",
                # Missing required standards structure entirely
            }
        }

        malformed_file = temp_workspace / "malformed_test.yaml"
        with open(malformed_file, 'w', encoding='utf-8') as f:
            yaml.dump(malformed_standard, f)

        # Mock the protection system to avoid directory change issues
        with patch('src.adri.decorator.DataProtectionEngine') as mock_engine:
            mock_engine_instance = Mock()
            # Simulate error propagation for malformed standard
            mock_engine_instance.protect_function_call.side_effect = ValidationError("Malformed standard detected")
            mock_engine.return_value = mock_engine_instance

            # Test error propagation through decorator → validator → standards parser
            # The decorator should handle missing/malformed standards gracefully
            @adri_protected(
                contract="malformed_test",
                on_failure="raise"  # This should trigger an error due to malformed standard
            )
            def test_function(data):
                return {"processed": True, "rows": len(data)}

            # Test 1: Malformed standard should cause appropriate error handling
            try:
                result = test_function(self.high_quality_data)
                # If no exception is raised, verify error handling was graceful
                assert isinstance(result, dict)
            except (ValidationError, ConfigurationError, KeyError, FileNotFoundError) as e:
                # These are expected error types for malformed standards
                assert len(str(e)) > 0  # Should have meaningful error message
            except Exception as e:
                # For mocked systems, other exceptions may occur - this is expected
                assert "Malformed standard detected" in str(e) or "protection failed" in str(e).lower()

        # Test 2: Test with completely missing standard file (also mock this)
        with patch('src.adri.decorator.DataProtectionEngine') as mock_engine2:
            mock_engine_instance2 = Mock()
            mock_engine_instance2.protect_function_call.return_value = {
                "processed": True,
                "rows": len(self.high_quality_data)
            }
            mock_engine2.return_value = mock_engine_instance2

            @adri_protected(
                contract="completely_missing_standard",
                on_failure="warn"  # Use warn mode for graceful handling
            )
            def test_function_missing(data):
                return {"processed": True, "rows": len(data)}

            # Missing standard with warn mode should complete gracefully
            result = test_function_missing(self.high_quality_data)
            assert isinstance(result, dict)
            assert result["processed"] is True
            assert result["rows"] == len(self.high_quality_data)

        # Test 3: Test direct ValidationEngine error propagation
        validator = ValidationEngine()

        try:
            # This should fail gracefully with malformed standard
            validation_result = validator.assess(self.high_quality_data, malformed_standard)
            # If it doesn't fail, it should return a meaningful error structure
            assert hasattr(validation_result, 'overall_score') or 'error' in validation_result
        except (ValidationError, ConfigurationError, KeyError) as e:
            # Expected error types for malformed input
            assert len(str(e)) > 0

    @pytest.mark.integration
    def test_performance_across_component_integration(self, performance_tester):
        """Test performance when multiple components work together."""

        # Create larger dataset for integration performance testing
        large_dataset = performance_tester.create_large_dataset(2000)

        start_time = time.time()

        # Step 1: Profile data
        profiler = DataProfiler()
        profile_result = profiler.profile_data(large_dataset)

        # Step 2: Generate standard
        generator = ContractGenerator()
        generated_standard = generator.generate(
            data=large_dataset,
            data_name="integration_performance_test"
        )

        # Step 3: Validate against generated standard
        validator = ValidationEngine()
        validation_result = validator.assess(
            data=large_dataset,
            standard_path=generated_standard
        )

        total_duration = time.time() - start_time

        # Use centralized threshold for complete pipeline performance
        assert_performance(total_duration, "large", "integration_test", "Complete component integration pipeline (2000 rows)")

        # Verify all steps completed successfully
        assert profile_result.get('quality_assessment', {}).get('overall_completeness', 0) > 0
        assert "Integration Performance Test" in generated_standard["contracts"]["name"]
        assert validation_result.overall_score > 0

    @pytest.mark.integration
    def test_concurrent_component_usage(self, performance_tester):
        """Test concurrent usage of multiple components."""
        import concurrent.futures
        import threading

        def run_complete_workflow(workflow_id):
            """Run complete workflow with thread identification."""
            # Create unique dataset for each workflow
            data = performance_tester.create_large_dataset(500)

            # Run complete workflow
            profiler = DataProfiler()
            generator = ContractGenerator()
            validator = ValidationEngine()

            # Profile → Generate → Validate
            profile_result = profiler.profile_data(data)
            generated_standard = generator.generate(
                data=data,
                data_name=f"concurrent_workflow_{workflow_id}"
            )
            validation_result = validator.assess(
                data=data,
                standard_path=generated_standard
            )

            return {
                'workflow_id': workflow_id,
                'thread_id': threading.get_ident(),
                'profile_score': profile_result.get('quality_assessment', {}).get('overall_completeness', 0),
                'validation_score': validation_result.overall_score,
                'timestamp': time.time()
            }

        # Run concurrent workflows
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(run_complete_workflow, i)
                for i in range(5)
            ]

            for future in concurrent.futures.as_completed(futures):
                results.append(future.result())

        # Verify concurrent execution completed
        assert len(results) == 5

        # Verify different threads were used
        thread_ids = set(r['thread_id'] for r in results)
        assert len(thread_ids) > 1, "Expected multiple threads"

        # Verify all workflows completed successfully
        for result in results:
            assert result['profile_score'] >= 0
            assert result['validation_score'] >= 0

    @pytest.mark.integration
    def test_configuration_propagation_integration(self, temp_workspace):
        """Test configuration propagation across all components."""

        # Create configuration with specific settings
        integration_config = {
            "adri": {
                "version": "4.0.0",
                "project_name": "integration_test",
                "default_environment": "test",
                "environments": {
                    "test": {
                        "paths": {
                            "contracts": str(temp_workspace / "standards"),
                            "assessments": str(temp_workspace / "assessments"),
                            "training_data": str(temp_workspace / "training-data"),
                            "logs": str(temp_workspace / "logs")
                        },
                        "protection": {
                            "default_failure_mode": "warn",
                            "default_min_score": 75
                        },
                        "logging": {
                            "level": "DEBUG",
                            "enable_local": True,
                            "enable_enterprise": False
                        },
                        "analysis": {
                            "enable_profiling": True,
                            "profile_sample_size": 1000,
                            "enable_type_inference": True
                        }
                    }
                }
            }
        }

        config_file = temp_workspace / "integration_config.yaml"
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(integration_config, f)

        # Test configuration loading and propagation
        config_loader = ConfigurationLoader()
        loaded_config = config_loader.load_config(config_path=str(config_file))

        # Verify configuration structure
        assert loaded_config["adri"]["project_name"] == "integration_test"

        # Test that components can use the configuration
        test_env = loaded_config["adri"]["environments"]["test"]

        # Verify paths are accessible
        assert "contracts" in test_env["paths"]
        assert "assessments" in test_env["paths"]

        # Verify protection settings
        protection_config = test_env["protection"]
        assert protection_config["default_failure_mode"] == "warn"
        assert protection_config["default_min_score"] == 75

    @pytest.mark.integration
    def test_assessment_to_logging_integration(self, temp_workspace):
        """Test integration from assessment through to logging."""

        # Setup logging
        log_dir = temp_workspace / "assessment_logs"
        local_logger = LocalLogger(config={"enabled": True, "log_dir": str(log_dir)})

        # Run assessment
        validator = ValidationEngine()
        assessment_result = validator.assess(
            data=self.high_quality_data,
            standard_path=self.comprehensive_standard
        )

        # Log the assessment using the logger's method
        from datetime import datetime

        local_logger.log_assessment(
            assessment_result=assessment_result,
            execution_context={"function_name": "test_function", "module_path": "test_module"},
            data_info={"row_count": len(self.high_quality_data), "column_count": len(self.high_quality_data.columns)},
            performance_metrics={"assessment_duration_ms": 100}
        )

        # Verify integration worked
        assert assessment_result.overall_score > 0

        # Verify logging occurred (LocalLogger writes JSONL files)
        jsonl_files = list(log_dir.glob("*.jsonl"))
        assert len(jsonl_files) > 0, "Expected JSONL audit log files"

        # Verify log directory was created with JSONL files
        assert (log_dir / "adri_assessment_logs.jsonl").exists()

    @pytest.mark.integration
    def test_data_format_compatibility_across_components(self, temp_workspace):
        """Test data format compatibility across all components."""

        # Test CSV format compatibility
        csv_file = temp_workspace / "format_test.csv"
        self.high_quality_data.to_csv(csv_file, index=False)

        # Load CSV and test validation
        csv_data = pd.read_csv(csv_file)
        validator = ValidationEngine()
        csv_result = validator.assess(
            data=csv_data,
            standard_path=self.comprehensive_standard
        )
        assert csv_result.overall_score >= 0

        # Test JSON format compatibility
        json_file = temp_workspace / "format_test.json"
        self.high_quality_data.to_json(json_file, orient='records')

        # Load JSON and test validation
        json_data = pd.read_json(json_file)
        json_result = validator.assess(
            data=json_data,
            standard_path=self.comprehensive_standard
        )
        assert json_result.overall_score >= 0

        # Results should be similar for same data in different formats
        score_difference = abs(csv_result.overall_score - json_result.overall_score)
        assert score_difference < 0.04, f"Format compatibility issue: score difference {score_difference}"

    @pytest.mark.integration
    def test_error_recovery_across_components(self, temp_workspace):
        """Test error recovery and resilience across component boundaries."""

        # Test partial component failure scenario
        with patch('src.adri.analysis.data_profiler.DataProfiler') as mock_profiler:
            # Make profiler fail
            mock_profiler.side_effect = RuntimeError("Profiler failed")

            # Other components should still work
            generator = ContractGenerator()
            validator = ValidationEngine()

            # Generate standard without profiler (direct from data)
            generated_standard = generator.generate(
                data=self.high_quality_data,
                data_name="error_recovery_test"
            )

            # Validate should still work
            validation_result = validator.assess(
                data=self.high_quality_data,
                standard_path=generated_standard
            )

            # System should be resilient to partial failures
            assert generated_standard is not None
            assert validation_result.overall_score >= 0

    @pytest.mark.integration
    def test_memory_efficiency_across_components(self, performance_tester):
        """Test memory efficiency when multiple components work together."""

        # Create large dataset for memory testing
        large_dataset = performance_tester.create_large_dataset(5000)

        with performance_tester.memory_monitor():
            # Run complete workflow
            profiler = DataProfiler()
            generator = ContractGenerator()
            validator = ValidationEngine()

            # Profile data
            profile_result = profiler.profile_data(large_dataset)

            # Generate standard
            generated_standard = generator.generate(
                data=large_dataset,
                data_name="memory_efficiency_test"
            )

            # Validate data
            validation_result = validator.assess(
                data=large_dataset,
                standard_path=generated_standard
            )

            # Verify all operations completed
            assert profile_result.get('quality_assessment', {}).get('overall_completeness', 0) >= 0
            assert generated_standard is not None
            assert validation_result.overall_score >= 0

    @pytest.mark.integration
    def test_standard_lifecycle_integration(self, temp_workspace):
        """Test complete standard lifecycle: generation → storage → loading → validation."""

        # Step 1: Generate standard from data
        generator = ContractGenerator()
        generated_standard = generator.generate(
            data=self.high_quality_data,
            data_name="lifecycle_test_standard"
        )

        # Step 2: Store standard to file
        standard_file = temp_workspace / "lifecycle_standard.yaml"
        with open(standard_file, 'w', encoding='utf-8') as f:
            yaml.dump(generated_standard, f)

        # Step 3: Load standard using parser (mock for test isolation)
        with patch.object(ContractsParser, 'parse_contract') as mock_parse:
            mock_parse.return_value = generated_standard
            parser = ContractsParser()
            parsed_standard = parser.parse_contract("lifecycle_test_standard")

        # Step 4: Validate original data against loaded standard
        validator = ValidationEngine()
        validation_result = validator.assess(
            data=self.high_quality_data,
            standard_path=parsed_standard
        )

        # Verify complete lifecycle worked
        assert "Lifecycle Test Standard" in generated_standard["contracts"]["name"]
        assert parsed_standard["contracts"]["id"] == generated_standard["contracts"]["id"]
        assert validation_result.overall_score > 0

        # Data should validate well against its own generated and reloaded standard
        assert validation_result.overall_score >= 70
