"""
ADRI Enterprise Package (verodat-adri).

Enterprise extensions for ADRI (AI-Driven Data Reliability Intelligence).
This package provides enterprise-grade features on top of the open source ADRI package:

- Enterprise decorator with additional parameters (reasoning_mode, workflow_context, data_provenance)
- Verodat API integration for centralized logging and monitoring
- AI reasoning step logging and validation
- Workflow orchestration context tracking
- Data provenance and lineage tracking
- License validation requiring valid Verodat API key

IMPORTANT: This package requires a valid Verodat API key to function.
Set the VERODAT_API_KEY environment variable before using the enterprise features.
Get your API key from your Verodat account settings.

Installation:
    pip install verodat-adri

For open source features without licensing, install the `adri` package instead:
    pip install adri

Usage:
    import os
    os.environ["VERODAT_API_KEY"] = "your-api-key"  # Or set in environment

    from adri_enterprise import adri_protected

    @adri_protected(
        contract="customer_data",
        reasoning_mode=True,
        workflow_context={...},
        data_provenance={...}
    )
    def process_data(data):
        return processed_data
"""

from importlib.metadata import PackageNotFoundError, version

# Import license components
from adri_enterprise.license import (
    LicenseInfo,
    LicenseValidationError,
    is_license_valid,
    validate_license,
)

# Import enterprise decorator
from adri_enterprise.decorator import adri_protected

__all__ = [
    "__version__",
    # Enterprise decorator
    "adri_protected",
    # License validation
    "validate_license",
    "is_license_valid",
    "LicenseInfo",
    "LicenseValidationError",
]

# Version management
try:
    __version__ = version("verodat-adri")
except PackageNotFoundError:
    __version__ = "unknown"
