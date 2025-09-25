"""
ADRI Validator Engine.

Core data quality assessment and validation engine functionality.
Migrated from adri/core/assessor.py for the new src/ layout.
"""

import os
import time
from typing import Any, Dict, List, Optional

import pandas as pd

# Updated imports for new structure - with fallbacks during migration
try:
    from ..logging.local import CSVAuditLogger
except ImportError:
    try:
        from adri.core.audit_logger_csv import CSVAuditLogger
    except ImportError:
        CSVAuditLogger = None  # type: ignore

try:
    from ..logging.enterprise import VerodatLogger
except ImportError:
    try:
        from adri.core.verodat_logger import VerodatLogger
    except ImportError:
        VerodatLogger = None  # type: ignore


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

    def get_dimension_requirements(self) -> Dict[str, Any]:
        """Get dimension requirements (including weights and scoring config) from the standard."""
        requirements = self.standard_dict.get("requirements", {})
        if isinstance(requirements, dict):
            dim_reqs = requirements.get("dimension_requirements", {})
            return dim_reqs if isinstance(dim_reqs, dict) else {}
        return {}


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
        # Updated import for new structure - with fallback during migration
        try:
            from adri.core.report_generator import ReportGenerator
        except ImportError:
            # During migration, we may not have moved report_generator yet
            # For now, use the v2 format
            return self.to_v2_standard_dict()

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
    """Data quality assessor for ADRI validation with integrated audit logging.

    # TEST COMMENT: Testing adaptive issue-driven workflow validation for high-risk core changes
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the DataQualityAssessor with optional configuration."""
        self.engine = ValidationEngine()  # Updated to use ValidationEngine
        self.config = config or {}

        # Initialize audit logger if configured
        self.audit_logger = None
        if self.config.get("audit", {}).get("enabled", False) and CSVAuditLogger:
            self.audit_logger = CSVAuditLogger(self.config.get("audit", {}))

            # Initialize Verodat logger if configured
            verodat_config = self.config.get("verodat", {})
            if verodat_config.get("enabled", False) and VerodatLogger:
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
                "module_path": "adri.validator.engine",  # Updated module path
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


class ValidationEngine:
    """Main validation engine for data quality assessment. Renamed from AssessmentEngine."""

    def __init__(self):
        # Warnings and explain payload are reset per assessment
        self._scoring_warnings: List[str] = []
        self._explain: Dict[str, Any] = {}

    def _reset_explain(self):
        self._scoring_warnings = []
        self._explain = {}

    def _normalize_nonneg_weights(self, weights: Dict[str, float]) -> Dict[str, float]:
        """Clamp negatives to 0.0 and coerce to float for weight dictionaries."""
        norm: Dict[str, float] = {}
        for k, v in weights.items():
            try:
                w = float(v)
            except Exception:
                w = 0.0
            if w < 0.0:
                w = 0.0
            norm[k] = w
        return norm

    def _equalize_if_zero(
        self, weights: Dict[str, float], label: str
    ) -> Dict[str, float]:
        """If all weights sum to 0, assign equal weight of 1.0 to each present key and record a warning."""
        total = sum(weights.values())
        if len(weights) > 0 and total <= 0.0:
            for k in list(weights.keys()):
                weights[k] = 1.0
            self._scoring_warnings.append(
                f"{label} weights were zero/invalid; applied equal weights of 1.0 to present dimensions"
            )
        return weights

    def _normalize_rule_weights(
        self,
        rule_weights_cfg: Dict[str, float],
        rule_keys: List[str],
        counts: Dict[str, Dict[str, int]],
    ) -> Dict[str, float]:
        """Normalize validity rule weights: clamp negatives, drop unknowns, and equalize when all zero for active rule-types."""
        applied: Dict[str, float] = {}
        for rk, w in (rule_weights_cfg or {}).items():
            if rk not in rule_keys:
                continue
            try:
                fw = float(w)
            except Exception:
                fw = 0.0
            if fw < 0.0:
                fw = 0.0
            applied[rk] = fw

        # Keep only rule types that had any evaluations
        active = {
            rk: applied.get(rk, 0.0)
            for rk in rule_keys
            if counts.get(rk, {}).get("total", 0) > 0
        }
        if active and sum(active.values()) <= 0.0:
            for rk in active.keys():
                active[rk] = 1.0
            self._scoring_warnings.append(
                "Validity rule_weights were zero/invalid; applied equal weights across active rule types"
            )
        return active

    # --------------------- Validity scoring helper methods ---------------------
    def _compute_validity_rule_counts(
        self, data: pd.DataFrame, field_requirements: Dict[str, Any]
    ):
        """
        Compute totals and passes per rule type and per field for validity scoring.

        Returns (counts, per_field_counts) with the same structure used in explain payloads.
        """
        # Import validation rules (apply in strict order)
        from collections import defaultdict

        from .rules import (
            check_allowed_values,
            check_date_bounds,
            check_field_pattern,
            check_field_range,
            check_field_type,
            check_length_bounds,
        )

        RULE_KEYS = [
            "type",
            "allowed_values",
            "length_bounds",
            "pattern",
            "numeric_bounds",
            "date_bounds",
        ]

        counts = {rk: {"passed": 0, "total": 0} for rk in RULE_KEYS}
        per_field_counts: Dict[str, Dict[str, Dict[str, int]]] = defaultdict(
            lambda: {rk: {"passed": 0, "total": 0} for rk in RULE_KEYS}
        )

        for column in data.columns:
            if column not in field_requirements:
                continue
            field_req = field_requirements[column]
            series = data[column].dropna()

            for value in series:
                # 1) Type
                counts["type"]["total"] += 1
                per_field_counts[column]["type"]["total"] += 1
                if not check_field_type(value, field_req):
                    # type failed; short-circuit further checks for this value
                    continue
                counts["type"]["passed"] += 1
                per_field_counts[column]["type"]["passed"] += 1

                # 2) Allowed values (only if rule present)
                if "allowed_values" in field_req:
                    counts["allowed_values"]["total"] += 1
                    per_field_counts[column]["allowed_values"]["total"] += 1
                    if not check_allowed_values(value, field_req):
                        continue
                    counts["allowed_values"]["passed"] += 1
                    per_field_counts[column]["allowed_values"]["passed"] += 1

                # 3) Length bounds (only if present)
                if ("min_length" in field_req) or ("max_length" in field_req):
                    counts["length_bounds"]["total"] += 1
                    per_field_counts[column]["length_bounds"]["total"] += 1
                    if not check_length_bounds(value, field_req):
                        continue
                    counts["length_bounds"]["passed"] += 1
                    per_field_counts[column]["length_bounds"]["passed"] += 1

                # 4) Pattern (only if present)
                if "pattern" in field_req:
                    counts["pattern"]["total"] += 1
                    per_field_counts[column]["pattern"]["total"] += 1
                    if not check_field_pattern(value, field_req):
                        continue
                    counts["pattern"]["passed"] += 1
                    per_field_counts[column]["pattern"]["passed"] += 1

                # 5) Numeric bounds (only if present)
                if ("min_value" in field_req) or ("max_value" in field_req):
                    counts["numeric_bounds"]["total"] += 1
                    per_field_counts[column]["numeric_bounds"]["total"] += 1
                    if not check_field_range(value, field_req):
                        continue
                    counts["numeric_bounds"]["passed"] += 1
                    per_field_counts[column]["numeric_bounds"]["passed"] += 1

                # 6) Date/datetime bounds (only if present)
                if any(
                    k in field_req
                    for k in [
                        "after_date",
                        "before_date",
                        "after_datetime",
                        "before_datetime",
                    ]
                ):
                    counts["date_bounds"]["total"] += 1
                    per_field_counts[column]["date_bounds"]["total"] += 1
                    if not check_date_bounds(value, field_req):
                        continue
                    counts["date_bounds"]["passed"] += 1
                    per_field_counts[column]["date_bounds"]["passed"] += 1

        return counts, per_field_counts

    def _apply_global_rule_weights(
        self,
        counts: Dict[str, Dict[str, int]],
        rule_weights_cfg: Dict[str, float],
        rule_keys: List[str],
    ):
        """
        Apply normalized global rule weights to aggregate score.

        Returns (S_raw_contrib, W_contrib, applied_global_weights).
        """
        S_raw = 0.0
        W = 0.0
        applied_global = self._normalize_rule_weights(
            rule_weights_cfg, rule_keys, counts
        )

        for rule_name, weight in applied_global.items():
            total = counts.get(rule_name, {}).get("total", 0)
            if total <= 0:
                continue
            passed = counts[rule_name]["passed"]
            score_r = passed / total
            S_raw += float(weight) * score_r
            W += float(weight)

        return S_raw, W, applied_global

    def _apply_field_overrides(
        self,
        per_field_counts: Dict[str, Dict[str, Dict[str, int]]],
        overrides_cfg: Dict[str, Dict[str, float]],
        rule_keys: List[str],
    ):
        """
        Apply field-level overrides to aggregate score.

        Returns (S_raw_contrib, W_contrib, applied_overrides_dict).
        """
        S_add = 0.0
        W_add = 0.0
        applied_overrides: Dict[str, Dict[str, float]] = {}

        if isinstance(overrides_cfg, dict):
            for field_name, overrides in overrides_cfg.items():
                if field_name not in per_field_counts or not isinstance(
                    overrides, dict
                ):
                    continue
                for rule_name, weight in overrides.items():
                    if rule_name not in rule_keys:
                        continue
                    try:
                        fw = float(weight)
                    except Exception:
                        fw = 0.0
                    if fw <= 0.0:
                        if isinstance(weight, (int, float)) and weight < 0:
                            self._scoring_warnings.append(
                                f"Validity field_overrides contained negative weight for '{field_name}.{rule_name}', clamped to 0.0"
                            )
                        continue
                    c = per_field_counts[field_name].get(rule_name)
                    if not c or c.get("total", 0) <= 0:
                        continue
                    passed = c["passed"]
                    total = c["total"]
                    score_fr = passed / total
                    S_add += fw * score_fr
                    W_add += fw
                    applied_overrides.setdefault(field_name, {})[rule_name] = fw

        return S_add, W_add, applied_overrides

    def _assemble_validity_explain(
        self,
        counts: Dict[str, Any],
        per_field_counts: Dict[str, Any],
        applied_global: Dict[str, float],
        applied_overrides: Dict[str, Dict[str, float]],
    ) -> Dict[str, Any]:
        """Assemble the validity explain payload preserving existing schema."""
        return {
            "rule_counts": counts,
            "per_field_counts": per_field_counts,
            "applied_weights": {
                "global": applied_global,
                "overrides": applied_overrides,
            },
        }

    def assess(self, data: pd.DataFrame, standard_path: str) -> AssessmentResult:
        """
        Run assessment on data using the provided standard.

        Args:
            data: DataFrame containing the data to assess
            standard_path: Path to YAML standard file

        Returns:
            AssessmentResult object
        """
        # Reset explain/warnings for this run
        self._reset_explain()
        # Load the YAML standard - prefer validator.loaders, fallback to legacy CLI path
        load_standard_fn = None
        try:
            from .loaders import load_standard as _ls  # same package

            load_standard_fn = _ls
        except Exception:
            try:
                from adri.validator.loaders import load_standard as _ls2  # absolute

                load_standard_fn = _ls2
            except Exception:
                try:
                    # Legacy fallback (older tree)
                    from adri.cli.commands import load_standard as _ls3

                    load_standard_fn = _ls3
                except Exception:
                    return self._basic_assessment(data)

        try:
            yaml_dict = load_standard_fn(standard_path)
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

        # Calculate overall score using per-dimension weights if provided
        try:
            dim_reqs = standard.get_dimension_requirements()
        except Exception:
            dim_reqs = {}

        weights = {
            "validity": float(dim_reqs.get("validity", {}).get("weight", 1.0)),
            "completeness": float(dim_reqs.get("completeness", {}).get("weight", 1.0)),
            "consistency": float(dim_reqs.get("consistency", {}).get("weight", 1.0)),
            "freshness": float(dim_reqs.get("freshness", {}).get("weight", 1.0)),
            "plausibility": float(dim_reqs.get("plausibility", {}).get("weight", 1.0)),
        }
        # Normalize and guard weights
        applied_weights = self._normalize_nonneg_weights(weights)
        applied_weights = self._equalize_if_zero(applied_weights, "Dimension")

        weighted_sum = 0.0
        weight_total = 0.0
        for dim, ds in dimension_scores.items():
            w = applied_weights.get(dim, 1.0)
            weighted_sum += w * float(ds.score)
            weight_total += w

        # Weighted average on 0..20, then scale to 0..100
        overall_score = (
            ((weighted_sum / weight_total) / 20.0) * 100.0 if weight_total > 0 else 0.0
        )

        # Get minimum score from standard or use default
        min_score = standard.get_overall_minimum()
        passed = overall_score >= min_score

        # Build metadata with explain and warnings
        metadata: Dict[str, Any] = {
            "applied_dimension_weights": applied_weights,
        }
        if getattr(self, "_scoring_warnings", None):
            metadata["scoring_warnings"] = list(self._scoring_warnings)
        if getattr(self, "_explain", None):
            metadata["explain"] = self._explain

        return AssessmentResult(
            overall_score, passed, dimension_scores, None, None, metadata
        )

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
        # Import validation rules (apply in strict order)
        from .rules import (
            check_allowed_values,
            check_date_bounds,
            check_field_pattern,
            check_field_range,
            check_field_type,
            check_length_bounds,
        )

        # Try to get scoring policy (rule weights) from dimension_requirements.validity
        try:
            dim_reqs = standard.get_dimension_requirements()
            validity_cfg = dim_reqs.get("validity", {})
            scoring_cfg = validity_cfg.get("scoring", {})
            rule_weights_cfg: Dict[str, float] = scoring_cfg.get("rule_weights", {})
            field_overrides_cfg: Dict[str, Dict[str, float]] = scoring_cfg.get(
                "field_overrides", {}
            )
        except Exception:
            dim_reqs = {}
            validity_cfg = {}
            scoring_cfg = {}
            rule_weights_cfg = {}
            field_overrides_cfg = {}

        # If no rule_weights provided, fall back to previous simple method
        fallback_simple = (
            not isinstance(rule_weights_cfg, dict) or len(rule_weights_cfg) == 0
        )

        # Get field requirements from standard
        try:
            field_requirements = standard.get_field_requirements()
        except Exception:
            # Fallback to basic validity check
            return self._assess_validity(data)

        # If falling back, keep original aggregation
        if fallback_simple:
            total_checks = 0
            failed_checks = 0
            for column in data.columns:
                if column in field_requirements:
                    field_req = field_requirements[column]
                    for value in data[column].dropna():
                        total_checks += 1
                        if not check_field_type(value, field_req):
                            failed_checks += 1
                            continue
                        if not check_allowed_values(value, field_req):
                            failed_checks += 1
                            continue
                        if not check_length_bounds(value, field_req):
                            failed_checks += 1
                            continue
                        if not check_field_pattern(value, field_req):
                            failed_checks += 1
                            continue
                        if not check_field_range(value, field_req):
                            failed_checks += 1
                            continue
                        if not check_date_bounds(value, field_req):
                            failed_checks += 1
                            continue
            if total_checks == 0:
                return 18.0
            success_rate = (total_checks - failed_checks) / total_checks
            return success_rate * 20.0

        # Weighted rule-type scoring
        RULE_KEYS = [
            "type",
            "allowed_values",
            "length_bounds",
            "pattern",
            "numeric_bounds",
            "date_bounds",
        ]

        counts, per_field_counts = self._compute_validity_rule_counts(
            data, field_requirements
        )

        # Apply global weights and field overrides
        Sg, Wg, applied_global = self._apply_global_rule_weights(
            counts, rule_weights_cfg, RULE_KEYS
        )
        So, Wo, applied_overrides = self._apply_field_overrides(
            per_field_counts, field_overrides_cfg, RULE_KEYS
        )

        S_raw = Sg + So
        W = Wg + Wo

        if W <= 0.0:
            # No applicable weighted components; fall back to default good score
            self._scoring_warnings.append(
                "No applicable validity rule weights after normalization; using default score 18.0/20"
            )
            # Cache minimal explain payload
            self._explain["validity"] = self._assemble_validity_explain(
                counts, per_field_counts, applied_global, applied_overrides
            )
            return 18.0

        S = S_raw / W  # 0..1

        # Cache explain payload
        self._explain["validity"] = self._assemble_validity_explain(
            counts, per_field_counts, applied_global, applied_overrides
        )
        return S * 20.0

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

    def _assess_validity(self, data: pd.DataFrame) -> float:
        """Assess data validity (format correctness)."""
        total_checks = 0
        failed_checks = 0

        for column in data.columns:
            # Convert column to string to handle integer column names
            column_str = str(column).lower()

            if "email" in column_str:
                # Check email format
                for value in data[column].dropna():
                    total_checks += 1
                    if not self._is_valid_email(str(value)):
                        failed_checks += 1

            elif "age" in column_str:
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


# Alias for backward compatibility
AssessmentEngine = ValidationEngine
