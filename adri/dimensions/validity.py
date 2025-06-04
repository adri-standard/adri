"""
Validity dimension assessment for the Agent Data Readiness Index.

This module evaluates whether data adheres to required types, formats, and ranges,
and most importantly, whether this information is explicitly communicated to agents.
"""

import logging
from typing import Dict, List, Tuple, Any, Optional

from ..config.config import get_config
from ..connectors import BaseConnector
from . import BaseDimensionAssessor, register_dimension
from .business_validity import calculate_business_validity_score
from ..rules.registry import RuleRegistry

logger = logging.getLogger(__name__)

# Get default scoring constants from configuration
default_config = get_config()
default_scoring = default_config.get_validity_scoring()

DEFAULT_MAX_TYPES_DEFINED_SCORE = default_scoring["MAX_TYPES_DEFINED_SCORE"]
DEFAULT_MAX_FORMATS_DEFINED_SCORE = default_scoring["MAX_FORMATS_DEFINED_SCORE"]
DEFAULT_MAX_RANGES_DEFINED_SCORE = default_scoring["MAX_RANGES_DEFINED_SCORE"]
DEFAULT_MAX_VALIDATION_PERFORMED_SCORE = default_scoring["MAX_VALIDATION_PERFORMED_SCORE"]
DEFAULT_MAX_VALIDATION_COMMUNICATED_SCORE = default_scoring["MAX_VALIDATION_COMMUNICATED_SCORE"]
DEFAULT_REQUIRE_EXPLICIT_METADATA = default_scoring["REQUIRE_EXPLICIT_METADATA"]


@register_dimension(
    name="validity",
    description="Whether data adheres to required types, formats, and ranges"
)
class ValidityAssessor(BaseDimensionAssessor):
    """
    Assessor for the Validity dimension.
    
    Evaluates whether data adheres to required types, formats, and ranges,
    and whether this information is explicitly communicated to agents.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the validity assessor with configuration.
        
        Args:
            config: Optional configuration dictionary
        """
        super().__init__(config)
        
        # Get scoring constants from instance config or use defaults
        self.MAX_TYPES_DEFINED_SCORE = self.config.get("MAX_TYPES_DEFINED_SCORE", DEFAULT_MAX_TYPES_DEFINED_SCORE)
        self.MAX_FORMATS_DEFINED_SCORE = self.config.get("MAX_FORMATS_DEFINED_SCORE", DEFAULT_MAX_FORMATS_DEFINED_SCORE)
        self.MAX_RANGES_DEFINED_SCORE = self.config.get("MAX_RANGES_DEFINED_SCORE", DEFAULT_MAX_RANGES_DEFINED_SCORE)
        self.MAX_VALIDATION_PERFORMED_SCORE = self.config.get("MAX_VALIDATION_PERFORMED_SCORE", DEFAULT_MAX_VALIDATION_PERFORMED_SCORE)
        self.MAX_VALIDATION_COMMUNICATED_SCORE = self.config.get("MAX_VALIDATION_COMMUNICATED_SCORE", DEFAULT_MAX_VALIDATION_COMMUNICATED_SCORE)
        self.REQUIRE_EXPLICIT_METADATA = self.config.get("REQUIRE_EXPLICIT_METADATA", DEFAULT_REQUIRE_EXPLICIT_METADATA)
    
    def _process_template_rules(self, connector: BaseConnector) -> Tuple[float, List[str], List[str]]:
        """
        Process template-specific rules if they are set.
        
        Args:
            connector: Data source connector
            
        Returns:
            Tuple containing:
                - score (0-20)
                - list of findings
                - list of recommendations
        """
        if not self.template_rules:
            return 0, [], []
            
        total_score = 0
        findings = []
        recommendations = []
        
        # Calculate total weight to validate it sums to 20
        total_weight = sum(rule.get('params', {}).get('weight', 0) for rule in self.template_rules)
        
        # Warn if weights don't sum to 20
        if abs(total_weight - 20) > 0.01:  # Allow for floating point precision
            logger.warning(
                f"Validity dimension rule weights sum to {total_weight}, not 20. "
                f"Scores may not be as expected. Consider adjusting weights to sum to 20."
            )
            findings.append(
                f"⚠️ Rule weights sum to {total_weight} instead of 20. "
                f"Each dimension should have rules totaling 20 points."
            )
        
        # Process each template rule
        for rule_config in self.template_rules:
            rule_type = rule_config.get('type')
            rule_params = rule_config.get('params', {})
            rule_weight = rule_params.get('weight', 0)
            
            # Try to get the rule class from registry
            rule_class = RuleRegistry.get_rule(f"validity.{rule_type.lower()}")
            if not rule_class:
                # Try without the dimension prefix
                rule_class = RuleRegistry.get_rule(rule_type.lower())
                
            if not rule_class:
                logger.warning(f"Unknown rule type: {rule_type}")
                continue
                
            # Create rule instance with template parameters
            rule = rule_class(rule_params)
            
            # Execute the rule
            try:
                result = rule.evaluate(connector)
                
                # Extract score from rule result
                rule_score = result.get('score', 0)
                
                # The rule_score represents how well the rule passed (0 to rule_weight)
                # Since weights now represent portions of 20, we use the score directly
                # but cap it at the rule's weight
                actual_score = min(rule_score, rule_weight)
                total_score += actual_score
                
                # Generate narrative for findings
                narrative = rule.generate_narrative(result)
                if narrative:
                    findings.append(f"[{rule_type}] {narrative}")
                    
                # Add score information to findings for transparency
                if actual_score < rule_weight:
                    findings.append(
                        f"[{rule_type}] Scored {actual_score:.1f}/{rule_weight} points"
                    )
                    
                # Add specific findings from rule result
                if 'column_results' in result:
                    for col, details in result.get('column_results', {}).items():
                        if not details.get('consistent', True) or details.get('violations', 0) > 0:
                            findings.append(f"Issues in column '{col}': {details}")
                            
                # Add recommendations based on rule results
                if not result.get('valid', True):
                    recommendations.append(f"Address {rule_type} issues to improve data quality")
                    
            except Exception as e:
                logger.error(f"Error executing rule {rule_type}: {e}")
                findings.append(f"Failed to execute rule {rule_type}: {str(e)}")
                
        # Ensure score doesn't exceed 20
        total_score = min(total_score, 20)
        
        return total_score, findings, recommendations
    
    def assess(self, connector: BaseConnector) -> Tuple[float, List[str], List[str]]:
        """
        Assess the validity dimension for a data source.
        
        Args:
            connector: Data source connector
            
        Returns:
            Tuple containing:
                - score (0-20)
                - list of findings
                - list of recommendations
        """
        logger.info(f"Assessing validity dimension for {connector.get_name()}")
        
        findings = []
        recommendations = []
        score_components = {}
        
        # If template rules are set, use them instead of standard assessment
        if self.template_rules:
            logger.info("Using template-specific validity rules")
            return self._process_template_rules(connector)
        
        # Check if we're in discovery mode and have business logic enabled
        business_logic_enabled = self.config.get("business_logic_enabled", False)
        if not self.REQUIRE_EXPLICIT_METADATA and business_logic_enabled and hasattr(connector, 'df'):
            # Use business-focused validity scoring
            business_score, business_findings, business_recommendations = calculate_business_validity_score(
                connector.df, 
                data_type=None  # Auto-detect
            )
            
            # In discovery mode, business validity takes precedence
            findings.extend(business_findings)
            recommendations.extend(business_recommendations)
            
            # Start with business score as the base
            return business_score, findings, recommendations
        
        # Get schema information
        schema = connector.get_schema()
        
        # 1. Evaluate whether data types are explicitly defined (from schema)
        field_types_defined = "fields" in schema and all("type" in f for f in schema.get("fields", []))
        types_defined_score = self.MAX_TYPES_DEFINED_SCORE if field_types_defined else 0
        score_components["types_defined"] = types_defined_score
        
        if field_types_defined:
            findings.append("Data types are explicitly defined for all fields")
        else:
            findings.append("Data types are not explicitly defined in schema")
            
        # 2. Evaluate whether data formats are defined (e.g., date formats, patterns)
        formats_defined = False
        format_fields = []
        
        for field in schema.get("fields", []):
            if "format" in field or "pattern" in field:
                format_fields.append(field["name"])
                
        formats_defined = len(format_fields) > 0
        formats_score = self.MAX_FORMATS_DEFINED_SCORE if formats_defined else 0
        score_components["formats_defined"] = formats_score
        
        if formats_defined:
            findings.append(f"Data formats are defined for {len(format_fields)} fields")
        else:
            findings.append("No explicit format definitions found in schema")
            
        # 3. Evaluate whether valid ranges are defined (in schema)
        ranges_defined = False
        range_fields = []
        
        for field in schema.get("fields", []):
            if "min_value" in field or "max_value" in field or "allowed_values" in field:
                range_fields.append(field["name"])
                
        ranges_defined = len(range_fields) > 0
        ranges_score = self.MAX_RANGES_DEFINED_SCORE if ranges_defined else 0
        score_components["ranges_defined"] = ranges_score
        
        if ranges_defined:
            findings.append(f"Valid ranges are defined for {len(range_fields)} fields")
        else:
            findings.append("No explicit range definitions found in schema")
            
        # Enhanced automatic validity checks
        auto_validity_performed = False
        if hasattr(connector, 'analyze_validity'):
            auto_validity_performed = True
            validity_analysis = connector.analyze_validity()
            
            # Process type inconsistencies
            type_inconsistencies = validity_analysis.get("type_inconsistencies", {})
            if type_inconsistencies:
                for column, details in type_inconsistencies.items():
                    findings.append(
                        f"Inconsistent data types in column '{column}': "
                        f"Expected {details['expected_type']}, found {details['inconsistent_count']} inconsistencies"
                    )
                    if "inconsistent_examples" in details and details["inconsistent_examples"]:
                        examples = ", ".join(str(x) for x in details["inconsistent_examples"])
                        findings.append(f"Examples: {examples}")
            else:
                findings.append("Data types are consistent across all columns")
                
                # Only improve the types_defined score if it wasn't already set from schema
                # and if we don't require explicit metadata
                if types_defined_score == 0 and not self.REQUIRE_EXPLICIT_METADATA:
                    # Calculate an automatic type consistency score based on issues found
                    total_columns = len(connector.df.columns)
                    inconsistent_columns = len(type_inconsistencies)
                    
                    if total_columns > 0:
                        consistency_ratio = 1 - (inconsistent_columns / total_columns)
                        # For datasets with inconsistencies, we want to reward valid datasets
                        # The maximum score for inconsistent datasets should be lower
                        if inconsistent_columns > 0:
                            # Apply a penalty for inconsistent datasets
                            auto_types_score = int(self.MAX_TYPES_DEFINED_SCORE * consistency_ratio * 0.7)
                            findings.append(f"Data types are inconsistent in {inconsistent_columns} of {total_columns} columns")
                        else:
                            # Fully consistent datasets get a better score
                            auto_types_score = int(self.MAX_TYPES_DEFINED_SCORE * 0.9)  # 90% of max
                            
                        score_components["types_defined"] = auto_types_score
                elif types_defined_score == 0 and self.REQUIRE_EXPLICIT_METADATA:
                    # When explicit metadata is required, give minimal points for inferred types
                    findings.append("No explicit data type definitions found, explicit metadata required")
                    score_components["types_defined"] = 0
            
            # Process format inconsistencies
            format_inconsistencies = validity_analysis.get("format_inconsistencies", {})
            if format_inconsistencies:
                for column, details in format_inconsistencies.items():
                    issue_type = details.get("type", "format inconsistency")
                    count = details.get("count", 0)
                    
                    if issue_type == "invalid_dates":
                        findings.append(f"Invalid date formats detected in column '{column}': {count} invalid values")
                        if "examples" in details and details["examples"]:
                            examples = ", ".join(str(x) for x in details["examples"])
                            findings.append(f"Examples of invalid dates: {examples}")
                    elif "inconsistent_length" in issue_type:
                        findings.append(f"Inconsistent ID formats in column '{column}': {count} values with non-standard length")
                        
                # Only improve the formats_defined score if it wasn't already set from schema
                # and if we don't require explicit metadata
                if formats_score == 0 and not self.REQUIRE_EXPLICIT_METADATA:
                        # Calculate an automatic format consistency score based on issues found
                        date_columns = [c for c, info in connector.infer_column_types().items() 
                                       if info.get("type") == "date"]
                        id_columns = [c for c, info in connector.infer_column_types().items() 
                                     if info.get("type") == "id"]
                        
                        format_columns = len(date_columns) + len(id_columns)
                        inconsistent_format_columns = len(format_inconsistencies)
                        
                        if format_columns > 0:
                            format_consistency_ratio = 1 - (inconsistent_format_columns / format_columns)
                            # Apply similar penalty for inconsistent formats
                            if inconsistent_format_columns > 0:
                                auto_formats_score = int(self.MAX_FORMATS_DEFINED_SCORE * format_consistency_ratio * 0.7)
                            else:
                                auto_formats_score = int(self.MAX_FORMATS_DEFINED_SCORE * 0.9)  # 90% of max
                                
                            score_components["formats_defined"] = auto_formats_score
                elif formats_score == 0 and self.REQUIRE_EXPLICIT_METADATA:
                    # When explicit metadata is required, give minimal points for inferred formats
                    findings.append("No explicit format definitions found, explicit metadata required")
                    score_components["formats_defined"] = 0
            
            # Process range violations
            range_violations = validity_analysis.get("range_violations", {})
            if range_violations:
                for column, details in range_violations.items():
                    issue_type = details.get("type", "range violation")
                    count = details.get("count", 0)
                    
                    if issue_type == "negative_values":
                        findings.append(f"Negative values detected in column '{column}' where values should be positive: {count} violations")
                        if "examples" in details and details["examples"]:
                            examples = ", ".join(str(x) for x in details["examples"])
                            findings.append(f"Examples of negative values: {examples}")
                    elif issue_type == "future_dates":
                        findings.append(f"Unexpected future dates detected in column '{column}': {count} violations")
                
                # Only improve the ranges_defined score if it wasn't already set from schema
                # and if we don't require explicit metadata
                if ranges_score == 0 and not self.REQUIRE_EXPLICIT_METADATA:
                    # Calculate an automatic range validation score based on issues found
                    numeric_columns = [c for c, info in connector.infer_column_types().items() 
                                      if info.get("type") in ("numeric", "integer")]
                    
                    if numeric_columns:
                        range_violation_ratio = len(range_violations) / len(numeric_columns)
                        # Lower score with more violations
                        if len(range_violations) > 0:
                            auto_ranges_score = int(self.MAX_RANGES_DEFINED_SCORE * (1 - min(1.0, range_violation_ratio)) * 0.7)
                        else:
                            auto_ranges_score = int(self.MAX_RANGES_DEFINED_SCORE * 0.9)  # 90% of max
                            
                        score_components["ranges_defined"] = auto_ranges_score
                elif ranges_score == 0 and self.REQUIRE_EXPLICIT_METADATA:
                    # When explicit metadata is required, give minimal points for inferred ranges
                    findings.append("No explicit range definitions found, explicit metadata required")
                    score_components["ranges_defined"] = 0
            
            # Statistical outliers (potential validity issues)
            statistical_outliers = validity_analysis.get("statistical_outliers", {})
            if statistical_outliers:
                significant_outliers = {col: details for col, details in statistical_outliers.items()
                                       if details.get("outlier_percent", 0) > 5}
                
                if significant_outliers:
                    for column, details in significant_outliers.items():
                        findings.append(
                            f"Statistical outliers detected in column '{column}': "
                            f"{details.get('outlier_count', 0)} values ({details.get('outlier_percent', 0):.1f}%)"
                        )
        
        # 4. Evaluate whether validation is performed (metadata-based)
        validation_supported = connector.supports_validation()
        validation_results = connector.get_validation_results() if validation_supported else None
        validation_performed = validation_results is not None
        
        # If we have automatic validity analysis, that also counts as validation
        # if we don't require explicit metadata
        if not validation_performed and auto_validity_performed:
            if not self.REQUIRE_EXPLICIT_METADATA:
                validation_performed = True
                # For automatic validation, the score depends on whether the dataset is valid
                if validity_analysis and validity_analysis.get("valid_overall", True):
                    validation_score = int(self.MAX_VALIDATION_PERFORMED_SCORE * 0.8)  # Higher score for valid datasets
                else:
                    validation_score = self.MAX_VALIDATION_PERFORMED_SCORE // 2  # Lower score for invalid datasets
            else:
                # When explicit metadata is required, give minimal points for automatic validation
                findings.append("No explicit validation results found, explicit metadata required")
                validation_score = 0
                validation_performed = False
        else:
            validation_score = self.MAX_VALIDATION_PERFORMED_SCORE if validation_performed else 0
            
        score_components["validation_performed"] = validation_score
        
        if validation_performed:
            if validation_results:
                findings.append("Validation is performed on this data source")
                
                # Check if validation results indicate any issues
                if not validation_results.get("valid_overall", True):
                    invalid_rules = [
                        r for r in validation_results.get("rule_results", [])
                        if not r.get("valid", True)
                    ]
                    findings.append(f"Found {len(invalid_rules)} validation rule violations")
            elif auto_validity_performed:
                # Even if no explicit validation metadata, the automatic analysis counts
                findings.append("Automatic validation performed on data source")
                
                # Check overall validity from automatic analysis
                if not validity_analysis.get("valid_overall", True):
                    total_issues = (
                        len(validity_analysis.get("type_inconsistencies", {})) +
                        len(validity_analysis.get("format_inconsistencies", {})) +
                        len(validity_analysis.get("range_violations", {}))
                    )
                    findings.append(f"Found {total_issues} validity issues through automatic validation")
        else:
            findings.append("No evidence of validation being performed")
        
        # 5. Most importantly, evaluate whether validation results are communicated to agents
        validation_communicated = (
            validation_performed and 
            (
                # Either explicit metadata-based validation results
                (isinstance(validation_results, dict) and len(validation_results) > 0) or
                # Or our automatic validity analysis results
                (auto_validity_performed and validity_analysis is not None)
            )
        )
        
        # Automatic validation gets a lower score than explicit communication
        if validation_communicated and validation_results:
            comm_score = self.MAX_VALIDATION_COMMUNICATED_SCORE
        elif validation_communicated and auto_validity_performed and not self.REQUIRE_EXPLICIT_METADATA:
            # For automatic validation, the score depends on whether the dataset is valid
            if validity_analysis and validity_analysis.get("valid_overall", True):
                comm_score = int(self.MAX_VALIDATION_COMMUNICATED_SCORE * 0.7)  # Higher score for valid datasets
            else:
                comm_score = self.MAX_VALIDATION_COMMUNICATED_SCORE // 3  # Lower score for invalid datasets
        else:
            # No validation communication or explicit metadata required but not provided
            comm_score = 0
            if self.REQUIRE_EXPLICIT_METADATA and auto_validity_performed:
                findings.append("Automatic validation available but explicit validation metadata required")
            
        score_components["validation_communicated"] = comm_score
        
        if validation_communicated:
            if validation_results:
                findings.append("Validation results are explicitly communicated in machine-readable format")
            else:
                findings.append("Automatic validation results are available but not explicitly designed for agents")
        else:
            findings.append("Validation results are not explicitly communicated to agents")
        
        # Calculate overall score (0-20)
        score = sum(score_components.values())
        
        # Ensure we don't exceed the maximum score
        score = min(score, 20)
        
        # Generate recommendations based on findings
        if score_components.get("types_defined", 0) < self.MAX_TYPES_DEFINED_SCORE:
            if field_types_defined:
                # Schema exists but may not be complete
                recommendations.append("Ensure all fields have explicit data type definitions")
            else:
                # No schema or inconsistent data types
                recommendations.append("Define explicit data types for all fields")
                
                # If we found type inconsistencies through auto analysis
                if auto_validity_performed and type_inconsistencies:
                    for column, details in type_inconsistencies.items():
                        expected_type = details.get("expected_type", "consistent")
                        recommendations.append(
                            f"Fix inconsistent values in column '{column}' to match {expected_type} type"
                        )
        
        if score_components.get("formats_defined", 0) < self.MAX_FORMATS_DEFINED_SCORE:
            recommendations.append("Define formats (e.g., date patterns, string patterns) for applicable fields")
            
            # Add specific recommendations based on auto analysis
            if auto_validity_performed and format_inconsistencies:
                for column, details in format_inconsistencies.items():
                    if details.get("type") == "invalid_dates":
                        recommendations.append(f"Fix invalid date formats in column '{column}'")
        
        if score_components.get("ranges_defined", 0) < self.MAX_RANGES_DEFINED_SCORE:
            recommendations.append("Define valid ranges (min/max values, allowed values) for applicable fields")
            
            # Add specific recommendations based on auto analysis
            if auto_validity_performed and range_violations:
                for column, details in range_violations.items():
                    if details.get("type") == "negative_values":
                        recommendations.append(f"Address negative values in '{column}' column")
        
        if score_components.get("validation_performed", 0) < self.MAX_VALIDATION_PERFORMED_SCORE:
            recommendations.append("Implement validation rules for this data source")
            
        if score_components.get("validation_communicated", 0) < self.MAX_VALIDATION_COMMUNICATED_SCORE:
            recommendations.append(
                "Ensure validation results are explicitly communicated to agents in a machine-readable format"
            )
        
        # Add score component breakdown to findings
        findings.append(f"Score components: {score_components}")
        
        # Add umbrella recommendation if score is low
        if score < 10:
            recommendations.append(
                "Implement a comprehensive validity framework with explicit agent communication"
            )
                
        logger.info(f"Validity assessment complete. Score: {score}")
        return score, findings, recommendations

# ----------------------------------------------
# TEST COVERAGE
# ----------------------------------------------
# This component is tested through:
# 
# 1. Unit tests:
#    - tests/unit/dimensions/test_validity_detection.py::TestValidityDetection::test_assessor_differential_scoring
#    - tests/unit/dimensions/test_validity_detection.py::TestValidityDetection::test_analyze_validity_on_ideal_dataset
#    - tests/unit/dimensions/test_validity_detection.py::TestValidityDetection::test_analyze_validity_on_invalid_dataset
#    - tests/unit/dimensions/test_validity_detection.py::TestValidityDetection::test_specific_validity_issues_detection
# 
# 2. Integration tests:
#    - tests/integration/test_cli.py (for reporting validity results)
# 
# 3. Test datasets:
#    - test_datasets/ideal_dataset.csv (tests validity scoring for clean data)
#    - test_datasets/invalid_dataset.csv (tests validity issue detection)
#    - test_datasets/mixed_issues_dataset.csv (tests scoring with partial validity issues)
#
# Complete test coverage details are documented in:
# docs/test_coverage/VALIDITY_test_coverage.md
# ----------------------------------------------
