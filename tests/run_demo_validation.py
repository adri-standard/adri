#!/usr/bin/env python3
"""
Simple Demo Validation Runner

Tests that ADRI demo experiences work correctly for AI engineers.
Focuses on credibility, first impressions, and real-world value.
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.demo_validation.demo_validator import DemoValidator


def print_header():
    """Print validation header."""
    print("\n" + "=" * 70)
    print("🎭 ADRI DEMO VALIDATION")
    print("=" * 70)
    print("🎯 Goal: Ensure AI engineers immediately see value in ADRI demos")
    print("📋 Tests: Credibility, first impressions, and user experience")
    print("=" * 70)


def run_quick_validation():
    """Run quick validation of demo experiences."""
    print_header()

    validator = DemoValidator()
    examples = validator.discover_examples()

    if not examples:
        print("❌ No examples found to validate!")
        return False

    print(f"🔍 Found {len(examples)} examples to validate")
    print()

    # Quick validation checks
    all_passed = True
    results = {}

    for example_path in examples:
        framework = validator.extract_framework_name(example_path)
        print(f"📋 Validating {framework.upper()}...")

        # Run comprehensive validation
        demo_results = validator.validate_demo_credibility(example_path)
        results[framework] = demo_results

        score = demo_results["overall_score"]
        credible = demo_results["credible"]

        if credible:
            print(f"   ✅ {score:.1f}% - CREDIBLE")
        else:
            print(f"   ❌ {score:.1f}% - NEEDS WORK")
            all_passed = False

            # Show top issues
            failed_validations = [
                name
                for name, result in demo_results["validations"].items()
                if not result["passed"]
            ]
            if failed_validations:
                print(f"      Issues: {', '.join(failed_validations[:3])}")

        print()

    # Setup tool validation
    print("🔧 Validating Setup Tool...")
    is_integrated, reason = validator.validate_setup_tool_integration()
    if is_integrated:
        print(f"   ✅ {reason}")
    else:
        print(f"   ❌ {reason}")
        all_passed = False

    print()

    # Overall summary
    credible_count = sum(1 for r in results.values() if r["credible"])
    total_count = len(results)
    overall_credibility = (credible_count / total_count) * 100 if total_count > 0 else 0

    print("📊 VALIDATION SUMMARY")
    print("-" * 50)
    print(f"Credible demos: {credible_count}/{total_count}")
    print(f"Overall score: {overall_credibility:.1f}%")

    if all_passed and overall_credibility >= 80.0:
        print()
        print("🎉 DEMO EXPERIENCES READY FOR AI ENGINEERS!")
        print("✅ All demos are credible and show clear value")
        print("✅ Setup tool is professional and functional")
        print("✅ First impressions will be positive")
        return True
    else:
        print()
        print("⚠️ DEMO EXPERIENCES NEED IMPROVEMENT")

        if overall_credibility < 80.0:
            print(f"❌ Credibility too low: {overall_credibility:.1f}% (need ≥80%)")

        # Show frameworks that need work
        needs_work = [fw for fw, r in results.items() if not r["credible"]]
        if needs_work:
            print(f"❌ Frameworks needing work: {', '.join(needs_work)}")

        return False


def run_detailed_validation():
    """Run detailed validation with full test suite."""
    print_header()
    print("🧪 Running detailed validation with full test suite...")
    print()

    try:
        import pytest

        # Run demo validation tests
        test_files = [
            "tests/demo_validation/test_demo_credibility.py",
            "tests/demo_validation/test_ai_engineer_first_impression.py",
        ]

        # Check that test files exist
        missing_tests = []
        for test_file in test_files:
            if not Path(test_file).exists():
                missing_tests.append(test_file)

        if missing_tests:
            print(f"❌ Missing test files: {missing_tests}")
            return False

        # Run tests
        print("Running demo credibility tests...")
        result1 = pytest.main(
            ["tests/demo_validation/test_demo_credibility.py", "-v", "--tb=short"]
        )

        print("\nRunning first impression tests...")
        result2 = pytest.main(
            [
                "tests/demo_validation/test_ai_engineer_first_impression.py",
                "-v",
                "--tb=short",
            ]
        )

        # Check results
        if result1 == 0 and result2 == 0:
            print("\n🎉 ALL DETAILED VALIDATION TESTS PASSED!")
            return True
        else:
            print("\n❌ Some detailed validation tests failed")
            return False

    except ImportError:
        print("❌ pytest not installed - cannot run detailed tests")
        print("💡 Install with: pip install pytest")
        print("🔄 Falling back to quick validation...")
        return run_quick_validation()


def run_standalone_demo_check():
    """Run standalone demo validator script."""
    print_header()
    print("🏃 Running standalone demo validator...")
    print()

    # Run the demo validator directly
    validator = DemoValidator()

    try:
        # This will run the validator's main() function
        from tests.demo_validation.demo_validator import main

        main()
        return True
    except Exception as e:
        print(f"❌ Standalone validation failed: {e}")
        return False


def main():
    """Main entry point for demo validation."""
    parser = argparse.ArgumentParser(
        description="Validate ADRI demo experiences for AI engineers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tests/run_demo_validation.py              # Quick validation
  python tests/run_demo_validation.py --detailed   # Full test suite
  python tests/run_demo_validation.py --standalone # Standalone validator
        """,
    )

    parser.add_argument(
        "--detailed",
        action="store_true",
        help="Run detailed validation with full test suite",
    )

    parser.add_argument(
        "--standalone", action="store_true", help="Run standalone demo validator script"
    )

    parser.add_argument(
        "--quiet", action="store_true", help="Minimize output (just final result)"
    )

    args = parser.parse_args()

    # Redirect output if quiet
    if args.quiet:
        import contextlib
        import io

        # Capture output but still show final result
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            if args.detailed:
                success = run_detailed_validation()
            elif args.standalone:
                success = run_standalone_demo_check()
            else:
                success = run_quick_validation()

        # Show final result
        if success:
            print("✅ Demo validation PASSED")
        else:
            print("❌ Demo validation FAILED")

        return 0 if success else 1

    # Normal output
    if args.detailed:
        success = run_detailed_validation()
    elif args.standalone:
        success = run_standalone_demo_check()
    else:
        success = run_quick_validation()

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
