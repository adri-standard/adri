# @ADRI_FEATURE[enterprise_config, scope=ENTERPRISE]
# Description: Enterprise configuration module with dev/prod environment support
"""
ADRI Enterprise Configuration Module.

Provides enterprise-specific configuration loading with support for
environment-based (dev/prod) folder structures.

This module extends the base ADRI configuration system to support:
- Auto-detection of flat vs environment-based config formats
- Dev/prod environment path resolution
- ADRI_ENV environment variable override
- Backward compatibility with flat OSS structure

Usage:
    from adri_enterprise.config import (
        EnterpriseConfigurationLoader,
        ConfigFormat,
        load_enterprise_config,
        resolve_enterprise_contract,
    )

    # Using the loader directly
    loader = EnterpriseConfigurationLoader()
    config = loader.get_active_config()
    contract_path = loader.resolve_contract_path("my_contract", environment="production")

    # Using convenience functions
    config = load_enterprise_config()
    path = resolve_enterprise_contract("my_contract", environment="development")
"""

from adri_enterprise.config.loader import (
    ConfigFormat,
    detect_config_format,
    EnterpriseConfigurationLoader,
    load_enterprise_config,
    resolve_enterprise_contract,
)

__all__ = [
    "ConfigFormat",
    "EnterpriseConfigurationLoader",
    "detect_config_format",
    "load_enterprise_config",
    "resolve_enterprise_contract",
]
# @ADRI_FEATURE_END[enterprise_config]
