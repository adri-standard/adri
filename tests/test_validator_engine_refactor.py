import unittest
from typing import Dict, Any, List

import pandas as pd

from adri.validator.engine import ValidationEngine, BundledStandardWrapper


class TestValidatorEngineRefactor(unittest.TestCase):
    """Stability tests for helper-level invariants introduced in refactor."""

    def setUp(self):
        self.engine = ValidationEngine()
        # Data crafted so all checks pass under provided requirements
        self.df = pd.DataFrame(
            {
                "code": ["A", "B", "B"],           # string: enum, length, pattern
                "age": [10, 20, 30],               # integer: numeric bounds
                "unused": ["x", "y", "z"],         # not in requirements
            }
        )
        self.field_requirements: Dict[str, Any] = {
            "code": {
                "type": "string",
                "allowed_values": ["A", "B"],
                "min_length": 1,
                "max_length": 2,
                "pattern": r"^[AB]$",
            },
            "age": {
                "type": "integer",
                "min_value": 0,
                "max_value": 120,
            },
        }
        # RULE_KEYS in the same order as engine
        self.RULE_KEYS: List[str] = [
            "type",
            "allowed_values",
            "length_bounds",
            "pattern",
            "numeric_bounds",
            "date_bounds",
        ]

    def test_validity_counts_and_weights_stability(self):
        """Counts reflect rule application order; weights normalize and equalize when zero."""
        counts, per_field_counts = self.engine._compute_validity_rule_counts(
            self.df, self.field_requirements
        )

        # Totals: for 'code' we apply type, allowed_values, length_bounds, pattern
        # for 'age' we apply type, numeric_bounds
        # date_bounds remain zero
        self.assertEqual(counts["type"]["total"], 6)
        self.assertEqual(counts["allowed_values"]["total"], 3)
        self.assertEqual(counts["length_bounds"]["total"], 3)
        self.assertEqual(counts["pattern"]["total"], 3)
        self.assertEqual(counts["numeric_bounds"]["total"], 3)
        self.assertEqual(counts["date_bounds"]["total"], 0)

        # All pass under our data/requirements
        for rk in ["type", "allowed_values", "length_bounds", "pattern", "numeric_bounds"]:
            self.assertEqual(counts[rk]["passed"], counts[rk]["total"])

        # Global weights: provide zeros (and an unknown) to force equalization over active rule types
        zero_weights_cfg = {
            "type": 0,
            "allowed_values": 0,
            "length_bounds": 0,
            "pattern": 0,
            "numeric_bounds": 0,
            "date_bounds": 0,  # inactive here, should be dropped by active filter
            "UNKNOWN": 5,      # ignored
        }
        Sg, Wg, applied_global = self.engine._apply_global_rule_weights(
            counts, zero_weights_cfg, self.RULE_KEYS
        )
        # Only active rules should be present (no date_bounds)
        self.assertTrue(all(rk in ["type", "allowed_values", "length_bounds", "pattern", "numeric_bounds"] for rk in applied_global.keys()))
        # Equalization implies weight sum > 0 and since all scores=1, Sg == Wg
        self.assertGreater(Wg, 0.0)
        self.assertAlmostEqual(Sg, Wg, places=6)
        # Warning recorded for equalization
        self.assertTrue(
            any("Validity rule_weights were zero/invalid" in w for w in getattr(self.engine, "_scoring_warnings", []))
        )

        # Field overrides: include a negative (clamped) and unknowns
        overrides_cfg = {
            "code": {"allowed_values": 2.0, "pattern": -3.0, "unknown": 7.0},
            "age": {"numeric_bounds": 3.0},
            "ghost": {"type": 5.0},  # field not present in counts
        }
        S_add, W_add, applied_overrides = self.engine._apply_field_overrides(
            per_field_counts, overrides_cfg, self.RULE_KEYS
        )
        # pattern negative is clamped to 0 and not applied; unknown ignored; ghost ignored
        self.assertIn("code", applied_overrides)
        self.assertIn("allowed_values", applied_overrides["code"])
        self.assertNotIn("pattern", applied_overrides["code"])
        self.assertIn("age", applied_overrides)
        self.assertIn("numeric_bounds", applied_overrides["age"])
        # Since all selected rule scores=1, S_add == W_add == 2 + 3
        self.assertAlmostEqual(S_add, 5.0, places=6)
        self.assertAlmostEqual(W_add, 5.0, places=6)
        # Warning recorded for negative override
        self.assertTrue(
            any("field_overrides contained negative weight" in w for w in getattr(self.engine, "_scoring_warnings", []))
        )

        # Explain payload structure remains stable
        explain = self.engine._assemble_validity_explain(counts, per_field_counts, applied_global, applied_overrides)
        self.assertIsInstance(explain, dict)
        self.assertIn("rule_counts", explain)
        self.assertIn("per_field_counts", explain)
        self.assertIn("applied_weights", explain)
        self.assertIn("global", explain["applied_weights"])
        self.assertIn("overrides", explain["applied_weights"])

    def test_explain_payload_schema_stability(self):
        """_assess_validity_with_standard produces stable explain payload structure."""
        standard_dict = {
            "requirements": {
                "field_requirements": self.field_requirements,
                "dimension_requirements": {
                    "validity": {
                        "scoring": {
                            # Force equalization path
                            "rule_weights": {
                                "type": 0, "allowed_values": 0, "length_bounds": 0, "pattern": 0, "numeric_bounds": 0
                            },
                            # Include a negative override to exercise warnings/clamping
                            "field_overrides": {
                                "code": {"pattern": -1.0}
                            },
                        }
                    }
                },
            }
        }
        wrapper = BundledStandardWrapper(standard_dict)

        score = self.engine._assess_validity_with_standard(self.df, wrapper)
        # Perfect pass should yield the top score under weighted aggregation
        self.assertGreaterEqual(score, 19.9)

        validity_explain = getattr(self.engine, "_explain", {}).get("validity", {})
        self.assertIsInstance(validity_explain, dict)
        self.assertIn("rule_counts", validity_explain)
        self.assertIn("per_field_counts", validity_explain)
        self.assertIn("applied_weights", validity_explain)
        self.assertIn("global", validity_explain["applied_weights"])
        self.assertIn("overrides", validity_explain["applied_weights"])

        # Warnings captured for both equalization and negative override clamping
        warnings = getattr(self.engine, "_scoring_warnings", [])
        self.assertTrue(any("rule_weights were zero/invalid" in w for w in warnings))
        self.assertTrue(any("field_overrides contained negative weight" in w for w in warnings))


if __name__ == "__main__":
    unittest.main()
