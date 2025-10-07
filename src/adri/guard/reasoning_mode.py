"""
ADRI Reasoning Protection Mode.

Specialized protection mode for AI/LLM reasoning workflows that coordinates
prompt logging, response capture, and AI output validation.
"""

import logging
import os
from typing import Any, Callable, Dict, Optional

from ..logging.reasoning import LLMConfig, ReasoningLogger

logger = logging.getLogger(__name__)


class ReasoningProtectionMode:
    """
    Protection mode for AI/LLM reasoning workflows.

    Coordinates the reasoning workflow:
    1. Captures prompts before AI execution
    2. Logs prompts to CSV with LLM configuration
    3. Captures responses after AI execution
    4. Logs responses to CSV with performance metrics
    5. Links reasoning logs to main assessment via IDs
    6. Validates AI outputs against reasoning standards
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize reasoning protection mode.

        Args:
            config: Configuration dictionary with reasoning settings
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)

        # Initialize reasoning logger if enabled
        reasoning_config = self._extract_reasoning_config(config)
        self.reasoning_logger = ReasoningLogger(reasoning_config)

    def _extract_reasoning_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Extract reasoning-specific configuration."""
        # Get audit config for log directory
        audit_config = config.get("audit", {})

        return {
            "enabled": audit_config.get("enabled", True),
            "log_dir": audit_config.get("log_dir", "./logs"),
            "log_prefix": audit_config.get("log_prefix", "adri"),
            "max_log_size_mb": audit_config.get("max_log_size_mb", 100),
        }

    def log_prompt(
        self,
        assessment_id: str,
        run_id: str,
        step_id: str,
        system_prompt: str,
        user_prompt: str,
        llm_config: LLMConfig,
    ) -> str:
        """
        Log AI reasoning prompt.

        Args:
            assessment_id: Associated assessment ID
            run_id: Current run identifier
            step_id: Step identifier in workflow
            system_prompt: System/instruction prompt
            user_prompt: User/context prompt
            llm_config: LLM configuration

        Returns:
            prompt_id for referencing this prompt
        """
        if not self.reasoning_logger.enabled:
            return ""

        return self.reasoning_logger.log_prompt(
            assessment_id=assessment_id,
            run_id=run_id,
            step_id=step_id,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            llm_config=llm_config,
        )

    def log_response(
        self,
        assessment_id: str,
        prompt_id: str,
        response_text: str,
        processing_time_ms: int,
        token_count: Optional[int] = None,
    ) -> str:
        """
        Log AI reasoning response.

        Args:
            assessment_id: Associated assessment ID
            prompt_id: Reference to prompt that generated this response
            response_text: AI-generated response
            processing_time_ms: Processing time in milliseconds
            token_count: Number of tokens in response

        Returns:
            response_id for referencing this response
        """
        if not self.reasoning_logger.enabled:
            return ""

        return self.reasoning_logger.log_response(
            assessment_id=assessment_id,
            prompt_id=prompt_id,
            response_text=response_text,
            processing_time_ms=processing_time_ms,
            token_count=token_count,
        )

    def capture_reasoning_context(
        self,
        func: Callable,
        args: tuple,
        kwargs: dict,
    ) -> Dict[str, str]:
        """
        Extract reasoning context from function parameters.

        Looks for prompt-related parameters in function signature
        and captures them for logging.

        Args:
            func: Function being protected
            args: Function arguments
            kwargs: Function keyword arguments

        Returns:
            Dictionary with system_prompt, user_prompt, etc.
        """
        import inspect

        # Default prompts if not found
        context = {
            "system_prompt": "AI reasoning system prompt",
            "user_prompt": "AI reasoning user prompt",
        }

        # Try to extract from kwargs
        if "system_prompt" in kwargs:
            context["system_prompt"] = str(kwargs["system_prompt"])
        if "user_prompt" in kwargs:
            context["user_prompt"] = str(kwargs["user_prompt"])
        if "prompt" in kwargs:
            context["user_prompt"] = str(kwargs["prompt"])

        # Try to extract from positional args based on function signature
        try:
            sig = inspect.signature(func)
            params = list(sig.parameters.keys())

            for idx, param_name in enumerate(params):
                if idx < len(args):
                    if param_name in ["system_prompt", "instruction"]:
                        context["system_prompt"] = str(args[idx])
                    elif param_name in ["user_prompt", "prompt", "query"]:
                        context["user_prompt"] = str(args[idx])
        except Exception as e:
            self.logger.debug(f"Could not inspect function signature: {e}")

        return context

    def create_llm_config(
        self, llm_config_dict: Optional[Dict[str, Any]] = None
    ) -> LLMConfig:
        """
        Create LLMConfig from dictionary or defaults.

        Args:
            llm_config_dict: Optional LLM configuration dictionary

        Returns:
            LLMConfig instance
        """
        if not llm_config_dict:
            # Return default configuration
            return LLMConfig(
                model="unknown",
                temperature=0.1,
                seed=None,
                max_tokens=4000,
            )

        return LLMConfig(
            model=llm_config_dict.get("model", "unknown"),
            temperature=llm_config_dict.get("temperature", 0.1),
            seed=llm_config_dict.get("seed"),
            max_tokens=llm_config_dict.get("max_tokens", 4000),
        )

    def generate_run_id(self) -> str:
        """Generate a unique run ID for reasoning workflow tracking."""
        import time

        return f"run_{int(time.time() * 1000)}_{os.urandom(2).hex()}"

    def generate_step_id(self, step_number: int = 1) -> str:
        """Generate a step ID for reasoning workflow tracking."""
        return f"step_{step_number:03d}"
