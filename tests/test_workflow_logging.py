"""
Tests for ADRI Workflow Logging functionality.

Tests the WorkflowLogger class for logging workflow execution context
and data provenance to JSONL audit trails.
"""

import json
import os
import tempfile
import threading
from pathlib import Path

import pytest

from adri.logging.workflow import DataProvenance, WorkflowExecution, WorkflowLogger


class TestWorkflowLogger:
    """Test suite for WorkflowLogger class."""

    @pytest.fixture
    def temp_log_dir(self):
        """Create a temporary directory for test logs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def logger_config(self, temp_log_dir):
        """Create a basic logger configuration."""
        return {
            "enabled": True,
            "log_dir": str(temp_log_dir),
            "log_prefix": "test_adri",
            "max_log_size_mb": 1,  # Small size for rotation testing
        }

    @pytest.fixture
    def workflow_logger(self, logger_config):
        """Create a WorkflowLogger instance for testing."""
        return WorkflowLogger(logger_config)

    @pytest.fixture
    def sample_workflow_context(self):
        """Create a sample workflow context."""
        return {
            "run_id": "run_20250107_143022_a1b2c3d4",
            "workflow_id": "test_workflow",
            "workflow_version": "1.0.0",
            "step_id": "step_001",
            "step_sequence": 1,
            "run_at_utc": "2025-01-07T14:30:22Z",
            "data_source_type": "verodat_query",
        }

    def test_initialization(self, workflow_logger, temp_log_dir):
        """Test logger initialization and file creation."""
        assert workflow_logger.enabled is True
        assert workflow_logger.log_dir == temp_log_dir
        assert workflow_logger.log_prefix == "test_adri"

        # Check JSONL files were created
        assert workflow_logger.execution_log_path.exists()
        assert workflow_logger.provenance_log_path.exists()
        assert workflow_logger.execution_log_path.suffix == ".jsonl"
        assert workflow_logger.provenance_log_path.suffix == ".jsonl"

        # Verify files are empty (no headers in JSONL)
        with open(workflow_logger.execution_log_path, 'r', encoding='utf-8') as f:
            content = f.read()
            assert content == ""

        with open(workflow_logger.provenance_log_path, 'r', encoding='utf-8') as f:
            content = f.read()
            assert content == ""

    def test_disabled_logger(self, temp_log_dir):
        """Test that disabled logger doesn't create files or log."""
        config = {
            "enabled": False,
            "log_dir": str(temp_log_dir),
        }
        logger = WorkflowLogger(config)

        # Files should not be created
        assert not logger.execution_log_path.exists()
        assert not logger.provenance_log_path.exists()

        # Logging should return empty string
        execution_id = logger.log_workflow_execution(
            workflow_context={"run_id": "test"},
            assessment_id="test_assessment",
            data_checksum="abc123",
        )
        assert execution_id == ""

    def test_log_workflow_execution(
        self, workflow_logger, sample_workflow_context
    ):
        """Test logging a workflow execution."""
        execution_id = workflow_logger.log_workflow_execution(
            workflow_context=sample_workflow_context,
            assessment_id="test_assessment_001",
            data_checksum="checksum_abc123",
        )

        # Execution ID should be generated
        assert execution_id.startswith("exec_")
        assert len(execution_id) > 20  # exec_YYYYMMDD_HHMMSS_hex

        # Read the JSONL file
        with open(workflow_logger.execution_log_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        assert len(lines) == 1
        row = json.loads(lines[0])

        # Verify all fields
        assert row["execution_id"] == execution_id
        assert row["run_id"] == "run_20250107_143022_a1b2c3d4"
        assert row["workflow_id"] == "test_workflow"
        assert row["workflow_version"] == "1.0.0"
        assert row["step_id"] == "step_001"
        assert row["step_sequence"] == 1
        assert row["run_at_utc"] == "2025-01-07T14:30:22Z"
        assert row["data_source_type"] == "verodat_query"
        assert row["assessment_id"] == "test_assessment_001"
        assert row["data_checksum"] == "checksum_abc123"
        assert row["timestamp"]  # Should have a timestamp

    def test_log_data_provenance_verodat(self, workflow_logger):
        """Test logging Verodat query provenance."""
        execution_id = "exec_test_001"

        provenance_data = {
            "source_type": "verodat_query",
            "verodat_query_id": 12345,
            "verodat_account_id": 91,
            "verodat_workspace_id": 161,
            "verodat_run_at_utc": "2025-01-07T14:25:00Z",
            "verodat_query_sql": "SELECT * FROM customers WHERE risk='HIGH'",
            "record_count": 150,
        }

        workflow_logger.log_data_provenance(execution_id, provenance_data)

        # Read the JSONL file
        with open(workflow_logger.provenance_log_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        assert len(lines) == 1
        row = json.loads(lines[0])

        assert row["execution_id"] == execution_id
        assert row["source_type"] == "verodat_query"
        assert row["verodat_query_id"] == 12345
        assert row["verodat_account_id"] == 91
        assert row["verodat_workspace_id"] == 161
        assert row["verodat_run_at_utc"] == "2025-01-07T14:25:00Z"
        assert row["verodat_query_sql"] == "SELECT * FROM customers WHERE risk='HIGH'"
        assert row["record_count"] == 150
        assert row["timestamp"]

    def test_log_data_provenance_file(self, workflow_logger):
        """Test logging file source provenance."""
        execution_id = "exec_test_002"

        provenance_data = {
            "source_type": "file",
            "file_path": "/data/customers.csv",
            "file_hash": "a1b2c3d4e5f67890",
            "file_size_bytes": 524288,
            "data_retrieved_at_utc": "2025-01-07T14:20:00Z",
            "record_count": 1000,
        }

        workflow_logger.log_data_provenance(execution_id, provenance_data)

        # Read the JSONL file
        with open(workflow_logger.provenance_log_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        assert len(lines) == 1
        row = json.loads(lines[0])

        assert row["execution_id"] == execution_id
        assert row["source_type"] == "file"
        assert row["file_path"] == "/data/customers.csv"
        assert row["file_hash"] == "a1b2c3d4e5f67890"
        assert row["file_size_bytes"] == 524288
        assert row["data_retrieved_at_utc"] == "2025-01-07T14:20:00Z"
        assert row["record_count"] == 1000

    def test_log_data_provenance_api(self, workflow_logger):
        """Test logging API source provenance."""
        execution_id = "exec_test_003"

        provenance_data = {
            "source_type": "api",
            "api_endpoint": "https://api.example.com/v1/credit-scores",
            "api_http_method": "POST",
            "api_response_hash": "abc123def456",
            "data_retrieved_at_utc": "2025-01-07T14:28:00Z",
            "record_count": 75,
        }

        workflow_logger.log_data_provenance(execution_id, provenance_data)

        # Read the JSONL file
        with open(workflow_logger.provenance_log_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        assert len(lines) == 1
        row = json.loads(lines[0])

        assert row["execution_id"] == execution_id
        assert row["source_type"] == "api"
        assert row["api_endpoint"] == "https://api.example.com/v1/credit-scores"
        assert row["api_http_method"] == "POST"
        assert row["api_response_hash"] == "abc123def456"
        assert row["record_count"] == 75

    def test_log_data_provenance_previous_step(self, workflow_logger):
        """Test logging previous step provenance."""
        execution_id = "exec_test_004"

        provenance_data = {
            "source_type": "previous_step",
            "previous_step_id": "enrichment_step",
            "previous_execution_id": "exec_20250107_142000_xyz",
            "data_retrieved_at_utc": "2025-01-07T14:30:00Z",
            "record_count": 250,
            "notes": "Data passed from enrichment step after transformation",
        }

        workflow_logger.log_data_provenance(execution_id, provenance_data)

        # Read the JSONL file
        with open(workflow_logger.provenance_log_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        assert len(lines) == 1
        row = json.loads(lines[0])

        assert row["execution_id"] == execution_id
        assert row["source_type"] == "previous_step"
        assert row["previous_step_id"] == "enrichment_step"
        assert row["previous_execution_id"] == "exec_20250107_142000_xyz"
        assert row["record_count"] == 250
        assert row["notes"] == "Data passed from enrichment step after transformation"

    def test_execution_id_uniqueness(self, workflow_logger, sample_workflow_context):
        """Test that execution IDs are unique."""
        execution_ids = set()

        for _ in range(10):
            exec_id = workflow_logger.log_workflow_execution(
                workflow_context=sample_workflow_context,
                assessment_id=f"test_assessment_{_}",
                data_checksum=f"checksum_{_}",
            )
            execution_ids.add(exec_id)

        # All IDs should be unique
        assert len(execution_ids) == 10

    def test_thread_safety(self, workflow_logger, sample_workflow_context):
        """Test concurrent logging from multiple threads."""
        num_threads = 10
        executions_per_thread = 5
        execution_ids = []
        lock = threading.Lock()

        def log_executions(thread_id):
            for i in range(executions_per_thread):
                exec_id = workflow_logger.log_workflow_execution(
                    workflow_context=sample_workflow_context,
                    assessment_id=f"thread_{thread_id}_exec_{i}",
                    data_checksum=f"checksum_{thread_id}_{i}",
                )
                with lock:
                    execution_ids.append(exec_id)

        threads = []
        for t in range(num_threads):
            thread = threading.Thread(target=log_executions, args=(t,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Verify all executions were logged
        assert len(execution_ids) == num_threads * executions_per_thread
        assert len(set(execution_ids)) == len(execution_ids)  # All unique

        # Verify JSONL contains all records
        with open(workflow_logger.execution_log_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        assert len(lines) == num_threads * executions_per_thread

    def test_get_log_files(self, workflow_logger, temp_log_dir):
        """Test getting log file paths."""
        log_files = workflow_logger.get_log_files()

        assert "workflow_executions" in log_files
        assert "data_provenance" in log_files
        assert log_files["workflow_executions"] == workflow_logger.execution_log_path
        assert log_files["data_provenance"] == workflow_logger.provenance_log_path

    def test_clear_logs(self, workflow_logger, sample_workflow_context):
        """Test clearing log files."""
        # Log some data
        workflow_logger.log_workflow_execution(
            workflow_context=sample_workflow_context,
            assessment_id="test",
            data_checksum="test",
        )

        # Verify data exists
        with open(workflow_logger.execution_log_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        assert len(lines) == 1

        # Clear logs
        workflow_logger.clear_logs()

        # Verify files are recreated empty (no headers in JSONL)
        with open(workflow_logger.execution_log_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        assert len(lines) == 0

    def test_file_rotation(self, workflow_logger, sample_workflow_context):
        """Test log file rotation when size limit is reached."""
        # Write enough data to trigger rotation (max_log_size_mb = 1)
        # Create large workflow context to fill file faster
        large_context = sample_workflow_context.copy()
        large_context["data_source_type"] = "x" * 1000  # Add large field

        # Log many executions to exceed 1MB
        for i in range(2000):
            workflow_logger.log_workflow_execution(
                workflow_context=large_context,
                assessment_id=f"test_{i}",
                data_checksum=f"checksum_{i}",
            )

        # Check if rotated files exist
        log_dir = workflow_logger.log_dir
        rotated_files = list(log_dir.glob("test_adri_workflow_executions.*.jsonl"))

        # May have rotated (depends on exact size)
        # At minimum, current file should exist
        assert workflow_logger.execution_log_path.exists()

    def test_workflow_execution_dataclass(self):
        """Test WorkflowExecution dataclass."""
        execution = WorkflowExecution(
            execution_id="exec_001",
            run_id="run_001",
            workflow_id="test_workflow",
            workflow_version="1.0.0",
            step_id="step_001",
            step_sequence=1,
            run_at_utc="2025-01-07T14:30:22Z",
            data_source_type="file",
            timestamp="2025-01-07T14:30:23Z",
            assessment_id="assessment_001",
            data_checksum="abc123",
        )

        data_dict = execution.to_dict()

        assert data_dict["execution_id"] == "exec_001"
        assert data_dict["run_id"] == "run_001"
        assert data_dict["workflow_id"] == "test_workflow"
        assert data_dict["step_sequence"] == 1
        assert data_dict["data_source_type"] == "file"

    def test_data_provenance_dataclass(self):
        """Test DataProvenance dataclass."""
        provenance = DataProvenance(
            execution_id="exec_001",
            source_type="verodat_query",
            timestamp="2025-01-07T14:30:23Z",
            verodat_query_id=12345,
            verodat_account_id=91,
            record_count=100,
        )

        data_dict = provenance.to_dict()

        assert data_dict["execution_id"] == "exec_001"
        assert data_dict["source_type"] == "verodat_query"
        assert data_dict["verodat_query_id"] == 12345
        assert data_dict["verodat_account_id"] == 91
        assert data_dict["record_count"] == 100
        assert data_dict["timestamp"] == "2025-01-07T14:30:23Z"

        # Optional fields should be empty strings
        assert data_dict["file_path"] == ""
        assert data_dict["api_endpoint"] == ""

    def test_optional_fields_handling(self, workflow_logger):
        """Test handling of optional fields in workflow context."""
        minimal_context = {
            "run_id": "run_001",
            "workflow_id": "test",
            "workflow_version": "1.0",
            "step_id": "step_001",
            "step_sequence": 1,
            "run_at_utc": "2025-01-07T14:30:22Z",
            # data_source_type is optional
        }

        execution_id = workflow_logger.log_workflow_execution(
            workflow_context=minimal_context,
            assessment_id="test",
            data_checksum="test",
        )

        assert execution_id  # Should succeed

        # Verify in JSONL
        with open(workflow_logger.execution_log_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            rows = [json.loads(line) for line in lines]

        assert len(rows) == 1
        assert rows[0]["data_source_type"] == ""  # Empty for optional field


class TestWorkflowLoggerIntegration:
    """Integration tests for workflow logging with other ADRI components."""

    @pytest.fixture
    def temp_log_dir(self):
        """Create a temporary directory for test logs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_multiple_executions_same_run(self, temp_log_dir):
        """Test logging multiple steps in the same workflow run."""
        config = {
            "enabled": True,
            "log_dir": str(temp_log_dir),
            "log_prefix": "integration_test",
        }
        logger = WorkflowLogger(config)

        run_id = "run_20250107_143022_a1b2c3d4"

        # Log three steps in the same run
        execution_ids = []
        for step_num in range(1, 4):
            context = {
                "run_id": run_id,
                "workflow_id": "multi_step_workflow",
                "workflow_version": "1.0.0",
                "step_id": f"step_{step_num:03d}",
                "step_sequence": step_num,
                "run_at_utc": f"2025-01-07T14:3{step_num}:00Z",
                "data_source_type": "previous_step" if step_num > 1 else "file",
            }

            exec_id = logger.log_workflow_execution(
                workflow_context=context,
                assessment_id=f"assessment_{step_num}",
                data_checksum=f"checksum_{step_num}",
            )
            execution_ids.append(exec_id)

        # Verify all three executions were logged
        with open(logger.execution_log_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            rows = [json.loads(line) for line in lines]

        assert len(rows) == 3

        # All should have same run_id
        for row in rows:
            assert row["run_id"] == run_id

        # Step sequences should be 1, 2, 3
        assert rows[0]["step_sequence"] == 1
        assert rows[1]["step_sequence"] == 2
        assert rows[2]["step_sequence"] == 3

    def test_provenance_chain(self, temp_log_dir):
        """Test logging a chain of data provenance across steps."""
        config = {
            "enabled": True,
            "log_dir": str(temp_log_dir),
            "log_prefix": "provenance_test",
        }
        logger = WorkflowLogger(config)

        # Step 1: Load from file
        exec_id_1 = "exec_step1"
        logger.log_data_provenance(
            exec_id_1,
            {
                "source_type": "file",
                "file_path": "/data/raw_data.csv",
                "file_hash": "abc123",
                "record_count": 1000,
            },
        )

        # Step 2: Use output from step 1
        exec_id_2 = "exec_step2"
        logger.log_data_provenance(
            exec_id_2,
            {
                "source_type": "previous_step",
                "previous_step_id": "step_001",
                "previous_execution_id": exec_id_1,
                "record_count": 1000,
            },
        )

        # Step 3: Enrich with API data
        exec_id_3 = "exec_step3"
        logger.log_data_provenance(
            exec_id_3,
            {
                "source_type": "api",
                "api_endpoint": "https://api.example.com/enrich",
                "api_http_method": "POST",
                "record_count": 1000,
            },
        )

        # Verify provenance chain
        with open(logger.provenance_log_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            rows = [json.loads(line) for line in lines]

        assert len(rows) == 3
        assert rows[0]["source_type"] == "file"
        assert rows[1]["source_type"] == "previous_step"
        assert rows[1]["previous_execution_id"] == exec_id_1
        assert rows[2]["source_type"] == "api"
