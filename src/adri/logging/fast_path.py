"""
Fast path logging for immediate assessment ID capture.

Provides <10ms latency writes to enable workflow orchestrators to access
assessment IDs without waiting for batch logging flush intervals.
"""

import json
import logging
import os
import time
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from ..events.types import AssessmentManifest

logger = logging.getLogger(__name__)


class ManifestStore(ABC):
    """Abstract base class for manifest storage backends."""

    @abstractmethod
    def write(self, manifest: AssessmentManifest) -> None:
        """Write manifest immediately with <10ms target latency.

        Args:
            manifest: Assessment manifest to write

        Raises:
            StorageError: If write fails
        """
        pass

    @abstractmethod
    def read(self, assessment_id: str) -> Optional[AssessmentManifest]:
        """Read manifest by assessment ID.

        Args:
            assessment_id: ID to look up

        Returns:
            AssessmentManifest if found, None otherwise
        """
        pass

    @abstractmethod
    def wait_for_completion(
        self, assessment_id: str, timeout: int = 30
    ) -> Optional[AssessmentManifest]:
        """Block until assessment completes or timeout.

        Args:
            assessment_id: ID to wait for
            timeout: Maximum seconds to wait

        Returns:
            AssessmentManifest when completed, None on timeout
        """
        pass

    @abstractmethod
    def close(self) -> None:
        """Clean up resources."""
        pass


class MemoryManifestStore(ManifestStore):
    """In-memory manifest storage for testing and development.

    This is the simplest backend with no external dependencies.
    Data is lost when process exits.
    """

    def __init__(self):
        """Initialize empty in-memory storage."""
        self._manifests: Dict[str, AssessmentManifest] = {}

    def write(self, manifest: AssessmentManifest) -> None:
        """Write manifest to memory (microsecond latency)."""
        self._manifests[manifest.assessment_id] = manifest
        logger.debug(f"Wrote manifest to memory: {manifest.assessment_id}")

    def read(self, assessment_id: str) -> Optional[AssessmentManifest]:
        """Read manifest from memory."""
        return self._manifests.get(assessment_id)

    def wait_for_completion(
        self, assessment_id: str, timeout: int = 30
    ) -> Optional[AssessmentManifest]:
        """Poll memory until manifest shows completion."""
        start_time = time.time()
        poll_interval = 0.1  # 100ms

        while (time.time() - start_time) < timeout:
            manifest = self.read(assessment_id)
            if manifest and manifest.status in ["PASSED", "BLOCKED", "ERROR"]:
                return manifest
            time.sleep(poll_interval)

        return None

    def close(self) -> None:
        """No-op for memory store."""
        pass


class FileManifestStore(ManifestStore):
    """File-based manifest storage with atomic writes.

    Uses filesystem for persistent storage with atomic renames
    to ensure durability. Good for single-machine deployments.
    """

    def __init__(self, storage_dir: str, ttl_seconds: int = 3600):
        """Initialize file storage.

        Args:
            storage_dir: Directory to store manifest files
            ttl_seconds: How long to keep manifests before cleanup
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.ttl_seconds = ttl_seconds
        logger.info(f"Initialized FileManifestStore at {self.storage_dir}")

    def _get_manifest_path(self, assessment_id: str) -> Path:
        """Get path for manifest file."""
        # Use subdirectories for better filesystem performance
        prefix = assessment_id[:8] if len(assessment_id) >= 8 else assessment_id
        subdir = self.storage_dir / prefix
        subdir.mkdir(exist_ok=True)
        return subdir / f"{assessment_id}.json"

    def write(self, manifest: AssessmentManifest) -> None:
        """Write manifest to file with atomic rename."""
        start_time = time.time()

        manifest_path = self._get_manifest_path(manifest.assessment_id)
        temp_path = manifest_path.with_suffix(".tmp")

        try:
            # Write to temp file first
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(manifest.to_dict(), f)
                f.flush()
                os.fsync(f.fileno())  # Ensure data is on disk

            # Atomic rename
            temp_path.replace(manifest_path)

            latency_ms = (time.time() - start_time) * 1000
            logger.debug(
                f"Wrote manifest to file in {latency_ms:.2f}ms: "
                f"{manifest.assessment_id}"
            )

            # Warn if we exceeded target latency
            if latency_ms > 10.0:
                logger.warning(
                    f"Fast path write exceeded 10ms target: {latency_ms:.2f}ms"
                )

        except Exception as e:
            logger.error(f"Failed to write manifest to file: {e}")
            if temp_path.exists():
                temp_path.unlink()
            raise

    def read(self, assessment_id: str) -> Optional[AssessmentManifest]:
        """Read manifest from file."""
        manifest_path = self._get_manifest_path(assessment_id)

        if not manifest_path.exists():
            return None

        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return AssessmentManifest(
                    assessment_id=data["assessment_id"],
                    timestamp=datetime.fromisoformat(data["timestamp"]),
                    status=data["status"],
                    score=data.get("score"),
                    standard_name=data.get("standard_name"),
                )
        except Exception as e:
            logger.error(f"Failed to read manifest from file: {e}")
            return None

    def wait_for_completion(
        self, assessment_id: str, timeout: int = 30
    ) -> Optional[AssessmentManifest]:
        """Poll file system until manifest shows completion."""
        start_time = time.time()
        poll_interval = 0.1  # 100ms

        while (time.time() - start_time) < timeout:
            manifest = self.read(assessment_id)
            if manifest and manifest.status in ["PASSED", "BLOCKED", "ERROR"]:
                return manifest
            time.sleep(poll_interval)

        return None

    def close(self) -> None:
        """No cleanup needed for file store."""
        pass


class RedisManifestStore(ManifestStore):
    """Redis-based manifest storage for distributed deployments.

    Uses Redis for fast, distributed storage with automatic TTL.
    Ideal for multi-machine deployments and workflow orchestrators.
    """

    def __init__(
        self, redis_url: str = "redis://localhost:6379", ttl_seconds: int = 3600
    ):
        """Initialize Redis storage.

        Args:
            redis_url: Redis connection URL
            ttl_seconds: TTL for manifest keys

        Raises:
            ImportError: If redis package not installed
            ConnectionError: If cannot connect to Redis
        """
        try:
            import redis
        except ImportError:
            raise ImportError(
                "redis package required for RedisManifestStore. "
                "Install with: pip install redis>=5.0.0"
            )

        self.redis_url = redis_url
        self.ttl_seconds = ttl_seconds

        try:
            self.client = redis.from_url(redis_url, decode_responses=True)
            # Test connection
            self.client.ping()
            logger.info(f"Connected to Redis at {redis_url}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise ConnectionError(f"Cannot connect to Redis: {e}")

    def _get_key(self, assessment_id: str) -> str:
        """Get Redis key for assessment ID."""
        return f"adri:manifest:{assessment_id}"

    def write(self, manifest: AssessmentManifest) -> None:
        """Write manifest to Redis with TTL."""
        start_time = time.time()

        try:
            key = self._get_key(manifest.assessment_id)
            data = json.dumps(manifest.to_dict())

            # Write with TTL
            self.client.setex(key, self.ttl_seconds, data)

            latency_ms = (time.time() - start_time) * 1000
            logger.debug(
                f"Wrote manifest to Redis in {latency_ms:.2f}ms: "
                f"{manifest.assessment_id}"
            )

            # Warn if we exceeded target latency
            if latency_ms > 10.0:
                logger.warning(
                    f"Fast path Redis write exceeded 10ms target: {latency_ms:.2f}ms"
                )

        except Exception as e:
            logger.error(f"Failed to write manifest to Redis: {e}")
            raise

    def read(self, assessment_id: str) -> Optional[AssessmentManifest]:
        """Read manifest from Redis."""
        try:
            key = self._get_key(assessment_id)
            data = self.client.get(key)

            if data is None:
                return None

            parsed = json.loads(data)
            return AssessmentManifest(
                assessment_id=parsed["assessment_id"],
                timestamp=datetime.fromisoformat(parsed["timestamp"]),
                status=parsed["status"],
                score=parsed.get("score"),
                standard_name=parsed.get("standard_name"),
            )
        except Exception as e:
            logger.error(f"Failed to read manifest from Redis: {e}")
            return None

    def wait_for_completion(
        self, assessment_id: str, timeout: int = 30
    ) -> Optional[AssessmentManifest]:
        """Use Redis pub/sub for efficient waiting (future enhancement).

        For now, uses polling like other backends. Future enhancement could
        use Redis pub/sub for more efficient blocking wait.
        """
        start_time = time.time()
        poll_interval = 0.1  # 100ms

        while (time.time() - start_time) < timeout:
            manifest = self.read(assessment_id)
            if manifest and manifest.status in ["PASSED", "BLOCKED", "ERROR"]:
                return manifest
            time.sleep(poll_interval)

        return None

    def close(self) -> None:
        """Close Redis connection."""
        try:
            self.client.close()
            logger.debug("Closed Redis connection")
        except Exception as e:
            logger.warning(f"Error closing Redis connection: {e}")


class FastPathLogger:
    """Fast path logger for immediate assessment ID capture.

    Provides <10ms manifest writes to enable workflow orchestrators
    to access assessment IDs without waiting for batch logging.

    Usage:
        # In-memory (testing)
        logger = FastPathLogger(storage="memory")

        # File-based (single machine)
        logger = FastPathLogger(
            storage="file",
            storage_dir="./ADRI/fast_path"
        )

        # Redis (distributed)
        logger = FastPathLogger(
            storage="redis",
            redis_url="redis://localhost:6379"
        )

        # Write manifest
        manifest = AssessmentManifest(
            assessment_id="adri_20250110_123456_abc",
            timestamp=datetime.now(),
            status="CREATED"
        )
        logger.log_manifest(manifest)

        # Read manifest
        manifest = logger.get_manifest("adri_20250110_123456_abc")

        # Wait for completion
        manifest = logger.wait_for_completion("adri_20250110_123456_abc", timeout=30)
    """

    def __init__(
        self,
        storage: str = "memory",
        storage_dir: Optional[str] = None,
        redis_url: str = "redis://localhost:6379",
        ttl_seconds: int = 3600,
    ):
        """Initialize fast path logger.

        Args:
            storage: Storage backend ("memory", "file", "redis")
            storage_dir: Directory for file storage (if storage="file")
            redis_url: Redis URL (if storage="redis")
            ttl_seconds: TTL for manifests

        Raises:
            ValueError: If invalid storage type
        """
        self.storage_type = storage

        if storage == "memory":
            self.store = MemoryManifestStore()
        elif storage == "file":
            if storage_dir is None:
                storage_dir = "./ADRI/fast_path"
            self.store = FileManifestStore(storage_dir, ttl_seconds)
        elif storage == "redis":
            self.store = RedisManifestStore(redis_url, ttl_seconds)
        else:
            raise ValueError(
                f"Invalid storage type: {storage}. "
                f"Must be 'memory', 'file', or 'redis'"
            )

        logger.info(f"Initialized FastPathLogger with {storage} storage")

    def log_manifest(self, manifest: AssessmentManifest) -> None:
        """Write manifest immediately with <10ms target latency.

        Args:
            manifest: Assessment manifest to write
        """
        self.store.write(manifest)

    def get_manifest(self, assessment_id: str) -> Optional[AssessmentManifest]:
        """Retrieve manifest by ID.

        Args:
            assessment_id: ID to look up

        Returns:
            AssessmentManifest if found, None otherwise
        """
        return self.store.read(assessment_id)

    def wait_for_completion(
        self, assessment_id: str, timeout: int = 30
    ) -> Optional[AssessmentManifest]:
        """Block until assessment completes or timeout.

        Args:
            assessment_id: ID to wait for
            timeout: Maximum seconds to wait

        Returns:
            AssessmentManifest when completed, None on timeout
        """
        return self.store.wait_for_completion(assessment_id, timeout)

    def close(self) -> None:
        """Clean up resources."""
        self.store.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
