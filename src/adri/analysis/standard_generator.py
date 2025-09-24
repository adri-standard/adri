"""
ADRI Standard Generator.

Automatic YAML standard generation from data analysis.
Migrated and updated for the new src/ layout architecture.
"""

import json
from typing import Any, Dict, Optional

import pandas as pd

# For training-pass self-validation
from ..validator.rules import (
    check_allowed_values,
    check_date_bounds,
    check_field_pattern,
    check_field_range,
    check_field_type,
    check_length_bounds,
)
from .data_profiler import DataProfiler
from .rule_inference import (
    detect_primary_key,
    infer_allowed_values,
    infer_allowed_values_tolerant,
    infer_date_bounds,
    infer_length_bounds,
    infer_numeric_range,
    infer_numeric_range_robust,
    infer_regex_pattern,
    InferenceConfig,
)


class StandardGenerator:
    """
    Generates ADRI-compliant YAML standards from data analysis.

    This component creates validation rules based on data patterns,
    enabling automatic standard creation for any dataset.
    """

    def __init__(self):
        """Initialize the standard generator."""
        self.profiler = DataProfiler()

    def generate_standard(
        self,
        data_profile: Dict[str, Any],
        data_name: str,
        generation_config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generate a complete ADRI standard from a data profile.

        Args:
            data_profile: Data profile from DataProfiler
            data_name: Name for the generated standard
            generation_config: Configuration for generation thresholds

        Returns:
            Complete ADRI standard dictionary
        """
        config = generation_config or {}
        thresholds = config.get("default_thresholds", {})

        # Generate standard metadata
        standard_metadata = {
            "id": f"{data_name}_standard",
            "name": f"{data_name.replace('_', ' ').title()} ADRI Standard",
            "version": "1.0.0",
            "authority": "ADRI Framework",
            "description": f"Auto-generated standard for {data_name} data",
            "effective_date": "2024-01-01T00:00:00Z",
        }

        # Generate requirements
        requirements = self._generate_requirements(data_profile, thresholds)

        # Build complete standard
        standard = {"standards": standard_metadata, "requirements": requirements}

        return standard

    def _generate_requirements(
        self, data_profile: Dict[str, Any], thresholds: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate requirements section from data profile."""
        requirements = {
            "overall_minimum": thresholds.get("overall_minimum", 75.0),
            "field_requirements": self._generate_field_requirements(data_profile),
            "dimension_requirements": self._generate_dimension_requirements(thresholds),
        }

        return requirements

    def _generate_field_requirements(
        self, data_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate field requirements from profiled fields."""
        field_requirements = {}
        fields = data_profile.get("fields", {})

        for field_name, field_profile in fields.items():
            field_req = self._generate_single_field_requirement(field_profile)
            field_requirements[field_name] = field_req

        return field_requirements

    def _generate_single_field_requirement(
        self, field_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate requirements for a single field."""
        requirement = {}

        # Determine data type
        dtype = field_profile.get("dtype", "object")
        if "int" in dtype:
            requirement["type"] = "integer"
        elif "float" in dtype:
            requirement["type"] = "float"
        elif "bool" in dtype:
            requirement["type"] = "boolean"
        elif "datetime" in dtype:
            requirement["type"] = "datetime"
        else:
            requirement["type"] = "string"

        # Determine nullable status
        null_percentage = field_profile.get("null_percentage", 0)
        requirement["nullable"] = null_percentage > 5  # Allow nulls if >5% are null

        # Add constraints based on data patterns
        if requirement["type"] in ["integer", "float"]:
            if "min_value" in field_profile and "max_value" in field_profile:
                # Ensure native Python types for YAML serialization
                requirement["min_value"] = float(field_profile["min_value"])
                requirement["max_value"] = float(field_profile["max_value"])

        elif requirement["type"] == "string":
            patterns = field_profile.get("common_patterns", [])
            if "email" in patterns:
                requirement["pattern"] = r"^[^@]+@[^@]+\.[^@]+$"
            elif "phone" in patterns:
                requirement["pattern"] = r"^[\+]?[0-9\s\-\(\)]+$"
            elif "date" in patterns:
                requirement["pattern"] = r"^\d{4}-\d{2}-\d{2}"

            # Add length constraints (emit both min_length and max_length when available)
            if "min_length" in field_profile:
                try:
                    requirement["min_length"] = int(field_profile["min_length"])
                except Exception:
                    pass
            if "max_length" in field_profile:
                max_len = field_profile["max_length"]
                try:
                    max_len_val = int(float(max_len))
                except Exception:
                    max_len_val = None
                if (
                    max_len_val is not None and max_len_val < 1000
                ):  # Only add if reasonable
                    # Keep the existing 20% buffer while ensuring it's >= min_length if present
                    widened = int(float(max_len) * 1.2)
                    if (
                        "min_length" in requirement
                        and widened < requirement["min_length"]
                    ):
                        widened = requirement["min_length"]
                    requirement["max_length"] = widened

        return requirement

    # ============ Enriched field requirement generation with inference ============
    def _build_field_requirement(
        self,
        field_profile: Dict[str, Any],
        series: pd.Series,
        inf_cfg: InferenceConfig,
        pk_fields: Optional[list] = None,
    ) -> Dict[str, Any]:
        """Construct comprehensive field requirement using inference utilities."""
        req: Dict[str, Any] = {}
        dtype = field_profile.get("dtype", "object")
        col_name = getattr(series, "name", None)

        def _is_id_like(name: Optional[str]) -> bool:
            if not name:
                return False
            lname = str(name).lower()
            for tok in ["id", "key", "code", "number", "num", "uuid", "guid"]:
                if tok in lname:
                    return True
            return False

        # Attempt numeric coercion for object columns
        treat_as_numeric = False
        numeric_series = None
        try:
            non_null = series.dropna()
            if len(non_null) > 0:
                coerced = pd.to_numeric(non_null, errors="coerce")
                if coerced.notna().all():
                    treat_as_numeric = True
                    numeric_series = coerced
        except Exception:
            treat_as_numeric = False

        # Type mapping (favor date when strongly indicated, else numeric coercion)
        common_patterns = field_profile.get("common_patterns", []) or []
        if "int" in dtype and not treat_as_numeric:
            req["type"] = "integer"
        elif ("float" in dtype or treat_as_numeric) and ("bool" not in dtype):
            req["type"] = "float"
        elif "bool" in dtype:
            req["type"] = "boolean"
        elif "datetime" in dtype:
            req["type"] = "datetime"
        elif "date" in common_patterns:
            req["type"] = "date"
        else:
            req["type"] = "string"

        # Nullability: false only when absolutely no nulls
        null_count = int(field_profile.get("null_count", 0) or 0)
        req["nullable"] = not (null_count == 0)

        # Enums / allowed_values (strings and integers only to satisfy meta-schema)
        if req["type"] in ("string", "integer"):
            # Suppress enums for identified PK columns and id-like names
            suppress_enum = False
            if pk_fields and col_name in pk_fields:
                suppress_enum = True
            if _is_id_like(col_name):
                suppress_enum = True

            if not suppress_enum:
                if getattr(inf_cfg, "enum_strategy", "coverage") == "tolerant":
                    enum_vals = infer_allowed_values_tolerant(
                        series,
                        min_coverage=inf_cfg.enum_min_coverage,
                        top_k=getattr(inf_cfg, "enum_top_k", 10),
                        max_unique=inf_cfg.enum_max_unique,
                    )
                else:
                    enum_vals = infer_allowed_values(
                        series,
                        max_unique=inf_cfg.enum_max_unique,
                        min_coverage=inf_cfg.enum_min_coverage,
                    )
                if enum_vals is not None:
                    req["allowed_values"] = enum_vals

        # Type-specific enrichment
        if req["type"] in ("integer", "float"):
            # Choose range inference strategy (default: robust iqr)
            strategy = getattr(inf_cfg, "range_strategy", "iqr")
            series_for_range = numeric_series if numeric_series is not None else series
            rng = None
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
                req["min_value"], req["max_value"] = float(rng[0]), float(rng[1])

        elif req["type"] == "string":
            # Length bounds - guarantee min and max
            lb = infer_length_bounds(series, widen=None)
            if lb:
                req["min_length"], req["max_length"] = int(lb[0]), int(lb[1])

            # Regex pattern only if 100% coverage
            if inf_cfg.regex_inference_enabled:
                pat = infer_regex_pattern(series)
                if pat:
                    req["pattern"] = pat

        elif req["type"] == "date":
            db = infer_date_bounds(series, margin_days=inf_cfg.date_margin_days)
            if db:
                req["after_date"], req["before_date"] = db[0], db[1]

        elif req["type"] == "datetime":
            db = infer_date_bounds(series, margin_days=inf_cfg.date_margin_days)
            if db:
                # use datetime keys for completeness of meta-schema
                req["after_datetime"], req["before_datetime"] = db[0], db[1]

        return req

    def _generate_enriched_field_requirements(
        self,
        data: pd.DataFrame,
        data_profile: Dict[str, Any],
        inf_cfg: InferenceConfig,
        pk_fields: Optional[list] = None,
    ) -> Dict[str, Any]:
        field_reqs: Dict[str, Any] = {}
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
        self, data: pd.DataFrame, standard: Dict[str, Any]
    ) -> Dict[str, Any]:
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
        observed_stats: Dict[str, Dict[str, Any]] = {}
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
                    # 1) type
                    if not check_field_type(val, field_req):
                        # Relax type to string; drop numeric/date constraints
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
                                if k in field_req:
                                    field_req.pop(k, None)
                            # Log adjustment
                            adj = exp_root.setdefault(col, {}).setdefault(
                                "adjustments", []
                            )
                            adj.append(
                                {
                                    "rule": "type",
                                    "action": "coerced_to_string",
                                    "reason": "training-pass failure",
                                }
                            )
                            any_changes = True
                        # Re-check from next value after relaxation
                        continue

                    # 2) allowed_values
                    if not check_allowed_values(val, field_req):
                        if "allowed_values" in field_req:
                            field_req.pop("allowed_values", None)
                            adj = exp_root.setdefault(col, {}).setdefault(
                                "adjustments", []
                            )
                            adj.append(
                                {
                                    "rule": "allowed_values",
                                    "action": "removed",
                                    "reason": "training-pass failure",
                                }
                            )
                            any_changes = True
                        continue

                    # 3) length bounds
                    if not check_length_bounds(val, field_req):
                        stats = observed_stats.get(col, {})
                        if stats:
                            min_len = stats.get("min_len")
                            max_len = stats.get("max_len")
                            before_min = field_req.get("min_length")
                            before_max = field_req.get("max_length")
                            if min_len is not None:
                                field_req["min_length"] = min(
                                    int(field_req.get("min_length", min_len)),
                                    int(min_len),
                                )
                            if max_len is not None:
                                field_req["max_length"] = max(
                                    int(field_req.get("max_length", max_len)),
                                    int(max_len),
                                )
                            adj = exp_root.setdefault(col, {}).setdefault(
                                "adjustments", []
                            )
                            adj.append(
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
                            any_changes = True
                        else:
                            # Drop if cannot compute
                            before_min = field_req.get("min_length")
                            before_max = field_req.get("max_length")
                            field_req.pop("min_length", None)
                            field_req.pop("max_length", None)
                            adj = exp_root.setdefault(col, {}).setdefault(
                                "adjustments", []
                            )
                            adj.append(
                                {
                                    "rule": "length_bounds",
                                    "action": "removed",
                                    "reason": "insufficient stats",
                                    "before": {"min": before_min, "max": before_max},
                                }
                            )
                            any_changes = True
                        continue

                    # 4) pattern
                    if not check_field_pattern(val, field_req):
                        if "pattern" in field_req:
                            before = field_req.get("pattern")
                            field_req.pop("pattern", None)
                            adj = exp_root.setdefault(col, {}).setdefault(
                                "adjustments", []
                            )
                            adj.append(
                                {
                                    "rule": "pattern",
                                    "action": "removed",
                                    "reason": "training-pass failure",
                                    "before": before,
                                }
                            )
                            any_changes = True
                        continue

                    # 5) numeric range
                    if not check_field_range(val, field_req):
                        stats = observed_stats.get(col, {})
                        min_val = stats.get("min_val")
                        max_val = stats.get("max_val")
                        before_min = field_req.get("min_value")
                        before_max = field_req.get("max_value")
                        if min_val is not None:
                            field_req["min_value"] = min(
                                float(field_req.get("min_value", min_val)),
                                float(min_val),
                            )
                        if max_val is not None:
                            field_req["max_value"] = max(
                                float(field_req.get("max_value", max_val)),
                                float(max_val),
                            )
                        adj = exp_root.setdefault(col, {}).setdefault("adjustments", [])
                        adj.append(
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
                        any_changes = True
                        continue

                    # 6) date/datetime bounds
                    if not check_date_bounds(val, field_req):
                        # Drop date bounds if too restrictive
                        before_after = field_req.get("after_date") or field_req.get(
                            "after_datetime"
                        )
                        before_before = field_req.get("before_date") or field_req.get(
                            "before_datetime"
                        )
                        for k in [
                            "after_date",
                            "before_date",
                            "after_datetime",
                            "before_datetime",
                        ]:
                            if k in field_req:
                                field_req.pop(k, None)
                        adj = exp_root.setdefault(col, {}).setdefault("adjustments", [])
                        adj.append(
                            {
                                "rule": "date_bounds",
                                "action": "removed",
                                "reason": "training-pass failure",
                                "before": {
                                    "after": before_after,
                                    "before": before_before,
                                },
                            }
                        )
                        any_changes = True
                        continue

                # write back
                reqs[col] = field_req

            if not any_changes:
                break

        return standard

    def _generate_dimension_requirements(
        self, thresholds: Dict[str, Any]
    ) -> Dict[str, Any]:
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
                        # "recency_window": 1.0  # enable when you add explicit recency rules
                    },
                    "field_overrides": {},
                },
            },
            "plausibility": {
                "minimum_score": thresholds.get("plausibility_min", 12.0),
                "weight": 1.0,
                "scoring": {
                    "rule_weights": {
                        # If you want plausibility to reflect realism separate from validity,
                        # you can route a portion of bounds/enums here:
                        # "numeric_bounds": 0.6,
                        # "allowed_values": 0.4,
                    },
                    "field_overrides": {},
                },
            },
        }

    def _build_explanations(
        self,
        data: pd.DataFrame,
        data_profile: Dict[str, Any],
        inf_cfg: InferenceConfig,
        field_requirements: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Build human-readable explanations per field/rule for the generated standard.
        Explanations are stored under metadata.explanations and do not affect validation.
        """
        explanations: Dict[str, Any] = {}
        for col, req in field_requirements.items():
            col_exp: Dict[str, Any] = {}
            s = data[col] if col in data.columns else pd.Series([], dtype=object)
            # Type
            if "type" in req:
                col_exp["type"] = str(req["type"])
            # Nullability
            if "nullable" in req:
                try:
                    nulls = int(s.isnull().sum())
                    total = int(len(s))
                except Exception:
                    nulls, total = (0, 0)
                col_exp["nullable"] = {
                    "active": bool(req["nullable"]),
                    "reason": (
                        "Required because 0% nulls observed in training"
                        if not req["nullable"]
                        else "Nulls were observed in training, so this field is allowed to be null"
                    ),
                    "stats": {"null_count": nulls, "total": total},
                }
            # Enums
            if "allowed_values" in req:
                try:
                    non_null = s.dropna()
                    in_set = non_null.isin(req["allowed_values"])
                    coverage = (
                        float((in_set.sum() / len(non_null)))
                        if len(non_null) > 0
                        else 1.0
                    )
                    uniq = int(non_null.nunique())
                except Exception:
                    coverage, uniq = (None, None)
                col_exp["allowed_values"] = {
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
            # Length bounds
            if "min_length" in req or "max_length" in req:
                try:
                    lengths = s.dropna().astype(str).str.len()
                    obs_min = int(lengths.min()) if len(lengths) else None
                    obs_max = int(lengths.max()) if len(lengths) else None
                except Exception:
                    obs_min = obs_max = None
                col_exp["length_bounds"] = {
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
            # Numeric ranges
            if req.get("type") in ("integer", "float") and (
                "min_value" in req or "max_value" in req
            ):
                strategy = getattr(inf_cfg, "range_strategy", "iqr")
                stats: Dict[str, Any] = {}
                try:
                    x = pd.to_numeric(s.dropna(), errors="coerce").dropna()
                    if len(x):
                        if strategy == "iqr":
                            q1 = float(x.quantile(0.25))
                            q3 = float(x.quantile(0.75))
                            stats.update(
                                {
                                    "q1": q1,
                                    "q3": q3,
                                    "iqr_k": getattr(inf_cfg, "iqr_k", 1.5),
                                }
                            )
                        elif strategy == "quantile":
                            stats.update(
                                {
                                    "q_low": float(
                                        x.quantile(
                                            getattr(inf_cfg, "quantile_low", 0.005)
                                        )
                                    ),
                                    "q_high": float(
                                        x.quantile(
                                            getattr(inf_cfg, "quantile_high", 0.995)
                                        )
                                    ),
                                }
                            )
                        elif strategy == "mad":
                            med = float(x.median())
                            stats.update(
                                {"median": med, "mad_k": getattr(inf_cfg, "mad_k", 3.0)}
                            )
                        stats.update(
                            {
                                "observed_min": float(x.min()),
                                "observed_max": float(x.max()),
                            }
                        )
                except Exception:
                    pass
                col_exp["range"] = {
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
            # Date bounds
            if req.get("type") in ("date", "datetime") and (
                "after_date" in req
                or "before_date" in req
                or "after_datetime" in req
                or "before_datetime" in req
            ):
                try:
                    x = pd.to_datetime(s.dropna(), errors="coerce")
                    obs_min = (
                        x.min().date().isoformat()
                        if len(x) and pd.notna(x.min())
                        else None
                    )
                    obs_max = (
                        x.max().date().isoformat()
                        if len(x) and pd.notna(x.max())
                        else None
                    )
                except Exception:
                    obs_min = obs_max = None
                col_exp["date_bounds"] = {
                    "active_after": req.get("after_date") or req.get("after_datetime"),
                    "active_before": req.get("before_date")
                    or req.get("before_datetime"),
                    "reason": "Plausible date window widened by margin days",
                    "stats": {
                        "observed_min": obs_min,
                        "observed_max": obs_max,
                        "margin_days": getattr(inf_cfg, "date_margin_days", 3),
                    },
                }
            # Pattern
            if "pattern" in req:
                try:
                    non_null = s.dropna().astype(str)
                    import re as _re

                    patt = _re.compile(req["pattern"])
                    coverage = (
                        float(non_null.apply(lambda v: bool(patt.match(v))).mean())
                        if len(non_null)
                        else 1.0
                    )
                except Exception:
                    coverage = None
                col_exp["pattern"] = {
                    "regex": req["pattern"],
                    "reason": (
                        "100% coverage on training non-nulls"
                        if coverage is None or coverage == 1.0
                        else "Less than full coverage"
                    ),
                    "stats": {"coverage": coverage},
                }
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

    def generate_from_dataframe(
        self,
        data: pd.DataFrame,
        data_name: str,
        generation_config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generate enriched standard directly from a DataFrame with training-pass guarantee.

        Args:
            data: DataFrame to analyze
            data_name: Name for the generated standard
            generation_config: Configuration for generation. Accepts:
                - default_thresholds: dict with dimension minimums
                - inference: dict that maps to InferenceConfig

        Returns:
            Complete ADRI standard dictionary (not yet including lineage/metadata)
        """
        # Sanitize object-like columns (dict/list/set) to strings to prevent hashing errors
        data = self._sanitize_dataframe(data)

        # Profile the data first
        data_profile = self.profiler.profile_data(data)

        # Extract thresholds and inference config
        config = generation_config or {}
        thresholds = config.get("default_thresholds", {})
        inf_cfg = InferenceConfig(**(config.get("inference", {}) or {}))

        # Build standards metadata
        standards_meta = {
            "id": f"{data_name}_standard",
            "name": f"{data_name.replace('_', ' ').title()} ADRI Standard",
            "version": "1.0.0",
            "authority": "ADRI Framework",
            "description": f"Auto-generated standard for {data_name} data",
        }

        # Record identification first (so we can suppress enums for PK)
        pk_fields = detect_primary_key(data, max_combo=inf_cfg.max_pk_combo_size)
        if not pk_fields and len(data.columns) > 0:
            pk_fields = [data.columns[0]]

        field_requirements = self._generate_enriched_field_requirements(
            data, data_profile, inf_cfg, pk_fields=pk_fields
        )

        requirements = {
            "overall_minimum": thresholds.get("overall_minimum", 75.0),
            "field_requirements": field_requirements,
            "dimension_requirements": self._generate_dimension_requirements(thresholds),
        }

        record_identification = {
            "primary_key_fields": pk_fields,
            "strategy": "primary_key_with_fallback",
        }

        # Build explanations for active rules
        explanations = self._build_explanations(
            data, data_profile, inf_cfg, field_requirements
        )

        # Build glossary and note for explanations
        explanations_glossary = {
            "iqr": "Interquartile Range (Q3 - Q1): a robust measure of spread, less sensitive to outliers.",
            "q1": "25th percentile of the training values.",
            "q3": "75th percentile of the training values.",
            "coverage": "Share of non-null training values that satisfy the rule.",
            "unique_count": "Number of distinct non-null values observed in training.",
        }
        explanations_note = "Explanations are for human review; only requirements.field_requirements are enforced."

        standard = {
            "standards": standards_meta,
            "record_identification": record_identification,
            "requirements": requirements,
            "metadata": {
                "explanations_note": explanations_note,
                "explanations_glossary": explanations_glossary,
                "explanations": explanations,
            },
        }

        # Enforce training-pass guarantee by self-validation and rule relaxation (log adjustments)
        standard = self._enforce_training_pass(data, standard)

        return standard


# Convenience function
def generate_standard_from_data(
    data: pd.DataFrame,
    data_name: str,
    generation_config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Generate an ADRI standard from DataFrame using default generator.

    Args:
        data: DataFrame to analyze
        data_name: Name for the generated standard
        generation_config: Configuration for generation

    Returns:
        Complete ADRI standard dictionary
    """
    generator = StandardGenerator()
    return generator.generate_from_dataframe(data, data_name, generation_config)
