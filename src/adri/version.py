"""
Version information for the ADRI package.

This module contains version constants and compatibility information
that can be used throughout the package. The version information follows
semantic versioning (MAJOR.MINOR.PATCH).

For ADRI:
- MAJOR: Breaking changes to API or assessment methodology
- MINOR: New features, dimensions, or CLI commands (backward compatible)
- PATCH: Bug fixes and documentation improvements

Version management is handled by setuptools_scm which automatically
generates version numbers from git tags.
"""

import os


def _get_version_from_setuptools_scm() -> str:
    """Get version from setuptools_scm generated file or fallback."""
    # First try environment variable (useful for CI/CD)
    env_version = os.getenv("ADRI_VERSION")
    if env_version:
        return env_version

    # Try to import from setuptools_scm generated version file
    try:
        from adri._version import version

        return version
    except (ImportError, AttributeError):
        pass

    # Fallback: try to get from package metadata
    try:
        import importlib.metadata

        return importlib.metadata.version("adri")
    except (ImportError, Exception):  # nosec B110
        pass

    # Final fallback - this should match the fallback_version in pyproject.toml
    return "4.0.0"


__version__ = _get_version_from_setuptools_scm()

# Minimum version compatible with current version (for report loading)
__min_compatible_version__ = "4.0.0"


def _get_compatible_versions() -> list[str]:
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
        # Handle pre-release versions (e.g., "4.0.1-beta.1")
        version_base = __version__.split("-")[0]  # Get "4.0.1" from "4.0.1-beta.1"
        major, minor, patch = version_base.split(".")

        base_versions = [
            "4.0.0",  # Initial open source release
            "4.1.0",  # First public release
        ]

        # Always add current version - this is critical for tests
        base_versions.append(__version__)

        return sorted(set(base_versions))
    except Exception:
        # Fallback to safe list that includes current version
        fallback_versions = ["4.0.0", __version__]
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
        current_base = __version__.split("-")[0]  # "4.0.1-beta.1" -> "4.0.1"
        check_base = version.split("-")[0]  # "4.1.0-alpha" -> "4.1.0"

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
        "api_version": "1.0",
        "standards_format_version": "1.0",
    }


# ----------------------------------------------
# ADRI V4.1.0 FIRST PUBLIC RELEASE NOTES
# ----------------------------------------------
# This is the first public release of ADRI (AI Data Reliability Intelligence).
# Built on the v4.0.0 foundation with significant improvements:
#
# 1. Issue #35 fixes for CLI/decorator consistency
# 2. Comprehensive test consolidation (816 passing tests)
# 3. Cross-platform compatibility (Ubuntu, Windows, macOS)
# 4. Enhanced governance with name-only standard resolution
# 5. Production-ready documentation and security policy
#
# Version compatibility:
# - Maintains backward compatibility with v4.0.0
# - Compatible versions: 4.0.0, 4.1.0
# - Future versions maintain compatibility within the same major version
# - Breaking changes will increment the major version number
#
# Version numbering:
# - setuptools_scm generates versions automatically from git tags
# - Development versions: 4.1.1.dev23+g1234567 (commits after latest tag)
# - Release versions: 4.0.0, 4.1.0, 4.2.0, etc. (from git tags)
#
# Platform support:
# - Python 3.10, 3.11, 3.12
# - Tested on Ubuntu, Windows, macOS
# - 9 platform/Python combinations validated by CI
#
# For detailed changelog, see CHANGELOG.md
# For contribution guidelines, see CONTRIBUTING.md
# ----------------------------------------------
