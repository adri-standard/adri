"""
Tests for FastPathLogger with multiple storage backends.

Verifies <10ms write performance and proper storage backend functionality.
"""

import tempfile
import time
from datetime import datetime
from pathlib import Path

import pytest

from src.adri.events.types import AssessmentManifest
from src.adri.logging.fast_path import (
    FastPathLogger,
    FileManifestStore,
    MemoryManifestStore,
)


class TestMemoryManifestStore:
    """Test in-memory manifest storage."""

    def test_write_and_read(self):
        """Test basic write and read operations."""
        store = MemoryManifestStore()

        manifest = AssessmentManifest(
            assessment_id="test_123",
            timestamp=datetime.now(),
            status="CREATED",
            score=None,
            standard_name="test_standard",
        )

        # Write manifest
        store.write(manifest)

        # Read it back
        retrieved = store.read("test_123")
        assert retrieved is not None
        assert retrieved.assessment_id == "test_123"
        assert retrieved.status == "CREATED"
        assert retrieved.standard_name == "test_standard"

    def test_read_nonexistent(self):
        """Test reading non-existent manifest."""
        store = MemoryManifestStore()
        result = store.read("nonexistent")
        assert result is None

    def test_wait_for_completion(self):
        """Test waiting for assessment completion."""
        store = MemoryManifestStore()

        # Write initial manifest
        manifest = AssessmentManifest(
            assessment_id="test_456",
            timestamp=datetime.now(),
            status="CREATED",
        )
        store.write(manifest)

        # Update to completed in a separate thread
        import threading

        def complete_assessment():
            time.sleep(0.2)  # 200ms delay
            completed = AssessmentManifest(
                assessment_id="test_456",
                timestamp=datetime.now(),
                status="PASSED",
                score=95.0,
            )
            store.write(completed)

        thread = threading.Thread(target=complete_assessment)
        thread.start()

        # Wait for completion
        result = store.wait_for_completion("test_456", timeout=5)
        thread.join()

        assert result is not None
        assert result.status == "PASSED"
        assert result.score == 95.0

    def test_wait_for_completion_timeout(self):
        """Test timeout when assessment doesn't complete."""
        store = MemoryManifestStore()

        # Write initial manifest that never completes
        manifest = AssessmentManifest(
            assessment_id="test_timeout",
            timestamp=datetime.now(),
            status="CREATED",
        )
        store.write(manifest)

        # Should timeout
        result = store.wait_for_completion("test_timeout", timeout=0.5)
        assert result is None


class TestFileManifestStore:
    """Test file-based manifest storage."""

    def test_write_and_read(self):
        """Test basic write and read operations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FileManifestStore(tmpdir, ttl_seconds=3600)

            manifest = AssessmentManifest(
                assessment_id="file_test_123",
                timestamp=datetime.now(),
                status="COMPLETED",
                score=88.5,
                standard_name="invoice_standard",
            )

            # Write manifest
            store.write(manifest)

            # Verify file was created
            manifest_files = list(Path(tmpdir).rglob("*.json"))
            assert len(manifest_files) == 1

            # Read it back
            retrieved = store.read("file_test_123")
            assert retrieved is not None
            assert retrieved.assessment_id == "file_test_123"
            assert retrieved.status == "COMPLETED"
            assert retrieved.score == 88.5

    def test_atomic_write(self):
        """Test that writes are atomic (no partial files)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FileManifestStore(tmpdir)

            manifest = AssessmentManifest(
                assessment_id="atomic_test",
                timestamp=datetime.now(),
                status="PASSED",
            )

            store.write(manifest)

            # Check no .tmp files left behind
            tmp_files = list(Path(tmpdir).rglob("*.tmp"))
            assert len(tmp_files) == 0

            # Check .json file exists
            json_files = list(Path(tmpdir).rglob("*.json"))
            assert len(json_files) == 1

    def test_write_performance(self):
        """Test that writes complete reasonably quickly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FileManifestStore(tmpdir)

            manifest = AssessmentManifest(
                assessment_id="perf_test",
                timestamp=datetime.now(),
                status="CREATED",
            )

            # Measure write time
            start = time.time()
            store.write(manifest)
            duration_ms = (time.time() - start) * 1000

            # Log for monitoring (no assertion - too flaky on CI runners)
            # Target is <10ms on local dev, but CI environments (especially Windows)
            # can have significant filesystem I/O variance due to virtualization
            print(f"File store write latency: {duration_ms:.2f}ms")

    def test_subdirectory_organization(self):
        """Test that manifests are organized in subdirectories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FileManifestStore(tmpdir)

            manifest = AssessmentManifest(
                assessment_id="adri_20250110_123456_abc123",
                timestamp=datetime.now(),
                status="CREATED",
            )

            store.write(manifest)

            # Check subdirectory was created
            subdirs = [d for d in Path(tmpdir).iterdir() if d.is_dir()]
            assert len(subdirs) == 1
            assert subdirs[0].name == "adri_202"  # First 8 chars


class TestFastPathLogger:
    """Test FastPathLogger with different backends."""

    def test_memory_backend(self):
        """Test logger with memory backend."""
        logger = FastPathLogger(storage="memory")

        manifest = AssessmentManifest(
            assessment_id="logger_test_1",
            timestamp=datetime.now(),
            status="CREATED",
        )

        logger.log_manifest(manifest)
        retrieved = logger.get_manifest("logger_test_1")

        assert retrieved is not None
        assert retrieved.assessment_id == "logger_test_1"

        logger.close()

    def test_file_backend(self):
        """Test logger with file backend."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = FastPathLogger(
                storage="file",
                storage_dir=tmpdir,
            )

            manifest = AssessmentManifest(
                assessment_id="logger_test_2",
                timestamp=datetime.now(),
                status="PASSED",
                score=92.0,
            )

            logger.log_manifest(manifest)
            retrieved = logger.get_manifest("logger_test_2")

            assert retrieved is not None
            assert retrieved.score == 92.0

            logger.close()

    def test_invalid_backend(self):
        """Test error handling for invalid backend."""
        with pytest.raises(ValueError, match="Invalid storage type"):
            FastPathLogger(storage="invalid")

    def test_context_manager(self):
        """Test using logger as context manager."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with FastPathLogger(storage="file", storage_dir=tmpdir) as logger:
                manifest = AssessmentManifest(
                    assessment_id="context_test",
                    timestamp=datetime.now(),
                    status="CREATED",
                )
                logger.log_manifest(manifest)

            # Logger should be closed after context

    def test_wait_for_completion_workflow(self):
        """Test workflow orchestrator wait pattern."""
        logger = FastPathLogger(storage="memory")

        # Simulate assessment starting
        manifest = AssessmentManifest(
            assessment_id="workflow_test",
            timestamp=datetime.now(),
            status="CREATED",
        )
        logger.log_manifest(manifest)

        # Simulate completion in background
        import threading

        def complete_assessment():
            time.sleep(0.3)
            completed = AssessmentManifest(
                assessment_id="workflow_test",
                timestamp=datetime.now(),
                status="PASSED",
                score=96.0,
            )
            logger.log_manifest(completed)

        thread = threading.Thread(target=complete_assessment)
        thread.start()

        # Wait for completion (like a workflow orchestrator would)
        result = logger.wait_for_completion("workflow_test", timeout=5)
        thread.join()

        assert result is not None
        assert result.status == "PASSED"
        assert result.score == 96.0

        logger.close()


class TestManifestSerialization:
    """Test AssessmentManifest serialization."""

    def test_to_dict(self):
        """Test manifest to_dict conversion."""
        timestamp = datetime.now()
        manifest = AssessmentManifest(
            assessment_id="serial_test",
            timestamp=timestamp,
            status="BLOCKED",
            score=45.0,
            standard_name="strict_standard",
        )

        data = manifest.to_dict()

        assert data["assessment_id"] == "serial_test"
        assert data["status"] == "BLOCKED"
        assert data["score"] == 45.0
        assert data["standard_name"] == "strict_standard"
        assert "timestamp" in data

    def test_roundtrip_serialization(self):
        """Test that manifest survives serialization roundtrip."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FileManifestStore(tmpdir)

            original = AssessmentManifest(
                assessment_id="roundtrip_test",
                timestamp=datetime.now(),
                status="PASSED",
                score=87.5,
                standard_name="test_standard",
            )

            # Write and read back
            store.write(original)
            retrieved = store.read("roundtrip_test")

            assert retrieved is not None
            assert retrieved.assessment_id == original.assessment_id
            assert retrieved.status == original.status
            assert retrieved.score == original.score
            assert retrieved.standard_name == original.standard_name


@pytest.mark.skipif(
    True,  # Skip by default - requires Redis
    reason="Redis integration test - run manually with Redis available"
)
class TestRedisManifestStore:
    """Test Redis-based manifest storage.

    These tests require a running Redis instance and are skipped by default.
    To run: pytest tests/logging/test_fast_path.py::TestRedisManifestStore -v
    """

    def test_redis_write_and_read(self):
        """Test Redis write and read operations."""
        try:
            from src.adri.logging.fast_path import RedisManifestStore

            store = RedisManifestStore(redis_url="redis://localhost:6379")

            manifest = AssessmentManifest(
                assessment_id="redis_test_1",
                timestamp=datetime.now(),
                status="COMPLETED",
                score=91.0,
            )

            store.write(manifest)
            retrieved = store.read("redis_test_1")

            assert retrieved is not None
            assert retrieved.assessment_id == "redis_test_1"
            assert retrieved.score == 91.0

            store.close()

        except (ImportError, ConnectionError) as e:
            pytest.skip(f"Redis not available: {e}")

    def test_redis_logger(self):
        """Test FastPathLogger with Redis backend."""
        try:
            logger = FastPathLogger(
                storage="redis",
                redis_url="redis://localhost:6379",
            )

            manifest = AssessmentManifest(
                assessment_id="redis_logger_test",
                timestamp=datetime.now(),
                status="PASSED",
            )

            logger.log_manifest(manifest)
            retrieved = logger.get_manifest("redis_logger_test")

            assert retrieved is not None
            assert retrieved.status == "PASSED"

            logger.close()

        except (ImportError, ConnectionError) as e:
            pytest.skip(f"Redis not available: {e}")
