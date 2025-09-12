"""
Unit tests for boundary.py - Core component boundary management.

Tests the critical infrastructure for external integrations, standalone mode,
and component boundary definitions.
"""

import unittest
from unittest.mock import Mock, patch

from adri.core.boundary import (
    AuditSink,
    ComponentBoundary,
    DataFormat,
    DataProvider,
    ExternalIntegration,
    IntegrationConfig,
    IntegrationType,
    StandaloneMode,
    get_boundary_manager,
    validate_standalone_operation,
)


class MockIntegration(ExternalIntegration):
    """Mock integration for testing."""

    def __init__(self, should_succeed: bool = True):
        self.should_succeed = should_succeed
        self.initialized = False
        self.shutdown_called = False

    def initialize(self, config: IntegrationConfig) -> bool:
        if self.should_succeed:
            self.initialized = True
        return self.should_succeed

    def send_data(self, data, format: DataFormat) -> bool:
        return self.should_succeed

    def receive_data(self, format: DataFormat):
        return {"test": "data"} if self.should_succeed else None

    def health_check(self) -> bool:
        return self.should_succeed and self.initialized

    def shutdown(self) -> bool:
        self.shutdown_called = True
        return self.should_succeed


class MockDataProvider:
    """Mock data provider for testing."""

    def get_data(self):
        return {"sample": "data"}

    def get_metadata(self):
        return {"rows": 100, "columns": 5}

    def validate_schema(self) -> bool:
        return True


class MockAuditSink:
    """Mock audit sink for testing."""

    def __init__(self):
        self.records = []
        self.flushed = False
        self.closed = False

    def write_record(self, record) -> bool:
        self.records.append(record)
        return True

    def flush(self) -> bool:
        self.flushed = True
        return True

    def close(self) -> bool:
        self.closed = True
        return True


class TestIntegrationType(unittest.TestCase):
    """Test IntegrationType enum."""

    def test_integration_types_defined(self):
        """Test that all expected integration types are defined."""
        expected_types = [
            "AUDIT_LOGGER",
            "DATA_SOURCE",
            "NOTIFICATION",
            "MONITORING",
            "CUSTOM"
        ]

        for type_name in expected_types:
            self.assertTrue(hasattr(IntegrationType, type_name))

    def test_integration_type_values(self):
        """Test integration type values."""
        self.assertEqual(IntegrationType.AUDIT_LOGGER.value, "audit_logger")
        self.assertEqual(IntegrationType.DATA_SOURCE.value, "data_source")
        self.assertEqual(IntegrationType.NOTIFICATION.value, "notification")
        self.assertEqual(IntegrationType.MONITORING.value, "monitoring")
        self.assertEqual(IntegrationType.CUSTOM.value, "custom")


class TestDataFormat(unittest.TestCase):
    """Test DataFormat enum."""

    def test_data_formats_defined(self):
        """Test that all expected data formats are defined."""
        expected_formats = ["JSON", "CSV", "PARQUET", "YAML", "DICT"]

        for format_name in expected_formats:
            self.assertTrue(hasattr(DataFormat, format_name))

    def test_data_format_values(self):
        """Test data format values."""
        self.assertEqual(DataFormat.JSON.value, "json")
        self.assertEqual(DataFormat.CSV.value, "csv")
        self.assertEqual(DataFormat.PARQUET.value, "parquet")
        self.assertEqual(DataFormat.YAML.value, "yaml")
        self.assertEqual(DataFormat.DICT.value, "dict")


class TestIntegrationConfig(unittest.TestCase):
    """Test IntegrationConfig dataclass."""

    def test_integration_config_creation(self):
        """Test creating integration config with required fields."""
        config = IntegrationConfig(
            integration_type=IntegrationType.AUDIT_LOGGER,
            enabled=True,
            config={"test": "value"}
        )

        self.assertEqual(config.integration_type, IntegrationType.AUDIT_LOGGER)
        self.assertTrue(config.enabled)
        self.assertEqual(config.config, {"test": "value"})
        self.assertEqual(config.data_format, DataFormat.JSON)  # Default
        self.assertEqual(config.timeout_seconds, 30)  # Default
        self.assertEqual(config.retry_count, 3)  # Default
        self.assertEqual(config.batch_size, 100)  # Default

    def test_integration_config_with_overrides(self):
        """Test integration config with all fields specified."""
        config = IntegrationConfig(
            integration_type=IntegrationType.MONITORING,
            enabled=False,
            config={"url": "http://test.com"},
            data_format=DataFormat.CSV,
            timeout_seconds=60,
            retry_count=5,
            batch_size=200
        )

        self.assertEqual(config.integration_type, IntegrationType.MONITORING)
        self.assertFalse(config.enabled)
        self.assertEqual(config.data_format, DataFormat.CSV)
        self.assertEqual(config.timeout_seconds, 60)
        self.assertEqual(config.retry_count, 5)
        self.assertEqual(config.batch_size, 200)


class TestComponentBoundary(unittest.TestCase):
    """Test ComponentBoundary class."""

    def setUp(self):
        """Set up test fixtures."""
        self.boundary = ComponentBoundary()
        self.mock_integration = MockIntegration(should_succeed=True)
        self.mock_provider = MockDataProvider()
        self.mock_sink = MockAuditSink()

    def test_boundary_initialization(self):
        """Test boundary manager initialization."""
        self.assertEqual(len(self.boundary.list_integrations()), 0)
        self.assertEqual(len(self.boundary.list_data_providers()), 0)
        self.assertEqual(len(self.boundary.list_audit_sinks()), 0)

    def test_register_integration_success(self):
        """Test successful integration registration."""
        config = IntegrationConfig(
            integration_type=IntegrationType.AUDIT_LOGGER,
            enabled=True,
            config={"test": "config"}
        )

        result = self.boundary.register_integration(
            "test_integration", self.mock_integration, config
        )

        self.assertTrue(result)
        self.assertTrue(self.mock_integration.initialized)
        self.assertIn("test_integration", self.boundary.list_integrations())

    def test_register_integration_failure(self):
        """Test integration registration failure."""
        failing_integration = MockIntegration(should_succeed=False)
        config = IntegrationConfig(
            integration_type=IntegrationType.AUDIT_LOGGER,
            enabled=True,
            config={}
        )

        result = self.boundary.register_integration(
            "failing_integration", failing_integration, config
        )

        self.assertFalse(result)
        self.assertNotIn("failing_integration", self.boundary.list_integrations())

    def test_register_data_provider_success(self):
        """Test successful data provider registration."""
        result = self.boundary.register_data_provider("test_provider", self.mock_provider)

        self.assertTrue(result)
        self.assertIn("test_provider", self.boundary.list_data_providers())

    def test_register_data_provider_invalid(self):
        """Test data provider registration with invalid provider."""
        invalid_provider = object()  # Doesn't implement protocol

        result = self.boundary.register_data_provider("invalid_provider", invalid_provider)

        self.assertFalse(result)
        self.assertNotIn("invalid_provider", self.boundary.list_data_providers())

    def test_register_audit_sink_success(self):
        """Test successful audit sink registration."""
        result = self.boundary.register_audit_sink("test_sink", self.mock_sink)

        self.assertTrue(result)
        self.assertIn("test_sink", self.boundary.list_audit_sinks())

    def test_register_audit_sink_invalid(self):
        """Test audit sink registration with invalid sink."""
        invalid_sink = object()  # Doesn't implement protocol

        result = self.boundary.register_audit_sink("invalid_sink", invalid_sink)

        self.assertFalse(result)
        self.assertNotIn("invalid_sink", self.boundary.list_audit_sinks())

    def test_get_registered_components(self):
        """Test retrieving registered components."""
        # Register components
        config = IntegrationConfig(
            integration_type=IntegrationType.CUSTOM,
            enabled=True,
            config={}
        )

        self.boundary.register_integration("test_integration", self.mock_integration, config)
        self.boundary.register_data_provider("test_provider", self.mock_provider)
        self.boundary.register_audit_sink("test_sink", self.mock_sink)

        # Test retrieval
        self.assertEqual(
            self.boundary.get_integration("test_integration"), self.mock_integration
        )
        self.assertEqual(
            self.boundary.get_data_provider("test_provider"), self.mock_provider
        )
        self.assertEqual(
            self.boundary.get_audit_sink("test_sink"), self.mock_sink
        )

    def test_get_nonexistent_components(self):
        """Test retrieving non-existent components."""
        self.assertIsNone(self.boundary.get_integration("nonexistent"))
        self.assertIsNone(self.boundary.get_data_provider("nonexistent"))
        self.assertIsNone(self.boundary.get_audit_sink("nonexistent"))

    def test_health_check(self):
        """Test health check functionality."""
        config = IntegrationConfig(
            integration_type=IntegrationType.MONITORING,
            enabled=True,
            config={}
        )

        # Register healthy integration
        healthy_integration = MockIntegration(should_succeed=True)
        self.boundary.register_integration("healthy", healthy_integration, config)

        # Create unhealthy integration manually for health check test
        unhealthy_integration = MockIntegration(should_succeed=True)
        # Register first (so it initializes), then make health check fail
        registration_result = self.boundary.register_integration("unhealthy", unhealthy_integration, config)
        self.assertTrue(registration_result)  # Should register successfully

        # Now change the behavior to make health check fail
        unhealthy_integration.should_succeed = False

        results = self.boundary.health_check()

        self.assertTrue(results["healthy"])
        self.assertFalse(results["unhealthy"])

    def test_health_check_exception_handling(self):
        """Test health check with exception-throwing integration."""
        config = IntegrationConfig(
            integration_type=IntegrationType.CUSTOM,
            enabled=True,
            config={}
        )

        # Create integration that throws on health check
        exception_integration = Mock(spec=ExternalIntegration)
        exception_integration.initialize.return_value = True
        exception_integration.health_check.side_effect = Exception("Test error")

        self.boundary.register_integration("exception_integration", exception_integration, config)

        results = self.boundary.health_check()
        self.assertFalse(results["exception_integration"])

    def test_shutdown_all_success(self):
        """Test successful shutdown of all components."""
        config = IntegrationConfig(
            integration_type=IntegrationType.AUDIT_LOGGER,
            enabled=True,
            config={}
        )

        # Register components
        self.boundary.register_integration("test_integration", self.mock_integration, config)
        self.boundary.register_audit_sink("test_sink", self.mock_sink)

        result = self.boundary.shutdown_all()

        self.assertTrue(result)
        self.assertTrue(self.mock_integration.shutdown_called)
        self.assertTrue(self.mock_sink.flushed)
        self.assertTrue(self.mock_sink.closed)

        # All registrations should be cleared
        self.assertEqual(len(self.boundary.list_integrations()), 0)
        self.assertEqual(len(self.boundary.list_data_providers()), 0)
        self.assertEqual(len(self.boundary.list_audit_sinks()), 0)

    def test_shutdown_all_with_failures(self):
        """Test shutdown with some component failures."""
        config = IntegrationConfig(
            integration_type=IntegrationType.AUDIT_LOGGER,
            enabled=True,
            config={}
        )

        # Register integration that will fail on shutdown
        failing_integration = MockIntegration(should_succeed=True)
        # Initialize successfully but make shutdown fail
        self.boundary.register_integration("failing", failing_integration, config)
        failing_integration.should_succeed = False  # Make shutdown fail

        result = self.boundary.shutdown_all()

        # Should return False due to shutdown failure
        self.assertFalse(result)
        # But still clear registrations
        self.assertEqual(len(self.boundary.list_integrations()), 0)


class TestStandaloneMode(unittest.TestCase):
    """Test StandaloneMode context manager."""

    def setUp(self):
        """Set up test fixtures."""
        self.boundary = get_boundary_manager()
        # Clear any existing registrations
        self.boundary.shutdown_all()

    def test_standalone_mode_context_manager(self):
        """Test standalone mode context manager behavior."""
        # Register an integration first
        integration = MockIntegration()
        config = IntegrationConfig(
            integration_type=IntegrationType.CUSTOM,
            enabled=True,
            config={}
        )

        self.boundary.register_integration("test", integration, config)
        self.assertEqual(len(self.boundary.list_integrations()), 1)

        # Enter standalone mode
        with StandaloneMode():
            # Integration should be temporarily removed
            self.assertEqual(len(self.boundary.list_integrations()), 0)

        # Integration should be restored after exiting context
        self.assertEqual(len(self.boundary.list_integrations()), 1)

    def test_standalone_mode_with_exception(self):
        """Test standalone mode handles exceptions properly."""
        # Register an integration
        integration = MockIntegration()
        config = IntegrationConfig(
            integration_type=IntegrationType.AUDIT_LOGGER,
            enabled=True,
            config={}
        )

        self.boundary.register_integration("test", integration, config)

        try:
            with StandaloneMode():
                # Even if exception occurs, integrations should be restored
                raise ValueError("Test exception")
        except ValueError:
            pass

        # Integration should still be restored
        self.assertEqual(len(self.boundary.list_integrations()), 1)

    def test_standalone_mode_empty_boundary(self):
        """Test standalone mode with no registered integrations."""
        self.assertEqual(len(self.boundary.list_integrations()), 0)

        with StandaloneMode():
            self.assertEqual(len(self.boundary.list_integrations()), 0)

        self.assertEqual(len(self.boundary.list_integrations()), 0)


class TestGlobalBoundaryManager(unittest.TestCase):
    """Test global boundary manager functionality."""

    def test_get_boundary_manager_singleton(self):
        """Test that get_boundary_manager returns singleton."""
        manager1 = get_boundary_manager()
        manager2 = get_boundary_manager()

        self.assertIs(manager1, manager2)

    def test_boundary_manager_is_component_boundary(self):
        """Test that boundary manager is ComponentBoundary instance."""
        manager = get_boundary_manager()
        self.assertIsInstance(manager, ComponentBoundary)


class TestValidateStandaloneOperation(unittest.TestCase):
    """Test standalone operation validation."""

    @patch('adri.standards.loader.StandardsLoader')
    def test_validate_standalone_operation_success(self, mock_loader_class):
        """Test successful standalone operation validation."""
        # Mock the standards loader
        mock_loader = Mock()
        mock_loader.list_available_standards.return_value = ["standard1", "standard2"]
        mock_loader_class.return_value = mock_loader

        # Clear any existing integrations
        boundary = get_boundary_manager()
        boundary.shutdown_all()

        result = validate_standalone_operation()

        self.assertTrue(result)

    @patch('adri.standards.loader.StandardsLoader')
    def test_validate_standalone_operation_no_standards(self, mock_loader_class):
        """Test standalone operation validation with no standards."""
        # Mock loader with no standards
        mock_loader = Mock()
        mock_loader.list_available_standards.return_value = []
        mock_loader_class.return_value = mock_loader

        result = validate_standalone_operation()

        self.assertFalse(result)

    @patch('adri.standards.loader.StandardsLoader')
    def test_validate_standalone_operation_with_active_integrations(self, mock_loader_class):
        """Test standalone validation succeeds in standalone mode."""
        # Setup loader to succeed
        mock_loader = Mock()
        mock_loader.list_available_standards.return_value = ["standard1"]
        mock_loader_class.return_value = mock_loader

        # Register an integration
        boundary = get_boundary_manager()
        boundary.shutdown_all()  # Clear first

        integration = MockIntegration()
        config = IntegrationConfig(
            integration_type=IntegrationType.MONITORING,
            enabled=True,
            config={}
        )
        boundary.register_integration("test", integration, config)

        with StandaloneMode():
            result = validate_standalone_operation()
            # Should succeed in standalone mode
            self.assertTrue(result)

    @patch('adri.standards.loader.StandardsLoader')
    def test_validate_standalone_operation_exception(self, mock_loader_class):
        """Test standalone operation validation with exception."""
        # Make loader throw exception during import/instantiation
        mock_loader_class.side_effect = ImportError("Module not found")

        result = validate_standalone_operation()

        # Should fail gracefully when import fails
        self.assertFalse(result)


class TestExternalIntegrationProtocol(unittest.TestCase):
    """Test that ExternalIntegration protocol works correctly."""

    def test_mock_integration_implements_protocol(self):
        """Test that our mock integration implements the protocol."""
        integration = MockIntegration()
        config = IntegrationConfig(
            integration_type=IntegrationType.CUSTOM,
            enabled=True,
            config={}
        )

        # All protocol methods should be callable
        self.assertTrue(integration.initialize(config))
        self.assertTrue(integration.send_data("test", DataFormat.JSON))
        self.assertIsNotNone(integration.receive_data(DataFormat.JSON))
        self.assertTrue(integration.health_check())
        self.assertTrue(integration.shutdown())


class TestDataProviderProtocol(unittest.TestCase):
    """Test DataProvider protocol."""

    def test_mock_provider_implements_protocol(self):
        """Test that our mock provider implements the protocol."""
        provider = MockDataProvider()

        # All protocol methods should be callable
        data = provider.get_data()
        metadata = provider.get_metadata()
        valid = provider.validate_schema()

        self.assertIsNotNone(data)
        self.assertIsNotNone(metadata)
        self.assertTrue(valid)


class TestAuditSinkProtocol(unittest.TestCase):
    """Test AuditSink protocol."""

    def test_mock_sink_implements_protocol(self):
        """Test that our mock sink implements the protocol."""
        sink = MockAuditSink()

        # All protocol methods should be callable
        result1 = sink.write_record({"test": "record"})
        result2 = sink.flush()
        result3 = sink.close()

        self.assertTrue(result1)
        self.assertTrue(result2)
        self.assertTrue(result3)
        self.assertEqual(len(sink.records), 1)
        self.assertTrue(sink.flushed)
        self.assertTrue(sink.closed)


class TestBoundaryIntegration(unittest.TestCase):
    """Test integrated boundary functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.boundary = ComponentBoundary()

    def test_complete_boundary_workflow(self):
        """Test complete workflow with all component types."""
        # Register all component types
        integration = MockIntegration()
        provider = MockDataProvider()
        sink = MockAuditSink()

        config = IntegrationConfig(
            integration_type=IntegrationType.AUDIT_LOGGER,
            enabled=True,
            config={"test": "config"}
        )

        # Register components
        self.assertTrue(self.boundary.register_integration("integration", integration, config))
        self.assertTrue(self.boundary.register_data_provider("provider", provider))
        self.assertTrue(self.boundary.register_audit_sink("sink", sink))

        # Verify all registered
        self.assertEqual(len(self.boundary.list_integrations()), 1)
        self.assertEqual(len(self.boundary.list_data_providers()), 1)
        self.assertEqual(len(self.boundary.list_audit_sinks()), 1)

        # Test health check
        health = self.boundary.health_check()
        self.assertTrue(health["integration"])

        # Test shutdown
        result = self.boundary.shutdown_all()
        self.assertTrue(result)
        self.assertTrue(integration.shutdown_called)
        self.assertTrue(sink.flushed)
        self.assertTrue(sink.closed)


if __name__ == "__main__":
    unittest.main()
