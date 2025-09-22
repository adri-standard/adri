#!/usr/bin/env python3
"""
ADRI Automated Testing Recommendation System.

Analyzes code changes and provides intelligent recommendations for testing
strategies based on the specific files and functionality modified.

Features:
- Git change analysis to identify modified components
- Intelligent test suite recommendations based on changes
- Performance impact assessment
- ACT testing recommendations for GitHub CI compatibility
- Risk assessment and confidence scoring
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from typing import Dict, List, Set, Any, Optional
from dataclasses import dataclass, asdict
import argparse


@dataclass
class TestRecommendation:
    """Represents a test recommendation."""
    test_suite: str
    priority: str  # "HIGH", "MEDIUM", "LOW"
    reason: str
    command: str
    estimated_duration: str
    risk_mitigation: str


@dataclass
class ChangeAnalysis:
    """Analysis of changes in the codebase."""
    modified_files: List[str]
    added_files: List[str]
    deleted_files: List[str]
    affected_components: Set[str]
    change_complexity: str  # "LOW", "MEDIUM", "HIGH"
    risk_level: str  # "LOW", "MEDIUM", "HIGH", "CRITICAL"


@dataclass
class TestingStrategy:
    """Complete testing strategy recommendation."""
    analysis: ChangeAnalysis
    recommendations: List[TestRecommendation]
    estimated_total_time: str
    confidence_level: str
    act_testing_required: bool
    performance_testing_required: bool


class GitChangeAnalyzer:
    """Analyzes git changes to understand modification scope."""

    def __init__(self, project_root: Path):
        self.project_root = project_root

    def get_git_changes(self, since_commit: str = "HEAD~1") -> ChangeAnalysis:
        """Get git changes since specified commit."""
        try:
            # Get modified files
            result = subprocess.run(
                ["git", "diff", "--name-status", since_commit],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )

            if result.returncode != 0:
                # Fallback to staged changes
                result = subprocess.run(
                    ["git", "diff", "--name-status", "--cached"],
                    capture_output=True,
                    text=True,
                    cwd=self.project_root
                )

            modified_files = []
            added_files = []
            deleted_files = []

            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue

                parts = line.split('\t')
                if len(parts) >= 2:
                    status = parts[0]
                    file_path = parts[1]

                    if status == 'M':
                        modified_files.append(file_path)
                    elif status == 'A':
                        added_files.append(file_path)
                    elif status == 'D':
                        deleted_files.append(file_path)
                    elif status.startswith('R'):  # Renamed
                        modified_files.append(file_path)

            # If no git changes found, analyze uncommitted changes
            if not any([modified_files, added_files, deleted_files]):
                result = subprocess.run(
                    ["git", "status", "--porcelain"],
                    capture_output=True,
                    text=True,
                    cwd=self.project_root
                )

                for line in result.stdout.strip().split('\n'):
                    if not line:
                        continue

                    status = line[:2].strip()
                    file_path = line[3:]

                    if status in ['M', 'MM']:
                        modified_files.append(file_path)
                    elif status in ['A', 'AM']:
                        added_files.append(file_path)
                    elif status == 'D':
                        deleted_files.append(file_path)

            affected_components = self._analyze_affected_components(modified_files + added_files)
            change_complexity = self._assess_change_complexity(modified_files, added_files, deleted_files)
            risk_level = self._assess_risk_level(affected_components, change_complexity)

            return ChangeAnalysis(
                modified_files=modified_files,
                added_files=added_files,
                deleted_files=deleted_files,
                affected_components=affected_components,
                change_complexity=change_complexity,
                risk_level=risk_level
            )

        except subprocess.CalledProcessError:
            # Return empty analysis if git is not available
            return ChangeAnalysis(
                modified_files=[],
                added_files=[],
                deleted_files=[],
                affected_components=set(),
                change_complexity="LOW",
                risk_level="LOW"
            )

    def _analyze_affected_components(self, changed_files: List[str]) -> Set[str]:
        """Analyze which components are affected by file changes."""
        components = set()

        for file_path in changed_files:
            # CLI components
            if "cli.py" in file_path:
                components.add("CLI")
            if "path_resolution" in file_path or "resolve" in file_path:
                components.add("PATH_RESOLUTION")

            # Testing components
            if file_path.startswith("tests/"):
                components.add("TESTS")
                if "path_resolution" in file_path:
                    components.add("PATH_RESOLUTION_TESTS")
                if "environment" in file_path:
                    components.add("ENVIRONMENT_TESTS")
                if "integration" in file_path:
                    components.add("INTEGRATION_TESTS")
                if "performance" in file_path:
                    components.add("PERFORMANCE_TESTS")

            # Configuration components
            if "config.yaml" in file_path:
                components.add("CONFIGURATION")
            if "ADRI/" in file_path:
                components.add("ADRI_STRUCTURE")

            # Documentation components
            if file_path.startswith("docs/"):
                components.add("DOCUMENTATION")

            # Workflow components
            if ".github/workflows" in file_path:
                components.add("GITHUB_WORKFLOWS")

            # Scripts
            if file_path.startswith("scripts/"):
                components.add("SCRIPTS")
                if "act" in file_path or "test" in file_path:
                    components.add("TESTING_SCRIPTS")

        return components

    def _assess_change_complexity(self, modified: List[str], added: List[str], deleted: List[str]) -> str:
        """Assess the complexity of changes."""
        total_changes = len(modified) + len(added) + len(deleted)

        # High complexity indicators
        if any("cli.py" in f for f in modified):
            return "HIGH"
        if total_changes > 20:
            return "HIGH"
        if any(".github/workflows" in f for f in modified + added):
            return "HIGH"

        # Medium complexity indicators
        if total_changes > 10:
            return "MEDIUM"
        if any("test_" in f for f in modified + added):
            return "MEDIUM"

        return "LOW"

    def _assess_risk_level(self, components: Set[str], complexity: str) -> str:
        """Assess risk level based on affected components and complexity."""
        critical_components = {"CLI", "PATH_RESOLUTION", "GITHUB_WORKFLOWS"}
        high_risk_components = {"CONFIGURATION", "ADRI_STRUCTURE", "TESTING_SCRIPTS"}

        if components.intersection(critical_components) and complexity == "HIGH":
            return "CRITICAL"
        if components.intersection(critical_components):
            return "HIGH"
        if components.intersection(high_risk_components):
            return "MEDIUM"

        return "LOW"


class TestRecommendationEngine:
    """Engine for generating test recommendations based on change analysis."""

    def __init__(self):
        self.recommendation_rules = self._initialize_recommendation_rules()

    def _initialize_recommendation_rules(self) -> Dict[str, Any]:
        """Initialize recommendation rules based on component changes."""
        return {
            "CLI": {
                "required_tests": [
                    "tests/test_cli_enhancements.py",
                    "tests/test_path_resolution_comprehensive.py",
                    "tests/test_cli_workflow_integration.py"
                ],
                "performance_testing": True,
                "act_testing": True,
                "risk_multiplier": 2.0
            },
            "PATH_RESOLUTION": {
                "required_tests": [
                    "tests/test_path_resolution_comprehensive.py",
                    "tests/test_cli_enhancements.py",
                    "tests/test_cli_workflow_integration.py"
                ],
                "performance_testing": True,
                "act_testing": True,
                "risk_multiplier": 2.5
            },
            "CONFIGURATION": {
                "required_tests": [
                    "tests/test_environment_documentation.py",
                    "tests/test_config_loader_comprehensive.py"
                ],
                "performance_testing": False,
                "act_testing": True,
                "risk_multiplier": 1.5
            },
            "GITHUB_WORKFLOWS": {
                "required_tests": [
                    "tests/test_cli_workflow_integration.py"
                ],
                "performance_testing": False,
                "act_testing": True,
                "risk_multiplier": 3.0
            },
            "TESTS": {
                "required_tests": ["tests/"],
                "performance_testing": False,
                "act_testing": False,
                "risk_multiplier": 1.0
            },
            "DOCUMENTATION": {
                "required_tests": [
                    "tests/test_environment_documentation.py"
                ],
                "performance_testing": False,
                "act_testing": False,
                "risk_multiplier": 0.5
            }
        }

    def generate_recommendations(self, analysis: ChangeAnalysis) -> List[TestRecommendation]:
        """Generate test recommendations based on change analysis."""
        recommendations = []

        # Always recommend pre-commit checks
        recommendations.append(TestRecommendation(
            test_suite="pre-commit-hooks",
            priority="HIGH",
            reason="Ensure code formatting and basic validation",
            command="pre-commit run --all-files",
            estimated_duration="1-2 minutes",
            risk_mitigation="Prevents basic formatting and linting issues"
        ))

        # Component-specific recommendations
        for component in analysis.affected_components:
            if component in self.recommendation_rules:
                rules = self.recommendation_rules[component]

                for test_suite in rules["required_tests"]:
                    priority = self._calculate_priority(component, analysis.risk_level)

                    recommendations.append(TestRecommendation(
                        test_suite=test_suite,
                        priority=priority,
                        reason=f"Validate {component.lower().replace('_', ' ')} changes",
                        command=f"python -m pytest {test_suite} -v",
                        estimated_duration=self._estimate_test_duration(test_suite),
                        risk_mitigation=f"Ensures {component.lower()} functionality works correctly"
                    ))

        # Performance testing recommendations
        if self._requires_performance_testing(analysis):
            recommendations.append(TestRecommendation(
                test_suite="performance-benchmarks",
                priority="MEDIUM",
                reason="Validate performance impact of changes",
                command="python tests/performance/cli_path_resolution_benchmarks.py --benchmark",
                estimated_duration="2-3 minutes",
                risk_mitigation="Prevents performance regressions"
            ))

        # ACT testing recommendations
        if self._requires_act_testing(analysis):
            recommendations.append(TestRecommendation(
                test_suite="act-compatibility",
                priority="HIGH",
                reason="Ensure GitHub CI compatibility",
                command="./scripts/comprehensive-act-test.sh",
                estimated_duration="5-10 minutes",
                risk_mitigation="Validates GitHub Actions workflow compatibility"
            ))

        # Integration testing for complex changes
        if analysis.change_complexity in ["MEDIUM", "HIGH"]:
            recommendations.append(TestRecommendation(
                test_suite="integration-tests",
                priority="HIGH",
                reason="Validate end-to-end functionality",
                command="python -m pytest tests/test_cli_workflow_integration.py -v",
                estimated_duration="3-5 minutes",
                risk_mitigation="Ensures all components work together correctly"
            ))

        # Full validation for critical changes
        if analysis.risk_level == "CRITICAL":
            recommendations.append(TestRecommendation(
                test_suite="comprehensive-validation",
                priority="CRITICAL",
                reason="Critical changes require comprehensive validation",
                command="./scripts/validate-github-compatibility.sh",
                estimated_duration="10-15 minutes",
                risk_mitigation="Comprehensive validation before PR creation"
            ))

        return recommendations

    def _calculate_priority(self, component: str, risk_level: str) -> str:
        """Calculate test priority based on component and risk level."""
        critical_components = {"CLI", "PATH_RESOLUTION", "GITHUB_WORKFLOWS"}

        if component in critical_components and risk_level in ["HIGH", "CRITICAL"]:
            return "HIGH"
        elif component in critical_components or risk_level in ["HIGH", "CRITICAL"]:
            return "MEDIUM"
        else:
            return "LOW"

    def _estimate_test_duration(self, test_suite: str) -> str:
        """Estimate test execution duration."""
        duration_map = {
            "tests/test_path_resolution_comprehensive.py": "2-3 minutes",
            "tests/test_environment_documentation.py": "1-2 minutes",
            "tests/test_cli_enhancements.py": "3-4 minutes",
            "tests/test_cli_workflow_integration.py": "4-5 minutes",
            "tests/performance/cli_path_resolution_benchmarks.py": "2-3 minutes",
            "tests/": "5-10 minutes",
        }

        return duration_map.get(test_suite, "1-2 minutes")

    def _requires_performance_testing(self, analysis: ChangeAnalysis) -> bool:
        """Determine if performance testing is required."""
        performance_components = {"CLI", "PATH_RESOLUTION", "PERFORMANCE_TESTS"}
        return bool(analysis.affected_components.intersection(performance_components))

    def _requires_act_testing(self, analysis: ChangeAnalysis) -> bool:
        """Determine if ACT testing is required."""
        act_components = {"CLI", "PATH_RESOLUTION", "GITHUB_WORKFLOWS", "TESTING_SCRIPTS"}
        return (
            bool(analysis.affected_components.intersection(act_components)) or
            analysis.risk_level in ["HIGH", "CRITICAL"]
        )


class TestingReportGenerator:
    """Generates comprehensive testing reports and recommendations."""

    def __init__(self, project_root: Path):
        self.project_root = project_root

    def generate_testing_strategy(self, analysis: ChangeAnalysis) -> TestingStrategy:
        """Generate complete testing strategy."""
        engine = TestRecommendationEngine()
        recommendations = engine.generate_recommendations(analysis)

        # Calculate total estimated time
        total_minutes = self._calculate_total_time(recommendations)
        estimated_total_time = self._format_duration(total_minutes)

        # Calculate confidence level
        confidence_level = self._calculate_confidence_level(analysis, recommendations)

        # Determine if ACT and performance testing are needed
        act_testing_required = any("act" in rec.command for rec in recommendations)
        performance_testing_required = any("performance" in rec.command for rec in recommendations)

        return TestingStrategy(
            analysis=analysis,
            recommendations=recommendations,
            estimated_total_time=estimated_total_time,
            confidence_level=confidence_level,
            act_testing_required=act_testing_required,
            performance_testing_required=performance_testing_required
        )

    def _calculate_total_time(self, recommendations: List[TestRecommendation]) -> int:
        """Calculate total estimated time in minutes."""
        total_minutes = 0

        for rec in recommendations:
            # Extract minutes from duration strings like "2-3 minutes"
            duration = rec.estimated_duration
            if "minute" in duration:
                # Take the higher estimate for safety
                if "-" in duration:
                    high_estimate = duration.split("-")[1].split()[0]
                    try:
                        total_minutes += int(high_estimate)
                    except ValueError:
                        total_minutes += 5  # Default fallback
                else:
                    try:
                        total_minutes += int(duration.split()[0])
                    except ValueError:
                        total_minutes += 5  # Default fallback

        return total_minutes

    def _format_duration(self, minutes: int) -> str:
        """Format duration in human-readable format."""
        if minutes < 60:
            return f"{minutes} minutes"
        else:
            hours = minutes // 60
            remaining_minutes = minutes % 60
            if remaining_minutes == 0:
                return f"{hours} hour{'s' if hours > 1 else ''}"
            else:
                return f"{hours}h {remaining_minutes}m"

    def _calculate_confidence_level(self, analysis: ChangeAnalysis, recommendations: List[TestRecommendation]) -> str:
        """Calculate confidence level based on testing coverage."""
        high_priority_tests = len([r for r in recommendations if r.priority == "HIGH"])
        critical_tests = len([r for r in recommendations if r.priority == "CRITICAL"])

        if critical_tests > 0 or analysis.risk_level == "CRITICAL":
            return "COMPREHENSIVE_REQUIRED"
        elif high_priority_tests >= 3:
            return "HIGH_CONFIDENCE"
        elif high_priority_tests >= 1:
            return "MEDIUM_CONFIDENCE"
        else:
            return "BASIC_VALIDATION"

    def generate_report(self, strategy: TestingStrategy, output_format: str = "console") -> str:
        """Generate testing report in specified format."""
        if output_format == "json":
            return json.dumps(asdict(strategy), indent=2)
        elif output_format == "console":
            return self._generate_console_report(strategy)
        else:
            raise ValueError(f"Unsupported output format: {output_format}")

    def _generate_console_report(self, strategy: TestingStrategy) -> str:
        """Generate human-readable console report."""
        lines = []
        lines.append("🧪 ADRI Testing Recommendation Report")
        lines.append("=" * 50)
        lines.append("")

        # Change Analysis
        lines.append("📊 Change Analysis:")
        lines.append(f"   Modified files: {len(strategy.analysis.modified_files)}")
        lines.append(f"   Added files: {len(strategy.analysis.added_files)}")
        lines.append(f"   Deleted files: {len(strategy.analysis.deleted_files)}")
        lines.append(f"   Affected components: {', '.join(sorted(strategy.analysis.affected_components))}")
        lines.append(f"   Change complexity: {strategy.analysis.change_complexity}")
        lines.append(f"   Risk level: {strategy.analysis.risk_level}")
        lines.append("")

        # Testing Strategy
        lines.append("🎯 Recommended Testing Strategy:")
        lines.append(f"   Estimated total time: {strategy.estimated_total_time}")
        lines.append(f"   Confidence level: {strategy.confidence_level}")
        lines.append(f"   ACT testing required: {'Yes' if strategy.act_testing_required else 'No'}")
        lines.append(f"   Performance testing required: {'Yes' if strategy.performance_testing_required else 'No'}")
        lines.append("")

        # Prioritized Recommendations
        priority_order = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]

        for priority in priority_order:
            priority_recs = [r for r in strategy.recommendations if r.priority == priority]
            if priority_recs:
                lines.append(f"🔥 {priority} Priority Tests:")
                for rec in priority_recs:
                    lines.append(f"   • {rec.test_suite}")
                    lines.append(f"     Reason: {rec.reason}")
                    lines.append(f"     Command: {rec.command}")
                    lines.append(f"     Duration: {rec.estimated_duration}")
                    lines.append(f"     Risk mitigation: {rec.risk_mitigation}")
                    lines.append("")

        # Quick Start Commands
        lines.append("⚡ Quick Start Commands:")
        lines.append("=" * 25)

        if strategy.confidence_level in ["COMPREHENSIVE_REQUIRED"]:
            lines.append("🚨 CRITICAL CHANGES - Run comprehensive validation:")
            lines.append("   ./scripts/validate-github-compatibility.sh")
            lines.append("   ./scripts/comprehensive-act-test.sh")
        elif strategy.confidence_level == "HIGH_CONFIDENCE":
            lines.append("🎯 SIGNIFICANT CHANGES - Run enhanced validation:")
            lines.append("   ./scripts/validate-github-compatibility.sh --fast")
            lines.append("   ./scripts/local-ci-test.sh")
        else:
            lines.append("✅ MINOR CHANGES - Run basic validation:")
            lines.append("   ./scripts/validate-github-compatibility.sh --fast")

        lines.append("")
        lines.append("📚 Additional Resources:")
        lines.append("   • Testing documentation: docs/testing-framework.md")
        lines.append("   • Performance benchmarks: tests/performance/")
        lines.append("   • Mock fixtures: tests/fixtures/mock_projects.py")

        return "\n".join(lines)


def main():
    """Main entry point for the testing recommendation system."""
    parser = argparse.ArgumentParser(
        description="ADRI Automated Testing Recommendation System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze changes since last commit
  python scripts/test-recommendation-system.py

  # Analyze changes since specific commit
  python scripts/test-recommendation-system.py --since HEAD~3

  # Generate JSON report
  python scripts/test-recommendation-system.py --format json

  # Analyze specific files
  python scripts/test-recommendation-system.py --files src/adri/cli.py tests/test_path_resolution_comprehensive.py
        """
    )

    parser.add_argument(
        "--since",
        default="HEAD~1",
        help="Git commit to compare against (default: HEAD~1)"
    )

    parser.add_argument(
        "--format",
        choices=["console", "json"],
        default="console",
        help="Output format (default: console)"
    )

    parser.add_argument(
        "--files",
        nargs="*",
        help="Specific files to analyze (overrides git analysis)"
    )

    parser.add_argument(
        "--output",
        help="Output file path (default: stdout)"
    )

    args = parser.parse_args()

    # Determine project root
    project_root = Path.cwd()
    while project_root != project_root.parent:
        if (project_root / "ADRI" / "config.yaml").exists():
            break
        project_root = project_root.parent
    else:
        print("❌ Could not find ADRI project root")
        sys.exit(1)

    # Analyze changes
    analyzer = GitChangeAnalyzer(project_root)

    if args.files:
        # Analyze specific files
        analysis = ChangeAnalysis(
            modified_files=args.files,
            added_files=[],
            deleted_files=[],
            affected_components=analyzer._analyze_affected_components(args.files),
            change_complexity=analyzer._assess_change_complexity(args.files, [], []),
            risk_level=analyzer._assess_risk_level(analyzer._analyze_affected_components(args.files), "MEDIUM")
        )
    else:
        # Analyze git changes
        analysis = analyzer.get_git_changes(args.since)

    # Generate testing strategy
    report_generator = TestingReportGenerator(project_root)
    strategy = report_generator.generate_testing_strategy(analysis)

    # Generate report
    report = report_generator.generate_report(strategy, args.format)

    # Output report
    if args.output:
        with open(args.output, 'w') as f:
            f.write(report)
        print(f"📄 Report saved to: {args.output}")
    else:
        print(report)

    # Exit with appropriate code based on risk level
    if strategy.analysis.risk_level == "CRITICAL":
        print("\n🚨 CRITICAL risk level detected - comprehensive testing required before PR")
        sys.exit(2)
    elif strategy.analysis.risk_level == "HIGH":
        print("\n⚠️  HIGH risk level detected - thorough testing recommended")
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
