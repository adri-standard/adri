"""
ADRI Standards Exceptions.

Custom exceptions for the ADRI standards loading system.
"""

from typing import Optional


class StandardNotFoundError(Exception):
    """
    Raised when a requested standard cannot be found in the bundled standards.

    This exception indicates that the standard name provided does not match
    any of the bundled standards available in the package.
    """

    def __init__(self, standard_name: str):
        """Initialize with the name of the missing standard."""
        self.standard_name = standard_name
        super().__init__(f"Standard '{standard_name}' not found in bundled standards")


class InvalidStandardError(Exception):
    """
    Raised when a standard file exists but contains invalid content.

    This exception indicates that the standard file could not be parsed
    or does not conform to the expected ADRI standard format.
    """

    def __init__(self, message: str, standard_name: Optional[str] = None):
        """Initialize with error message and optional standard name."""
        self.standard_name = standard_name
        if standard_name:
            super().__init__(f"Invalid standard '{standard_name}': {message}")
        else:
            super().__init__(f"Invalid standard: {message}")


class StandardsDirectoryNotFoundError(Exception):
    """
    Raised when the bundled standards directory cannot be found.

    This exception indicates a packaging or installation issue where
    the bundled standards directory is missing from the package.
    """

    def __init__(self, directory_path: str):
        """Initialize with the path of the missing directory."""
        self.directory_path = directory_path
        super().__init__(f"Bundled standards directory not found: {directory_path}")
