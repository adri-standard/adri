#!/usr/bin/env python3
"""
Demo Validator - Core utilities for validating ADRI demo experiences

Focuses on AI engineer experience rather than technical implementation details.
Validates that demos are credible, relatable, and immediately valuable.
"""

import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class DemoValidator:
    """Validates ADRI demo experiences from AI engineer perspective."""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.examples_dir = self.project_root / "examples"
        self.tools_dir = self.project_root / "tools"

    def discover_examples(self) -> List[Path]:
        """Discover all framework example files."""
        if not self.examples_dir.exists():
            return []

        example_files = []
        for file_path in self.examples_dir.glob("*.py"):
            if file_path.name.startswith(
                (
                    "langchain-",
                    "crewai-",
                    "autogen-",
                    "llamaindex-",
                    "haystack-",
                    "langgraph-",
                    "semantic-kernel-",
                )
            ):
                example_files.append(file_path)

        return sorted(example_files)

    def extract_framework_name(self, example_path: Path) -> str:
        """Extract framework name from example filename."""
        filename = example_path.name
        if filename.startswith("langchain-"):
            return "langchain"
        elif filename.startswith("crewai-"):
            return "crewai"
        elif filename.startswith("autogen-"):
            return "autogen"
        elif filename.startswith("llamaindex-"):
            return "llamaindex"
        elif filename.startswith("haystack-"):
            return "haystack"
        elif filename.startswith("langgraph-"):
            return "langgraph"
        elif filename.startswith("semantic-kernel-"):
            return "semantic-kernel"
        else:
            return "unknown"

    def validate_problem_recognition(self, example_path: Path) -> Tuple[bool, str]:
        """
        Validate that example demonstrates a real, recognizable problem.

        Returns:
            (is_valid, reason)
        """
        try:
            with open(example_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Check for problem demonstration patterns
            problem_indicators = [
                "GitHub issue",
                "github.com",
                "real-world problem",
                "production issue",
                "data validation",
                "conversation flow",
                "agent coordination",
                "document processing",
                "knowledge retrieval",
                "workflow automation",
                "customer service",
                "business analysis",
                "research collaboration",
            ]

            found_indicators = [
                indicator
                for indicator in problem_indicators
                if indicator.lower() in content.lower()
            ]

            if len(found_indicators) >= 2:
                return True, f"Shows real problems: {', '.join(found_indicators[:3])}"
            else:
                return False, "Doesn't clearly demonstrate real-world problems"

        except Exception as e:
            return False, f"Error reading example: {e}"

    def validate_solution_credibility(self, example_path: Path) -> Tuple[bool, str]:
        """
        Validate that ADRI protection feels natural and credible.

        Returns:
            (is_credible, reason)
        """
        try:
            with open(example_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Check for ADRI protection patterns
            adri_patterns = [
                "@adri_protected",
                "adri_protected",
                "ADRI",
                "data quality",
                "protection",
                "validation",
                "standard",
            ]

            found_patterns = [
                pattern for pattern in adri_patterns if pattern in content
            ]

            # Check for natural integration (not forced)
            if "@adri_protected" in content or "adri_protected" in content:
                # Count decorator usage - should be focused, not everywhere
                decorator_count = content.count("@adri_protected")
                if 1 <= decorator_count <= 3:
                    return (
                        True,
                        f"Natural ADRI integration ({decorator_count} decorators)",
                    )
                elif decorator_count > 3:
                    return (
                        False,
                        f"Over-engineered ({decorator_count} decorators - too many)",
                    )
                else:
                    return False, "Missing ADRI protection decorators"
            else:
                return False, "No ADRI protection found"

        except Exception as e:
            return False, f"Error validating solution: {e}"

    def validate_value_clarity(self, example_path: Path) -> Tuple[bool, str]:
        """
        Validate that value proposition is immediately clear.

        Returns:
            (is_clear, reason)
        """
        try:
            with open(example_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Check for clear value messaging
            value_indicators = [
                "prevents",
                "protection",
                "validation",
                "quality",
                "reliable",
                "error",
                "failure",
                "issue",
                "problem",
                "solution",
                "benefit",
            ]

            # Look for value messaging in comments and docstrings
            lines = content.split("\n")
            value_lines = []

            for line in lines:
                if line.strip().startswith("#") or '"""' in line or "'''" in line:
                    for indicator in value_indicators:
                        if indicator.lower() in line.lower():
                            value_lines.append(line.strip())
                            break

            if len(value_lines) >= 3:
                return (
                    True,
                    f"Clear value messaging found ({len(value_lines)} value statements)",
                )
            else:
                return (
                    False,
                    f"Value proposition not clear enough ({len(value_lines)} value statements)",
                )

        except Exception as e:
            return False, f"Error validating value clarity: {e}"

    def validate_workflow_naturalness(self, example_path: Path) -> Tuple[bool, str]:
        """
        Validate that example feels like natural framework usage.

        Returns:
            (is_natural, reason)
        """
        try:
            with open(example_path, "r", encoding="utf-8") as f:
                content = f.read()

            framework = self.extract_framework_name(example_path)

            # Framework-specific natural patterns
            framework_patterns = {
                "langchain": [
                    "ChatOpenAI",
                    "LLMChain",
                    "PromptTemplate",
                    "chat",
                    "llm",
                ],
                "crewai": ["Agent", "Task", "Crew", "crew.kickoff", "agent"],
                "autogen": [
                    "ConversableAgent",
                    "GroupChat",
                    "GroupChatManager",
                    "chat",
                ],
                "llamaindex": [
                    "VectorStoreIndex",
                    "SimpleDirectoryReader",
                    "query_engine",
                    "index",
                ],
                "haystack": ["Pipeline", "Component", "Document", "pipeline.run"],
                "langgraph": ["StateGraph", "CompiledGraph", "MessageState", "graph"],
                "semantic-kernel": ["Kernel", "Function", "Plugin", "kernel"],
            }

            expected_patterns = framework_patterns.get(framework, [])
            found_patterns = [
                pattern for pattern in expected_patterns if pattern in content
            ]

            if len(found_patterns) >= 2:
                return (
                    True,
                    f"Natural {framework} usage: {', '.join(found_patterns[:3])}",
                )
            else:
                return False, f"Doesn't feel like natural {framework} usage"

        except Exception as e:
            return False, f"Error validating naturalness: {e}"

    def validate_setup_tool_integration(self) -> Tuple[bool, str]:
        """
        Validate that setup tool exists and looks professional.

        Returns:
            (is_integrated, reason)
        """
        setup_tool_path = self.tools_dir / "adri-setup.py"

        if not setup_tool_path.exists():
            return False, "Setup tool (tools/adri-setup.py) not found"

        try:
            with open(setup_tool_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Check for professional setup tool features
            professional_features = [
                "virtual environment",
                "venv",
                "dependency",
                "install",
                "framework",
                "requirements",
                "python -m pip",
            ]

            found_features = [
                feature
                for feature in professional_features
                if feature.lower() in content.lower()
            ]

            if len(found_features) >= 4:
                return (
                    True,
                    f"Professional setup tool with {len(found_features)} features",
                )
            else:
                return (
                    False,
                    f"Setup tool lacks professional features ({len(found_features)} found)",
                )

        except Exception as e:
            return False, f"Error reading setup tool: {e}"

    def test_example_execution(
        self, example_path: Path, timeout: int = 10
    ) -> Tuple[bool, str]:
        """
        Test that example executes without crashing (basic smoke test).

        Returns:
            (executed_ok, result_message)
        """
        try:
            # Run example with no API key (should exit gracefully)
            env = os.environ.copy()
            if "OPENAI_API_KEY" in env:
                del env["OPENAI_API_KEY"]

            result = subprocess.run(
                [sys.executable, str(example_path)],
                capture_output=True,
                text=True,
                timeout=timeout,
                env=env,
                cwd=str(self.project_root),
            )

            # Success criteria:
            # - Exit code 0 (success) or 1 (graceful exit due to no API key)
            # - No Python crashes or import errors
            # - Mentions ADRI in output

            if result.returncode in [0, 1]:
                output = result.stdout + result.stderr
                if "ADRI" in output or "adri" in output:
                    return (
                        True,
                        f"Executed successfully (exit code {result.returncode})",
                    )
                else:
                    return False, f"Executed but no ADRI mention in output"
            else:
                return False, f"Execution failed (exit code {result.returncode})"

        except subprocess.TimeoutExpired:
            return False, f"Execution timed out after {timeout} seconds"
        except Exception as e:
            return False, f"Execution error: {e}"

    def validate_demo_credibility(self, example_path: Path) -> Dict[str, any]:
        """
        Comprehensive validation of demo credibility for AI engineers.

        Returns:
            Dict with validation results
        """
        framework = self.extract_framework_name(example_path)

        results = {
            "framework": framework,
            "example_file": example_path.name,
            "validations": {},
            "overall_score": 0,
            "credible": False,
        }

        # Run all validation checks
        validations = [
            ("problem_recognition", self.validate_problem_recognition),
            ("solution_credibility", self.validate_solution_credibility),
            ("value_clarity", self.validate_value_clarity),
            ("workflow_naturalness", self.validate_workflow_naturalness),
            ("execution_test", self.test_example_execution),
        ]

        passed_count = 0

        for validation_name, validation_func in validations:
            try:
                is_valid, reason = validation_func(example_path)
                results["validations"][validation_name] = {
                    "passed": is_valid,
                    "reason": reason,
                }
                if is_valid:
                    passed_count += 1
            except Exception as e:
                results["validations"][validation_name] = {
                    "passed": False,
                    "reason": f"Validation error: {e}",
                }

        # Calculate overall score
        total_validations = len(validations)
        results["overall_score"] = (passed_count / total_validations) * 100
        results["credible"] = (
            results["overall_score"] >= 70.0
        )  # 70% threshold for credibility

        return results


def main():
    """Run demo validation as standalone script."""
    validator = DemoValidator()
    examples = validator.discover_examples()

    print("🎭 ADRI Demo Credibility Validator")
    print("=" * 50)
    print(f"Found {len(examples)} examples to validate\n")

    all_results = []

    for example_path in examples:
        print(f"🔍 Validating {example_path.name}...")
        results = validator.validate_demo_credibility(example_path)
        all_results.append(results)

        # Show results
        framework = results["framework"]
        score = results["overall_score"]
        credible = "✅ CREDIBLE" if results["credible"] else "❌ NEEDS WORK"

        print(f"   {framework.upper()}: {score:.1f}% - {credible}")

        # Show failed validations
        for validation_name, validation_result in results["validations"].items():
            if not validation_result["passed"]:
                reason = validation_result["reason"]
                print(f"     ⚠️ {validation_name}: {reason}")

        print()

    # Overall summary
    credible_count = sum(1 for r in all_results if r["credible"])
    total_count = len(all_results)
    overall_credibility = (credible_count / total_count) * 100 if total_count > 0 else 0

    print(f"📊 Overall Demo Credibility: {overall_credibility:.1f}%")
    print(f"✅ Credible demos: {credible_count}/{total_count}")

    if overall_credibility >= 80.0:
        print("🎉 Demo experiences ready for AI engineers!")
    else:
        print("🔧 Demo experiences need improvement for credibility")


if __name__ == "__main__":
    main()
