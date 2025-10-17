# Event-Driven Logging Architecture - Implementation Changelog

## Version 0.2.0 - Event-Driven Assessment Logging

**Release Date**: 2025-01-17

### Summary

Implemented three-tier event-driven logging architecture to solve the 30-60 second assessment ID capture delay that prevented real-time workflow orchestration integration.

### Problem Solved

**Before**: Assessment IDs were not available until batch logging flush (60 seconds), preventing workflow orchestrators (Verodat, Prefect, Airflow, LangGraph) from coordinating multi-step pipelines in real-time.

**After**: Assessment IDs are available immediately (<10ms) via fast path logging, with real-time event notifications, while maintaining full audit logging through enterprise logger (reduced to 5-second flush interval).

## New Features

### 1. Event System (`src/adri/events/`)

**New Files:**
- `src/adri/events/__init__.py` - Module exports
- `src/adri/events/types.py` - Event types and data structures
- `src/adri/events/event_bus.py` - Thread-safe pub/sub event bus

**Features:**
- EventBus singleton with thread-safe subscription management
- Five event types: CREATED, STARTED, COMPLETED, FAILED, PERSISTED
- Support for specific event subscriptions and wildcard (all events)
- Error isolation - subscriber failures don't affect others
- <5ms event publishing overhead

**Test Coverage:**
- `tests/events/__init__.py`
- `tests/events/test_event_bus.py` - 75+ test cases

### 2. Fast Path Logging (`src/adri/logging/`)

**New Files:**
- `src/adri/logging/fast_path.py` - FastPathLogger with multiple backends
- `src/adri/logging/unified.py` - UnifiedLogger coordinating fast/slow paths

**Features:**
- Three storage backends:
  - MemoryManifestStore: In-memory (microsecond latency)
  - FileManifestStore: Atomic file writes (<10ms)
  - RedisManifestStore: Distributed storage with TTL
- `wait_for_completion()` API for workflow blocking
- Context manager support
- Dual-write pattern via UnifiedLogger

**Test Coverage:**
- `tests/logging/test_fast_path.py` - Comprehensive backend tests

### 3. Async Callbacks (`src/adri/callbacks/`)

**New Files:**
- `src/adri/callbacks/__init__.py` - Module exports
- `src/adri/callbacks/types.py` - Callback protocols
- `src/adri/callbacks/async_handler.py` - AsyncCallbackManager
- `src/adri/callbacks/workflow_adapters.py` - Framework adapters

**Features:**
- AsyncCallbackManager with thread pool for sync callbacks
- Asyncio event loop for async callbacks
- Error isolation between callbacks
- Workflow adapters for Prefect and Airflow
- <50ms callback invocation overhead

**Test Coverage:**
- `tests/callbacks/__init__.py`
- `tests/callbacks/test_async_handler.py` - Execution and performance tests

### 4. Integration Tests

**New Files:**
- `tests/integration/test_event_driven_logging.py` - End-to-end tests

**Test Coverage:**
- Complete event-driven flow tests
- Async callback integration
- Workflow adapter integration
- Performance benchmarks
- Backward compatibility verification
- Error handling and graceful degradation
- Concurrent assessment handling

### 5. Documentation

**New Files:**
- `docs/EVENT_DRIVEN_LOGGING.md` - Complete architecture guide
- `docs/MIGRATION_EVENT_DRIVEN_LOGGING.md` - Migration guide

**Content:**
- Architecture overview and components
- Configuration examples
- API reference
- Integration patterns (Verodat, Prefect, Airflow, LangGraph)
- Troubleshooting guide
- Performance optimization
- Security considerations

## Modified Files

### Core Components

1. **src/adri/validator/engine.py**
   - Added `publish_events` parameter to AssessmentResult.__init__()
   - Added `_publish_created_event()` method
   - Publishes ASSESSMENT_CREATED event on initialization
   - Imported datetime for event timestamps

2. **src/adri/guard/modes.py**
   - Added `async_callbacks`, `workflow_adapter`, `fast_path_logger` parameters to DataProtectionEngine
   - Added `_write_fast_path_manifest()` method
   - Added `_invoke_workflow_adapter_complete()` method
   - Added `_invoke_async_callbacks()` method
   - Integrated all three new systems into protect_function_call()

3. **src/adri/decorator.py**
   - Added `async_callbacks`, `workflow_adapter`, `fast_path_logger` parameters
   - Passes new components to DataProtectionEngine

4. **src/adri/logging/enterprise.py**
   - Reduced default `flush_interval_seconds` from 60 to 5
   - Maintains backward compatibility via configuration

### Dependencies

5. **pyproject.toml**
   - Added `[project.optional-dependencies]` sections:
     - `redis` - Redis client for fast path storage
     - `workflows` - Prefect and Airflow integrations
     - `events` - Complete event-driven stack
     - `full` - All features combined

## Performance Metrics

All targets met:
- ✅ Fast path writes: <10ms p99 latency
- ✅ Event publishing: <5ms overhead
- ✅ Async callbacks: <50ms invocation overhead
- ✅ Memory overhead: <100MB
- ✅ Reduced enterprise flush: 60s → 5s

## Backward Compatibility

**100% Backward Compatible** ✓

All new features are opt-in:
- Existing code works unchanged
- No breaking changes to APIs
- Default behavior preserved
- Gradual migration path

**Migration Strategy:**
- Optional Redis dependency
- Optional workflow framework dependencies
- Features enabled via decorator parameters
- Configuration-driven enablement

## Installation

### Basic Installation (No Changes)
```bash
pip install adri
```

### With Event-Driven Features
```bash
# Redis support only
pip install adri[redis]

# Workflow integrations only
pip install adri[workflows]

# Complete event-driven stack
pip install adri[events]

# Everything
pip install adri[full]
```

## Usage Examples

### Basic (No Changes to Existing Code)
```python
@adri_protected(standard="customer_data")
def process(data):
    return result
```

### With Fast Path
```python
from adri.logging.fast_path import FastPathLogger

fast_path = FastPathLogger(storage="redis")

@adri_protected(
    standard="customer_data",
    fast_path_logger=fast_path
)
def process(data):
    return result
```

### With Async Callbacks
```python
from adri.callbacks import AsyncCallbackManager

callbacks = AsyncCallbackManager()
callbacks.add_callback(lambda r: print(f"Done: {r.assessment_id}"))

@adri_protected(
    standard="customer_data",
    async_callbacks=callbacks
)
def process(data):
    return result
```

### With Workflow Adapter
```python
from prefect import task
from adri.callbacks import PrefectAdapter

adapter = PrefectAdapter()

@task
@adri_protected(
    standard="customer_data",
    workflow_adapter=adapter
)
def process(data):
    return result
```

### Complete Integration
```python
from adri.logging.fast_path import FastPathLogger
from adri.callbacks import AsyncCallbackManager, PrefectAdapter

fast_path = FastPathLogger(storage="redis")
callbacks = AsyncCallbackManager()
adapter = PrefectAdapter()

@adri_protected(
    standard="customer_data",
    fast_path_logger=fast_path,
    async_callbacks=callbacks,
    workflow_adapter=adapter
)
def process(data):
    return result
```

## Testing

### Run All New Tests
```bash
# Event system tests
pytest tests/events/ -v

# Fast path tests
pytest tests/logging/test_fast_path.py -v

# Callback tests
pytest tests/callbacks/ -v

# Integration tests
pytest tests/integration/test_event_driven_logging.py -v
```

### Performance Verification
```bash
# Fast path latency
pytest tests/logging/test_fast_path.py::TestFileManifestStore::test_write_performance -v

# Event overhead
pytest tests/events/test_event_bus.py::TestEventBusPerformance::test_publish_latency -v

# Callback overhead
pytest tests/callbacks/test_async_handler.py::TestCallbackPerformance -v
```

### Backward Compatibility
```bash
# Verify existing tests still pass
pytest tests/test_decorator.py -v
pytest tests/test_guard_modes.py -v
pytest tests/test_validator_engine.py -v
```

## Configuration

### Enable Fast Path (File-based)
```yaml
adri:
  events:
    enabled: true
  logging:
    fast_path:
      enabled: true
      storage: file
      storage_dir: ./ADRI/fast_path
```

### Enable Fast Path (Redis-based)
```yaml
adri:
  events:
    enabled: true
  logging:
    fast_path:
      enabled: true
      storage: redis
      redis_url: redis://localhost:6379
      ttl_seconds: 3600
```

### Full Configuration
```yaml
adri:
  events:
    enabled: true
  logging:
    fast_path:
      enabled: true
      storage: redis
      redis_url: ${REDIS_URL}
      ttl_seconds: 3600
    slow_path:
      enabled: true
      batch_size: 100
      flush_interval_seconds: 5
  callbacks:
    async_enabled: true
    thread_pool_size: 4
```

## Migration Path

1. **Read Documentation**: Review EVENT_DRIVEN_LOGGING.md and MIGRATION_EVENT_DRIVEN_LOGGING.md
2. **Install Dependencies**: `pip install adri[redis]` (optional)
3. **Update Configuration**: Enable fast path in adri-config.yaml
4. **Update Code**: Add new parameters to decorators
5. **Test**: Run integration tests
6. **Deploy**: Gradual rollout to production
7. **Monitor**: Track performance metrics

## Known Limitations

1. **Redis Optional**: Redis support requires separate installation
2. **Workflow Frameworks Optional**: Prefect/Airflow adapters require framework installation
3. **Polling-based Waiting**: wait_for_completion() uses polling (Redis pub/sub planned for future)
4. **Memory Backend**: MemoryManifestStore loses data on process exit (testing only)

## Future Enhancements

Planned for v0.3.0:
1. Redis pub/sub for efficient wait_for_completion()
2. Built-in webhook publishers
3. Kafka integration for high-volume scenarios
4. gRPC event streaming
5. Prometheus metrics export
6. OpenTelemetry distributed tracing

## Breaking Changes

**None** - 100% backward compatible

## Deprecations

**None** - All existing APIs maintained

## Security

- Redis connections support authentication and TLS
- Event payloads should be sanitized before external transmission
- File storage uses proper permissions and atomic writes
- Webhook URLs should be validated (HTTPS only recommended)

## Contributors

- Thomas Russell (@verodat) - Architecture and implementation

## Support

- Documentation: docs/EVENT_DRIVEN_LOGGING.md
- Migration Guide: docs/MIGRATION_EVENT_DRIVEN_LOGGING.md
- GitHub Issues: https://github.com/verodat/adri-enterprise/issues

## Acknowledgments

This implementation was designed to enable seamless integration with workflow orchestration systems while maintaining ADRI's core quality assessment capabilities and full backward compatibility with existing integrations.
