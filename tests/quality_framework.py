"""
ADRI Quality Framework for Multi-Dimensional Test Assessment.

Implements the multi-dimensional quality measurement system as defined in ARCHITECTURE.md:
- Line Coverage: Traditional code coverage metrics (target 80%)
- Integration Tests: Component interaction and end-to-end scenarios
- Error Handling: Failure modes, edge cases, and recovery scenarios
- Performance: Speed, efficiency, and resource usage under load

Component Quality Targets:
- Business Critical (Guard Decorator, Validator Engine, Protection Modes): 90%+ overall quality
- System Infrastructure (Config, Standards, CLI, Local Logging): 80%+ overall quality
- Data Processing (Profiler, Generator, Type Inference, Enterprise Logging): 75%+ overall quality
"""

from enum import Enum
from typing import Dict, List, Literal, TypedDict, Any, Optional
import time
import sys
import tracemalloc
from contextlib import contextmanager


class TestCategory(Enum):
    """Test execution categories for comprehensive coverage."""
    UNIT = "unit"
    INTEGRATION = "integration"
    PERFORMANCE = "performance"
    BENCHMARK = "benchmark"
    ERROR_HANDLING = "error_handling"
    END_TO_END = "end_to_end"


class QualityMetrics(TypedDict):
    """Multi-dimensional quality metrics for component assessment."""
    line_coverage: float
    integration_tests: float
    error_handling: float
    performance: float
    overall_score: float


class ComponentTarget(TypedDict):
    """Quality targets for different component types."""
    component_type: Literal["business_critical", "system_infrastructure", "data_processing", "supporting_infrastructure"]
    line_coverage_target: float
    integration_target: float
    error_handling_target: float
    performance_target: float
    overall_target: float


class TestConfig(TypedDict):
    """Configuration for comprehensive test execution."""
    category: TestCategory
    component: str
    quality_target: ComponentTarget
    fixtures_required: List[str]
    mock_patterns: List[str]


# Component Quality Targets as defined in ARCHITECTURE.md
COMPONENT_TARGETS: Dict[str, ComponentTarget] = {
    # Business Critical Components (90%+ overall quality)
    "decorator": {
        "component_type": "business_critical",
        "line_coverage_target": 95.0,
        "integration_target": 90.0,
        "error_handling_target": 95.0,
        "performance_target": 85.0,
        "overall_target": 90.0
    },
    "validator_engine": {
        "component_type": "business_critical",
        "line_coverage_target": 95.0,
        "integration_target": 90.0,
        "error_handling_target": 95.0,
        "performance_target": 85.0,
        "overall_target": 90.0
    },
    "guard_modes": {
        "component_type": "business_critical",
        "line_coverage_target": 95.0,
        "integration_target": 90.0,
        "error_handling_target": 95.0,
        "performance_target": 85.0,
        "overall_target": 90.0
    },

    # System Infrastructure Components (80%+ overall quality)
    "config_loader": {
        "component_type": "system_infrastructure",
        "line_coverage_target": 85.0,
        "integration_target": 80.0,
        "error_handling_target": 85.0,
        "performance_target": 75.0,
        "overall_target": 80.0
    },
    "standards_parser": {
        "component_type": "system_infrastructure",
        "line_coverage_target": 85.0,
        "integration_target": 80.0,
        "error_handling_target": 85.0,
        "performance_target": 75.0,
        "overall_target": 80.0
    },
    "cli_commands": {
        "component_type": "system_infrastructure",
        "line_coverage_target": 85.0,
        "integration_target": 80.0,
        "error_handling_target": 85.0,
        "performance_target": 75.0,
        "overall_target": 80.0
    },
    "local_logging": {
        "component_type": "system_infrastructure",
        "line_coverage_target": 85.0,
        "integration_target": 80.0,
        "error_handling_target": 85.0,
        "performance_target": 75.0,
        "overall_target": 80.0
    },

    # Data Processing Components (75%+ overall quality)
    "data_profiler": {
        "component_type": "data_processing",
        "line_coverage_target": 80.0,
        "integration_target": 75.0,
        "error_handling_target": 80.0,
        "performance_target": 70.0,
        "overall_target": 75.0
    },
    "standard_generator": {
        "component_type": "data_processing",
        "line_coverage_target": 80.0,
        "integration_target": 75.0,
        "error_handling_target": 80.0,
        "performance_target": 70.0,
        "overall_target": 75.0
    },
    "type_inference": {
        "component_type": "data_processing",
        "line_coverage_target": 80.0,
        "integration_target": 75.0,
        "error_handling_target": 80.0,
        "performance_target": 70.0,
        "overall_target": 75.0
    },
    "enterprise_logging": {
        "component_type": "data_processing",
        "line_coverage_target": 80.0,
        "integration_target": 75.0,
        "error_handling_target": 80.0,
        "performance_target": 70.0,
        "overall_target": 75.0
    }
}


class QualityFramework:
    """Multi-dimensional quality measurement framework for ADRI components."""

    def __init__(self):
        self.component_targets = COMPONENT_TARGETS
        self.test_results: Dict[str, QualityMetrics] = {}

    def calculate_quality_score(
        self,
        line_coverage: float,
        integration_tests: float,
        error_handling: float,
        performance: float,
        weights: Optional[Dict[str, float]] = None
    ) -> float:
        """Calculate overall quality score from multi-dimensional metrics."""
        if weights is None:
            # Default weights based on ARCHITECTURE.md priorities
            weights = {
                "line_coverage": 0.30,     # 30% - Traditional coverage
                "integration_tests": 0.25,  # 25% - Component interactions
                "error_handling": 0.25,     # 25% - Failure scenarios
                "performance": 0.20         # 20% - Efficiency metrics
            }

        overall_score = (
            line_coverage * weights["line_coverage"] +
            integration_tests * weights["integration_tests"] +
            error_handling * weights["error_handling"] +
            performance * weights["performance"]
        )

        return round(overall_score, 2)

    def validate_component_quality(self, component_name: str, metrics: QualityMetrics) -> bool:
        """Validate component quality against defined targets."""
        if component_name not in self.component_targets:
            raise ValueError(f"Unknown component: {component_name}")

        target = self.component_targets[component_name]

        # Check each dimension against targets
        checks = {
            "line_coverage": metrics["line_coverage"] >= target["line_coverage_target"],
            "integration_tests": metrics["integration_tests"] >= target["integration_target"],
            "error_handling": metrics["error_handling"] >= target["error_handling_target"],
            "performance": metrics["performance"] >= target["performance_target"],
            "overall_score": metrics["overall_score"] >= target["overall_target"]
        }

        return all(checks.values())

    def get_component_target(self, component_name: str) -> ComponentTarget:
        """Get quality targets for a specific component."""
        if component_name not in self.component_targets:
            raise ValueError(f"Unknown component: {component_name}")
        return self.component_targets[component_name]

    def record_test_result(self, component_name: str, metrics: QualityMetrics):
        """Record test results for a component."""
        self.test_results[component_name] = metrics

    def generate_quality_report(self) -> Dict[str, Any]:
        """Generate comprehensive quality report for all tested components."""
        report = {
            "overall_coverage": 0.0,
            "components_tested": len(self.test_results),
            "components_passing": 0,
            "component_details": {},
            "summary": {}
        }

        total_coverage = 0
        passing_components = 0

        for component_name, metrics in self.test_results.items():
            target = self.component_targets.get(component_name)
            if not target:
                continue

            is_passing = self.validate_component_quality(component_name, metrics)
            if is_passing:
                passing_components += 1

            total_coverage += metrics["line_coverage"]

            report["component_details"][component_name] = {
                "metrics": metrics,
                "target": target,
                "passing": is_passing,
                "gaps": {
                    "line_coverage": max(0, target["line_coverage_target"] - metrics["line_coverage"]),
                    "integration_tests": max(0, target["integration_target"] - metrics["integration_tests"]),
                    "error_handling": max(0, target["error_handling_target"] - metrics["error_handling"]),
                    "performance": max(0, target["performance_target"] - metrics["performance"])
                }
            }

        if self.test_results:
            report["overall_coverage"] = round(total_coverage / len(self.test_results), 2)

        report["components_passing"] = passing_components
        report["summary"] = {
            "pass_rate": round((passing_components / len(self.test_results)) * 100, 2) if self.test_results else 0,
            "target_80_percent_met": report["overall_coverage"] >= 80.0,
            "production_ready": report["overall_coverage"] >= 80.0 and passing_components == len(self.test_results)
        }

        return report


class ComponentTester:
    """Standardized component testing framework."""

    def __init__(self, component_name: str, quality_framework: QualityFramework):
        self.component_name = component_name
        self.quality_framework = quality_framework
        self.target = quality_framework.get_component_target(component_name)

        # Metrics tracking
        self.line_coverage = 0.0
        self.integration_score = 0.0
        self.error_handling_score = 0.0
        self.performance_score = 0.0

        # Test execution tracking
        self.tests_executed = 0
        self.tests_passed = 0
        self.integration_tests = 0
        self.error_handling_tests = 0
        self.performance_tests = 0

    def record_test_execution(self, test_category: TestCategory, passed: bool):
        """Record test execution results."""
        self.tests_executed += 1
        if passed:
            self.tests_passed += 1

        if test_category == TestCategory.INTEGRATION:
            self.integration_tests += 1
        elif test_category == TestCategory.ERROR_HANDLING:
            self.error_handling_tests += 1
        elif test_category in [TestCategory.PERFORMANCE, TestCategory.BENCHMARK]:
            self.performance_tests += 1

    def calculate_metrics(self, line_coverage: float) -> QualityMetrics:
        """Calculate comprehensive quality metrics for the component."""
        # Line coverage from external measurement
        self.line_coverage = line_coverage

        # Integration score based on test execution
        if self.integration_tests > 0:
            self.integration_score = min(100.0, (self.integration_tests / max(1, self.tests_executed)) * 100)

        # Error handling score
        if self.error_handling_tests > 0:
            self.error_handling_score = min(100.0, (self.error_handling_tests / max(1, self.tests_executed)) * 100)

        # Performance score based on benchmarks
        if self.performance_tests > 0:
            self.performance_score = min(100.0, (self.performance_tests / max(1, self.tests_executed)) * 100)

        # Calculate overall score
        overall_score = self.quality_framework.calculate_quality_score(
            self.line_coverage,
            self.integration_score,
            self.error_handling_score,
            self.performance_score
        )

        metrics: QualityMetrics = {
            "line_coverage": self.line_coverage,
            "integration_tests": self.integration_score,
            "error_handling": self.error_handling_score,
            "performance": self.performance_score,
            "overall_score": overall_score
        }

        return metrics

    def finalize_component_testing(self, line_coverage: float) -> bool:
        """Finalize component testing and validate against targets."""
        metrics = self.calculate_metrics(line_coverage)
        self.quality_framework.record_test_result(self.component_name, metrics)
        return self.quality_framework.validate_component_quality(self.component_name, metrics)


@contextmanager
def performance_monitor():
    """Context manager for performance monitoring during tests."""
    tracemalloc.start()
    start_time = time.time()
    start_memory = tracemalloc.get_traced_memory()[0]

    try:
        yield
    finally:
        end_time = time.time()
        end_memory = tracemalloc.get_traced_memory()[0]
        tracemalloc.stop()

        execution_time = end_time - start_time
        memory_delta = end_memory - start_memory

        # Store performance metrics (simplified for now)
        performance_data = {
            "execution_time": execution_time,
            "memory_delta": memory_delta,
            "memory_peak": tracemalloc.get_traced_memory()[1]
        }


def create_test_config(
    category: TestCategory,
    component: str,
    fixtures_required: Optional[List[str]] = None,
    mock_patterns: Optional[List[str]] = None
) -> TestConfig:
    """Create standardized test configuration."""
    quality_framework = QualityFramework()

    if component not in COMPONENT_TARGETS:
        raise ValueError(f"Unknown component: {component}")

    return {
        "category": category,
        "component": component,
        "quality_target": COMPONENT_TARGETS[component],
        "fixtures_required": fixtures_required or [],
        "mock_patterns": mock_patterns or []
    }


# Global quality framework instance for test execution
quality_framework = QualityFramework()
