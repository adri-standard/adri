"""
ADRI Enterprise - AI Reasoning Step Logging.

Provides logging and tracking for AI reasoning steps, including prompt/response pairs
and reasoning validation for enterprise deployments.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class ReasoningLogger:
    """
    Enterprise AI reasoning step logger.

    Tracks AI prompts, responses, and reasoning validation for audit and
    compliance purposes in enterprise deployments.
    """

    def __init__(
        self,
        log_dir: Path | str = "./logs",
        store_prompts: bool = True,
        store_responses: bool = True,
    ):
        """
        Initialize reasoning logger.

        Args:
            log_dir: Directory for reasoning log files (default: ./logs)
            store_prompts: Whether to store AI prompts (default: True)
            store_responses: Whether to store AI responses (default: True)
        """
        self.log_dir = Path(log_dir)
        self.store_prompts = store_prompts
        self.store_responses = store_responses

        # Ensure log directory exists
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Define log file paths
        self.prompt_log_file = self.log_dir / "adri_reasoning_prompts.jsonl"
        self.response_log_file = self.log_dir / "adri_reasoning_responses.jsonl"

    def log_reasoning_step(
        self,
        prompt: str | dict[str, Any],
        response: str | dict[str, Any],
        llm_config: dict[str, Any] | None = None,
        assessment_id: str | None = None,
        function_name: str | None = None,
    ) -> tuple[str | None, str | None]:
        """
        Log a complete AI reasoning step (prompt + response).

        Args:
            prompt: AI prompt text or structured prompt
            response: AI response text or structured response
            llm_config: LLM configuration used
            assessment_id: Associated ADRI assessment ID
            function_name: Name of the protected function

        Returns:
            Tuple of (prompt_id, response_id)
        """
        prompt_id = None
        response_id = None

        # Log prompt if enabled
        if self.store_prompts:
            prompt_id = self.log_prompt(
                prompt=prompt,
                llm_config=llm_config,
                assessment_id=assessment_id,
                function_name=function_name,
            )

        # Log response if enabled
        if self.store_responses:
            response_id = self.log_response(
                response=response,
                prompt_id=prompt_id,
                llm_config=llm_config,
                assessment_id=assessment_id,
                function_name=function_name,
            )

        return prompt_id, response_id

    def log_prompt(
        self,
        prompt: str | dict[str, Any],
        llm_config: dict[str, Any] | None = None,
        assessment_id: str | None = None,
        function_name: str | None = None,
    ) -> str:
        """
        Log an AI prompt.

        Args:
            prompt: AI prompt text or structured prompt
            llm_config: LLM configuration used
            assessment_id: Associated ADRI assessment ID
            function_name: Name of the protected function

        Returns:
            Prompt ID for linking to responses
        """
        try:
            # Generate unique prompt ID
            timestamp = datetime.utcnow().isoformat()
            prompt_id = f"prompt_{timestamp}_{id(prompt)}"

            # Construct prompt log entry
            prompt_entry = {
                "prompt_id": prompt_id,
                "timestamp": timestamp,
                "prompt": prompt,
                "llm_config": llm_config or {},
                "assessment_id": assessment_id,
                "function_name": function_name,
            }

            # Append to JSONL file
            with open(self.prompt_log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(prompt_entry) + "\n")

            return prompt_id

        except Exception as e:
            logger.error(f"Failed to log prompt: {e}")
            return f"error_{datetime.utcnow().isoformat()}"

    def log_response(
        self,
        response: str | dict[str, Any],
        prompt_id: str | None = None,
        llm_config: dict[str, Any] | None = None,
        assessment_id: str | None = None,
        function_name: str | None = None,
    ) -> str:
        """
        Log an AI response.

        Args:
            response: AI response text or structured response
            prompt_id: Associated prompt ID for linking
            llm_config: LLM configuration used
            assessment_id: Associated ADRI assessment ID
            function_name: Name of the protected function

        Returns:
            Response ID
        """
        try:
            # Generate unique response ID
            timestamp = datetime.utcnow().isoformat()
            response_id = f"response_{timestamp}_{id(response)}"

            # Construct response log entry
            response_entry = {
                "response_id": response_id,
                "prompt_id": prompt_id,
                "timestamp": timestamp,
                "response": response,
                "llm_config": llm_config or {},
                "assessment_id": assessment_id,
                "function_name": function_name,
            }

            # Append to JSONL file
            with open(self.response_log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(response_entry) + "\n")

            return response_id

        except Exception as e:
            logger.error(f"Failed to log response: {e}")
            return f"error_{datetime.utcnow().isoformat()}"

    def get_reasoning_history(
        self,
        assessment_id: str | None = None,
        function_name: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """
        Retrieve reasoning history from logs.

        Args:
            assessment_id: Filter by assessment ID
            function_name: Filter by function name
            limit: Maximum number of entries to return

        Returns:
            List of reasoning log entries
        """
        try:
            history = []

            # Read prompt logs
            if self.prompt_log_file.exists():
                with open(self.prompt_log_file, "r", encoding="utf-8") as f:
                    for line in f:
                        if len(history) >= limit:
                            break

                        entry = json.loads(line)

                        # Apply filters
                        if assessment_id and entry.get("assessment_id") != assessment_id:
                            continue
                        if function_name and entry.get("function_name") != function_name:
                            continue

                        history.append({"type": "prompt", **entry})

            # Read response logs
            if self.response_log_file.exists():
                with open(self.response_log_file, "r", encoding="utf-8") as f:
                    for line in f:
                        if len(history) >= limit:
                            break

                        entry = json.loads(line)

                        # Apply filters
                        if assessment_id and entry.get("assessment_id") != assessment_id:
                            continue
                        if function_name and entry.get("function_name") != function_name:
                            continue

                        history.append({"type": "response", **entry})

            # Sort by timestamp
            history.sort(key=lambda x: x.get("timestamp", ""))

            return history[:limit]

        except Exception as e:
            logger.error(f"Failed to retrieve reasoning history: {e}")
            return []
