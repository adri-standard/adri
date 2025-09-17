# ADRI Guard Modes

ADRI's protection system supports different modes for different scenarios. Choose the right mode for your use case.

## Protection Modes Overview

| Mode | Behavior | Best For |
|------|----------|----------|
| **FailFast** | Stops execution immediately on quality failure | Production, Financial, Critical systems |
| **Selective** | Logs warnings but continues execution | Balanced protection with flexibility |
| **WarnOnly** | Shows warnings but never blocks | Monitoring, Development, Gradual adoption |

## FailFast Mode (Default)

**When to use:** Production systems, financial processing, critical applications

```python
from adri import adri_protected

@adri_protected(
    standard="financial_data_standard",
    on_failure="raise"  # Explicit fail-fast
)
def process_transactions(transaction_data):
    return execute_payment(transaction_data)
```

**Behavior:**
- ❌ **Blocks execution** immediately when data quality is insufficient
- 🛑 **Raises ProtectionError** with detailed error message
- 📝 **Logs failure** for audit trail
- 🎯 **Best for:** Mission-critical functions that must have perfect data

## Selective Mode

**When to use:** Balanced protection, business logic that can handle some data issues

```python
@adri_protected(
    standard="customer_data_standard",
    on_failure="continue"  # Selective mode
)
def update_customer_profiles(customer_data):
    return update_profiles(customer_data)
```

**Behavior:**
- ⚠️ **Logs warnings** when data quality is below threshold
- ✅ **Continues execution** despite quality issues
- 📊 **Records quality metrics** for later review
- 🎯 **Best for:** Functions that can gracefully handle imperfect data

## WarnOnly Mode

**When to use:** Development, testing, gradual ADRI adoption

```python
@adri_protected(
    standard="user_data_standard",
    on_failure="warn"  # Warn-only mode
)
def analyze_user_behavior(user_data):
    return behavior_analysis(user_data)
```

**Behavior:**
- 💡 **Shows warnings** for quality issues
- 🚀 **Never blocks execution** 
- 📈 **Monitors quality trends** without impacting workflow
- 🎯 **Best for:** Development, monitoring, learning data patterns

## Configuration Examples

### Environment-Based Modes

```yaml
# adri-config.yaml
adri:
  environments:
    development:
      protection:
        default_failure_mode: "warn"    # Permissive in dev
        default_min_score: 70
    
    production:
      protection:
        default_failure_mode: "raise"   # Strict in prod
        default_min_score: 85
```

### Function-Specific Requirements

```python
# High-stakes financial processing
@adri_protected(
    standard="financial_standard",
    min_score=95,
    dimensions={
        "validity": 19,      # Near-perfect validity required
        "completeness": 19   # All fields must be complete
    },
    on_failure="raise"
)
def process_wire_transfer(transfer_data):
    return execute_transfer(transfer_data)

# User preference updates (more permissive)
@adri_protected(
    standard="preference_standard", 
    min_score=70,
    on_failure="warn"
)
def update_preferences(preference_data):
    return save_preferences(preference_data)
```

## Advanced Protection Patterns

### Dimension-Specific Protection

```python
@adri_protected(
    standard="customer_standard",
    dimensions={
        "validity": 18,      # Email/phone must be valid
        "completeness": 17,  # Most fields required
        "freshness": 15      # Data should be recent
    }
)
def personalized_marketing(customer_data):
    return create_campaign(customer_data)
```

### Conditional Protection

```python
def smart_processing(data, is_production=False):
    mode = "raise" if is_production else "warn"
    min_score = 90 if is_production else 75
    
    @adri_protected(
        standard="dynamic_standard",
        min_score=min_score,
        on_failure=mode
    )
    def protected_function(data):
        return process_data(data)
    
    return protected_function(data)
```

## Protection Mode API

### Using DataProtectionEngine Directly

```python
from adri.guard.modes import (
    DataProtectionEngine,
    FailFastMode,
    SelectiveMode, 
    WarnOnlyMode
)

# Create engine with specific mode
engine = DataProtectionEngine(FailFastMode())

# Or use factory functions
from adri.guard.modes import fail_fast_mode, selective_mode, warn_only_mode

strict_mode = fail_fast_mode({"min_score": 95})
balanced_mode = selective_mode({"min_score": 80})
monitoring_mode = warn_only_mode({"min_score": 70})
```

## Error Messages by Mode

### FailFast Mode Error
```
🛡️ ADRI Protection: BLOCKED ❌

📊 Quality Score: 65.0/100 (Required: 80.0/100)
📋 Standard: customer_data_standard

🔧 Fix This:
   1. Review standard: adri show-standard customer_data_standard
   2. Fix data issues and retry
   3. Test fixes: adri assess <data> --standard customer_data_standard
```

### Selective Mode Warning
```
⚠️  ADRI Warning: Data quality below threshold but continuing execution
📊 Score: 65.0
```

### WarnOnly Mode Message
```
⚠️  ADRI Data Quality Warning:
📊 Score: 65.0 (below threshold)
💡 Consider improving data quality for better AI agent performance
```

## Best Practices

1. **Start with WarnOnly** during development to understand your data patterns
2. **Use Selective** for business logic that can handle imperfect data
3. **Use FailFast** for critical production functions
4. **Set environment-specific defaults** in your configuration
5. **Monitor audit logs** to understand quality trends over time

For more information, see [Configuration Guide](../README.md) and [Standards Documentation](./standards.md).
