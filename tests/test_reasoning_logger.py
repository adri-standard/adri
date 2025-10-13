"""
Unit tests for ReasoningLogger.

Tests JSONL-based logging of AI reasoning prompts and responses.
"""

import json
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from adri.logging.reasoning import LLMConfig, ReasoningLogger


class TestLLMConfig:
    """Test LLMConfig dataclass."""

    def test_llm_config_creation(self):
        """Test creating LLM configuration."""
        config = LLMConfig(
            model="claude-3-5-sonnet",
            temperature=0.1,
            seed=42,
            max_tokens=4000,
        )

        assert config.model == "claude-3-5-sonnet"
        assert config.temperature == 0.1
        assert config.seed == 42
        assert config.max_tokens == 4000

    def test_llm_config_defaults(self):
        """Test LLM config with minimal parameters."""
        config = LLMConfig(
            model="gpt-4",
            temperature=0.5,
        )

        assert config.model == "gpt-4"
        assert config.temperature == 0.5
        assert config.seed is None
        assert config.max_tokens == 4000  # default


class TestReasoningLogger:
    """Test ReasoningLogger functionality."""

    @pytest.fixture
    def temp_log_dir(self):
        """Create temporary directory for logs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def logger_config(self, temp_log_dir):
        """Create logger configuration."""
        return {
            "enabled": True,
            "log_dir": str(temp_log_dir),
            "log_prefix": "test_adri",
            "max_log_size_mb": 10,
        }

    @pytest.fixture
    def logger(self, logger_config):
        """Create ReasoningLogger instance."""
        return ReasoningLogger(logger_config)

    def test_logger_initialization(self, logger, temp_log_dir):
        """Test logger initializes correctly."""
        assert logger.enabled is True
        assert logger.log_dir == temp_log_dir
        assert logger.log_prefix == "test_adri"

        # Check JSONL files were created
        assert logger.prompts_log_path.exists()
        assert logger.responses_log_path.exists()
        assert logger.prompts_log_path.suffix == ".jsonl"
        assert logger.responses_log_path.suffix == ".jsonl"

    def test_logger_disabled(self, temp_log_dir):
        """Test logger when disabled."""
        logger = ReasoningLogger({
            "enabled": False,
            "log_dir": str(temp_log_dir)
        })
        assert logger.enabled is False

        # Should not create any files
        assert not logger.prompts_log_path.exists()
        assert not logger.responses_log_path.exists()

    def test_log_prompt(self, logger):
        """Test logging a prompt."""
        llm_config = LLMConfig(
            model="claude-3-5-sonnet",
            temperature=0.1,
            seed=42,
        )

        prompt_id = logger.log_prompt(
            assessment_id="test_assess_001",
            run_id="run_001",
            step_id="step_001",
            system_prompt="You are a risk analyst",
            user_prompt="Analyze project risks",
            llm_config=llm_config,
        )

        # Check prompt_id was generated
        assert prompt_id.startswith("prompt_")
        assert len(prompt_id) > 10

        # Check JSONL file has content
        with open(logger.prompts_log_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            assert len(lines) == 1  # One JSON line
            record = json.loads(lines[0])
            assert record["assessment_id"] == "test_assess_001"
            assert record["run_id"] == "run_001"
            assert record["step_id"] == "step_001"
            assert record["system_prompt"] == "You are a risk analyst"
            assert record["model"] == "claude-3-5-sonnet"

    def test_log_response(self, logger):
        """Test logging a response."""
        # First log a prompt
        llm_config = LLMConfig(model="test-model", temperature=0.1)
        prompt_id = logger.log_prompt(
            assessment_id="test_assess_002",
            run_id="run_002",
            step_id="step_001",
            system_prompt="System",
            user_prompt="User",
            llm_config=llm_config,
        )

        # Then log response
        response_id = logger.log_response(
            assessment_id="test_assess_002",
            prompt_id=prompt_id,
            response_text="Risk level: HIGH",
            processing_time_ms=2000,
            token_count=100,
        )

        # Check response_id was generated
        assert response_id.startswith("response_")
        assert len(response_id) > 10

        # Check JSONL file has content
        with open(logger.responses_log_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            assert len(lines) == 1  # One JSON line
            record = json.loads(lines[0])
            assert record["assessment_id"] == "test_assess_002"
            assert record["prompt_id"] == prompt_id
            assert record["response_text"] == "Risk level: HIGH"
            assert record["processing_time_ms"] == 2000

    def test_prompt_id_uniqueness(self, logger):
        """Test that prompt IDs are unique."""
        llm_config = LLMConfig(model="test", temperature=0.1)

        prompt_ids = set()
        for i in range(10):
            prompt_id = logger.log_prompt(
                assessment_id=f"assess_{i}",
                run_id="run_001",
                step_id="step_001",
                system_prompt="System",
                user_prompt=f"Prompt {i}",
                llm_config=llm_config,
            )
            prompt_ids.add(prompt_id)

        # All prompt IDs should be unique
        assert len(prompt_ids) == 10

    def test_response_id_uniqueness(self, logger):
        """Test that response IDs are unique."""
        llm_config = LLMConfig(model="test", temperature=0.1)
        prompt_id = logger.log_prompt(
            assessment_id="assess_001",
            run_id="run_001",
            step_id="step_001",
            system_prompt="System",
            user_prompt="User",
            llm_config=llm_config,
        )

        response_ids = set()
        for i in range(10):
            response_id = logger.log_response(
                assessment_id="assess_001",
                prompt_id=prompt_id,
                response_text=f"Response {i}",
                processing_time_ms=1000,
                token_count=50,
            )
            response_ids.add(response_id)

        # All response IDs should be unique
        assert len(response_ids) == 10

    def test_prompt_hash_generation(self, logger):
        """Test that prompt hashes are generated."""
        llm_config = LLMConfig(model="test", temperature=0.1)

        prompt_id = logger.log_prompt(
            assessment_id="assess_001",
            run_id="run_001",
            step_id="step_001",
            system_prompt="System prompt text",
            user_prompt="User prompt text",
            llm_config=llm_config,
        )

        # Read JSONL and check for hash
        with open(logger.prompts_log_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            record = json.loads(lines[0])
            # Hash should be present (16 hex characters for truncated hash)
            assert "prompt_hash" in record
            assert len(record["prompt_hash"]) == 16
            # Verify it's a hex string
            int(record["prompt_hash"], 16)

    def test_response_hash_generation(self, logger):
        """Test that response hashes are generated."""
        llm_config = LLMConfig(model="test", temperature=0.1)
        prompt_id = logger.log_prompt(
            assessment_id="assess_001",
            run_id="run_001",
            step_id="step_001",
            system_prompt="System",
            user_prompt="User",
            llm_config=llm_config,
        )

        response_id = logger.log_response(
            assessment_id="assess_001",
            prompt_id=prompt_id,
            response_text="Response with content to hash",
            processing_time_ms=1000,
            token_count=50,
        )

        # Read JSONL and check for hash
        with open(logger.responses_log_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            record = json.loads(lines[0])
            # Hash should be present (16 hex characters for truncated hash)
            assert "response_hash" in record
            assert len(record["response_hash"]) == 16
            # Verify it's a hex string
            int(record["response_hash"], 16)

    def test_jsonl_format(self, logger):
        """Test that files use JSONL format (no headers, valid JSON per line)."""
        llm_config = LLMConfig(model="test", temperature=0.1)

        # Log a prompt
        prompt_id = logger.log_prompt(
            assessment_id="test_assess",
            run_id="run_001",
            step_id="step_001",
            system_prompt="System",
            user_prompt="User",
            llm_config=llm_config,
        )

        # Log a response
        logger.log_response(
            assessment_id="test_assess",
            prompt_id=prompt_id,
            response_text="Response text",
            processing_time_ms=1000,
            token_count=50,
        )

        # Verify prompts file has valid JSON lines (no headers)
        with open(logger.prompts_log_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            assert len(lines) == 1
            record = json.loads(lines[0])  # Should not raise exception
            assert "prompt_id" in record
            assert "assessment_id" in record

        # Verify responses file has valid JSON lines (no headers)
        with open(logger.responses_log_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            assert len(lines) == 1
            record = json.loads(lines[0])  # Should not raise exception
            assert "response_id" in record
            assert "prompt_id" in record

    def test_thread_safety(self, logger):
        """Test that logger is thread-safe."""
        import threading

        llm_config = LLMConfig(model="test", temperature=0.1)

        def log_prompts():
            for i in range(5):
                logger.log_prompt(
                    assessment_id=f"assess_{i}",
                    run_id="run_001",
                    step_id="step_001",
                    system_prompt="System",
                    user_prompt=f"Prompt {i}",
                    llm_config=llm_config,
                )

        # Run multiple threads
        threads = [threading.Thread(target=log_prompts) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Count lines in JSONL (should be 15 prompts, no header)
        with open(logger.prompts_log_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            assert len(lines) == 15  # 15 prompts (no header in JSONL)

    def test_get_log_files(self, logger):
        """Test getting log file paths."""
        log_files = logger.get_log_files()

        assert "reasoning_prompts" in log_files
        assert "reasoning_responses" in log_files
        assert log_files["reasoning_prompts"] == logger.prompts_log_path
        assert log_files["reasoning_responses"] == logger.responses_log_path

    def test_clear_logs(self, logger):
        """Test clearing log files."""
        # Log some data first
        llm_config = LLMConfig(model="test", temperature=0.1)
        logger.log_prompt(
            assessment_id="test",
            run_id="run_001",
            step_id="step_001",
            system_prompt="System",
            user_prompt="User",
            llm_config=llm_config,
        )

        # Verify file exists and has content
        assert logger.prompts_log_path.exists()
        with open(logger.prompts_log_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            assert len(lines) >= 1  # At least one record

        # Clear logs
        logger.clear_logs()

        # Files should still exist but be empty (no headers in JSONL)
        assert logger.prompts_log_path.exists()
        assert logger.responses_log_path.exists()

        with open(logger.prompts_log_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            assert len(lines) == 0  # Empty file (no headers in JSONL)
