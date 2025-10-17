# verodat-adri Enterprise Features

This document describes features unique to **verodat-adri** that differentiate it from the community ADRI edition.

## Overview

**verodat-adri** is built on the foundation of community ADRI with enterprise-grade extensions for:
- Real-time workflow orchestration integration
- Verodat cloud platform integration
- Event-driven assessment logging
- Fast-path assessment ID capture
- Async callback infrastructure

## Community ADRI vs verodat-adri

| Feature | Community ADRI | verodat-adri |
|---------|---------------|--------------|
| **Package Name** | `adri` | `verodat-adri` |
| **Import** | `import adri` | `import adri` (same!) |
| **Core Decorator** | ✅ @adri_protected | ✅ @adri_protected |
| **Validation Engine** | ✅ Complete | ✅ Complete |
| **Guard Modes** | ✅ All modes | ✅ All modes |
| **Local Logging** | ✅ LocalLogger | ✅ LocalLogger |
| **Verodat API** | ❌ Not available | ✅ EnterpriseLogger |
| **Event System** | ❌ Not available | ✅ EventBus & Events |
| **Fast Path Logging** | ❌ Not available | ✅ <10ms ID capture |
| **Async Callbacks** | ❌ Not available | ✅ Callback infrastructure |
| **Workflow Adapters** | ❌ Not available | ✅ Prefect, Airflow |
| **Real-time Integration** | ❌ Limited | ✅ Full support |

## Enterprise-Only Features

### 1. Verodat Cloud Integration

**Module**: `src/adri/logging/enterprise.py`

The `EnterpriseLogger` provides seamless integration with the Verodat cloud platform:

```python
from adri.logging.enterprise import EnterpriseLogger

# Configure Verodat integration
logger = EnterpriseLogger(
    api_base_url="https://api.verodat.com",
    api_key="your-api-key",
    workspace_id="your-workspace-id"
)

# Use with decorator
@adri_protected(
    standard="invoice_standard.yaml",
    logger=logger  # Enterprise cloud logging
)
def process_invoice(invoice_data):
    return {"invoice_id": invoice_data["id"]}
```

**Features**:
- ✅ Real-time upload to Verodat platform
- ✅ 5-second batch flush (vs 60s in community edition)
- ✅ Cloud-based assessment history
- ✅ Team collaboration and sharing
- ✅ Advanced analytics and reporting
- ✅ Compliance and audit trails

### 2. Event-Driven Architecture

**Modules**: `src/adri/events/`

Real-time pub/sub event system for assessment lifecycle:

```python
from adri.events import EventBus, AssessmentEvent

# Create event bus
event_bus = EventBus()

# Subscribe to events
@event_bus.subscribe(AssessmentEvent.COMPLETED)
def on_assessment_complete(event):
    print(f"Assessment {event.assessment_id} completed with score {event.score}")

# Use with decorator
@adri_protected(
    standard="data_standard.yaml",
    event_bus=event_bus  # Enable events
)
def process_data(data):
    return {"data_id": data["id"]}
```

**Event Types**:
- `CREATED` - Assessment record created
- `STARTED` - Validation started
- `COMPLETED` - Assessment finished successfully
- `FAILED` - Assessment failed
- `PERSISTED` - Assessment logged to storage

**Performance**:
- ✅ <5ms event publishing overhead
- ✅ Thread-safe event bus
- ✅ Error isolation between subscribers
- ✅ Async and sync callback support

### 3. Fast Path Logging

**Module**: `src/adri/logging/fast_path.py`

Immediate assessment ID capture for workflow orchestration:

```python
from adri.logging.fast_path import FastPathLogger, MemoryBackend

# Create fast path logger
fast_logger = FastPathLogger(
    backend=MemoryBackend(),  # Or FileBackend, RedisBackend
    ttl_seconds=3600
)

# Use with decorator
@adri_protected(
    standard="order_standard.yaml",
    fast_path_logger=fast_logger  # Immediate ID capture
)
def process_order(order_data):
    return {"order_id": order_data["id"]}

# Get assessment ID immediately (< 10ms)
result = process_order(my_order)
assessment = fast_logger.get_latest()
print(f"Assessment ID: {assessment.assessment_id}")
```

**Storage Backends**:

**MemoryBackend** - In-memory storage for development
```python
from adri.logging.fast_path import MemoryBackend
backend = MemoryBackend()
```

**FileBackend** - JSON file storage for persistence
```python
from adri.logging.fast_path import FileBackend
backend = FileBackend(directory="/var/log/adri/fast-path")
```

**RedisBackend** - Distributed storage for production
```python
from adri.logging.fast_path import RedisBackend
backend = RedisBackend(
    host="redis.example.com",
    port=6379,
    db=0,
    password="secret"
)
```

**Performance**:
- ✅ <10ms write latency (p99)
- ✅ Immediate assessment ID availability
- ✅ Blocking wait API: `wait_for_completion()`
- ✅ TTL-based automatic cleanup

### 4. Unified Logging

**Module**: `src/adri/logging/unified.py`

Coordinated dual-write to fast path and enterprise cloud:

```python
from adri.logging.unified import UnifiedLogger
from adri.logging.enterprise import EnterpriseLogger
from adri.logging.fast_path import FastPathLogger, MemoryBackend

# Create unified logger
unified = UnifiedLogger(
    fast_path_logger=FastPathLogger(backend=MemoryBackend()),
    slow_path_logger=EnterpriseLogger(
        api_base_url="https://api.verodat.com",
        api_key="your-key"
    )
)

# Use with decorator - gets both fast and slow path
@adri_protected(
    standard="customer_standard.yaml",
    logger=unified  # Best of both worlds
)
def process_customer(customer_data):
    return {"customer_id": customer_data["id"]}
```

**Benefits**:
- ✅ Immediate ID availability (fast path)
- ✅ Complete cloud logging (slow path)
- ✅ Automatic coordination
- ✅ Error isolation between paths

### 5. Async Callback Infrastructure

**Modules**: `src/adri/callbacks/`

Asynchronous callback system for workflow integration:

```python
from adri.callbacks import AsyncCallbackManager

# Create callback manager
callback_mgr = AsyncCallbackManager(max_workers=4)

# Define callbacks
async def send_notification(assessment_id, score):
    await notify_team(f"Assessment {assessment_id}: score {score}")

def update_database(assessment_id, result):
    db.update("assessments", assessment_id, result)

# Register callbacks
callback_mgr.add_callback("send_notification", send_notification)
callback_mgr.add_callback("update_db", update_database)

# Use with decorator
@adri_protected(
    standard="transaction_standard.yaml",
    callback_manager=callback_mgr,
    on_complete=["send_notification", "update_db"]
)
def process_transaction(txn_data):
    return {"txn_id": txn_data["id"]}
```

**Features**:
- ✅ Async and sync callback support
- ✅ Thread pool execution
- ✅ <50ms invocation overhead
- ✅ Error handling and logging
- ✅ Configurable timeout

### 6. Workflow Orchestration Adapters

**Module**: `src/adri/callbacks/workflow_adapters.py`

Pre-built adapters for popular workflow engines:

**Prefect Integration**:
```python
from adri.callbacks.workflow_adapters import PrefectAdapter
from prefect import flow, task

# Create adapter
adapter = PrefectAdapter()

@task
@adri_protected(
    standard="pipeline_standard.yaml",
    callback_manager=adapter.callback_manager,
    on_complete=["create_prefect_artifact"]
)
def process_data(data):
    return {"result": data["value"] * 2}

@flow
def data_pipeline():
    result = process_data({"value": 42})
    return result
```

**Airflow Integration**:
```python
from adri.callbacks.workflow_adapters import AirflowAdapter
from airflow.decorators import dag, task
from datetime import datetime

# Create adapter
adapter = AirflowAdapter()

@dag(start_date=datetime(2025, 1, 1), schedule=None)
def data_quality_dag():

    @task
    @adri_protected(
        standard="etl_standard.yaml",
        callback_manager=adapter.callback_manager,
        on_complete=["push_to_xcom"]
    )
    def validate_data(data):
        return {"validation_result": "passed"}

    validate_data({"source": "database"})
```

**Features**:
- ✅ Automatic artifact creation
- ✅ XCom integration (Airflow)
- ✅ State updates
- ✅ Failure handling

## Migration from Community ADRI

### Installation

**Community ADRI**:
```bash
pip install adri
```

**verodat-adri**:
```bash
# Base installation
pip install verodat-adri

# With Redis support
pip install verodat-adri[redis]

# With workflow support
pip install verodat-adri[workflows]

# Full enterprise features
pip install verodat-adri[events]
```

### Code Changes

**Minimal Migration** - No code changes required:
```python
# This works in both editions
from adri import adri_protected

@adri_protected(standard="standard.yaml")
def process_data(data):
    return {"id": data["id"]}
```

**Enterprise Features** - Opt-in gradually:
```python
# Step 1: Add fast path for immediate IDs
from adri.logging.fast_path import FastPathLogger, MemoryBackend

fast_logger = FastPathLogger(backend=MemoryBackend())

@adri_protected(
    standard="standard.yaml",
    fast_path_logger=fast_logger  # Add this
)
def process_data(data):
    return {"id": data["id"]}

# Step 2: Add Verodat cloud integration
from adri.logging.enterprise import EnterpriseLogger

enterprise_logger = EnterpriseLogger(
    api_base_url="https://api.verodat.com",
    api_key=os.getenv("VERODAT_API_KEY")
)

@adri_protected(
    standard="standard.yaml",
    logger=enterprise_logger  # Replace or add
)
def process_data(data):
    return {"id": data["id"]}

# Step 3: Add event notifications
from adri.events import EventBus, AssessmentEvent

event_bus = EventBus()

@event_bus.subscribe(AssessmentEvent.COMPLETED)
def on_complete(event):
    print(f"Assessment {event.assessment_id} completed")

@adri_protected(
    standard="standard.yaml",
    event_bus=event_bus  # Add event system
)
def process_data(data):
    return {"id": data["id"]}
```

### Configuration

**Community ADRI** config (adri-config.yaml):
```yaml
logging:
  type: local
  log_dir: ./adri_logs
  flush_interval: 60
```

**verodat-adri** config (adri-config.yaml):
```yaml
logging:
  type: enterprise
  api_base_url: https://api.verodat.com
  api_key: ${VERODAT_API_KEY}
  workspace_id: ${VERODAT_WORKSPACE_ID}
  flush_interval: 5  # Faster enterprise flush

fast_path:
  enabled: true
  backend: redis
  redis_url: redis://localhost:6379/0
  ttl_seconds: 3600

events:
  enabled: true
  max_subscribers: 100

callbacks:
  enabled: true
  max_workers: 4
  timeout: 30
```

## Performance Comparison

| Metric | Community ADRI | verodat-adri |
|--------|---------------|--------------|
| **Assessment ID Availability** | 30-60 seconds | <10ms |
| **Log Flush Interval** | 60 seconds | 5 seconds |
| **Event Notification** | Not available | <5ms |
| **Callback Overhead** | Not available | <50ms |
| **Memory Overhead** | Baseline | +<100MB |
| **Workflow Integration** | Manual | Native adapters |

## Enterprise Use Cases

### 1. Real-Time Data Pipeline

```python
from adri import adri_protected
from adri.logging.unified import UnifiedLogger
from adri.logging.enterprise import EnterpriseLogger
from adri.logging.fast_path import FastPathLogger, RedisBackend
from adri.events import EventBus, AssessmentEvent
from prefect import flow, task

# Setup enterprise stack
event_bus = EventBus()
fast_logger = FastPathLogger(backend=RedisBackend())
enterprise_logger = EnterpriseLogger(api_base_url="https://api.verodat.com")
unified = UnifiedLogger(fast_logger, enterprise_logger)

@event_bus.subscribe(AssessmentEvent.FAILED)
def handle_failure(event):
    alert_team(f"Data quality issue: {event.assessment_id}")

@task
@adri_protected(
    standard="pipeline_standard.yaml",
    logger=unified,
    event_bus=event_bus
)
def validate_pipeline_stage(data):
    return {"stage": "completed", "records": len(data)}

@flow
def data_quality_pipeline():
    raw_data = extract_data()
    validated = validate_pipeline_stage(raw_data)
    return validated
```

### 2. Multi-Stage Workflow

```python
from airflow.decorators import dag, task
from adri.callbacks.workflow_adapters import AirflowAdapter

adapter = AirflowAdapter()

@dag(schedule="@daily")
def etl_quality_dag():

    @task
    @adri_protected(
        standard="extract_standard.yaml",
        callback_manager=adapter.callback_manager,
        on_complete=["push_to_xcom"]
    )
    def extract():
        return {"records": 1000}

    @task
    @adri_protected(
        standard="transform_standard.yaml",
        callback_manager=adapter.callback_manager,
        on_complete=["push_to_xcom"]
    )
    def transform(data):
        return {"transformed": data["records"]}

    @task
    @adri_protected(
        standard="load_standard.yaml",
        callback_manager=adapter.callback_manager,
        on_complete=["push_to_xcom", "notify_completion"]
    )
    def load(data):
        return {"loaded": data["transformed"]}

    data = extract()
    transformed = transform(data)
    load(transformed)
```

### 3. Event-Driven Monitoring

```python
from adri.events import EventBus, AssessmentEvent
from adri.callbacks import AsyncCallbackManager

event_bus = EventBus()
callback_mgr = AsyncCallbackManager()

# Monitor all assessments
@event_bus.subscribe(AssessmentEvent.COMPLETED)
def track_quality(event):
    metrics.increment("assessments.completed")
    metrics.gauge("assessment.score", event.score)

@event_bus.subscribe(AssessmentEvent.FAILED)
async def alert_on_failure(event):
    await send_slack_alert(
        f"⚠️ Assessment {event.assessment_id} failed\n"
        f"Dimension: {event.dimension}\n"
        f"Details: {event.details}"
    )

# Apply to all functions
@adri_protected(
    standard="monitoring_standard.yaml",
    event_bus=event_bus,
    callback_manager=callback_mgr
)
def process_critical_data(data):
    return {"processed": True}
```

## Support & Resources

### Documentation
- **Installation**: See README.md
- **Configuration**: See CONTRIBUTING.md
- **Upstream Sync**: See UPSTREAM_SYNC.md
- **Implementation**: See implementation_plan.md

### Getting Help
- **Issues**: https://github.com/Verodat/verodat-adri/issues
- **Enterprise Support**: Contact Verodat team
- **Community ADRI**: https://github.com/adri-standard/adri

### License
verodat-adri maintains the same Apache 2.0 license as community ADRI, with additional enterprise components copyright Verodat.

---

*Last Updated: 2025-04-05*
*Version: 5.0.0*
