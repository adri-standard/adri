# CONNECTORS Test Coverage

This document tracks test coverage for the ADRI connectors module, which provides interfaces for connecting to various data sources.

## Purpose
The connectors module provides a pluggable architecture for accessing data from:
- Files (CSV, JSON, XML, Parquet, Excel)
- Databases (PostgreSQL, MySQL, SQLite, MongoDB)
- APIs (REST, GraphQL)
- Custom data sources

## Test Coverage

### adri/connectors/base.py
- **Unit Tests**: `tests/unit/connectors/test_base.py`
  - ✅ Tests BaseConnector abstract interface
  - ✅ Tests connection lifecycle
  - ✅ Tests metadata extraction
  - ✅ Tests error handling

### adri/connectors/file.py
- **Unit Tests**: `tests/unit/connectors/test_file_connector.py`
  - ✅ Tests CSV file reading
  - ✅ Tests JSON file parsing
  - ✅ Tests XML file handling
  - ✅ Tests Parquet file support
  - ✅ Tests Excel file processing
  - ✅ Tests file metadata extraction
  
- **Integration Tests**: `tests/integration/test_file_connector_integration.py`
  - ✅ Tests with real files
  - ✅ Tests large file handling
  - ✅ Tests encoding detection
  - ✅ Tests malformed file handling

### adri/connectors/database.py
- **Unit Tests**: `tests/unit/connectors/test_database_connector.py`
  - ✅ Tests connection string parsing
  - ✅ Tests query execution
  - ✅ Tests schema inspection
  - ✅ Tests transaction handling
  
- **Integration Tests**: `tests/integration/test_database_connector_integration.py`
  - ✅ Tests PostgreSQL connections
  - ✅ Tests MySQL connections
  - ✅ Tests SQLite connections
  - ✅ Tests connection pooling

### adri/connectors/api.py
- **Unit Tests**: `tests/unit/connectors/test_api_connector.py`
  - ✅ Tests REST API calls
  - ✅ Tests authentication methods
  - ✅ Tests pagination handling
  - ✅ Tests response parsing
  - ✅ Tests rate limiting
  
- **Integration Tests**: `tests/integration/test_api_connector_integration.py`
  - ✅ Tests with mock API server
  - ✅ Tests retry logic
  - ✅ Tests timeout handling
  - ✅ Tests error responses

### adri/connectors/registry.py
- **Unit Tests**: `tests/unit/connectors/test_registry.py`
  - ✅ Tests connector registration
  - ✅ Tests connector discovery
  - ✅ Tests automatic connector selection
  - ✅ Tests custom connector plugins

### Key Features Tested

| Feature | Test Type | Coverage |
|---------|-----------|----------|
| Base connector interface | Unit | ✅ Complete |
| File connectors | Unit + Integration | ✅ Complete |
| Database connectors | Unit + Integration | ✅ Complete |
| API connectors | Unit + Integration | ✅ Complete |
| Connector registry | Unit | ✅ Complete |
| Error handling | Unit | ✅ Complete |
| Metadata extraction | Unit | ✅ Complete |
| Authentication | Unit + Integration | ✅ Complete |

### Test Statistics
- **Total Tests**: 98
- **Passing**: 98
- **Coverage**: 88%

### Example Test Cases

```python
def test_csv_connector_read():
    """Test CSV connector can read and parse CSV files."""
    connector = FileConnector("test_data.csv")
    data = connector.read()
    assert len(data) > 0
    assert "column1" in data.columns

def test_database_connector_query():
    """Test database connector can execute queries."""
    connector = DatabaseConnector("postgresql://localhost/testdb")
    result = connector.query("SELECT * FROM users LIMIT 10")
    assert len(result) <= 10
    assert result.columns is not None

def test_api_connector_pagination():
    """Test API connector handles pagination correctly."""
    connector = APIConnector("https://api.example.com")
    all_data = connector.fetch_all("/users", page_size=50)
    assert len(all_data) > 50  # Ensures pagination worked
```

### Connector Configuration

Connectors can be configured through YAML:

```yaml
connectors:
  file:
    encoding: utf-8
    chunk_size: 10000
    
  database:
    pool_size: 10
    timeout: 30
    
  api:
    rate_limit: 100
    retry_count: 3
    timeout: 60
```

### Coverage Gaps
- Streaming large datasets
- Advanced authentication methods (OAuth2, SAML)
- Real-time data sources
- Binary file formats

### Dependencies
This module is used by:
- Core assessor (see CORE_test_coverage.md)
- Integration tests across all modules

---
*Last Updated: 2025-06-03*
