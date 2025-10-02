#!/usr/bin/env python3
"""
Test Threshold Audit Script

Systematically finds and categorizes all hardcoded thresholds in the test suite
to support threshold standardization initiative.
"""

import re
import os
import ast
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional, Tuple
from enum import Enum

class ThresholdCategory(Enum):
    """Categories of thresholds for systematic standardization"""
    TIMING_PARSING = "timing_parsing"
    TIMING_PROCESSING = "timing_processing"
    TIMING_WORKFLOW = "timing_workflow"
    QUALITY_SCORE = "quality_score"
    DIMENSION_SCORE = "dimension_score"
    MEMORY_USAGE = "memory_usage"
    BENCHMARK_PERFORMANCE = "benchmark_performance"
    OTHER = "other"

@dataclass
class ThresholdLocation:
    """Represents a hardcoded threshold found in the codebase"""
    file_path: str
    line_number: int
    line_content: str
    threshold_value: float
    operator: str  # '<', '>', '>=', '<=', '=='
    variable_name: str
    context: str  # surrounding function/test name
    category: Optional[ThresholdCategory] = None
    suggested_value: Optional[float] = None

@dataclass
class ThresholdAudit:
    """Complete audit results"""
    locations: List[ThresholdLocation] = field(default_factory=list)
    categories: Dict[ThresholdCategory, List[ThresholdLocation]] = field(default_factory=dict)
    files_processed: int = 0
    total_thresholds: int = 0

class ThresholdAuditor:
    """Systematic threshold auditing and categorization"""

    def __init__(self, test_directory: str = "tests"):
        self.test_dir = Path(test_directory)
        self.audit = ThresholdAudit()

        # Patterns for finding thresholds
        self.threshold_patterns = [
            # Timing assertions: assert duration < 3.0
            r'assert\s+(\w+(?:\.\w+)*)\s*([<>=!]+)\s*([0-9]+\.?[0-9]*)',
            # Quality score assertions: assert score >= 80.0
            r'assert\s+(\w+(?:\.\w+)*)\s*([<>=!]+)\s*([0-9]+\.?[0-9]*)',
            # Benchmark assertions: assert benchmark.stats.mean < 5.0
            r'assert\s+(benchmark\.[\w\.]+)\s*([<>=!]+)\s*([0-9]+\.?[0-9]*)',
            # Memory assertions: assert memory_mb < 100
            r'assert\s+(\w+(?:_mb|_memory|_size))\s*([<>=!]+)\s*([0-9]+\.?[0-9]*)'
        ]

        # Keywords that indicate threshold categories
        self.category_keywords = {
            ThresholdCategory.TIMING_PARSING: [
                'duration', 'time', 'parsing', 'load', 'config', 'elapsed', 'parse'
            ],
            ThresholdCategory.TIMING_PROCESSING: [
                'validation', 'process', 'generation', 'inference', 'profiling'
            ],
            ThresholdCategory.TIMING_WORKFLOW: [
                'workflow', 'pipeline', 'end_to_end', 'complete', 'batch'
            ],
            ThresholdCategory.QUALITY_SCORE: [
                'quality', 'score', 'assessment', 'overall', 'rating'
            ],
            ThresholdCategory.DIMENSION_SCORE: [
                'dimension', 'validity', 'completeness', 'accuracy'
            ],
            ThresholdCategory.MEMORY_USAGE: [
                'memory', 'mb', 'size', 'usage', 'bytes'
            ],
            ThresholdCategory.BENCHMARK_PERFORMANCE: [
                'benchmark', 'mean', 'stats', 'performance'
            ]
        }

    def find_all_thresholds(self) -> ThresholdAudit:
        """Find all hardcoded thresholds in the test suite"""
        print(f"Auditing thresholds in: {self.test_dir}")

        for py_file in self.test_dir.rglob("*.py"):
            if py_file.name.startswith("test_") or "test" in py_file.name:
                self._audit_file(py_file)
                self.audit.files_processed += 1

        self._categorize_thresholds()
        self._suggest_outer_limits()

        print(f"Audit complete: {self.audit.total_thresholds} thresholds found in {self.audit.files_processed} files")
        return self.audit

    def _audit_file(self, file_path: Path):
        """Audit a single Python test file for hardcoded thresholds"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            for line_num, line in enumerate(lines, 1):
                thresholds = self._extract_thresholds_from_line(
                    str(file_path), line_num, line.strip()
                )
                self.audit.locations.extend(thresholds)
                self.audit.total_thresholds += len(thresholds)

        except Exception as e:
            print(f"Error processing {file_path}: {e}")

    def _extract_thresholds_from_line(self, file_path: str, line_num: int, line: str) -> List[ThresholdLocation]:
        """Extract threshold values from a single line"""
        thresholds = []

        for pattern in self.threshold_patterns:
            matches = re.finditer(pattern, line)
            for match in matches:
                variable_name = match.group(1)
                operator = match.group(2)
                threshold_value = float(match.group(3))

                # Skip obviously non-threshold values
                if self._is_likely_threshold(variable_name, threshold_value, line):
                    context = self._get_function_context(file_path, line_num)

                    threshold = ThresholdLocation(
                        file_path=file_path,
                        line_number=line_num,
                        line_content=line.strip(),
                        threshold_value=threshold_value,
                        operator=operator,
                        variable_name=variable_name,
                        context=context
                    )
                    thresholds.append(threshold)

        return thresholds

    def _is_likely_threshold(self, variable_name: str, value: float, line: str) -> bool:
        """Filter out non-threshold numeric comparisons"""
        line_lower = line.lower()

        # Skip exact equality checks - these are usually testing specific expected values
        if '==' in line and 'score' not in line_lower and 'quality' not in line_lower:
            return False

        # Skip exit codes and call counts
        if any(keyword in line_lower for keyword in ['exit_code', 'call_count', 'result =', 'failed_result']):
            return False

        # Skip confidence scores (typically 0-1 range)
        if 'confidence' in line_lower and value <= 1.0:
            return False

        # Skip counts and exact matches
        if any(keyword in variable_name.lower() for keyword in ['count', 'code', 'result']):
            return False

        # Skip very small values that are likely not performance thresholds
        if value < 0.01:
            return False

        # Skip very large values that are unlikely to be performance thresholds
        if value > 10000:
            return False

        # Focus on genuine performance and quality thresholds
        performance_indicators = [
            # Timing thresholds
            'duration <', 'time <', 'elapsed <', '.mean <', 'too slow',
            # Quality score thresholds
            'score >=', 'score <=', 'score >', 'score <', 'quality_score',
            # Performance benchmarks
            'benchmark.stats', 'sla', 'performance',
            # Memory usage
            'memory', '_mb <', 'size <'
        ]

        return any(indicator in line_lower for indicator in performance_indicators)

    def _get_function_context(self, file_path: str, line_num: int) -> str:
        """Get the function/test name containing this threshold"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # Search backwards for function definition
            for i in range(line_num - 1, max(0, line_num - 20), -1):
                line = lines[i].strip()
                if line.startswith('def '):
                    func_match = re.match(r'def\s+(\w+)', line)
                    if func_match:
                        return func_match.group(1)

            return "unknown_function"

        except Exception:
            return "unknown_function"

    def _categorize_thresholds(self):
        """Categorize thresholds by their purpose"""
        for location in self.audit.locations:
            location.category = self._categorize_threshold(location)

            # Group by category
            if location.category not in self.audit.categories:
                self.audit.categories[location.category] = []
            self.audit.categories[location.category].append(location)

    def _categorize_threshold(self, location: ThresholdLocation) -> ThresholdCategory:
        """Categorize a single threshold based on context"""
        context_text = f"{location.variable_name} {location.context} {location.line_content}".lower()

        for category, keywords in self.category_keywords.items():
            if any(keyword in context_text for keyword in keywords):
                return category

        return ThresholdCategory.OTHER

    def _suggest_outer_limits(self):
        """Suggest reasonable outer limits for each threshold"""
        for location in self.audit.locations:
            location.suggested_value = self._calculate_outer_limit(location)

    def _calculate_outer_limit(self, location: ThresholdLocation) -> float:
        """Calculate a reasonable outer limit for a threshold"""
        current = location.threshold_value
        category = location.category

        # Suggested multipliers based on category
        multipliers = {
            ThresholdCategory.TIMING_PARSING: 5.0,      # 0.1s -> 0.5s, 3.0s -> 15.0s
            ThresholdCategory.TIMING_PROCESSING: 3.0,    # 10.0s -> 30.0s
            ThresholdCategory.TIMING_WORKFLOW: 2.0,      # 300.0s -> 600.0s
            ThresholdCategory.QUALITY_SCORE: 0.8,        # 90.0 -> 72.0 (reduce minimum)
            ThresholdCategory.DIMENSION_SCORE: 0.8,      # 15.0 -> 12.0 (reduce minimum)
            ThresholdCategory.MEMORY_USAGE: 2.0,         # 100MB -> 200MB
            ThresholdCategory.BENCHMARK_PERFORMANCE: 3.0, # Performance benchmarks
            ThresholdCategory.OTHER: 2.0                 # Conservative default
        }

        multiplier = multipliers.get(category, 2.0)

        # Special handling for quality scores (reduce minimums, increase maximums)
        if category in [ThresholdCategory.QUALITY_SCORE, ThresholdCategory.DIMENSION_SCORE]:
            if location.operator in ['>=', '>']:
                # For minimum thresholds, reduce the requirement
                return max(current * multiplier, 60.0 if category == ThresholdCategory.QUALITY_SCORE else 12.0)
            else:
                # For maximum thresholds, allow higher values
                return current * (2.0 - multiplier + 1.0)  # Increase ceiling

        return current * multiplier

    def generate_report(self) -> str:
        """Generate a comprehensive audit report"""
        report = ["# Test Threshold Audit Report\n"]
        report.append(f"**Total thresholds found:** {self.audit.total_thresholds}")
        report.append(f"**Files processed:** {self.audit.files_processed}\n")

        # Summary by category
        report.append("## Summary by Category\n")
        for category, locations in self.audit.categories.items():
            report.append(f"- **{category.value}**: {len(locations)} thresholds")

        # Detailed breakdown
        report.append("\n## Detailed Threshold Locations\n")
        for category, locations in self.audit.categories.items():
            if not locations:
                continue

            report.append(f"### {category.value.title().replace('_', ' ')} ({len(locations)} items)\n")

            for loc in locations:
                report.append(f"**File:** `{loc.file_path}:{loc.line_number}`")
                report.append(f"**Context:** `{loc.context}`")
                report.append(f"**Current:** `{loc.variable_name} {loc.operator} {loc.threshold_value}`")
                report.append(f"**Suggested:** `{loc.variable_name} {loc.operator} {loc.suggested_value:.1f}`")
                report.append(f"**Line:** `{loc.line_content}`\n")

        return "\n".join(report)

    def generate_replacement_script(self) -> str:
        """Generate a script to perform mass threshold replacements"""
        script = ['#!/usr/bin/env python3']
        script.append('"""Mass threshold replacement script"""')
        script.append('')
        script.append('import re')
        script.append('from pathlib import Path')
        script.append('')
        script.append('def replace_thresholds():')
        script.append('    """Replace all thresholds with suggested outer limits"""')
        script.append('    replacements = [')

        for location in self.audit.locations:
            # Create a replacement tuple
            old_pattern = f"{location.variable_name} {location.operator} {location.threshold_value}"
            new_pattern = f"{location.variable_name} {location.operator} {location.suggested_value:.1f}"

            script.append(f'        ("{location.file_path}", {location.line_number}, r"{re.escape(old_pattern)}", "{new_pattern}"),')

        script.append('    ]')
        script.append('')
        script.append('    for file_path, line_num, old_pattern, new_pattern in replacements:')
        script.append('        print(f"Updating {file_path}:{line_num}")')
        script.append('        # Implementation for actual replacement')
        script.append('')
        script.append('if __name__ == "__main__":')
        script.append('    replace_thresholds()')

        return '\n'.join(script)

def main():
    """Run the threshold audit"""
    auditor = ThresholdAuditor()
    audit_results = auditor.find_all_thresholds()

    # Generate and save report
    report = auditor.generate_report()
    with open('threshold_audit_report.md', 'w') as f:
        f.write(report)
    print("Report saved to: threshold_audit_report.md")

    # Generate replacement script
    replacement_script = auditor.generate_replacement_script()
    with open('scripts/replace_thresholds.py', 'w') as f:
        f.write(replacement_script)
    print("Replacement script saved to: scripts/replace_thresholds.py")

if __name__ == "__main__":
    main()
