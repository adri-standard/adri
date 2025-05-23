"""
Completeness dimension rules for ADRI.

This module provides rule implementations for assessing the completeness
dimension of data quality, including required field validation,
population density analysis, and schema completeness checking.
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Union, Set

from .base import DiagnosticRule
from .registry import RuleRegistry

logger = logging.getLogger(__name__)


@RuleRegistry.register
class RequiredFieldRule(DiagnosticRule):
    """
    Check if required fields contain non-null values.
    
    This rule validates that specified fields, considered required for data
    completeness, are populated with non-null values.
    """
    
    rule_id = "completeness.required_fields"
    dimension = "completeness"
    name = "Required Field Check"
    description = "Checks if required fields contain non-null values."
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
                "default": 2.0,
                "description": "Importance weight of this rule in the overall assessment"
            },
            {
                "name": "required_fields",
                "type": "array",
                "default": [],
                "description": "List of field names that are required (must not be null)"
            },
            {
                "name": "threshold",
                "type": "float",
                "default": 1.0,
                "description": "Minimum acceptable completeness rate (0.0-1.0)"
            }
        ]
    
    def evaluate(self, data: Union[pd.DataFrame, Any]) -> Dict[str, Any]:
        """
        Evaluate this rule against the provided data.
        
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
        required_fields = self.params.get("required_fields", [])
        threshold = self.params.get("threshold", 1.0)
        weight = self.params.get("weight", 2.0)
        
        if not required_fields:
            return {
                "score": weight,
                "valid": True,
                "processed": False,
                "reason": "No required fields specified"
            }
        
        # Find missing required fields
        missing_fields = [field for field in required_fields if field not in df.columns]
        if missing_fields:
            return {
                "score": 0,
                "valid": False,
                "processed": True,
                "missing_fields": missing_fields,
                "message": f"Required fields missing from dataset: {', '.join(missing_fields)}"
            }
        
        # Analyze each required field
        field_results = {}
        total_records = len(df)
        total_missing = 0
        
        for field in required_fields:
            null_count = df[field].isna().sum()
            completeness_rate = 1.0 - (null_count / total_records if total_records > 0 else 0)
            
            # Collect missing value examples
            if null_count > 0:
                missing_indices = df[df[field].isna()].index.tolist()[:5]  # Get up to 5 examples
            else:
                missing_indices = []
                
            field_results[field] = {
                "null_count": int(null_count),
                "completeness_rate": float(completeness_rate),
                "missing_indices": missing_indices
            }
            
            total_missing += null_count
        
        # Calculate overall completeness rate
        total_required_values = total_records * len(required_fields)
        overall_completeness = 1.0 - (total_missing / total_required_values if total_required_values > 0 else 0)
        
        # Determine score based on completeness
        score = weight * min(1.0, overall_completeness / threshold) if threshold > 0 else 0
        score = max(0, min(weight, score))
        
        return {
            "score": score,
            "valid": overall_completeness >= threshold,
            "total_records": total_records,
            "total_missing": int(total_missing),
            "overall_completeness": float(overall_completeness),
            "threshold": threshold,
            "field_results": field_results
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
            return f"Required field check was not performed: {result.get('reason', 'Unknown reason')}"
            
        if "missing_fields" in result:
            missing_fields = result.get("missing_fields", [])
            return f"Required fields are missing from the dataset: {', '.join(missing_fields)}. These fields must be added to the dataset."
        
        total_records = result.get("total_records", 0)
        if total_records == 0:
            return "No records were available for required field analysis."
            
        overall_completeness = result.get("overall_completeness", 0) * 100  # Convert to percentage
        threshold = result.get("threshold", 1.0) * 100  # Convert to percentage
        field_results = result.get("field_results", {})
        
        if result.get("valid", False):
            return (
                f"Required fields are {overall_completeness:.1f}% complete across {total_records} records, "
                f"which meets or exceeds the {threshold:.1f}% threshold."
            )
        
        # Generate detailed description for failures
        narrative = (
            f"Required fields are only {overall_completeness:.1f}% complete, below the required "
            f"{threshold:.1f}% threshold. "
        )
        
        # Add details about problematic fields
        problem_fields = [(field, details) for field, details in field_results.items() 
                         if details.get("null_count", 0) > 0]
        problem_fields.sort(key=lambda x: x[1].get("null_count", 0), reverse=True)
        
        if problem_fields:
            # Add info about most problematic fields
            field_details = []
            for field, details in problem_fields[:3]:  # Show top 3 worst fields
                null_count = details.get("null_count", 0)
                completeness = details.get("completeness_rate", 0) * 100
                missing_indices = details.get("missing_indices", [])
                
                if missing_indices:
                    indices_str = ", ".join(str(idx) for idx in missing_indices[:3])
                    if len(missing_indices) > 3:
                        indices_str += f", and {len(missing_indices) - 3} more"
                        
                    field_details.append(
                        f"Field '{field}' has {null_count} missing values ({completeness:.1f}% complete). "
                        f"Missing at indices: {indices_str}."
                    )
                else:
                    field_details.append(
                        f"Field '{field}' has {null_count} missing values ({completeness:.1f}% complete)."
                    )
            
            narrative += " ".join(field_details)
        
        # Add recommendation
        narrative += (
            " Missing values in required fields impact data usability and quality. "
            "Consider addressing these gaps through data collection improvements, imputation, "
            "or by explicitly indicating why values are missing."
        )
        
        return narrative


@RuleRegistry.register
class PopulationDensityRule(DiagnosticRule):
    """
    Analyze the overall density of populated values across the dataset.
    
    This rule assesses the proportion of non-null values across all fields,
    identifying sparsely populated areas of the dataset.
    """
    
    rule_id = "completeness.population_density"
    dimension = "completeness"
    name = "Population Density Analysis"
    description = "Analyzes the overall density of populated values across the dataset."
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
                "name": "threshold",
                "type": "float", 
                "default": 0.75,
                "description": "Minimum acceptable overall population density (0.0-1.0)"
            },
            {
                "name": "column_threshold",
                "type": "float",
                "default": 0.5,
                "description": "Minimum acceptable population density per column (0.0-1.0)"
            },
            {
                "name": "exclude_columns",
                "type": "array",
                "default": [],
                "description": "List of columns to exclude from density analysis"
            }
        ]
    
    def evaluate(self, data: Union[pd.DataFrame, Any]) -> Dict[str, Any]:
        """
        Evaluate the overall population density of the dataset.
        
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
        threshold = self.params.get("threshold", 0.75)
        column_threshold = self.params.get("column_threshold", 0.5)
        exclude_columns = self.params.get("exclude_columns", [])
        weight = self.params.get("weight", 1.5)
        
        # Filter out excluded columns
        included_columns = [col for col in df.columns if col not in exclude_columns]
        
        if not included_columns:
            return {
                "score": weight,
                "valid": True,
                "processed": False,
                "reason": "No columns to analyze (all excluded)"
            }
            
        # Create filtered dataframe
        filtered_df = df[included_columns]
        
        # Calculate overall density
        total_cells = filtered_df.size
        null_cells = filtered_df.isna().sum().sum()
        
        if total_cells == 0:
            overall_density = 1.0  # Avoid division by zero
        else:
            overall_density = 1.0 - (null_cells / total_cells)
        
        # Calculate per-column density
        column_results = {}
        sparse_columns = 0
        
        for col in included_columns:
            null_count = filtered_df[col].isna().sum()
            total_count = len(filtered_df)
            
            if total_count == 0:
                density = 1.0  # Avoid division by zero
            else:
                density = 1.0 - (null_count / total_count)
                
            is_sparse = density < column_threshold
            
            if is_sparse:
                sparse_columns += 1
                
            column_results[col] = {
                "density": float(density),
                "null_count": int(null_count),
                "is_sparse": is_sparse
            }
        
        # Calculate score
        if threshold > 0:
            score = weight * min(1.0, overall_density / threshold)
        else:
            score = 0
            
        score = max(0, min(weight, score))
        
        return {
            "score": score,
            "valid": overall_density >= threshold,
            "overall_density": float(overall_density),
            "total_cells": int(total_cells),
            "null_cells": int(null_cells),
            "threshold": threshold,
            "column_threshold": column_threshold,
            "columns_analyzed": len(included_columns),
            "sparse_columns": sparse_columns,
            "column_results": column_results
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
            return f"Population density analysis was not performed: {result.get('reason', 'Unknown reason')}"
        
        overall_density = result.get("overall_density", 0) * 100  # Convert to percentage
        threshold = result.get("threshold", 0.75) * 100  # Convert to percentage
        sparse_columns = result.get("sparse_columns", 0)
        columns_analyzed = result.get("columns_analyzed", 0)
        column_threshold = result.get("column_threshold", 0.5) * 100  # Convert to percentage
        
        if result.get("valid", False):
            if sparse_columns > 0:
                return (
                    f"Data has a good overall population density of {overall_density:.1f}% (above the {threshold:.1f}% threshold), "
                    f"however {sparse_columns} out of {columns_analyzed} columns are sparsely populated "
                    f"(below {column_threshold:.1f}% density)."
                )
            else:
                return (
                    f"Data has a good overall population density of {overall_density:.1f}% (above the {threshold:.1f}% threshold), "
                    f"with all {columns_analyzed} columns meeting the minimum density requirement of {column_threshold:.1f}%."
                )
        
        # Generate detailed description for failures
        narrative = (
            f"Data has a low overall population density of {overall_density:.1f}%, below the {threshold:.1f}% threshold. "
            f"In addition, {sparse_columns} out of {columns_analyzed} columns are sparsely populated "
            f"(below {column_threshold:.1f}% density). "
        )
        
        # Add details about sparse columns
        column_results = result.get("column_results", {})
        sparse_cols = [(col, details) for col, details in column_results.items() if details.get("is_sparse", False)]
        sparse_cols.sort(key=lambda x: x[1].get("density", 0))
        
        if sparse_cols:
            # Add info about most sparse columns
            col_details = []
            for col, details in sparse_cols[:3]:  # Show top 3 sparsest columns
                density = details.get("density", 0) * 100
                null_count = details.get("null_count", 0)
                
                col_details.append(
                    f"Column '{col}' is only {density:.1f}% populated ({null_count} missing values)."
                )
            
            narrative += " ".join(col_details)
        
        # Add recommendation
        narrative += (
            " Low population density reduces the analytical value of the dataset. "
            "Consider collecting more complete data, removing consistently empty columns, "
            "or imputing missing values where appropriate."
        )
        
        return narrative


@RuleRegistry.register
class SchemaCompletenessRule(DiagnosticRule):
    """
    Check if all expected fields are present in the dataset.
    
    This rule verifies that the dataset contains all fields defined in a reference
    schema or expected field list, ensuring structural completeness.
    """
    
    rule_id = "completeness.schema"
    dimension = "completeness"
    name = "Schema Completeness"
    description = "Checks if all expected fields are present in the dataset."
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
                "default": 2.0,
                "description": "Importance weight of this rule in the overall assessment"
            },
            {
                "name": "expected_fields",
                "type": "array",
                "default": [],
                "description": "List of field names expected to be present in the dataset"
            },
            {
                "name": "allow_extra_fields",
                "type": "boolean",
                "default": True,
                "description": "Whether additional fields beyond expected ones are allowed"
            },
            {
                "name": "case_sensitive",
                "type": "boolean",
                "default": True,
                "description": "Whether field name matching is case-sensitive"
            }
        ]
    
    def evaluate(self, data: Union[pd.DataFrame, Any]) -> Dict[str, Any]:
        """
        Evaluate schema completeness of the dataset.
        
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
        expected_fields = self.params.get("expected_fields", [])
        allow_extra_fields = self.params.get("allow_extra_fields", True)
        case_sensitive = self.params.get("case_sensitive", True)
        weight = self.params.get("weight", 2.0)
        
        if not expected_fields:
            return {
                "score": weight,
                "valid": True,
                "processed": False,
                "reason": "No expected fields specified"
            }
        
        # Get actual fields
        actual_fields = list(df.columns)
        
        # Prepare for comparison
        if not case_sensitive:
            expected_fields_normalized = [field.lower() for field in expected_fields]
            actual_fields_normalized = [field.lower() for field in actual_fields]
        else:
            expected_fields_normalized = expected_fields
            actual_fields_normalized = actual_fields
            
        # Find missing and extra fields
        expected_set = set(expected_fields_normalized)
        actual_set = set(actual_fields_normalized)
        
        missing_fields_indices = [i for i, field in enumerate(expected_fields_normalized) if field not in actual_set]
        missing_fields = [expected_fields[i] for i in missing_fields_indices]
        
        extra_fields_indices = [i for i, field in enumerate(actual_fields_normalized) if field not in expected_set]
        extra_fields = [actual_fields[i] for i in extra_fields_indices]
        
        # Determine if schema is complete
        is_complete = len(missing_fields) == 0
        
        # Check for extra fields if not allowed
        is_valid = is_complete and (allow_extra_fields or len(extra_fields) == 0)
        
        # Calculate score
        if len(expected_fields) > 0:
            completeness_ratio = 1.0 - (len(missing_fields) / len(expected_fields))
        else:
            completeness_ratio = 1.0
            
        # Penalize for extra fields if not allowed
        if not allow_extra_fields and len(actual_fields) > 0:
            extra_field_penalty = len(extra_fields) / len(actual_fields)
            completeness_ratio = completeness_ratio * (1.0 - extra_field_penalty * 0.5)
            
        score = weight * completeness_ratio
        score = max(0, min(weight, score))
        
        return {
            "score": score,
            "valid": is_valid,
            "schema_complete": is_complete,
            "expected_fields": expected_fields,
            "actual_fields": actual_fields,
            "missing_fields": missing_fields,
            "extra_fields": extra_fields,
            "allow_extra_fields": allow_extra_fields
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
            return f"Schema completeness check was not performed: {result.get('reason', 'Unknown reason')}"
        
        expected_count = len(result.get("expected_fields", []))
        actual_count = len(result.get("actual_fields", []))
        missing_fields = result.get("missing_fields", [])
        extra_fields = result.get("extra_fields", [])
        allow_extra = result.get("allow_extra_fields", True)
        
        if result.get("valid", False):
            if len(missing_fields) == 0 and len(extra_fields) == 0:
                return (
                    f"Data schema is complete with exactly the expected {expected_count} fields. "
                    f"No fields are missing or extra."
                )
            elif len(missing_fields) == 0:
                return (
                    f"Data schema contains all {expected_count} expected fields. "
                    f"Additionally, there are {len(extra_fields)} extra fields, which is allowed "
                    f"by the current configuration."
                )
        
        # Generate detailed description for failures
        narrative = []
        
        if missing_fields:
            if len(missing_fields) <= 5:
                narrative.append(
                    f"Data schema is missing {len(missing_fields)} expected fields: {', '.join(missing_fields)}."
                )
            else:
                narrative.append(
                    f"Data schema is missing {len(missing_fields)} expected fields, including: "
                    f"{', '.join(missing_fields[:5])} and {len(missing_fields) - 5} more."
                )
        
        if extra_fields and not allow_extra:
            if len(extra_fields) <= 5:
                narrative.append(
                    f"Data schema contains {len(extra_fields)} unexpected extra fields: {', '.join(extra_fields)}. "
                    f"Extra fields are not allowed by the current configuration."
                )
            else:
                narrative.append(
                    f"Data schema contains {len(extra_fields)} unexpected extra fields, including: "
                    f"{', '.join(extra_fields[:5])} and {len(extra_fields) - 5} more. "
                    f"Extra fields are not allowed by the current configuration."
                )
        
        # Add recommendation
        if missing_fields:
            narrative.append(
                "Missing fields affect data completeness and may impact analysis. "
                "Consider adding these fields to the dataset or adjusting expectations."
            )
        
        if extra_fields and not allow_extra:
            narrative.append(
                "Unexpected extra fields may indicate schema drift or data quality issues. "
                "Consider removing these fields or updating the expected schema."
            )
            
        return " ".join(narrative)
