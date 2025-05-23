"""
Plausibility dimension rules for ADRI.

This module provides rule implementations for assessing the plausibility
dimension of data quality, including outlier detection, value distribution,
range checks, and pattern frequency analysis.
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Union, Tuple, Optional
import scipy.stats as stats

from .base import DiagnosticRule
from .registry import RuleRegistry

logger = logging.getLogger(__name__)


@RuleRegistry.register
class OutlierDetectionRule(DiagnosticRule):
    """
    Detects statistical outliers in numeric data.
    
    This rule uses various statistical methods to identify values
    that are significantly different from other observations.
    """
    
    rule_id = "plausibility.outlier"
    dimension = "plausibility"
    name = "Outlier Detection"
    description = "Identifies statistical outliers in numeric data."
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
                "description": "Column to analyze for outliers"
            },
            {
                "name": "method",
                "type": "string",
                "default": "zscore",
                "description": "Method for outlier detection: 'zscore', 'iqr', 'modified_zscore'"
            },
            {
                "name": "threshold",
                "type": "float",
                "default": 3.0,
                "description": "Threshold for outlier detection (e.g., Z-score > 3.0)"
            },
            {
                "name": "multiplier",
                "type": "float",
                "default": 1.5,
                "description": "Multiplier for IQR method (e.g., 1.5 * IQR)"
            },
            {
                "name": "exclude_outliers",
                "type": "boolean",
                "default": True,
                "description": "Whether to flag outliers as invalid data"
            }
        ]
    
    def evaluate(self, data: Union[pd.DataFrame, Any]) -> Dict[str, Any]:
        """
        Evaluate data for statistical outliers.
        
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
        method = self.params.get("method", "zscore")
        threshold = self.params.get("threshold", 3.0)
        multiplier = self.params.get("multiplier", 1.5)
        exclude_outliers = self.params.get("exclude_outliers", True)
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
        
        # Extract the column data and drop nulls
        values = df[column].dropna()
        
        # If no values after dropping nulls, return
        if len(values) == 0:
            return {
                "score": 0,
                "valid": False,
                "processed": False,
                "reason": f"No non-null values in column '{column}'"
            }
        
        # Check if the column is numeric
        if not pd.api.types.is_numeric_dtype(values):
            return {
                "score": 0,
                "valid": False,
                "processed": False,
                "reason": f"Column '{column}' is not numeric"
            }
        
        # Initialize tracking variables
        total_records = len(df)
        non_null_records = len(values)
        outliers = []
        outlier_indices = []
        
        try:
            # Detect outliers using the specified method
            if method == "zscore":
                # Z-score method: values beyond +/- threshold standard deviations
                z_scores = np.abs(stats.zscore(values))
                outlier_mask = z_scores > threshold
                outlier_indices = values.index[outlier_mask].tolist()
                outliers = values[outlier_mask].tolist()
                
            elif method == "iqr":
                # IQR method: values beyond Q1 - multiplier*IQR or Q3 + multiplier*IQR
                q1 = values.quantile(0.25)
                q3 = values.quantile(0.75)
                iqr = q3 - q1
                lower_bound = q1 - (multiplier * iqr)
                upper_bound = q3 + (multiplier * iqr)
                outlier_mask = (values < lower_bound) | (values > upper_bound)
                outlier_indices = values.index[outlier_mask].tolist()
                outliers = values[outlier_mask].tolist()
                
            elif method == "modified_zscore":
                # Modified Z-score method: more robust to extreme outliers
                median = values.median()
                mad = np.median(np.abs(values - median))
                if mad == 0:  # Avoid division by zero
                    modified_z_scores = np.zeros(len(values))
                else:
                    modified_z_scores = 0.6745 * np.abs(values - median) / mad
                outlier_mask = modified_z_scores > threshold
                outlier_indices = values.index[outlier_mask].tolist()
                outliers = values[outlier_mask].tolist()
                
            else:
                return {
                    "score": 0,
                    "valid": False,
                    "processed": False,
                    "reason": f"Unsupported outlier detection method: {method}"
                }
                
        except Exception as e:
            return {
                "score": 0,
                "valid": False,
                "processed": False,
                "reason": f"Error detecting outliers: {str(e)}"
            }
        
        # Get statistics for the column
        stats_dict = {
            "min": values.min(),
            "max": values.max(),
            "mean": values.mean(),
            "median": values.median(),
            "std": values.std(),
            "q1": values.quantile(0.25),
            "q3": values.quantile(0.75)
        }
        
        # Count outliers
        outlier_count = len(outliers)
        
        # Get examples of outliers
        outlier_examples = []
        for idx in outlier_indices[:10]:  # Limit to 10 examples
            outlier_examples.append({
                "index": int(idx),
                "value": float(df.at[idx, column])
            })
        
        # Calculate plausibility score
        if non_null_records > 0:
            if exclude_outliers:
                plausibility_ratio = 1.0 - (outlier_count / non_null_records)
            else:
                plausibility_ratio = 1.0  # If we don't exclude outliers, all values are considered plausible
        else:
            plausibility_ratio = 1.0
            
        # Calculate weighted score
        score = weight * plausibility_ratio
        score = max(0, min(weight, score))
        
        return {
            "score": score,
            "valid": outlier_count == 0 or not exclude_outliers,
            "total_records": total_records,
            "non_null_records": non_null_records,
            "outlier_count": outlier_count,
            "plausibility_ratio": plausibility_ratio,
            "method": method,
            "threshold": threshold,
            "statistics": stats_dict,
            "outlier_examples": outlier_examples,
            "exclude_outliers": exclude_outliers
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
            return f"Outlier detection was not performed: {result.get('reason', 'Unknown reason')}"
        
        total_records = result.get("total_records", 0)
        non_null_records = result.get("non_null_records", 0)
        outlier_count = result.get("outlier_count", 0)
        method = result.get("method", "")
        threshold = result.get("threshold", 0)
        exclude_outliers = result.get("exclude_outliers", True)
        column = self.params.get("column", "")
        stats = result.get("statistics", {})
        
        method_desc = {
            "zscore": f"Z-score > {threshold}",
            "iqr": f"beyond {threshold} times the interquartile range",
            "modified_zscore": f"modified Z-score > {threshold}"
        }.get(method, method)
        
        if outlier_count == 0:
            return (
                f"No outliers detected in column '{column}' using the {method} method "
                f"(threshold: {method_desc}). "
                f"All {non_null_records} non-null values are within expected statistical ranges."
            )
        
        outlier_percent = (outlier_count / non_null_records) * 100 if non_null_records > 0 else 0
        
        # Get examples for the narrative
        examples = result.get("outlier_examples", [])
        example_strs = []
        
        for i, example in enumerate(examples[:3]):  # Show up to 3 examples
            idx = example.get("index", "")
            value = example.get("value", "")
            example_strs.append(f"record at index {idx}: {value}")
        
        examples_text = ""
        if example_strs:
            examples_text = f" Examples of outliers: {'; '.join(example_strs)}."
        
        # Create a more detailed statistical context
        stat_context = (
            f"The column has min={stats.get('min')}, max={stats.get('max')}, "
            f"mean={stats.get('mean'):.2f}, median={stats.get('median'):.2f}, "
            f"and std={stats.get('std'):.2f}."
        )
        
        valid_text = ""
        if exclude_outliers:
            valid_text = (
                f"These outliers are flagged as potentially problematic data points "
                f"that should be reviewed."
            )
        else:
            valid_text = (
                f"These outliers have been identified for informational purposes "
                f"but are not flagged as invalid data."
            )
        
        narrative = (
            f"{outlier_percent:.1f}% of values ({outlier_count} out of {non_null_records}) "
            f"in column '{column}' were identified as outliers using the {method} method "
            f"(threshold: {method_desc}). "
            f"{stat_context}{examples_text} "
            f"{valid_text}"
        )
        
        return narrative


@RuleRegistry.register
class ValueDistributionRule(DiagnosticRule):
    """
    Evaluates if data follows expected statistical distributions.
    
    This rule checks if the distribution of values in a column matches
    an expected statistical pattern or reference distribution.
    """
    
    rule_id = "plausibility.distribution"
    dimension = "plausibility"
    name = "Value Distribution"
    description = "Evaluates if data follows expected statistical distributions."
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
                "description": "Column to analyze for distribution"
            },
            {
                "name": "distribution_type",
                "type": "string",
                "default": "normal",
                "description": "Expected distribution type: 'normal', 'uniform', 'poisson', etc."
            },
            {
                "name": "test_method",
                "type": "string",
                "default": "ks",
                "description": "Statistical test to use: 'ks' (Kolmogorov-Smirnov), 'chi2'"
            },
            {
                "name": "p_threshold",
                "type": "float",
                "default": 0.05,
                "description": "P-value threshold for statistical significance"
            },
            {
                "name": "distribution_params",
                "type": "dict",
                "default": {},
                "description": "Parameters for the expected distribution"
            }
        ]
    
    def evaluate(self, data: Union[pd.DataFrame, Any]) -> Dict[str, Any]:
        """
        Evaluate if data follows an expected distribution.
        
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
        distribution_type = self.params.get("distribution_type", "normal")
        test_method = self.params.get("test_method", "ks")
        p_threshold = self.params.get("p_threshold", 0.05)
        distribution_params = self.params.get("distribution_params", {})
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
        
        # Extract the column data and drop nulls
        values = df[column].dropna()
        
        # If no values after dropping nulls, return
        if len(values) == 0:
            return {
                "score": 0,
                "valid": False,
                "processed": False,
                "reason": f"No non-null values in column '{column}'"
            }
        
        # Check if the column is numeric
        if not pd.api.types.is_numeric_dtype(values):
            return {
                "score": 0,
                "valid": False,
                "processed": False,
                "reason": f"Column '{column}' is not numeric"
            }
        
        # Initialize tracking variables
        total_records = len(df)
        non_null_records = len(values)
        
        try:
            # Analyze data distribution
            sample_data = values.values
            
            # Calculate basic statistics
            data_stats = {
                "mean": values.mean(),
                "std": values.std(),
                "min": values.min(),
                "max": values.max(),
                "median": values.median(),
                "skew": float(stats.skew(sample_data)),
                "kurtosis": float(stats.kurtosis(sample_data))
            }
            
            # Set up the expected distribution
            if distribution_type == "normal":
                # Use empirical mean and std if not provided
                loc = distribution_params.get("loc", data_stats["mean"])
                scale = distribution_params.get("scale", data_stats["std"])
                dist = stats.norm(loc=loc, scale=scale)
                
            elif distribution_type == "uniform":
                # Use empirical min and max if not provided
                a = distribution_params.get("a", data_stats["min"])
                b = distribution_params.get("b", data_stats["max"])
                dist = stats.uniform(loc=a, scale=b-a)
                
            elif distribution_type == "poisson":
                # Use empirical mean if not provided
                mu = distribution_params.get("mu", data_stats["mean"])
                dist = stats.poisson(mu=mu)
                
            elif distribution_type == "exponential":
                # Use 1/empirical mean if not provided
                scale = distribution_params.get("scale", 1/data_stats["mean"] if data_stats["mean"] > 0 else 1.0)
                dist = stats.expon(scale=scale)
                
            else:
                return {
                    "score": 0,
                    "valid": False,
                    "processed": False,
                    "reason": f"Unsupported distribution type: {distribution_type}"
                }
            
            # Run the statistical test
            if test_method == "ks":
                # Kolmogorov-Smirnov test
                ks_statistic, p_value = stats.kstest(sample_data, dist.cdf)
                test_result = {
                    "test_name": "Kolmogorov-Smirnov",
                    "statistic": float(ks_statistic),
                    "p_value": float(p_value),
                    "significant": p_value < p_threshold
                }
                
            elif test_method == "chi2":
                # Chi-square test
                # Bin the data
                hist, bin_edges = np.histogram(sample_data, bins='auto')
                bin_mids = (bin_edges[1:] + bin_edges[:-1]) / 2
                
                # Expected frequencies based on the distribution
                expected = len(sample_data) * np.diff(dist.cdf(bin_edges))
                # Ensure no zeros in expected (which would cause division by zero)
                expected = np.maximum(expected, 0.1)
                
                chi2_statistic, p_value = stats.chisquare(hist, expected)
                test_result = {
                    "test_name": "Chi-square",
                    "statistic": float(chi2_statistic),
                    "p_value": float(p_value),
                    "significant": p_value < p_threshold
                }
                
            else:
                return {
                    "score": 0,
                    "valid": False,
                    "processed": False,
                    "reason": f"Unsupported test method: {test_method}"
                }
            
            # Calculate distribution similarity score (inverse to statistical significance)
            # Higher p-value means more similar to the expected distribution
            distribution_score = 1.0 - min(1.0, test_result["statistic"])
            
            # Calculate plausibility score
            # Data is considered plausible if it follows the expected distribution
            # Higher distribution_score means more plausible
            plausibility_ratio = distribution_score
            
            # Calculate weighted score
            score = weight * plausibility_ratio
            score = max(0, min(weight, score))
            
            # Data is valid if the test is NOT significant (p-value >= threshold)
            is_valid = not test_result["significant"]
            
            return {
                "score": score,
                "valid": is_valid,
                "total_records": total_records,
                "non_null_records": non_null_records,
                "distribution_type": distribution_type,
                "test_method": test_method,
                "p_threshold": p_threshold,
                "plausibility_ratio": plausibility_ratio,
                "data_statistics": data_stats,
                "distribution_parameters": distribution_params,
                "test_result": test_result
            }
            
        except Exception as e:
            return {
                "score": 0,
                "valid": False,
                "processed": False,
                "reason": f"Error evaluating distribution: {str(e)}"
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
            return f"Distribution check was not performed: {result.get('reason', 'Unknown reason')}"
        
        total_records = result.get("total_records", 0)
        non_null_records = result.get("non_null_records", 0)
        distribution_type = result.get("distribution_type", "")
        test_method = result.get("test_method", "")
        p_threshold = result.get("p_threshold", 0.05)
        column = self.params.get("column", "")
        data_stats = result.get("data_statistics", {})
        test_result = result.get("test_result", {})
        
        test_name = test_result.get("test_name", test_method)
        p_value = test_result.get("p_value", 0.0)
        statistic = test_result.get("statistic", 0.0)
        significant = test_result.get("significant", False)
        
        # Format statistics
        stats_text = (
            f"mean={data_stats.get('mean', 0.0):.2f}, "
            f"std={data_stats.get('std', 0.0):.2f}, "
            f"skewness={data_stats.get('skew', 0.0):.2f}, "
            f"kurtosis={data_stats.get('kurtosis', 0.0):.2f}"
        )
        
        if not significant:
            narrative = (
                f"The values in column '{column}' follow a {distribution_type} distribution "
                f"based on the {test_name} test (p-value: {p_value:.4f} >= {p_threshold}). "
                f"The distribution of the {non_null_records} non-null values has {stats_text}. "
                f"The data distribution is consistent with expectations."
            )
        else:
            narrative = (
                f"The values in column '{column}' do NOT follow the expected {distribution_type} distribution "
                f"based on the {test_name} test (p-value: {p_value:.4f} < {p_threshold}, statistic: {statistic:.4f}). "
                f"The distribution of the {non_null_records} non-null values has {stats_text}. "
                f"This deviation from the expected distribution may indicate data quality issues, "
                f"presence of multiple subpopulations, or invalid assumptions about the underlying process."
            )
        
        return narrative


@RuleRegistry.register
class RangeCheckRule(DiagnosticRule):
    """
    Validates if values fall within expected ranges.
    
    This rule checks if numeric values are within specified boundaries,
    which may be based on business rules, domain knowledge, or data constraints.
    """
    
    rule_id = "plausibility.range"
    dimension = "plausibility"
    name = "Range Check"
    description = "Validates if values fall within expected ranges."
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
                "description": "Column to check for range compliance"
            },
            {
                "name": "min_value",
                "type": "float",
                "default": None,
                "description": "Minimum allowed value (inclusive)"
            },
            {
                "name": "max_value",
                "type": "float",
                "default": None,
                "description": "Maximum allowed value (inclusive)"
            },
            {
                "name": "quantile_based",
                "type": "boolean",
                "default": False,
                "description": "Whether min/max values are interpreted as quantiles"
            },
            {
                "name": "use_log_scale",
                "type": "boolean",
                "default": False,
                "description": "Whether to use logarithmic scale for checks"
            }
        ]
    
    def evaluate(self, data: Union[pd.DataFrame, Any]) -> Dict[str, Any]:
        """
        Evaluate if values fall within expected ranges.
        
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
        min_value = self.params.get("min_value")
        max_value = self.params.get("max_value")
        quantile_based = self.params.get("quantile_based", False)
        use_log_scale = self.params.get("use_log_scale", False)
        weight = self.params.get("weight", 1.0)
        
        # Check parameter validity
        if not column:
            return {
                "score": 0,
                "valid": False,
                "processed": False,
                "reason": "No column specified"
            }
        
        if min_value is None and max_value is None:
            return {
                "score": 0,
                "valid": False,
                "processed": False,
                "reason": "No range limits specified (both min_value and max_value are None)"
            }
        
        if column not in df.columns:
            return {
                "score": 0,
                "valid": False,
                "processed": False,
                "reason": f"Column '{column}' not found in data"
            }
        
        # Extract the column data and drop nulls
        values = df[column].dropna()
        
        # If no values after dropping nulls, return
        if len(values) == 0:
            return {
                "score": 0,
                "valid": False,
                "processed": False,
                "reason": f"No non-null values in column '{column}'"
            }
        
        # Check if the column is numeric
        if not pd.api.types.is_numeric_dtype(values):
            return {
                "score": 0,
                "valid": False,
                "processed": False,
                "reason": f"Column '{column}' is not numeric"
            }
        
        # Apply log transformation if specified
        if use_log_scale:
            # Check for non-positive values before log transformation
            if (values <= 0).any():
                return {
                    "score": 0,
                    "valid": False,
                    "processed": False,
                    "reason": f"Column '{column}' contains non-positive values, cannot use log scale"
                }
            
            values = np.log(values)
            if min_value is not None and min_value > 0:
                min_value = np.log(min_value)
            if max_value is not None and max_value > 0:
                max_value = np.log(max_value)
        
        # Initialize tracking variables
        total_records = len(df)
        non_null_records = len(values)
        below_min = []
        above_max = []
        min_violations = 0
        max_violations = 0
        
        try:
            # If using quantiles, convert min/max to actual values
            if quantile_based:
                if min_value is not None:
                    min_value = values.quantile(min_value)
                if max_value is not None:
                    max_value = values.quantile(max_value)
            
            # Check for values below minimum
            if min_value is not None:
                below_min_mask = values < min_value
                min_violations = below_min_mask.sum()
                below_min_indices = values.index[below_min_mask].tolist()[:10]  # Limit to 10 examples
                below_min = [
                    {"index": int(idx), "value": float(df.at[idx, column])}
                    for idx in below_min_indices
                ]
            
            # Check for values above maximum
            if max_value is not None:
                above_max_mask = values > max_value
                max_violations = above_max_mask.sum()
                above_max_indices = values.index[above_max_mask].tolist()[:10]  # Limit to 10 examples
                above_max = [
                    {"index": int(idx), "value": float(df.at[idx, column])}
                    for idx in above_max_indices
                ]
            
            # Calculate total violations and plausibility score
            total_violations = min_violations + max_violations
            
            if non_null_records > 0:
                plausibility_ratio = 1.0 - (total_violations / non_null_records)
            else:
                plausibility_ratio = 1.0
            
            # Calculate weighted score
            score = weight * plausibility_ratio
            score = max(0, min(weight, score))
            
        except Exception as e:
            return {
                "score": 0,
                "valid": False,
                "processed": False,
                "reason": f"Error checking value ranges: {str(e)}"
            }
        
        # Get statistics for context
        stats_dict = {
            "min": values.min(),
            "max": values.max(),
            "mean": values.mean(),
            "median": values.median(),
            "std": values.std(),
            "q1": values.quantile(0.25),
            "q3": values.quantile(0.75)
        }
        
        # Determine actual limits used
        actual_min = min_value if min_value is not None else "-∞"
        actual_max = max_value if max_value is not None else "+∞"
        
        return {
            "score": score,
            "valid": total_violations == 0,
            "total_records": total_records,
            "non_null_records": non_null_records,
            "min_violations": int(min_violations),
            "max_violations": int(max_violations),
            "total_violations": int(total_violations),
            "plausibility_ratio": plausibility_ratio,
            "min_value": actual_min,
            "max_value": actual_max,
            "quantile_based": quantile_based,
            "use_log_scale": use_log_scale,
            "statistics": stats_dict,
            "below_min_examples": below_min,
            "above_max_examples": above_max
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
            return f"Range check was not performed: {result.get('reason', 'Unknown reason')}"
        
        total_records = result.get("total_records", 0)
        non_null_records = result.get("non_null_records", 0)
        min_violations = result.get("min_violations", 0)
        max_violations = result.get("max_violations", 0)
        total_violations = result.get("total_violations", 0)
        min_value = result.get("min_value", "-∞")
        max_value = result.get("max_value", "+∞")
        quantile_based = result.get("quantile_based", False)
        use_log_scale = result.get("use_log_scale", False)
        column = self.params.get("column", "")
        stats = result.get("statistics", {})
        
        # Range description
        if quantile_based:
            range_desc = f"the range defined by quantiles [{min_value}, {max_value}]"
        else:
            range_desc = f"the range [{min_value}, {max_value}]"
        
        if use_log_scale:
            range_desc += " (using logarithmic scale)"
        
        if total_violations == 0:
            return (
                f"All {non_null_records} non-null values in column '{column}' "
                f"are within {range_desc}. "
                f"The data has mean={stats.get('mean'):.2f}, min={stats.get('min'):.2f}, "
                f"and max={stats.get('max'):.2f}."
            )
        
        violation_percent = (total_violations / non_null_records) * 100 if non_null_records > 0 else 0
        
        # Get examples for the narrative
        below_examples = result.get("below_min_examples", [])
        above_examples = result.get("above_max_examples", [])
        
        example_strs = []
        
        for i, example in enumerate(below_examples[:2]):  # Show up to 2 examples of below min
            idx = example.get("index", "")
            value = example.get("value", "")
            example_strs.append(f"record at index {idx}: {value} (below min)")
        
        for i, example in enumerate(above_examples[:2]):  # Show up to 2 examples of above max
            idx = example.get("index", "")
            value = example.get("value", "")
            example_strs.append(f"record at index {idx}: {value} (above max)")
        
        examples_text = ""
        if example_strs:
            examples_text = f" Examples of out-of-range values: {'; '.join(example_strs)}."
        
        narrative = (
            f"{violation_percent:.1f}% of values ({total_violations} out of {non_null_records}) "
            f"in column '{column}' are outside {range_desc}. "
            f"This includes {min_violations} values below the minimum and "
            f"{max_violations} values above the maximum.{examples_text} "
            f"Out-of-range values may indicate data entry errors, "
            f"measurement issues, or invalid assumptions about expected ranges."
        )
        
        return narrative


@RuleRegistry.register
class PatternFrequencyRule(DiagnosticRule):
    """
    Analyzes frequency distribution of categorical values.
    
    This rule checks if the frequency of categorical values matches
    expected patterns or distributions, identifying values that are
    unusually common or rare.
    """
    
    rule_id = "plausibility.pattern_frequency"
    dimension = "plausibility"
    name = "Pattern Frequency Analysis"
    description = "Analyzes frequency distribution of categorical values."
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
                "description": "Column to analyze for pattern frequency"
            },
            {
                "name": "expected_frequencies",
                "type": "dict",
                "default": {},
                "description": "Expected relative frequencies for specific values (optional)"
            },
            {
                "name": "max_categories",
                "type": "integer",
                "default": 20,
                "description": "Maximum number of unique categories expected"
            },
            {
                "name": "min_frequency",
                "type": "float",
                "default": 0.01,
                "description": "Minimum relative frequency expected for any category (0.01 = 1%)"
            },
            {
                "name": "max_frequency",
                "type": "float",
                "default": 0.95,
                "description": "Maximum relative frequency expected for any category (0.95 = 95%)"
            },
            {
                "name": "tolerance",
                "type": "float",
                "default": 0.1,
                "description": "Tolerance for frequency deviation from expected"
            }
        ]
    
    def evaluate(self, data: Union[pd.DataFrame, Any]) -> Dict[str, Any]:
        """
        Analyze frequency distribution of categorical values.
        
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
        expected_frequencies = self.params.get("expected_frequencies", {})
        max_categories = self.params.get("max_categories", 20)
        min_frequency = self.params.get("min_frequency", 0.01)
        max_frequency = self.params.get("max_frequency", 0.95)
        tolerance = self.params.get("tolerance", 0.1)
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
        
        # Calculate value frequencies
        value_counts = df[column].value_counts(dropna=True)
        unique_values = len(value_counts)
        
        # If no values after dropping nulls, return
        if non_null_records == 0:
            return {
                "score": 0,
                "valid": False,
                "processed": False,
                "reason": f"No non-null values in column '{column}'"
            }
        
        try:
            # Calculate relative frequencies
            rel_frequencies = value_counts / non_null_records
            
            # Identify issues
            issues = []
            issue_records = 0
            issue_examples = []
            
            # Check for too many categories
            if unique_values > max_categories:
                issues.append(f"Too many unique values: {unique_values} > {max_categories}")
                
            # Check for unusually high or low frequency values
            high_freq_mask = rel_frequencies > max_frequency
            low_freq_mask = (rel_frequencies < min_frequency) & (rel_frequencies.index != "")  # Exclude empty string

            high_freq_values = rel_frequencies[high_freq_mask]
            low_freq_values = rel_frequencies[low_freq_mask]
            
            # Add issues for high/low frequency
            for value, freq in high_freq_values.items():
                issues.append(f"Value '{value}' has unusually high frequency: {freq:.2%} > {max_frequency:.2%}")
                issue_records += value_counts[value]
                # Get example records with this value
                example_indices = df[df[column] == value].index.tolist()[:3]  # Limit to 3 examples
                for idx in example_indices:
                    issue_examples.append({
                        "index": int(idx),
                        "value": str(df.at[idx, column]),
                        "issue": "high_frequency"
                    })
            
            for value, freq in low_freq_values.items():
                issues.append(f"Value '{value}' has unusually low frequency: {freq:.2%} < {min_frequency:.2%}")
                issue_records += value_counts[value]
                # Get example records with this value
                example_indices = df[df[column] == value].index.tolist()[:3]  # Limit to 3 examples
                for idx in example_indices:
                    issue_examples.append({
                        "index": int(idx),
                        "value": str(df.at[idx, column]),
                        "issue": "low_frequency"
                    })
                
            # Check for deviations from expected frequencies
            if expected_frequencies:
                for value, expected_freq in expected_frequencies.items():
                    if value in rel_frequencies:
                        actual_freq = rel_frequencies[value]
                        deviation = abs(actual_freq - expected_freq)
                        if deviation > tolerance:
                            issues.append(
                                f"Value '{value}' has frequency {actual_freq:.2%}, "
                                f"which deviates from expected {expected_freq:.2%} by {deviation:.2%} > {tolerance:.2%}"
                            )
                            issue_records += value_counts[value]
                            # Get example records with this value
                            example_indices = df[df[column] == value].index.tolist()[:3]  # Limit to 3 examples
                            for idx in example_indices:
                                issue_examples.append({
                                    "index": int(idx),
                                    "value": str(df.at[idx, column]),
                                    "issue": "unexpected_frequency"
                                })
            
            # Calculate plausibility score
            if non_null_records > 0:
                plausibility_ratio = 1.0 - (issue_records / non_null_records)
            else:
                plausibility_ratio = 1.0
            
            # Calculate weighted score
            score = weight * plausibility_ratio
            score = max(0, min(weight, score))
            
            # Get top frequencies
            top_freqs = rel_frequencies.head(10).to_dict()  # Get top 10 values
            
            return {
                "score": score,
                "valid": len(issues) == 0,
                "total_records": total_records,
                "non_null_records": non_null_records,
                "unique_values": unique_values,
                "top_frequencies": {str(k): float(v) for k, v in top_freqs.items()},
                "issue_count": len(issues),
                "issue_records": issue_records,
                "plausibility_ratio": plausibility_ratio,
                "issues": issues,
                "issue_examples": issue_examples
            }
            
        except Exception as e:
            return {
                "score": 0,
                "valid": False,
                "processed": False,
                "reason": f"Error analyzing pattern frequencies: {str(e)}"
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
            return f"Pattern frequency analysis was not performed: {result.get('reason', 'Unknown reason')}"
        
        total_records = result.get("total_records", 0)
        non_null_records = result.get("non_null_records", 0)
        unique_values = result.get("unique_values", 0)
        issue_count = result.get("issue_count", 0)
        issue_records = result.get("issue_records", 0)
        column = self.params.get("column", "")
        issues = result.get("issues", [])
        top_freqs = result.get("top_frequencies", {})
        
        # Format top frequencies for display
        top_freq_strs = [f"'{k}': {v:.1%}" for k, v in top_freqs.items()][:5]  # Show top 5
        top_freq_text = ", ".join(top_freq_strs)
        
        if issue_count == 0:
            return (
                f"The frequency distribution of values in column '{column}' appears normal. "
                f"There are {unique_values} unique values across {non_null_records} non-null records. "
                f"Top frequencies: {top_freq_text}."
            )
        
        issue_percent = (issue_records / non_null_records) * 100 if non_null_records > 0 else 0
        
        # Get examples for the narrative
        examples = result.get("issue_examples", [])
        example_strs = []
        
        for i, example in enumerate(examples[:3]):  # Show up to 3 examples
            idx = example.get("index", "")
            value = example.get("value", "")
            issue_type = example.get("issue", "")
            issue_desc = {
                "high_frequency": "high frequency",
                "low_frequency": "low frequency",
                "unexpected_frequency": "unexpected frequency"
            }.get(issue_type, issue_type)
            
            example_strs.append(f"record at index {idx}: '{value}' ({issue_desc})")
        
        examples_text = ""
        if example_strs:
            examples_text = f" Examples: {'; '.join(example_strs)}."
        
        # List top issues (limit to 3)
        issue_text = ""
        if issues:
            issue_text = f" Detected issues include: {'; '.join(issues[:3])}"
            if len(issues) > 3:
                issue_text += f" and {len(issues) - 3} more."
        
        narrative = (
            f"Analysis of the frequency distribution in column '{column}' identified {issue_count} issue(s) "
            f"affecting {issue_percent:.1f}% of values. "
            f"There are {unique_values} unique values across {non_null_records} non-null records."
            f"{issue_text}.{examples_text} "
            f"Top frequencies: {top_freq_text}."
        )
        
        return narrative
