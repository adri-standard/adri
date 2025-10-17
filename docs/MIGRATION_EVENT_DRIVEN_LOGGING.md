# Migration Guide: Event-Driven Assessment Logging

## Overview

This guide helps you migrate from the old batched logging architecture to the new event-driven three-tier logging system. The migration is designed to be **gradual and non-breaking** - you can adopt features incrementally.

## Migration Checklist

- [ ] **Review new architecture** (read EVENT_DRIVEN_LOGGING.md)
- [ ] **Install optional dependencies** (if using Redis)
- [ ] **Update configuration** (enable fast path and events)
- [ ] **Update decorator usage** (add async features)
- [ ] **Test in development** (verify fast path and callbacks)
- [ ] **Deploy to production** (monitor performance)
- [ ] **Monitor and optimize** (tune settings)

## Phase 1: Dependencies (Optional)

### Install Redis Support (Recommended for Production)

```bash
# Install Redis client
pip install redis>=5.0.0

# Or install with all workflow features
pip install adri[workflows]
```

### Verify Installation

```bash
python -c "import redis; print(f'Redis version: {redis.__version__}')"
```

## Phase 2: Configuration

### Minimal Configuration (Fast Path Only)

Add to `adri-config.yaml`:

```yaml
adri:
  # Enable events (no external dependencies)
  events:
    enabled: true

  # Enable fast path with file storage (no Redis needed)
  logging:
    fast_path:
      enabled: true
      storage: file
      storage_dir: ./ADRI/fast_path
      ttl_seconds: 3600
```

### Full Configuration (All Features)

```yaml
adri:
  # Event system
  events:
    enabled: true

  # Fast path logging
  logging:
    fast_path:
      enabled: true
      storage: redis
      redis_url: redis://localhost:6379
      ttl_seconds: 3600

    slow_path:
      enabled: true
      batch_size: 100
      flush_interval_seconds: 5  # Reduced from 60

  # Async callbacks
  callbacks:
    async_enabled: true
    thread_pool_size: 4
```

## Phase 3: Code Migration

### Step 1: Event Subscribers (Optional)

Add event listeners for monitoring:

```python
from adri.events import get_event_bus, EventType

bus = get_event_bus()

def log_assessment_complete(event):
    print(f"✓ Assessment {event.assessment_id} completed")

bus.subscribe(EventType.ASSESSMENT_COMPLETED, log_assessment_complete)
```

### Step 2: Fast Path Logger

#### Before (No immediate access):
```python
@adri_protected(standard="customer_data")
def process_customers(data):
    return analyze(data)

# Assessment ID not available until batch flush (30-60s delay)
```

#### After (Immediate access):
```python
from adri.logging.fast_path import FastPathLogger

# Initialize once per application
fast_path = FastPathLogger(storage="redis")

@adri_protected(
    standard="customer_data",
    fast_path_logger=fast_path
)
def process_customers(data):
    return analyze(data)

# Assessment ID available immediately via fast_path.get_manifest()
```

### Step 3: Async Callbacks

#### Before (Polling for results):
```python
results = []

def capture_result(result):
    results.append(result)

@adri_protected(
    standard="data",
    on_assessment=capture_result
)
def process(data):
    return result

# Sync callback blocks or requires polling
```

#### After (Async notifications):
```python
from adri.callbacks import AsyncCallbackManager

manager = AsyncCallbackManager()
results = []

async def async_capture(result):
    # Non-blocking async operation
    await send_to_monitoring_system(result)
    results.append(result)

manager.add_callback(async_capture)

@adri_protected(
    standard="data",
    async_callbacks=manager
)
def process(data):
    return result

# Async callback executes without blocking
```

### Step 4: Workflow Adapters

#### Prefect Migration:

```python
from prefect import task, flow
from adri.callbacks import PrefectAdapter
from adri.logging.fast_path import FastPathLogger

# Setup once
fast_path = FastPathLogger(storage="redis")
adapter = PrefectAdapter()

# Before
@task
@adri_protected(standard="invoice_data")
def validate_invoices(data):
    return process(data)

# After
@task
@adri_protected(
    standard="invoice_data",
    fast_path_logger=fast_path,
    workflow_adapter=adapter
)
def validate_invoices(data):
    return process(data)
```

#### Airflow Migration:

```python
from airflow.decorators import task
from adri.callbacks import AirflowAdapter
from adri.logging.fast_path import FastPathLogger

# Setup
fast_path = FastPathLogger(storage="redis")
adapter = AirflowAdapter(push_to_xcom=True)

# Before
@task
@adri_protected(standard="customer_data")
def validate_customers(**context):
    return process(data)

# After
@task
@adri_protected(
    standard="customer_data",
    fast_path_logger=fast_path,
    workflow_adapter=adapter
)
def validate_customers(**context):
    return process(data)
    # Results automatically pushed to XCom
```

## Phase 4: Testing

### Unit Tests

Verify new components work:

```bash
# Event system
pytest tests/events/test_event_bus.py -v

# Fast path logging
pytest tests/logging/test_fast_path.py -v

# Async callbacks
pytest tests/callbacks/test_async_handler.py -v
```

### Integration Tests

Test end-to-end flow:

```bash
# Complete integration tests
pytest tests/integration/test_event_driven_logging.py -v

# Specific scenarios
pytest tests/integration/test_event_driven_logging.py::TestEventDrivenLoggingFlow -v
```

### Performance Tests

Verify performance targets:

```bash
# Fast path latency (<10ms)
pytest tests/logging/test_fast_path.py::TestFileManifestStore::test_write_performance -v

# Event overhead (<5ms)
pytest tests/events/test_event_bus.py::TestEventBusPerformance::test_publish_latency -v

# Callback overhead (<50ms)
pytest tests/callbacks/test_async_handler.py::TestCallbackPerformance::test_callback_invocation_overhead -v
```

## Phase 5: Deployment

### Development Environment

```yaml
# adri-config.yaml (dev)
adri:
  environment: development
  events:
    enabled: true
  logging:
    fast_path:
      enabled: true
      storage: file  # No Redis dependency
      storage_dir: ./ADRI/dev/fast_path
```

### Production Environment

```yaml
# adri-config.yaml (prod)
adri:
  environment: production
  events:
    enabled: true
  logging:
    fast_path:
      enabled: true
      storage: redis
      redis_url: ${REDIS_URL}  # From environment variable
      ttl_seconds: 7200  # 2 hours
    slow_path:
      flush_interval_seconds: 5
  callbacks:
    async_enabled: true
    thread_pool_size: 8  # More threads for production
```

### Environment Variables

```bash
# Production environment
export REDIS_URL="redis://username:password@redis.prod.example.com:6379"
export ADRI_ENV=production
export ADRI_CONFIG_PATH=/etc/adri/adri-config.yaml
```

## Common Migration Patterns

### Pattern 1: Workflow Orchestration

**Goal**: Enable real-time pipeline coordination

```python
from adri.logging.fast_path import FastPathLogger
from adri.callbacks import AsyncCallbackManager

# Initialize once at app startup
fast_path = FastPathLogger(storage="redis")
callbacks = AsyncCallbackManager()

async def notify_next_step(result):
    await workflow_engine.trigger_next_step(
        assessment_id=result.assessment_id,
        can_proceed=result.passed
    )

callbacks.add_callback(notify_next_step)

# Use in all validation steps
@adri_protected(
    standard="step1_data",
    fast_path_logger=fast_path,
    async_callbacks=callbacks
)
def step1(data):
    return validated_data

@adri_protected(
    standard="step2_data",
    fast_path_logger=fast_path,
    async_callbacks=callbacks
)
def step2(data):
    return processed_data
```

### Pattern 2: Real-Time Monitoring

**Goal**: Monitor data quality in real-time

```python
from adri.events import get_event_bus, EventType

bus = get_event_bus()
quality_metrics = []

def track_quality(event):
    quality_metrics.append({
        "assessment_id": event.assessment_id,
        "timestamp": event.timestamp,
        "score": event.payload.get("score")
    })

    # Send to monitoring system
    prometheus_client.gauge("adri_quality_score").set(event.payload.get("score", 0))

bus.subscribe(EventType.ASSESSMENT_COMPLETED, track_quality)
```

### Pattern 3: Multi-Framework Integration

**Goal**: Use ADRI with multiple workflow frameworks

```python
from adri.callbacks import PrefectAdapter, AirflowAdapter
from adri.logging.fast_path import FastPathLogger

# Shared components
fast_path = FastPathLogger(storage="redis")

# Prefect tasks
prefect_adapter = PrefectAdapter()

@prefect_task
@adri_protected(
    standard="prefect_data",
    fast_path_logger=fast_path,
    workflow_adapter=prefect_adapter
)
def prefect_validation(data):
    return result

# Airflow tasks
airflow_adapter = AirflowAdapter(push_to_xcom=True)

@airflow_task
@adri_protected(
    standard="airflow_data",
    fast_path_logger=fast_path,
    workflow_adapter=airflow_adapter
)
def airflow_validation(data):
    return result
```

## Rollback Plan

If issues arise, you can rollback incrementally:

### Step 1: Disable Fast Path

```yaml
adri:
  logging:
    fast_path:
      enabled: false  # Disable fast path
```

### Step 2: Disable Events

```python
# Disable event publishing in code
from adri.validator.engine import AssessmentResult

result = AssessmentResult(
    ...,
    publish_events=False  # Disable events
)
```

### Step 3: Remove Async Callbacks

```python
# Don't pass async_callbacks to decorator
@adri_protected(standard="data")  # Works without async features
def process(data):
    return result
```

### Step 4: Restore Old Flush Interval

```yaml
adri:
  logging:
    slow_path:
      flush_interval_seconds: 60  # Restore old interval
```

## Monitoring & Validation

### Metrics to Track

1. **Fast Path Latency**: Should be <10ms p99
2. **Event Publish Overhead**: Should be <5ms
3. **Callback Execution Time**: Monitor for slow callbacks
4. **Memory Usage**: Should be <100MB overhead
5. **Redis Connection Health**: Monitor connection errors

### Health Checks

```python
from adri.logging.fast_path import FastPathLogger
from adri.events import get_event_bus

def health_check():
    """Verify event-driven logging is healthy."""
    checks = {}

    # Check fast path
    try:
        fast_path = FastPathLogger(storage="redis")
        from adri.events.types import AssessmentManifest
        from datetime import datetime

        test_manifest = AssessmentManifest(
            assessment_id="health_check",
            timestamp=datetime.now(),
            status="CREATED"
        )
        fast_path.log_manifest(test_manifest)
        retrieved = fast_path.get_manifest("health_check")
        checks["fast_path"] = retrieved is not None
        fast_path.close()
    except Exception as e:
        checks["fast_path"] = False
        checks["fast_path_error"] = str(e)

    # Check event bus
    try:
        bus = get_event_bus()
        checks["event_bus"] = True
        checks["subscribers"] = bus.get_subscriber_count()
    except Exception as e:
        checks["event_bus"] = False
        checks["event_bus_error"] = str(e)

    return checks
```

### Logging

Enable debug logging to troubleshoot:

```bash
export ADRI_DEBUG=1
export PYTHONUNBUFFERED=1
python your_script.py 2>&1 | tee adri_migration.log
```

## Troubleshooting Common Issues

### Issue 1: Redis Connection Failures

**Symptom**: `ConnectionError: Cannot connect to Redis`

**Solutions:**
1. Check Redis is running: `redis-cli ping`
2. Verify Redis URL: Check `redis_url` in config
3. Fall back to file storage temporarily:
   ```yaml
   logging:
     fast_path:
       storage: file  # Fallback
   ```

### Issue 2: Async Callbacks Not Executing

**Symptom**: Callbacks registered but not invoked

**Solutions:**
1. Add wait time for async execution: `time.sleep(0.5)`
2. Check callback errors in logs
3. Verify AsyncCallbackManager is passed to decorator
4. Test with sync callback first to isolate async issues

### Issue 3: Events Not Received

**Symptom**: Event subscribers not receiving events

**Solutions:**
1. Verify subscription: `bus.get_subscriber_count(EventType.ASSESSMENT_CREATED)`
2. Check event publishing is enabled: `publish_events=True` (default)
3. Test with simple callback: `bus.subscribe(None, lambda e: print(e))`

### Issue 4: Performance Degradation

**Symptom**: Assessments slower with new features

**Solutions:**
1. Check fast path latency: Should be <10ms
2. Verify Redis is local or low-latency
3. Reduce thread pool size if CPU-bound: `thread_pool_size=2`
4. Disable features selectively to isolate issue

## Validation After Migration

### Test Checklist

Run these tests to validate migration:

```bash
# 1. Basic event publishing
pytest tests/events/test_event_bus.py::TestEventBusBasics::test_subscribe_and_publish -v

# 2. Fast path writes
pytest tests/logging/test_fast_path.py::TestMemoryManifestStore::test_write_and_read -v

# 3. Async callbacks
pytest tests/callbacks/test_async_handler.py::TestSyncCallbackExecution::test_invoke_sync_callback -v

# 4. Integration flow
pytest tests/integration/test_event_driven_logging.py::TestEventDrivenLoggingFlow::test_end_to_end_flow -v

# 5. Backward compatibility
pytest tests/integration/test_event_driven_logging.py::TestBackwardCompatibility -v
```

### Functional Testing

Create a test script:

```python
# test_migration.py
import pandas as pd
from datetime import datetime
from adri.logging.fast_path import FastPathLogger
from adri.callbacks import AsyncCallbackManager
from adri.events import get_event_bus, EventType
from adri.decorator import adri_protected

# Setup
fast_path = FastPathLogger(storage="file", storage_dir="./test_fast_path")
callbacks = AsyncCallbackManager()
events_received = []

# Event subscriber
bus = get_event_bus()
bus.subscribe(None, lambda e: events_received.append(e))

# Callback
def track_assessment(result):
    print(f"✓ Assessment {result.assessment_id} completed: {result.overall_score:.1f}")

callbacks.add_callback(track_assessment)

# Test function
@adri_protected(
    standard="test_migration",
    fast_path_logger=fast_path,
    async_callbacks=callbacks
)
def test_function(data):
    return len(data)

# Execute
test_data = pd.DataFrame({"x": [1, 2, 3]})
try:
    result = test_function(test_data)
    print(f"✓ Function executed: {result}")
except Exception as e:
    print(f"✗ Function failed: {e}")

# Wait for async processing
import time
time.sleep(0.5)

# Verify
print(f"\n✓ Events received: {len(events_received)}")
print(f"✓ Callbacks executed: Check output above")

# Cleanup
fast_path.close()
callbacks.close()
```

Run: `python test_migration.py`

## Production Deployment

### Step-by-Step Deployment

1. **Deploy to Staging**
   ```bash
   # Enable in staging environment
   export ADRI_ENV=staging
   # Test with production-like data
   pytest tests/integration/ -v
   ```

2. **Monitor Staging**
   - Check fast path latency metrics
   - Verify event publishing works
   - Monitor callback execution
   - Check Redis memory usage

3. **Gradual Production Rollout**
   ```python
   # Enable for 10% of traffic
   import random

   enable_fast_path = random.random() < 0.1

   fast_path = FastPathLogger(storage="redis") if enable_fast_path else None

   @adri_protected(
       standard="production_data",
       fast_path_logger=fast_path
   )
   def process(data):
       return result
   ```

4. **Monitor Production**
   - Fast path write latency
   - Redis connection errors
   - Callback failures
   - Memory usage trends

5. **Full Production Deployment**
   ```yaml
   # Enable for all traffic
   adri:
     logging:
       fast_path:
         enabled: true
   ```

### Production Checklist

- [ ] Redis cluster deployed and monitored
- [ ] TLS enabled for Redis connections
- [ ] Authentication configured
- [ ] Monitoring dashboards created
- [ ] Alerts configured for failures
- [ ] Backup fast path storage configured
- [ ] Rollback procedure documented
- [ ] Team trained on new architecture

## Performance Tuning

### Redis Optimization

```yaml
# Optimize for your workload
adri:
  logging:
    fast_path:
      storage: redis
      redis_url: redis://localhost:6379
      ttl_seconds: 1800  # Shorter TTL = less memory

      # Redis-specific tuning
      redis_config:
        socket_timeout: 5
        socket_connect_timeout: 5
        max_connections: 50
```

### Callback Thread Pool Sizing

```python
# I/O-bound callbacks (HTTP requests, DB writes)
manager = AsyncCallbackManager(thread_pool_size=16)

# CPU-bound callbacks (data processing)
manager = AsyncCallbackManager(thread_pool_size=4)

# Mixed workload
manager = AsyncCallbackManager(thread_pool_size=8)
```

### Event System Tuning

```python
# Subscribe only to needed events
bus.subscribe(EventType.ASSESSMENT_COMPLETED, callback)  # Specific

# Avoid subscribing to all events unless necessary
bus.subscribe(None, callback)  # Less selective
```

## FAQ

### Q: Do I need Redis?

A: No. File storage works well for single-machine deployments. Redis is recommended for distributed systems and high-volume scenarios.

### Q: Will this break my existing code?

A: No. All new features are opt-in. Existing decorators work unchanged.

### Q: What's the performance impact?

A: Minimal. Fast path adds <10ms, events add <5ms. Overall assessment time unchanged.

### Q: Can I use with my existing workflow tools?

A: Yes. We provide adapters for Prefect and Airflow, or create custom adapters.

### Q: How do I disable if there are issues?

A: Remove the optional parameters from decorator (`async_callbacks`, `fast_path_logger`, `workflow_adapter`). Everything works as before.

### Q: What about data privacy?

A: Fast path only stores minimal metadata (ID, status, score). No raw data. Sanitize event payloads before external transmission.

### Q: Can I use without async/await?

A: Yes. Use sync callbacks only, or don't use callbacks at all.

### Q: What if Redis goes down?

A: Assessments continue normally. Fast path writes fail but are non-critical. Slow path logging unaffected.

## Support & Resources

- **Documentation**: [EVENT_DRIVEN_LOGGING.md](EVENT_DRIVEN_LOGGING.md)
- **Architecture**: [ARCHITECTURE.md](../ARCHITECTURE.md)
- **Examples**: `examples/workflow_orchestration_example.py`
- **GitHub Issues**: https://github.com/verodat/adri-enterprise/issues
- **Community**: https://community.adri.ai

## Version Compatibility

- **ADRI >= 0.2.0**: Full event-driven logging support
- **ADRI 0.1.x**: Backward compatible (new features disabled)
- **Redis >= 5.0.0**: Required for Redis storage backend
- **Prefect >= 2.0.0**: Required for PrefectAdapter
- **Airflow >= 2.0.0**: Required for AirflowAdapter

## Next Steps

After successful migration:

1. **Monitor Performance**: Track metrics for 1-2 weeks
2. **Optimize Configuration**: Tune based on actual usage
3. **Expand Usage**: Apply to more workflows
4. **Train Team**: Ensure team understands new patterns
5. **Document Custom Patterns**: Document your specific use cases
6. **Contribute Back**: Share improvements with community

## Conclusion

The event-driven logging architecture provides immediate assessment ID access while maintaining full audit capabilities. Migration is gradual, non-breaking, and can be done incrementally. Start with fast path logging, add callbacks as needed, then integrate with workflow frameworks.

For questions or issues during migration, please file a GitHub issue or reach out to the community.
