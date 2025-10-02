#!/usr/bin/env python3
"""
Realistic Threshold Adjustment (2x Actual Performance)

Sets thresholds to 2x actual measured performance for aggressive
production-quality validation.
"""

import re
from pathlib import Path

class RealisticThresholdAdjuster:
    """Set thresholds to 2x actual measured performance"""

    def __init__(self):
        # 2x actual performance measured from benchmarks
        self.realistic_thresholds = {
            # Micro-operations: 2x actual performance
            15.0: 0.003,   # Validator: 1.2ms actual -> 3ms threshold
            60.0: 0.030,   # Profiler: 13.7ms actual -> 30ms threshold
            20.0: 0.040,   # Type inference: ~20ms actual -> 40ms threshold

            # Standard generation: 2x actual
            60.0: 0.200,   # Generator: 100.6ms actual -> 200ms threshold (when not profiler)

            # Configuration operations: 2x reasonable estimates
            10.0: 0.100,   # Config loading: ~50ms actual -> 100ms threshold
            15.0: 0.200,   # Parsing: ~100ms actual -> 200ms threshold

            # SLA operations: 2x actual (all completed in <1s)
            15.0: 2.0,     # Assessment SLA: <1s actual -> 2s threshold
            90.0: 2.0,     # Profiling SLA: <1s actual -> 2s threshold

            # Workflow operations: 2x actual
            120.0: 3.0,    # Complete workflow: ~1.5s actual -> 3s threshold
            180.0: 10.0,   # Stress testing: ~5s estimated -> 10s threshold
            300.0: 20.0,   # Large operations: ~10s estimated -> 20s threshold
        }

    def adjust_file_thresholds(self, file_path: str) -> int:
        """Adjust thresholds in a single file to 2x actual performance"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            original_content = content
            replacement_count = 0

            # Apply realistic threshold adjustments
            for old_value, new_value in self.realistic_thresholds.items():
                # Multiple patterns to catch different assertion formats
                patterns = [
                    # Benchmark assertions
                    (rf'(benchmark\.stats\.stats\.mean\s*<\s*){old_value}\.0', rf'\g<1>{new_value}'),
                    (rf'(benchmark\.stats\.stats\.mean\s*<\s*){old_value}', rf'\g<1>{new_value}'),
                    # Duration assertions
                    (rf'(\w*duration\w*\s*<\s*){old_value}\.0', rf'\g<1>{new_value}'),
                    (rf'(\w*duration\w*\s*<\s*){old_value}', rf'\g<1>{new_value}'),
                    # Time assertions
                    (rf'(\w*time\w*\s*<\s*){old_value}\.0', rf'\g<1>{new_value}'),
                    (rf'(\w*time\w*\s*<\s*){old_value}', rf'\g<1>{new_value}'),
                    # Generic assert patterns
                    (rf'(assert\s+\w+\s*<\s*){old_value}\.0', rf'\g<1>{new_value}'),
                    (rf'(assert\s+\w+\s*<\s*){old_value}', rf'\g<1>{new_value}'),
                ]

                for pattern, replacement in patterns:
                    content, count = re.subn(pattern, replacement, content)
                    replacement_count += count

            # Write back if changes made
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)

            return replacement_count

        except Exception as e:
            print(f"Error adjusting {file_path}: {e}")
            return 0

    def adjust_all_thresholds(self) -> dict:
        """Adjust all test files to realistic 2x performance thresholds"""
        files_to_adjust = [
            'tests/performance/test_quality_benchmarks.py',
            'tests/unit/analysis/test_data_profiler_comprehensive.py',
            'tests/unit/standards/test_parser_comprehensive.py',
            'tests/unit/config/test_loader_comprehensive.py',
            'tests/unit/validator/test_engine_comprehensive.py',
            'tests/integration/test_component_interactions.py',
            'tests/integration/test_end_to_end_workflows.py'
        ]

        results = {}
        for file_path in files_to_adjust:
            if Path(file_path).exists():
                count = self.adjust_file_thresholds(file_path)
                if count > 0:
                    results[file_path] = count
                    print(f"Applied 2x realistic thresholds: {count} in {file_path}")

        return results

def main():
    """Apply aggressive 2x actual performance thresholds"""
    print("Applying realistic 2x performance thresholds...")
    print("This will set very aggressive limits based on actual measured performance.")

    adjuster = RealisticThresholdAdjuster()
    results = adjuster.adjust_all_thresholds()

    total = sum(results.values())
    print(f"\nRealistic Threshold Summary:")
    print(f"Files updated: {len(results)}")
    print(f"Total adjustments: {total}")

    if results:
        print(f"\nUpdated files:")
        for file_path, count in results.items():
            print(f"  {file_path}: {count} thresholds")

    print(f"\nRealistic 2x performance thresholds applied!")
    print(f"New thresholds:")
    print(f"  - Micro-operations: 3-200ms (was 15-60s)")
    print(f"  - SLA operations: 2s (was 15-90s)")
    print(f"  - Workflows: 3-20s (was 120-300s)")

if __name__ == "__main__":
    main()
