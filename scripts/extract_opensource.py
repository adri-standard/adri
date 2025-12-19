#!/usr/bin/env python3
"""
Extract Open Source Code from Enterprise Repository.

This script implements directory-based extraction, copying src/adri/ wholesale
to create a clean open source distribution. Replaces the marker-based extraction
system with simpler directory copying.

Usage:
    python scripts/extract_opensource.py --output /path/to/opensource/repo

Features:
- Copies src/adri/ directory tree to output
- Copies open source and shared tests
- Validates no enterprise imports exist
- Generates sync report
- Prepares for PR creation

Exit Codes:
    0 - Success
    1 - Validation errors found
    2 - Extraction failed
"""

import argparse
import ast
import shutil
import sys
from pathlib import Path
from typing import Dict, List, Set


class OpenSourceExtractor:
    """Manages extraction of open source code from enterprise repository."""

    def __init__(self, enterprise_repo: Path, output_dir: Path):
        """
        Initialize extractor.

        Args:
            enterprise_repo: Path to enterprise repository root
            output_dir: Path to output directory for extracted code
        """
        self.enterprise_repo = Path(enterprise_repo)
        self.output_dir = Path(output_dir)
        self.validation_errors: List[str] = []
        self.stats = {
            "files_copied": 0,
            "dirs_created": 0,
            "tests_copied": 0,
            "bytes_copied": 0,
        }

    def extract(self) -> bool:
        """
        Perform full extraction.

        Returns:
            True if extraction succeeded, False otherwise
        """
        print("=" * 70)
        print("ADRI Open Source Extraction")
        print("=" * 70)
        print(f"Enterprise repo: {self.enterprise_repo}")
        print(f"Output directory: {self.output_dir}")
        print()

        try:
            # Step 1: Extract source code
            print("Step 1: Extracting open source code...")
            self.extract_source_code()
            print(f"  ✓ Copied {self.stats['files_copied']} files")
            print()

            # Step 2: Extract tests
            print("Step 2: Extracting tests...")
            self.extract_tests()
            print(f"  ✓ Copied {self.stats['tests_copied']} test files")
            print()

            # Step 3: Copy supporting files
            print("Step 3: Copying supporting files...")
            self.copy_supporting_files()
            print("  ✓ Copied README, LICENSE, etc.")
            print()

            # Step 4: Validate extraction
            print("Step 4: Validating extraction...")
            validation_ok = self.validate_extraction()
            if validation_ok:
                print("  ✓ No enterprise imports detected")
                print("  ✓ All Python files have valid syntax")
            else:
                print(f"  ✗ {len(self.validation_errors)} validation errors")
                for error in self.validation_errors:
                    print(f"    - {error}")
            print()

            # Step 5: Generate report
            print("Step 5: Generating sync report...")
            report = self.generate_report()
            report_file = self.output_dir / "SYNC_REPORT.md"
            report_file.write_text(report)
            print(f"  ✓ Report saved to {report_file}")
            print()

            # Summary
            print("=" * 70)
            print("Extraction Summary")
            print("=" * 70)
            print(f"Files copied:     {self.stats['files_copied']}")
            print(f"Test files:       {self.stats['tests_copied']}")
            print(f"Directories:      {self.stats['dirs_created']}")
            print(f"Total size:       {self.stats['bytes_copied'] / 1024:.1f} KB")
            print(f"Validation:       {'PASSED ✓' if validation_ok else 'FAILED ✗'}")
            print("=" * 70)

            return validation_ok

        except Exception as e:
            print(f"\n✗ Extraction failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    def extract_source_code(self) -> None:
        """Extract src/adri/ directory tree."""
        source_dir = self.enterprise_repo / "src" / "adri"
        target_dir = self.output_dir / "src" / "adri"

        if not source_dir.exists():
            raise FileNotFoundError(f"Source directory not found: {source_dir}")

        # Copy entire adri directory tree
        if target_dir.exists():
            shutil.rmtree(target_dir)

        shutil.copytree(source_dir, target_dir)

        # Count files
        for file_path in target_dir.rglob("*"):
            if file_path.is_file():
                self.stats["files_copied"] += 1
                self.stats["bytes_copied"] += file_path.stat().st_size
            elif file_path.is_dir():
                self.stats["dirs_created"] += 1

    def extract_tests(self) -> None:
        """Extract open source and shared tests."""
        test_source = self.enterprise_repo / "tests"
        test_target = self.output_dir / "tests"

        # Create target test directory
        test_target.mkdir(parents=True, exist_ok=True)

        # Directories to copy
        test_dirs = [
            "open_source",  # Open source specific tests
            "shared",       # Shared utility tests
            "fixtures",     # Test fixtures
            "utils",        # Test utilities
        ]

        # Copy test directories
        for test_dir in test_dirs:
            source_path = test_source / test_dir
            if source_path.exists():
                target_path = test_target / test_dir
                if target_path.exists():
                    shutil.rmtree(target_path)
                # Use ignore_dangling_symlinks to skip broken symlinks
                shutil.copytree(source_path, target_path, symlinks=True, 
                               ignore_dangling_symlinks=True)

                # Count test files
                for file_path in target_path.rglob("*.py"):
                    self.stats["tests_copied"] += 1

        # Copy key test files
        test_files = [
            "conftest.py",
            "__init__.py",
            "test_decorator.py",  # Open source decorator tests
        ]

        for test_file in test_files:
            source_path = test_source / test_file
            if source_path.exists():
                target_path = test_target / test_file
                shutil.copy2(source_path, target_path)
                self.stats["tests_copied"] += 1

    def copy_supporting_files(self) -> None:
        """Copy README, LICENSE, and other supporting files."""
        supporting_files = [
            "README.md",
            "LICENSE",
            "NOTICE",
            "CODE_OF_CONDUCT.md",
            "CONTRIBUTING.md",
            "SECURITY.md",
            "CHANGELOG.md",
            ".gitignore",
        ]

        for filename in supporting_files:
            source_path = self.enterprise_repo / filename
            if source_path.exists():
                target_path = self.output_dir / filename
                shutil.copy2(source_path, target_path)

        # Copy open source pyproject.toml (not the enterprise one)
        opensource_pyproject = self.enterprise_repo / "pyproject.opensource.toml"
        if opensource_pyproject.exists():
            target_path = self.output_dir / "pyproject.toml"
            shutil.copy2(opensource_pyproject, target_path)
        else:
            print(f"  ⚠️ Warning: pyproject.opensource.toml not found, skipping")

    def validate_extraction(self) -> bool:
        """
        Validate extracted code has no enterprise dependencies.

        Returns:
            True if validation passed, False otherwise
        """
        self.validation_errors = []

        # Find all Python files in extracted code
        source_dir = self.output_dir / "src" / "adri"
        if not source_dir.exists():
            self.validation_errors.append(f"Source directory not found: {source_dir}")
            return False

        python_files = list(source_dir.rglob("*.py"))

        # Validate each file
        for py_file in python_files:
            # Check for enterprise imports
            enterprise_imports = self._check_enterprise_imports(py_file)
            if enterprise_imports:
                self.validation_errors.append(
                    f"{py_file.relative_to(self.output_dir)}: "
                    f"Contains enterprise imports: {', '.join(enterprise_imports)}"
                )

            # Check Python syntax
            if not self._check_syntax(py_file):
                self.validation_errors.append(
                    f"{py_file.relative_to(self.output_dir)}: "
                    f"Invalid Python syntax"
                )

        return len(self.validation_errors) == 0

    def _check_enterprise_imports(self, file_path: Path) -> List[str]:
        """
        Check for enterprise-only imports in a Python file.

        Args:
            file_path: Path to Python file

        Returns:
            List of enterprise imports found
        """
        enterprise_imports = []
        enterprise_patterns = [
            "adri_enterprise",
            "from adri.logging.enterprise",
            "from ..logging.enterprise",
        ]

        try:
            content = file_path.read_text(encoding="utf-8")

            for pattern in enterprise_patterns:
                if pattern in content:
                    enterprise_imports.append(pattern)

        except Exception as e:
            self.validation_errors.append(
                f"{file_path}: Failed to read file: {e}"
            )

        return enterprise_imports

    def _check_syntax(self, file_path: Path) -> bool:
        """
        Check if Python file has valid syntax.

        Args:
            file_path: Path to Python file

        Returns:
            True if syntax is valid, False otherwise
        """
        try:
            content = file_path.read_text(encoding="utf-8")
            ast.parse(content)
            return True
        except SyntaxError:
            return False
        except Exception:
            # Other errors (encoding issues, etc.) - be permissive
            return True

    def generate_report(self) -> str:
        """
        Generate sync report.

        Returns:
            Markdown-formatted sync report
        """
        report_lines = [
            "# Open Source Extraction Report",
            "",
            f"**Date:** {self._get_timestamp()}",
            f"**Enterprise Commit:** {self._get_git_commit()}",
            "",
            "## Extraction Statistics",
            "",
            f"- **Source files:** {self.stats['files_copied']}",
            f"- **Test files:** {self.stats['tests_copied']}",
            f"- **Directories:** {self.stats['dirs_created']}",
            f"- **Total size:** {self.stats['bytes_copied'] / 1024:.1f} KB",
            "",
            "## Validation Results",
            "",
        ]

        if self.validation_errors:
            report_lines.extend([
                f"**Status:** ❌ FAILED ({len(self.validation_errors)} errors)",
                "",
                "### Errors",
                "",
            ])
            for error in self.validation_errors:
                report_lines.append(f"- {error}")
        else:
            report_lines.extend([
                "**Status:** ✅ PASSED",
                "",
                "- No enterprise imports detected",
                "- All Python files have valid syntax",
                "- Ready for sync to upstream",
            ])

        report_lines.extend([
            "",
            "## Extracted Directories",
            "",
            "- `src/adri/` - Complete open source package",
            "- `tests/open_source/` - Open source tests",
            "- `tests/shared/` - Shared test utilities",
            "",
            "## Next Steps",
            "",
            "1. Review this report",
            "2. Run tests in extracted code: `pytest tests/`",
            "3. Create PR to upstream repository",
            "",
        ])

        return "\n".join(report_lines)

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _get_git_commit(self) -> str:
        """Get current git commit hash."""
        import subprocess
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.enterprise_repo,
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()[:8]
        except Exception:
            return "unknown"


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Extract open source code from enterprise repository"
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        required=True,
        help="Output directory for extracted code",
    )
    parser.add_argument(
        "--enterprise-repo",
        type=Path,
        default=Path.cwd(),
        help="Path to enterprise repository (default: current directory)",
    )

    args = parser.parse_args()

    # Create extractor and run extraction
    extractor = OpenSourceExtractor(args.enterprise_repo, args.output)
    success = extractor.extract()

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
