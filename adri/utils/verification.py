"""
ADRI Standalone Verification Utilities.

Provides utilities to verify that the ADRI Validator is operating
in standalone mode without external dependencies.
"""

import os
import sys
from typing import Any, Dict, List, Tuple

from adri.standards.loader import StandardsLoader
from adri.version import __version__


def verify_standalone_installation() -> Tuple[bool, List[str]]:
    """
    Verify that ADRI Validator is installed and operating in standalone mode.

    Returns:
        Tuple of (success: bool, messages: List[str])
        - success: True if all checks pass
        - messages: List of status/error messages from checks
    """
    messages = []
    success = True

    # Check 1: Verify no adri-standards dependency
    try:
        import pkg_resources

        installed_packages = {pkg.key for pkg in pkg_resources.working_set}
        if "adri-standards" in installed_packages:
            success = False
            messages.append(
                "❌ External adri-standards package detected - not standalone"
            )
        else:
            messages.append("✅ No external adri-standards dependency found")
    except ImportError:
        messages.append(
            "⚠️  Could not verify package dependencies (pkg_resources not available)"
        )

    # Check 2: Verify bundled standards exist
    try:
        loader = StandardsLoader()
        available_standards = loader.list_available_standards()
        if len(available_standards) > 0:
            messages.append(
                f"✅ {len(available_standards)} bundled standards available"
            )
        else:
            success = False
            messages.append("❌ No bundled standards found")
    except Exception as e:
        success = False
        messages.append(f"❌ Failed to load bundled standards: {e}")

    # Check 3: Verify no external standards path fallback
    try:
        loader = StandardsLoader()
        standards_path = loader.standards_path
        if "bundled" in str(standards_path) or os.getenv("ADRI_STANDARDS_PATH"):
            messages.append(f"✅ Using correct standards path: {standards_path}")
        else:
            success = False
            messages.append(f"❌ Using external standards path: {standards_path}")
    except Exception as e:
        success = False
        messages.append(f"❌ Failed to verify standards path: {e}")

    # Check 4: Verify core modules are importable
    core_modules = [
        "adri.core.assessor",
        "adri.core.protection",
        "adri.core.audit_logger",
        "adri.config.manager",
        "adri.decorators",
    ]

    for module in core_modules:
        try:
            __import__(module)
            messages.append(f"✅ Module {module} loaded successfully")
        except ImportError as e:
            success = False
            messages.append(f"❌ Failed to import {module}: {e}")

    # Check 5: Verify version information
    messages.append(f"ℹ️  ADRI Validator version: {__version__}")

    return success, messages


def list_bundled_standards() -> List[Dict[str, str]]:
    """
    List all available bundled standards with metadata.

    Returns:
        List of dictionaries containing standard metadata
    """
    loader = StandardsLoader()
    standards = []

    for standard_name in loader.list_available_standards():
        try:
            metadata = loader.get_standard_metadata(standard_name)
            standards.append(
                {
                    "name": standard_name,
                    "id": metadata.get("id", "unknown"),
                    "version": metadata.get("version", "unknown"),
                    "description": metadata.get("description", "No description"),
                }
            )
        except Exception as e:
            standards.append(
                {
                    "name": standard_name,
                    "id": "error",
                    "version": "error",
                    "description": f"Failed to load metadata: {e}",
                }
            )

    return standards


def check_system_compatibility() -> Dict[str, Any]:
    """
    Check system compatibility for ADRI Validator.

    Returns:
        Dictionary with system information and compatibility status
    """
    import platform

    info: Dict[str, Any] = {
        "python_version": sys.version,
        "python_version_tuple": sys.version_info[:3],
        "platform": platform.platform(),
        "architecture": platform.machine(),
        "os": platform.system(),
    }

    # Check Python version compatibility
    min_version = (3, 10, 0)
    info["python_compatible"] = sys.version_info[:3] >= min_version

    # Check for required packages
    required_packages = ["pandas", "yaml", "click", "pyarrow"]
    info["missing_packages"] = []

    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            info["missing_packages"].append(package)

    info["packages_compatible"] = len(info["missing_packages"]) == 0

    return info


def verify_audit_logging(enabled: bool = False) -> Tuple[bool, List[str]]:
    """
    Verify audit logging functionality.

    Args:
        enabled: Whether audit logging should be enabled

    Returns:
        Tuple of (success: bool, messages: List[str])
    """
    messages = []
    success = True

    try:
        from adri.core.audit_logger import AuditLogger

        # Test basic instantiation
        AuditLogger({"enabled": enabled})
        messages.append(f"✅ AuditLogger instantiated (enabled={enabled})")

        # Test audit record creation
        if enabled:
            from datetime import datetime

            from adri.core.audit_logger import AuditRecord

            record = AuditRecord(
                assessment_id="test_001",
                timestamp=datetime.now(),
                adri_version=__version__,
            )
            messages.append("✅ AuditRecord created successfully")

            # Test conversion formats
            _ = record.to_dict()
            messages.append("✅ AuditRecord converts to dict")

            _ = record.to_json()
            messages.append("✅ AuditRecord converts to JSON")

            _ = record.to_verodat_format()
            messages.append("✅ AuditRecord converts to Verodat format")

    except Exception as e:
        success = False
        messages.append(f"❌ Audit logging verification failed: {e}")

    # Verify optional Verodat logger
    try:
        from adri.core.verodat_logger import VerodatLogger  # noqa: F401

        messages.append("✅ VerodatLogger module available (optional)")
    except ImportError:
        messages.append("ℹ️  VerodatLogger not available (optional feature)")

    # Verify CSV logger
    try:
        from adri.core.audit_logger_csv import AuditLoggerCSV  # noqa: F401

        messages.append("✅ AuditLoggerCSV module available")
    except ImportError:
        success = False
        messages.append("❌ AuditLoggerCSV module not found")

    return success, messages


def run_full_verification(verbose: bool = True) -> bool:
    """
    Run complete standalone verification suite.

    Args:
        verbose: Whether to print detailed output

    Returns:
        True if all verifications pass, False otherwise
    """
    if verbose:
        print("\n" + "=" * 60)
        print("ADRI VALIDATOR STANDALONE VERIFICATION")
        print("=" * 60)

    all_success = True

    # Run standalone installation check
    if verbose:
        print("\n1. Verifying Standalone Installation")
        print("-" * 40)

    success, messages = verify_standalone_installation()
    all_success = all_success and success

    if verbose:
        for msg in messages:
            print(f"   {msg}")

    # Check system compatibility
    if verbose:
        print("\n2. Checking System Compatibility")
        print("-" * 40)

    sys_info = check_system_compatibility()

    if verbose:
        print(f"   Python: {sys_info['python_version_tuple']}")
        print(f"   Platform: {sys_info['platform']}")
        print(
            f"   Python Compatible: {'✅' if sys_info['python_compatible'] else '❌'}"
        )
        print(
            f"   Packages Compatible: {'✅' if sys_info['packages_compatible'] else '❌'}"
        )

        if sys_info["missing_packages"]:
            print(f"   Missing Packages: {', '.join(sys_info['missing_packages'])}")

    all_success = (
        all_success
        and sys_info["python_compatible"]
        and sys_info["packages_compatible"]
    )

    # List bundled standards
    if verbose:
        print("\n3. Bundled Standards")
        print("-" * 40)

    standards = list_bundled_standards()

    if verbose:
        for std in standards[:5]:  # Show first 5
            print(f"   • {std['name']} (v{std['version']})")
        if len(standards) > 5:
            print(f"   ... and {len(standards) - 5} more")

    # Verify audit logging
    if verbose:
        print("\n4. Verifying Audit Logging")
        print("-" * 40)

    success, messages = verify_audit_logging(enabled=False)
    all_success = all_success and success

    if verbose:
        for msg in messages:
            print(f"   {msg}")

    # Final summary
    if verbose:
        print("\n" + "=" * 60)
        if all_success:
            print("✅ ALL VERIFICATIONS PASSED - STANDALONE MODE CONFIRMED")
        else:
            print("❌ SOME VERIFICATIONS FAILED - REVIEW MESSAGES ABOVE")
        print("=" * 60 + "\n")

    return all_success


if __name__ == "__main__":
    # Run verification when module is executed directly
    success = run_full_verification(verbose=True)
    sys.exit(0 if success else 1)
