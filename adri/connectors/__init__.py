"""
Data source connectors for the Agent Data Readiness Index.

This package contains connectors for various data sources including:
- FileConnector: For file-based data sources (CSV, JSON, etc.)
- DatabaseConnector: For database tables
- APIConnector: For API endpoints
"""

from .base import BaseConnector
from .registry import ConnectorRegistry


def register_connector(name: str, description: str = ""):
    """
    Decorator to register a connector.
    
    Args:
        name: Name of the connector
        description: Optional description of the connector
        
    Returns:
        Callable: Decorator function
    """
    def decorator(cls):
        cls.connector_name = name
        cls.connector_description = description
        ConnectorRegistry.register(name, cls)
        return cls
    return decorator


# Import all connectors
from .file import FileConnector
from .database import DatabaseConnector
from .api import APIConnector


__all__ = [
    "BaseConnector",
    "ConnectorRegistry",
    "register_connector",
    "FileConnector",
    "DatabaseConnector",
    "APIConnector",
]
