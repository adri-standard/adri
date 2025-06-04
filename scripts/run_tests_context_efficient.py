#!/usr/bin/env python3
"""
Context-efficient test runner for ADRI project.

This script runs tests in batches and provides summarized output
to avoid overwhelming the context window while still providing
useful feedback on test results.
"""

import subprocess
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple
import os

class ContextEfficientTestRunner:
    """Run tests efficiently without overwhelming context."""
    
    def __init__(self):
        self.results = {}
        self.start_time = datetime.now()
        self.failed_tests = []
        self.passed_tests = []
        self.skipped_tests = []
        
    def run_test_group(self, name: str, test_path: str) -> Dict:
        """Run a group of tests and capture results."""
        print(f"\n{'='*60}")
        print(f"Running {name}...")
        print(f"{'='*60}")
        
        # Run pytest with JSON report
        cmd = [
            sys.executable, '-m', 'pytest',
            test_path,
            '-v',
            '--tb=short',
            '--json-report',
            '--json-report-file=/tmp/pytest_report.json',
            '-q'  # Quiet mode
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Parse results
        group_results = {
            'name': name,
            'path': test_path,
            'passed': 0,
            'failed': 0,
            'skipped': 0,
            'errors': 0,
            'duration': 0,
            'failures': []
        }
        
        # Try to load JSON report
        json_report_path = Path('/tmp/pytest_report.json')
        if json_report_path.exists():
            try:
                with open(json_report_path, 'r') as f:
                    report = json.load(f)
                    
                group_results['passed'] = report['summary'].get('passed', 0)
                group_results['failed'] = report['summary'].get('failed', 0)
                group_results['skipped'] = report['summary'].get('skipped', 0)
                group_results['errors'] = report['summary'].get('error', 0)
                group_results['duration'] = report.get('duration', 0)
                
                # Collect failed test details
                for test in report.get('tests', []):
                    if test['outcome'] == 'failed':
                        self.failed_tests.append({
                            'nodeid': test['nodeid'],
                            'group': name,
                            'message': test.get('call', {}).get('longrepr', 'No error message')[:200]
                        })
                    elif test['outcome'] == 'passed':
                        self.passed_tests.append(test['nodeid'])
                    elif test['outcome'] == 'skipped':
                        self.skipped_tests.append(test['nodeid'])
                        
            except Exception as e:
                print(f"Warning: Could not parse JSON report: {e}")
        
        # Fallback to parsing stdout if JSON fails
        if group_results['passed'] == 0 and group_results['failed'] == 0:
            output = result.stdout + result.stderr
            if 'passed' in output:
                try:
                    # Extract test counts from output
                    import re
                    passed_match = re.search(r'(\d+) passed', output)
                    failed_match = re.search(r'(\d+) failed', output)
                    skipped_match = re.search(r'(\d+) skipped', output)
                    
                    if passed_match:
                        group_results['passed'] = int(passed_match.group(1))
                    if failed_match:
                        group_results['failed'] = int(failed_match.group(1))
                    if skipped_match:
                        group_results['skipped'] = int(skipped_match.group(1))
                except:
                    pass
        
        # Print compact summary
        total = group_results['passed'] + group_results['failed'] + group_results['skipped']
        if total > 0:
            print(f"✓ Passed: {group_results['passed']}")
            if group_results['failed'] > 0:
                print(f"✗ Failed: {group_results['failed']}")
            if group_results['skipped'] > 0:
                print(f"- Skipped: {group_results['skipped']}")
            print(f"Duration: {group_results['duration']:.2f}s")
        else:
            print("No tests found or unable to parse results")
            
        return group_results
    
    def run_all_tests(self):
        """Run all test groups."""
        # Define test groups
        test_groups = [
            # Unit tests
            ("Unit: Core", "tests/unit/test_assessor.py tests/unit/test_report.py"),
            ("Unit: Dimensions", "tests/unit/dimensions/"),
            ("Unit: Rules", "tests/unit/rules/"),
            ("Unit: Templates", "tests/unit/templates/"),
            ("Unit: Examples", "tests/unit/examples/"),
            ("Unit: Other", "tests/unit/test_assessment_modes.py tests/unit/test_error_handling.py"),
            
            # Integration tests
            ("Integration: Core", "tests/integration/test_cli.py tests/integration/test_version_integration.py"),
            ("Integration: Templates", "tests/integration/templates/"),
            ("Integration: Scenarios", "tests/integration/scenarios/"),
            
            # Infrastructure tests
            ("Infrastructure", "tests/infrastructure/"),
        ]
        
        # Run each group
        for name, path in test_groups:
            if not Path(path.split()[0]).exists():
                print(f"\nSkipping {name} - path not found: {path}")
                continue
                
            self.results[name] = self.run_test_group(name, path)
        
        # Print final summary
        self.print_summary()
    
    def print_summary(self):
        """Print a comprehensive summary."""
        duration = (datetime.now() - self.start_time).total_seconds()
        
        print(f"\n{'='*60}")
        print("TEST SUMMARY")
        print(f"{'='*60}")
        
        total_passed = sum(r['passed'] for r in self.results.values())
        total_failed = sum(r['failed'] for r in self.results.values())
        total_skipped = sum(r['skipped'] for r in self.results.values())
        total_tests = total_passed + total_failed + total_skipped
        
        print(f"\nTotal Tests: {total_tests}")
        print(f"✓ Passed: {total_passed} ({total_passed/total_tests*100:.1f}%)")
        print(f"✗ Failed: {total_failed} ({total_failed/total_tests*100:.1f}%)")
        print(f"- Skipped: {total_skipped} ({total_skipped/total_tests*100:.1f}%)")
        print(f"\nTotal Duration: {duration:.2f}s")
        
        # Show failed tests if any
        if self.failed_tests:
            print(f"\n{'='*60}")
            print(f"FAILED TESTS ({len(self.failed_tests)})")
            print(f"{'='*60}")
            for test in self.failed_tests[:10]:  # Show first 10
                print(f"\n{test['group']}: {test['nodeid']}")
                print(f"  Error: {test['message']}")
            
            if len(self.failed_tests) > 10:
                print(f"\n... and {len(self.failed_tests) - 10} more failed tests")
        
        # Group summary
        print(f"\n{'='*60}")
        print("GROUP SUMMARY")
        print(f"{'='*60}")
        print(f"{'Group':<30} {'Pass':<8} {'Fail':<8} {'Skip':<8} {'Time':<8}")
        print("-" * 60)
        
        for name, results in self.results.items():
            status = "✓" if results['failed'] == 0 else "✗"
            print(f"{status} {name:<28} {results['passed']:<8} {results['failed']:<8} {results['skipped']:<8} {results['duration']:.1f}s")
        
        # Exit code
        sys.exit(0 if total_failed == 0 else 1)

def main():
    """Main entry point."""
    runner = ContextEfficientTestRunner()
    
    # Check for specific test group argument
    if len(sys.argv) > 1:
        test_path = sys.argv[1]
        runner.results['custom'] = runner.run_test_group("Custom Tests", test_path)
        runner.print_summary()
    else:
        runner.run_all_tests()

if __name__ == "__main__":
    main()
