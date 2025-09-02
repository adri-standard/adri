"""
Basic assessment engine for ADRI V2.

This is a simplified stub implementation for testing the configuration integration.
"""

import os
import time
from typing import Any, Dict, List, Optional

import pandas as pd

from .audit_logger_csv import CSVAuditLogger
from .verodat_logger import VerodatLogger


class BundledStandardWrapper:
    """Wrapper class to make bundled standards compatible with YAML standard interface."""

    def __init__(self, standard_dict: Dict[str, Any]):
        """Initialize wrapper with bundled standard dictionary."""
        self.standard_dict = standard_dict

    def get_field_requirements(self) -> Dict[str, Any]:
        """Get field requirements from the bundled standard."""
        requirements = self.standard_dict.get("requirements", {})
        if isinstance(requirements, dict):
            field_requirements = requirements.get("field_requirements", {})
            return field_requirements if isinstance(field_requirements, dict) else {}
        return {}

    def get_overall_minimum(self) -> float:
        """Get the overall minimum score requirement."""
        requirements = self.standard_dict.get("requirements", {})
        if isinstance(requirements, dict):
            overall_minimum = requirements.get("overall_minimum", 75.0)
            return (
                float(overall_minimum)
                if isinstance(overall_minimum, (int, float))
                else 75.0
            )
        return 75.0


class AssessmentResult:
    """Represents the result of a data quality assessment."""

    def __init__(
        self,
        overall_score: float,
        passed: bool,
        dimension_scores: Dict[str, Any],
        standard_id: Optional[str] = None,
        assessment_date=None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Initialize assessment result with scores and metadata."""
        self.overall_score = overall_score
        self.passed = bool(passed)  # Ensure it's a Python bool, not numpy bool
        self.dimension_scores = dimension_scores
        self.standard_id = standard_id
        self.assessment_date = assessment_date
        self.metadata = metadata or {}
        self.rule_execution_log: List[Any] = []
        self.field_analysis: Dict[str, Any] = {}

    def add_rule_execution(self, rule_result):
        """Add a rule execution result to the assessment."""
        self.rule_execution_log.append(rule_result)

    def add_field_analysis(self, field_name: str, field_analysis):
        """Add field analysis to the assessment."""
        self.field_analysis[field_name] = field_analysis

    def set_dataset_info(self, total_records: int, total_fields: int, size_mb: float):
        """Set dataset information."""
        self.dataset_info = {
            "total_records": total_records,
            "total_fields": total_fields,
            "size_mb": size_mb,
        }

    def set_execution_stats(
        self,
        total_execution_time_ms: Optional[int] = None,
        rules_executed: Optional[int] = None,
        duration_ms: Optional[int] = None,
    ):
        """Set execution statistics."""
        # Support both parameter names for compatibility
        if duration_ms is not None:
            total_execution_time_ms = duration_ms

        self.execution_stats = {
            "total_execution_time_ms": total_execution_time_ms,
            "duration_ms": total_execution_time_ms,  # Alias for compatibility
            "rules_executed": rules_executed or len(self.rule_execution_log),
        }

    def to_standard_dict(self) -> Dict[str, Any]:
        """Convert assessment result to ADRI v0.1.0 compliant format using ReportGenerator."""
        from .report_generator import ReportGenerator

        # Use the template-driven report generator
        generator = ReportGenerator()
        return generator.generate_report(self)

    def to_v2_standard_dict(
        self, dataset_name: Optional[str] = None, adri_version: str = "0.1.0"
    ) -> Dict[str, Any]:
        """Convert assessment result to ADRI v0.1.0 compliant format."""
        from datetime import datetime

        # Convert dimension scores to simple numbers
        dimension_scores = {}
        for dim, score in self.dimension_scores.items():
            if hasattr(score, "score"):
                dimension_scores[dim] = float(score.score)
            else:
                dimension_scores[dim] = (
                    float(score) if isinstance(score, (int, float)) else score
                )

        # Build the v2 format structure
        report = {
            "adri_assessment_report": {
                "metadata": {
                    "assessment_id": f"adri_assessment_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    "adri_version": adri_version,
                    "timestamp": (
                        (self.assessment_date.isoformat() + "Z")
                        if self.assessment_date
                        else (datetime.now().isoformat() + "Z")
                    ),
                    "dataset_name": dataset_name or "unknown_dataset",
                    "dataset": {  # Required field as object
                        "name": dataset_name or "unknown_dataset",
                        "size_mb": getattr(self, "dataset_info", {}).get(
                            "size_mb", 0.0
                        ),
                        "total_records": getattr(self, "dataset_info", {}).get(
                            "total_records", 0
                        ),
                        "total_fields": getattr(self, "dataset_info", {}).get(
                            "total_fields", 0
                        ),
                    },
                    "standard_id": self.standard_id or "unknown_standard",
                    "standard_applied": {  # Required field as object
                        "id": self.standard_id or "unknown_standard",
                        "version": "1.0.0",
                        "domain": self.metadata.get("domain", "data_quality"),
                    },
                    "execution": {  # Required field
                        "total_execution_time_ms": getattr(
                            self, "execution_stats", {}
                        ).get("total_execution_time_ms", 0),
                        "duration_ms": getattr(self, "execution_stats", {}).get(
                            "total_execution_time_ms", 0
                        ),  # Required field
                        "rules_executed": len(self.rule_execution_log),
                        "total_validations": sum(
                            getattr(rule, "total_records", 0)
                            for rule in self.rule_execution_log
                        ),  # Required field
                    },
                    **self.metadata,
                },
                "summary": {
                    "overall_score": float(self.overall_score),
                    "overall_passed": bool(self.passed),
                    "pass_fail_status": {  # Required field as object
                        "overall_passed": bool(self.passed),
                        "dimension_passed": {
                            dim: score >= 15.0
                            for dim, score in dimension_scores.items()
                        },
                        "failed_dimensions": [
                            dim
                            for dim, score in dimension_scores.items()
                            if score < 15.0
                        ],
                        "critical_issues": 0,  # Required field as integer
                        "total_failures": sum(
                            getattr(analysis, "total_failures", 0)
                            for analysis in self.field_analysis.values()
                        ),  # Required field
                    },
                    "dimension_scores": dimension_scores,
                    "total_failures": sum(
                        getattr(analysis, "total_failures", 0)
                        for analysis in self.field_analysis.values()
                    ),
                },
                "rule_execution_log": [
                    rule.to_dict() for rule in self.rule_execution_log
                ],
                "field_analysis": {
                    field_name: analysis.to_dict()
                    for field_name, analysis in self.field_analysis.items()
                },
            }
        }

        # Add dataset info if available
        if hasattr(self, "dataset_info"):
            metadata_dict = report["adri_assessment_report"]["metadata"]
            if isinstance(metadata_dict, dict):
                metadata_dict["dataset_info"] = self.dataset_info

        # Add execution stats if available
        if hasattr(self, "execution_stats"):
            metadata_dict = report["adri_assessment_report"]["metadata"]
            if isinstance(metadata_dict, dict):
                metadata_dict["execution_stats"] = self.execution_stats

        return report

    def to_dict(self) -> Dict[str, Any]:
        """Convert assessment result to dictionary format."""
        return self.to_v2_standard_dict()


class DimensionScore:
    """Represents a score for a specific data quality dimension."""

    def __init__(
        self,
        score: float,
        max_score: float = 20.0,
        issues: Optional[List[Any]] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize dimension score with value and metadata."""
        self.score = score
        self.max_score = max_score
        self.issues = issues or []
        self.details = details or {}

    def percentage(self) -> float:
        """Convert score to percentage."""
        return (self.score / self.max_score) * 100.0


class FieldAnalysis:
    """Represents analysis results for a specific field."""

    def __init__(
        self,
        field_name: str,
        data_type: Optional[str] = None,
        null_count: Optional[int] = None,
        total_count: Optional[int] = None,
        rules_applied: Optional[List[Any]] = None,
        overall_field_score: Optional[float] = None,
        total_failures: Optional[int] = None,
        ml_readiness: Optional[str] = None,
        recommended_actions: Optional[List[Any]] = None,
    ):
        """Initialize field analysis with statistics and recommendations."""
        self.field_name = field_name
        self.data_type = data_type
        self.null_count = null_count
        self.total_count = total_count
        self.rules_applied = rules_applied or []
        self.overall_field_score = overall_field_score
        self.total_failures = total_failures or 0
        self.ml_readiness = ml_readiness
        self.recommended_actions = recommended_actions or []

        # Calculate completeness if we have the data
        if total_count is not None and null_count is not None:
            self.completeness: Optional[float] = (
                (total_count - null_count) / total_count if total_count > 0 else 0.0
            )
        else:
            self.completeness = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert field analysis to dictionary."""
        result = {
            "field_name": self.field_name,
            "rules_applied": self.rules_applied,
            "overall_field_score": self.overall_field_score,
            "total_failures": self.total_failures,
            "ml_readiness": self.ml_readiness,
            "recommended_actions": self.recommended_actions,
        }

        # Include legacy fields if available
        if self.data_type is not None:
            result["data_type"] = self.data_type
        if self.null_count is not None:
            result["null_count"] = self.null_count
        if self.total_count is not None:
            result["total_count"] = self.total_count
        if self.completeness is not None:
            result["completeness"] = self.completeness

        return result


class RuleExecutionResult:
    """Represents the result of executing a validation rule."""

    def __init__(
        self,
        rule_id: Optional[str] = None,
        dimension: Optional[str] = None,
        field: Optional[str] = None,
        rule_definition: Optional[str] = None,
        total_records: int = 0,
        passed: int = 0,
        failed: int = 0,
        rule_score: float = 0.0,
        rule_weight: float = 1.0,
        execution_time_ms: int = 0,
        sample_failures: Optional[List[Any]] = None,
        failure_patterns: Optional[Dict[str, Any]] = None,
        rule_name: Optional[str] = None,
        score: Optional[float] = None,
        message: str = "",
    ):
        """Initialize rule execution result with performance and failure data."""
        # Support both old and new signatures
        if rule_name is not None:
            # Old signature compatibility
            self.rule_name = rule_name
            self.rule_id = rule_name
            self.passed = passed if isinstance(passed, int) else (1 if passed else 0)
            self.score = score if score is not None else rule_score
            self.message = message
            # Set defaults for new fields
            self.dimension = dimension or "unknown"
            self.field = field or "unknown"
            self.rule_definition = rule_definition or ""
            self.total_records = total_records
            self.failed = failed
            self.rule_score = score if score is not None else rule_score
            self.rule_weight = rule_weight
            self.execution_time_ms = execution_time_ms
            self.sample_failures = sample_failures or []
            self.failure_patterns = failure_patterns or {}
        else:
            # New signature
            self.rule_id = rule_id or "unknown"
            self.rule_name = rule_id or "unknown"  # For backward compatibility
            self.dimension = dimension or "unknown"
            self.field = field or "unknown"
            self.rule_definition = rule_definition or ""
            self.total_records = total_records
            self.passed = passed  # Keep as numeric count, not boolean
            self.failed = failed
            self.rule_score = rule_score
            self.score = rule_score  # For backward compatibility
            self.rule_weight = rule_weight
            self.execution_time_ms = execution_time_ms
            self.sample_failures = sample_failures or []
            self.failure_patterns = failure_patterns or {}
            self.message = message

    def to_dict(self) -> Dict[str, Any]:
        """Convert rule execution result to dictionary."""
        # Fix passed count to be numeric, not boolean
        passed_count = (
            self.passed
            if isinstance(self.passed, int)
            else (self.total_records - self.failed)
        )

        return {
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "dimension": self.dimension,
            "field": self.field,
            "rule_definition": self.rule_definition,
            "total_records": self.total_records,
            "passed": passed_count,
            "failed": self.failed,
            "rule_score": self.rule_score,
            "score": self.score,
            "rule_weight": self.rule_weight,
            "execution_time_ms": self.execution_time_ms,
            "sample_failures": self.sample_failures,
            "failure_patterns": self.failure_patterns,
            "message": self.message,
            "execution": {  # Required field for v2.0 compliance
                "total_records": self.total_records,
                "passed": passed_count,
                "failed": self.failed,
                "execution_time_ms": self.execution_time_ms,
                "rule_score": self.rule_score,  # Required field
                "rule_weight": self.rule_weight,  # Required field
            },
            "failures": {  # Required field for v2.0 compliance
                "sample_failures": self.sample_failures,
                "failure_patterns": self.failure_patterns,
                "total_failed": self.failed,
            },
        }


class DataQualityAssessor:
    """Data quality assessor for ADRI validation with integrated audit logging."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the assessor with optional configuration.

        Args:
            config: Configuration dictionary with audit and verodat settings
        """
        self.engine = AssessmentEngine()
        self.config = config or {}

        # Initialize audit logger if configured
        self.audit_logger = None
        if self.config.get("audit", {}).get("enabled", False):
            self.audit_logger = CSVAuditLogger(self.config.get("audit", {}))

            # Initialize Verodat logger if configured
            verodat_config = self.config.get("verodat", {})
            if verodat_config.get("enabled", False):
                # Attach Verodat logger to audit logger
                self.audit_logger.verodat_logger = VerodatLogger(verodat_config)

    def assess(self, data, standard_path=None):
        """Assess data quality using optional standard with audit logging."""
        # Start timing
        start_time = time.time()

        # Handle different data formats
        if hasattr(data, "to_frame"):
            # Handle pandas Series
            data = data.to_frame()
        elif not hasattr(data, "columns"):
            # Handle dict or other data types
            import pandas as pd

            if isinstance(data, dict):
                data = pd.DataFrame([data])
            else:
                data = pd.DataFrame(data)

        # Run assessment
        if standard_path:
            result = self.engine.assess(data, standard_path)
            result.standard_id = os.path.basename(standard_path).replace(".yaml", "")
        else:
            result = self.engine._basic_assessment(data)

        # Calculate execution time
        duration_ms = int((time.time() - start_time) * 1000)

        # Log assessment if audit logger is configured
        if self.audit_logger:
            # Prepare execution context
            execution_context = {
                "function_name": "assess",
                "module_path": "adri.core.assessor",
                "environment": os.environ.get("ADRI_ENV", "PRODUCTION"),
            }

            # Prepare data info
            data_info = {
                "row_count": len(data),
                "column_count": len(data.columns),
                "columns": list(data.columns),
            }

            # Prepare performance metrics
            performance_metrics = {
                "duration_ms": duration_ms,
                "rows_per_second": (
                    len(data) / (duration_ms / 1000.0) if duration_ms > 0 else 0
                ),
            }

            # Prepare failed checks (extract from dimension scores)
            failed_checks = []
            for dim_name, dim_score in result.dimension_scores.items():
                if hasattr(dim_score, "score") and dim_score.score < 15:
                    failed_checks.append(
                        {
                            "dimension": dim_name,
                            "issue": f"Low score: {dim_score.score:.1f}/20",
                            "affected_percentage": ((20 - dim_score.score) / 20) * 100,
                        }
                    )

            # Log the assessment
            audit_record = self.audit_logger.log_assessment(
                assessment_result=result,
                execution_context=execution_context,
                data_info=data_info,
                performance_metrics=performance_metrics,
                failed_checks=failed_checks if failed_checks else None,
            )

            # Send to Verodat if configured
            if hasattr(self.audit_logger, "verodat_logger"):
                verodat_logger = getattr(self.audit_logger, "verodat_logger", None)
                if verodat_logger:
                    # Add the audit record to the batch
                    verodat_logger.add_to_batch(audit_record)

                # The VerodatLogger will handle batching and auto-flush at the configured batch size
                # For immediate upload (useful for testing), we could call flush_all() here
                # but it's better to let it batch for performance

        return result


class AssessmentEngine:
    """Basic assessment engine for data quality evaluation."""

    def assess(self, data: pd.DataFrame, standard_path: str) -> AssessmentResult:
        """
        Run assessment on data using the provided standard.

        Args:
            data: DataFrame containing the data to assess
            standard_path: Path to YAML standard file

        Returns:
            AssessmentResult object
        """
        # Load the YAML standard
        from ..cli.commands import load_standard

        try:
            yaml_dict = load_standard(standard_path)
            standard = BundledStandardWrapper(yaml_dict)
        except Exception:
            # Fallback to basic assessment if standard can't be loaded
            return self._basic_assessment(data)

        # Perform assessment using the standard's requirements
        validity_score = self._assess_validity_with_standard(data, standard)
        completeness_score = self._assess_completeness_with_standard(data, standard)
        consistency_score = self._assess_consistency(data)  # Keep basic for now
        freshness_score = self._assess_freshness(data)  # Keep basic for now
        plausibility_score = self._assess_plausibility(data)  # Keep basic for now

        dimension_scores = {
            "validity": DimensionScore(validity_score),
            "completeness": DimensionScore(completeness_score),
            "consistency": DimensionScore(consistency_score),
            "freshness": DimensionScore(freshness_score),
            "plausibility": DimensionScore(plausibility_score),
        }

        # Calculate overall score
        total_score = sum(score.score for score in dimension_scores.values())
        overall_score = (total_score / 100.0) * 100.0  # Convert to percentage

        # Get minimum score from standard or use default
        min_score = standard.get_overall_minimum()
        passed = overall_score >= min_score

        return AssessmentResult(overall_score, passed, dimension_scores)

    def assess_with_standard_dict(
        self, data: pd.DataFrame, standard_dict: Dict[str, Any]
    ) -> AssessmentResult:
        """
        Run assessment on data using a bundled standard dictionary.

        Args:
            data: DataFrame containing the data to assess
            standard_dict: Dictionary containing the standard definition

        Returns:
            AssessmentResult object
        """
        try:
            # Create a wrapper object that mimics the YAML standard interface
            standard_wrapper = BundledStandardWrapper(standard_dict)

            # Perform assessment using the standard's requirements
            validity_score = self._assess_validity_with_standard(data, standard_wrapper)
            completeness_score = self._assess_completeness_with_standard(
                data, standard_wrapper
            )
            consistency_score = self._assess_consistency(data)  # Keep basic for now
            freshness_score = self._assess_freshness(data)  # Keep basic for now
            plausibility_score = self._assess_plausibility(data)  # Keep basic for now

            dimension_scores = {
                "validity": DimensionScore(validity_score),
                "completeness": DimensionScore(completeness_score),
                "consistency": DimensionScore(consistency_score),
                "freshness": DimensionScore(freshness_score),
                "plausibility": DimensionScore(plausibility_score),
            }

            # Calculate overall score
            total_score = sum(score.score for score in dimension_scores.values())
            overall_score = (total_score / 100.0) * 100.0  # Convert to percentage

            # Get minimum score from standard or use default
            min_score = standard_dict.get("requirements", {}).get(
                "overall_minimum", 75.0
            )
            passed = overall_score >= min_score

            return AssessmentResult(overall_score, passed, dimension_scores)

        except Exception:
            # Fallback to basic assessment if standard can't be processed
            return self._basic_assessment(data)

    def _basic_assessment(self, data: pd.DataFrame) -> AssessmentResult:
        """Fallback basic assessment when standard can't be loaded."""
        validity_score = self._assess_validity(data)
        completeness_score = self._assess_completeness(data)
        consistency_score = self._assess_consistency(data)
        freshness_score = self._assess_freshness(data)
        plausibility_score = self._assess_plausibility(data)

        dimension_scores = {
            "validity": DimensionScore(validity_score),
            "completeness": DimensionScore(completeness_score),
            "consistency": DimensionScore(consistency_score),
            "freshness": DimensionScore(freshness_score),
            "plausibility": DimensionScore(plausibility_score),
        }

        total_score = sum(score.score for score in dimension_scores.values())
        overall_score = (total_score / 100.0) * 100.0
        passed = overall_score >= 75.0

        return AssessmentResult(overall_score, passed, dimension_scores)

    def _assess_validity_with_standard(
        self, data: pd.DataFrame, standard: Any
    ) -> float:
        """Assess validity using rules from the YAML standard."""
        total_checks = 0
        failed_checks = 0

        # Get field requirements from standard
        try:
            field_requirements = standard.get_field_requirements()
        except Exception:
            # Fallback to basic validity check
            return self._assess_validity(data)

        for column in data.columns:
            if column in field_requirements:
                field_req = field_requirements[column]

                for value in data[column].dropna():
                    total_checks += 1

                    # Check type constraints
                    if not self._check_field_type(value, field_req):
                        failed_checks += 1
                        continue

                    # Check pattern constraints (e.g., email regex)
                    if not self._check_field_pattern(value, field_req):
                        failed_checks += 1
                        continue

                    # Check range constraints
                    if not self._check_field_range(value, field_req):
                        failed_checks += 1
                        continue

        if total_checks == 0:
            return 18.0  # Default good score if no checks

        # Calculate score (0-20 scale)
        success_rate = (total_checks - failed_checks) / total_checks
        return success_rate * 20.0

    def _assess_completeness_with_standard(
        self, data: pd.DataFrame, standard: Any
    ) -> float:
        """Assess completeness using nullable requirements from standard."""
        try:
            field_requirements = standard.get_field_requirements()
        except Exception:
            # Fallback to basic completeness check
            return self._assess_completeness(data)

        total_required_fields = 0
        missing_required_values = 0

        for column in data.columns:
            if column in field_requirements:
                field_req = field_requirements[column]
                nullable = field_req.get("nullable", True)

                if not nullable:  # Field is required
                    total_required_fields += len(data)
                    missing_required_values += data[column].isnull().sum()

        if total_required_fields == 0:
            # No required fields defined, use basic completeness
            return self._assess_completeness(data)

        completeness_rate = (
            total_required_fields - missing_required_values
        ) / total_required_fields
        return completeness_rate * 20.0

    def _check_field_type(self, value: Any, field_req: Dict[str, Any]) -> bool:
        """Check if value matches the required type."""
        required_type = field_req.get("type", "string")

        try:
            if required_type == "integer":
                int(value)
                return True
            elif required_type == "float":
                float(value)
                return True
            elif required_type == "string":
                return isinstance(value, str)
            elif required_type == "boolean":
                return isinstance(value, bool) or str(value).lower() in [
                    "true",
                    "false",
                    "1",
                    "0",
                ]
            elif required_type == "date":
                # Basic date validation
                import re

                date_patterns = [
                    r"^\d{4}-\d{2}-\d{2}$",  # YYYY-MM-DD
                    r"^\d{2}/\d{2}/\d{4}$",  # MM/DD/YYYY
                ]
                return any(re.match(pattern, str(value)) for pattern in date_patterns)
        except Exception:
            return False

        return True

    def _check_field_pattern(self, value: Any, field_req: Dict[str, Any]) -> bool:
        """Check if value matches the required pattern (e.g., email regex)."""
        pattern = field_req.get("pattern")
        if not pattern:
            return True

        try:
            import re

            return bool(re.match(pattern, str(value)))
        except Exception:
            return False

    def _check_field_range(self, value: Any, field_req: Dict[str, Any]) -> bool:
        """Check if value is within the required range."""
        try:
            numeric_value = float(value)

            min_val = field_req.get("min_value")
            max_val = field_req.get("max_value")

            if min_val is not None and numeric_value < min_val:
                return False

            if max_val is not None and numeric_value > max_val:
                return False

            return True
        except Exception:
            # Not a numeric value, skip range check
            return True

    def _assess_validity(self, data: pd.DataFrame) -> float:
        """Assess data validity (format correctness)."""
        total_checks = 0
        failed_checks = 0

        for column in data.columns:
            if "email" in column.lower():
                # Check email format
                for value in data[column].dropna():
                    total_checks += 1
                    if not self._is_valid_email(str(value)):
                        failed_checks += 1

            elif "age" in column.lower():
                # Check age values
                for value in data[column].dropna():
                    total_checks += 1
                    try:
                        age = float(value)
                        if age < 0 or age > 150:
                            failed_checks += 1
                    except (ValueError, TypeError):
                        failed_checks += 1

        if total_checks == 0:
            return 18.0  # Default good score if no checks

        # Calculate score (0-20 scale)
        success_rate = (total_checks - failed_checks) / total_checks
        return success_rate * 20.0

    def _assess_completeness(self, data: pd.DataFrame) -> float:
        """Assess data completeness (missing values)."""
        if data.empty:
            return 0.0

        total_cells = int(data.size)
        missing_cells = int(data.isnull().sum().sum())
        completeness_rate = (total_cells - missing_cells) / total_cells

        return float(completeness_rate * 20.0)

    def _assess_consistency(self, data: pd.DataFrame) -> float:
        """Assess data consistency."""
        # Simple consistency check - return good score for now
        return 16.0

    def _assess_freshness(self, data: pd.DataFrame) -> float:
        """Assess data freshness."""
        # Simple freshness check - return good score for now
        return 19.0

    def _assess_plausibility(self, data: pd.DataFrame) -> float:
        """Assess data plausibility."""
        # Simple plausibility check - return good score for now
        return 15.5

    # Public methods for backward compatibility with tests
    def assess_validity(
        self, data: pd.DataFrame, field_requirements: Optional[Dict[str, Any]] = None
    ) -> float:
        """Public method for validity assessment."""
        if field_requirements:
            # Create a mock standard wrapper for the field requirements
            mock_standard = type(
                "MockStandard",
                (),
                {"get_field_requirements": lambda: field_requirements},
            )()
            return self._assess_validity_with_standard(data, mock_standard)
        return self._assess_validity(data)

    def assess_completeness(
        self, data: pd.DataFrame, requirements: Optional[Dict[str, Any]] = None
    ) -> float:
        """Public method for completeness assessment."""
        if requirements:
            # Handle completeness requirements
            mandatory_fields = requirements.get("mandatory_fields", [])
            if mandatory_fields:
                total_required_cells = len(data) * len(mandatory_fields)
                missing_required_cells = sum(
                    data[field].isnull().sum()
                    for field in mandatory_fields
                    if field in data.columns
                )
                if total_required_cells > 0:
                    completeness_rate = (
                        total_required_cells - missing_required_cells
                    ) / total_required_cells
                    return float(completeness_rate * 20.0)
        return self._assess_completeness(data)

    def assess_consistency(
        self, data: pd.DataFrame, consistency_rules: Optional[Dict[str, Any]] = None
    ) -> float:
        """Public method for consistency assessment."""
        if consistency_rules:
            # Basic consistency scoring based on format rules
            total_checks = 0
            failed_checks = 0

            format_rules = consistency_rules.get("format_rules", {})
            for field, rule in format_rules.items():
                if field in data.columns:
                    for value in data[field].dropna():
                        total_checks += 1
                        # Simple format checking
                        if rule == "title_case" and not str(value).istitle():
                            failed_checks += 1
                        elif rule == "lowercase" and str(value) != str(value).lower():
                            failed_checks += 1

            if total_checks > 0:
                success_rate = (total_checks - failed_checks) / total_checks
                return success_rate * 20.0
        return self._assess_consistency(data)

    def assess_freshness(
        self, data: pd.DataFrame, freshness_config: Optional[Dict[str, Any]] = None
    ) -> float:
        """Public method for freshness assessment."""
        if freshness_config:
            # Basic freshness assessment
            date_fields = freshness_config.get("date_fields", [])
            if date_fields:
                # Simple freshness check - return good score if date fields exist
                return 18.0
        return self._assess_freshness(data)

    def assess_plausibility(
        self, data: pd.DataFrame, plausibility_config: Optional[Dict[str, Any]] = None
    ) -> float:
        """Public method for plausibility assessment."""
        if plausibility_config:
            # Basic plausibility assessment
            total_checks = 0
            failed_checks = 0

            outlier_detection = plausibility_config.get("outlier_detection", {})
            business_rules = plausibility_config.get("business_rules", {})

            # Check business rules
            for field, rules in business_rules.items():
                if field in data.columns:
                    min_val = rules.get("min")
                    max_val = rules.get("max")
                    for value in data[field].dropna():
                        total_checks += 1
                        try:
                            numeric_value = float(value)
                            if min_val is not None and numeric_value < min_val:
                                failed_checks += 1
                            elif max_val is not None and numeric_value > max_val:
                                failed_checks += 1
                        except Exception:
                            failed_checks += 1

            # Check outlier detection rules
            for field, rules in outlier_detection.items():
                if field in data.columns:
                    method = rules.get("method")
                    if method == "range":
                        min_val = rules.get("min")
                        max_val = rules.get("max")
                        for value in data[field].dropna():
                            total_checks += 1
                            try:
                                numeric_value = float(value)
                                if min_val is not None and numeric_value < min_val:
                                    failed_checks += 1
                                elif max_val is not None and numeric_value > max_val:
                                    failed_checks += 1
                            except Exception:
                                failed_checks += 1

            if total_checks > 0:
                success_rate = (total_checks - failed_checks) / total_checks
                return success_rate * 20.0
        return self._assess_plausibility(data)

    def _is_valid_email(self, email: str) -> bool:
        """Check if email format is valid."""
        import re

        # Basic email pattern - must have exactly one @ symbol
        if email.count("@") != 1:
            return False

        # More comprehensive email regex
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(pattern, email))
