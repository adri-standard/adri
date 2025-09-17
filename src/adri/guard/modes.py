"""
ADRI Guard Modes

Protection mode classes extracted and refactored from the original core/protection.py.
Provides clean separation of different protection strategies.
"""

import logging
import os
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

import pandas as pd

# Updated imports for new structure - with fallbacks during migration
try:
    from ..validator.engine import ValidationEngine
    from ..config.loader import ConfigurationLoader
    from ..logging.local import LocalLogger
    from ..logging.enterprise import EnterpriseLogger
except ImportError:
    # Fallback to legacy imports during migration
    try:
        from adri.core.assessor import AssessmentEngine as ValidationEngine
        from adri.config.manager import ConfigManager as ConfigurationLoader
        from adri.core.audit_logger_csv import CSVAuditLogger as LocalLogger
        from adri.core.verodat_logger import VerodatLogger as EnterpriseLogger
    except ImportError:
        ValidationEngine = None
        ConfigurationLoader = None
        LocalLogger = None
        EnterpriseLogger = None

logger = logging.getLogger(__name__)


class ProtectionError(Exception):
    """Exception raised when data protection fails."""
    pass


class ProtectionMode(ABC):
    """
    Base class for all protection modes.
    
    Defines the interface that all protection modes must implement.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize protection mode with configuration."""
        self.config = config or {}
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    @abstractmethod
    def handle_failure(self, assessment_result: Any, error_message: str) -> None:
        """
        Handle assessment failure based on this protection mode's strategy.
        
        Args:
            assessment_result: The failed assessment result
            error_message: Formatted error message
            
        Raises:
            ProtectionError: If the mode requires stopping execution
        """
        pass
    
    @abstractmethod
    def handle_success(self, assessment_result: Any, success_message: str) -> None:
        """
        Handle assessment success based on this protection mode's strategy.
        
        Args:
            assessment_result: The successful assessment result  
            success_message: Formatted success message
        """
        pass
    
    @property
    @abstractmethod
    def mode_name(self) -> str:
        """Return the name of this protection mode."""
        pass
    
    def get_description(self) -> str:
        """Return a description of what this protection mode does."""
        return f"{self.mode_name} protection mode"


class FailFastMode(ProtectionMode):
    """
    Fail-fast protection mode.
    
    Immediately raises an exception when data quality is insufficient.
    This is the strictest protection mode - no bad data passes through.
    """
    
    @property
    def mode_name(self) -> str:
        return "fail-fast"
    
    def handle_failure(self, assessment_result: Any, error_message: str) -> None:
        """Raise ProtectionError to stop execution immediately."""
        self.logger.error(f"Fail-fast mode: {error_message}")
        raise ProtectionError(error_message)
    
    def handle_success(self, assessment_result: Any, success_message: str) -> None:
        """Log success and continue execution."""
        self.logger.info(f"Fail-fast mode success: {success_message}")
        print(success_message)
    
    def get_description(self) -> str:
        return "Fail-fast mode: Immediately stops execution when data quality is insufficient"


class SelectiveMode(ProtectionMode):
    """
    Selective protection mode.
    
    Continues execution but logs failures for later review.
    Allows some flexibility while maintaining audit trail.
    """
    
    @property 
    def mode_name(self) -> str:
        return "selective"
    
    def handle_failure(self, assessment_result: Any, error_message: str) -> None:
        """Log failure but continue execution."""
        self.logger.warning(f"Selective mode: Data quality issue detected but continuing - {error_message}")
        print(f"⚠️  ADRI Warning: Data quality below threshold but continuing execution")
        print(f"📊 Score: {assessment_result.overall_score:.1f}")
    
    def handle_success(self, assessment_result: Any, success_message: str) -> None:
        """Log success and continue execution."""
        self.logger.debug(f"Selective mode success: {success_message}")
        print(f"✅ ADRI: Quality check passed ({assessment_result.overall_score:.1f}/100)")
    
    def get_description(self) -> str:
        return "Selective mode: Logs quality issues but continues execution"


class WarnOnlyMode(ProtectionMode):
    """
    Warn-only protection mode.
    
    Shows warnings for quality issues but never stops execution.
    Useful for monitoring without impacting production workflows.
    """
    
    @property
    def mode_name(self) -> str:
        return "warn-only"
    
    def handle_failure(self, assessment_result: Any, error_message: str) -> None:
        """Show warning but continue execution."""
        self.logger.warning(f"Warn-only mode: {error_message}")
        print(f"⚠️  ADRI Data Quality Warning:")
        print(f"📊 Score: {assessment_result.overall_score:.1f} (below threshold)")
        print(f"💡 Consider improving data quality for better AI agent performance")
    
    def handle_success(self, assessment_result: Any, success_message: str) -> None:
        """Log success quietly."""
        self.logger.debug(f"Warn-only mode success: {success_message}")
        print(f"✅ ADRI: Data quality check passed")
    
    def get_description(self) -> str:
        return "Warn-only mode: Shows warnings but never stops execution"


class DataProtectionEngine:
    """
    Main data protection engine using configurable protection modes.
    
    Refactored from the original DataProtectionEngine to use the new mode-based architecture.
    """
    
    def __init__(self, protection_mode: Optional[ProtectionMode] = None):
        """
        Initialize the data protection engine.
        
        Args:
            protection_mode: Protection mode to use (defaults to FailFastMode)
        """
        self.protection_mode = protection_mode or FailFastMode()
        self.config_manager = ConfigurationLoader() if ConfigurationLoader else None
        self.protection_config = self._load_protection_config()
        self._assessment_cache = {}
        self.logger = logging.getLogger(__name__)
        
        # Initialize loggers with proper configuration
        self.local_logger = LocalLogger() if LocalLogger else None
        self.enterprise_logger = EnterpriseLogger(self.protection_config) if EnterpriseLogger else None
        
        self.logger.debug(f"DataProtectionEngine initialized with {self.protection_mode.mode_name} mode")
    
    def _load_protection_config(self) -> Dict[str, Any]:
        """Load protection configuration."""
        if self.config_manager:
            try:
                return self.config_manager.get_protection_config()
            except:
                pass
        
        # Return default config
        return {
            "default_min_score": 80,
            "default_failure_mode": "raise",
            "auto_generate_standards": True,
            "cache_duration_hours": 1,
            "verbose_protection": False,
        }
    
    def protect_function_call(
        self,
        func: Callable,
        args: tuple,
        kwargs: dict,
        data_param: str,
        function_name: str,
        standard_file: Optional[str] = None,
        standard_name: Optional[str] = None,
        min_score: Optional[float] = None,
        dimensions: Optional[Dict[str, float]] = None,
        on_failure: Optional[str] = None,
        auto_generate: Optional[bool] = None,
        cache_assessments: Optional[bool] = None,
        verbose: Optional[bool] = None,
    ) -> Any:
        """
        Protect a function call with data quality checks.
        
        Args:
            func: Function to protect
            args: Function positional arguments  
            kwargs: Function keyword arguments
            data_param: Name of parameter containing data to check
            function_name: Name of the function being protected
            standard_file: Explicit standard file to use
            standard_name: Custom standard name
            min_score: Minimum quality score required
            dimensions: Specific dimension requirements
            on_failure: How to handle quality failures (overrides protection mode)
            auto_generate: Whether to auto-generate missing standards
            cache_assessments: Whether to cache assessment results
            verbose: Whether to show verbose output
            
        Returns:
            Result of the protected function call
            
        Raises:
            ValueError: If data parameter is not found
            ProtectionError: If data quality is insufficient (fail-fast mode)
        """
        # Apply configuration defaults
        min_score = min_score if min_score is not None else self.protection_config.get("default_min_score", 80)
        verbose = verbose if verbose is not None else self.protection_config.get("verbose_protection", False)
        
        # Override protection mode if on_failure is specified
        effective_mode = self.protection_mode
        if on_failure:
            if on_failure == "raise":
                effective_mode = FailFastMode(self.protection_config)
            elif on_failure == "warn":
                effective_mode = WarnOnlyMode(self.protection_config)
            elif on_failure == "continue":
                effective_mode = SelectiveMode(self.protection_config)
        
        if verbose:
            self.logger.info(f"Protecting function '{function_name}' with {effective_mode.mode_name} mode, min_score={min_score}")
        
        try:
            # Extract data from function parameters
            data = self._extract_data_parameter(func, args, kwargs, data_param)
            
            # Resolve and ensure standard exists
            standard = self._resolve_standard(function_name, data_param, standard_file, standard_name)
            self._ensure_standard_exists(standard, data)
            
            # Assess data quality
            start_time = time.time()
            assessment_result = self._assess_data_quality(data, standard)
            assessment_duration = time.time() - start_time
            
            if verbose:
                self.logger.info(f"Assessment completed in {assessment_duration:.2f}s, score: {assessment_result.overall_score:.1f}")
            
            # Check if assessment passed
            assessment_passed = assessment_result.overall_score >= min_score
            
            # Check dimension requirements if specified
            if dimensions and assessment_passed:
                assessment_passed = self._check_dimension_requirements(assessment_result, dimensions)
            
            # Handle result based on protection mode
            if assessment_passed:
                success_message = self._format_success_message(assessment_result, min_score, standard, function_name, verbose)
                effective_mode.handle_success(assessment_result, success_message)
            else:
                error_message = self._format_error_message(assessment_result, min_score, standard)
                effective_mode.handle_failure(assessment_result, error_message)
            
            # Execute the protected function
            return func(*args, **kwargs)
            
        except ProtectionError:
            # Re-raise protection errors (from fail-fast mode)
            raise
        except Exception as e:
            self.logger.error(f"Protection engine error: {e}")
            raise ProtectionError(f"Data protection failed: {e}")
    
    def _extract_data_parameter(self, func: Callable, args: tuple, kwargs: dict, data_param: str) -> Any:
        """Extract the data parameter from function arguments."""
        import inspect
        
        # Check kwargs first
        if data_param in kwargs:
            return kwargs[data_param]
        
        # Check positional args
        try:
            sig = inspect.signature(func)
            params = list(sig.parameters.keys())
            if data_param in params:
                param_index = params.index(data_param)
                if param_index < len(args):
                    return args[param_index]
        except Exception as e:
            self.logger.warning(f"Could not inspect function signature: {e}")
        
        raise ValueError(
            f"Could not find data parameter '{data_param}' in function arguments.\n"
            f"Available kwargs: {list(kwargs.keys())}\n"
            f"Available positional args: {len(args)} arguments"
        )
    
    def _resolve_standard(
        self, 
        function_name: str, 
        data_param: str, 
        standard_file: Optional[str] = None,
        standard_name: Optional[str] = None,
    ) -> str:
        """Resolve which standard to use for protection."""
        if standard_file:
            return standard_file
        
        if standard_name:
            return f"{standard_name}.yaml"
        
        # Auto-generate standard name
        pattern = self.protection_config.get("standard_naming_pattern", "{function_name}_{data_param}_standard.yaml")
        return pattern.format(function_name=function_name, data_param=data_param)
    
    def _ensure_standard_exists(self, standard_path: str, sample_data: Any) -> None:
        """Ensure a standard exists, generating it if necessary."""
        if os.path.exists(standard_path):
            return
        
        if not self.protection_config.get("auto_generate_standards", True):
            raise ProtectionError(f"Standard file not found: {standard_path}")
        
        self.logger.info(f"Generating new standard: {standard_path}")
        
        try:
            # Create directory if needed
            dir_path = os.path.dirname(standard_path)
            if dir_path:  # Only create directory if there is one
                os.makedirs(dir_path, exist_ok=True)
            
            # Convert data to DataFrame
            if not isinstance(sample_data, pd.DataFrame):
                if isinstance(sample_data, list):
                    df = pd.DataFrame(sample_data)
                elif isinstance(sample_data, dict):
                    # Handle dict with scalar values by wrapping in a list
                    df = pd.DataFrame([sample_data])
                else:
                    raise ProtectionError(f"Cannot generate standard from data type: {type(sample_data)}")
            else:
                df = sample_data
            
            # Generate basic standard
            self._generate_basic_standard(df, standard_path)
            
        except Exception as e:
            raise ProtectionError(f"Failed to generate standard: {e}")
    
    def _generate_basic_standard(self, df: pd.DataFrame, standard_path: str) -> None:
        """Generate a basic YAML standard from DataFrame."""
        import yaml
        
        # Generate field requirements
        field_requirements = {}
        for column in df.columns:
            non_null_data = df[column].dropna()
            if len(non_null_data) == 0:
                field_type = "string"
            elif non_null_data.dtype in ['int64', 'int32']:
                field_type = "integer"
            elif non_null_data.dtype in ['float64', 'float32']:
                field_type = "float"
            else:
                field_type = "string"
            
            nullable = df[column].isnull().any()
            field_requirements[column] = {"type": field_type, "nullable": nullable}
        
        # Create standard structure
        data_name = Path(standard_path).stem.replace("_standard", "")
        standard = {
            "standards": {
                "id": f"{data_name}_standard",
                "name": f"{data_name} ADRI Standard",
                "version": "1.0.0",
                "authority": "ADRI Framework",
                "description": f"Auto-generated standard for {data_name} data"
            },
            "requirements": {
                "overall_minimum": 75.0,
                "field_requirements": field_requirements,
                "dimension_requirements": {
                    "validity": {"minimum_score": 15.0},
                    "completeness": {"minimum_score": 15.0},
                    "consistency": {"minimum_score": 12.0},
                    "freshness": {"minimum_score": 15.0},
                    "plausibility": {"minimum_score": 12.0}
                }
            }
        }
        
        # Save standard
        with open(standard_path, 'w') as f:
            yaml.dump(standard, f, default_flow_style=False, sort_keys=False)
    
    def _assess_data_quality(self, data: Any, standard_path: str) -> Any:
        """Assess data quality against a standard."""
        if not ValidationEngine:
            raise ProtectionError("Validation engine not available")
        
        # Convert data to DataFrame if needed
        if not isinstance(data, pd.DataFrame):
            if isinstance(data, list):
                df = pd.DataFrame(data)
            elif isinstance(data, dict):
                # Handle dict with scalar values by wrapping in a list
                df = pd.DataFrame([data])
            else:
                raise ProtectionError(f"Cannot assess data type: {type(data)}")
        else:
            df = data
        
        # Run assessment
        engine = ValidationEngine()
        return engine.assess(df, standard_path)
    
    def _check_dimension_requirements(self, assessment_result: Any, dimensions: Dict[str, float]) -> bool:
        """Check dimension-specific requirements."""
        if not hasattr(assessment_result, "dimension_scores"):
            return True
        
        for dim_name, required_score in dimensions.items():
            if dim_name in assessment_result.dimension_scores:
                dim_score_obj = assessment_result.dimension_scores[dim_name]
                actual_score = dim_score_obj.score if hasattr(dim_score_obj, "score") else 0
                if actual_score < required_score:
                    return False
        
        return True
    
    def _format_error_message(self, assessment_result: Any, min_score: float, standard: str) -> str:
        """Format a detailed error message."""
        standard_name = Path(standard).stem.replace("_standard", "")
        
        message_lines = [
            "🛡️ ADRI Protection: BLOCKED ❌",
            "",
            f"📊 Quality Score: {assessment_result.overall_score:.1f}/100 (Required: {min_score:.1f}/100)",
            f"📋 Standard: {standard_name}",
            "",
            "🔧 Fix This:",
            f"   1. Review standard: adri show-standard {standard_name}",
            f"   2. Fix data issues and retry",
            f"   3. Test fixes: adri assess <data> --standard {standard_name}",
        ]
        
        return "\n".join(message_lines)
    
    def _format_success_message(self, assessment_result: Any, min_score: float, standard: str, function_name: str, verbose: bool) -> str:
        """Format a success message."""
        standard_name = Path(standard).stem.replace("_standard", "")
        
        if verbose:
            return (
                f"🛡️ ADRI Protection: ALLOWED ✅\n"
                f"📊 Quality Score: {assessment_result.overall_score:.1f}/100 (Required: {min_score:.1f}/100)\n"
                f"📋 Standard: {standard_name}\n"
                f"🚀 Function: {function_name}"
            )
        else:
            return (
                f"🛡️ ADRI Protection: ALLOWED ✅\n"
                f"📊 Score: {assessment_result.overall_score:.1f}/100 | Standard: {standard_name}"
            )


# Mode factory functions
def fail_fast_mode(config: Optional[Dict[str, Any]] = None) -> FailFastMode:
    """Create a fail-fast protection mode."""
    return FailFastMode(config)


def selective_mode(config: Optional[Dict[str, Any]] = None) -> SelectiveMode:
    """Create a selective protection mode."""
    return SelectiveMode(config)


def warn_only_mode(config: Optional[Dict[str, Any]] = None) -> WarnOnlyMode:
    """Create a warn-only protection mode."""
    return WarnOnlyMode(config)
