import unittest
from typing import Dict, Any, List

import pandas as pd

from src.adri.analysis.standard_generator import StandardGenerator


class TestStandardGeneratorRefactor(unittest.TestCase):
    """Helper-level stability tests for the enriched standard generator."""

    def setUp(self):
        self.gen = StandardGenerator()
        # Data fixture with clear invariants
        self.df = pd.DataFrame(
            {
                "user_id": [1, 2, 3],            # id-like: enums should be suppressed
                "code": ["A", "BB", "CCC"],      # string: length bounds inferred
                "age": [10, 20, 30],             # integer: numeric bounds inferred
                "unused": ["x", "y", "z"],       # not used in assertions
            }
        )

    def test_field_requirement_equivalence_on_fixture(self):
        """Generate standard and assert key invariants preserved."""
        std = self.gen.generate_from_dataframe(self.df, "sample_data")
        reqs: Dict[str, Any] = std.get("requirements", {}).get("field_requirements", {})
        self.assertIsInstance(reqs, dict)

        # user_id: id-like -> no allowed_values, type numeric or string depending on dtype
        uid_req = reqs.get("user_id", {})
        self.assertIsInstance(uid_req, dict)
        self.assertNotIn("allowed_values", uid_req)  # enums suppressed for id-like
        self.assertIn(uid_req.get("type"), {"integer", "float", "string"})
        # Nullability strict: no nulls observed -> nullable False
        self.assertIn("nullable", uid_req)
        self.assertFalse(uid_req["nullable"])

        # code: string -> length bounds present and consistent
        code_req = reqs.get("code", {})
        self.assertEqual(code_req.get("type"), "string")
        self.assertIn("min_length", code_req)
        self.assertIn("max_length", code_req)
        self.assertGreaterEqual(code_req["min_length"], 0)
        self.assertGreaterEqual(code_req["max_length"], code_req["min_length"])
        # No requirement that pattern must exist by default (regex_inference may be disabled)

        # age: integer -> numeric bounds present and cover observed span after training-pass
        age_req = reqs.get("age", {})
        self.assertIn(age_req.get("type"), {"integer", "float"})
        # After training-pass guarantee, bounds must cover observed min/max
        self.assertIn("min_value", age_req)
        self.assertIn("max_value", age_req)
        self.assertLessEqual(float(age_req["min_value"]), 10.0)
        self.assertGreaterEqual(float(age_req["max_value"]), 30.0)

    def test_training_pass_adjustments_logged_equivalently(self):
        """Force failures and verify targeted relaxations with logged adjustments."""
        # Start with a deliberately too-strict standard against the same data
        standard = {
            "standards": {"id": "strict_standard"},
            "requirements": {
                "overall_minimum": 75.0,
                "field_requirements": {
                    "code": {
                        "type": "string",
                        "allowed_values": ["X"],     # will be removed
                        "min_length": 5,             # will be widened down to observed min
                        "max_length": 5,             # will be widened up to observed max
                        "pattern": r"^Z+$",          # will be removed
                        "nullable": False,
                    },
                    "age": {
                        "type": "integer",
                        "min_value": 50.0,           # will be widened
                        "max_value": 60.0,           # will be widened
                        "nullable": False,
                    },
                },
                "dimension_requirements": {},
            },
            "metadata": {
                "explanations": {}  # sink for adjustments
            },
        }

        adjusted = self.gen._enforce_training_pass(self.df, standard)
        reqs = adjusted["requirements"]["field_requirements"]
        exps = adjusted["metadata"]["explanations"]

        # code: allowed_values removed
        code_req = reqs["code"]
        self.assertNotIn("allowed_values", code_req)
        # code: length widened to observed [1, 3]
        self.assertLessEqual(int(code_req.get("min_length", 1)), 1)
        self.assertGreaterEqual(int(code_req.get("max_length", 3)), 3)
        # code: pattern removed
        self.assertNotIn("pattern", code_req)

        # age: numeric range widened to cover [10, 30]
        age_req = reqs["age"]
        self.assertLessEqual(float(age_req.get("min_value", 10.0)), 10.0)
        self.assertGreaterEqual(float(age_req.get("max_value", 30.0)), 30.0)

        # Adjustments logged under metadata.explanations.<column>.adjustments
        self.assertIn("code", exps)
        adj_code: List[Dict[str, Any]] = exps["code"].get("adjustments", [])
        self.assertTrue(any(a.get("rule") == "allowed_values" and a.get("action") == "removed" for a in adj_code))
        self.assertTrue(any(a.get("rule") == "length_bounds" and a.get("action") == "widened" for a in adj_code))
        self.assertTrue(any(a.get("rule") == "pattern" and a.get("action") == "removed" for a in adj_code))

        self.assertIn("age", exps)
        adj_age: List[Dict[str, Any]] = exps["age"].get("adjustments", [])
        self.assertTrue(any(a.get("rule") == "numeric_range" and a.get("action") == "widened" for a in adj_age))


if __name__ == "__main__":
    unittest.main()
