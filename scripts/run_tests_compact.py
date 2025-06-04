#!/usr/bin/env python3
"""
Compact test runner that avoids context window issues.

This script runs tests with minimal output and provides summary reports
to prevent exceeding context windows during AI-assisted development.
"""

import subprocess
import sys
import json
import time
from pathlib import Path
from typing import Optional, List, Dict, Any


class CompactTestRunner:
    """Run tests with compact output suitable for AI context windows."""
    
    def __init__(self, output_dir: str = "test_results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
    def run_tests(
        self, 
        test_path: Optional[str] = None,
        markers: Optional[str] = None,
        quiet: bool = True,
        capture_output: bool = True
    ) -> Dict[str, Any]:
        """
        Run tests with compact output.
        
        Args:
            test_path: Specific test file or directory to run
            markers: Pytest markers to filter tests
            quiet: Run in quiet mode
            capture_output: Capture output to file
            
        Returns:
            Test results summary
        """
        # Build pytest command
        cmd = ["python3", "-m", "pytest"]
        
        # Add json output for parsing
        json_output = self.output_dir / f"test_results_{int(time.time())}.json"
        cmd.extend(["--json-report", f"--json-report-file={json_output}"])
        
        # Add quiet options
        if quiet:
            cmd.extend(["-q", "--tb=short", "--no-header"])
        
        # Add test path if specified
        if test_path:
            cmd.append(test_path)
            
        # Add markers if specified
        if markers:
            cmd.extend(["-m", markers])
            
        # Run tests
        if capture_output:
            # Capture to file
            stdout_file = self.output_dir / f"test_output_{int(time.time())}.txt"
            with open(stdout_file, "w") as f:
                result = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT)
        else:
            # Run normally but with minimal output
            result = subprocess.run(cmd)
            
        # Parse results
        summary = self._parse_results(json_output if json_output.exists() else None, result.returncode)
        
        # Print compact summary
        self._print_summary(summary)
        
        return summary
        
    def run_test_groups(self, groups: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Run multiple test groups sequentially.
        
        Args:
            groups: List of test group configurations
            
        Returns:
            Combined results summary
        """
        all_results = {
            "total_passed": 0,
            "total_failed": 0,
            "total_skipped": 0,
            "groups": []
        }
        
        for group in groups:
            print(f"\n{'='*60}")
            print(f"Running: {group.get('name', 'Tests')}")
            print(f"{'='*60}")
            
            result = self.run_tests(
                test_path=group.get("path"),
                markers=group.get("markers"),
                quiet=group.get("quiet", True)
            )
            
            all_results["total_passed"] += result.get("passed", 0)
            all_results["total_failed"] += result.get("failed", 0)
            all_results["total_skipped"] += result.get("skipped", 0)
            all_results["groups"].append({
                "name": group.get("name"),
                "result": result
            })
            
        self._print_final_summary(all_results)
        return all_results
        
    def _parse_results(self, json_file: Optional[Path], return_code: int) -> Dict[str, Any]:
        """Parse test results from JSON output."""
        if json_file and json_file.exists():
            try:
                with open(json_file) as f:
                    data = json.load(f)
                    return {
                        "passed": data["summary"].get("passed", 0),
                        "failed": data["summary"].get("failed", 0),
                        "skipped": data["summary"].get("skipped", 0),
                        "total": data["summary"].get("total", 0),
                        "duration": data.get("duration", 0),
                        "failures": self._extract_failures(data)
                    }
            except:
                pass
                
        # Fallback for when JSON parsing fails
        return {
            "passed": 0 if return_code != 0 else "unknown",
            "failed": "unknown",
            "skipped": 0,
            "total": "unknown",
            "return_code": return_code
        }
        
    def _extract_failures(self, data: Dict) -> List[str]:
        """Extract failure information."""
        failures = []
        for test in data.get("tests", []):
            if test["outcome"] == "failed":
                failures.append({
                    "nodeid": test["nodeid"],
                    "message": test.get("call", {}).get("longrepr", "No details")[:200]  # Truncate long messages
                })
        return failures
        
    def _print_summary(self, summary: Dict[str, Any]):
        """Print a compact test summary."""
        print("\n" + "-" * 40)
        print("TEST SUMMARY")
        print("-" * 40)
        print(f"Passed:  {summary.get('passed', 'unknown')}")
        print(f"Failed:  {summary.get('failed', 'unknown')}")
        print(f"Skipped: {summary.get('skipped', 'unknown')}")
        
        if summary.get("failures"):
            print("\nFAILURES:")
            for failure in summary["failures"][:5]:  # Show max 5 failures
                print(f"  - {failure['nodeid']}")
                
    def _print_final_summary(self, results: Dict[str, Any]):
        """Print final summary for all test groups."""
        print("\n" + "=" * 60)
        print("FINAL TEST SUMMARY")
        print("=" * 60)
        print(f"Total Passed:  {results['total_passed']}")
        print(f"Total Failed:  {results['total_failed']}")
        print(f"Total Skipped: {results['total_skipped']}")
        
        if any(g["result"].get("failed", 0) > 0 for g in results["groups"]):
            print("\nFailed Groups:")
            for group in results["groups"]:
                if group["result"].get("failed", 0) > 0:
                    print(f"  - {group['name']}: {group['result']['failed']} failures")


def main():
    """Main entry point for the test runner."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run tests with compact output")
    parser.add_argument("path", nargs="?", help="Test path to run")
    parser.add_argument("-m", "--markers", help="Pytest markers")
    parser.add_argument("-g", "--groups", action="store_true", help="Run predefined test groups")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--no-capture", action="store_true", help="Don't capture output to file")
    
    args = parser.parse_args()
    
    runner = CompactTestRunner()
    
    if args.groups:
        # Run predefined test groups
        groups = [
            {"name": "Unit Tests - Core", "path": "tests/unit", "markers": "not slow and not integration"},
            {"name": "Unit Tests - Templates", "path": "tests/unit/templates"},
            {"name": "Unit Tests - Examples", "path": "tests/unit/examples"},
            {"name": "Integration Tests", "path": "tests/integration", "markers": "not slow"},
            {"name": "Infrastructure Tests", "path": "tests/infrastructure"},
        ]
        runner.run_test_groups(groups)
    else:
        # Run specific tests
        runner.run_tests(
            test_path=args.path,
            markers=args.markers,
            quiet=not args.verbose,
            capture_output=not args.no_capture
        )


if __name__ == "__main__":
    main()
