"""
ADRI Reasoning Logger - CSV-based Logging for AI/LLM Reasoning Steps.

Captures comprehensive audit logs for AI reasoning prompts and responses
in structured CSV format with relational linking to main assessments.
"""

import csv
import hashlib
import os
import threading
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass
class LLMConfig:
    """Configuration for LLM operations."""

    model: str
    temperature: float = 0.1
    seed: Optional[int] = None
    max_tokens: Optional[int] = 4000

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "model": self.model,
            "temperature": self.temperature,
            "seed": self.seed,
            "max_tokens": self.max_tokens,
        }


@dataclass
class ReasoningPrompt:
    """Represents an AI reasoning prompt with configuration."""

    prompt_id: str
    assessment_id: str
    run_id: str
    step_id: str
    prompt_hash: str
    model: str
    temperature: float
    seed: Optional[int]
    max_tokens: Optional[int]
    system_prompt: str
    user_prompt: str
    timestamp: str  # ISO format string
    execution_id: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for CSV writing."""
        return {
            "prompt_id": self.prompt_id,
            "assessment_id": self.assessment_id,
            "run_id": self.run_id,
            "step_id": self.step_id,
            "prompt_hash": self.prompt_hash,
            "model": self.model,
            "temperature": self.temperature,
            "seed": self.seed if self.seed is not None else "",
            "max_tokens": self.max_tokens if self.max_tokens is not None else "",
            "system_prompt": self.system_prompt,
            "user_prompt": self.user_prompt,
            "timestamp": self.timestamp,
            "execution_id": self.execution_id,
        }


@dataclass
class ReasoningResponse:
    """Represents an AI reasoning response with metrics."""

    response_id: str
    assessment_id: str
    prompt_id: str
    response_hash: str
    response_text: str
    processing_time_ms: int
    token_count: Optional[int]
    timestamp: str  # ISO format string
    execution_id: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for CSV writing."""
        return {
            "response_id": self.response_id,
            "assessment_id": self.assessment_id,
            "prompt_id": self.prompt_id,
            "response_hash": self.response_hash,
            "response_text": self.response_text,
            "processing_time_ms": self.processing_time_ms,
            "token_count": self.token_count if self.token_count is not None else "",
            "timestamp": self.timestamp,
            "execution_id": self.execution_id,
        }


class ReasoningLogger:
    """CSV-based logger for AI reasoning prompts and responses."""

    # Define CSV headers for reasoning datasets
    PROMPT_LOG_HEADERS = [
        "prompt_id",
        "assessment_id",
        "run_id",
        "step_id",
        "prompt_hash",
        "model",
        "temperature",
        "seed",
        "max_tokens",
        "system_prompt",
        "user_prompt",
        "timestamp",
        "execution_id",
    ]

    RESPONSE_LOG_HEADERS = [
        "response_id",
        "assessment_id",
        "prompt_id",
        "response_hash",
        "response_text",
        "processing_time_ms",
        "token_count",
        "timestamp",
        "execution_id",
    ]

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the reasoning logger with configuration.

        Args:
            config: Configuration dictionary with keys:
                - enabled: Whether reasoning logging is enabled
                - log_dir: Directory for log files
                - log_prefix: Prefix for log files (default: 'adri')
                - max_log_size_mb: Maximum log file size before rotation
        """
        config = config or {}

        self.enabled = config.get("enabled", False)
        log_path = config.get("log_dir") or config.get("log_location", "./logs")
        # Extract directory from log_location if it includes filename
        if "/" in str(log_path) and str(log_path).endswith((".jsonl", ".log", ".csv")):
            log_path = str(Path(log_path).parent)
        self.log_dir = Path(log_path)
        self.log_prefix = config.get("log_prefix", "adri")
        self.max_log_size_mb = config.get("max_log_size_mb", 100)

        # File paths for reasoning CSV files
        self.prompts_log_path = (
            self.log_dir / f"{self.log_prefix}_reasoning_prompts.csv"
        )
        self.responses_log_path = (
            self.log_dir / f"{self.log_prefix}_reasoning_responses.csv"
        )

        # Thread safety
        self._lock = threading.Lock()

        # Initialize CSV files if enabled
        if self.enabled:
            self._initialize_csv_files()

    def _initialize_csv_files(self) -> None:
        """Initialize reasoning CSV files with headers if they don't exist."""
        with self._lock:
            # Ensure log directory exists
            self.log_dir.mkdir(parents=True, exist_ok=True)

            # Initialize prompts log file
            if not self.prompts_log_path.exists():
                with open(
                    self.prompts_log_path, "w", newline="", encoding="utf-8"
                ) as f:
                    writer = csv.DictWriter(f, fieldnames=self.PROMPT_LOG_HEADERS)
                    writer.writeheader()

            # Initialize responses log file
            if not self.responses_log_path.exists():
                with open(
                    self.responses_log_path, "w", newline="", encoding="utf-8"
                ) as f:
                    writer = csv.DictWriter(f, fieldnames=self.RESPONSE_LOG_HEADERS)
                    writer.writeheader()

    def _generate_prompt_hash(self, system_prompt: str, user_prompt: str) -> str:
        """Generate hash for a prompt."""
        combined = f"{system_prompt}|{user_prompt}"
        return hashlib.sha256(combined.encode("utf-8")).hexdigest()[:16]

    def _generate_response_hash(self, response_text: str) -> str:
        """Generate hash for a response."""
        return hashlib.sha256(response_text.encode("utf-8")).hexdigest()[:16]

    def _generate_prompt_id(self) -> str:
        """Generate unique prompt ID."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"prompt_{timestamp}_{os.urandom(3).hex()}"

    def _generate_response_id(self) -> str:
        """Generate unique response ID."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"response_{timestamp}_{os.urandom(3).hex()}"

    def log_prompt(
        self,
        assessment_id: str,
        run_id: str,
        step_id: str,
        system_prompt: str,
        user_prompt: str,
        llm_config: LLMConfig,
        execution_id: Optional[str] = None,
    ) -> str:
        """
        Log reasoning prompt to CSV and return prompt_id.

        Args:
            assessment_id: Associated assessment ID
            run_id: Current run identifier
            step_id: Step identifier in workflow
            system_prompt: System/instruction prompt
            user_prompt: User/context prompt
            llm_config: LLM configuration
            execution_id: Optional workflow execution ID for linking

        Returns:
            prompt_id for referencing this prompt
        """
        if not self.enabled:
            return ""

        # Generate IDs and hashes
        prompt_id = self._generate_prompt_id()
        prompt_hash = self._generate_prompt_hash(system_prompt, user_prompt)
        timestamp = datetime.now().isoformat()

        # Create prompt record
        prompt = ReasoningPrompt(
            prompt_id=prompt_id,
            assessment_id=assessment_id,
            run_id=run_id,
            step_id=step_id,
            prompt_hash=prompt_hash,
            model=llm_config.model,
            temperature=llm_config.temperature,
            seed=llm_config.seed,
            max_tokens=llm_config.max_tokens,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            timestamp=timestamp,
            execution_id=execution_id or "",
        )

        # Write to CSV
        self._write_prompt_to_csv(prompt)

        return prompt_id

    def log_response(
        self,
        assessment_id: str,
        prompt_id: str,
        response_text: str,
        processing_time_ms: int,
        token_count: Optional[int] = None,
        execution_id: Optional[str] = None,
    ) -> str:
        """
        Log reasoning response to CSV and return response_id.

        Args:
            assessment_id: Associated assessment ID
            prompt_id: Reference to prompt that generated this response
            response_text: AI-generated response
            processing_time_ms: Processing time in milliseconds
            token_count: Number of tokens in response
            execution_id: Optional workflow execution ID for linking

        Returns:
            response_id for referencing this response
        """
        if not self.enabled:
            return ""

        # Generate IDs and hashes
        response_id = self._generate_response_id()
        response_hash = self._generate_response_hash(response_text)
        timestamp = datetime.now().isoformat()

        # Create response record
        response = ReasoningResponse(
            response_id=response_id,
            assessment_id=assessment_id,
            prompt_id=prompt_id,
            response_hash=response_hash,
            response_text=response_text,
            processing_time_ms=processing_time_ms,
            token_count=token_count,
            timestamp=timestamp,
            execution_id=execution_id or "",
        )

        # Write to CSV
        self._write_response_to_csv(response)

        return response_id

    def _write_prompt_to_csv(self, prompt: ReasoningPrompt) -> None:
        """Write prompt record to CSV file."""
        with self._lock:
            # Check for file rotation
            self._check_rotation(self.prompts_log_path, self.PROMPT_LOG_HEADERS)

            # Write prompt record
            with open(self.prompts_log_path, "a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=self.PROMPT_LOG_HEADERS)
                writer.writerow(prompt.to_dict())

    def _write_response_to_csv(self, response: ReasoningResponse) -> None:
        """Write response record to CSV file."""
        with self._lock:
            # Check for file rotation
            self._check_rotation(self.responses_log_path, self.RESPONSE_LOG_HEADERS)

            # Write response record
            with open(self.responses_log_path, "a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=self.RESPONSE_LOG_HEADERS)
                writer.writerow(response.to_dict())

    def _check_rotation(self, file_path: Path, headers: list) -> None:
        """Check if log file needs rotation."""
        import time

        if not file_path.exists():
            return

        # Get file size in MB
        file_size_mb = file_path.stat().st_size / (1024 * 1024)

        if file_size_mb >= self.max_log_size_mb:
            # Rotate log file with Windows-safe handling
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            rotated_path = file_path.with_suffix(f".{timestamp}.csv")

            # Windows-safe file rotation
            try:
                # Ensure unique filename to avoid conflicts
                counter = 0
                original_rotated_path = rotated_path
                while rotated_path.exists():
                    counter += 1
                    rotated_path = original_rotated_path.with_suffix(
                        f".{timestamp}_{counter:03d}.csv"
                    )

                # Small delay to ensure file handles are released on Windows
                time.sleep(0.01)
                file_path.rename(rotated_path)
            except (OSError, PermissionError):
                # If rotation fails on Windows, continue without rotating
                return

            # Recreate file with headers
            try:
                with open(file_path, "w", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=headers)
                    writer.writeheader()
            except (OSError, PermissionError):
                # If recreation fails, file will be recreated on next write
                pass

    def get_log_files(self) -> Dict[str, Path]:
        """Get the paths to the current reasoning log files."""
        return {
            "reasoning_prompts": self.prompts_log_path,
            "reasoning_responses": self.responses_log_path,
        }

    def clear_logs(self) -> None:
        """Clear all reasoning log files (useful for testing)."""
        if not self.enabled:
            return

        with self._lock:
            for file_path in [self.prompts_log_path, self.responses_log_path]:
                if file_path.exists():
                    file_path.unlink()

            # Reinitialize with headers (inline to avoid deadlock)
            self.log_dir.mkdir(parents=True, exist_ok=True)

            # Initialize prompts log file
            with open(self.prompts_log_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=self.PROMPT_LOG_HEADERS)
                writer.writeheader()

            # Initialize responses log file
            with open(self.responses_log_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=self.RESPONSE_LOG_HEADERS)
                writer.writeheader()
