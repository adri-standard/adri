#!/usr/bin/env python3
"""
Automatically fix open() calls to include encoding='utf-8'.

This script scans all Python files and adds encoding='utf-8' to text mode
file operations that are missing it.
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple


def fix_open_call(line: str) -> Tuple[str, bool]:
    """
    Fix a line containing open() to include encoding='utf-8'.

    Returns:
        Tuple of (fixed_line, was_modified)
    """
    # Skip if already has encoding
    if 'encoding=' in line:
        return line, False

    # Skip binary mode opens
    if "'rb'" in line or '"rb"' in line or "'wb'" in line or '"wb"' in line:
        return line, False

    # Skip if it's a comment
    if line.strip().startswith('#'):
        return line, False

    # Skip urlopen (different function)
    if 'urlopen' in line:
        return line, False

    # Pattern for open() with mode parameter
    # Matches: open(path, 'r') or open(path, "w", ...)
    pattern = r"open\(([^,]+),\s*['\"]([rwa])['\"]"

    def add_encoding(match):
        path_arg = match.group(1)
        mode = match.group(2)
        # Check if there's more after the mode (like newline='')
        # We'll add encoding after mode
        return f"open({path_arg}, '{mode}', encoding='utf-8'"

    new_line = re.sub(pattern, add_encoding, line)

    # Also handle open(path) with no explicit mode (defaults to 'r')
    if new_line == line:  # No change yet
        # Pattern: open(path) with no mode
        pattern2 = r"open\(([^)]+)\)\s+as"
        match = re.search(pattern2, line)
        if match and "encoding=" not in line:
            # This is open(path) as f - needs encoding
            new_line = line.replace("open(", "open(", 1)
            # Insert encoding before 'as'
            new_line = re.sub(r"\)\s+as", ", encoding='utf-8') as", new_line)

    return new_line, (new_line != line)


def fix_file(filepath: Path) -> int:
    """Fix encoding issues in a single file. Returns number of fixes."""
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    fixed_lines = []
    fix_count = 0

    for line in lines:
        if 'open(' in line and 'encoding=' not in line:
            fixed_line, was_modified = fix_open_call(line)
            fixed_lines.append(fixed_line)
            if was_modified:
                fix_count += 1
        else:
            fixed_lines.append(line)

    if fix_count > 0:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(fixed_lines)

    return fix_count


def main():
    """Fix encoding in all Python files."""
    total_fixes = 0
    files_modified = 0

    print("🔧 Fixing encoding issues in Python files...")
    print()

    # Fix source files
    for pyfile in Path('src').rglob('*.py'):
        fixes = fix_file(pyfile)
        if fixes > 0:
            files_modified += 1
            total_fixes += fixes
            print(f"✅ Fixed {fixes} issue(s) in {pyfile}")

    # Fix test files
    for pyfile in Path('tests').rglob('*.py'):
        fixes = fix_file(pyfile)
        if fixes > 0:
            files_modified += 1
            total_fixes += fixes
            print(f"✅ Fixed {fixes} issue(s) in {pyfile}")

    print()
    print(f"📊 Summary:")
    print(f"   Files modified: {files_modified}")
    print(f"   Total fixes: {total_fixes}")
    print()

    if total_fixes > 0:
        print("✅ All encoding issues fixed!")
        print("⚠️  Run tests to verify: pytest")
    else:
        print("✅ No encoding issues found")

    return 0


if __name__ == '__main__':
    sys.exit(main())
