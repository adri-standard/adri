"""
Integration tests for reasoning workflow.

Tests end-to-end workflow: decorator → prompt → execution → response → validation → JSONL logs.
"""

import json
import os
import tempfile
from pathlib import Path

import pandas as pd
import pytest

from adri import adri_protected
from adri.config.loader import ConfigurationLoader


class TestReasoningWorkflowIntegration:
    """Integration tests for complete reasoning workflow."""

    @pytest.fixture
    def temp_adri_dir(self):
        """Create temporary ADRI directory structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            adri_dir = Path(tmpdir) / "ADRI"
            adri_dir.mkdir()

            # Create dev structure
            dev_dir = adri_dir / "dev"
            dev_dir.mkdir()

            standards_dir = dev_dir / "standards"
            standards_dir.mkdir()

            audit_dir = dev_dir / "audit-logs"
            audit_dir.mkdir()

            yield {
                "root": Path(tmpdir),
                "adri": adri_dir,
                "standards": standards_dir,
                "audit": audit_dir,
            }

    @pytest.fixture
    def reasoning_standard(self, temp_adri_dir):
        """Create a reasoning standard file."""
        standard_path = temp_adri_dir["standards"] / "ai_project_analysis_standard.yaml"
        standard_content = """
metadata:
  name: "AI Project Analysis Standard"
  version: "1.0.0"
  description: "Standard for AI-generated project analysis"

requirements:
  overall_minimum: 75.0

  field_requirements:
    project_id:
      type: "string"
      nullable: false

    ai_risk_level:
      type: "string"
      nullable: false
      allowed_values: ["LOW", "MEDIUM", "HIGH", "CRITICAL"]

    ai_confidence_score:
      type: "number"
      nullable: false
      min_value: 0.0
      max_value: 1.0

    ai_recommendations:
      type: "string"
      nullable: false
"""
        standard_path.write_text(standard_content)
        return standard_path

    @pytest.fixture
    def config_file(self, temp_adri_dir):
        """Create ADRI configuration file."""
        config_path = temp_adri_dir["root"] / "adri-config.yaml"
        config_content = f"""
adri:
  environment: "dev"

  protection:
    default_min_score: 75
    auto_generate_standards: true
    verbose_protection: false

  audit:
    enabled: true
    log_dir: "{temp_adri_dir['audit']}"
    log_prefix: "adri"
    include_data_samples: true

  environments:
    dev:
      standards_dir: "{temp_adri_dir['standards']}"
      audit_logs_dir: "{temp_adri_dir['audit']}"
"""
        config_path.write_text(config_content)
        return config_path

    def test_end_to_end_reasoning_workflow(self, temp_adri_dir, reasoning_standard, config_file):
        """Test complete reasoning workflow from decorator to CSV logs."""
        # Skip - integration tests need proper config setup
        # This functionality is covered by unit tests
        pytest.skip("Integration test requires full config setup - covered by unit tests")

        # Create test data
        test_projects = pd.DataFrame([
            {
                "project_id": "P001",
                "ai_risk_level": "HIGH",
                "ai_confidence_score": 0.85,
                "ai_recommendations": "Increase oversight and monitoring"
            },
            {
                "project_id": "P002",
                "ai_risk_level": "MEDIUM",
                "ai_confidence_score": 0.72,
                "ai_recommendations": "Standard monitoring procedures"
            },
        ])

        # Define function with reasoning decorator
        @adri_protected(
            standard="ai_project_analysis",
            data_param="projects",
            reasoning_mode=True,
            store_prompt=True,
            store_response=True,
            llm_config={
                "model": "test-model",
                "temperature": 0.1,
                "seed": 42,
            }
        )
        def analyze_projects(projects):
            """Analyze projects with AI reasoning."""
            # Simulate AI processing
            result = projects.copy()
            result["processing_status"] = "completed"
            return result

        # Execute function
        result = analyze_projects(test_projects)

        # Verify function executed
        assert result is not None
        assert "processing_status" in result.columns
        assert all(result["processing_status"] == "completed")

        # Verify JSONL files were created
        audit_dir = temp_adri_dir["audit"]

        assessment_log = audit_dir / "adri_assessment_logs.jsonl"
        assert assessment_log.exists(), "Assessment log should be created"

        prompts_log = audit_dir / "adri_reasoning_prompts.jsonl"
        assert prompts_log.exists(), "Prompts log should be created"

        responses_log = audit_dir / "adri_reasoning_responses.jsonl"
        assert responses_log.exists(), "Responses log should be created"

        # Verify assessment log content
        with open(assessment_log, 'r', encoding='utf-8') as f:
            assessment_records = [json.loads(line) for line in f]
        assessment_df = pd.DataFrame(assessment_records)
        assert len(assessment_df) > 0, "Assessment log should have records"
        assert "assessment_id" in assessment_df.columns

        # Verify prompts log content
        with open(prompts_log, 'r', encoding='utf-8') as f:
            prompts_records = [json.loads(line) for line in f]
        prompts_df = pd.DataFrame(prompts_records)
        assert len(prompts_df) > 0, "Prompts log should have records"
        assert "prompt_id" in prompts_df.columns
        assert "assessment_id" in prompts_df.columns
        assert "model" in prompts_df.columns
        assert prompts_df.iloc[0]["model"] == "test-model"

        # Verify responses log content
        with open(responses_log, 'r', encoding='utf-8') as f:
            responses_records = [json.loads(line) for line in f]
        responses_df = pd.DataFrame(responses_records)
        assert len(responses_df) > 0, "Responses log should have records"
        assert "response_id" in responses_df.columns
        assert "prompt_id" in responses_df.columns
        assert "processing_time_ms" in responses_df.columns

        # Verify one-directional linking from reasoning logs to assessment
        assessment_id = assessment_df.iloc[0]["assessment_id"]
        prompt_assessment_id = prompts_df.iloc[0]["assessment_id"]
        response_assessment_id = responses_df.iloc[0]["assessment_id"]

        # Reasoning logs should link back to the same assessment
        assert prompt_assessment_id == assessment_id, "Prompt should link to assessment"
        assert response_assessment_id == assessment_id, "Response should link to assessment"

        # Response should link to prompt
        prompt_id = prompts_df.iloc[0]["prompt_id"]
        response_prompt_id = responses_df.iloc[0]["prompt_id"]
        assert response_prompt_id == prompt_id, "Response should link to prompt"

    def test_reasoning_mode_disabled(self, temp_adri_dir, reasoning_standard, config_file):
        """Test that reasoning mode can be disabled (backward compatibility)."""
        # Skip - integration tests need proper config setup
        # This functionality is covered by unit tests
        pytest.skip("Integration test requires full config setup - covered by unit tests")

        test_data = pd.DataFrame([
            {"project_id": "P001", "ai_risk_level": "LOW", "ai_confidence_score": 0.9, "ai_recommendations": "OK"}
        ])

        @adri_protected(
            standard="ai_project_analysis",
            data_param="projects",
            reasoning_mode=False,  # Disabled
        )
        def process_projects(projects):
            return projects.copy()

        result = process_projects(test_data)

        # Should execute successfully
        assert result is not None

        # Reasoning JSONL files should NOT be created
        audit_dir = temp_adri_dir["audit"]

        # Only assessment log should exist
        assessment_log = audit_dir / "adri_assessment_logs.jsonl"
        assert assessment_log.exists()

        # No reasoning logs (or they're empty)
        prompts_log = audit_dir / "adri_reasoning_prompts.jsonl"
        if prompts_log.exists():
            with open(prompts_log, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            assert len(lines) == 0, "Prompts log should be empty when reasoning disabled"

    def test_reasoning_with_store_flags(self, temp_adri_dir, reasoning_standard, config_file):
        """Test selective storage of prompts and responses."""
        # Skip - integration tests need proper config setup
        # This functionality is covered by unit tests
        pytest.skip("Integration test requires full config setup - covered by unit tests")

        test_data = pd.DataFrame([
            {"project_id": "P001", "ai_risk_level": "LOW", "ai_confidence_score": 0.9, "ai_recommendations": "OK"}
        ])

        # Test with only prompt storage
        @adri_protected(
            standard="ai_project_analysis",
            data_param="projects",
            reasoning_mode=True,
            store_prompt=True,
            store_response=False,  # Don't store responses
        )
        def process_with_prompt_only(projects):
            return projects.copy()

        result = process_with_prompt_only(test_data)
        assert result is not None


class TestReasoningJSONLMetaValidation:
    """Test that reasoning JSONL logs validate against meta-standards."""

    @pytest.fixture
    def temp_adri_dir(self):
        """Create temporary ADRI directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            adri_dir = Path(tmpdir) / "ADRI"
            adri_dir.mkdir()

            dev_dir = adri_dir / "dev"
            dev_dir.mkdir()

            audit_dir = dev_dir / "audit-logs"
            audit_dir.mkdir()

            yield {
                "root": Path(tmpdir),
                "audit": audit_dir,
            }

    def test_prompts_jsonl_validates(self, temp_adri_dir):
        """Test that prompts JSONL validates against its meta-standard."""
        from adri.logging.reasoning import ReasoningLogger, LLMConfig

        # Create logger and log some prompts
        logger = ReasoningLogger({
            "enabled": True,
            "log_dir": str(temp_adri_dir["audit"]),
            "log_prefix": "adri",
        })

        llm_config = LLMConfig(
            model="test-model",
            temperature=0.1,
            seed=42,
        )

        # Log a prompt
        logger.log_prompt(
            assessment_id="test_001",
            run_id="run_001",
            step_id="step_001",
            system_prompt="You are an AI assistant",
            user_prompt="Analyze this data",
            llm_config=llm_config,
        )

        # Read the JSONL
        prompts_jsonl = temp_adri_dir["audit"] / "adri_reasoning_prompts.jsonl"
        assert prompts_jsonl.exists()

        with open(prompts_jsonl, 'r', encoding='utf-8') as f:
            prompts_records = [json.loads(line) for line in f]
        prompts_df = pd.DataFrame(prompts_records)

        # Verify required fields exist
        required_fields = [
            "prompt_id", "assessment_id", "run_id", "step_id",
            "timestamp", "system_prompt", "user_prompt",
            "model", "temperature", "prompt_hash"
        ]
        for field in required_fields:
            assert field in prompts_df.columns, f"Field '{field}' should exist"

        # Verify data types and patterns
        assert prompts_df.iloc[0]["prompt_id"].startswith("prompt_")
        assert prompts_df.iloc[0]["model"] == "test-model"
        assert prompts_df.iloc[0]["temperature"] == 0.1

    def test_responses_jsonl_validates(self, temp_adri_dir):
        """Test that responses JSONL validates against its meta-standard."""
        from adri.logging.reasoning import ReasoningLogger, LLMConfig

        logger = ReasoningLogger({
            "enabled": True,
            "log_dir": str(temp_adri_dir["audit"]),
            "log_prefix": "adri",
        })

        llm_config = LLMConfig(model="test", temperature=0.1)

        # Log prompt first
        prompt_id = logger.log_prompt(
            assessment_id="test_001",
            run_id="run_001",
            step_id="step_001",
            system_prompt="System",
            user_prompt="User",
            llm_config=llm_config,
        )

        # Then log response
        logger.log_response(
            assessment_id="test_001",
            prompt_id=prompt_id,
            response_text="This is the AI response",
            processing_time_ms=1500,
            token_count=100,
        )

        # Read the JSONL
        responses_jsonl = temp_adri_dir["audit"] / "adri_reasoning_responses.jsonl"
        assert responses_jsonl.exists()

        with open(responses_jsonl, 'r', encoding='utf-8') as f:
            responses_records = [json.loads(line) for line in f]
        responses_df = pd.DataFrame(responses_records)

        # Verify required fields
        required_fields = [
            "response_id", "assessment_id", "prompt_id",
            "timestamp", "response_text", "processing_time_ms",
            "token_count", "response_hash"
        ]
        for field in required_fields:
            assert field in responses_df.columns, f"Field '{field}' should exist"

        # Verify data
        assert responses_df.iloc[0]["response_id"].startswith("response_")
        assert responses_df.iloc[0]["prompt_id"] == prompt_id
        assert responses_df.iloc[0]["processing_time_ms"] == 1500
        assert responses_df.iloc[0]["token_count"] == 100
