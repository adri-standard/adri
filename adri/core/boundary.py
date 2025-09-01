"""
ADRI Component Boundary Definitions.

Defines clear interfaces and boundaries for the ADRI Validator component,
ensuring proper separation from external systems and dependencies.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol


class IntegrationType(Enum):
    """Types of external integrations supported."""

    AUDIT_LOGGER = "audit_logger"
    DATA_SOURCE = "data_source"
    NOTIFICATION = "notification"
    MONITORING = "monitoring"
    CUSTOM = "custom"


class DataFormat(Enum):
    """Supported data formats for external communication."""

    JSON = "json"
    CSV = "csv"
    PARQUET = "parquet"
    YAML = "yaml"
    DICT = "dict"


@dataclass
class IntegrationConfig:
    """Configuration for external integrations."""

    integration_type: IntegrationType
    enabled: bool
    config: Dict[str, Any]
    data_format: DataFormat = DataFormat.JSON
    timeout_seconds: Optional[int] = 30
    retry_count: Optional[int] = 3
    batch_size: Optional[int] = 100


class ExternalIntegration(ABC):
    """
    Abstract base class for external integrations.

    All external integrations must implement this interface to ensure
    proper boundary control and separation of concerns.
    """

    @abstractmethod
    def initialize(self, config: IntegrationConfig) -> bool:
        """
        Initialize the external integration.

        Args:
            config: Integration configuration

        Returns:
            True if initialization successful, False otherwise
        """
        pass

    @abstractmethod
    def send_data(self, data: Any, format: DataFormat) -> bool:
        """
        Send data to the external system.

        Args:
            data: Data to send
            format: Format of the data

        Returns:
            True if send successful, False otherwise
        """
        pass

    @abstractmethod
    def receive_data(self, format: DataFormat) -> Optional[Any]:
        """
        Receive data from the external system.

        Args:
            format: Expected format of the data

        Returns:
            Received data or None if no data available
        """
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """
        Check if the external integration is healthy.

        Returns:
            True if healthy, False otherwise
        """
        pass

    @abstractmethod
    def shutdown(self) -> bool:
        """
        Gracefully shutdown the external integration.

        Returns:
            True if shutdown successful, False otherwise
        """
        pass


class DataProvider(Protocol):
    """
    Protocol for data providers that supply data to ADRI Validator.

    This protocol ensures that any data source conforms to the expected
    interface without requiring inheritance.
    """

    def get_data(self) -> Any:
        """Get data from the provider."""
        ...

    def get_metadata(self) -> Dict[str, Any]:
        """Get metadata about the data."""
        ...

    def validate_schema(self) -> bool:
        """Validate that the data conforms to expected schema."""
        ...


class AuditSink(Protocol):
    """
    Protocol for audit log sinks that receive audit records.

    This protocol allows different audit backends to be plugged in
    without modifying the core ADRI Validator code.
    """

    def write_record(self, record: Dict[str, Any]) -> bool:
        """Write an audit record."""
        ...

    def flush(self) -> bool:
        """Flush any buffered records."""
        ...

    def close(self) -> bool:
        """Close the audit sink."""
        ...


class ComponentBoundary:
    """
    Manages the boundaries between ADRI Validator and external systems.

    This class acts as a facade for all external integrations, ensuring
    that the core ADRI Validator remains independent and testable.
    """

    def __init__(self):
        """Initialize the component boundary manager."""
        self._integrations: Dict[str, ExternalIntegration] = {}
        self._data_providers: Dict[str, DataProvider] = {}
        self._audit_sinks: Dict[str, AuditSink] = {}

    def register_integration(
        self, name: str, integration: ExternalIntegration, config: IntegrationConfig
    ) -> bool:
        """
        Register an external integration.

        Args:
            name: Unique name for the integration
            integration: Integration instance
            config: Integration configuration

        Returns:
            True if registration successful, False otherwise
        """
        try:
            if integration.initialize(config):
                self._integrations[name] = integration
                return True
            return False
        except Exception:
            return False

    def register_data_provider(self, name: str, provider: DataProvider) -> bool:
        """
        Register a data provider.

        Args:
            name: Unique name for the provider
            provider: Provider instance

        Returns:
            True if registration successful, False otherwise
        """
        try:
            # Validate that provider conforms to protocol
            if (
                hasattr(provider, "get_data")
                and hasattr(provider, "get_metadata")
                and hasattr(provider, "validate_schema")
            ):
                self._data_providers[name] = provider
                return True
            return False
        except Exception:
            return False

    def register_audit_sink(self, name: str, sink: AuditSink) -> bool:
        """
        Register an audit sink.

        Args:
            name: Unique name for the sink
            sink: Sink instance

        Returns:
            True if registration successful, False otherwise
        """
        try:
            # Validate that sink conforms to protocol
            if (
                hasattr(sink, "write_record")
                and hasattr(sink, "flush")
                and hasattr(sink, "close")
            ):
                self._audit_sinks[name] = sink
                return True
            return False
        except Exception:
            return False

    def get_integration(self, name: str) -> Optional[ExternalIntegration]:
        """Get a registered integration by name."""
        return self._integrations.get(name)

    def get_data_provider(self, name: str) -> Optional[DataProvider]:
        """Get a registered data provider by name."""
        return self._data_providers.get(name)

    def get_audit_sink(self, name: str) -> Optional[AuditSink]:
        """Get a registered audit sink by name."""
        return self._audit_sinks.get(name)

    def list_integrations(self) -> List[str]:
        """List all registered integration names."""
        return list(self._integrations.keys())

    def list_data_providers(self) -> List[str]:
        """List all registered data provider names."""
        return list(self._data_providers.keys())

    def list_audit_sinks(self) -> List[str]:
        """List all registered audit sink names."""
        return list(self._audit_sinks.keys())

    def health_check(self) -> Dict[str, bool]:
        """
        Perform health check on all registered integrations.

        Returns:
            Dictionary mapping integration names to health status
        """
        results = {}
        for name, integration in self._integrations.items():
            try:
                results[name] = integration.health_check()
            except Exception:
                results[name] = False
        return results

    def shutdown_all(self) -> bool:
        """
        Shutdown all registered integrations.

        Returns:
            True if all shutdowns successful, False otherwise
        """
        all_success = True

        # Shutdown integrations
        for integration in self._integrations.values():
            try:
                if not integration.shutdown():
                    all_success = False
            except Exception:
                all_success = False

        # Close audit sinks
        for sink in self._audit_sinks.values():
            try:
                sink.flush()
                if not sink.close():
                    all_success = False
            except Exception:
                all_success = False

        # Clear registrations
        self._integrations.clear()
        self._data_providers.clear()
        self._audit_sinks.clear()

        return all_success


# Singleton instance for global access
_boundary_manager = ComponentBoundary()


def get_boundary_manager() -> ComponentBoundary:
    """
    Get the global component boundary manager.

    Returns:
        The singleton ComponentBoundary instance
    """
    return _boundary_manager


class StandaloneMode:
    """
    Context manager for ensuring standalone operation.

    This context manager temporarily disables all external integrations
    to ensure the ADRI Validator operates in pure standalone mode.
    """

    def __init__(self):
        """Initialize standalone mode context."""
        self._original_integrations = {}
        self._boundary = get_boundary_manager()

    def __enter__(self):
        """Enter standalone mode by disabling external integrations."""
        # Store and remove all integrations
        for name in list(self._boundary.list_integrations()):
            integration = self._boundary.get_integration(name)
            if integration:
                self._original_integrations[name] = integration
                # Remove from boundary manager
                del self._boundary._integrations[name]
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit standalone mode by restoring external integrations."""
        # Restore all integrations
        for name, integration in self._original_integrations.items():
            self._boundary._integrations[name] = integration
        self._original_integrations.clear()


def validate_standalone_operation() -> bool:
    """
    Validate that ADRI Validator can operate in standalone mode.

    Returns:
        True if standalone operation is possible, False otherwise
    """
    try:
        # Test that we can enter standalone mode
        with StandaloneMode():
            # Try to import and use core functionality
            from adri.standards.loader import StandardsLoader

            # Verify standards can be loaded
            loader = StandardsLoader()
            standards = loader.list_available_standards()

            # Check that we have bundled standards
            if len(standards) == 0:
                return False

            # Verify no external integrations are active
            boundary = get_boundary_manager()
            if len(boundary.list_integrations()) > 0:
                return False

            return True

    except Exception:
        return False
