"""
Version information for the ADRI package.

This module contains version constants and compatibility information
that can be used throughout the package. The version information follows
semantic versioning (MAJOR.MINOR.PATCH).

For ADRI specifically:
- MAJOR: Incompatible changes to scoring methodology
- MINOR: New features, dimensions, or connectors (backward compatible)
- PATCH: Bug fixes and documentation improvements
"""

__version__ = "0.2.0b1"  # Current version (beta)

# Minimum version compatible with current version (for report loading)
__min_compatible_version__ = "0.1.0"

# Versions with compatible scoring methodology
# Reports from these versions can be directly compared
__score_compatible_versions__ = ["0.1.0", "0.2.0b1"]

def is_version_compatible(version):
    """
    Check if the given version is compatible with the current version.
    
    Args:
        version (str): Version string to check
        
    Returns:
        bool: True if compatible, False if not
    """
    if version in __score_compatible_versions__:
        return True
        
    # Parse versions - basic semver handling
    try:
        # Simple version comparison - should be expanded with proper semver parsing
        current_major = int(__version__.split('.')[0])
        check_major = int(version.split('.')[0])
        
        # For now, only compatible within same major version
        return current_major == check_major
    except (ValueError, IndexError):
        return False

def get_score_compatibility_message(version):
    """
    Get a human-readable message about score compatibility.
    
    Args:
        version (str): Version string to check
        
    Returns:
        str: Message about compatibility
    """
    if version in __score_compatible_versions__:
        return f"Version {version} has fully compatible scoring with current version {__version__}"
    
    if is_version_compatible(version):
        return f"Version {version} has generally compatible scoring with current version {__version__}, but check VERSIONS.md for details"
    
    return f"Warning: Version {version} has incompatible scoring with current version {__version__}. See VERSIONS.md for details."
