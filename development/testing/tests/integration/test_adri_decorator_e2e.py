"""
End-to-End tests for ADRI Decorator execution combinations.

This test suite covers all possible scenarios for the ADRI protection decorator,
from standard resolution through data assessment to execution blocking.
"""

import json
import os
import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pandas as pd
import pytest
import yaml

from adri.core.protection import DataProtectionEngine, ProtectionError
from adri.decorators.guard import adri_protected


class TestADRIDecoratorE2E:
    """Comprehensive end-to-end tests for ADRI decorator"""

    # ===== FIXTURES =====

    @pytest.fixture
    def excellent_data(self):
        """High quality data that should pass all checks"""
        return pd.DataFrame(
            {
                "email": ["john@example.com", "jane@test.org", "bob@company.net"],
                "age": [25, 30, 35],
                "name": ["John Doe", "Jane Smith", "Bob Johnson"],
                "created_date": pd.date_range("2024-01-01", periods=3),
            }
        )

    @pytest.fixture
    def good_data(self):
        """Good quality data that should pass most checks"""
        return pd.DataFrame(
            {
                "email": ["john@example.com", "jane@test.org", None],  # One missing
                "age": [25, 30, 35],
                "name": ["John Doe", "Jane Smith", "Bob Johnson"],
            }
        )

    @pytest.fixture
    def marginal_data(self):
        """Borderline quality data"""
        return pd.DataFrame(
            {
                "email": ["john@example.com", None, "invalid-email"],  # Some issues
                "age": [25, 30, 999],  # One outlier
                "name": ["John Doe", None, "Bob"],  # One missing
            }
        )

    @pytest.fixture
    def bad_data(self):
        """Low quality data that should fail checks"""
        return pd.DataFrame(
            {
                "email": ["not-an-email", None, "also-bad", "@@invalid"],
                "age": [-5, 999, None, 200],  # Invalid ages
                "name": [None, None, "X", ""],  # Mostly missing
            }
        )

    @pytest.fixture
    def terrible_data(self):
        """Extremely poor quality data"""
        return pd.DataFrame(
            {
                "email": [None, None, None],
                "age": [None, None, None],
                "name": [None, None, None],
            }
        )

    @pytest.fixture
    def temp_standard_dir(self):
        """Create temporary directory for standards"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def mock_assessment_result(self):
        """Create mock assessment result factory"""

        def _create_result(score=85.0, passed=None):
            result = Mock()
            result.overall_score = score
            result.passed = passed if passed is not None else (score >= 80)
            result.standard_id = "test_standard"
            result.assessment_date = None
            result.dimension_scores = {
                "validity": Mock(score=score / 100 * 20),
                "completeness": Mock(score=score / 100 * 20),
                "consistency": Mock(score=score / 100 * 20),
                "freshness": Mock(score=score / 100 * 20),
                "plausibility": Mock(score=score / 100 * 20),
            }
            result.metadata = {}
            result.rule_execution_log = []
            result.field_analysis = {}
            return result

        return _create_result

    @pytest.fixture
    def sample_standard_dict(self):
        """Create a sample bundled standard dictionary"""
        return {
            "standards": {
                "id": "test_bundled_standard",
                "name": "Test Bundled Standard",
                "version": "1.0.0",
            },
            "requirements": {
                "overall_minimum": 80.0,
                "field_requirements": {
                    "email": {
                        "type": "string",
                        "nullable": False,
                        "pattern": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
                    },
                    "age": {
                        "type": "integer",
                        "nullable": False,
                        "min_value": 0,
                        "max_value": 150,
                    },
                },
            },
        }

    # ===== TEST SECTION 1: STANDARD RESOLUTION =====

    def test_no_standard_auto_generate_true(self, excellent_data, temp_standard_dir):
        """Case 1.1: No standard exists + auto_generate=True → Standard generated"""
        with patch(
            "adri.config.manager.ConfigManager.get_protection_config"
        ) as mock_config:
            mock_config.return_value = {
                "auto_generate_standards": True,
                "default_min_score": 80,
                "default_failure_mode": "raise",
            }

            with patch(
                "adri.config.manager.ConfigManager.resolve_standard_path_simple"
            ) as mock_path:
                standard_path = os.path.join(temp_standard_dir, "test_standard.yaml")
                mock_path.return_value = standard_path

                engine = DataProtectionEngine()

                # Mock bundled standards to not exist
                with patch.object(
                    engine.standards_loader, "standard_exists", return_value=False
                ):
                    # Mock the assessment to return good score
                    with patch.object(engine, "assess_data_quality") as mock_assess:
                        mock_assess.return_value = Mock(
                            overall_score=95.0, passed=True, dimension_scores={}
                        )

                        # Define test function
                        def process_data(data):
                            return f"Processed {len(data)} records"

                        # Execute protected function
                        result = engine.protect_function_call(
                            func=process_data,
                            args=(excellent_data,),
                            kwargs={},
                            data_param="data",
                            function_name="process_data",
                            auto_generate=True,
                        )

                        # Verify standard was generated
                        assert os.path.exists(standard_path)

                        # Verify function executed (fixture has 3 rows, plus date column makes 4)
                        assert result == "Processed 3 records"

    def test_no_standard_auto_generate_false(self, excellent_data):
        """Case 1.2: No standard exists + auto_generate=False → Raises ProtectionError"""
        with patch(
            "adri.config.manager.ConfigManager.get_protection_config"
        ) as mock_config:
            mock_config.return_value = {
                "auto_generate_standards": False,
                "default_min_score": 80,
                "default_failure_mode": "raise",
            }

            with patch(
                "adri.config.manager.ConfigManager.resolve_standard_path_simple"
            ) as mock_path:
                mock_path.return_value = "/non/existent/standard.yaml"

                engine = DataProtectionEngine()

                # Mock bundled standards to not exist
                with patch.object(
                    engine.standards_loader, "standard_exists", return_value=False
                ):

                    def process_data(data):
                        return f"Processed {len(data)} records"

                    # Should raise ProtectionError
                    with pytest.raises(ProtectionError) as exc_info:
                        engine.protect_function_call(
                            func=process_data,
                            args=(excellent_data,),
                            kwargs={},
                            data_param="data",
                            function_name="process_data",
                            auto_generate=False,
                        )

                    assert "Standard file not found" in str(exc_info.value)
                    assert "Auto-generation is disabled" in str(exc_info.value)

    def test_file_based_standard_exists(self, excellent_data, temp_standard_dir):
        """Case 1.3: File-based standard exists → Uses existing standard"""
        # Create a standard file
        standard_path = os.path.join(temp_standard_dir, "existing_standard.yaml")
        standard_content = {
            "standards": {"id": "existing_standard", "version": "1.0.0"},
            "requirements": {"overall_minimum": 75.0},
        }

        with open(standard_path, "w") as f:
            yaml.dump(standard_content, f)

        with patch(
            "adri.config.manager.ConfigManager.resolve_standard_path_simple"
        ) as mock_path:
            mock_path.return_value = standard_path

            engine = DataProtectionEngine()

            with patch.object(engine, "assess_data_quality") as mock_assess:
                mock_assess.return_value = Mock(
                    overall_score=85.0, passed=True, dimension_scores={}
                )

                def process_data(data):
                    return f"Processed {len(data)} records"

                result = engine.protect_function_call(
                    func=process_data,
                    args=(excellent_data,),
                    kwargs={},
                    data_param="data",
                    function_name="process_data",
                    standard_file=standard_path,
                )

                # Verify assessment was called with the file path
                mock_assess.assert_called_once()
                assert result == "Processed 3 records"

    def test_bundled_standard_exists(self, excellent_data, sample_standard_dict):
        """Case 1.4: Bundled standard exists → Uses bundled standard"""
        engine = DataProtectionEngine()

        # Mock standards loader to return bundled standard
        with patch.object(engine.standards_loader, "standard_exists") as mock_exists:
            with patch.object(engine.standards_loader, "load_standard") as mock_load:
                mock_exists.return_value = True
                mock_load.return_value = sample_standard_dict

                with patch.object(engine, "assess_data_quality") as mock_assess:
                    mock_assess.return_value = Mock(
                        overall_score=90.0, passed=True, dimension_scores={}
                    )

                    def process_data(data):
                        return f"Processed {len(data)} records"

                    result = engine.protect_function_call(
                        func=process_data,
                        args=(excellent_data,),
                        kwargs={},
                        data_param="data",
                        function_name="process_data",
                        standard_name="test_bundled_standard",
                    )

                    # Verify bundled standard was used (assess called with dict)
                    mock_assess.assert_called_once()
                    assert isinstance(
                        mock_assess.call_args[0][1], dict
                    )  # Second arg is standard
                    assert result == "Processed 3 records"

    def test_both_bundled_and_file_standard_exist(
        self, excellent_data, temp_standard_dir, sample_standard_dict
    ):
        """Case 1.5: Both bundled and file standard exist → Bundled takes priority"""
        # Create a file standard
        standard_path = os.path.join(temp_standard_dir, "test_standard.yaml")
        file_standard = {
            "standards": {"id": "file_standard", "version": "1.0.0"},
            "requirements": {"overall_minimum": 60.0},  # Different threshold
        }
        with open(standard_path, "w") as f:
            yaml.dump(file_standard, f)

        engine = DataProtectionEngine()

        # Mock bundled standard to exist with priority
        with patch.object(
            engine.standards_loader, "standard_exists", return_value=True
        ):
            with patch.object(engine.standards_loader, "load_standard") as mock_load:
                mock_load.return_value = sample_standard_dict  # Bundled standard

                with patch.object(engine, "assess_data_quality") as mock_assess:
                    mock_assess.return_value = Mock(
                        overall_score=85.0, passed=True, dimension_scores={}
                    )

                    def process_data(data):
                        return f"Processed {len(data)} records"

                    result = engine.protect_function_call(
                        func=process_data,
                        args=(excellent_data,),
                        kwargs={},
                        data_param="data",
                        function_name="process_data",
                        standard_name="test_bundled_standard",
                    )

                    # Verify bundled standard was used (not file)
                    mock_load.assert_called_once()
                    assert result == "Processed 3 records"

    # ===== TEST SECTION 2: DATA QUALITY SCENARIOS =====

    def test_excellent_data_passes(self, excellent_data, mock_assessment_result):
        """Case 2.1: Excellent data (score: 95/100) + min_score=80 → ALLOWED"""
        engine = DataProtectionEngine()

        with patch.object(engine, "ensure_standard_exists"):
            with patch.object(engine, "assess_data_quality") as mock_assess:
                mock_assess.return_value = mock_assessment_result(score=95.0)

                def process_data(data):
                    return "Success"

                result = engine.protect_function_call(
                    func=process_data,
                    args=(excellent_data,),
                    kwargs={},
                    data_param="data",
                    function_name="process_data",
                    min_score=80.0,
                )

                assert result == "Success"

    def test_good_data_passes(self, good_data, mock_assessment_result):
        """Case 2.2: Good data (score: 85/100) + min_score=80 → ALLOWED"""
        engine = DataProtectionEngine()

        with patch.object(engine, "ensure_standard_exists"):
            with patch.object(engine, "assess_data_quality") as mock_assess:
                mock_assess.return_value = mock_assessment_result(score=85.0)

                def process_data(data):
                    return "Success"

                result = engine.protect_function_call(
                    func=process_data,
                    args=(good_data,),
                    kwargs={},
                    data_param="data",
                    function_name="process_data",
                    min_score=80.0,
                )

                assert result == "Success"

    def test_marginal_pass_allowed(self, good_data, mock_assessment_result):
        """Case 2.3: Marginal pass (score: 80.1/100) + min_score=80 → ALLOWED"""
        engine = DataProtectionEngine()

        with patch.object(engine, "ensure_standard_exists"):
            with patch.object(engine, "assess_data_quality") as mock_assess:
                mock_assess.return_value = mock_assessment_result(score=80.1)

                def process_data(data):
                    return "Success"

                result = engine.protect_function_call(
                    func=process_data,
                    args=(good_data,),
                    kwargs={},
                    data_param="data",
                    function_name="process_data",
                    min_score=80.0,
                )

                assert result == "Success"

    def test_marginal_fail_blocked(self, marginal_data, mock_assessment_result):
        """Case 2.4: Marginal fail (score: 79.9/100) + min_score=80 → BLOCKED"""
        engine = DataProtectionEngine()

        with patch.object(engine, "ensure_standard_exists"):
            with patch.object(engine, "assess_data_quality") as mock_assess:
                mock_assess.return_value = mock_assessment_result(score=79.9)

                def process_data(data):
                    return "Should not execute"

                with pytest.raises(ProtectionError) as exc_info:
                    engine.protect_function_call(
                        func=process_data,
                        args=(marginal_data,),
                        kwargs={},
                        data_param="data",
                        function_name="process_data",
                        min_score=80.0,
                        on_failure="raise",
                    )

                assert "Data quality too low" in str(exc_info.value)

    def test_bad_data_blocked(self, bad_data, mock_assessment_result):
        """Case 2.5: Bad data (score: 40/100) + min_score=80 → BLOCKED"""
        engine = DataProtectionEngine()

        with patch.object(engine, "ensure_standard_exists"):
            with patch.object(engine, "assess_data_quality") as mock_assess:
                mock_assess.return_value = mock_assessment_result(score=40.0)

                def process_data(data):
                    return "Should not execute"

                with pytest.raises(ProtectionError) as exc_info:
                    engine.protect_function_call(
                        func=process_data,
                        args=(bad_data,),
                        kwargs={},
                        data_param="data",
                        function_name="process_data",
                        min_score=80.0,
                        on_failure="raise",
                    )

                assert "BLOCKED" in str(exc_info.value)
                assert "40.0/100" in str(exc_info.value)

    def test_terrible_data_blocked(self, terrible_data, mock_assessment_result):
        """Case 2.6: Terrible data (score: 10/100) + min_score=80 → BLOCKED"""
        engine = DataProtectionEngine()

        with patch.object(engine, "ensure_standard_exists"):
            with patch.object(engine, "assess_data_quality") as mock_assess:
                mock_assess.return_value = mock_assessment_result(score=10.0)

                def process_data(data):
                    return "Should not execute"

                with pytest.raises(ProtectionError) as exc_info:
                    engine.protect_function_call(
                        func=process_data,
                        args=(terrible_data,),
                        kwargs={},
                        data_param="data",
                        function_name="process_data",
                        min_score=80.0,
                        on_failure="raise",
                    )

                assert "BLOCKED" in str(exc_info.value)
                assert "10.0/100" in str(exc_info.value)

    # ===== TEST SECTION 3: FAILURE MODE SCENARIOS =====

    def test_bad_data_failure_mode_raise(self, bad_data, mock_assessment_result):
        """Case 3.1: Bad data + on_failure='raise' → Raises ProtectionError"""
        engine = DataProtectionEngine()

        with patch.object(engine, "ensure_standard_exists"):
            with patch.object(engine, "assess_data_quality") as mock_assess:
                mock_assess.return_value = mock_assessment_result(score=40.0)

                def process_data(data):
                    return "Should not execute"

                with pytest.raises(ProtectionError):
                    engine.protect_function_call(
                        func=process_data,
                        args=(bad_data,),
                        kwargs={},
                        data_param="data",
                        function_name="process_data",
                        min_score=80.0,
                        on_failure="raise",
                    )

    def test_bad_data_failure_mode_warn(self, bad_data, mock_assessment_result):
        """Case 3.2: Bad data + on_failure='warn' → Logs warning, continues"""
        engine = DataProtectionEngine()

        with patch.object(engine, "ensure_standard_exists"):
            with patch.object(engine, "assess_data_quality") as mock_assess:
                mock_assess.return_value = mock_assessment_result(score=40.0)

                with patch("adri.core.protection.logger"):

                    def process_data(data):
                        return "Executed despite bad data"

                    result = engine.protect_function_call(
                        func=process_data,
                        args=(bad_data,),
                        kwargs={},
                        data_param="data",
                        function_name="process_data",
                        min_score=80.0,
                        on_failure="warn",
                    )

                    # Should log warning but continue
                    assert result == "Executed despite bad data"

    def test_bad_data_failure_mode_continue(self, bad_data, mock_assessment_result):
        """Case 3.3: Bad data + on_failure='continue' → Continues silently"""
        engine = DataProtectionEngine()

        with patch.object(engine, "ensure_standard_exists"):
            with patch.object(engine, "assess_data_quality") as mock_assess:
                mock_assess.return_value = mock_assessment_result(score=40.0)

                def process_data(data):
                    return "Executed silently"

                result = engine.protect_function_call(
                    func=process_data,
                    args=(bad_data,),
                    kwargs={},
                    data_param="data",
                    function_name="process_data",
                    min_score=80.0,
                    on_failure="continue",
                )

                assert result == "Executed silently"

    # ===== TEST SECTION 4: DIMENSION REQUIREMENTS =====

    def test_no_dimension_requirements(self, excellent_data):
        """Case 4.1: No dimension requirements + good overall score → ALLOWED"""
        engine = DataProtectionEngine()

        with patch.object(engine, "ensure_standard_exists"):
            with patch.object(engine, "assess_data_quality") as mock_assess:
                result = Mock()
                result.overall_score = 85.0
                result.passed = True
                result.dimension_scores = {
                    "validity": Mock(score=15.0),
                    "completeness": Mock(score=17.0),
                }
                mock_assess.return_value = result

                def process_data(data):
                    return "Success"

                # No dimensions parameter = no dimension requirements
                result = engine.protect_function_call(
                    func=process_data,
                    args=(excellent_data,),
                    kwargs={},
                    data_param="data",
                    function_name="process_data",
                    min_score=80.0,
                    # Note: no dimensions parameter
                )

                assert result == "Success"

    def test_dimension_requirements_met(self, excellent_data):
        """Case 4.2: Dimension requirements met + good overall → ALLOWED"""
        engine = DataProtectionEngine()

        with patch.object(engine, "ensure_standard_exists"):
            with patch.object(engine, "assess_data_quality") as mock_assess:
                result = Mock()
                result.overall_score = 85.0
                result.passed = True
                result.dimension_scores = {
                    "validity": Mock(score=18.0),
                    "completeness": Mock(score=17.0),
                }
                mock_assess.return_value = result

                def process_data(data):
                    return "Success"

                result = engine.protect_function_call(
                    func=process_data,
                    args=(excellent_data,),
                    kwargs={},
                    data_param="data",
                    function_name="process_data",
                    min_score=80.0,
                    dimensions={"validity": 15.0, "completeness": 15.0},
                )

                assert result == "Success"

    def test_dimension_requirements_not_met(self, good_data):
        """Case 4.3: Dimension requirements NOT met + good overall → BLOCKED"""
        engine = DataProtectionEngine()

        with patch.object(engine, "ensure_standard_exists"):
            with patch.object(engine, "assess_data_quality") as mock_assess:
                result = Mock()
                result.overall_score = 85.0  # Good overall
                result.passed = True
                result.dimension_scores = {
                    "validity": Mock(score=18.0),  # Good
                    "completeness": Mock(score=10.0),  # Bad
                }
                mock_assess.return_value = result

                def process_data(data):
                    return "Should not execute"

                with pytest.raises(ProtectionError) as exc_info:
                    engine.protect_function_call(
                        func=process_data,
                        args=(good_data,),
                        kwargs={},
                        data_param="data",
                        function_name="process_data",
                        min_score=80.0,
                        dimensions={
                            "validity": 15.0,
                            "completeness": 15.0,
                        },  # Completeness will fail
                        on_failure="raise",
                    )

                assert "completeness" in str(exc_info.value).lower()

    def test_mixed_dimensions_some_pass_some_fail(self, good_data):
        """Case 4.4: Mixed dimensions (some pass, some fail) → BLOCKED"""
        engine = DataProtectionEngine()

        with patch.object(engine, "ensure_standard_exists"):
            with patch.object(engine, "assess_data_quality") as mock_assess:
                result = Mock()
                result.overall_score = 85.0
                result.passed = True
                result.dimension_scores = {
                    "validity": Mock(score=18.0),  # Pass
                    "completeness": Mock(score=10.0),  # Fail
                    "consistency": Mock(score=17.0),  # Pass
                    "freshness": Mock(score=8.0),  # Fail
                    "plausibility": Mock(score=16.0),  # Pass
                }
                mock_assess.return_value = result

                def process_data(data):
                    return "Should not execute"

                with pytest.raises(ProtectionError) as exc_info:
                    engine.protect_function_call(
                        func=process_data,
                        args=(good_data,),
                        kwargs={},
                        data_param="data",
                        function_name="process_data",
                        min_score=80.0,
                        dimensions={
                            "validity": 15.0,  # Will pass
                            "completeness": 15.0,  # Will fail
                            "consistency": 15.0,  # Will pass
                            "freshness": 15.0,  # Will fail
                            "plausibility": 15.0,  # Will pass
                        },
                        on_failure="raise",
                    )

                # Should mention failed dimensions
                error_msg = str(exc_info.value).lower()
                assert "completeness" in error_msg or "freshness" in error_msg

    # ===== TEST SECTION 5: AUDIT LOGGING =====

    def test_successful_assessment_logged(self, excellent_data, mock_assessment_result):
        """Case 5.1: Successful assessment → Logged with passed=True"""
        engine = DataProtectionEngine()

        with patch.object(engine, "ensure_standard_exists"):
            with patch.object(engine, "assess_data_quality") as mock_assess:
                mock_assess.return_value = mock_assessment_result(
                    score=90.0, passed=True
                )

                with patch.object(engine.audit_logger, "log_assessment") as mock_log:

                    def process_data(data):
                        return "Success"

                    result = engine.protect_function_call(
                        func=process_data,
                        args=(excellent_data,),
                        kwargs={},
                        data_param="data",
                        function_name="process_data",
                        min_score=80.0,
                    )

                    # Verify audit log was called
                    mock_log.assert_called_once()
                    assert (
                        mock_log.call_args[1]["execution_context"]["assessment_passed"]
                        is True
                    )
                    assert result == "Success"

    def test_failed_assessment_logged(self, bad_data, mock_assessment_result):
        """Case 5.2: Failed assessment → Logged with passed=False"""
        engine = DataProtectionEngine()

        with patch.object(engine, "ensure_standard_exists"):
            with patch.object(engine, "assess_data_quality") as mock_assess:
                mock_assess.return_value = mock_assessment_result(
                    score=40.0, passed=False
                )

                with patch.object(engine.audit_logger, "log_assessment") as mock_log:

                    def process_data(data):
                        return "Should not execute"

                    try:
                        engine.protect_function_call(
                            func=process_data,
                            args=(bad_data,),
                            kwargs={},
                            data_param="data",
                            function_name="process_data",
                            min_score=80.0,
                            on_failure="raise",
                        )
                    except ProtectionError:
                        pass  # Expected

                    # Verify audit log was called even though execution failed
                    mock_log.assert_called_once()
                    call_args = mock_log.call_args[1]
                    assert call_args["execution_context"]["assessment_passed"] is False

    def test_audit_logging_failure_continues(
        self, excellent_data, mock_assessment_result
    ):
        """Case 5.3: Audit logging fails → Warning logged, execution continues"""
        engine = DataProtectionEngine()

        with patch.object(engine, "ensure_standard_exists"):
            with patch.object(engine, "assess_data_quality") as mock_assess:
                mock_assess.return_value = mock_assessment_result(score=90.0)

                # Make audit logger raise exception
                with patch.object(engine.audit_logger, "log_assessment") as mock_log:
                    mock_log.side_effect = Exception("Audit log error")

                    with patch("adri.core.protection.logger") as mock_logger:

                        def process_data(data):
                            return "Success despite audit failure"

                        result = engine.protect_function_call(
                            func=process_data,
                            args=(excellent_data,),
                            kwargs={},
                            data_param="data",
                            function_name="process_data",
                            min_score=80.0,
                        )

                        # Should log warning about audit failure
                        mock_logger.warning.assert_called()
                        assert "Failed to create audit log" in str(
                            mock_logger.warning.call_args
                        )

                        # But function should still execute
                        assert result == "Success despite audit failure"

    def test_concurrent_assessments_logged(
        self, excellent_data, mock_assessment_result
    ):
        """Case 5.4: Concurrent assessments → All logged correctly"""
        import queue
        import threading

        engine = DataProtectionEngine()
        results = queue.Queue()
        errors = queue.Queue()

        def run_protected_function(thread_id):
            try:
                with patch.object(engine, "ensure_standard_exists"):
                    with patch.object(engine, "assess_data_quality") as mock_assess:
                        mock_assess.return_value = mock_assessment_result(
                            score=85.0 + thread_id
                        )

                        def process_data(data):
                            return f"Thread {thread_id} processed"

                        result = engine.protect_function_call(
                            func=process_data,
                            args=(excellent_data,),
                            kwargs={},
                            data_param="data",
                            function_name=f"process_data_thread_{thread_id}",
                            min_score=80.0,
                        )
                        results.put((thread_id, result))
            except Exception as e:
                errors.put((thread_id, e))

        # Create and start threads
        threads = []
        for i in range(3):
            t = threading.Thread(target=run_protected_function, args=(i,))
            threads.append(t)
            t.start()

        # Wait for all threads to complete
        for t in threads:
            t.join()

        # Check results
        assert errors.empty(), "No errors should occur in concurrent execution"
        assert results.qsize() == 3, "All threads should complete successfully"

        # Verify each thread got its result
        results_list = []
        while not results.empty():
            results_list.append(results.get())

        assert len(results_list) == 3
        for thread_id, result in results_list:
            assert result == f"Thread {thread_id} processed"

    # ===== TEST SECTION 6: EDGE CASES =====

    def test_empty_dataframe(self, mock_assessment_result):
        """Case 6.1: Empty DataFrame → Handled gracefully"""
        empty_df = pd.DataFrame()
        engine = DataProtectionEngine()

        # Mock bundled standards to not exist
        with patch.object(
            engine.standards_loader, "standard_exists", return_value=False
        ):
            with patch.object(engine, "ensure_standard_exists"):
                with patch.object(engine, "assess_data_quality") as mock_assess:
                    mock_assess.return_value = mock_assessment_result(
                        score=50.0
                    )  # Low score for empty

                    def process_data(data):
                        return f"Processed {len(data)} records"

                    with pytest.raises(ProtectionError):
                        engine.protect_function_call(
                            func=process_data,
                            args=(empty_df,),
                            kwargs={},
                            data_param="data",
                            function_name="process_data",
                            min_score=80.0,
                            on_failure="raise",  # Explicitly set to raise
                        )

    def test_single_row_dataframe(self, mock_assessment_result):
        """Case 6.2: Single row DataFrame → Assessed correctly"""
        single_row_df = pd.DataFrame({"email": ["test@example.com"], "age": [30]})

        engine = DataProtectionEngine()

        with patch.object(engine, "ensure_standard_exists"):
            with patch.object(engine, "assess_data_quality") as mock_assess:
                mock_assess.return_value = mock_assessment_result(score=85.0)

                def process_data(data):
                    return f"Processed {len(data)} record"

                result = engine.protect_function_call(
                    func=process_data,
                    args=(single_row_df,),
                    kwargs={},
                    data_param="data",
                    function_name="process_data",
                    min_score=80.0,
                )

                assert result == "Processed 1 record"

    def test_list_data_conversion(self, mock_assessment_result):
        """Case 6.3: Non-DataFrame data (list) → Converted and assessed"""
        list_data = [
            {"email": "test@example.com", "age": 30},
            {"email": "user@test.org", "age": 25},
        ]

        engine = DataProtectionEngine()

        with patch.object(engine, "ensure_standard_exists"):
            with patch.object(engine, "assess_data_quality") as mock_assess:
                mock_assess.return_value = mock_assessment_result(score=85.0)

                def process_data(data):
                    return "Success"

                result = engine.protect_function_call(
                    func=process_data,
                    args=(list_data,),
                    kwargs={},
                    data_param="data",
                    function_name="process_data",
                    min_score=80.0,
                )

                # Verify data was converted to DataFrame
                # The function converts internally, so we check it was called
                assert mock_assess.called
                assert result == "Success"

    def test_invalid_data_type(self):
        """Case 6.4: Invalid data type → Raises appropriate error"""
        invalid_data = "This is just a string, not valid data"

        engine = DataProtectionEngine()

        with patch.object(engine, "ensure_standard_exists"):

            def process_data(data):
                return "Should not execute"

            with pytest.raises(ProtectionError) as exc_info:
                engine.protect_function_call(
                    func=process_data,
                    args=(invalid_data,),
                    kwargs={},
                    data_param="data",
                    function_name="process_data",
                    min_score=80.0,
                )

            # Check for proper error message
            error_msg = str(exc_info.value).lower()
            assert "cannot assess" in error_msg or "assessment failed" in error_msg
            assert "str" in error_msg  # Should mention the invalid type

    def test_missing_data_parameter(self, excellent_data):
        """Case 6.5: Missing data parameter → Raises ValueError"""
        engine = DataProtectionEngine()

        def process_data(input_data):  # Note: parameter is 'input_data', not 'data'
            return "Success"

        with pytest.raises(ValueError) as exc_info:
            engine.protect_function_call(
                func=process_data,
                args=(excellent_data,),
                kwargs={},
                data_param="data",  # Looking for 'data' but function has 'input_data'
                function_name="process_data",
                min_score=80.0,
            )

        assert "Could not find data parameter 'data'" in str(exc_info.value)

    # ===== TEST SECTION 7: CONFIGURATION OVERRIDES =====

    def test_default_configuration(self, excellent_data, mock_assessment_result):
        """Case 7.1: Default configuration → Uses config values"""
        with patch(
            "adri.config.manager.ConfigManager.get_protection_config"
        ) as mock_config:
            mock_config.return_value = {
                "default_min_score": 75,  # Default config
                "default_failure_mode": "warn",  # Default config
                "auto_generate_standards": False,
            }

            engine = DataProtectionEngine()

            with patch.object(engine, "ensure_standard_exists"):
                with patch.object(engine, "assess_data_quality") as mock_assess:
                    mock_assess.return_value = mock_assessment_result(
                        score=76.0
                    )  # Just above default

                    with patch("adri.core.protection.logger"):

                        def process_data(data):
                            return "Success with defaults"

                        # Call without specifying min_score or on_failure
                        result = engine.protect_function_call(
                            func=process_data,
                            args=(excellent_data,),
                            kwargs={},
                            data_param="data",
                            function_name="process_data",
                            # Note: no min_score or on_failure specified
                        )

                        # Should use default config values
                        assert result == "Success with defaults"

    def test_override_min_score(self, excellent_data, mock_assessment_result):
        """Case 7.2: Override min_score → Uses override"""
        with patch(
            "adri.config.manager.ConfigManager.get_protection_config"
        ) as mock_config:
            mock_config.return_value = {
                "default_min_score": 60,  # Low default
                "default_failure_mode": "raise",
            }

            engine = DataProtectionEngine()

            with patch.object(engine, "ensure_standard_exists"):
                with patch.object(engine, "assess_data_quality") as mock_assess:
                    mock_assess.return_value = mock_assessment_result(score=75.0)

                    def process_data(data):
                        return "Should not execute"

                    # Override to higher min_score
                    with pytest.raises(ProtectionError):
                        engine.protect_function_call(
                            func=process_data,
                            args=(excellent_data,),
                            kwargs={},
                            data_param="data",
                            function_name="process_data",
                            min_score=90.0,  # Override to 90, score is 75
                        )

    def test_override_failure_mode(self, bad_data, mock_assessment_result):
        """Case 7.3: Override on_failure → Uses override"""
        with patch(
            "adri.config.manager.ConfigManager.get_protection_config"
        ) as mock_config:
            mock_config.return_value = {
                "default_min_score": 80,
                "default_failure_mode": "raise",  # Default is raise
            }

            engine = DataProtectionEngine()

            with patch.object(engine, "ensure_standard_exists"):
                with patch.object(engine, "assess_data_quality") as mock_assess:
                    mock_assess.return_value = mock_assessment_result(score=40.0)

                    def process_data(data):
                        return "Continued"

                    # Override to continue mode
                    result = engine.protect_function_call(
                        func=process_data,
                        args=(bad_data,),
                        kwargs={},
                        data_param="data",
                        function_name="process_data",
                        min_score=80.0,
                        on_failure="continue",  # Override to continue
                    )

                    assert result == "Continued"

    def test_override_verbose(self, excellent_data, mock_assessment_result):
        """Case 7.4: Override verbose → Uses override"""
        engine = DataProtectionEngine()

        with patch.object(engine, "ensure_standard_exists"):
            with patch.object(engine, "assess_data_quality") as mock_assess:
                mock_assess.return_value = mock_assessment_result(score=85.0)

                with patch("adri.core.protection.logger") as mock_logger:

                    def process_data(data):
                        return "Success"

                    # Test with verbose=True
                    result = engine.protect_function_call(
                        func=process_data,
                        args=(excellent_data,),
                        kwargs={},
                        data_param="data",
                        function_name="process_data",
                        min_score=80.0,
                        verbose=True,  # Override to verbose
                    )

                    # Should have logged info messages
                    assert mock_logger.info.called
                    assert result == "Success"

    # ===== TEST SECTION 8: CACHING SCENARIOS =====

    def test_first_assessment_no_cache(self, excellent_data, mock_assessment_result):
        """Case 8.1: First assessment → No cache, full assessment"""
        engine = DataProtectionEngine()

        with patch.object(engine, "ensure_standard_exists"):
            with patch.object(engine, "assess_data_quality") as mock_assess:
                mock_assess.return_value = mock_assessment_result(score=85.0)

                def process_data(data):
                    return "Success"

                # First call - no cache
                result = engine.protect_function_call(
                    func=process_data,
                    args=(excellent_data,),
                    kwargs={},
                    data_param="data",
                    function_name="process_data",
                    min_score=80.0,
                )

                # Should have called assessment
                assert mock_assess.call_count == 1
                assert result == "Success"

    def test_repeated_assessment_uses_cache(
        self, excellent_data, mock_assessment_result
    ):
        """Case 8.2: Repeated assessment → Uses cache"""
        with patch(
            "adri.config.manager.ConfigManager.get_protection_config"
        ) as mock_config:
            mock_config.return_value = {
                "cache_duration_hours": 1,  # Enable caching
                "default_min_score": 80,
                "default_failure_mode": "raise",
            }

            engine = DataProtectionEngine()

            with patch.object(engine, "ensure_standard_exists"):
                with patch.object(
                    engine, "assess_data_quality", wraps=engine.assess_data_quality
                ):
                    # Manually set up cache entry
                    cache_key = "test_cache_key"
                    cached_result = mock_assessment_result(score=85.0)
                    engine._assessment_cache[cache_key] = (cached_result, time.time())

                    # Mock the hash generation to return consistent key
                    with patch.object(engine, "_generate_data_hash") as mock_hash:
                        mock_hash.return_value = "test_hash"

                        # Mock resolve_standard to return a simple path
                        with patch.object(engine, "resolve_standard") as mock_resolve:
                            mock_resolve.return_value = "test_standard.yaml"

                            # This should use cache
                            def process_data(data):
                                return "Success"

                            # Set cache key that will match
                            engine._assessment_cache["test_standard.yaml:test_hash"] = (
                                cached_result,
                                time.time(),
                            )

                            result = engine.protect_function_call(
                                func=process_data,
                                args=(excellent_data,),
                                kwargs={},
                                data_param="data",
                                function_name="process_data",
                                min_score=80.0,
                            )

                            assert result == "Success"

    def test_cache_expired(self, excellent_data, mock_assessment_result):
        """Case 8.3: Cache expired → Re-assesses"""
        with patch(
            "adri.config.manager.ConfigManager.get_protection_config"
        ) as mock_config:
            mock_config.return_value = {
                "cache_duration_hours": 0.0001,  # Very short cache duration (0.36 seconds)
                "default_min_score": 80,
                "default_failure_mode": "raise",
            }

            engine = DataProtectionEngine()

            with patch.object(engine, "ensure_standard_exists"):
                with patch.object(engine, "assess_data_quality") as mock_assess:
                    mock_assess.return_value = mock_assessment_result(score=85.0)

                    def process_data(data):
                        return "Success"

                    # First call - creates cache
                    result1 = engine.protect_function_call(
                        func=process_data,
                        args=(excellent_data,),
                        kwargs={},
                        data_param="data",
                        function_name="process_data",
                        min_score=80.0,
                    )

                    # Wait for cache to expire (more than 0.36 seconds)
                    time.sleep(0.5)

                    # Second call - cache should be expired
                    result2 = engine.protect_function_call(
                        func=process_data,
                        args=(excellent_data,),
                        kwargs={},
                        data_param="data",
                        function_name="process_data",
                        min_score=80.0,
                    )

                    # Should have called assessment twice (cache expired)
                    assert mock_assess.call_count == 2
                    assert result1 == "Success"
                    assert result2 == "Success"

    def test_cache_disabled(self, excellent_data, mock_assessment_result):
        """Case 8.4: Cache disabled → Always re-assesses"""
        with patch(
            "adri.config.manager.ConfigManager.get_protection_config"
        ) as mock_config:
            mock_config.return_value = {
                "cache_duration_hours": 0,  # Disable caching
                "default_min_score": 80,
                "default_failure_mode": "raise",
            }

            engine = DataProtectionEngine()

            with patch.object(engine, "ensure_standard_exists"):
                with patch.object(engine, "assess_data_quality") as mock_assess:
                    mock_assess.return_value = mock_assessment_result(score=85.0)

                    def process_data(data):
                        return "Success"

                    # First call
                    result1 = engine.protect_function_call(
                        func=process_data,
                        args=(excellent_data,),
                        kwargs={},
                        data_param="data",
                        function_name="process_data",
                        min_score=80.0,
                    )

                    # Second call - should NOT use cache
                    result2 = engine.protect_function_call(
                        func=process_data,
                        args=(excellent_data,),
                        kwargs={},
                        data_param="data",
                        function_name="process_data",
                        min_score=80.0,
                    )

                    # Should have called assessment twice (no caching)
                    assert mock_assess.call_count == 2
                    assert result1 == "Success"
                    assert result2 == "Success"

    # ===== TEST DECORATOR INTEGRATION =====

    def test_decorator_with_good_data(self, excellent_data, mock_assessment_result):
        """Test the @adri_protected decorator with good data"""
        with patch("adri.decorators.guard.DataProtectionEngine") as mock_engine_class:
            mock_engine = Mock()
            mock_engine_class.return_value = mock_engine
            mock_engine.protect_function_call.return_value = "Decorator Success"

            @adri_protected(data_param="data", min_score=80.0)
            def my_protected_function(data):
                return "Original function"

            result = my_protected_function(excellent_data)

            # Verify protection was applied
            mock_engine.protect_function_call.assert_called_once()
            assert result == "Decorator Success"

    def test_decorator_with_bad_data_raises(self, bad_data):
        """Test the @adri_protected decorator blocks bad data"""
        with patch("adri.decorators.guard.DataProtectionEngine") as mock_engine_class:
            mock_engine = Mock()
            mock_engine_class.return_value = mock_engine
            mock_engine.protect_function_call.side_effect = ProtectionError(
                "Data quality too low"
            )

            @adri_protected(data_param="data", min_score=80.0, on_failure="raise")
            def my_protected_function(data):
                return "Should not execute"

            with pytest.raises(ProtectionError) as exc_info:
                my_protected_function(bad_data)

            assert "Data quality too low" in str(exc_info.value)

    # ===== END-TO-END REAL SCENARIO TESTS =====

    def test_e2e_real_scenario_auto_generate_and_assess(self, temp_standard_dir):
        """Complete end-to-end test: auto-generate standard, assess, and execute"""
        # Create real data
        real_data = pd.DataFrame(
            {
                "customer_id": [1, 2, 3, 4, 5],
                "email": [
                    "john@example.com",
                    "jane@test.org",
                    "bob@company.net",
                    "alice@domain.com",
                    "charlie@email.org",
                ],
                "age": [25, 30, 35, 28, 45],
                "purchase_amount": [100.50, 250.75, 50.25, 175.00, 300.00],
            }
        )

        with patch(
            "adri.config.manager.ConfigManager.get_protection_config"
        ) as mock_config:
            mock_config.return_value = {
                "auto_generate_standards": True,
                "default_min_score": 70,
                "default_failure_mode": "raise",
                "cache_duration_hours": 1,
            }

            with patch(
                "adri.config.manager.ConfigManager.resolve_standard_path_simple"
            ) as mock_path:
                standard_path = os.path.join(
                    temp_standard_dir, "customer_standard.yaml"
                )
                mock_path.return_value = standard_path

                # Use real engine but mock the assessment
                engine = DataProtectionEngine()

                # Mock bundled standards to not exist
                with patch.object(
                    engine.standards_loader, "standard_exists", return_value=False
                ):
                    with patch.object(engine, "assess_data_quality") as mock_assess:
                        # Mock a good assessment result
                        assessment = Mock()
                        assessment.overall_score = 88.5
                        assessment.passed = True
                        assessment.dimension_scores = {
                            "validity": Mock(score=18.0),
                            "completeness": Mock(score=19.0),
                            "consistency": Mock(score=17.5),
                            "freshness": Mock(score=16.0),
                            "plausibility": Mock(score=18.0),
                        }
                        mock_assess.return_value = assessment

                        # Define business function
                        def calculate_customer_metrics(data):
                            avg_purchase = data["purchase_amount"].mean()
                            total_customers = len(data)
                            return {
                                "average_purchase": avg_purchase,
                                "total_customers": total_customers,
                                "total_revenue": data["purchase_amount"].sum(),
                            }

                        # Execute with protection
                        result = engine.protect_function_call(
                            func=calculate_customer_metrics,
                            args=(real_data,),
                            kwargs={},
                            data_param="data",
                            function_name="calculate_customer_metrics",
                            min_score=70.0,
                            verbose=True,
                        )

                        # Verify standard was created
                        assert os.path.exists(standard_path)

                        # Verify function executed and returned correct results
                        assert round(result["average_purchase"], 2) == 175.30
                        assert result["total_customers"] == 5
                        assert round(result["total_revenue"], 2) == 876.50

                        # Verify assessment was called
                        mock_assess.assert_called_once()

    def test_e2e_real_scenario_data_quality_blocks_execution(self, temp_standard_dir):
        """Complete end-to-end test: bad data quality blocks execution"""
        # Create poor quality data
        poor_data = pd.DataFrame(
            {
                "customer_id": [None, None, 3, None, 5],
                "email": ["not-an-email", None, "@@invalid", "", "also-bad"],
                "age": [-5, 999, None, 200, -10],
                "purchase_amount": [None, None, None, -50, None],
            }
        )

        with patch(
            "adri.config.manager.ConfigManager.get_protection_config"
        ) as mock_config:
            mock_config.return_value = {
                "auto_generate_standards": True,
                "default_min_score": 80,
                "default_failure_mode": "raise",
                "cache_duration_hours": 0,
            }

            with patch(
                "adri.config.manager.ConfigManager.resolve_standard_path_simple"
            ) as mock_path:
                standard_path = os.path.join(
                    temp_standard_dir, "customer_standard.yaml"
                )
                mock_path.return_value = standard_path

                engine = DataProtectionEngine()

                with patch.object(engine, "assess_data_quality") as mock_assess:
                    # Mock a poor assessment result
                    assessment = Mock()
                    assessment.overall_score = 35.2  # Very low score
                    assessment.passed = False
                    assessment.dimension_scores = {
                        "validity": Mock(score=5.0),
                        "completeness": Mock(score=3.0),
                        "consistency": Mock(score=7.5),
                        "freshness": Mock(score=10.0),
                        "plausibility": Mock(score=9.7),
                    }
                    mock_assess.return_value = assessment

                    # Mock audit logger to verify it gets called
                    with patch.object(
                        engine.audit_logger, "log_assessment"
                    ) as mock_log:
                        # Define business function
                        def calculate_customer_metrics(data):
                            # This should NOT execute
                            return "Should not reach here"

                        # Try to execute with protection - should fail
                        with pytest.raises(ProtectionError) as exc_info:
                            engine.protect_function_call(
                                func=calculate_customer_metrics,
                                args=(poor_data,),
                                kwargs={},
                                data_param="data",
                                function_name="calculate_customer_metrics",
                                min_score=80.0,
                                verbose=False,
                            )

                        # Verify error message contains helpful information
                        error_msg = str(exc_info.value)
                        assert "BLOCKED" in error_msg
                        assert "35.2/100" in error_msg
                        assert "Required: 80.0/100" in error_msg

                        # Verify audit log was still created despite failure
                        mock_log.assert_called_once()
                        audit_call = mock_log.call_args[1]
                        assert (
                            audit_call["execution_context"]["assessment_passed"]
                            is False
                        )
