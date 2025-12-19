# @ADRI_FEATURE[analysis_contract_generator, scope=OPEN_SOURCE]
# Description: Auto-generates ADRI contracts from data profiling and rule inference
"""
ADRI Standard Generator.

Refactored to use modular generation components for improved maintainability.
Coordinates field inference, dimension building, and explanation generation.
"""

import json
from typing import Any

import pandas as pd

from ..validator.rules import (
    check_date_bounds,
    check_field_pattern,
    check_field_range,
    check_field_type,
    check_length_bounds,
)
from .data_profiler import DataProfiler
from .generation import (
    ContractBuilder,
    DimensionRequirementsBuilder,
    ExplanationGenerator,
    FieldInferenceEngine,
)
from .rule_inference import (
    infer_allowed_values,
    infer_allowed_values_tolerant,
    infer_date_bounds,
    infer_length_bounds,
    infer_numeric_range,
    infer_numeric_range_robust,
    infer_regex_pattern,
    InferenceConfig,
)


class GenerationConfig:
    """Configuration for standard generation."""

    def __init__(self, **kwargs):
        """Initialize GenerationConfig with keyword arguments."""
        for key, value in kwargs.items():
            setattr(self, key, value)


class StandardTemplate:
    """Template for standard generation."""

    def __init__(self, template_id: str, template_data: dict):
        """Initialize StandardTemplate with template information."""
        self.template_id = template_id
        self.template_data = template_data


class ContractGenerator:
    """
    Generates ADRI-compliant YAML standards from data analysis.

    Refactored to use modular architecture with focused component classes
    for field inference, dimension requirements, and explanation generation.
    """

    def __init__(self, config=None):
        """Initialize the standard generator with modular components."""
        self.config = config or {}
        self.profiler = DataProfiler(config=self.config.get("profiler", {}))
        self.field_engine = FieldInferenceEngine()
        self.dimension_builder = DimensionRequirementsBuilder()
        self.standard_builder = ContractBuilder()
        self.explanation_generator = ExplanationGenerator()

    def _generate_standard_name(self, data_name: str) -> str:
        """
        Generate consistent standard names across all generation methods.

        Args:
            data_name: Base name for the standard

        Returns:
            Formatted standard name following naming conventions
        """
        display_name = data_name.replace("_", " ").title()

        # Check if "Standard" is already in the name to avoid duplication
        if display_name.endswith(" Standard"):
            return display_name

        if data_name and data_name.lower().startswith("test"):
            # For test data, use simple naming pattern
            return f"{display_name} Standard"
        else:
            # Normal naming pattern includes ADRI branding
            return f"{display_name} ADRI Standard"

    # ------------------------- Helper methods (refactor) -------------------------
    def _is_id_like(self, name: str | None) -> bool:
        """Heuristic to detect id-like column names to suppress enums."""
        if not name:
            return False
        lname = str(name).lower()
        for tok in ["id", "key", "code", "number", "num", "uuid", "guid"]:
            if tok in lname:
                return True
        return False

    def _infer_type_and_nullability(
        self, field_profile: dict[str, Any], series: pd.Series, inf_cfg: InferenceConfig
    ) -> dict[str, Any]:
        """
        Infer field 'type' and 'nullable' consistent with existing behavior.
        - Type mapping prioritizes datetime/date hints, then numeric coercion.
        - Nullability is False only when absolutely no nulls were observed.
        """
        dtype = field_profile.get("dtype", "object")
        common_patterns = field_profile.get("common_patterns", []) or []

        # Attempt numeric coercion for object columns only
        treat_as_numeric = False
        if "object" in dtype or dtype == "object":
            try:
                non_null = series.dropna()
                if len(non_null) > 0:
                    coerced = pd.to_numeric(non_null, errors="coerce")
                    if coerced.notna().all():
                        treat_as_numeric = True
            except Exception:
                treat_as_numeric = False

        # Integer types take priority - check int dtype first
        if "int" in dtype:
            inferred_type = "integer"
        elif "float" in dtype:
            inferred_type = "float"
        elif treat_as_numeric:
            # Object column that can be coerced to numeric - check if all values are whole numbers
            try:
                non_null = series.dropna()
                coerced = pd.to_numeric(non_null, errors="coerce")
                if (coerced == coerced.astype(int)).all():
                    inferred_type = "integer"
                else:
                    inferred_type = "float"
            except Exception:
                inferred_type = "float"
        elif "bool" in dtype:
            inferred_type = "boolean"
        elif "datetime" in dtype:
            inferred_type = "datetime"
        elif "date" in common_patterns:
            inferred_type = "date"
        else:
            inferred_type = "string"

        null_count = int(field_profile.get("null_count", 0) or 0)
        nullable = not (null_count == 0)

        return {"type": inferred_type, "nullable": nullable}

    def _infer_allowed_values(
        self,
        series: pd.Series,
        inf_cfg: InferenceConfig,
        col_name: str | None,
        pk_fields: list | None,
    ) -> list | None:
        """
        Infer allowed_values (enums) for string/integer fields when not id-like and not PK.
        Honors enum_strategy ('coverage' or 'tolerant') and coverage/uniqueness thresholds.
        """
        suppress_enum = False
        if pk_fields and col_name in pk_fields:
            suppress_enum = True
        if self._is_id_like(col_name):
            suppress_enum = True
        if suppress_enum:
            return None

        if getattr(inf_cfg, "enum_strategy", "coverage") == "tolerant":
            return infer_allowed_values_tolerant(
                series,
                min_coverage=inf_cfg.enum_min_coverage,
                top_k=getattr(inf_cfg, "enum_top_k", 10),
                max_unique=inf_cfg.enum_max_unique,
            )
        return infer_allowed_values(
            series,
            max_unique=inf_cfg.enum_max_unique,
            min_coverage=inf_cfg.enum_min_coverage,
        )

    def _infer_numeric_bounds(
        self, series: pd.Series, inf_cfg: InferenceConfig, treat_as_numeric: bool
    ) -> tuple | None:
        """
        Infer numeric range bounds using the configured strategy.
        Returns (min_value, max_value) as floats when available.
        """
        series_for_range = None
        try:
            if treat_as_numeric:
                series_for_range = pd.to_numeric(series, errors="coerce")
            else:
                series_for_range = series
        except Exception:
            series_for_range = series

        strategy = getattr(inf_cfg, "range_strategy", "iqr")
        if strategy == "span":
            rng = infer_numeric_range(
                series_for_range, margin_pct=inf_cfg.range_margin_pct
            )
        else:
            rng = infer_numeric_range_robust(
                series_for_range,
                strategy=strategy,
                iqr_k=getattr(inf_cfg, "iqr_k", 1.5),
                quantile_low=getattr(inf_cfg, "quantile_low", 0.005),
                quantile_high=getattr(inf_cfg, "quantile_high", 0.995),
                mad_k=getattr(inf_cfg, "mad_k", 3.0),
            )
        if rng:
            return (float(rng[0]), float(rng[1]))
        return None

    def _infer_length_and_pattern(
        self, series: pd.Series, inf_cfg: InferenceConfig
    ) -> dict[str, Any]:
        """
        Infer string length bounds and regex pattern (only if 100% coverage observed).
        Returns keys among: min_length, max_length, pattern.
        """
        out: dict[str, Any] = {}
        try:
            lb = infer_length_bounds(series, widen=None)
            if lb:
                out["min_length"], out["max_length"] = int(lb[0]), int(lb[1])
        except Exception:
            pass

        if getattr(inf_cfg, "regex_inference_enabled", False):
            try:
                pat = infer_regex_pattern(series)
                if pat:
                    out["pattern"] = pat
            except Exception:
                pass
        return out

    def _infer_date_or_datetime_bounds(
        self, series: pd.Series, inf_cfg: InferenceConfig, is_datetime: bool
    ) -> dict[str, Any]:
        """Infer date/datetime bounds and return appropriate keys for the meta-schema."""
        out: dict[str, Any] = {}
        try:
            db = infer_date_bounds(series, margin_days=inf_cfg.date_margin_days)
        except Exception:
            db = None
        if not db:
            return out
        if is_datetime:
            out["after_datetime"], out["before_datetime"] = db[0], db[1]
        else:
            out["after_date"], out["before_date"] = db[0], db[1]
        return out

    def _prepare_observed_stats(self, data: pd.DataFrame) -> dict[str, dict[str, Any]]:
        """
        Precompute observed per-field stats for training-pass relaxation.
        Provides min/max length and numeric min/max for widening rules.
        """
        observed_stats: dict[str, dict[str, Any]] = {}
        for col in data.columns:
            s = data[col].dropna()
            if s.empty:
                observed_stats[col] = {}
                continue
            try:
                lengths = s.astype(str).str.len()
            except Exception:
                lengths = pd.Series(dtype=int)
            observed_stats[col] = {
                "min_len": int(lengths.min()) if not lengths.empty else None,
                "max_len": int(lengths.max()) if not lengths.empty else None,
                "min_val": (
                    float(pd.to_numeric(s, errors="coerce").min())
                    if pd.to_numeric(s, errors="coerce").notna().any()
                    else None
                ),
                "max_val": (
                    float(pd.to_numeric(s, errors="coerce").max())
                    if pd.to_numeric(s, errors="coerce").notna().any()
                    else None
                ),
            }
        return observed_stats

    def _validate_value_against_rules(
        self, val: Any, field_req: dict[str, Any]
    ) -> str | None:
        """
        Validate a single value against field requirements in strict order.
        Returns the first failing rule key or None if all pass.
        """
        if not check_field_type(val, field_req):
            return "type"
        if "allowed_values" in field_req and val not in field_req["allowed_values"]:
            return "allowed_values"
        if (
            ("min_length" in field_req) or ("max_length" in field_req)
        ) and not check_length_bounds(val, field_req):
            return "length_bounds"
        if "pattern" in field_req and not check_field_pattern(val, field_req):
            return "pattern"
        if (
            ("min_value" in field_req) or ("max_value" in field_req)
        ) and not check_field_range(val, field_req):
            return "numeric_range"
        if any(
            k in field_req
            for k in ["after_date", "before_date", "after_datetime", "before_datetime"]
        ) and not check_date_bounds(val, field_req):
            return "date_bounds"
        return None

    def _relax_constraint_for_failure(
        self,
        col: str,
        failing_rule: str,
        field_req: dict[str, Any],
        observed: dict[str, Any],
        exp_root: dict[str, Any],
    ) -> None:
        """
        Relax only the failing rule and log adjustments for training-pass guarantee.
        Mutates field_req in-place.
        """
        if failing_rule == "type":
            if field_req.get("type") != "string":
                field_req["type"] = "string"
                for k in [
                    "min_value",
                    "max_value",
                    "after_date",
                    "before_date",
                    "after_datetime",
                    "before_datetime",
                ]:
                    field_req.pop(k, None)
                exp_root.setdefault(col, {}).setdefault("adjustments", []).append(
                    {
                        "rule": "type",
                        "action": "coerced_to_string",
                        "reason": "training-pass failure",
                    }
                )
        elif failing_rule == "allowed_values":
            if "allowed_values" in field_req:
                field_req.pop("allowed_values", None)
                exp_root.setdefault(col, {}).setdefault("adjustments", []).append(
                    {
                        "rule": "allowed_values",
                        "action": "removed",
                        "reason": "training-pass failure",
                    }
                )
        elif failing_rule == "length_bounds":
            stats = observed or {}
            if stats:
                min_len = stats.get("min_len")
                max_len = stats.get("max_len")
                before_min = field_req.get("min_length")
                before_max = field_req.get("max_length")
                if min_len is not None:
                    field_req["min_length"] = min(
                        int(field_req.get("min_length", min_len)), int(min_len)
                    )
                if max_len is not None:
                    field_req["max_length"] = max(
                        int(field_req.get("max_length", max_len)), int(max_len)
                    )
                exp_root.setdefault(col, {}).setdefault("adjustments", []).append(
                    {
                        "rule": "length_bounds",
                        "action": "widened",
                        "reason": "training-pass failure",
                        "before": {"min": before_min, "max": before_max},
                        "after": {
                            "min": field_req.get("min_length"),
                            "max": field_req.get("max_length"),
                        },
                    }
                )
            else:
                before_min = field_req.get("min_length")
                before_max = field_req.get("max_length")
                field_req.pop("min_length", None)
                field_req.pop("max_length", None)
                exp_root.setdefault(col, {}).setdefault("adjustments", []).append(
                    {
                        "rule": "length_bounds",
                        "action": "removed",
                        "reason": "insufficient stats",
                        "before": {"min": before_min, "max": before_max},
                    }
                )
        elif failing_rule == "pattern":
            if "pattern" in field_req:
                before = field_req.get("pattern")
                field_req.pop("pattern", None)
                exp_root.setdefault(col, {}).setdefault("adjustments", []).append(
                    {
                        "rule": "pattern",
                        "action": "removed",
                        "reason": "training-pass failure",
                        "before": before,
                    }
                )
        elif failing_rule == "numeric_range":
            stats = observed or {}
            min_val = stats.get("min_val")
            max_val = stats.get("max_val")
            before_min = field_req.get("min_value")
            before_max = field_req.get("max_value")
            if min_val is not None:
                field_req["min_value"] = min(
                    float(field_req.get("min_value", min_val)), float(min_val)
                )
            if max_val is not None:
                field_req["max_value"] = max(
                    float(field_req.get("max_value", max_val)), float(max_val)
                )
            exp_root.setdefault(col, {}).setdefault("adjustments", []).append(
                {
                    "rule": "numeric_range",
                    "action": "widened",
                    "reason": "training-pass failure",
                    "before": {"min": before_min, "max": before_max},
                    "after": {
                        "min": field_req.get("min_value"),
                        "max": field_req.get("max_value"),
                    },
                }
            )
        elif failing_rule == "date_bounds":
            before_after = field_req.get("after_date") or field_req.get(
                "after_datetime"
            )
            before_before = field_req.get("before_date") or field_req.get(
                "before_datetime"
            )
            for k in ["after_date", "before_date", "after_datetime", "before_datetime"]:
                field_req.pop(k, None)
            exp_root.setdefault(col, {}).setdefault("adjustments", []).append(
                {
                    "rule": "date_bounds",
                    "action": "removed",
                    "reason": "training-pass failure",
                    "before": {"after": before_after, "before": before_before},
                }
            )

    # --- Explanation helpers (kept 1:1 with existing explain payload semantics) ---
    def _explain_type(self, req: dict[str, Any]) -> Any:
        return str(req.get("type")) if "type" in req else None

    def _explain_nullable(
        self, series: pd.Series, req: dict[str, Any]
    ) -> dict[str, Any] | None:
        if "nullable" not in req:
            return None
        try:
            nulls = int(series.isnull().sum())
            total = int(len(series))
        except Exception:
            nulls, total = (0, 0)
        return {
            "active": bool(req["nullable"]),
            "reason": (
                "Required because 0% nulls observed in training"
                if not req["nullable"]
                else "Nulls were observed in training, so this field is allowed to be null"
            ),
            "stats": {"null_count": nulls, "total": total},
        }

    def _explain_allowed_values(
        self, series: pd.Series, req: dict[str, Any], inf_cfg: InferenceConfig
    ) -> dict[str, Any] | None:
        if "allowed_values" not in req:
            return None
        try:
            non_null = series.dropna()
            in_set = non_null.isin(req["allowed_values"])
            coverage = float(in_set.sum() / len(non_null)) if len(non_null) > 0 else 1.0
            uniq = int(non_null.nunique())
        except Exception:
            coverage, uniq = (None, None)
        return {
            "values": list(req.get("allowed_values", [])),
            "reason": (
                "High coverage stable set"
                if coverage is None or coverage >= inf_cfg.enum_min_coverage
                else "Coverage below threshold"
            ),
            "stats": {
                "coverage": coverage,
                "unique_count": uniq,
                "strategy": getattr(inf_cfg, "enum_strategy", "coverage"),
            },
        }

    def _explain_length(
        self, series: pd.Series, req: dict[str, Any]
    ) -> dict[str, Any] | None:
        if "min_length" not in req and "max_length" not in req:
            return None
        try:
            lengths = series.dropna().astype(str).str.len()
            obs_min = int(lengths.min()) if len(lengths) else None
            obs_max = int(lengths.max()) if len(lengths) else None
        except Exception:
            obs_min = obs_max = None
        return {
            "active_min": (
                int(req.get("min_length", 0))
                if req.get("min_length") is not None
                else None
            ),
            "active_max": (
                int(req.get("max_length", 0))
                if req.get("max_length") is not None
                else None
            ),
            "stats": {"observed_min": obs_min, "observed_max": obs_max},
        }

    def _explain_range(
        self, series: pd.Series, req: dict[str, Any], inf_cfg: InferenceConfig
    ) -> dict[str, Any] | None:
        if not (
            req.get("type") in ("integer", "float")
            and ("min_value" in req or "max_value" in req)
        ):
            return None
        strategy = getattr(inf_cfg, "range_strategy", "iqr")
        stats: dict[str, Any] = {}
        try:
            x = pd.to_numeric(series.dropna(), errors="coerce").dropna()
            if len(x):
                if strategy == "iqr":
                    q1 = float(x.quantile(0.25))
                    q3 = float(x.quantile(0.75))
                    stats.update(
                        {"q1": q1, "q3": q3, "iqr_k": getattr(inf_cfg, "iqr_k", 1.5)}
                    )
                elif strategy == "quantile":
                    stats.update(
                        {
                            "q_low": float(
                                x.quantile(getattr(inf_cfg, "quantile_low", 0.005))
                            ),
                            "q_high": float(
                                x.quantile(getattr(inf_cfg, "quantile_high", 0.995))
                            ),
                        }
                    )
                elif strategy == "mad":
                    med = float(x.median())
                    stats.update(
                        {"median": med, "mad_k": getattr(inf_cfg, "mad_k", 3.0)}
                    )
                stats.update(
                    {"observed_min": float(x.min()), "observed_max": float(x.max())}
                )
        except Exception:
            pass
        return {
            "strategy": strategy,
            "active_min": (
                float(req.get("min_value"))
                if req.get("min_value") is not None
                else None
            ),
            "active_max": (
                float(req.get("max_value"))
                if req.get("max_value") is not None
                else None
            ),
            "reason": (
                "Robust range (IQR/Quantile/MAD) clamped to training min/max for pass guarantee"
                if strategy != "span"
                else "Span-based range with margin"
            ),
            "stats": stats,
        }

    def _explain_date(
        self, series: pd.Series, req: dict[str, Any], inf_cfg: InferenceConfig
    ) -> dict[str, Any] | None:
        if not (
            req.get("type") in ("date", "datetime")
            and any(
                k in req
                for k in [
                    "after_date",
                    "before_date",
                    "after_datetime",
                    "before_datetime",
                ]
            )
        ):
            return None
        try:
            x = pd.to_datetime(series.dropna(), errors="coerce")
            obs_min = (
                x.min().date().isoformat() if len(x) and pd.notna(x.min()) else None
            )
            obs_max = (
                x.max().date().isoformat() if len(x) and pd.notna(x.max()) else None
            )
        except Exception:
            obs_min = obs_max = None
        return {
            "active_after": req.get("after_date") or req.get("after_datetime"),
            "active_before": req.get("before_date") or req.get("before_datetime"),
            "reason": "Plausible date window widened by margin days",
            "stats": {
                "observed_min": obs_min,
                "observed_max": obs_max,
                "margin_days": getattr(inf_cfg, "date_margin_days", 3),
            },
        }

    def _explain_pattern(
        self, series: pd.Series, req: dict[str, Any]
    ) -> dict[str, Any] | None:
        if "pattern" not in req:
            return None
        try:
            non_null = series.dropna().astype(str)
            import re as _re

            patt = _re.compile(req["pattern"])
            coverage = (
                float(non_null.apply(lambda v: bool(patt.match(v))).mean())
                if len(non_null)
                else 1.0
            )
        except Exception:
            coverage = None
        return {
            "regex": req["pattern"],
            "reason": (
                "100% coverage on training non-nulls"
                if coverage is None or coverage == 1.0
                else "Less than full coverage"
            ),
            "stats": {"coverage": coverage},
        }

    # ============ Enriched field requirement generation with inference ============
    def _build_field_requirement(
        self,
        field_profile: dict[str, Any],
        series: pd.Series,
        inf_cfg: InferenceConfig,
        pk_fields: list | None = None,
    ) -> dict[str, Any]:
        """Construct comprehensive field requirement using inference utilities."""
        req: dict[str, Any] = {}

        # 1) Type and nullability (strict behavior parity)
        tn = self._infer_type_and_nullability(field_profile, series, inf_cfg)
        req.update(tn)
        col_name = getattr(series, "name", None)

        # 2) Enums (allowed_values) only for string/integer, suppress for PK/id-like
        if req.get("type") in ("string", "integer"):
            enum_vals = self._infer_allowed_values(series, inf_cfg, col_name, pk_fields)
            if enum_vals is not None:
                req["allowed_values"] = enum_vals

        # 3) Type-specific enrichment
        t = req.get("type")
        if t in ("integer", "float"):
            # Decide if we should treat as numeric via coercion (as in original logic)
            treat_as_numeric = False
            try:
                non_null = series.dropna()
                if len(non_null) > 0:
                    coerced = pd.to_numeric(non_null, errors="coerce")
                    if coerced.notna().all():
                        treat_as_numeric = True
            except Exception:
                treat_as_numeric = False

            bounds = self._infer_numeric_bounds(series, inf_cfg, treat_as_numeric)
            if bounds:
                req["min_value"], req["max_value"] = bounds[0], bounds[1]

        elif t == "string":
            req.update(self._infer_length_and_pattern(series, inf_cfg))

        elif t == "date":
            req.update(
                self._infer_date_or_datetime_bounds(series, inf_cfg, is_datetime=False)
            )

        elif t == "datetime":
            req.update(
                self._infer_date_or_datetime_bounds(series, inf_cfg, is_datetime=True)
            )

        return req

    def _generate_enriched_field_requirements(
        self,
        data: pd.DataFrame,
        data_profile: dict[str, Any],
        inf_cfg: InferenceConfig,
        pk_fields: list | None = None,
    ) -> dict[str, Any]:
        field_reqs: dict[str, Any] = {}
        prof_fields = data_profile.get("fields", {}) or {}
        for col in data.columns:
            fp = prof_fields.get(col, {"dtype": str(data[col].dtype)})
            # Ensure name for downstream logic
            fp.setdefault("name", col)
            field_reqs[col] = self._build_field_requirement(
                fp, data[col], inf_cfg, pk_fields=pk_fields
            )
        return field_reqs

    def _enforce_training_pass(
        self, data: pd.DataFrame, standard: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Training-pass guarantee:
        - Validate each field value against its rules in strict order
        - On failures, relax only the failing rule(s) and re-validate
        - Returns adjusted standard that the training data passes
        """
        reqs = standard.get("requirements", {}).get("field_requirements", {})
        if not isinstance(reqs, dict):
            return standard

        # Prepare explanations sink for adjustments
        meta = standard.setdefault("metadata", {})
        exp_root = meta.setdefault("explanations", {})

        # Precompute observed per-field stats for relaxation
        observed_stats = self._prepare_observed_stats(data)

        # Iterate until stable or 2 passes for safety
        for _ in range(2):
            any_changes = False
            for col in data.columns:
                if col not in reqs:
                    continue
                field_req = reqs[col]
                # Ensure nullable aligns with data if required
                if not field_req.get("nullable", True) and data[col].isnull().any():
                    field_req["nullable"] = True
                    any_changes = True

                # Validate non-null values and capture first failing rule type
                for val in data[col].dropna():
                    failing_rule = self._validate_value_against_rules(val, field_req)
                    if failing_rule:
                        self._relax_constraint_for_failure(
                            col,
                            failing_rule,
                            field_req,
                            observed_stats.get(col, {}),
                            exp_root,
                        )
                        any_changes = True
                        # After relaxation, continue to next value
                        continue

                # write back
                reqs[col] = field_req

            if not any_changes:
                break

        return standard

    def _generate_dimension_requirements(
        self, thresholds: dict[str, Any]
    ) -> dict[str, Any]:
        """Generate dimension requirements from thresholds with explicit scoring policy."""
        return {
            "validity": {
                "minimum_score": thresholds.get("validity_min", 15.0),
                "weight": 1.0,
                "scoring": {
                    "rule_weights": {
                        "type": 0.30,
                        "allowed_values": 0.20,
                        "pattern": 0.20,
                        "length_bounds": 0.10,
                        "numeric_bounds": 0.20,
                        # date_bounds typically contributes to validity for date/datetime fields
                        # If you want it to contribute, add it here and in the engine:
                        # "date_bounds": 0.10
                    },
                    "field_overrides": {},
                },
            },
            "completeness": {
                "minimum_score": thresholds.get("completeness_min", 15.0),
                "weight": 1.0,
                "scoring": {
                    "rule_weights": {"missing_required": 1.0},
                    "field_overrides": {},
                },
            },
            "consistency": {
                "minimum_score": thresholds.get("consistency_min", 12.0),
                "weight": 1.0,
                "scoring": {
                    "rule_weights": {
                        "primary_key_uniqueness": 1.0,
                        # "referential_integrity": 0.0  # placeholder for future
                    },
                    "field_overrides": {},
                },
            },
            "freshness": {
                "minimum_score": thresholds.get("freshness_min", 15.0),
                "weight": 1.0,
                "scoring": {
                    "rule_weights": {
                        "recency_window": 0.0  # inactive by default; generator may enable when safe
                    },
                    "field_overrides": {},
                },
            },
            "plausibility": {
                "minimum_score": thresholds.get("plausibility_min", 12.0),
                "weight": 1.0,
                "scoring": {
                    "rule_weights": {
                        # Active by default with distinct rule types from Validity
                        "statistical_outliers": 0.4,  # IQR/MAD-based outlier detection (different from validity bounds)
                        "categorical_frequency": 0.3,  # Flag rare categories (different from validity allowed_values)
                        "business_logic": 0.2,  # Domain-specific business rules
                        "cross_field_consistency": 0.1,  # Relationships between fields
                    },
                    "field_overrides": {},
                },
            },
        }

    def _build_explanations(
        self,
        data: pd.DataFrame,
        data_profile: dict[str, Any],
        inf_cfg: InferenceConfig,
        field_requirements: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Build human-readable explanations per field/rule for the generated standard.
        Explanations are stored under metadata.explanations and do not affect validation.
        """
        explanations: dict[str, Any] = {}
        for col, req in field_requirements.items():
            s = data[col] if col in data.columns else pd.Series([], dtype=object)
            col_exp: dict[str, Any] = {}

            t = self._explain_type(req)
            if t is not None:
                col_exp["type"] = t

            n = self._explain_nullable(s, req)
            if n is not None:
                col_exp["nullable"] = n

            av = self._explain_allowed_values(s, req, inf_cfg)
            if av is not None:
                col_exp["allowed_values"] = av

            lb = self._explain_length(s, req)
            if lb is not None:
                col_exp["length_bounds"] = lb

            rng = self._explain_range(s, req, inf_cfg)
            if rng is not None:
                col_exp["range"] = rng

            db = self._explain_date(s, req, inf_cfg)
            if db is not None:
                col_exp["date_bounds"] = db

            patt = self._explain_pattern(s, req)
            if patt is not None:
                col_exp["pattern"] = patt

            if col_exp:
                explanations[col] = col_exp

        return explanations

    def _sanitize_dataframe(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Coerce unhashable/object-like column values (e.g., dict/list/set) to JSON strings to avoid
        hashing errors during inference and PK detection.
        """
        df = data.copy()
        for col in df.columns:
            s = df[col]
            if s.dtype == object:
                try:
                    sample = s.dropna().head(50)
                    if sample.apply(lambda v: isinstance(v, (dict, list, set))).any():

                        def _coerce(v):
                            if isinstance(v, (dict, list)):
                                try:
                                    return json.dumps(v, sort_keys=True)
                                except Exception:
                                    return str(v)
                            if isinstance(v, set):
                                try:
                                    return ",".join(sorted(map(str, v)))
                                except Exception:
                                    return str(v)
                            return (
                                v
                                if v is None or isinstance(v, (str, int, float, bool))
                                else str(v)
                            )

                        df[col] = s.apply(_coerce)
                except Exception:
                    # As a last resort, stringify entire column
                    try:
                        df[col] = s.astype(str)
                    except Exception:
                        pass
        return df

    def generate(
        self,
        data: pd.DataFrame,
        data_name: str,
        generation_config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Generate ADRI standard from DataFrame using modern modular architecture.

        This is the single, unified method for standard generation using:
        - ContractBuilder for structure
        - FieldInferenceEngine for field analysis
        - Training-pass guarantee for data compatibility
        - ExplanationGenerator for human-readable metadata

        Args:
            data: DataFrame to analyze
            data_name: Name for the generated standard
            generation_config: Optional configuration for generation thresholds

        Returns:
            Complete ADRI standard dictionary in normalized format:
            {
                'standards': {...},      # Metadata
                'requirements': {...}    # Field + dimension requirements
            }
        """
        # Sanitize data to handle complex object types
        data = self.standard_builder.sanitize_dataframe(data)

        # Profile the data
        data_profile = self.profiler.profile_data(data)

        # Build the standard using modular components
        standard = self.standard_builder.build_standard(
            data, data_name, data_profile, generation_config
        )

        # Apply consistent naming logic (override any naming from modular components)
        if "contracts" in standard and "name" in standard["contracts"]:
            standard["contracts"]["name"] = self._generate_standard_name(data_name)

        # Apply authority override if available through modular path
        if hasattr(self, "_current_authority_override"):
            if "contracts" in standard:
                standard["contracts"]["authority"] = self._current_authority_override
            delattr(self, "_current_authority_override")

        # Enforce training-pass guarantee
        standard = self.standard_builder.enforce_training_pass_guarantee(data, standard)

        # Configure freshness detection
        standard = self.standard_builder.detect_and_configure_freshness(data, standard)

        # Add explanations
        config = generation_config or {}
        inference_config = InferenceConfig(**(config.get("inference", {}) or {}))
        standard = self.explanation_generator.add_explanations_to_standard(
            standard, data, data_profile, inference_config
        )

        # Add plausibility templates
        standard = self.standard_builder.add_plausibility_templates(standard)

        # Clean numpy types for YAML compatibility
        standard = self._clean_numpy_types(standard)

        return standard

    def _clean_numpy_types(self, obj: Any) -> Any:
        """Convert numpy types to native Python for YAML compatibility.

        Recursively traverses the contract dictionary and converts all numpy
        scalar types (numpy.integer, numpy.floating, numpy.ndarray) to their
        Python equivalents. This ensures YAML serialization works without
        requiring custom constructors.

        Args:
            obj: Object to clean (dict, list, or scalar value)

        Returns:
            Cleaned object with all numpy types converted to Python types
        """
        import numpy as np

        if isinstance(obj, dict):
            return {k: self._clean_numpy_types(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._clean_numpy_types(item) for item in obj]
        elif isinstance(obj, (np.integer, np.floating)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif hasattr(obj, "item"):  # numpy scalar with .item() method
            return obj.item()
        else:
            return obj


# Convenience function
def generate_contract_from_data(
    data: pd.DataFrame, data_name: str, generation_config: dict[str, Any] | None = None
) -> dict[str, Any]:
    """
    Generate an ADRI standard from DataFrame using default generator.

    Args:
        data: DataFrame to analyze
        data_name: Name for the generated standard
        generation_config: Configuration for generation

    Returns:
        Complete ADRI standard dictionary
    """
    generator = ContractGenerator()
    return generator.generate(data, data_name, generation_config)


# @ADRI_FEATURE_END[analysis_contract_generator]
