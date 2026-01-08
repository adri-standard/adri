"""Scoring command implementation for ADRI CLI.

This module contains the ScoringExplainCommand class that handles scoring
breakdown and explanation operations.
"""

import json
from typing import Any

import click
import pandas as pd

from ...core.protocols import Command
from ...utils.path_utils import (
    get_project_root_display,
    rel_to_project_root,
    resolve_project_path,
)
from ...validator.engine import DataQualityAssessor
from ...validator.loaders import load_data, load_contract


class ScoringExplainCommand(Command):
    """Command for explaining scoring breakdown for datasets.

    Handles detailed scoring analysis showing dimension contributions,
    rule-level breakdowns, and weight applications.
    """

    def get_description(self) -> str:
        """Get command description."""
        return "Explain scoring breakdown for a dataset against a standard"

    def execute(self, args: dict[str, Any]) -> int:
        """Execute the scoring-explain command.

        Args:
            args: Command arguments containing:
                - data_path: str - Path to data file
                - standard_path: str - Path to YAML standard file
                - json_output: bool - Output machine-readable breakdown JSON

        Returns:
            Exit code (0 for success, non-zero for error)
        """
        data_path = args["data_path"]
        standard_path = args["standard_path"]
        json_output = args.get("json_output", False)

        return self._scoring_explain(data_path, standard_path, json_output)

    def _scoring_explain(
        self, data_path: str, standard_path: str, json_output: bool = False
    ) -> int:
        """Produce a scoring breakdown using the standard's configured weights."""
        try:
            # Resolve and validate paths
            resolved_data_path = resolve_project_path(data_path)
            resolved_standard_path = resolve_project_path(standard_path)

            if not resolved_data_path.exists():
                click.echo(f"❌ Data file not found: {data_path}")
                click.echo(get_project_root_display())
                click.echo(f"📄 Testing: {rel_to_project_root(resolved_data_path)}")
                return 1

            if not resolved_standard_path.exists():
                click.echo(f"❌ Standard file not found: {standard_path}")
                click.echo(get_project_root_display())
                click.echo(
                    f"📋 Against Standard: {rel_to_project_root(resolved_standard_path)}"
                )
                return 1

            # Load data
            data_list = load_data(str(resolved_data_path))
            if not data_list:
                click.echo("❌ No data loaded")
                return 1

            data = pd.DataFrame(data_list)

            # Run assessment
            assessor = DataQualityAssessor(self._load_assessor_config())
            result = assessor.assess(data, str(resolved_standard_path))

            # Get threshold and metadata
            threshold = self._get_threshold_from_standard(resolved_standard_path)
            metadata = result.metadata or {}

            # Extract scoring information
            scoring_info = self._extract_scoring_information(result, metadata)

            if json_output:
                self._display_json_output(result, threshold, scoring_info)
            else:
                self._display_text_output(result, threshold, scoring_info)

            return 0

        except Exception as e:
            click.echo(f"❌ Scoring explain failed: {e}")
            return 1

    def _load_assessor_config(self) -> dict[str, Any]:
        """Load configuration for the data quality assessor."""
        from ...config.loader import ConfigurationLoader

        assessor_config: dict[str, Any] = {}

        try:
            config_loader = ConfigurationLoader()
            config = config_loader.get_active_config()
            if config:
                env_config = config_loader.get_environment_config(config)
                assessor_config["audit"] = env_config.get(
                    "audit", self._get_default_audit_config()
                )
            else:
                assessor_config["audit"] = self._get_default_audit_config()
        except Exception:
            assessor_config["audit"] = self._get_default_audit_config()

        return assessor_config

    def _get_default_audit_config(self) -> dict[str, Any]:
        """Get default audit configuration."""
        return {
            "enabled": True,
            "log_dir": "ADRI/dev/audit-logs",
            "log_prefix": "adri",
            "log_level": "INFO",
            "include_data_samples": True,
            "max_log_size_mb": 100,
        }

    def _get_threshold_from_standard(self, standard_path) -> float:
        """Read requirements.overall_minimum from a standard YAML."""
        try:
            std = load_contract(str(standard_path))
            req = std.get("requirements", {}) if isinstance(std, dict) else {}
            thr = float(req.get("overall_minimum", 75.0))
            return max(0.0, min(100.0, thr))  # Clamp to [0, 100]
        except Exception:
            return 75.0

    def _extract_scoring_information(
        self, result, metadata: dict[str, Any]
    ) -> dict[str, Any]:
        """Extract scoring information from assessment result."""
        # Convert dimension scores to simple numbers
        dim_scores_obj = result.dimension_scores or {}
        dim_scores = {
            dim: (float(s.score) if hasattr(s, "score") else float(s))
            for dim, s in dim_scores_obj.items()
        }

        # Get weights and calculate contributions
        applied_dim_weights = metadata.get("applied_dimension_weights", {})
        contributions = self._compute_dimension_contributions(
            dim_scores_obj, applied_dim_weights
        )

        # Get explain payload
        warnings = metadata.get("scoring_warnings", [])
        explain = metadata.get("explain", {}) or {}

        return {
            "dimension_scores": dim_scores,
            "applied_dimension_weights": applied_dim_weights,
            "contributions": contributions,
            "warnings": warnings,
            "explain": explain,
        }

    def _compute_dimension_contributions(
        self, dimension_scores, applied_dimension_weights
    ) -> dict[str, float]:
        """Compute contribution (%) of each dimension to overall score."""
        try:
            scores = {}
            for dim, val in (dimension_scores or {}).items():
                if hasattr(val, "score"):
                    scores[dim] = float(val.score)
                elif isinstance(val, (int, float)):
                    scores[dim] = float(val)
                else:
                    try:
                        scores[dim] = float(val.get("score", 0.0))
                    except Exception:
                        scores[dim] = 0.0

            weights = {
                k: float(v) for k, v in (applied_dimension_weights or {}).items()
            }
            sum_w = sum(weights.values()) if weights else 0.0
            contributions = {}

            for dim, s in scores.items():
                w = weights.get(dim, 1.0)
                contributions[dim] = (
                    (s / 20.0) * (w / sum_w) * 100.0 if sum_w > 0.0 else 0.0
                )

            return contributions
        except Exception:
            return {}

    def _display_json_output(
        self, result, threshold: float, scoring_info: dict[str, Any]
    ) -> None:
        """Display scoring breakdown as JSON."""
        explain = scoring_info["explain"]

        payload = {
            "overall_score": float(result.overall_score),
            "threshold": float(threshold),
            "passed": bool(result.passed),
            "dimension_scores": scoring_info["dimension_scores"],
            "dimension_weights": {
                k: float(v)
                for k, v in scoring_info["applied_dimension_weights"].items()
            },
            "contributions_percent": {
                k: float(v) for k, v in scoring_info["contributions"].items()
            },
            "warnings": scoring_info["warnings"],
        }

        # Add dimension-specific explanations
        for dimension in [
            "validity",
            "completeness",
            "consistency",
            "freshness",
            "plausibility",
        ]:
            dim_explain = explain.get(dimension, {})
            if dim_explain:
                payload[dimension] = self._format_dimension_explanation(
                    dimension, dim_explain
                )

        click.echo(json.dumps(payload, indent=2))

    def _display_text_output(
        self, result, threshold: float, scoring_info: dict[str, Any]
    ) -> None:
        """Display scoring breakdown as formatted text."""
        status_icon = "✅" if result.passed else "❌"
        status_text = "PASSED" if result.passed else "FAILED"

        click.echo("📊 Scoring Explain")
        click.echo("==================")
        click.echo(
            f"Overall: {result.overall_score:.1f}/100 {status_icon} {status_text}"
        )
        click.echo(f"Threshold: {threshold:.1f}/100")
        click.echo("")

        # Display dimension breakdown
        click.echo("Dimensions (score/20, weight, contribution to overall):")
        for dim in [
            "validity",
            "completeness",
            "consistency",
            "freshness",
            "plausibility",
        ]:
            if dim in scoring_info["dimension_scores"]:
                s = scoring_info["dimension_scores"][dim]
                w = float(scoring_info["applied_dimension_weights"].get(dim, 1.0))
                c = float(scoring_info["contributions"].get(dim, 0.0))
                click.echo(
                    f"  • {dim}: {s:.2f}/20, weight={w:.2f}, contribution={c:.2f}%"
                )

        # Display dimension-specific explanations
        self._display_dimension_explanations(scoring_info["explain"])

        # Display warnings if any
        if scoring_info["warnings"]:
            click.echo("")
            click.echo("⚠️  Warnings:")
            for warning in scoring_info["warnings"]:
                click.echo(f" - {warning}")

    def _format_dimension_explanation(
        self, dimension: str, dim_explain: dict[str, Any]
    ) -> dict[str, Any]:
        """Format dimension explanation for JSON output."""
        if dimension == "validity":
            return {
                "rule_counts": dim_explain.get("rule_counts", {}),
                "per_field_counts": dim_explain.get("per_field_counts", {}),
                "applied_weights": dim_explain.get("applied_weights", {}),
            }
        elif dimension == "completeness":
            return {
                "required_total": int(dim_explain.get("required_total", 0)),
                "missing_required": int(dim_explain.get("missing_required", 0)),
                "pass_rate": float(dim_explain.get("pass_rate", 0.0)),
                "score_0_20": float(dim_explain.get("score_0_20", 0.0)),
                "per_field_missing": dim_explain.get("per_field_missing", {}),
                "top_missing_fields": dim_explain.get("top_missing_fields", []),
            }
        elif dimension in ["consistency", "freshness", "plausibility"]:
            return {
                "pass_rate": float(dim_explain.get("pass_rate", 0.0)),
                "rule_weights_applied": dim_explain.get("rule_weights_applied", {}),
                "score_0_20": float(dim_explain.get("score_0_20", 0.0)),
                "warnings": dim_explain.get("warnings", []),
                **{
                    k: v
                    for k, v in dim_explain.items()
                    if k
                    not in [
                        "pass_rate",
                        "rule_weights_applied",
                        "score_0_20",
                        "warnings",
                    ]
                },
            }
        else:
            return dim_explain

    def _display_dimension_explanations(self, explain: dict[str, Any]) -> None:
        """Display dimension-specific explanations in text format."""
        # Validity explanation
        validity_explain = explain.get("validity", {})
        if validity_explain:
            self._display_validity_explanation(validity_explain)

        # Completeness explanation
        completeness_explain = explain.get("completeness", {})
        if completeness_explain:
            self._display_completeness_explanation(completeness_explain)

        # Consistency explanation
        consistency_explain = explain.get("consistency", {})
        if consistency_explain:
            self._display_consistency_explanation(consistency_explain)

        # Freshness explanation
        freshness_explain = explain.get("freshness", {})
        if freshness_explain:
            self._display_freshness_explanation(freshness_explain)
        else:
            click.echo("")
            click.echo("Freshness: no active rules configured")

    def _display_validity_explanation(self, validity_explain: dict[str, Any]) -> None:
        """Display validity dimension explanation."""
        rule_counts = validity_explain.get("rule_counts", {})
        applied_weights = validity_explain.get("applied_weights", {})
        global_weights = (applied_weights or {}).get("global", {}) or {}

        active_rules = [
            rk for rk, cnt in rule_counts.items() if cnt.get("total", 0) > 0
        ]
        if active_rules:
            click.echo("")
            click.echo("Validity rule-type breakdown:")
            for rk in [
                "type",
                "allowed_values",
                "pattern",
                "length_bounds",
                "numeric_bounds",
                "date_bounds",
            ]:
                cnt = rule_counts.get(rk, {})
                total = int(cnt.get("total", 0) or 0)
                passed_c = int(cnt.get("passed", 0) or 0)
                if total <= 0:
                    continue
                pass_rate = (passed_c / total) * 100.0
                gw = float(global_weights.get(rk, 0.0))
                click.echo(
                    f" - {rk}: {passed_c}/{total} ({pass_rate:.1f}%), weight={gw:.2f}"
                )

    def _display_completeness_explanation(
        self, completeness_explain: dict[str, Any]
    ) -> None:
        """Display completeness dimension explanation."""
        click.echo("")
        click.echo("Completeness breakdown:")
        req_total = int(completeness_explain.get("required_total", 0) or 0)
        miss = int(completeness_explain.get("missing_required", 0) or 0)
        pr = float(completeness_explain.get("pass_rate", 0.0) or 0.0) * 100.0
        click.echo(
            f" - required cells: {req_total}, missing required: {miss}, pass_rate={pr:.1f}%"
        )

        top_missing = completeness_explain.get("top_missing_fields", []) or []
        if top_missing:
            click.echo("  - top missing fields:")
            for item in top_missing[:5]:
                try:
                    click.echo(
                        f"     • {item.get('field')}: {int(item.get('missing', 0))} missing"
                    )
                except Exception:
                    pass

    def _display_consistency_explanation(
        self, consistency_explain: dict[str, Any]
    ) -> None:
        """Display consistency dimension explanation."""
        click.echo("")
        click.echo("Consistency breakdown:")
        pk_fields = consistency_explain.get("pk_fields", []) or []
        counts = consistency_explain.get("counts", {}) or {}
        total = int(counts.get("total", 0) or 0)
        passed_c = int(counts.get("passed", 0) or 0)
        failed_c = int(counts.get("failed", 0) or 0)
        pr = float(consistency_explain.get("pass_rate", 0.0) or 0.0) * 100.0
        rw = (consistency_explain.get("rule_weights_applied", {}) or {}).get(
            "primary_key_uniqueness", 0.0
        )

        click.echo(f" - pk_fields: {pk_fields if pk_fields else '[]'}")
        click.echo(
            f" - primary_key_uniqueness: {passed_c}/{total} passed, failed={failed_c}, pass_rate={pr:.1f}%, weight={float(rw):.2f}"
        )

    def _display_freshness_explanation(self, freshness_explain: dict[str, Any]) -> None:
        """Display freshness dimension explanation."""
        click.echo("")
        click.echo("Freshness breakdown:")
        df = freshness_explain.get("date_field")
        as_of = freshness_explain.get("as_of")
        wd = freshness_explain.get("window_days")
        counts = freshness_explain.get("counts", {}) or {}
        total = int(counts.get("total", 0) or 0)
        passed_c = int(counts.get("passed", 0) or 0)
        pr = float(freshness_explain.get("pass_rate", 0.0) or 0.0) * 100.0
        rw = (freshness_explain.get("rule_weights_applied", {}) or {}).get(
            "recency_window", 0.0
        )

        click.echo(f" - date_field: {df}, window_days: {wd}, as_of: {as_of}")
        click.echo(
            f" - recency_window: {passed_c}/{total} passed, pass_rate={pr:.1f}%, weight={float(rw):.2f}"
        )

    def get_name(self) -> str:
        """Get the command name."""
        return "scoring-explain"


class ScoringPresetApplyCommand(Command):
    """Command for applying scoring presets to standards.

    Handles application of predefined scoring configurations (balanced, strict, lenient)
    to ADRI standard files.
    """

    def get_description(self) -> str:
        """Get command description."""
        return "Apply a scoring preset to a standard's dimension requirements"

    def execute(self, args: dict[str, Any]) -> int:
        """Execute the scoring-preset-apply command.

        Args:
            args: Command arguments containing:
                - preset: str - Preset name (balanced, strict, lenient)
                - standard_path: str - Path to YAML standard file
                - output_path: Optional[str] - Write modified standard to this path

        Returns:
            Exit code (0 for success, non-zero for error)
        """
        preset = args["preset"]
        standard_path = args["standard_path"]
        output_path = args.get("output_path")

        return self._apply_scoring_preset(preset, standard_path, output_path)

    def _apply_scoring_preset(
        self, preset: str, standard_path: str, output_path: str | None = None
    ) -> int:
        """Apply a scoring preset to a standard's dimension requirements."""
        try:
            import yaml

            resolved_standard_path = resolve_project_path(standard_path)
            if not resolved_standard_path.exists():
                click.echo(f"❌ Standard file not found: {standard_path}")
                click.echo(get_project_root_display())
                click.echo(
                    f"📋 Path tried: {rel_to_project_root(resolved_standard_path)}"
                )
                return 1

            # Load standard
            std = load_contract(str(resolved_standard_path))
            if not isinstance(std, dict):
                click.echo("❌ Invalid standard structure")
                return 1

            # Get preset configuration
            preset_config = self._get_preset_config(preset)
            if not preset_config:
                click.echo(f"❌ Unknown preset: {preset}")
                click.echo("Available: balanced, strict, lenient")
                return 1

            # Apply preset
            changed_dims = self._apply_preset_to_standard(std, preset_config)

            # Determine output path
            out_path = (
                resolve_project_path(output_path)
                if output_path
                else resolved_standard_path
            )
            out_path.parent.mkdir(parents=True, exist_ok=True)

            # Save modified standard
            with open(out_path, "w", encoding="utf-8") as f:
                yaml.dump(std, f, default_flow_style=False, sort_keys=False)

            # Display results
            if output_path:
                click.echo(
                    f"✅ Preset '{preset}' applied and saved to: {rel_to_project_root(out_path)}"
                )
            else:
                click.echo(
                    f"✅ Preset '{preset}' applied in-place: {rel_to_project_root(out_path)}"
                )

            click.echo("Changes:")
            for line in changed_dims:
                click.echo(f"  • {line}")

            return 0

        except Exception as e:
            click.echo(f"❌ Failed to apply preset: {e}")
            return 1

    def _get_preset_config(self, preset: str) -> dict[str, Any] | None:
        """Get configuration for the specified preset."""
        presets = {
            "balanced": {
                "weights": {
                    "validity": 1.0,
                    "completeness": 1.0,
                    "consistency": 1.0,
                    "freshness": 1.0,
                    "plausibility": 1.0,
                },
                "minimums": {
                    "validity": 15.0,
                    "completeness": 15.0,
                    "consistency": 12.0,
                    "freshness": 15.0,
                    "plausibility": 12.0,
                },
                "validity_rule_weights": {
                    "type": 0.30,
                    "allowed_values": 0.20,
                    "pattern": 0.20,
                    "length_bounds": 0.10,
                    "numeric_bounds": 0.20,
                },
            },
            "strict": {
                "weights": {
                    "validity": 1.3,
                    "completeness": 1.2,
                    "consistency": 1.1,
                    "freshness": 1.0,
                    "plausibility": 0.9,
                },
                "minimums": {
                    "validity": 17.0,
                    "completeness": 17.0,
                    "consistency": 14.0,
                    "freshness": 16.0,
                    "plausibility": 14.0,
                },
                "validity_rule_weights": {
                    "type": 0.35,
                    "allowed_values": 0.15,
                    "pattern": 0.25,
                    "length_bounds": 0.10,
                    "numeric_bounds": 0.25,
                },
            },
            "lenient": {
                "weights": {
                    "validity": 0.9,
                    "completeness": 0.8,
                    "consistency": 1.0,
                    "freshness": 1.0,
                    "plausibility": 1.0,
                },
                "minimums": {
                    "validity": 12.0,
                    "completeness": 12.0,
                    "consistency": 10.0,
                    "freshness": 12.0,
                    "plausibility": 10.0,
                },
                "validity_rule_weights": {
                    "type": 0.25,
                    "allowed_values": 0.25,
                    "pattern": 0.15,
                    "length_bounds": 0.10,
                    "numeric_bounds": 0.25,
                },
            },
        }

        return presets.get(preset)

    def _apply_preset_to_standard(
        self, std: dict[str, Any], preset_config: dict[str, Any]
    ) -> list[str]:
        """Apply preset configuration to standard."""
        req = std.setdefault("requirements", {})
        dim_reqs = req.setdefault("dimension_requirements", {})

        changed_dims = []

        for dim in [
            "validity",
            "completeness",
            "consistency",
            "freshness",
            "plausibility",
        ]:
            dim_cfg = dim_reqs.setdefault(dim, {})
            before_weight = dim_cfg.get("weight")
            before_min = dim_cfg.get("minimum_score")

            dim_cfg["weight"] = float(
                preset_config["weights"].get(dim, dim_cfg.get("weight", 1.0))
            )
            dim_cfg["minimum_score"] = float(
                preset_config["minimums"].get(dim, dim_cfg.get("minimum_score", 15.0))
            )

            if dim == "validity":
                scoring = dim_cfg.setdefault("scoring", {})
                scoring["rule_weights"] = {
                    k: float(v)
                    for k, v in preset_config["validity_rule_weights"].items()
                }
                scoring.setdefault(
                    "field_overrides", scoring.get("field_overrides", {})
                )

            changed_dims.append(
                f"{dim} (weight {before_weight}→{dim_cfg['weight']}, min {before_min}→{dim_cfg['minimum_score']})"
            )

        return changed_dims

    def get_name(self) -> str:
        """Get the command name."""
        return "scoring-preset-apply"
