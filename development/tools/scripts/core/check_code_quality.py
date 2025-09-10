#!/usr/bin/env python3
"""
Code Quality Check Script for ADRI Validator.

This script runs all the code quality checks that are performed in GitHub Actions.
Run this before committing to catch issues early and prevent CI failures.

Usage:
    python scripts/check_code_quality.py [--fix] [--fast]

Options:
    --fix    Automatically fix issues where possible (Black, isort)
    --fast   Skip slower checks (mypy, bandit)
"""

import argparse
import subprocess  # nosec B404 - subprocess needed for running tools
import sys
from pathlib import Path
from typing import List, Tuple


def run_command(cmd: List[str], fix_mode: bool = False) -> Tuple[bool, str]:
    """
    Run a command and return success status and output.

    Args:
        cmd: Command to run as list of strings
        fix_mode: If True, don't check return code for formatters

    Returns:
        Tuple of (success, output)
    """
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=False
        )  # nosec B603

        # In fix mode, formatters return non-zero when they make changes
        # This is not considered an error
        if fix_mode and cmd[0] in ["black", "isort"]:
            success = True
        else:
            success = result.returncode == 0

        output = result.stdout + result.stderr
        return success, output

    except FileNotFoundError:
        return False, f"Command not found: {cmd[0]}"
    except Exception as e:
        return False, f"Error running command: {e}"


def print_check_header(name: str, description: str):
    """Print a formatted header for a check."""
    print(f"\n{'='*60}")
    print(f"🔍 {name}")
    print(f"{'='*60}")
    print(f"{description}")
    print()


def print_result(success: bool, output: str = "", show_output: bool = True):
    """Print the result of a check."""
    if success:
        print("✅ PASSED")
    else:
        print("❌ FAILED")
        if output and show_output:
            print("\nOutput:")
            print(output)
    print()


def check_black(fix_mode: bool = False) -> bool:
    """Check Black code formatting."""
    print_check_header(
        "Black Code Formatting", "Checking Python code formatting with Black"
    )

    if fix_mode:
        cmd = ["python", "-m", "black", "adri/", "tests/", "scripts/"]
        print("🔧 Running Black formatter (fixing issues)...")
    else:
        cmd = [
            "python",
            "-m",
            "black",
            "--check",
            "--diff",
            "adri/",
            "tests/",
            "scripts/",
        ]
        print("🔧 Running Black formatter check...")

    success, output = run_command(cmd, fix_mode)
    print_result(success, output)
    return success


def check_isort(fix_mode: bool = False) -> bool:
    """Check import sorting with isort."""
    print_check_header("Import Sorting", "Checking import organization with isort")

    if fix_mode:
        cmd = ["python", "-m", "isort", "adri/", "tests/", "scripts/"]
        print("🔧 Running isort (fixing issues)...")
    else:
        cmd = [
            "python",
            "-m",
            "isort",
            "--check-only",
            "--diff",
            "adri/",
            "tests/",
            "scripts/",
        ]
        print("🔧 Running isort check...")

    success, output = run_command(cmd, fix_mode)
    print_result(success, output)
    return success


def check_flake8() -> bool:
    """Check code style with flake8."""
    print_check_header(
        "Flake8 Linting", "Checking code style and potential issues with flake8"
    )

    cmd = ["python", "-m", "flake8", "adri/", "tests/", "scripts/"]
    print("🔧 Running flake8 linter...")

    success, output = run_command(cmd)
    print_result(success, output)
    return success


def check_mypy() -> bool:
    """Check type hints with mypy."""
    print_check_header("Type Checking", "Checking type hints with mypy")

    cmd = ["python", "-m", "mypy", "adri/", "--ignore-missing-imports"]
    print("🔧 Running mypy type checker...")

    success, output = run_command(cmd)
    print_result(success, output)
    return success


def check_bandit() -> bool:
    """Check security issues with bandit."""
    print_check_header("Security Scan", "Checking for security issues with bandit")

    cmd = ["python", "-m", "bandit", "-r", "adri/", "-f", "text"]
    print("🔧 Running bandit security scanner...")

    success, output = run_command(cmd)
    print_result(success, output)
    return success


def check_tests() -> bool:
    """Run a quick test to ensure basic functionality."""
    print_check_header(
        "Quick Test", "Running a quick test to verify basic functionality"
    )

    cmd = ["python", "-m", "pytest", "tests/unit/test_init.py", "-v"]
    print("🔧 Running quick test...")

    success, output = run_command(cmd)
    print_result(success, output)
    return success


def check_imports() -> bool:
    """Check that all modules can be imported."""
    print_check_header("Import Test", "Testing that all modules can be imported")

    cmd = ["python", "-c", "import adri; print('✅ ADRI imports successfully')"]
    print("🔧 Testing imports...")

    success, output = run_command(cmd)
    print_result(success, output)
    return success


def main():
    """Execute all code quality checks."""
    parser = argparse.ArgumentParser(
        description="Run code quality checks for ADRI Validator"
    )
    parser.add_argument(
        "--fix", action="store_true", help="Automatically fix issues where possible"
    )
    parser.add_argument(
        "--fast", action="store_true", help="Skip slower checks (mypy, bandit)"
    )
    parser.add_argument(
        "--format-only",
        action="store_true",
        help="Only run formatting checks (Black, isort)",
    )

    args = parser.parse_args()

    # Change to project root
    project_root = Path(__file__).parent.parent
    import os

    os.chdir(project_root)

    print("🚀 ADRI Validator Code Quality Checker")
    print("=" * 60)

    if args.fix:
        print("🔧 Fix mode enabled - will automatically fix formatting issues")
    if args.fast:
        print("⚡ Fast mode enabled - skipping slower checks")
    if args.format_only:
        print("✨ Format-only mode - running Black and isort only")

    checks = []
    all_passed = True

    # Core formatting checks (always run)
    checks.append(("Black", check_black, args.fix))
    checks.append(("isort", check_isort, args.fix))

    if not args.format_only:
        # Linting checks
        checks.append(("flake8", check_flake8, False))
        checks.append(("imports", check_imports, False))

        if not args.fast:
            # Slower checks
            checks.append(("mypy", check_mypy, False))
            checks.append(("bandit", check_bandit, False))

        # Basic functionality check
        checks.append(("tests", check_tests, False))

    # Run all checks
    for name, check_func, fix_arg in checks:
        try:
            if fix_arg is not False:
                success = check_func(fix_arg)
            else:
                success = check_func()

            if not success:
                all_passed = False

        except Exception as e:
            print(f"❌ Error running {name}: {e}")
            all_passed = False

    # Final summary
    print("\n" + "=" * 60)
    print("📊 FINAL SUMMARY")
    print("=" * 60)

    if all_passed:
        print("✅ ALL CHECKS PASSED!")
        print("🎉 Your code is ready for commit!")

        if args.fix:
            print("\n💡 Some files may have been auto-formatted.")
            print("   Please review the changes before committing.")

    else:
        print("❌ SOME CHECKS FAILED!")
        print("🔧 Please fix the issues above before committing.")

        if not args.fix:
            print("\n💡 Tip: Run with --fix to automatically fix formatting issues:")
            print("   python scripts/check_code_quality.py --fix")

    print("=" * 60)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
