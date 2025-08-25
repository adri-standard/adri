#!/usr/bin/env python3
"""
Local testing script for ADRI Validator.
Runs all quality checks that would run in GitHub Actions.
"""

import subprocess
import sys
from pathlib import Path
from typing import List, Tuple
import json

# ANSI color codes
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'  # No Color


class LocalTester:
    """Run local tests for ADRI Validator."""
    
    def __init__(self):
        self.failed_checks = []
        self.project_root = Path.cwd()
        
        # Verify we're in the right directory
        if not (self.project_root / "pyproject.toml").exists():
            print(f"{RED}[✗]{NC} Please run this script from the adri-validator directory")
            sys.exit(1)
    
    def print_status(self, message: str):
        """Print success status."""
        print(f"{GREEN}[✓]{NC} {message}")
    
    def print_error(self, message: str):
        """Print error status."""
        print(f"{RED}[✗]{NC} {message}")
    
    def print_warning(self, message: str):
        """Print warning status."""
        print(f"{YELLOW}[!]{NC} {message}")
    
    def print_header(self, title: str):
        """Print section header."""
        print("\n" + "=" * 50)
        print(title)
        print("=" * 50)
    
    def run_command(self, command: List[str], check_name: str) -> bool:
        """Run a command and track results."""
        print(f"\nRunning: {check_name}")
        print(f"Command: {' '.join(command)}")
        
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True
            )
            self.print_status(f"{check_name} passed")
            if result.stdout:
                print(result.stdout)
            return True
        except subprocess.CalledProcessError as e:
            self.print_error(f"{check_name} failed")
            if e.stdout:
                print(e.stdout)
            if e.stderr:
                print(e.stderr)
            self.failed_checks.append(check_name)
            return False
        except FileNotFoundError:
            self.print_warning(f"{command[0]} not found - skipping {check_name}")
            return True
    
    def check_tool_installed(self, tool: str) -> bool:
        """Check if a tool is installed."""
        try:
            subprocess.run([tool, "--version"], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def run_formatting_checks(self):
        """Run code formatting checks."""
        self.print_header("Code Formatting Checks")
        
        # Black
        self.run_command(
            ["black", "--check", "adri/", "tests/"],
            "Black formatting"
        )
        
        # isort
        self.run_command(
            ["isort", "--check-only", "adri/", "tests/"],
            "isort import sorting"
        )
    
    def run_quality_checks(self):
        """Run code quality checks."""
        self.print_header("Code Quality Checks")
        
        # Flake8
        self.run_command(
            ["flake8", "adri/", "tests/"],
            "Flake8 linting"
        )
        
        # MyPy
        self.run_command(
            ["mypy", "adri/", "tests/"],
            "MyPy type checking"
        )
    
    def run_security_checks(self):
        """Run security checks."""
        self.print_header("Security Checks")
        
        # Bandit
        self.run_command(
            ["bandit", "-r", "adri/", "-ll"],
            "Bandit security scan"
        )
        
        # Safety (if installed)
        if self.check_tool_installed("safety"):
            self.run_command(
                ["safety", "check", "--json"],
                "Safety dependency check"
            )
        else:
            self.print_warning("Safety not installed, skipping dependency check")
            self.print_warning("Install with: pip install safety")
    
    def run_tests(self):
        """Run test suite."""
        self.print_header("Running Test Suite")
        
        # Unit tests
        self.run_command(
            ["pytest", "tests/unit/", "-v"],
            "Pytest unit tests"
        )
        
        # Integration tests
        self.run_command(
            ["pytest", "tests/integration/", "-v"],
            "Pytest integration tests"
        )
    
    def run_coverage(self):
        """Run test coverage analysis."""
        self.print_header("Test Coverage Analysis")
        
        success = self.run_command(
            ["pytest", "tests/", "--cov=adri", "--cov-report=term-missing", "--cov-report=html"],
            "Coverage report"
        )
        
        if success:
            # Try to get coverage percentage
            try:
                result = subprocess.run(
                    ["coverage", "report"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                for line in result.stdout.split('\n'):
                    if 'TOTAL' in line:
                        parts = line.split()
                        if len(parts) >= 4:
                            coverage_percent = parts[-1]
                            print(f"Overall coverage: {coverage_percent}")
                            
                            # Check threshold
                            try:
                                coverage_value = float(coverage_percent.rstrip('%'))
                                if coverage_value < 80:
                                    self.print_warning("Coverage is below 80% threshold")
                                    self.failed_checks.append("Coverage threshold")
                            except ValueError:
                                pass
            except subprocess.CalledProcessError:
                pass
    
    def check_documentation(self):
        """Check for documentation issues."""
        self.print_header("Documentation Checks")
        
        print("Checking for missing docstrings...")
        
        missing_count = 0
        for py_file in Path("adri").rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            
            with open(py_file, 'r') as f:
                content = f.read()
                
            # Simple check for function/class definitions without docstrings
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.strip().startswith(('def ', 'class ')):
                    # Check if next non-empty line is a docstring
                    for j in range(i + 1, min(i + 5, len(lines))):
                        next_line = lines[j].strip()
                        if next_line:
                            if not next_line.startswith(('"""', "'''")):
                                missing_count += 1
                                if missing_count <= 5:  # Show first 5
                                    print(f"  - {py_file}:{i+1}")
                            break
        
        if missing_count > 0:
            self.print_warning(f"Found {missing_count} potential missing docstrings")
        else:
            self.print_status("Documentation looks good")
    
    def run_precommit(self):
        """Run pre-commit hooks if available."""
        self.print_header("Pre-commit Hooks")
        
        if (self.project_root / ".pre-commit-config.yaml").exists():
            if self.check_tool_installed("pre-commit"):
                self.run_command(
                    ["pre-commit", "run", "--all-files"],
                    "Pre-commit hooks"
                )
            else:
                self.print_warning("pre-commit not installed")
                self.print_warning("Install with: pip install pre-commit")
                self.print_warning("Then run: pre-commit install")
        else:
            self.print_warning("No .pre-commit-config.yaml found")
    
    def check_common_issues(self):
        """Check for common code issues."""
        self.print_header("Common Issues Check")
        
        # Check for print statements
        print("Checking for print statements...")
        print_found = False
        for py_file in Path("adri").rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            
            with open(py_file, 'r') as f:
                for i, line in enumerate(f, 1):
                    if 'print(' in line and '# noqa' not in line:
                        if not any(x in line for x in ['__str__', '__repr__']):
                            if not print_found:
                                self.print_warning("Found print statements - consider using logging instead")
                                print_found = True
                            print(f"  - {py_file}:{i}")
        
        if not print_found:
            self.print_status("No print statements found")
        
        # Check for TODO comments
        print("\nChecking for TODO comments...")
        todo_count = 0
        for py_file in Path("adri").rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            
            with open(py_file, 'r') as f:
                for i, line in enumerate(f, 1):
                    if 'TODO' in line:
                        todo_count += 1
                        if todo_count <= 5:  # Show first 5
                            print(f"  - {py_file}:{i}: {line.strip()}")
        
        if todo_count > 0:
            self.print_warning(f"Found {todo_count} TODO comments")
        else:
            self.print_status("No TODO comments found")
    
    def run_quick_check(self):
        """Run only the essential checks (faster)."""
        self.print_header("Quick Check Mode")
        print("Running essential checks only...")
        
        self.run_formatting_checks()
        self.run_quality_checks()
        
        # Run minimal tests
        self.print_header("Quick Test Run")
        self.run_command(
            ["pytest", "tests/unit/", "-x", "--tb=short"],
            "Quick unit tests"
        )
    
    def print_summary(self):
        """Print final summary."""
        self.print_header("Test Summary")
        
        if not self.failed_checks:
            self.print_status("All checks passed! ✨")
            print("\nYour code is ready to commit!")
            print("GitHub Actions should pass without issues.")
            return 0
        else:
            self.print_error("Some checks failed:")
            for check in self.failed_checks:
                print(f"  - {check}")
            print("\nPlease fix these issues before committing.")
            print("Run this script again after making fixes.")
            return 1
    
    def run_all(self):
        """Run all checks."""
        self.print_header("ADRI Validator Local Testing")
        print("This will run all quality checks locally")
        print("Similar to what runs in GitHub Actions")
        
        self.run_formatting_checks()
        self.run_quality_checks()
        self.run_security_checks()
        self.run_tests()
        self.run_coverage()
        self.check_documentation()
        self.run_precommit()
        self.check_common_issues()
        
        return self.print_summary()
    
    def run_ci_simulation(self):
        """Simulate exactly what CI runs."""
        self.print_header("CI Simulation Mode")
        print("Running exact CI workflow locally...")
        
        # Simulate quality-gate job
        self.print_header("Quality Gate (CI Job)")
        self.run_formatting_checks()
        self.run_quality_checks()
        
        # Simulate test job
        self.print_header("Test Suite (CI Job)")
        self.run_tests()
        self.run_coverage()
        
        # Simulate security job
        self.print_header("Security Scan (CI Job)")
        self.run_security_checks()
        
        return self.print_summary()


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Local testing for ADRI Validator")
    parser.add_argument(
        "--quick", 
        action="store_true",
        help="Run quick checks only (faster)"
    )
    parser.add_argument(
        "--ci",
        action="store_true",
        help="Simulate exact CI workflow"
    )
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Run coverage analysis only"
    )
    parser.add_argument(
        "--security",
        action="store_true",
        help="Run security checks only"
    )
    
    args = parser.parse_args()
    
    tester = LocalTester()
    
    if args.quick:
        return tester.run_quick_check()
    elif args.ci:
        return tester.run_ci_simulation()
    elif args.coverage:
        tester.run_coverage()
        return tester.print_summary()
    elif args.security:
        tester.run_security_checks()
        return tester.print_summary()
    else:
        return tester.run_all()


if __name__ == "__main__":
    sys.exit(main())
