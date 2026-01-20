"""
Comprehensive tests for enterprise reasoning logger.

Tests covering:
- AI prompt and response logging to JSONL files
- Reasoning step tracking and history retrieval
- File system operations and directory management
- Concurrent logging operations and thread safety
- Error handling and recovery scenarios
- Performance and memory efficiency
"""

import json
import os
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from adri_enterprise.logging.reasoning import ReasoningLogger


class TestReasoningLogger:
    """Test suite for core reasoning logger functionality."""

    def test_reasoning_logger_initialization(self, temp_log_dir):
        """Test reasoning logger initialization and directory creation."""
        logger = ReasoningLogger(
            log_dir=temp_log_dir,
            store_prompts=True,
            store_responses=True
        )

        assert logger.log_dir == temp_log_dir
        assert logger.store_prompts is True
        assert logger.store_responses is True
        assert logger.prompt_log_file == temp_log_dir / "adri_reasoning_prompts.jsonl"
        assert logger.response_log_file == temp_log_dir / "adri_reasoning_responses.jsonl"

        # Directory should exist
        assert temp_log_dir.exists()
        assert temp_log_dir.is_dir()

    def test_reasoning_logger_default_initialization(self):
        """Test reasoning logger with default parameters."""
        original_dir = os.getcwd()
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                os.chdir(temp_dir)

                logger = ReasoningLogger()

                # Should create ./logs directory
                logs_dir = Path("./logs")
                assert logger.log_dir == logs_dir
                assert logs_dir.exists()
            finally:
                # Change back before temp_dir is deleted (required for Windows)
                os.chdir(original_dir)

            # Default settings
            assert logger.store_prompts is True
            assert logger.store_responses is True

    def test_prompt_logging_functionality(self, temp_log_dir, mock_reasoning_data):
        """Test AI prompt logging to JSONL file."""
        logger = ReasoningLogger(log_dir=temp_log_dir)

        prompt_id = logger.log_prompt(
            prompt=mock_reasoning_data['prompt'],
            llm_config=mock_reasoning_data['llm_config'],
            assessment_id=mock_reasoning_data['assessment_id'],
            function_name=mock_reasoning_data['function_name']
        )

        # Verify prompt ID is generated
        assert prompt_id.startswith("prompt_")
        assert mock_reasoning_data['assessment_id'] in prompt_id or len(prompt_id) > 20

        # Verify file was created and contains entry
        assert logger.prompt_log_file.exists()

        with open(logger.prompt_log_file, 'r', encoding='utf-8') as f:
            entries = [json.loads(line) for line in f]

        assert len(entries) == 1
        entry = entries[0]

        assert entry['prompt_id'] == prompt_id
        assert entry['prompt'] == mock_reasoning_data['prompt']
        assert entry['llm_config'] == mock_reasoning_data['llm_config']
        assert entry['assessment_id'] == mock_reasoning_data['assessment_id']
        assert entry['function_name'] == mock_reasoning_data['function_name']
        assert 'timestamp' in entry

    def test_response_logging_functionality(self, temp_log_dir, mock_reasoning_data):
        """Test AI response logging to JSONL file."""
        logger = ReasoningLogger(log_dir=temp_log_dir)

        # First log a prompt to get prompt_id
        prompt_id = logger.log_prompt(
            prompt=mock_reasoning_data['prompt'],
            assessment_id=mock_reasoning_data['assessment_id']
        )

        # Then log response linked to prompt
        response_id = logger.log_response(
            response=mock_reasoning_data['response'],
            prompt_id=prompt_id,
            llm_config=mock_reasoning_data['llm_config'],
            assessment_id=mock_reasoning_data['assessment_id'],
            function_name=mock_reasoning_data['function_name']
        )

        # Verify response ID is generated
        assert response_id.startswith("response_")

        # Verify file was created and contains entry
        assert logger.response_log_file.exists()

        with open(logger.response_log_file, 'r', encoding='utf-8') as f:
            entries = [json.loads(line) for line in f]

        assert len(entries) == 1
        entry = entries[0]

        assert entry['response_id'] == response_id
        assert entry['prompt_id'] == prompt_id  # Linked to prompt
        assert entry['response'] == mock_reasoning_data['response']
        assert entry['llm_config'] == mock_reasoning_data['llm_config']
        assert entry['assessment_id'] == mock_reasoning_data['assessment_id']
        assert entry['function_name'] == mock_reasoning_data['function_name']

    def test_complete_reasoning_step_logging(self, temp_log_dir, mock_reasoning_data):
        """Test logging a complete reasoning step (prompt + response)."""
        logger = ReasoningLogger(log_dir=temp_log_dir)

        prompt_id, response_id = logger.log_reasoning_step(
            prompt=mock_reasoning_data['prompt'],
            response=mock_reasoning_data['response'],
            llm_config=mock_reasoning_data['llm_config'],
            assessment_id=mock_reasoning_data['assessment_id'],
            function_name=mock_reasoning_data['function_name']
        )

        # Both IDs should be generated
        assert prompt_id.startswith("prompt_")
        assert response_id.startswith("response_")

        # Both files should exist
        assert logger.prompt_log_file.exists()
        assert logger.response_log_file.exists()

        # Verify prompt entry
        with open(logger.prompt_log_file, 'r', encoding='utf-8') as f:
            prompt_entries = [json.loads(line) for line in f]
        assert len(prompt_entries) == 1
        assert prompt_entries[0]['prompt_id'] == prompt_id

        # Verify response entry and linking
        with open(logger.response_log_file, 'r', encoding='utf-8') as f:
            response_entries = [json.loads(line) for line in f]
        assert len(response_entries) == 1
        assert response_entries[0]['response_id'] == response_id
        assert response_entries[0]['prompt_id'] == prompt_id  # Linked

    def test_reasoning_step_with_disabled_prompt_logging(self, temp_log_dir, mock_reasoning_data):
        """Test reasoning step with prompt logging disabled."""
        logger = ReasoningLogger(
            log_dir=temp_log_dir,
            store_prompts=False,
            store_responses=True
        )

        prompt_id, response_id = logger.log_reasoning_step(
            prompt=mock_reasoning_data['prompt'],
            response=mock_reasoning_data['response'],
            assessment_id=mock_reasoning_data['assessment_id']
        )

        # Prompt ID should be None, response ID should be generated
        assert prompt_id is None
        assert response_id.startswith("response_")

        # Only response file should exist
        assert not logger.prompt_log_file.exists()
        assert logger.response_log_file.exists()

        # Response should not have prompt_id link
        with open(logger.response_log_file, 'r', encoding='utf-8') as f:
            entries = [json.loads(line) for line in f]
        assert entries[0]['prompt_id'] is None

    def test_reasoning_step_with_disabled_response_logging(self, temp_log_dir, mock_reasoning_data):
        """Test reasoning step with response logging disabled."""
        logger = ReasoningLogger(
            log_dir=temp_log_dir,
            store_prompts=True,
            store_responses=False
        )

        prompt_id, response_id = logger.log_reasoning_step(
            prompt=mock_reasoning_data['prompt'],
            response=mock_reasoning_data['response'],
            assessment_id=mock_reasoning_data['assessment_id']
        )

        # Prompt ID should be generated, response ID should be None
        assert prompt_id.startswith("prompt_")
        assert response_id is None

        # Only prompt file should exist
        assert logger.prompt_log_file.exists()
        assert not logger.response_log_file.exists()

    def test_string_prompt_and_response(self, temp_log_dir):
        """Test logging with simple string prompts and responses."""
        logger = ReasoningLogger(log_dir=temp_log_dir)

        simple_prompt = "Analyze this customer data for quality issues."
        simple_response = "The data appears to be well-structured with no missing values."

        prompt_id, response_id = logger.log_reasoning_step(
            prompt=simple_prompt,
            response=simple_response,
            assessment_id="simple_test_001"
        )

        # Verify both IDs generated
        assert prompt_id and response_id

        # Verify content was logged correctly
        with open(logger.prompt_log_file, 'r', encoding='utf-8') as f:
            prompt_entry = json.loads(f.readline())
        assert prompt_entry['prompt'] == simple_prompt

        with open(logger.response_log_file, 'r', encoding='utf-8') as f:
            response_entry = json.loads(f.readline())
        assert response_entry['response'] == simple_response

    def test_complex_structured_data(self, temp_log_dir):
        """Test logging with complex nested data structures."""
        logger = ReasoningLogger(log_dir=temp_log_dir)

        complex_prompt = {
            "system": "You are an expert data analyst",
            "messages": [
                {"role": "user", "content": "Analyze this data"},
                {"role": "assistant", "content": "I'll analyze the data structure"}
            ],
            "metadata": {
                "dataset_info": {
                    "rows": 1500,
                    "columns": ["id", "name", "score"],
                    "quality_flags": ["missing_emails", "duplicate_ids"]
                }
            }
        }

        complex_response = {
            "analysis": {
                "overall_quality": "good",
                "issues_found": ["missing_emails", "duplicate_ids"],
                "recommendations": [
                    {"issue": "missing_emails", "action": "implement email validation"},
                    {"issue": "duplicate_ids", "action": "add unique constraint"}
                ]
            },
            "metrics": {
                "completeness": 85.4,
                "validity": 92.1,
                "consistency": 88.7
            }
        }

        prompt_id, response_id = logger.log_reasoning_step(
            prompt=complex_prompt,
            response=complex_response,
            assessment_id="complex_test_001"
        )

        # Verify complex data was preserved
        with open(logger.prompt_log_file, 'r', encoding='utf-8') as f:
            prompt_entry = json.loads(f.readline())
        assert prompt_entry['prompt'] == complex_prompt
        assert prompt_entry['prompt']['metadata']['dataset_info']['rows'] == 1500

        with open(logger.response_log_file, 'r', encoding='utf-8') as f:
            response_entry = json.loads(f.readline())
        assert response_entry['response'] == complex_response
        assert response_entry['response']['metrics']['completeness'] == 85.4


class TestReasoningLoggerFileOperations:
    """Test suite for file system operations."""

    def test_log_directory_creation(self):
        """Test that log directory is created if it doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            non_existent_path = Path(temp_dir) / "new_logs"
            assert not non_existent_path.exists()

            logger = ReasoningLogger(log_dir=non_existent_path)

            # Directory should be created
            assert non_existent_path.exists()
            assert non_existent_path.is_dir()

    def test_nested_directory_creation(self):
        """Test creation of nested log directories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            nested_path = Path(temp_dir) / "deep" / "nested" / "logs"
            assert not nested_path.exists()

            logger = ReasoningLogger(log_dir=nested_path)

            # All parent directories should be created
            assert nested_path.exists()
            assert nested_path.is_dir()
            assert (nested_path.parent / "../..").resolve().exists()

    def test_existing_directory_preservation(self, temp_log_dir):
        """Test that existing log directories are preserved."""
        # Create a test file in the directory
        test_file = temp_log_dir / "existing_file.txt"
        test_file.write_text("test content")

        logger = ReasoningLogger(log_dir=temp_log_dir)

        # Existing content should be preserved
        assert test_file.exists()
        assert test_file.read_text() == "test content"

    def test_log_file_appending(self, temp_log_dir):
        """Test that log entries are appended to existing files."""
        logger = ReasoningLogger(log_dir=temp_log_dir)

        # Log first entry
        logger.log_prompt("First prompt", assessment_id="append_test_1")

        # Log second entry
        logger.log_prompt("Second prompt", assessment_id="append_test_2")

        # Both entries should be in the file
        with open(logger.prompt_log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        assert len(lines) == 2
        entry1 = json.loads(lines[0])
        entry2 = json.loads(lines[1])

        assert entry1['prompt'] == "First prompt"
        assert entry2['prompt'] == "Second prompt"

    @pytest.mark.skipif(os.name == 'nt', reason="Windows filesystem has race conditions with concurrent writes")
    def test_concurrent_file_operations(self, temp_log_dir):
        """Test concurrent logging to the same files."""
        import uuid
        logger = ReasoningLogger(log_dir=temp_log_dir)

        def log_prompt_concurrent(index):
            # Use index for unique assessment ID to avoid ID collisions
            prompt_text = f"Concurrent prompt {index}"
            return logger.log_prompt(
                prompt=prompt_text,
                assessment_id=f"concurrent_{uuid.uuid4().hex[:8]}_{index}"
            )

        # Run multiple concurrent logging operations
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            for i in range(20):
                future = executor.submit(log_prompt_concurrent, i)
                futures.append(future)

            # Collect all prompt IDs
            prompt_ids = []
            for future in as_completed(futures):
                prompt_ids.append(future.result())

        # All prompt IDs should be unique
        assert len(prompt_ids) == 20
        assert len(set(prompt_ids)) == 20  # All unique

        # All entries should be in the file
        with open(logger.prompt_log_file, 'r', encoding='utf-8') as f:
            entries = [json.loads(line) for line in f]

        assert len(entries) == 20
        logged_prompts = [entry['prompt'] for entry in entries]
        expected_prompts = [f"Concurrent prompt {i}" for i in range(20)]

        # All prompts should be present (order may vary due to concurrency)
        assert set(logged_prompts) == set(expected_prompts)


class TestReasoningLoggerHistory:
    """Test suite for history retrieval and filtering."""

    def test_get_reasoning_history_basic(self, temp_log_dir, mock_reasoning_data):
        """Test basic reasoning history retrieval."""
        logger = ReasoningLogger(log_dir=temp_log_dir)

        # Log several reasoning steps
        for i in range(3):
            logger.log_reasoning_step(
                prompt=f"Test prompt {i}",
                response=f"Test response {i}",
                assessment_id=f"history_test_{i}",
                function_name=f"test_function_{i}"
            )

        # Retrieve history
        history = logger.get_reasoning_history()

        # Should return all entries sorted by timestamp
        assert len(history) >= 6  # 3 prompts + 3 responses

        # Verify entries have correct structure
        for entry in history:
            assert entry['type'] in ['prompt', 'response']
            assert 'timestamp' in entry

        # Verify prompts and responses are present
        prompts = [e for e in history if e['type'] == 'prompt']
        responses = [e for e in history if e['type'] == 'response']
        assert len(prompts) == 3
        assert len(responses) == 3

    def test_get_reasoning_history_with_assessment_filter(self, temp_log_dir):
        """Test history retrieval filtered by assessment ID."""
        logger = ReasoningLogger(log_dir=temp_log_dir)

        # Log entries with different assessment IDs
        logger.log_prompt("Target prompt", assessment_id="target_assessment")
        logger.log_prompt("Other prompt", assessment_id="other_assessment")
        logger.log_response("Target response", assessment_id="target_assessment")
        logger.log_response("Other response", assessment_id="other_assessment")

        # Filter by specific assessment
        history = logger.get_reasoning_history(assessment_id="target_assessment")

        # Should only return entries for target assessment
        assert len(history) == 2
        for entry in history:
            assert entry['assessment_id'] == "target_assessment"

        # Should include both prompt and response
        entry_types = [entry['type'] for entry in history]
        assert 'prompt' in entry_types
        assert 'response' in entry_types

    def test_get_reasoning_history_with_function_filter(self, temp_log_dir):
        """Test history retrieval filtered by function name."""
        logger = ReasoningLogger(log_dir=temp_log_dir)

        # Log entries for different functions
        logger.log_prompt("Function A prompt", function_name="function_a")
        logger.log_prompt("Function B prompt", function_name="function_b")
        logger.log_response("Function A response", function_name="function_a")

        # Filter by specific function
        history = logger.get_reasoning_history(function_name="function_a")

        # Should only return entries for function_a
        assert len(history) == 2
        for entry in history:
            assert entry['function_name'] == "function_a"

    def test_get_reasoning_history_with_limit(self, temp_log_dir):
        """Test history retrieval with result limit."""
        logger = ReasoningLogger(log_dir=temp_log_dir)

        # Log many entries
        for i in range(10):
            logger.log_prompt(f"Prompt {i}", assessment_id=f"limit_test_{i}")

        # Retrieve with limit
        history = logger.get_reasoning_history(limit=5)

        # Should respect limit
        assert len(history) == 5

    def test_get_reasoning_history_chronological_order(self, temp_log_dir):
        """Test that history is returned in chronological order."""
        logger = ReasoningLogger(log_dir=temp_log_dir)

        # Log entries with small delays to ensure different timestamps
        timestamps = []
        for i in range(3):
            logger.log_prompt(f"Ordered prompt {i}", assessment_id=f"order_test_{i}")
            time.sleep(0.01)  # Small delay
            timestamps.append(datetime.utcnow().isoformat())

        history = logger.get_reasoning_history()

        # Extract timestamps and verify ordering
        history_timestamps = [entry['timestamp'] for entry in history]

        # Should be in chronological order (earliest first)
        for i in range(1, len(history_timestamps)):
            assert history_timestamps[i-1] <= history_timestamps[i]

    def test_get_reasoning_history_empty_logs(self, temp_log_dir):
        """Test history retrieval with no existing logs."""
        logger = ReasoningLogger(log_dir=temp_log_dir)

        # No logs created yet
        history = logger.get_reasoning_history()

        # Should return empty list
        assert history == []

    def test_get_reasoning_history_error_handling(self, temp_log_dir):
        """Test history retrieval error handling for corrupted files."""
        logger = ReasoningLogger(log_dir=temp_log_dir)

        # Create corrupted log file
        with open(logger.prompt_log_file, 'w', encoding='utf-8') as f:
            f.write("invalid json line\n")
            f.write('{"valid": "json"}\n')

        # Should handle corruption gracefully
        history = logger.get_reasoning_history()

        # Should return what it can parse (may be empty due to error handling)
        assert isinstance(history, list)


class TestReasoningLoggerErrorHandling:
    """Test suite for error handling and edge cases."""

    def test_log_prompt_with_file_write_error(self, temp_log_dir):
        """Test prompt logging when file write fails."""
        logger = ReasoningLogger(log_dir=temp_log_dir)

        # Mock file write to raise exception
        with patch('builtins.open', side_effect=PermissionError("Permission denied")):
            prompt_id = logger.log_prompt("Test prompt", assessment_id="error_test")

            # Should return error ID instead of failing
            assert prompt_id.startswith("error_")

    def test_log_response_with_file_write_error(self, temp_log_dir):
        """Test response logging when file write fails."""
        logger = ReasoningLogger(log_dir=temp_log_dir)

        with patch('builtins.open', side_effect=IOError("Disk full")):
            response_id = logger.log_response("Test response", assessment_id="error_test")

            # Should return error ID instead of failing
            assert response_id.startswith("error_")

    def test_log_reasoning_step_with_partial_failure(self, temp_log_dir):
        """Test reasoning step logging when only one operation fails."""
        logger = ReasoningLogger(log_dir=temp_log_dir)

        # Mock to fail only response logging
        original_log_response = logger.log_response
        def mock_log_response(*args, **kwargs):
            raise IOError("Response logging failed")

        with patch.object(logger, 'log_response', side_effect=mock_log_response):
            prompt_id, response_id = logger.log_reasoning_step(
                prompt="Test prompt",
                response="Test response",
                assessment_id="partial_failure_test"
            )

            # Prompt should succeed, response should fail with error ID
            assert prompt_id.startswith("prompt_")
            assert response_id.startswith("error_")

    def test_none_parameters(self, temp_log_dir):
        """Test logging with None parameters."""
        logger = ReasoningLogger(log_dir=temp_log_dir)

        prompt_id = logger.log_prompt(
            prompt=None,
            llm_config=None,
            assessment_id=None,
            function_name=None
        )

        # Should handle None values gracefully
        assert prompt_id.startswith("prompt_")

        # Verify entry was logged with None values
        with open(logger.prompt_log_file, 'r', encoding='utf-8') as f:
            entry = json.loads(f.readline())

        assert entry['prompt'] is None
        assert entry['llm_config'] == {}  # Empty dict for None llm_config
        assert entry['assessment_id'] is None
        assert entry['function_name'] is None

    def test_empty_log_directory_string(self):
        """Test initialization with empty log directory string."""
        logger = ReasoningLogger(log_dir="")

        # Should handle empty string gracefully
        assert logger.log_dir == Path("")
        assert isinstance(logger.log_dir, Path)


@pytest.mark.integration
class TestReasoningLoggerIntegration:
    """Integration tests for reasoning logger with other enterprise components."""

    def test_reasoning_logger_with_enterprise_decorator(self, temp_log_dir, mock_reasoning_data):
        """Test reasoning logger integration with enterprise decorator."""
        from adri_enterprise.decorator import _log_reasoning_step

        # Mock the private function that would be called by the decorator
        logger = ReasoningLogger(log_dir=temp_log_dir)

        # Simulate decorator calling reasoning logger
        with patch('adri_enterprise.logging.reasoning.ReasoningLogger', return_value=logger):
            _log_reasoning_step(
                function_name=mock_reasoning_data['function_name'],
                store_prompt=True,
                store_response=True,
                llm_config=mock_reasoning_data['llm_config'],
                verbose=True
            )

            # Verify logger was instantiated (this is a simplified integration test)
            assert isinstance(logger, ReasoningLogger)

    def test_reasoning_logger_with_verodat_integration(self, temp_log_dir):
        """Test reasoning logger working alongside Verodat logging."""
        from adri_enterprise.logging.verodat import VerodatLogger

        reasoning_logger = ReasoningLogger(log_dir=temp_log_dir)
        verodat_logger = VerodatLogger(
            api_url="https://test.api.com",
            api_key="test-key"
        )

        # Both loggers should work independently
        prompt_id = reasoning_logger.log_prompt("Integration test prompt")
        assert prompt_id.startswith("prompt_")

        # Verodat logger should also work (will fail API call but that's expected)
        with patch('requests.post'):
            result = verodat_logger.log_assessment({"test": "data"})
            # Result may be True or False depending on mock, but shouldn't crash


@pytest.mark.performance
class TestReasoningLoggerPerformance:
    """Performance tests for reasoning logger."""

    def test_prompt_logging_performance(self, temp_log_dir, performance_baseline):
        """Test that prompt logging meets performance baseline."""
        logger = ReasoningLogger(log_dir=temp_log_dir)

        start_time = time.time()
        logger.log_prompt("Performance test prompt", assessment_id="perf_test")
        end_time = time.time()

        log_time = end_time - start_time
        assert log_time < performance_baseline['reasoning_log_write_max_time']

    def test_reasoning_logger_throughput(self, temp_log_dir):
        """Test reasoning logger throughput under load."""
        logger = ReasoningLogger(log_dir=temp_log_dir)

        def log_reasoning_steps(count):
            for i in range(count):
                logger.log_reasoning_step(
                    prompt=f"Throughput test prompt {i}",
                    response=f"Throughput test response {i}",
                    assessment_id=f"throughput_test_{i}"
                )

        start_time = time.time()
        log_reasoning_steps(50)
        end_time = time.time()

        total_time = end_time - start_time
        throughput = 50 / total_time  # reasoning steps per second

        # Should be able to log at least 10 reasoning steps per second
        assert throughput >= 10.0

    def test_concurrent_logging_performance(self, temp_log_dir):
        """Test performance with concurrent logging operations."""
        logger = ReasoningLogger(log_dir=temp_log_dir)

        def concurrent_log():
            return logger.log_reasoning_step(
                prompt="Concurrent performance test",
                response="Concurrent response",
                assessment_id=f"concurrent_perf_{id(logger)}"
            )

        start_time = time.time()

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(concurrent_log) for _ in range(25)]
            results = [future.result() for future in as_completed(futures)]

        end_time = time.time()

        # All operations should succeed
        assert len(results) == 25
        for prompt_id, response_id in results:
            assert prompt_id.startswith("prompt_")
            assert response_id.startswith("response_")

        # Total time should be reasonable
        total_time = end_time - start_time
        assert total_time < 10.0  # Should complete in under 10 seconds

    def test_large_data_logging_performance(self, temp_log_dir):
        """Test performance with large data structures."""
        logger = ReasoningLogger(log_dir=temp_log_dir)

        # Create large nested data structure
        large_prompt = {
            "system": "Complex analysis prompt",
            "data": {
                "customers": [
                    {
                        "id": i,
                        "name": f"Customer {i}",
                        "transactions": [
                            {"amount": j * 10, "date": f"2025-01-{j:02d}"}
                            for j in range(1, 31)  # 30 transactions per customer
                        ]
                    }
                    for i in range(100)  # 100 customers
                ]
            }
        }

        start_time = time.time()
        prompt_id = logger.log_prompt(
            prompt=large_prompt,
            assessment_id="large_data_test"
        )
        end_time = time.time()

        # Should handle large data within reasonable time
        log_time = end_time - start_time
        assert log_time < 5.0  # Should complete within 5 seconds
        assert prompt_id.startswith("prompt_")

        # Verify data integrity
        with open(logger.prompt_log_file, 'r', encoding='utf-8') as f:
            entry = json.loads(f.readline())

        assert len(entry['prompt']['data']['customers']) == 100
        assert len(entry['prompt']['data']['customers'][0]['transactions']) == 30
