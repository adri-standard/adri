#!/usr/bin/env python3
"""
Script to fix legacy test standards to use the new dimension_requirements format.

Old format:
    requirements:
        dimensions:
            validity: 85.0

New format:
    requirements:
        dimension_requirements:
            validity:
                weight: 3
                minimum_score: 85.0
"""

import re
import sys


def fix_standard_dict_in_code(content: str) -> str:
    """Fix standard dictionaries in Python test code."""

    # Pattern 1: Simple dimension scores like "validity": 85.0
    # Replace with proper structure
    def replace_dimension_score(match):
        indent = match.group(1)
        dimension = match.group(2)
        score = match.group(3)
        return f'{indent}"{dimension}": {{"weight": 3, "minimum_score": {score}}}'

    # Fix requirements.dimensions -> requirements.dimension_requirements
    content = re.sub(
        r'"dimensions":\s*{([^}]+)}',
        lambda m: f'"dimension_requirements": {{{fix_dimension_values(m.group(1))}}}',
        content,
        flags=re.MULTILINE
    )

    return content


def fix_dimension_values(dimensions_content: str) -> str:
    """Convert simple scores to proper dimension requirement structure."""
    lines = dimensions_content.split('\n')
    fixed_lines = []

    for line in lines:
        # Match pattern like: "validity": 85.0,
        match = re.match(r'(\s*)"(\w+)":\s*(\d+\.?\d*),?\s*$', line)
        if match:
            indent, dimension, score = match.groups()
            fixed_lines.append(f'{indent}"{dimension}": {{"weight": 3, "minimum_score": {score}}}')
        else:
            fixed_lines.append(line)

    return '\n'.join(fixed_lines)


def main():
    if len(sys.argv) != 2:
        print("Usage: python fix_test_standards.py <file_to_fix>")
        sys.exit(1)

    filepath = sys.argv[1]

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Fix the content
    fixed_content = fix_standard_dict_in_code(content)

    # Write back
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(fixed_content)

    print(f"Fixed {filepath}")


if __name__ == "__main__":
    main()
