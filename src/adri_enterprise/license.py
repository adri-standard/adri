"""
ADRI Enterprise - License and API Key Validation.

Provides API key validation for enterprise deployments, ensuring only
licensed users can access enterprise features.

The verodat-adri package requires a valid Verodat API key to function.
Keys can be obtained from your Verodat account settings.
"""

import logging
import os
import threading
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

import requests

logger = logging.getLogger(__name__)

# Default Verodat API configuration
DEFAULT_VERODAT_API_URL = "https://api.verodat.com/api/v1"

# Environment variable names
ENV_VERODAT_API_KEY = "VERODAT_API_KEY"
ENV_VERODAT_API_URL = "VERODAT_API_URL"


@dataclass
class LicenseInfo:
    """Information about a validated license/API key."""

    is_valid: bool
    api_key: str
    validated_at: datetime
    expires_at: Optional[datetime] = None
    account_id: Optional[int] = None
    username: Optional[str] = None
    error_message: Optional[str] = None


class LicenseValidationError(Exception):
    """Raised when license/API key validation fails."""

    def __init__(self, message: str, details: Optional[str] = None):
        self.message = message
        self.details = details
        super().__init__(self.message)


class LicenseValidator:
    """
    Validates Verodat API keys for enterprise licensing.

    This class implements a "validate on first use" pattern with caching
    to minimize API calls while ensuring license compliance.
    """

    _instance: Optional["LicenseValidator"] = None
    _lock = threading.Lock()

    def __new__(cls):
        """Singleton pattern to ensure single validation state."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize the license validator."""
        if self._initialized:
            return
        
        self._validated_license: Optional[LicenseInfo] = None
        self._validation_cache_duration = timedelta(hours=24)
        self._api_url = os.environ.get(ENV_VERODAT_API_URL, DEFAULT_VERODAT_API_URL)
        self._timeout = 30
        self._initialized = True

    def validate_api_key(
        self,
        api_key: Optional[str] = None,
        force_revalidation: bool = False,
    ) -> LicenseInfo:
        """
        Validate a Verodat API key.

        Args:
            api_key: The API key to validate. If not provided, reads from
                    VERODAT_API_KEY environment variable.
            force_revalidation: If True, bypasses cache and revalidates.

        Returns:
            LicenseInfo object with validation results.

        Raises:
            LicenseValidationError: If validation fails or no key is provided.
        """
        # Get API key from parameter or environment
        key = api_key or os.environ.get(ENV_VERODAT_API_KEY)
        
        if not key:
            raise LicenseValidationError(
                "Verodat API key required",
                details=(
                    "The verodat-adri package requires a valid Verodat API key. "
                    "Set the VERODAT_API_KEY environment variable or pass the key "
                    "to the validator. Get your API key from your Verodat account."
                ),
            )

        # Check cache (unless force revalidation)
        if not force_revalidation and self._is_cache_valid(key):
            logger.debug("Using cached license validation")
            return self._validated_license

        # Perform validation
        return self._perform_validation(key)

    def _is_cache_valid(self, api_key: str) -> bool:
        """Check if cached validation is still valid."""
        if self._validated_license is None:
            return False
        
        if self._validated_license.api_key != api_key:
            return False
        
        if not self._validated_license.is_valid:
            return False
        
        cache_age = datetime.now() - self._validated_license.validated_at
        if cache_age > self._validation_cache_duration:
            return False
        
        return True

    def _perform_validation(self, api_key: str) -> LicenseInfo:
        """Perform actual API key validation against Verodat API."""
        try:
            headers = {
                "Authorization": f"ApiKey {api_key}",
                "Content-Type": "application/json",
            }

            response = requests.get(
                f"{self._api_url}/ai/key",
                headers=headers,
                timeout=self._timeout,
            )

            if response.status_code == 200:
                data = response.json()
                license_info = LicenseInfo(
                    is_valid=True,
                    api_key=api_key,
                    validated_at=datetime.now(),
                    account_id=data.get("accountId"),
                    username=data.get("username"),
                )
                self._validated_license = license_info
                logger.info("Verodat API key validated successfully")
                return license_info

            elif response.status_code == 401:
                license_info = LicenseInfo(
                    is_valid=False,
                    api_key=api_key,
                    validated_at=datetime.now(),
                    error_message="Invalid or expired API key",
                )
                self._validated_license = license_info
                raise LicenseValidationError(
                    "Invalid Verodat API key",
                    details="The API key is invalid or has expired. Please check your "
                           "Verodat account settings and generate a new key if needed.",
                )

            elif response.status_code == 403:
                license_info = LicenseInfo(
                    is_valid=False,
                    api_key=api_key,
                    validated_at=datetime.now(),
                    error_message="API key does not have enterprise access",
                )
                self._validated_license = license_info
                raise LicenseValidationError(
                    "Enterprise license required",
                    details="Your Verodat account does not have enterprise access. "
                           "Please contact Verodat to upgrade your license.",
                )

            else:
                error_msg = f"Unexpected response: {response.status_code}"
                logger.error(f"License validation failed: {error_msg}")
                raise LicenseValidationError(
                    "License validation failed",
                    details=f"Server returned status {response.status_code}",
                )

        except requests.exceptions.Timeout:
            raise LicenseValidationError(
                "License validation timeout",
                details="Could not reach Verodat API. Please check your network "
                       "connection and try again.",
            )
        except requests.exceptions.RequestException as e:
            raise LicenseValidationError(
                "License validation failed",
                details=f"Network error: {str(e)}",
            )

    @property
    def is_validated(self) -> bool:
        """Check if a valid license has been validated."""
        return (
            self._validated_license is not None
            and self._validated_license.is_valid
            and self._is_cache_valid(self._validated_license.api_key)
        )

    @property
    def current_license(self) -> Optional[LicenseInfo]:
        """Get the current validated license info."""
        return self._validated_license

    def clear_cache(self) -> None:
        """Clear the validation cache."""
        self._validated_license = None
        logger.debug("License validation cache cleared")


# Global validator instance
_validator: Optional[LicenseValidator] = None


def get_validator() -> LicenseValidator:
    """Get the global license validator instance."""
    global _validator
    if _validator is None:
        _validator = LicenseValidator()
    return _validator


def validate_license(
    api_key: Optional[str] = None,
    force_revalidation: bool = False,
) -> LicenseInfo:
    """
    Validate a Verodat API key (convenience function).

    Args:
        api_key: The API key to validate. If not provided, reads from
                VERODAT_API_KEY environment variable.
        force_revalidation: If True, bypasses cache and revalidates.

    Returns:
        LicenseInfo object with validation results.

    Raises:
        LicenseValidationError: If validation fails or no key is provided.

    Example:
        >>> import os
        >>> os.environ["VERODAT_API_KEY"] = "your-api-key"
        >>> license_info = validate_license()
        >>> print(f"Valid: {license_info.is_valid}")
    """
    return get_validator().validate_api_key(api_key, force_revalidation)


def require_license(func):
    """
    Decorator that requires a valid Verodat license before execution.

    This decorator validates the API key on first use and caches the result.
    Subsequent calls use the cached validation until it expires.

    Example:
        >>> @require_license
        ... def my_enterprise_function():
        ...     return "Enterprise feature executed"
    """
    import functools

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        validate_license()
        return func(*args, **kwargs)

    return wrapper


def is_license_valid() -> bool:
    """
    Check if a valid license is currently cached.

    Returns:
        True if a valid license is cached, False otherwise.

    Note:
        This does not perform validation - it only checks the cache.
        Use validate_license() to perform actual validation.
    """
    return get_validator().is_validated
