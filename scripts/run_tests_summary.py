#!/usr/bin/env python
"""
Enhanced test runner that provides compact summaries to avoid context window overflow.

Features:
- Groups test results by category
- Shows only essential failure information
- Provides actionable summaries
- Tracks progress without verbose output
"""

import subprocess
import sys
import json
import re
from pathlib import Path
from collections import defaultdict
import time

def run_tests_with_summary(test_path=".", max_failures_shown=10):
    """Run tests and provide a compact summary."""
    
    print("Running tests with context-efficient summary...")
    print("-" * 60)
    
    # Run pytest with JSON output
    cmd = [
        sys.executable, "-m", "pytest",
        test_path,
        "--tb=short",
        "--json-report",
        "--json-report-file=test_report.json",
        "-q"  # Quiet mode
    ]
    
    # Show progress dots
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=1
    )
    
    # Track progress without storing all output
    test_count = 0
    for line in process.stdout:
        if '.' in line or 'F' in line or 's' in line:
            # Show progress indicators
            sys.stdout.write('.')
            sys.stdout.flush()
            test_count += 1
            if test_count % 50 == 0:
                sys.stdout.write(f' [{test_count}]\n')
                sys.stdout.flush()
    
    process.wait()
    print("\n")
    
    # Parse results from JSON report
    try:
        with open('test_report.json', 'r') as f:
            report = json.load(f)
    except:
        # Fallback to basic pytest run if json report fails
        return run_basic_summary(test_path)
    
    # Analyze results
    summary = analyze_test_results(report, max_failures_shown)
    
    # Clean up
    Path('test_report.json').unlink(missing_ok=True)
    
    return summary

def run_basic_summary(test_path):
    """Fallback method using basic pytest output."""
    cmd = [
        sys.executable, "-m", "pytest",
        test_path,
        "--tb=no",
        "-q",
        "--no-header"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    # Parse basic output
    output_lines = result.stdout.strip().split('\n')
    summary_line = output_lines[-1] if output_lines else ""
    
    # Extract counts
    passed = failed = skipped = 0
    if "passed" in summary_line:
        passed = int(re.search(r'(\d+) passed', summary_line).group(1))
    if "failed" in summary_line:
        failed = int(re.search(r'(\d+) failed', summary_line).group(1))
    if "skipped" in summary_line:
        skipped = int(re.search(r'(\d+) skipped', summary_line).group(1))
    
    print("\n" + "="*60)
    print("TEST SUMMARY (Basic Mode)")
    print("="*60)
    print(f"Total Tests: {passed + failed + skipped}")
    print(f"Passed:  {passed}")
    print(f"Failed:  {failed}")
    print(f"Skipped: {skipped}")
    
    if failed > 0:
        print("\nRun with -v flag for detailed failure information")
    
    return result.returncode

def analyze_test_results(report, max_failures_shown):
    """Analyze test results and provide actionable summary."""
    
    summary = report.get('summary', {})
    tests = report.get('tests', [])
    
    # Group failures by module
    failures_by_module = defaultdict(list)
    for test in tests:
        if test['outcome'] == 'failed':
            module = test['nodeid'].split('::')[0]
            failures_by_module[module].append(test)
    
    # Print summary
    print("="*60)
    print("TEST EXECUTION SUMMARY")
    print("="*60)
    print(f"Total Tests: {summary.get('total', 0)}")
    print(f"Passed:  {summary.get('passed', 0)}")
    print(f"Failed:  {summary.get('failed', 0)}")
    print(f"Skipped: {summary.get('skipped', 0)}")
    print(f"Duration: {summary.get('duration', 0):.2f}s")
    
    if failures_by_module:
        print("\n" + "="*60)
        print("FAILURES BY MODULE")
        print("="*60)
        
        for module, failures in sorted(failures_by_module.items()):
            print(f"\n{module}: {len(failures)} failures")
            
            # Show first few failures from each module
            for i, test in enumerate(failures[:3]):
                test_name = test['nodeid'].split('::')[-1]
                print(f"  - {test_name}")
                
                # Extract key error info
                if 'call' in test:
                    error_msg = extract_error_summary(test['call'])
                    if error_msg:
                        print(f"    → {error_msg}")
            
            if len(failures) > 3:
                print(f"  ... and {len(failures) - 3} more")
    
    # Provide actionable next steps
    if summary.get('failed', 0) > 0:
        print("\n" + "="*60)
        print("RECOMMENDED ACTIONS")
        print("="*60)
        
        # Group by common failure patterns
        common_issues = identify_common_issues(tests)
        
        for issue_type, count in common_issues.items():
            print(f"\n{issue_type}: {count} occurrences")
            print(f"  → {get_fix_suggestion(issue_type)}")
    
    return 0 if summary.get('failed', 0) == 0 else 1

def extract_error_summary(call_info):
    """Extract concise error message from test call info."""
    if 'longrepr' in call_info:
        longrepr = call_info['longrepr']
        
        # Try to get the assertion error
        if isinstance(longrepr, str):
            lines = longrepr.split('\n')
            for line in lines:
                if 'AssertionError:' in line:
                    return line.split('AssertionError:')[1].strip()[:80]
                elif 'assert' in line and '==' in line:
                    return line.strip()[:80]
        
        # Fallback to last line
        if isinstance(longrepr, str):
            last_line = longrepr.strip().split('\n')[-1]
            return last_line[:80] if last_line else None
    
    return None

def identify_common_issues(tests):
    """Identify common failure patterns."""
    issues = defaultdict(int)
    
    for test in tests:
        if test['outcome'] == 'failed' and 'call' in test:
            longrepr = test['call'].get('longrepr', '')
            if isinstance(longrepr, str):
                # Categorize common issues
                if 'AttributeError' in longrepr:
                    issues['AttributeError'] += 1
                elif 'KeyError' in longrepr:
                    issues['KeyError'] += 1
                elif 'score' in longrepr.lower():
                    issues['Score Assertion Failures'] += 1
                elif 'metadata' in longrepr.lower():
                    issues['Metadata Loading Issues'] += 1
                elif 'not found' in longrepr.lower():
                    issues['File/Resource Not Found'] += 1
                else:
                    issues['Other Assertion Failures'] += 1
    
    return issues

def get_fix_suggestion(issue_type):
    """Provide fix suggestions for common issues."""
    suggestions = {
        'AttributeError': 'Check object attributes and API changes',
        'KeyError': 'Verify dictionary keys and data structures',
        'Score Assertion Failures': 'Review scoring logic and thresholds',
        'Metadata Loading Issues': 'Check metadata file paths and formats',
        'File/Resource Not Found': 'Verify file paths and test data',
        'Other Assertion Failures': 'Review test expectations and logic'
    }
    return suggestions.get(issue_type, 'Review test implementation')

def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run tests with compact summary')
    parser.add_argument('path', nargs='?', default='.', 
                       help='Path to test directory or file')
    parser.add_argument('--max-failures', type=int, default=10,
                       help='Maximum failures to show in detail')
    
    args = parser.parse_args()
    
    try:
        exit_code = run_tests_with_summary(args.path, args.max_failures)
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nTest run interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError running tests: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
