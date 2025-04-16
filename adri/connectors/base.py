"""
Base connector interface for the Agent Data Readiness Index.

This module defines the BaseConnector abstract class that all data source
connectors must implement.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple, Iterator


class BaseConnector(ABC):
    """
    Abstract base class for all data source connectors.
    
    Connectors are responsible for interfacing with various data sources
    and providing a consistent API for assessors to evaluate them.
    """
    
    connector_name: str = "base"  # Override in subclasses
    connector_description: str = ""  # Override in subclasses
    
    @abstractmethod
    def get_name(self) -> str:
        """
        Get the name of this data source.
        
        Returns:
            str: The name of the data source
        """
        pass
    
    @abstractmethod
    def get_type(self) -> str:
        """
        Get the type of this data source.
        
        Returns:
            str: Type of data source (e.g., "csv", "database", "api")
        """
        pass
    
    @abstractmethod
    def get_metadata(self) -> Dict[str, Any]:
        """
        Get metadata about the data source.
        
        Returns:
            Dict[str, Any]: Dictionary of metadata
        """
        pass
    
    @abstractmethod
    def get_schema(self) -> Dict[str, Any]:
        """
        Get the schema information for this data source.
        
        Returns:
            Dict[str, Any]: Schema information including field names, types, etc.
        """
        pass
    
    @abstractmethod
    def sample_data(self, n: int = 100) -> List[Dict[str, Any]]:
        """
        Get a sample of data from this data source.
        
        Args:
            n: Number of records to sample
            
        Returns:
            List[Dict[str, Any]]: List of sampled records
        """
        pass
    
    @abstractmethod
    def get_update_frequency(self) -> Optional[str]:
        """
        Get information about how frequently this data is updated.
        
        Returns:
            Optional[str]: Update frequency information if available
        """
        pass
    
    @abstractmethod
    def get_last_update_time(self) -> Optional[str]:
        """
        Get the last time this data was updated.
        
        Returns:
            Optional[str]: Timestamp of last update if available
        """
        pass
    
    @abstractmethod
    def get_data_size(self) -> Optional[int]:
        """
        Get the size of the data (e.g., number of records).
        
        Returns:
            Optional[int]: Size of the data if available
        """
        pass
    
    @abstractmethod
    def get_quality_metadata(self) -> Dict[str, Any]:
        """
        Get any explicit quality metadata provided by the data source.
        
        Returns:
            Dict[str, Any]: Quality metadata if available
        """
        pass
    
    @abstractmethod
    def supports_validation(self) -> bool:
        """
        Check if this data source supports validation.
        
        Returns:
            bool: True if validation is supported
        """
        pass
    
    @abstractmethod
    def get_validation_results(self) -> Optional[Dict[str, Any]]:
        """
        Get results of any validation performed on this data source.
        
        Returns:
            Optional[Dict[str, Any]]: Validation results if available
        """
        pass
    
    @abstractmethod
    def supports_completeness_check(self) -> bool:
        """
        Check if this data source supports completeness checking.
        
        Returns:
            bool: True if completeness checking is supported
        """
        pass
    
    @abstractmethod
    def get_completeness_results(self) -> Optional[Dict[str, Any]]:
        """
        Get results of any completeness checks on this data source.
        
        Returns:
            Optional[Dict[str, Any]]: Completeness results if available
        """
        pass
    
    @abstractmethod
    def supports_consistency_check(self) -> bool:
        """
        Check if this data source supports consistency checking.
        
        Returns:
            bool: True if consistency checking is supported
        """
        pass
    
    @abstractmethod
    def get_consistency_results(self) -> Optional[Dict[str, Any]]:
        """
        Get results of any consistency checks on this data source.
        
        Returns:
            Optional[Dict[str, Any]]: Consistency results if available
        """
        pass
    
    @abstractmethod
    def supports_freshness_check(self) -> bool:
        """
        Check if this data source supports freshness checking.
        
        Returns:
            bool: True if freshness checking is supported
        """
        pass
    
    @abstractmethod
    def get_freshness_results(self) -> Optional[Dict[str, Any]]:
        """
        Get results of any freshness checks on this data source.
        
        Returns:
            Optional[Dict[str, Any]]: Freshness results if available
        """
        pass
    
    @abstractmethod
    def supports_plausibility_check(self) -> bool:
        """
        Check if this data source supports plausibility checking.
        
        Returns:
            bool: True if plausibility checking is supported
        """
        pass
    
    @abstractmethod
    def get_plausibility_results(self) -> Optional[Dict[str, Any]]:
        """
        Get results of any plausibility checks on this data source.
        
        Returns:
            Optional[Dict[str, Any]]: Plausibility results if available
        """
        pass
    
    @abstractmethod
    def get_agent_accessibility(self) -> Dict[str, Any]:
        """
        Get information about how accessible this data source is to agents.
        
        Returns:
            Dict[str, Any]: Information about agent accessibility
        """
        pass
    
    @abstractmethod
    def get_data_lineage(self) -> Optional[Dict[str, Any]]:
        """
        Get lineage information for this data source.
        
        Returns:
            Optional[Dict[str, Any]]: Lineage information if available
        """
        pass
    
    @abstractmethod
    def get_governance_metadata(self) -> Optional[Dict[str, Any]]:
        """
        Get governance metadata for this data source.
        
        Returns:
            Optional[Dict[str, Any]]: Governance metadata if available
        """
        pass

    def __str__(self) -> str:
        """String representation of the connector."""
        return f"{self.get_type()} connector for {self.get_name()}"
