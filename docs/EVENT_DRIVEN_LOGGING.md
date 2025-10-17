# Event-Driven Assessment Logging Architecture

## Overview

ADRI's event-driven logging architecture solves the 30-60 second assessment ID capture delay that previously prevented real-time workflow orchestration integration. This new three-tier architecture provides:

1. **Fast Path**: Immediate (<10ms) assessment ID and status capture
2. **Event System**: Real-time notifications via pub/sub
3. **Slow Path**: Batched full details for analytics and compliance

## Problem Statement

**Before**: Enterprise logging used a 60-second batch flush interval, meaning workflow orchestrators (Verodat, Prefect, Airflow, LangGraph) couldn't access assessment IDs for 30-60 seconds after assessment completion. This broke real-time multi-step pipeline coordination.

**After**: Assessment IDs are now available immediately (<10ms) through fast path logging, while comprehensive audit logs still flow through the batched enterprise logger (reduced to 5-second flush interval).

## Architecture Components

### 1. Event System (`src/adri/events/`)

Thread-safe pub/sub event bus for assessment lifecycle notifications.

**Key Files:**
- `types.py`: EventType enum, AssessmentEvent, AssessmentManifest
- `event_bus.py`: EventBus singleton with thread-safe pub/sub
- `__init__.py`: Module exports

**Event Types:**
- `ASSESSMENT_CREATED`: Published when AssessmentResult is instantiated
- `ASSESSMENT_STARTED`: Published when assessment begins processing
- `ASSESSMENT_COMPLETED`: Published when assessment finishes
- `ASSESSMENT_FAILED`: Published on assessment errors
- `ASSESSMENT_PERSISTED`: Published when logged to persistent storage

**Usage Example:**
```python
from adri.events import get_event_bus, EventType

# Subscribe to events
bus = get_event_bus()

def on_assessment_complete(event):
    print(f"Assessment {event.assessment_id} completed with score {event.payload['score']}")

subscription_id = bus.subscribe(EventType.ASSESSMENT_COMPLETED, on_assessment_complete)

# Events are automatically published during assessments
# Unsubscribe when done
bus.unsubscribe(subscription_id)
```

### 2. Fast Path Logging (`src/adri/logging/fast_path.py`)

Immediate (<10ms) manifest writes for workflow orchestration.

**Storage Backends:**
- **Memory**: In-memory storage (development/testing)
- **File**: File-based with atomic writes (single machine)
- **Redis**: Distributed storage with TTL (production)

**Usage Example:**
```python
from adri.logging.fast_path import FastPathLogger
from adri.events.types import AssessmentManifest
from datetime import datetime

# Initialize logger
logger = FastPathLogger(
    storage="redis",
    redis_url="redis://localhost:6379",
    ttl_seconds=3600
)

# Write manifest
manifest = AssessmentManifest(
    assessment_id="adri_20250110_123456_abc",
    timestamp=datetime.now(),
    status="PASSED",
    score=95.0,
    standard_name="invoice_standard"
)
logger.log_manifest(manifest)

# Read manifest
manifest = logger.get_manifest("adri_20250110_123456_abc")

# Wait for completion (blocking)
manifest = logger.wait_for_completion("adri_20250110_123456_abc", timeout=30)

logger.close()
```

### 3. Async Callbacks (`src/adri/callbacks/`)

Non-blocking callback execution for workflow notifications.

**Key Files:**
- `types.py`: SyncCallback, AsyncCallback protocols
- `async_handler.py`: AsyncCallbackManager
- `workflow_adapters.py`: Framework integrations (Prefect, Airflow)

**Usage Example:**
```python
from adri.callbacks import AsyncCallbackManager
from adri.decorator import adri_protected

# Setup callbacks
manager = AsyncCallbackManager(thread_pool_size=4)

def sync_callback(result):
    print(f"Assessment {result.assessment_id}: {result.overall_score}")

async def async_callback(result):
    async with aiohttp.ClientSession() as session:
        await session.post(
            "https://api.example.com/assessments",
            json={"id": result.assessment_id, "score": result.overall_score}
        )

manager.add_callback(sync_callback)
manager.add_callback(async_callback)

# Use with decorator
@adri_protected(
    standard="customer_data",
    async_callbacks=manager
)
def process_customers(data):
    return analyze(data)

# Callbacks are invoked asynchronously when assessment completes
result = process_customers(customer_data)

manager.close()
```

### 4. Workflow Adapters

Framework-specific integrations for Prefect and Airflow.

**Prefect Example:**
```python
from prefect import task, flow
from adri.callbacks import PrefectAdapter
from adri.decorator import adri_protected

adapter = PrefectAdapter()

@task
@adri_protected(
    standard="invoice_data",
    workflow_adapter=adapter
)
def validate_invoices(data):
    return process(data)

@flow
def invoice_processing_flow():
    data = load_invoices()
    result = validate_invoices(data)  # Logs to Prefect automatically
    return result
```

**Airflow Example:**
```python
from airflow.decorators import task, dag
from adri.callbacks import AirflowAdapter
from adri.decorator import adri_protected

adapter = AirflowAdapter(push_to_xcom=True)

@dag(schedule_interval="@daily")
def customer_data_pipeline():

    @task
    @adri_protected(
        standard="customer_data",
        workflow_adapter=adapter
    )
    def validate_customers(data):
        return process(data)

    data = load_data()
    result = validate_customers(data)  # Pushes to XCom automatically
    return result

pipeline = customer_data_pipeline()
```

### 5. Unified Logger (`src/adri/logging/unified.py`)

Coordinates fast and slow path logging with dual-write pattern.

**Usage Example:**
```python
from adri.logging.unified import UnifiedLogger
from adri.logging.local import CSVAuditLogger

# Setup slow path (existing logger)
slow_path = CSVAuditLogger({"log_dir": "./ADRI/audit-logs"})

# Create unified logger
unified = UnifiedLogger(
    fast_path_enabled=True,
    fast_path_storage="redis",
    fast_path_config={
        "redis_url": "redis://localhost:6379",
        "ttl_seconds": 3600
    },
    slow_path_logger=slow_path
)

# Log assessment (dual write)
unified.log_assessment(
    assessment_result=result,
    execution_context=context,
    data_info=info,
    performance_metrics=metrics
)

# Fast path read
manifest = unified.get_manifest(assessment_id)

# Wait for completion
manifest = unified.wait_for_completion(assessment_id, timeout=30)

unified.close()
```

## Configuration

Add to `adri-config.yaml`:

```yaml
adri:
  # Event system configuration
  events:
    enabled: true

  # Fast path logging configuration
  logging:
    fast_path:
      enabled: true
      storage: redis  # or "file" or "memory"
      redis_url: redis://localhost:6379
      ttl_seconds: 3600

    slow_path:
      enabled: true
      batch_size: 100
      flush_interval_seconds: 5  # Reduced from 60

  # Async callback configuration
  callbacks:
    async_enabled: true
    thread_pool_size: 4
```

## Performance Targets

- **Fast path writes**: <10ms p99 latency ✓
- **Event publishing**: <5ms overhead ✓
- **Async callbacks**: <50ms invocation overhead ✓
- **Memory overhead**: <100MB ✓

## Workflow Orchestrator Integration

### Verodat Integration

```python
from adri.callbacks import AsyncCallbackManager
from adri.logging.fast_path import FastPathLogger
from adri.decorator import adri_protected

# Setup
fast_path = FastPathLogger(storage="redis")
callbacks = AsyncCallbackManager()

async def notify_verodat(result):
    # Send assessment ID to Verodat workflow
    await verodat_client.update_workflow(
        assessment_id=result.assessment_id,
        status="PASSED" if result.passed else "BLOCKED",
        score=result.overall_score
    )

callbacks.add_callback(notify_verodat)

@adri_protected(
    standard="transaction_data",
    fast_path_logger=fast_path,
    async_callbacks=callbacks
)
def process_transactions(data):
    return validated_data
```

### Prefect Integration

```python
from prefect import task, flow
from adri.callbacks import PrefectAdapter
from adri.logging.fast_path import FastPathLogger

fast_path = FastPathLogger(storage="redis")
adapter = PrefectAdapter()

@task
@adri_protected(
    standard="customer_data",
    fast_path_logger=fast_path,
    workflow_adapter=adapter
)
def validate_customers(data):
    return process(data)

@flow
def customer_pipeline():
    data = extract_customers()

    # Fast path makes assessment ID available immediately
    result = validate_customers(data)

    # Next task can start without waiting for batch flush
    transformed = transform_customers(result)

    return transformed
```

### LangGraph Integration

```python
from langgraph.graph import StateGraph
from adri.callbacks import AsyncCallbackManager
from adri.decorator import adri_protected

callbacks = AsyncCallbackManager()

async def update_graph_state(result):
    # Update graph state with assessment results
    await graph.update_node_state({
        "assessment_id": result.assessment_id,
        "quality_score": result.overall_score,
        "passed": result.passed
    })

callbacks.add_callback(update_graph_state)

@adri_protected(
    standard="agent_data",
    async_callbacks=callbacks
)
def agent_decision_node(state):
    # Agent decision logic
    return decision
```

## Migration Guide

### From Old Architecture

**Before (60s delay):**
```python
@adri_protected(standard="data")
def process(data):
    return result

# Assessment ID not available for 30-60 seconds
# Workflow orchestrators had to poll or wait
```

**After (immediate access):**
```python
from adri.logging.fast_path import FastPathLogger

fast_path = FastPathLogger(storage="redis")

@adri_protected(
    standard="data",
    fast_path_logger=fast_path
)
def process(data):
    return result

# Assessment ID available immediately via fast path
# Workflow orchestrators can proceed without delay
```

### Backward Compatibility

All new features are **opt-in** via parameters:
- No `async_callbacks` → No async callback execution
- No `workflow_adapter` → No framework integration
- No `fast_path_logger` → No fast path writes
- Existing code works unchanged ✓

### Enabling New Features

**Step 1: Add Redis dependency (optional)**
```bash
pip install redis>=5.0.0
```

**Step 2: Update configuration**
```yaml
# adri-config.yaml
adri:
  events:
    enabled: true
  logging:
    fast_path:
      enabled: true
      storage: redis
```

**Step 3: Update decorator usage**
```python
from adri.logging.fast_path import FastPathLogger
from adri.callbacks import AsyncCallbackManager, PrefectAdapter

# Setup components
fast_path = FastPathLogger(storage="redis")
callbacks = AsyncCallbackManager()
adapter = PrefectAdapter()

# Use in decorator
@adri_protected(
    standard="your_standard",
    fast_path_logger=fast_path,
    async_callbacks=callbacks,
    workflow_adapter=adapter
)
def your_function(data):
    return result
```

## Testing

Run integration tests:
```bash
# All integration tests
pytest tests/integration/test_event_driven_logging.py -v

# Specific test class
pytest tests/integration/test_event_driven_logging.py::TestEventDrivenLoggingFlow -v

# Performance benchmarks (manual)
pytest tests/integration/test_event_driven_logging.py::TestPerformanceBenchmarks -v
```

Run unit tests:
```bash
# Event system tests
pytest tests/events/test_event_bus.py -v

# Fast path tests
pytest tests/logging/test_fast_path.py -v

# Callback tests
pytest tests/callbacks/test_async_handler.py -v
```

## Troubleshooting

### Fast Path Not Working

**Symptom**: Manifests not being written

**Solutions:**
1. Check fast_path_logger is passed to decorator
2. Verify storage backend is accessible (Redis running, file dir writable)
3. Check logs for errors: `ADRI_DEBUG=1 python your_script.py`

### Events Not Publishing

**Symptom**: Event subscribers not receiving events

**Solutions:**
1. Verify events are enabled in AssessmentResult: `publish_events=True` (default)
2. Check event bus subscriptions: `bus.get_subscriber_count()`
3. Verify no exceptions in event callbacks (they're logged but swallowed)

### Async Callbacks Not Executing

**Symptom**: Async callbacks not being invoked

**Solutions:**
1. Verify AsyncCallbackManager is passed to decorator
2. Check `enable_async=True` (default)
3. Ensure event loop is running: `manager._loop_ready.is_set()`
4. Check callback logs for errors

### Redis Connection Issues

**Symptom**: "Cannot connect to Redis" error

**Solutions:**
1. Verify Redis is running: `redis-cli ping`
2. Check Redis URL is correct: `redis://localhost:6379`
3. Test connection: `redis-cli -u redis://localhost:6379 ping`
4. Fall back to file storage if Redis unavailable

## Performance Optimization

### Fast Path Storage Selection

- **Memory**: Fastest (microseconds), not persistent, dev/testing only
- **File**: Fast (<10ms), persistent, single machine
- **Redis**: Fast (<10ms), persistent, distributed, production recommended

### Async Callback Configuration

```python
# Optimize thread pool for your workload
manager = AsyncCallbackManager(
    thread_pool_size=8,  # More threads for I/O-bound callbacks
    enable_async=True
)
```

### Event System Tuning

```python
# Subscribe to specific events, not all
bus.subscribe(EventType.ASSESSMENT_COMPLETED, callback)  # Specific
bus.subscribe(None, callback)  # All events (slower)
```

## Security Considerations

### Redis Security

```yaml
adri:
  logging:
    fast_path:
      redis_url: redis://username:password@localhost:6379
      # Use TLS in production
      redis_url: rediss://username:password@prod-redis:6379
```

### Webhook Security

```python
# Validate webhook URLs
async def secure_webhook(result):
    if not webhook_url.startswith("https://"):
        raise ValueError("Only HTTPS webhooks allowed")
    await send_webhook(result)
```

### Data Sanitization

```python
# Sanitize sensitive data before events
def sanitize_callback(result):
    # Remove PII before sending to external systems
    safe_data = {
        "assessment_id": result.assessment_id,
        "score": result.overall_score,
        "passed": result.passed
        # Don't include raw data or field details
    }
    send_to_external_system(safe_data)
```

## Advanced Usage

### Custom Event Subscribers

```python
from adri.events import get_event_bus, EventType

class WorkflowOrchestrator:
    def __init__(self):
        self.bus = get_event_bus()
        self.sub_id = self.bus.subscribe(
            EventType.ASSESSMENT_COMPLETED,
            self.on_assessment_complete
        )

    def on_assessment_complete(self, event):
        # Update workflow state
        self.update_workflow(
            assessment_id=event.assessment_id,
            status=event.payload.get("status"),
            score=event.payload.get("score")
        )

    def cleanup(self):
        self.bus.unsubscribe(self.sub_id)
```

### Multi-Backend Fast Path

```python
from adri.logging.fast_path import FastPathLogger

# Primary: Redis (fast, distributed)
primary = FastPathLogger(storage="redis")

# Fallback: File (slower, but always available)
fallback = FastPathLogger(storage="file", storage_dir="./ADRI/fast_path")

def write_with_fallback(manifest):
    try:
        primary.log_manifest(manifest)
    except Exception:
        fallback.log_manifest(manifest)
```

### Workflow Context Tracking

```python
from adri.decorator import adri_protected

workflow_context = {
    "run_id": "run_20250110_143022_abc",
    "workflow_id": "customer_processing",
    "workflow_version": "2.1.0",
    "step_id": "validation",
    "step_sequence": 1,
    "run_at_utc": "2025-01-10T14:30:22Z"
}

@adri_protected(
    standard="customer_data",
    workflow_context=workflow_context
)
def validate_step(data):
    return result
```

## API Reference

### FastPathLogger

**Constructor:**
```python
FastPathLogger(
    storage: str = "memory",
    storage_dir: Optional[str] = None,
    redis_url: str = "redis://localhost:6379",
    ttl_seconds: int = 3600
)
```

**Methods:**
- `log_manifest(manifest: AssessmentManifest) -> None`: Write manifest
- `get_manifest(assessment_id: str) -> Optional[AssessmentManifest]`: Read manifest
- `wait_for_completion(assessment_id: str, timeout: int = 30) -> Optional[AssessmentManifest]`: Block until complete
- `close() -> None`: Cleanup resources

### AsyncCallbackManager

**Constructor:**
```python
AsyncCallbackManager(
    thread_pool_size: int = 4,
    enable_async: bool = True
)
```

**Methods:**
- `add_callback(callback: CallbackType) -> str`: Register callback
- `remove_callback(callback_id: str) -> bool`: Remove callback
- `invoke_all(assessment_result: Any) -> None`: Invoke all callbacks
- `get_callback_count() -> int`: Get registered count
- `close() -> None`: Cleanup resources

### EventBus

**Methods:**
- `subscribe(event_type: Optional[EventType], callback: Callable) -> str`: Subscribe
- `unsubscribe(subscription_id: str) -> bool`: Unsubscribe
- `publish(event: AssessmentEvent) -> None`: Publish event
- `get_subscriber_count(event_type: Optional[EventType] = None) -> int`: Get count

## Best Practices

1. **Use Redis for Production**: File storage is ok for single-machine, but Redis scales better
2. **Enable Fast Path Selectively**: Only enable where real-time access is needed
3. **Monitor Performance**: Track fast path latency and event overhead
4. **Cleanup Resources**: Always call `close()` or use context managers
5. **Handle Errors Gracefully**: Fast path and callback failures are non-critical
6. **Sanitize Event Payloads**: Remove PII before publishing to external systems
7. **Use Workflow Adapters**: Let framework-specific adapters handle integration details
8. **Test Async Patterns**: Async callbacks need special testing consideration

## Future Enhancements

Potential future improvements:

1. **Redis Pub/Sub**: More efficient wait_for_completion using Redis pub/sub instead of polling
2. **Webhook Publishers**: Built-in HTTP webhook event publishers
3. **Kafka Integration**: Event streaming to Kafka for high-volume scenarios
4. **gRPC Adapters**: Low-latency event streaming via gRPC
5. **GraphQL Subscriptions**: Real-time event subscriptions via GraphQL
6. **Prometheus Metrics**: Performance metrics export to Prometheus
7. **OpenTelemetry**: Distributed tracing integration

## Support

For issues or questions:
- Documentation: https://docs.adri.ai
- GitHub Issues: https://github.com/verodat/adri-enterprise/issues
- Community: https://community.adri.ai
