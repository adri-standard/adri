#!/usr/bin/env python
"""
Script to help tag code examples in documentation with audience tags.

This script scans markdown files for Python code blocks and suggests
appropriate audience tags based on content analysis.
"""
import os
import re
import argparse
from pathlib import Path
from typing import List, Dict, Tuple, Optional

# Define audience patterns
AUDIENCE_PATTERNS = {
    "AI_BUILDER": [
        r"DataSourceAssessor",
        r"assess\(",
        r"report\.score",
        r"from adri import",
        r"adri\.assess",
    ],
    "STANDARD_CONTRIBUTOR": [
        r"class \w+\(Base\w+\)",
        r"class \w+Dimension",
        r"class \w+Rule",
        r"def evaluate\(",
        r"registry\.register",
        r"@register",
    ],
    "DATA_PROVIDER": [
        r"class \w+Connector",
        r"def read\(",
        r"def fetch_data\(",
        r"def execute_query\(",
        r"metadata\[",
    ]
}

def detect_audience(code: str) -> str:
    """Detect the most likely audience for a code block"""
    scores = {"AI_BUILDER": 0, "STANDARD_CONTRIBUTOR": 0, "DATA_PROVIDER": 0}
    
    # Check for audience patterns
    for audience, patterns in AUDIENCE_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, code):
                scores[audience] += 1
    
    # Get the audience with the highest score
    max_score = max(scores.values())
    if max_score == 0:
        return "AI_BUILDER"  # Default to AI_BUILDER
    
    # If there's a tie, prefer in order: AI_BUILDER, DATA_PROVIDER, STANDARD_CONTRIBUTOR
    max_audiences = [a for a, s in scores.items() if s == max_score]
    if len(max_audiences) > 1:
        if "AI_BUILDER" in max_audiences:
            return "AI_BUILDER"
        elif "DATA_PROVIDER" in max_audiences:
            return "DATA_PROVIDER"
        else:
            return "STANDARD_CONTRIBUTOR"
    
    return max(scores, key=scores.get)

def extract_code_blocks(content: str) -> List[Tuple[str, int, int]]:
    """Extract Python code blocks from markdown content"""
    code_blocks = []
    lines = content.split('\n')
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Check for code block start
        if line.strip().startswith("```python") or line.strip().startswith("```py"):
            start_line = i
            code_lines = []
            i += 1
            
            # Collect code until closing ```
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i])
                i += 1
            
            if code_lines:
                code = '\n'.join(code_lines)
                code_blocks.append((code, start_line, i))
        i += 1
    
    return code_blocks

def has_audience_tag(code: str) -> bool:
    """Check if code already has an audience tag"""
    first_lines = code.split('\n')[:3]
    for line in first_lines:
        if re.search(r'#\s*\[(AI_BUILDER|STANDARD_CONTRIBUTOR|DATA_PROVIDER)\]', line):
            return True
    return False

def process_file(file_path: Path, dry_run: bool = True) -> Dict:
    """Process a markdown file and suggest audience tags"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    code_blocks = extract_code_blocks(content)
    results = {
        "file": str(file_path),
        "total_blocks": len(code_blocks),
        "already_tagged": 0,
        "suggested_tags": [],
        "updated": False
    }
    
    if not code_blocks:
        return results
    
    lines = content.split('\n')
    modified = False
    
    # Process in reverse order to avoid line number changes
    for code, start_line, end_line in reversed(code_blocks):
        if has_audience_tag(code):
            results["already_tagged"] += 1
            continue
        
        audience = detect_audience(code)
        results["suggested_tags"].append({
            "line": start_line + 1,
            "audience": audience,
            "code_preview": code.split('\n')[0][:50] + "..." if len(code.split('\n')[0]) > 50 else code.split('\n')[0]
        })
        
        if not dry_run:
            # Insert audience tag after opening ```
            tag_line = f"# [{audience}]"
            lines.insert(start_line + 1, tag_line)
            modified = True
    
    if modified:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        results["updated"] = True
    
    return results

def main():
    parser = argparse.ArgumentParser(description="Tag code examples with audience tags")
    parser.add_argument("path", help="Path to markdown file or directory")
    parser.add_argument("--apply", action="store_true", help="Apply suggested tags (default is dry run)")
    parser.add_argument("--recursive", action="store_true", help="Process directories recursively")
    args = parser.parse_args()
    
    path = Path(args.path)
    dry_run = not args.apply
    
    if path.is_file() and path.suffix.lower() == '.md':
        results = process_file(path, dry_run)
        print_results([results], dry_run)
    elif path.is_dir():
        results = []
        if args.recursive:
            for md_file in path.glob('**/*.md'):
                results.append(process_file(md_file, dry_run))
        else:
            for md_file in path.glob('*.md'):
                results.append(process_file(md_file, dry_run))
        print_results(results, dry_run)
    else:
        print(f"Error: {path} is not a markdown file or directory")
        return 1
    
    return 0

def print_results(results: List[Dict], dry_run: bool):
    """Print processing results"""
    total_files = len(results)
    total_blocks = sum(r["total_blocks"] for r in results)
    already_tagged = sum(r["already_tagged"] for r in results)
    to_tag = sum(len(r["suggested_tags"]) for r in results)
    
    print(f"\n{'DRY RUN - ' if dry_run else ''}Code Example Audience Tagging Results")
    print("="*60)
    print(f"Files processed: {total_files}")
    print(f"Total code blocks: {total_blocks}")
    print(f"Already tagged: {already_tagged}")
    print(f"Suggested tags: {to_tag}")
    
    if dry_run and to_tag > 0:
        print("\nSuggested Tags:")
        print("-"*60)
        for result in results:
            if result["suggested_tags"]:
                print(f"\n{result['file']}:")
                for tag in result["suggested_tags"]:
                    print(f"  Line {tag['line']}: [{tag['audience']}] - {tag['code_preview']}")
        
        print("\nRun with --apply to apply these changes")
    elif not dry_run and to_tag > 0:
        print("\nApplied Tags:")
        print("-"*60)
        updated_files = sum(1 for r in results if r["updated"])
        print(f"Updated {updated_files} files with {to_tag} audience tags")

if __name__ == "__main__":
    exit(main())
