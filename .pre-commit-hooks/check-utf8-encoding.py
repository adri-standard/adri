#!/usr/bin/env python3
"""Check that all file opens specify encoding='utf-8'."""

import sys
from pathlib import Path


def check_file(filepath):
    """Check file for open() calls without encoding."""
    with open(filepath, encoding="utf-8") as f:
        lines = f.readlines()

    issues = []
    i = 0
    while i < len(lines):
        line = lines[i]

        # Check if line has open() call
        if "open(" not in line:
            i += 1
            continue

        # Ignore comments
        if line.strip().startswith("#"):
            i += 1
            continue

        # Ignore urlopen and other non-builtin open
        if "urlopen" in line or "mock_open" in line:
            i += 1
            continue

        # For multi-line open() calls, check the next few lines too
        statement = line
        j = i + 1
        while j < len(lines) and j < i + 5:  # Look ahead up to 5 lines
            statement += lines[j]
            if ")" in lines[j]:  # Found closing paren
                break
            j += 1

        # Check if this statement has encoding
        if "encoding=" in statement:
            i += 1
            continue

        # Ignore binary mode opens
        if (
            "'rb'" in statement
            or '"rb"' in statement
            or "'wb'" in statement
            or '"wb"' in statement
        ):
            i += 1
            continue

        # This is an open() without encoding
        issues.append((i + 1, line.strip()))
        i += 1

    return issues


def main():
    """Check all Python files."""
    errors = []

    for pyfile in Path("src").rglob("*.py"):
        issues = check_file(pyfile)
        if issues:
            errors.append((pyfile, issues))

    for pyfile in Path("tests").rglob("*.py"):
        issues = check_file(pyfile)
        if issues:
            errors.append((pyfile, issues))

    if errors:
        print("[ERROR] Found open() calls without encoding='utf-8':")
        print("\nTo fix, add encoding='utf-8' parameter:")
        print("  with open(file, 'r', encoding='utf-8') as f:")
        print()
        for filepath, issues in errors:
            print(f"\n{filepath}:")
            for line_num, line in issues[:3]:  # Show first 3 issues per file
                print(f"  Line {line_num}: {line}")
            if len(issues) > 3:
                print(f"  ... and {len(issues) - 3} more issues")
        print("\n[WARNING] This causes Windows CI failures (cp1252 vs UTF-8)")
        sys.exit(1)

    print("[PASS] All open() calls specify encoding")
    sys.exit(0)


if __name__ == "__main__":
    main()
