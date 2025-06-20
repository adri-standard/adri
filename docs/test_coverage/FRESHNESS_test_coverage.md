# FRESHNESS Test Coverage

This document tracks test coverage specifically for freshness-related functionality across ADRI, including the freshness dimension, freshness rules, and time-based validations.

## Purpose
Freshness testing ensures data is current, timely, and updated according to expected schedules. This is critical for time-sensitive data quality assessments.

## Test Coverage

### Freshness Dimension (adri/dimensions/freshness.py)
- **Unit Tests**: `tests/unit/dimensions/test_freshness.py`
  - ✅ Tests timestamp validation
  - ✅ Tests age calculation
  - ✅ Tests update frequency checking
  - ✅ Tests timezone handling
  - ✅ Tests stale data detection

### Freshness Rules (adri/rules/freshness.py)
- **Unit Tests**: `tests/unit/rules/test_freshness_rules.py`
  - ✅ Tests MaxAgeRule
  - ✅ Tests UpdateFrequencyRule
  - ✅ Tests LastModifiedRule
  - ✅ Tests ExpirationRule
  - ✅ Tests StaleDataRule
  - ✅ Tests time window rules

### Expiration Rule (adri/rules/expiration_rule.py)
- **Unit Tests**: `tests/unit/rules/test_expiration_rule.py`
  - ✅ Tests expiration date parsing
  - ✅ Tests warning period calculations
  - ✅ Tests multiple date formats
  - ✅ Tests timezone conversions
  - ✅ Tests grace period handling

### Business Freshness (adri/dimensions/business_freshness.py)
- **Unit Tests**: `tests/unit/dimensions/test_business_freshness.py`
  - ✅ Tests business hour calculations
  - ✅ Tests SLA compliance
  - ✅ Tests industry-specific freshness rules

### Integration Tests
- **Real-time Data**: `tests/integration/test_freshness_realtime.py`
  - ✅ Tests streaming data freshness
  - ✅ Tests API response timeliness
  - ✅ Tests database update tracking

### Key Features Tested

| Feature | Test Type | Coverage |
|---------|-----------|----------|
| Age calculation | Unit | ✅ Complete |
| Update frequency | Unit | ✅ Complete |
| Expiration checking | Unit | ✅ Complete |
| Timezone handling | Unit | ✅ Complete |
| SLA compliance | Unit | ✅ Complete |
| Warning periods | Unit | ✅ Complete |
| Business hours | Unit | ✅ Complete |

### Test Statistics
- **Total Tests**: 72
- **Passing**: 72
- **Coverage**: 90%

### Example Test Cases

```python
<!-- audience: ai-builders -->
def test_max_age_rule():
    """Test data age validation."""
    rule = MaxAgeRule(max_age_hours=24)
    
    # Fresh data
    fresh_data = {
        "updated_at": datetime.now() - timedelta(hours=12)
    }
    assert rule.evaluate(fresh_data).passed
    
    # Stale data
    stale_data = {
        "updated_at": datetime.now() - timedelta(hours=48)
    }
    assert not rule.evaluate(stale_data).passed

def test_expiration_with_warning():
    """Test expiration detection with warning period."""
    rule = ExpirationRule(warning_days=7)
    
    # Data expiring soon (within warning period)
    warning_data = {
        "expires_at": datetime.now() + timedelta(days=5)
    }
    result = rule.evaluate(warning_data)
    assert result.severity == Severity.WARNING
    assert "expires in 5 days" in result.message
```

### Freshness Configurations

```yaml
freshness:
  rules:
    - field: last_updated
      max_age_hours: 24
      severity: error
      
    - field: created_date
      update_frequency_hours: 12
      business_hours_only: true
      
    - field: expires_at
      warning_days: 30
      error_days: 7
      
    - field: data_timestamp
      timezone: UTC
      max_lag_minutes: 15
```

### Common Freshness Issues Detected
1. **Stale Data**: Data older than acceptable threshold
2. **Missing Updates**: Expected updates not received
3. **Expired Data**: Data past expiration date
4. **Update Delays**: Updates arriving later than SLA
5. **Timezone Issues**: Incorrect timestamp interpretations

### Time-based Test Utilities

```python
<!-- audience: ai-builders -->
# Test helpers for time-based testing
def freeze_time(timestamp):
    """Context manager to freeze time for testing."""
    
def advance_time(hours=0, days=0):
    """Advance frozen time by specified duration."""
    
def set_timezone(tz):
    """Set timezone for test execution."""
```

### Coverage Gaps
- Complex scheduling patterns
- Daylight saving time transitions
- Historical data freshness
- Cascading freshness dependencies

### Related Documentation
- Freshness dimension details: [freshness_dimension.md](freshness_dimension.md)
- Rules framework: [RULES_test_coverage.md](RULES_test_coverage.md)
- Dimensions overview: [DIMENSIONS_test_coverage.md](DIMENSIONS_test_coverage.md)

---
*Last Updated: 2025-06-03*
