"""
Comprehensive tests for adri.core.boundary module.

This test suite provides extensive coverage for the component boundary system,
including enums, protocols, abstract classes, and the ComponentBoundary manager.
"""

import pytest
from unittest.mock import MagicMock, patch
from abc import ABC
from dataclasses import dataclass
from typing import Any, Dict, Optional

from adri.core.boundary import (
    IntegrationType,
    DataFormat,
    IntegrationConfig,
    ExternalIntegration,
    DataProvider,
    AuditSink,
    ComponentBoundary,
    get_boundary_manager,
    StandaloneMode,
    validate_standalone_operation,
)


class TestEnums:
    """Test enum classes."""

    def test_integration_type_enum(self):
        """Test IntegrationType enum values."""
        assert IntegrationType.AUDIT_LOGGER.value == "audit_logger"
        assert IntegrationType.DATA_SOURCE.value == "data_source"
        assert IntegrationType.NOTIFICATION.value == "notification"
        assert IntegrationType.MONITORING.value == "monitoring"
        assert IntegrationType.CUSTOM.value == "custom"

    def test_data_format_enum(self):
        """Test DataFormat enum values."""
        assert DataFormat.JSON.value == "json"
        assert DataFormat.CSV.value == "csv"
        assert DataFormat.PARQUET.value == "parquet"
        assert DataFormat.YAML.value == "yaml"
        assert DataFormat.DICT.value == "dict"


class TestIntegrationConfig:
    """Test IntegrationConfig dataclass."""

    def test_integration_config_creation(self):
        """Test creating IntegrationConfig with required fields."""
        config = IntegrationConfig(
            integration_type=IntegrationType.AUDIT_LOGGER,
            enabled=True,
            config={"endpoint": "http://example.com"}
        )
        
        assert config.integration_type == IntegrationType.AUDIT_LOGGER
        assert config.enabled is True
        assert config.config == {"endpoint": "http://example.com"}
        assert config.data_format == DataFormat.JSON  # default
        assert config.timeout_seconds == 30  # default
        assert config.retry_count == 3  # default
        assert config.batch_size == 100  # default

    def test_integration_config_with_custom_values(self):
        """Test creating IntegrationConfig with custom values."""
        config = IntegrationConfig(
            integration_type=IntegrationType.MONITORING,
            enabled=False,
            config={"url": "http://monitor.com"},
            data_format=DataFormat.CSV,
            timeout_seconds=60,
            retry_count=5,
            batch_size=200
        )
        
        assert config.integration_type == IntegrationType.MONITORING
        assert config.enabled is False
        assert config.data_format == DataFormat.CSV
        assert config.timeout_seconds == 60
        assert config.retry_count == 5
        assert config.batch_size == 200


class MockExternalIntegration(ExternalIntegration):
    """Mock implementation of ExternalIntegration for testing."""
    
    def __init__(self, should_succeed=True):
        self.should_succeed = should_succeed
        self.initialized = False
        self.data_sent = []
        self.health_status = True
        self.shutdown_called = False

    def initialize(self, config: IntegrationConfig) -> bool:
        self.initialized = self.should_succeed
        return self.should_succeed

    def send_data(self, data: Any, format: DataFormat) -> bool:
        if self.should_succeed:
            self.data_sent.append((data, format))
        return self.should_succeed

    def receive_data(self, format: DataFormat) -> Optional[Any]:
        if self.should_succeed:
            return {"test": "data"}
        return None

    def health_check(self) -> bool:
        return self.health_status

    def shutdown(self) -> bool:
        self.shutdown_called = True
        return self.should_succeed


class MockDataProvider:
    """Mock implementation of DataProvider protocol."""
    
    def __init__(self, should_succeed=True):
        self.should_succeed = should_succeed

    def get_data(self) -> Any:
        return {"mock": "data"} if self.should_succeed else None

    def get_metadata(self) -> Dict[str, Any]:
        return {"source": "mock"} if self.should_succeed else {}

    def validate_schema(self) -> bool:
        return self.should_succeed


class MockAuditSink:
    """Mock implementation of AuditSink protocol."""
    
    def __init__(self, should_succeed=True):
        self.should_succeed = should_succeed
        self.records = []
        self.flushed = False
        self.closed = False

    def write_record(self, record: Dict[str, Any]) -> bool:
        if self.should_succeed:
            self.records.append(record)
        return self.should_succeed

    def flush(self) -> bool:
        self.flushed = True
        return self.should_succeed

    def close(self) -> bool:
        self.closed = True
        return self.should_succeed


class TestExternalIntegration:
    """Test ExternalIntegration abstract base class."""

    def test_external_integration_is_abstract(self):
        """Test that ExternalIntegration cannot be instantiated directly."""
        with pytest.raises(TypeError):
            ExternalIntegration()

    def test_mock_implementation_works(self):
        """Test that our mock implementation works correctly."""
        integration = MockExternalIntegration()
        config = IntegrationConfig(
            integration_type=IntegrationType.CUSTOM,
            enabled=True,
            config={}
        )
        
        assert integration.initialize(config) is True
        assert integration.send_data("test", DataFormat.JSON) is True
        assert integration.receive_data(DataFormat.JSON) == {"test": "data"}
        assert integration.health_check() is True
        assert integration.shutdown() is True


class TestProtocols:
    """Test protocol implementations."""

    def test_data_provider_protocol(self):
        """Test DataProvider protocol implementation."""
        provider = MockDataProvider()
        
        # Test successful operations
        assert provider.get_data() == {"mock": "data"}
        assert provider.get_metadata() == {"source": "mock"}
        assert provider.validate_schema() is True

    def test_audit_sink_protocol(self):
        """Test AuditSink protocol implementation."""
        sink = MockAuditSink()
        
        # Test successful operations
        assert sink.write_record({"test": "record"}) is True
        assert sink.flush() is True
        assert sink.close() is True
        assert sink.records == [{"test": "record"}]


class TestComponentBoundary:
    """Test ComponentBoundary class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.boundary = ComponentBoundary()

    def test_component_boundary_initialization(self):
        """Test ComponentBoundary initialization."""
        assert len(self.boundary._integrations) == 0
        assert len(self.boundary._data_providers) == 0
        assert len(self.boundary._audit_sinks) == 0

    def test_register_integration_success(self):
        """Test successful integration registration."""
        integration = MockExternalIntegration(should_succeed=True)
        config = IntegrationConfig(
            integration_type=IntegrationType.CUSTOM,
            enabled=True,
            config={}
        )
        
        result = self.boundary.register_integration("test", integration, config)
        assert result is True
        assert "test" in self.boundary._integrations
        assert integration.initialized is True

    def test_register_integration_failure(self):
        """Test integration registration failure."""
        integration = MockExternalIntegration(should_succeed=False)
        config = IntegrationConfig(
            integration_type=IntegrationType.CUSTOM,
            enabled=True,
            config={}
        )
        
        result = self.boundary.register_integration("test", integration, config)
        assert result is False
        assert "test" not in self.boundary._integrations

    def test_register_integration_exception(self):
        """Test integration registration with exception."""
        integration = MagicMock()
        integration.initialize.side_effect = Exception("Test error")
        config = IntegrationConfig(
            integration_type=IntegrationType.CUSTOM,
            enabled=True,
            config={}
        )
        
        result = self.boundary.register_integration("test", integration, config)
        assert result is False

    def test_register_data_provider_success(self):
        """Test successful data provider registration."""
        provider = MockDataProvider()
        
        result = self.boundary.register_data_provider("test", provider)
        assert result is True
        assert "test" in self.boundary._data_providers

    def test_register_data_provider_invalid_protocol(self):
        """Test data provider registration with invalid protocol."""
        invalid_provider = MagicMock()
        # Remove required methods to make it invalid
        del invalid_provider.get_data
        
        result = self.boundary.register_data_provider("test", invalid_provider)
        assert result is False

    def test_register_data_provider_exception(self):
        """Test data provider registration with exception."""
        provider = MagicMock()
        # Make hasattr raise an exception
        with patch('builtins.hasattr', side_effect=Exception("Test error")):
            result = self.boundary.register_data_provider("test", provider)
            assert result is False

    def test_register_audit_sink_success(self):
        """Test successful audit sink registration."""
        sink = MockAuditSink()
        
        result = self.boundary.register_audit_sink("test", sink)
        assert result is True
        assert "test" in self.boundary._audit_sinks

    def test_register_audit_sink_invalid_protocol(self):
        """Test audit sink registration with invalid protocol."""
        invalid_sink = MagicMock()
        # Remove required methods to make it invalid
        del invalid_sink.write_record
        
        result = self.boundary.register_audit_sink("test", invalid_sink)
        assert result is False

    def test_register_audit_sink_exception(self):
        """Test audit sink registration with exception."""
        sink = MagicMock()
        # Make hasattr raise an exception
        with patch('builtins.hasattr', side_effect=Exception("Test error")):
            result = self.boundary.register_audit_sink("test", sink)
            assert result is False

    def test_get_integration(self):
        """Test getting registered integration."""
        integration = MockExternalIntegration()
        config = IntegrationConfig(
            integration_type=IntegrationType.CUSTOM,
            enabled=True,
            config={}
        )
        
        self.boundary.register_integration("test", integration, config)
        
        retrieved = self.boundary.get_integration("test")
        assert retrieved is integration
        
        # Test non-existent integration
        assert self.boundary.get_integration("nonexistent") is None

    def test_get_data_provider(self):
        """Test getting registered data provider."""
        provider = MockDataProvider()
        self.boundary.register_data_provider("test", provider)
        
        retrieved = self.boundary.get_data_provider("test")
        assert retrieved is provider
        
        # Test non-existent provider
        assert self.boundary.get_data_provider("nonexistent") is None

    def test_get_audit_sink(self):
        """Test getting registered audit sink."""
        sink = MockAuditSink()
        self.boundary.register_audit_sink("test", sink)
        
        retrieved = self.boundary.get_audit_sink("test")
        assert retrieved is sink
        
        # Test non-existent sink
        assert self.boundary.get_audit_sink("nonexistent") is None

    def test_list_integrations(self):
        """Test listing integration names."""
        integration1 = MockExternalIntegration()
        integration2 = MockExternalIntegration()
        config = IntegrationConfig(
            integration_type=IntegrationType.CUSTOM,
            enabled=True,
            config={}
        )
        
        self.boundary.register_integration("test1", integration1, config)
        self.boundary.register_integration("test2", integration2, config)
        
        names = self.boundary.list_integrations()
        assert "test1" in names
        assert "test2" in names
        assert len(names) == 2

    def test_list_data_providers(self):
        """Test listing data provider names."""
        provider1 = MockDataProvider()
        provider2 = MockDataProvider()
        
        self.boundary.register_data_provider("test1", provider1)
        self.boundary.register_data_provider("test2", provider2)
        
        names = self.boundary.list_data_providers()
        assert "test1" in names
        assert "test2" in names
        assert len(names) == 2

    def test_list_audit_sinks(self):
        """Test listing audit sink names."""
        sink1 = MockAuditSink()
        sink2 = MockAuditSink()
        
        self.boundary.register_audit_sink("test1", sink1)
        self.boundary.register_audit_sink("test2", sink2)
        
        names = self.boundary.list_audit_sinks()
        assert "test1" in names
        assert "test2" in names
        assert len(names) == 2

    def test_health_check(self):
        """Test health check functionality."""
        integration1 = MockExternalIntegration()
        integration1.health_status = True
        integration2 = MockExternalIntegration()
        integration2.health_status = False
        
        config = IntegrationConfig(
            integration_type=IntegrationType.CUSTOM,
            enabled=True,
            config={}
        )
        
        self.boundary.register_integration("healthy", integration1, config)
        self.boundary.register_integration("unhealthy", integration2, config)
        
        results = self.boundary.health_check()
        assert results["healthy"] is True
        assert results["unhealthy"] is False

    def test_health_check_with_exception(self):
        """Test health check with exception."""
        integration = MagicMock()
        integration.health_check.side_effect = Exception("Health check failed")
        
        self.boundary._integrations["error"] = integration
        
        results = self.boundary.health_check()
        assert results["error"] is False

    def test_shutdown_all_success(self):
        """Test successful shutdown of all components."""
        integration = MockExternalIntegration()
        sink = MockAuditSink()
        
        config = IntegrationConfig(
            integration_type=IntegrationType.CUSTOM,
            enabled=True,
            config={}
        )
        
        self.boundary.register_integration("test", integration, config)
        self.boundary.register_audit_sink("test", sink)
        
        result = self.boundary.shutdown_all()
        assert result is True
        assert integration.shutdown_called is True
        assert sink.flushed is True
        assert sink.closed is True
        
        # All registrations should be cleared
        assert len(self.boundary._integrations) == 0
        assert len(self.boundary._audit_sinks) == 0

    def test_shutdown_all_with_failures(self):
        """Test shutdown with some failures."""
        integration = MockExternalIntegration(should_succeed=False)
        sink = MockAuditSink(should_succeed=False)
        
        config = IntegrationConfig(
            integration_type=IntegrationType.CUSTOM,
            enabled=True,
            config={}
        )
        
        self.boundary.register_integration("test", integration, config)
        self.boundary.register_audit_sink("test", sink)
        
        result = self.boundary.shutdown_all()
        assert result is False  # Should fail due to integration/sink failures

    def test_shutdown_all_with_exceptions(self):
        """Test shutdown with exceptions."""
        integration = MagicMock()
        integration.shutdown.side_effect = Exception("Shutdown error")
        sink = MagicMock()
        sink.flush.side_effect = Exception("Flush error")
        
        self.boundary._integrations["test"] = integration
        self.boundary._audit_sinks["test"] = sink
        
        result = self.boundary.shutdown_all()
        assert result is False


class TestSingletonManager:
    """Test singleton boundary manager."""

    def test_get_boundary_manager_singleton(self):
        """Test that get_boundary_manager returns the same instance."""
        manager1 = get_boundary_manager()
        manager2 = get_boundary_manager()
        
        assert manager1 is manager2
        assert isinstance(manager1, ComponentBoundary)


class TestStandaloneMode:
    """Test StandaloneMode context manager."""

    def test_standalone_mode_context(self):
        """Test StandaloneMode context manager functionality."""
        boundary = get_boundary_manager()
        
        # Add a test integration
        integration = MockExternalIntegration()
        config = IntegrationConfig(
            integration_type=IntegrationType.CUSTOM,
            enabled=True,
            config={}
        )
        boundary.register_integration("test", integration, config)
        
        # Verify integration is registered
        assert len(boundary.list_integrations()) == 1
        
        # Enter standalone mode
        with StandaloneMode():
            # Integration should be temporarily removed
            assert len(boundary.list_integrations()) == 0
        
        # Integration should be restored after exiting
        assert len(boundary.list_integrations()) == 1

    def test_standalone_mode_initialization(self):
        """Test StandaloneMode initialization."""
        standalone = StandaloneMode()
        assert standalone._original_integrations == {}
        assert standalone._boundary is get_boundary_manager()

    def test_standalone_mode_with_exception(self):
        """Test StandaloneMode with exception during context."""
        boundary = get_boundary_manager()
        
        # Clean up any existing integrations
        boundary.shutdown_all()
        
        # Add a test integration
        integration = MockExternalIntegration()
        config = IntegrationConfig(
            integration_type=IntegrationType.CUSTOM,
            enabled=True,
            config={}
        )
        boundary.register_integration("test", integration, config)
        
        try:
            with StandaloneMode():
                assert len(boundary.list_integrations()) == 0
                raise ValueError("Test exception")
        except ValueError:
            pass
        
        # Integration should still be restored after exception
        assert len(boundary.list_integrations()) == 1


class TestValidateStandaloneOperation:
    """Test validate_standalone_operation function."""

    def test_validate_standalone_operation_success(self):
        """Test successful standalone operation validation."""
        # This should succeed with the current setup
        result = validate_standalone_operation()
        assert result is True

    @patch('adri.standards.loader.StandardsLoader')
    def test_validate_standalone_operation_no_standards(self, mock_loader_class):
        """Test validation failure when no standards available."""
        mock_loader = MagicMock()
        mock_loader.list_available_standards.return_value = []
        mock_loader_class.return_value = mock_loader
        
        result = validate_standalone_operation()
        assert result is False

    @patch('adri.standards.loader.StandardsLoader')
    def test_validate_standalone_operation_exception(self, mock_loader_class):
        """Test validation failure with exception."""
        mock_loader_class.side_effect = Exception("Import error")
        
        result = validate_standalone_operation()
        assert result is False

    def test_validate_standalone_operation_with_active_integrations(self):
        """Test validation with active integrations in standalone mode."""
        boundary = get_boundary_manager()
        
        # Clean up first
        boundary.shutdown_all()
        
        # Add an integration that should be removed in standalone mode
        integration = MockExternalIntegration()
        config = IntegrationConfig(
            integration_type=IntegrationType.CUSTOM,
            enabled=True,
            config={}
        )
        boundary.register_integration("test", integration, config)
        
        # Validation should still succeed because StandaloneMode removes integrations
        result = validate_standalone_operation()
        assert result is True
        
        # Clean up
        boundary.shutdown_all()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
