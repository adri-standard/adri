# @ADRI_FEATURE[config_types, scope=OPEN_SOURCE]
# Description: Type definitions for ADRI configuration including resolution strategies
"""
ADRI Configuration Types.

Defines enums, dataclasses, and type definitions used across the ADRI configuration system.
Supports package-local contract resolution for atomic/self-contained package architectures.
"""

from dataclasses import dataclass
from enum import Enum


class ResolutionStrategy(Enum):
    """
    Contract resolution strategy options.

    Determines how ADRI locates contract files when given a contract name.

    Strategies:
        FLAT: Use centralized contracts directory only (traditional/legacy behavior)
        PACKAGE_LOCAL: Use package-local directory only (strict atomic packages)
        HYBRID: Check package-local first, fall back to centralized (recommended for migration)
    """

    FLAT = "flat"
    PACKAGE_LOCAL = "package_local"
    HYBRID = "hybrid"

    @classmethod
    def from_string(cls, value: str) -> "ResolutionStrategy":
        """
        Parse a string value into a ResolutionStrategy.

        Args:
            value: String value like "flat", "package_local", or "hybrid"

        Returns:
            ResolutionStrategy enum value

        Raises:
            ValueError: If value is not a valid strategy
        """
        value_lower = value.lower().strip()
        for strategy in cls:
            if strategy.value == value_lower:
                return strategy
        valid_values = [s.value for s in cls]
        raise ValueError(
            f"Invalid resolution strategy: '{value}'. "
            f"Valid values are: {', '.join(valid_values)}"
        )


@dataclass
class ContractResolutionResult:
    """
    Result of contract path resolution.

    Contains the resolved path and metadata about how it was resolved,
    useful for debugging and audit logging.

    Attributes:
        path: Absolute path to the resolved contract file
        source: How the contract was resolved ("package_local", "centralized", "env_override")
        package_context: Package directory used for resolution (if applicable)
        exists: Whether the contract file actually exists at the resolved path
        strategy_used: The resolution strategy that was applied
    """

    path: str
    source: str
    package_context: str | None = None
    exists: bool = False
    strategy_used: ResolutionStrategy | None = None

    def __str__(self) -> str:
        """Human-readable representation."""
        status = "exists" if self.exists else "NOT FOUND"
        return f"ContractResolutionResult(path={self.path}, source={self.source}, {status})"


@dataclass
class ResolutionConfig:
    """
    Configuration for contract resolution behavior.

    Attributes:
        strategy: Which resolution strategy to use
        package_subdirectory: Subdirectory name within package context (default: "adri")
        fallback_enabled: For hybrid mode, whether to fall back to centralized
    """

    strategy: ResolutionStrategy = ResolutionStrategy.HYBRID
    package_subdirectory: str = "adri"
    fallback_enabled: bool = True

    @classmethod
    def from_dict(cls, config_dict: dict) -> "ResolutionConfig":
        """
        Create ResolutionConfig from a dictionary.

        Args:
            config_dict: Dictionary with resolution configuration

        Returns:
            ResolutionConfig instance
        """
        strategy_str = config_dict.get("strategy", "hybrid")
        strategy = ResolutionStrategy.from_string(strategy_str)

        return cls(
            strategy=strategy,
            package_subdirectory=config_dict.get("package_subdirectory", "adri"),
            fallback_enabled=config_dict.get("fallback_enabled", True),
        )


# @ADRI_FEATURE_END[config_types]
