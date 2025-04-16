"""
Registry for data source connectors in the Agent Data Readiness Index.

This module provides a registry for data source connectors, allowing them to be
dynamically registered and discovered.
"""

from typing import Dict, Type, List, Any

from .base import BaseConnector


class ConnectorRegistry:
    """
    Registry for data source connectors.
    
    This class provides a central registry for all data source connectors,
    allowing them to be dynamically registered and discovered.
    """
    
    _connectors: Dict[str, Type[BaseConnector]] = {}
    
    @classmethod
    def register(cls, name: str, connector_class: Type[BaseConnector]) -> None:
        """
        Register a connector.
        
        Args:
            name: Name of the connector
            connector_class: Connector class
        """
        cls._connectors[name] = connector_class
        
    @classmethod
    def get_connector(cls, name: str) -> Type[BaseConnector]:
        """
        Get a connector by name.
        
        Args:
            name: Name of the connector
            
        Returns:
            Type[BaseConnector]: Connector class
            
        Raises:
            ValueError: If the connector is not registered
        """
        if name not in cls._connectors:
            raise ValueError(f"Connector '{name}' not registered")
        return cls._connectors[name]
        
    @classmethod
    def get_all_connectors(cls) -> Dict[str, Type[BaseConnector]]:
        """
        Get all registered connectors.
        
        Returns:
            Dict[str, Type[BaseConnector]]: Dictionary of connector name to connector class
        """
        return cls._connectors.copy()
        
    @classmethod
    def list_connectors(cls) -> List[str]:
        """
        List all registered connector names.
        
        Returns:
            List[str]: List of connector names
        """
        return list(cls._connectors.keys())
