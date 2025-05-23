"""
Consistency dimension rules for ADRI.

This module provides rule implementations for assessing the consistency
dimension of data quality, including cross-field validation, referential
integrity, uniform representation, and calculation consistency.
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Union, Tuple, Set, Optional
import re

from .base import DiagnosticRule
from .registry import RuleRegistry

logger = logging.getLogger(__name__)


@RuleRegistry.register
class CrossFieldConsistencyRule(DiagnosticRule):
    """
    Validates consistency between related fields within records.
    
    This rule checks that values in different columns maintain 
    logical relationships as defined by custom validation functions.
    """
    
    rule_id = "consistency.cross_field"
    dimension = "consistency"
    name = "Cross-Field Consistency"
    description = "Validates logical relationships between related fields."
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
                "name": "validation_type",
                "type": "string",
                "default": "expression",
                "description": "Type of validation: 'expression', 'comparison', or 'custom'"
            },
            {
                "name": "fields",
                "type": "list",
                "default": [],
                "description": "List of field names to validate together"
            },
            {
                "name": "expression",
                "type": "string",
                "default": "",
                "description": "Python expression that should evaluate to True (used with validation_type='expression')"
            },
            {
                "name": "comparisons",
                "type": "list",
                "default": [],
                "description": "List of comparison operations between fields (used with validation_type='comparison')"
            },
            {
                "name": "custom_validation",
                "type": "string",
                "default": "",
                "description": "Name of a custom validation function (used with validation_type='custom')"
            }
        ]
    
    def evaluate(self, data: Union[pd.DataFrame, Any]) -> Dict[str, Any]:
        """
        Evaluate cross-field consistency in the dataset.
        
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
        validation_type = self.params.get("validation_type", "expression")
        fields = self.params.get("fields", [])
        expression = self.params.get("expression", "")
        comparisons = self.params.get("comparisons", [])
        custom_validation = self.params.get("custom_validation", "")
        weight = self.params.get("weight", 1.5)
        
        # Validate that we have all required fields
        if not fields:
            return {
                "score": 0,
                "valid": False,
                "processed": False,
                "reason": "No fields specified for validation"
            }
        
        # Check if all specified fields exist in the dataframe
        missing_fields = [field for field in fields if field not in df.columns]
        if missing_fields:
            return {
                "score": 0,
                "valid": False,
                "processed": False,
                "reason": f"Fields not found in data: {', '.join(missing_fields)}"
            }
        
        # Initialize tracking variables
        total_records = len(df)
        invalid_records = 0
        invalid_examples = []
        
        # Perform validation based on the specified type
        if validation_type == "expression":
            if not expression:
                return {
                    "score": 0,
                    "valid": False,
                    "processed": False,
                    "reason": "No expression provided for validation_type 'expression'"
                }
            
            try:
                # Create a subset of the dataframe with only the required fields
                subset_df = df[fields].copy()
                
                # Define the validation using the expression
                # Replace field names with df column references in the expression
                eval_expr = expression
                for field in fields:
                    eval_expr = eval_expr.replace(field, f"subset_df['{field}']")
                
                # Evaluate the expression
                mask = eval(eval_expr)
                invalid_mask = ~mask
                
                # Count invalid records
                invalid_records = invalid_mask.sum()
                
                # Get examples
                if invalid_records > 0:
                    example_indices = df.index[invalid_mask].tolist()[:5]  # Get up to 5 examples
                    for idx in example_indices:
                        example_values = {field: df.at[idx, field] for field in fields}
                        invalid_examples.append((idx, example_values))
                
            except Exception as e:
                return {
                    "score": 0,
                    "valid": False,
                    "processed": False,
                    "reason": f"Error evaluating expression: {str(e)}"
                }
                
        elif validation_type == "comparison":
            if not comparisons:
                return {
                    "score": 0,
                    "valid": False,
                    "processed": False,
                    "reason": "No comparisons provided for validation_type 'comparison'"
                }
            
            try:
                # Initialize mask for all records as valid
                mask = pd.Series([True] * len(df), index=df.index)
                
                # Apply each comparison
                for comparison in comparisons:
                    field1 = comparison.get("field1")
                    field2 = comparison.get("field2")
                    operator = comparison.get("operator", "==")
                    
                    if not field1 or not field2:
                        logger.warning(f"Incomplete comparison specification: {comparison}")
                        continue
                        
                    if field1 not in df.columns or field2 not in df.columns:
                        logger.warning(f"Fields not found: {field1} or {field2}")
                        continue
                    
                    # Apply the comparison operator
                    if operator == "==":
                        comp_mask = df[field1] == df[field2]
                    elif operator == "!=":
                        comp_mask = df[field1] != df[field2]
                    elif operator == "<":
                        comp_mask = df[field1] < df[field2]
                    elif operator == "<=":
                        comp_mask = df[field1] <= df[field2]
                    elif operator == ">":
                        comp_mask = df[field1] > df[field2]
                    elif operator == ">=":
                        comp_mask = df[field1] >= df[field2]
                    else:
                        logger.warning(f"Unsupported operator: {operator}")
                        continue
                    
                    # Combine with overall mask
                    mask = mask & comp_mask
                
                invalid_mask = ~mask
                invalid_records = invalid_mask.sum()
                
                # Get examples
                if invalid_records > 0:
                    example_indices = df.index[invalid_mask].tolist()[:5]  # Get up to 5 examples
                    for idx in example_indices:
                        example_values = {field: df.at[idx, field] for field in fields}
                        invalid_examples.append((idx, example_values))
                
            except Exception as e:
                return {
                    "score": 0,
                    "valid": False,
                    "processed": False,
                    "reason": f"Error evaluating comparisons: {str(e)}"
                }
                
        elif validation_type == "custom":
            if not custom_validation:
                return {
                    "score": 0,
                    "valid": False,
                    "processed": False,
                    "reason": "No custom_validation function provided for validation_type 'custom'"
                }
            
            try:
                # Use the custom validation function (should be accessible in the global scope)
                validation_func = globals().get(custom_validation)
                
                if not validation_func:
                    return {
                        "score": 0,
                        "valid": False,
                        "processed": False,
                        "reason": f"Custom validation function '{custom_validation}' not found"
                    }
                
                # Apply custom validation function to the dataframe subset
                subset_df = df[fields].copy()
                validation_results = validation_func(subset_df)
                
                if isinstance(validation_results, pd.Series):
                    # Interpret the result as a boolean mask (True = valid)
                    invalid_mask = ~validation_results
                    invalid_records = invalid_mask.sum()
                    
                    # Get examples
                    if invalid_records > 0:
                        example_indices = df.index[invalid_mask].tolist()[:5]  # Get up to 5 examples
                        for idx in example_indices:
                            example_values = {field: df.at[idx, field] for field in fields}
                            invalid_examples.append((idx, example_values))
                            
                elif isinstance(validation_results, dict):
                    # Interpret the result as a dictionary with explicit invalid records
                    invalid_records = validation_results.get("invalid_count", 0)
                    invalid_examples = validation_results.get("examples", [])
                else:
                    return {
                        "score": 0,
                        "valid": False,
                        "processed": False,
                        "reason": f"Unsupported validation result format from {custom_validation}"
                    }
                    
            except Exception as e:
                return {
                    "score": 0,
                    "valid": False,
                    "processed": False,
                    "reason": f"Error applying custom validation: {str(e)}"
                }
        else:
            return {
                "score": 0,
                "valid": False,
                "processed": False,
                "reason": f"Unsupported validation_type: {validation_type}"
            }
        
        # Calculate consistency ratio
        if total_records > 0:
            consistency_ratio = 1.0 - (invalid_records / total_records)
        else:
            consistency_ratio = 1.0
        
        # Calculate score
        score = weight * consistency_ratio
        score = max(0, min(weight, score))
        
        # Prepare examples for reporting
        examples_formatted = []
        for idx, values in invalid_examples:
            examples_formatted.append({
                "index": idx,
                "values": values
            })
        
        return {
            "score": score,
            "valid": invalid_records == 0,
            "total_records": total_records,
            "invalid_records": int(invalid_records),
            "consistency_ratio": consistency_ratio,
            "validation_type": validation_type,
            "fields": fields,
            "examples": examples_formatted
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
            return f"Cross-field consistency check was not performed: {result.get('reason', 'Unknown reason')}"
        
        total_records = result.get("total_records", 0)
        invalid_records = result.get("invalid_records", 0)
        consistency_ratio = result.get("consistency_ratio", 1.0)
        validation_type = result.get("validation_type", "")
        fields = result.get("fields", [])
        
        fields_str = ", ".join(fields)
        
        if result.get("valid", False):
            return (
                f"All {total_records} records maintain consistent relationships "
                f"between the fields: {fields_str}. "
                f"No inconsistencies were detected using {validation_type} validation."
            )
        
        invalid_percent = (invalid_records / total_records) * 100 if total_records > 0 else 0
        
        # Get examples for the narrative
        examples = result.get("examples", [])
        example_strs = []
        
        for i, example in enumerate(examples[:3]):  # Show up to 3 examples
            idx = example.get("index", "")
            values = example.get("values", {})
            value_strs = [f"{field}={values.get(field, 'N/A')}" for field in fields]
            example_strs.append(f"record at index {idx}: {', '.join(value_strs)}")
        
        examples_text = ""
        if example_strs:
            examples_text = f" Examples of inconsistent records: {'; '.join(example_strs)}."
        
        narrative = (
            f"{invalid_percent:.1f}% of records ({invalid_records} out of {total_records}) "
            f"show inconsistencies between the fields {fields_str}."
            f"{examples_text} "
            f"These inconsistencies may indicate data entry errors, schema violations, "
            f"or business rule failures that should be investigated."
        )
        
        return narrative


@RuleRegistry.register
class UniformRepresentationRule(DiagnosticRule):
    """
    Validates consistent formatting and representation of values.
    
    This rule checks that values of the same semantic type are represented
    consistently throughout the dataset, such as dates, phone numbers,
    addresses, or other formatted fields.
    """
    
    rule_id = "consistency.uniform_representation"
    dimension = "consistency"
    name = "Uniform Representation"
    description = "Validates consistent formatting and representation of values."
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
                "default": 1.0,
                "description": "Importance weight of this rule in the overall assessment"
            },
            {
                "name": "column",
                "type": "string",
                "default": "",
                "description": "Column to validate for uniform representation"
            },
            {
                "name": "format_type",
                "type": "string",
                "default": "pattern",
                "description": "Type of format check: 'pattern', 'categorical', 'length'"
            },
            {
                "name": "pattern",
                "type": "string",
                "default": "",
                "description": "Regex pattern that values should match (used with format_type='pattern')"
            },
            {
                "name": "allowed_values",
                "type": "list",
                "default": [],
                "description": "List of allowed values (used with format_type='categorical')"
            },
            {
                "name": "max_variations",
                "type": "integer",
                "default": 1,
                "description": "Maximum number of different formats allowed in the data"
            },
            {
                "name": "case_sensitive",
                "type": "boolean",
                "default": False,
                "description": "Whether to treat text values as case-sensitive"
            }
        ]
    
    def evaluate(self, data: Union[pd.DataFrame, Any]) -> Dict[str, Any]:
        """
        Evaluate uniform representation in the dataset.
        
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
        column = self.params.get("column", "")
        format_type = self.params.get("format_type", "pattern")
        pattern = self.params.get("pattern", "")
        allowed_values = self.params.get("allowed_values", [])
        max_variations = self.params.get("max_variations", 1)
        case_sensitive = self.params.get("case_sensitive", False)
        weight = self.params.get("weight", 1.0)
        
        # Check parameter validity
        if not column:
            return {
                "score": 0,
                "valid": False,
                "processed": False,
                "reason": "No column specified"
            }
        
        if column not in df.columns:
            return {
                "score": 0,
                "valid": False,
                "processed": False,
                "reason": f"Column '{column}' not found in data"
            }
        
        # Initialize tracking variables
        total_records = len(df)
        non_null_records = df[column].notna().sum()
        invalid_records = 0
        invalid_examples = []
        format_variations = set()
        
        # Process only non-null values for uniformity check
        non_null_mask = df[column].notna()
        values = df.loc[non_null_mask, column].astype(str)
        
        try:
            if format_type == "pattern":
                if not pattern:
                    return {
                        "score": 0,
                        "valid": False,
                        "processed": False,
                        "reason": "No pattern specified for format_type='pattern'"
                    }
                
                # Compile regex pattern
                if case_sensitive:
                    regex = re.compile(pattern)
                else:
                    regex = re.compile(pattern, re.IGNORECASE)
                
                # Check if values match the pattern
                valid_mask = values.str.match(regex)
                
                # Filter for records in the original dataframe
                invalid_mask = non_null_mask & ~valid_mask.reindex(df.index, fill_value=False)
                invalid_records = invalid_mask.sum()
                
                # Get examples and format variations
                if invalid_records > 0:
                    example_indices = df.index[invalid_mask].tolist()[:5]  # Get up to 5 examples
                    for idx in example_indices:
                        value = str(df.at[idx, column])
                        invalid_examples.append({
                            "index": int(idx),
                            "value": value
                        })
                        format_variations.add(value)
                
            elif format_type == "categorical":
                if not allowed_values:
                    return {
                        "score": 0,
                        "valid": False,
                        "processed": False,
                        "reason": "No allowed_values provided for format_type='categorical'"
                    }
                
                # For non-case-sensitive comparison, convert all to lowercase
                if not case_sensitive:
                    allowed_set = set(str(v).lower() for v in allowed_values)
                    valid_mask = values.str.lower().isin(allowed_set)
                else:
                    allowed_set = set(str(v) for v in allowed_values)
                    valid_mask = values.isin(allowed_set)
                
                # Filter for records in the original dataframe
                invalid_mask = non_null_mask & ~valid_mask.reindex(df.index, fill_value=False)
                invalid_records = invalid_mask.sum()
                
                # Get examples and format variations
                if invalid_records > 0:
                    example_indices = df.index[invalid_mask].tolist()[:5]  # Get up to 5 examples
                    for idx in example_indices:
                        value = str(df.at[idx, column])
                        invalid_examples.append({
                            "index": int(idx),
                            "value": value
                        })
                        format_variations.add(value)
                
            elif format_type == "length":
                # Check for consistency in string length
                lengths = values.str.len()
                length_counts = lengths.value_counts()
                
                if len(length_counts) > max_variations:
                    # More variations than allowed
                    invalid_records = non_null_records - length_counts.iloc[0]  # Count all except most common
                    
                    # Most common length is considered the expected format
                    expected_length = length_counts.index[0]
                    invalid_mask = non_null_mask & (lengths != expected_length).reindex(df.index, fill_value=False)
                    
                    # Get examples
                    example_indices = df.index[invalid_mask].tolist()[:5]  # Get up to 5 examples
                    for idx in example_indices:
                        value = str(df.at[idx, column])
                        invalid_examples.append({
                            "index": int(idx),
                            "value": value,
                            "length": len(value)
                        })
                        format_variations.add(f"length: {len(value)}")
                    
            else:
                return {
                    "score": 0,
                    "valid": False,
                    "processed": False,
                    "reason": f"Unsupported format_type: {format_type}"
                }
        
        except Exception as e:
            return {
                "score": 0,
                "valid": False,
                "processed": False,
                "reason": f"Error in uniformity check: {str(e)}"
            }
        
        # Calculate uniformity ratio
        if non_null_records > 0:
            uniformity_ratio = 1.0 - (invalid_records / non_null_records)
        else:
            uniformity_ratio = 1.0
        
        # Calculate score
        score = weight * uniformity_ratio
        score = max(0, min(weight, score))
        
        return {
            "score": score,
            "valid": invalid_records == 0,
            "total_records": total_records,
            "non_null_records": non_null_records,
            "invalid_records": int(invalid_records),
            "uniformity_ratio": uniformity_ratio,
            "format_type": format_type,
            "column": column,
            "format_variations": list(format_variations)[:10],  # Limit to 10 examples
            "examples": invalid_examples
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
            return f"Uniform representation check was not performed: {result.get('reason', 'Unknown reason')}"
        
        total_records = result.get("total_records", 0)
        non_null_records = result.get("non_null_records", 0)
        invalid_records = result.get("invalid_records", 0)
        uniformity_ratio = result.get("uniformity_ratio", 1.0)
        format_type = result.get("format_type", "")
        column = result.get("column", "")
        
        if result.get("valid", False):
            return (
                f"All {non_null_records} non-null values in column '{column}' follow a consistent format. "
                f"Uniform representation is maintained in the '{format_type}' format check."
            )
        
        invalid_percent = (invalid_records / non_null_records) * 100 if non_null_records > 0 else 0
        
        # Get examples for the narrative
        examples = result.get("examples", [])
        example_strs = []
        
        for i, example in enumerate(examples[:3]):  # Show up to 3 examples
            idx = example.get("index", "")
            value = example.get("value", "")
            example_strs.append(f"record at index {idx}: '{value}'")
        
        examples_text = ""
        if example_strs:
            examples_text = f" Examples of inconsistent formats: {'; '.join(example_strs)}."
        
        variations = result.get("format_variations", [])
        variations_str = ", ".join([f"'{v}'" for v in variations[:5]])  # Show up to 5 variations
        if len(variations) > 5:
            variations_str += f" and {len(variations) - 5} more"
        
        narrative = (
            f"{invalid_percent:.1f}% of non-null values ({invalid_records} out of {non_null_records}) "
            f"in column '{column}' have inconsistent formats. "
            f"Format variations include: {variations_str}."
            f"{examples_text} "
            f"Inconsistent formatting can cause problems with data processing, filtering, "
            f"and analysis. Consider standardizing the representation."
        )
        
        return narrative


@RuleRegistry.register
class CalculationConsistencyRule(DiagnosticRule):
    """
    Validates consistency of calculated values.
    
    This rule checks that derived or calculated fields are consistent
    with their expected values based on other fields in the dataset.
    """
    
    rule_id = "consistency.calculation"
    dimension = "consistency"
    name = "Calculation Consistency"
    description = "Validates derivation consistency for calculated fields."
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
                "name": "result_column",
                "type": "string",
                "default": "",
                "description": "Column containing the calculated result to validate"
            },
            {
                "name": "calculation_type",
                "type": "string",
                "default": "expression",
                "description": "Type of calculation: 'expression', 'aggregation', or 'custom'"
            },
            {
                "name": "expression",
                "type": "string",
                "default": "",
                "description": "Python expression for recalculating expected values"
            },
            {
                "name": "input_columns",
                "type": "list",
                "default": [],
                "description": "Columns used as inputs to the calculation"
            },
            {
                "name": "tolerance",
                "type": "float",
                "default": 0.001,
                "description": "Tolerance for floating-point comparisons"
            },
            {
                "name": "custom_calculation",
                "type": "string",
                "default": "",
                "description": "Name of a custom calculation function"
            }
        ]
    
    def evaluate(self, data: Union[pd.DataFrame, Any]) -> Dict[str, Any]:
        """
        Evaluate calculation consistency in the dataset.
        
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
        result_column = self.params.get("result_column", "")
        calculation_type = self.params.get("calculation_type", "expression")
        expression = self.params.get("expression", "")
        input_columns = self.params.get("input_columns", [])
        tolerance = self.params.get("tolerance", 0.001)
        custom_calculation = self.params.get("custom_calculation", "")
        weight = self.params.get("weight", 1.5)
        
        # Initialize result dictionary with required fields for test compatibility
        result = {
            "score": 0,
            "valid": True,
            "total_records": len(df),
            "valid_records": 0,
            "invalid_records": 0,
            "total_violations": 0,
            "consistency_ratio": 1.0,
            "calculation_type": calculation_type,
            "result_column": result_column,
            "input_columns": input_columns,
            "examples": []
        }
        
        # Check parameter validity
        if not result_column:
            result["processed"] = False
            result["valid"] = False
            result["reason"] = "No result_column specified"
            return result
        
        if result_column not in df.columns:
            result["processed"] = False
            result["valid"] = False
            result["reason"] = f"Result column '{result_column}' not found in data"
            return result
        
        # Check that all input columns exist
        missing_columns = [col for col in input_columns if col not in df.columns]
        if missing_columns:
            result["processed"] = False
            result["valid"] = False
            result["reason"] = f"Input columns not found: {', '.join(missing_columns)}"
            return result
        
        # Filter out rows with null values in result or input columns
        valid_rows_mask = df[result_column].notna()
        for col in input_columns:
            valid_rows_mask = valid_rows_mask & df[col].notna()
        
        # If no valid rows to check, return early
        if valid_rows_mask.sum() == 0:
            result["processed"] = False
            result["valid"] = False
            result["reason"] = "No rows with complete data for calculation check"
            return result
        
        df_valid = df[valid_rows_mask].copy()
        result["valid_records"] = len(df_valid)
        
        # Calculate expected values based on the calculation type
        try:
            if calculation_type == "expression":
                if not expression:
                    result["processed"] = False
                    result["valid"] = False
                    result["reason"] = "No expression provided for calculation_type 'expression'"
                    return result
                
                # Create a subset with only the required fields
                subset_df = df_valid[input_columns].copy()
                
                # Substitute column references in the expression
                eval_expr = expression
                for col in input_columns:
                    eval_expr = eval_expr.replace(col, f"subset_df['{col}']")
                
                # Calculate the expected values
                expected_values = eval(eval_expr)
                
                # Compare with actual values using tolerance for numeric values
                actual_values = df_valid[result_column]
                
                if pd.api.types.is_numeric_dtype(actual_values):
                    # For numeric values, use tolerance
                    diff = (actual_values - expected_values).abs()
                    invalid_mask = diff > tolerance
                else:
                    # For non-numeric values, use equality
                    invalid_mask = actual_values != expected_values
                
                invalid_indices = df_valid.index[invalid_mask]
                invalid_records = len(invalid_indices)
                result["invalid_records"] = invalid_records
                result["total_violations"] = invalid_records
                
                # Get examples
                invalid_examples = []
                if invalid_records > 0:
                    example_indices = invalid_indices.tolist()[:5]  # Get up to 5 examples
                    for idx in example_indices:
                        invalid_examples.append({
                            "index": int(idx),
                            "actual": str(df_valid.at[idx, result_column]),
                            "expected": str(expected_values.iloc[df_valid.index.get_loc(idx)]),
                            "inputs": {col: str(df_valid.at[idx, col]) for col in input_columns}
                        })
                result["examples"] = invalid_examples
                result["valid"] = (invalid_records == 0)
                
            elif calculation_type == "custom":
                if not custom_calculation:
                    result["processed"] = False
                    result["valid"] = False
                    result["reason"] = "No custom_calculation function provided for calculation_type 'custom'"
                    return result
                
                # Implement custom calculation if needed
                # ...
                result["processed"] = False
                result["valid"] = False
                result["reason"] = "Custom calculation not implemented yet"
                return result
            else:
                result["processed"] = False
                result["valid"] = False
                result["reason"] = f"Unsupported calculation_type: {calculation_type}"
                return result
                
        except Exception as e:
            result["processed"] = False
            result["valid"] = False
            result["reason"] = f"Error in calculation consistency check: {str(e)}"
            return result
        
        # Calculate consistency ratio
        if valid_rows_mask.sum() > 0:
            consistency_ratio = 1.0 - (invalid_records / valid_rows_mask.sum())
        else:
            consistency_ratio = 1.0
        result["consistency_ratio"] = consistency_ratio
        
        # Calculate score
        score = weight * consistency_ratio
        score = max(0, min(weight, score))
        result["score"] = score
        
        return result
    
    def generate_narrative(self, result: Dict[str, Any]) -> str:
        """
        Generate a narrative description of the rule evaluation result.
        
        Args:
            result: The result from evaluate()
            
        Returns:
            String containing the narrative description
        """
        if not result.get("processed", True):
            return f"Calculation consistency check was not performed: {result.get('reason', 'Unknown reason')}"
        
        total_records = result.get("total_records", 0)
        valid_records = result.get("valid_records", 0)
        invalid_records = result.get("invalid_records", 0)
        consistency_ratio = result.get("consistency_ratio", 1.0)
        calculation_type = result.get("calculation_type", "")
        result_column = result.get("result_column", "")
        input_columns = result.get("input_columns", [])
        
        input_columns_str = ", ".join(input_columns)
        
        if result.get("valid", False):
            return (
                f"All {valid_records} records maintain consistent calculated values "
                f"in column '{result_column}' based on inputs from {input_columns_str}. "
                f"No calculation inconsistencies were detected."
            )
        
        invalid_percent = (invalid_records / valid_records) * 100 if valid_records > 0 else 0
        
        # Get examples for the narrative
        examples = result.get("examples", [])
        example_strs = []
        
        for i, example in enumerate(examples[:3]):  # Show up to 3 examples
            idx = example.get("index", "")
            actual = example.get("actual", "")
            expected = example.get("expected", "")
            
            if expected:
                example_strs.append(f"record at index {idx}: actual={actual}, expected={expected}")
            else:
                example_strs.append(f"record at index {idx}: actual={actual}")
        
        examples_text = ""
        if example_strs:
            examples_text = f" Examples of inconsistent calculations: {'; '.join(example_strs)}."
        
        narrative = (
            f"{invalid_percent:.1f}% of records ({invalid_records} out of {valid_records}) "
            f"show calculation inconsistencies in the '{result_column}' column."
            f"{examples_text} "
            f"These inconsistencies may indicate calculation errors, formula changes, "
            f"or data processing issues that should be investigated."
        )
        
        return narrative
