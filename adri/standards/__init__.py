"""
ADRI Standards Module

This module provides bundled standards loading functionality for the ADRI validator.
All standards are bundled with the package to ensure offline-first operation and
eliminate network dependencies.
"""

from .loader import BundledStandardsLoader
from .exceptions import StandardNotFoundError, InvalidStandardError

__all__ = [
    'BundledStandardsLoader',
    'StandardNotFoundError', 
    'InvalidStandardError'
]

# Default loader instance for convenience
default_loader = BundledStandardsLoader()

def load_standard(standard_name: str):
    """
    Convenience function to load a standard using the default loader.
    
    Args:
        standard_name: Name of the standard to load
        
    Returns:
        dict: The loaded standard
        
    Raises:
        StandardNotFoundError: If the standard is not found
        InvalidStandardError: If the standard is invalid
    """
    return default_loader.load_standard(standard_name)

def list_available_standards():
    """
    Convenience function to list available standards.
    
    Returns:
        list: List of available standard names
    """
    return default_loader.list_available_standards()

def standard_exists(standard_name: str) -> bool:
    """
    Convenience function to check if a standard exists.
    
    Args:
        standard_name: Name of the standard to check
        
    Returns:
        bool: True if the standard exists, False otherwise
    """
    return default_loader.standard_exists(standard_name)
