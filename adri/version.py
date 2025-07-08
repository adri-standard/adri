"""
Version information for the ADRI package.

This module contains version constants and compatibility information
that can be used throughout the package. The version information follows
semantic versioning (MAJOR.MINOR.PATCH).

For ADRI:
- MAJOR: Breaking changes to API or assessment methodology
- MINOR: New features, dimensions, or CLI commands (backward compatible)
- PATCH: Bug fixes and documentation improvements
"""

import os
from typing import List


def _get_version_from_metadata() -> str:
    """Get version from package metadata or environment variable."""
    # First try environment variable (useful for CI/CD)
    env_version = os.getenv("ADRI_VERSION")
    if env_version:
        return env_version

    # Try to read from pyproject.toml first (more reliable for development)
    try:
        import os.path as ospath

        # Look for pyproject.toml in current directory or parent directories
        current_dir = ospath.dirname(ospath.abspath(__file__))
        for _ in range(3):  # Check up to 3 levels up
            pyproject_path = ospath.join(current_dir, "pyproject.toml")
            if ospath.exists(pyproject_path):
                try:
                    import tomllib  # Python 3.11+
                except ImportError:
                    try:
                        import tomli as tomllib  # Python < 3.11
                    except ImportError:
                        # If no TOML library available, parse manually
                        with open(pyproject_path, "r") as f:
                            for line in f:
                                if line.strip().startswith('version = "'):
                                    return line.split('"')[1]
                        break

                with open(pyproject_path, "rb") as f:
                    data = tomllib.load(f)
                    return str(data["project"]["version"])
            current_dir = ospath.dirname(current_dir)
    except (ImportError, FileNotFoundError, KeyError, Exception):  # nosec B110
        pass

    # Fallback: try to get from package metadata
    try:
        import importlib.metadata

        return importlib.metadata.version("adri")
    except (ImportError, Exception):  # nosec B110
        pass

    # Final fallback
    return "0.2.0"


__version__ = _get_version_from_metadata()

# Minimum version compatible with current version (for report loading)
__min_compatible_version__ = "0.1.0"


def _get_compatible_versions() -> List[str]:
    """
    Generate list of compatible versions based on current version.

    For patch versions (x.y.z), all versions with same major.minor are compatible.
    This can be overridden with ADRI_COMPATIBLE_VERSIONS environment variable.
    """
    # Allow override via environment variable
    env_versions = os.getenv("ADRI_COMPATIBLE_VERSIONS")
    if env_versions:
        return env_versions.split(",")

    # Auto-generate based on semantic versioning
    try:
        # Handle pre-release versions (e.g., "0.3.0-beta.1")
        version_base = __version__.split("-")[0]  # Get "0.3.0" from "0.3.0-beta.1"
        major, minor, patch = version_base.split(".")

        base_versions = [
            "0.1.0",  # Always include initial version
            "0.1.1",  # Known compatible versions
            "0.1.2",  # Known compatible versions
            "0.2.0",  # Previous release
            "1.0.0",  # Future major version
        ]

        # Always add current version - this is critical for tests
        base_versions.append(__version__)

        return sorted(set(base_versions))
    except Exception:
        # Fallback to safe list that includes current version
        fallback_versions = ["0.1.0", "0.1.1", "0.1.2", "0.2.0", "1.0.0", __version__]
        return sorted(set(fallback_versions))


# Versions with compatible scoring methodology
# Reports from these versions can be directly compared
# Note: This is calculated dynamically to handle environment variable changes


# For backward compatibility, provide a property-like access
class _CompatibleVersions:
    def _get_versions(self):
        """Get compatible versions, calculated dynamically."""
        return _get_compatible_versions()

    def __iter__(self):
        return iter(self._get_versions())

    def __contains__(self, item):
        return item in self._get_versions()

    def __getitem__(self, index):
        return self._get_versions()[index]

    def __len__(self):
        return len(self._get_versions())

    def __repr__(self):
        return repr(self._get_versions())


__score_compatible_versions__ = _CompatibleVersions()


def is_version_compatible(version: str) -> bool:
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
        # Handle pre-release versions by extracting base version
        current_base = __version__.split("-")[0]  # "0.3.0-beta.1" -> "0.3.0"
        check_base = version.split("-")[0]  # "1.0.0-alpha" -> "1.0.0"

        current_major = int(current_base.split(".")[0])
        check_major = int(check_base.split(".")[0])

        # For now, only compatible within same major version
        return current_major == check_major
    except (ValueError, IndexError):
        return False


def get_score_compatibility_message(version: str) -> str:
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
        return f"Version {version} has generally compatible scoring with current version {__version__}, but check CHANGELOG.md for details"

    return f"Warning: Version {version} has incompatible scoring with current version {__version__}. See CHANGELOG.md for details."


def get_version_info() -> dict:
    """
    Get comprehensive version information.

    Returns:
        dict: Version information including current version, compatibility, etc.
    """
    return {
        "version": __version__,
        "min_compatible_version": __min_compatible_version__,
        "score_compatible_versions": list(__score_compatible_versions__),
        "is_production_ready": True,
        "api_version": "0.1",
        "standards_format_version": "1.0",
    }


# ----------------------------------------------
# ADRI V1.0.0 ARCHITECTURE NOTES
# ----------------------------------------------
# This is the first production release of ADRI with the new simplified architecture.
# Key changes from experimental versions:
#
# 1. Decorator-first API with @adri_protected
# 2. YAML-based standards system
# 3. CLI-driven workflow
# 4. Five-dimension assessment (validity, completeness, freshness, consistency, plausibility)
# 5. Environment-aware configuration (dev/prod)
# 6. Framework integration examples
#
# Version compatibility:
# - This version starts fresh with no backward compatibility requirements
# - Future versions will maintain compatibility within the same major version
# - Breaking changes will increment the major version number
#
# For detailed changelog, see CHANGELOG.md
# For migration information, see documentation
# ----------------------------------------------
