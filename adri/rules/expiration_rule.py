"""
ExpirationCheckRule implementation for ADRI.
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Union

from .base import DiagnosticRule
from .registry import RuleRegistry

logger = logging.getLogger(__name__)


@RuleRegistry.register
class ExpirationCheckRule(DiagnosticRule):
    """
    Check if data has expired based on domain-specific rules.
    
    This rule verifies that data is still valid based on expiration
    criteria such as explicit expiration dates or domain-specific
    time-to-live configurations.
    """
    
    rule_id = "freshness.expiration"
    dimension = "freshness"
    name = "Expiration Check"
    description = "Verifies that data has not expired based on domain-specific rules."
    version = "1.0.0"
    
    def _get_parameter_metadata(self) -> List[Dict[str, Any]]:
        """Get metadata about the parameters this rule accepts."""
        return [
            {
                "name": "enabled",
                "type": "boolean",
                "default": True,
                "description": "Whether this rule is enabled"
            },
            {
                "name": "weight",
                "type": "float",
                "default": 1.5,
                "description": "Importance weight of this rule in the overall assessment"
            },
            {
                "name": "expiration_column",
                "type": "string",
                "default": "",
                "description": "Name of column containing expiration dates (if available)"
            },
            {
                "name": "creation_column",
                "type": "string",
                "default": "",
                "description": "Name of column containing creation dates"
            },
            {
                "name": "ttl_days",
                "type": "integer",
                "default": 90,
                "description": "Time-to-live in days (used if no expiration column)"
            },
            {
                "name": "reference_time",
                "type": "string",
                "default": "",
                "description": "Reference timestamp (default is current time)"
            },
            {
                "name": "expiration_warning_days",
                "type": "integer",
                "default": 15,
                "description": "Days before expiration to issue warnings"
            }
        ]
    
    def evaluate(self, data: Union[pd.DataFrame, Any]) -> Dict[str, Any]:
        """
        Evaluate if data has expired.
        
        Args:
            data: Either a pandas DataFrame or a connector object
            
        Returns:
            Dict containing evaluation results
        """
        if not self.enabled:
            return {
                "score": 0,
                "valid": True,
                "processed": False,
                "reason": "Rule disabled"
            }
        
        # Extract DataFrame from connector if needed
        if hasattr(data, 'df'):
            df = data.df
        elif isinstance(data, pd.DataFrame):
            df = data
        else:
            return {
                "score": 0,
                "valid": False,
                "processed": False,
                "reason": "Unsupported data type"
            }
        
        # Get parameters
        expiration_column = self.params.get("expiration_column", "")
        creation_column = self.params.get("creation_column", "")
        ttl_days = self.params.get("ttl_days", 90)
        expiration_warning_days = self.params.get("expiration_warning_days", 15)
        reference_time_str = self.params.get("reference_time", "")
        weight = self.params.get("weight", 1.5)
        
        # Get reference time
        if reference_time_str:
            try:
                reference_time = pd.to_datetime(reference_time_str)
            except Exception as e:
                logger.warning(f"Failed to parse reference_time '{reference_time_str}': {str(e)}")
                reference_time = pd.Timestamp.now()
        else:
            reference_time = pd.Timestamp.now()
        
        # Check if we have explicit expiration dates or need to calculate them
        use_explicit_expiration = expiration_column in df.columns
        use_calculated_expiration = creation_column in df.columns
        
        if not use_explicit_expiration and not use_calculated_expiration:
            return {
                "score": 0,
                "valid": False,
                "processed": False,
                "reason": "Neither expiration nor creation column specified or found"
            }
        
        # Initialize result components
        total_records = len(df)
        expired_count = 0
        warning_count = 0
        valid_count = 0
        examples = {}
        
        if use_explicit_expiration:
            # Use explicit expiration dates
            try:
                expiration_dates = pd.to_datetime(df[expiration_column])
                
                # Check expiration status
                expired_mask = (expiration_dates <= reference_time) & ~expiration_dates.isna()
                warning_mask = ((expiration_dates > reference_time) & 
                               (expiration_dates <= reference_time + pd.Timedelta(days=expiration_warning_days)) &
                               ~expiration_dates.isna())
                valid_mask = ((expiration_dates > reference_time + pd.Timedelta(days=expiration_warning_days)) |
                             expiration_dates.isna())
                
                expired_count = expired_mask.sum()
                warning_count = warning_mask.sum()
                valid_count = valid_mask.sum()
                
                # Get example records
                if expired_count > 0:
                    expired_indices = df.index[expired_mask].tolist()[:5]  # Get up to 5 examples
                    expired_values = expiration_dates[expired_indices].tolist()
                    examples["expired"] = list(zip(expired_indices, [str(val) for val in expired_values]))
                
                if warning_count > 0:
                    warning_indices = df.index[warning_mask].tolist()[:5]  # Get up to 5 examples
                    warning_values = expiration_dates[warning_indices].tolist()
                    examples["warning"] = list(zip(warning_indices, [str(val) for val in warning_values]))
                
            except Exception as e:
                return {
                    "score": 0,
                    "valid": False,
                    "processed": False,
                    "reason": f"Failed to process expiration dates: {str(e)}"
                }
                
        elif use_calculated_expiration:
            # Calculate expiration based on creation dates + TTL
            try:
                creation_dates = pd.to_datetime(df[creation_column])
                calculated_expiration = creation_dates + pd.Timedelta(days=ttl_days)
                
                # Check expiration status
                expired_mask = (calculated_expiration <= reference_time) & ~creation_dates.isna()
                warning_mask = ((calculated_expiration > reference_time) & 
                               (calculated_expiration <= reference_time + pd.Timedelta(days=expiration_warning_days)) &
                               ~creation_dates.isna())
                valid_mask = ((calculated_expiration > reference_time + pd.Timedelta(days=expiration_warning_days)) |
                             creation_dates.isna())
                
                expired_count = expired_mask.sum()
                warning_count = warning_mask.sum()
                valid_count = valid_mask.sum()
                
                # Get example records
                if expired_count > 0:
                    expired_indices = df.index[expired_mask].tolist()[:5]  # Get up to 5 examples
                    expired_values = calculated_expiration[expired_indices].tolist()
                    examples["expired"] = list(zip(expired_indices, [str(val) for val in expired_values]))
                
                if warning_count > 0:
                    warning_indices = df.index[warning_mask].tolist()[:5]  # Get up to 5 examples
                    warning_values = calculated_expiration[warning_indices].tolist()
                    examples["warning"] = list(zip(warning_indices, [str(val) for val in warning_values]))
                
            except Exception as e:
                return {
                    "score": 0,
                    "valid": False,
                    "processed": False,
                    "reason": f"Failed to process creation dates: {str(e)}"
                }
        
        # Calculate freshness ratio based on expiration
        total_valid_records = expired_count + warning_count + valid_count
        if total_valid_records > 0:
            # - Valid values get full weight
            # - Warning values get partial weight
            # - Expired values get no weight
            freshness_ratio = (valid_count + (warning_count * 0.5)) / total_valid_records
        else:
            freshness_ratio = 0.0
        
        # Calculate score
        score = weight * freshness_ratio
        score = max(0, min(weight, score))
        
        return {
            "score": score,
            "valid": expired_count == 0,
            "reference_time": str(reference_time),
            "ttl_days": ttl_days if use_calculated_expiration else None,
            "expiration_warning_days": expiration_warning_days,
            "total_records": total_records,
            "valid_count": int(valid_count),
            "warning_count": int(warning_count),
            "expired_count": int(expired_count),
            "examples": examples
        }
    
    def generate_narrative(self, result: Dict[str, Any]) -> str:
        """
        Generate a narrative description of the rule evaluation result.
        
        Args:
            result: The result from evaluate()
            
        Returns:
            String containing the narrative description
        """
        if not result.get("processed", True):
            return f"Expiration check was not performed: {result.get('reason', 'Unknown reason')}"
        
        reference_time = result.get("reference_time", "")
        ttl_days = result.get("ttl_days")
        expiration_warning_days = result.get("expiration_warning_days", 15)
        
        valid_count = result.get("valid_count", 0)
        warning_count = result.get("warning_count", 0)
        expired_count = result.get("expired_count", 0)
        total_records = result.get("total_records", 0)
        
        # Calculate percentages
        if total_records > 0:
            valid_percent = (valid_count / total_records) * 100
            warning_percent = (warning_count / total_records) * 100
            expired_percent = (expired_count / total_records) * 100
        else:
            valid_percent = warning_percent = expired_percent = 0.0
        
        if result.get("valid", False):
            if warning_count > 0:
                return (
                    f"No data has expired as of {reference_time}. "
                    f"{valid_percent:.1f}% of records are valid and "
                    f"{warning_percent:.1f}% are approaching expiration "
                    f"within the next {expiration_warning_days} days."
                )
            else:
                if ttl_days:
                    return (
                        f"All data is valid with no expirations detected. "
                        f"All records are more than {expiration_warning_days} days "
                        f"away from their calculated expiration date (TTL: {ttl_days} days)."
                    )
                else:
                    return (
                        f"All data is valid with no expirations detected. "
                        f"All records are more than {expiration_warning_days} days "
                        f"away from their explicit expiration date."
                    )
        
        # Generate detailed description for failures
        examples = result.get("examples", {})
        expired_examples = examples.get("expired", [])
        
        narrative = (
            f"{expired_percent:.1f}% of records ({expired_count} out of {total_records}) "
            f"have expired as of {reference_time}. "
            f"Additionally, {warning_percent:.1f}% ({warning_count}) of records will expire "
            f"within the next {expiration_warning_days} days."
        )
        
        if expired_examples:
            example_strs = []
            for idx, val in expired_examples[:3]:
                example_strs.append(f"record at index {idx}: expired on {val}")
                
            narrative += f" Examples of expired records: {'; '.join(example_strs)}."
        
        # Add recommendation
        narrative += (
            " Expired data should be refreshed, archived, or explicitly marked as historical "
            "to avoid using outdated information in analyses and reports."
        )
        
        return narrative

# ----------------------------------------------
# TEST COVERAGE
# ----------------------------------------------
# This component is tested through:
# 
# 1. Unit tests:
#    - tests/unit/dimensions/test_freshness_basic.py (rule functionality)
# 
# 2. Integration tests:
#    - tests/integration/test_cli.py (rule execution in CLI context)
#
# 3. Test datasets:
#    - test_datasets/stale_dataset.csv (for expiration detection)
#    - test_datasets/ideal_dataset.csv (for valid data case)
#
# Complete test coverage details are documented in:
# docs/test_coverage/FRESHNESS_test_coverage.md
# ----------------------------------------------
