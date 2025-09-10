"""
Test demo credibility and user first impressions.
"""

import unittest
from pathlib import Path

from .demo_validator import DemoValidator


class TestDemoCredibility(unittest.TestCase):
    """Test that demos provide credible first impression for users."""

    def setUp(self):
        self.validator = DemoValidator()

    def test_all_framework_examples_exist(self):
        """Test that all promised framework examples are present."""
        complete, missing = self.validator.validate_framework_examples()
        self.assertTrue(complete, f"Missing framework examples: {missing}")

    def test_dependency_helpers_available(self):
        """Test that dependency helpers are available for users."""
        available = self.validator.check_dependency_helpers()
        self.assertTrue(available, "Dependency helpers not found")

    def test_examples_directory_structure(self):
        """Test that examples directory has proper structure."""
        examples_dir = self.validator.examples_dir
        self.assertTrue(examples_dir.exists(), "Examples directory not found")

        utils_dir = examples_dir / "utils"
        self.assertTrue(utils_dir.exists(), "Utils directory not found")

    def test_framework_coverage(self):
        """Test that major AI frameworks are covered."""
        expected_frameworks = [
            "langchain",
            "crewai",
            "autogen",
            "langgraph",
            "llamaindex",
            "haystack",
            "semantic-kernel",
        ]

        examples_dir = self.validator.examples_dir
        example_files = list(examples_dir.glob("*.py"))

        covered_frameworks = []
        for example_file in example_files:
            for framework in expected_frameworks:
                if framework in example_file.name.lower():
                    covered_frameworks.append(framework)

        # Should cover at least 6 of the major frameworks
        self.assertGreaterEqual(
            len(set(covered_frameworks)),
            6,
            f"Only {len(set(covered_frameworks))} frameworks covered",
        )


if __name__ == "__main__":
    unittest.main()
