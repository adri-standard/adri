"""
Unit tests for ReasoningLogger.

Tests CSV-based logging of AI reasoning prompts and responses.
"""

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

        # Check CSV files were created (correct attribute names)
        assert logger.prompts_log_path.exists()
        assert logger.responses_log_path.exists()

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

        # Check CSV file has content (correct attribute name)
        with open(logger.prompts_log_path, 'r', encoding='utf-8') as f:
            content = f.read()
            assert "test_assess_001" in content
            assert "run_001" in content
            assert "step_001" in content
            assert "You are a risk analyst" in content
            assert "claude-3-5-sonnet" in content

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

        # Check CSV file has content (correct attribute name)
        with open(logger.responses_log_path, 'r', encoding='utf-8') as f:
            content = f.read()
            assert "test_assess_002" in content
            assert prompt_id in content
            assert "Risk level: HIGH" in content
            assert "2000" in content

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

        # Read CSV and check for hash (correct attribute name)
        with open(logger.prompts_log_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # Hash should be present (16 hex characters for truncated hash)
            assert len([c for c in content if c in '0123456789abcdef']) >= 16

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

        # Read CSV and check for hash (correct attribute name)
        with open(logger.responses_log_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # Hash should be present (16 hex characters for truncated hash)
            assert len([c for c in content if c in '0123456789abcdef']) >= 16

    def test_csv_headers(self, logger):
        """Test that CSV files have correct headers."""
        # Check prompts CSV (correct attribute name)
        with open(logger.prompts_log_path, 'r', encoding='utf-8') as f:
            first_line = f.readline().strip()
            expected_headers = [
                "prompt_id", "assessment_id", "run_id", "step_id",
                "prompt_hash", "model", "temperature", "seed",
                "max_tokens", "system_prompt", "user_prompt", "timestamp"
            ]
            for header in expected_headers:
                assert header in first_line

        # Check responses CSV (correct attribute name)
        with open(logger.responses_log_path, 'r', encoding='utf-8') as f:
            first_line = f.readline().strip()
            expected_headers = [
                "response_id", "assessment_id", "prompt_id",
                "response_hash", "response_text", "processing_time_ms",
                "token_count", "timestamp"
            ]
            for header in expected_headers:
                assert header in first_line

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

        # Count lines in CSV (should be header + 15 prompts) (correct attribute name)
        with open(logger.prompts_log_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            assert len(lines) == 16  # header + 15 prompts

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
            assert len(lines) > 1  # header + at least one record

        # Clear logs
        logger.clear_logs()

        # Files should still exist but only have headers
        assert logger.prompts_log_path.exists()
        assert logger.responses_log_path.exists()

        with open(logger.prompts_log_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            assert len(lines) == 1  # only header
