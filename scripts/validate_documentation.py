#!/usr/bin/env python3
"""
ADRI Documentation Validation Suite

Comprehensive validation of documentation migration, including:
- Link validation (internal and external)
- Code example syntax checking
- File structure audit against PROJECT_INDEX.md
- Legacy content detection
- Cross-reference validation

Usage:
    python scripts/validate_documentation.py [--fix] [--report-format html|json|text]
"""

import os
import re
import sys
import json
import argparse
import subprocess
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass, asdict
from urllib.parse import urlparse
import requests
import ast
import yaml
from datetime import datetime

@dataclass
class ValidationIssue:
    """Represents a validation issue found during checks"""
    file_path: str
    line_number: int
    issue_type: str
    severity: str  # 'error', 'warning', 'info'
    message: str
    suggestion: Optional[str] = None

@dataclass
class ValidationReport:
    """Complete validation report"""
    timestamp: str
    total_files_checked: int
    issues: List[ValidationIssue]
    summary: Dict[str, int]
    
    def add_issue(self, issue: ValidationIssue):
        self.issues.append(issue)
        if issue.severity not in self.summary:
            self.summary[issue.severity] = 0
        self.summary[issue.severity] += 1

class DocumentationValidator:
    """Main validation class"""
    
    def __init__(self, root_path: str = "."):
        self.root_path = Path(root_path)
        self.docs_path = self.root_path / "docs"
        self.project_index_path = self.root_path / "PROJECT_INDEX.md"
        self.report = ValidationReport(
            timestamp=datetime.now().isoformat(),
            total_files_checked=0,
            issues=[],
            summary={}
        )
        
        # Patterns for different checks
        self.markdown_link_pattern = re.compile(r'\[([^\]]*)\]\(([^)]+)\)')
        self.code_block_pattern = re.compile(r'```(\w+)?\n(.*?)\n```', re.DOTALL)
        self.audience_tag_pattern = re.compile(r'# \[(AI_BUILDER|DATA_PROVIDER|STANDARD_CONTRIBUTOR)\]')
        
    def validate_all(self) -> ValidationReport:
        """Run all validation checks"""
        print("🔍 Starting comprehensive documentation validation...")
        
        # Get all markdown files
        md_files = list(self.docs_path.rglob("*.md"))
        md_files.extend([self.root_path / "README.md"])
        
        self.report.total_files_checked = len(md_files)
        
        print(f"📁 Found {len(md_files)} markdown files to validate")
        
        # Run validation checks
        self._validate_links(md_files)
        self._validate_code_examples(md_files)
        self._validate_project_index()
        self._validate_file_structure()
        self._detect_legacy_content()
        self._validate_audience_tags(md_files)
        
        return self.report
    
    def _validate_links(self, md_files: List[Path]):
        """Validate all markdown links"""
        print("🔗 Validating links...")
        
        for file_path in md_files:
            try:
                content = file_path.read_text(encoding='utf-8')
                lines = content.split('\n')
                
                for line_num, line in enumerate(lines, 1):
                    links = self.markdown_link_pattern.findall(line)
                    
                    for link_text, link_url in links:
                        self._check_link(file_path, line_num, link_text, link_url)
                        
            except Exception as e:
                self.report.add_issue(ValidationIssue(
                    file_path=str(file_path),
                    line_number=0,
                    issue_type="file_read_error",
                    severity="error",
                    message=f"Could not read file: {e}"
                ))
    
    def _check_link(self, file_path: Path, line_num: int, link_text: str, link_url: str):
        """Check individual link"""
        # Skip anchors and external URLs for now (focus on internal links)
        if link_url.startswith('#') or link_url.startswith('http'):
            if link_url.startswith('http'):
                # Quick external link check (optional)
                try:
                    response = requests.head(link_url, timeout=5, allow_redirects=True)
                    if response.status_code >= 400:
                        self.report.add_issue(ValidationIssue(
                            file_path=str(file_path),
                            line_number=line_num,
                            issue_type="broken_external_link",
                            severity="warning",
                            message=f"External link returns {response.status_code}: {link_url}"
                        ))
                except:
                    # Don't fail on external link checks
                    pass
            return
        
        # Check internal links
        if link_url.startswith('/'):
            # Absolute path from docs root
            target_path = self.docs_path / link_url.lstrip('/')
        else:
            # Relative path
            target_path = file_path.parent / link_url
        
        # Remove anchor if present
        if '#' in str(target_path):
            target_path = Path(str(target_path).split('#')[0])
        
        if not target_path.exists():
            self.report.add_issue(ValidationIssue(
                file_path=str(file_path),
                line_number=line_num,
                issue_type="broken_internal_link",
                severity="error",
                message=f"Broken internal link: {link_url} -> {target_path}",
                suggestion=f"Check if file exists or update link path"
            ))
    
    def _validate_code_examples(self, md_files: List[Path]):
        """Validate code examples in markdown files"""
        print("💻 Validating code examples...")
        
        for file_path in md_files:
            try:
                content = file_path.read_text(encoding='utf-8')
                code_blocks = self.code_block_pattern.findall(content)
                
                for i, (language, code) in enumerate(code_blocks):
                    self._check_code_block(file_path, language, code, i)
                    
            except Exception as e:
                self.report.add_issue(ValidationIssue(
                    file_path=str(file_path),
                    line_number=0,
                    issue_type="file_read_error",
                    severity="error",
                    message=f"Could not read file for code validation: {e}"
                ))
    
    def _check_code_block(self, file_path: Path, language: str, code: str, block_index: int):
        """Check individual code block"""
        if language == 'python':
            # Check Python syntax
            try:
                ast.parse(code)
            except SyntaxError as e:
                self.report.add_issue(ValidationIssue(
                    file_path=str(file_path),
                    line_number=0,  # Would need more complex parsing to get exact line
                    issue_type="python_syntax_error",
                    severity="error",
                    message=f"Python syntax error in code block {block_index + 1}: {e}",
                    suggestion="Fix Python syntax in code example"
                ))
            
            # Check for audience tags
            if not self.audience_tag_pattern.search(code):
                # Only warn for code blocks that look like they should have audience tags
                if any(keyword in code.lower() for keyword in ['adri', 'assessor', 'guard', 'connector']):
                    self.report.add_issue(ValidationIssue(
                        file_path=str(file_path),
                        line_number=0,
                        issue_type="missing_audience_tag",
                        severity="warning",
                        message=f"Code block {block_index + 1} may need audience tag",
                        suggestion="Add # [AI_BUILDER], # [DATA_PROVIDER], or # [STANDARD_CONTRIBUTOR] tag"
                    ))
        
        elif language == 'bash':
            # Basic bash validation - check for common issues
            if 'rm -rf /' in code:
                self.report.add_issue(ValidationIssue(
                    file_path=str(file_path),
                    line_number=0,
                    issue_type="dangerous_command",
                    severity="error",
                    message=f"Dangerous command in bash code block {block_index + 1}",
                    suggestion="Remove or modify dangerous command"
                ))
    
    def _validate_project_index(self):
        """Validate PROJECT_INDEX.md against actual file structure"""
        print("📋 Validating PROJECT_INDEX.md...")
        
        if not self.project_index_path.exists():
            self.report.add_issue(ValidationIssue(
                file_path=str(self.project_index_path),
                line_number=0,
                issue_type="missing_project_index",
                severity="error",
                message="PROJECT_INDEX.md not found"
            ))
            return
        
        try:
            content = self.project_index_path.read_text(encoding='utf-8')
            
            # Extract file references from PROJECT_INDEX.md
            referenced_files = set()
            lines = content.split('\n')
            
            for line_num, line in enumerate(lines, 1):
                # Look for markdown file references
                matches = re.findall(r'\*\*([^*]+\.md)\*\*', line)
                for match in matches:
                    referenced_files.add(match)
                
                # Look for file paths in tables
                if '|' in line and '.md' in line:
                    parts = line.split('|')
                    for part in parts:
                        if '.md' in part:
                            # Extract filename
                            match = re.search(r'([^/\s]+\.md)', part)
                            if match:
                                referenced_files.add(match.group(1))
            
            # Check if referenced files exist
            for ref_file in referenced_files:
                found = False
                for actual_file in self.docs_path.rglob("*.md"):
                    if actual_file.name == ref_file:
                        found = True
                        break
                
                if not found and ref_file != "README.md":  # README.md is in root
                    self.report.add_issue(ValidationIssue(
                        file_path=str(self.project_index_path),
                        line_number=0,
                        issue_type="missing_referenced_file",
                        severity="warning",
                        message=f"File referenced in PROJECT_INDEX.md not found: {ref_file}",
                        suggestion=f"Create {ref_file} or remove reference from PROJECT_INDEX.md"
                    ))
                    
        except Exception as e:
            self.report.add_issue(ValidationIssue(
                file_path=str(self.project_index_path),
                line_number=0,
                issue_type="project_index_read_error",
                severity="error",
                message=f"Could not validate PROJECT_INDEX.md: {e}"
            ))
    
    def _validate_file_structure(self):
        """Validate expected file structure exists"""
        print("🏗️ Validating file structure...")
        
        expected_structure = {
            "docs/index.md": "Main documentation hub",
            "docs/ai-builders/index.md": "AI Builders landing page",
            "docs/data-providers/index.md": "Data Providers landing page", 
            "docs/standard-contributors/index.md": "Standard Contributors landing page",
            "docs/reference/api/index.md": "API reference",
            "docs/reference/dimensions/index.md": "Dimensions reference",
            "docs/examples/index.md": "Examples index"
        }
        
        for file_path, description in expected_structure.items():
            full_path = self.root_path / file_path
            if not full_path.exists():
                self.report.add_issue(ValidationIssue(
                    file_path=file_path,
                    line_number=0,
                    issue_type="missing_expected_file",
                    severity="error",
                    message=f"Expected file missing: {description}",
                    suggestion=f"Create {file_path}"
                ))
    
    def _detect_legacy_content(self):
        """Detect legacy content that should be migrated or removed"""
        print("🗂️ Detecting legacy content...")
        
        # Files that should have been migrated
        legacy_patterns = [
            "docs/QUICKSTART.md",
            "docs/API_REFERENCE.md", 
            "docs/UNDERSTANDING_DIMENSIONS.md",
            "docs/UNDERSTANDING_TEMPLATES.md",
            "docs/CONTRIBUTING_TEMPLATES.md"
        ]
        
        for pattern in legacy_patterns:
            legacy_path = self.root_path / pattern
            if legacy_path.exists():
                self.report.add_issue(ValidationIssue(
                    file_path=pattern,
                    line_number=0,
                    issue_type="legacy_content_found",
                    severity="warning",
                    message=f"Legacy file still exists: {pattern}",
                    suggestion=f"Remove or migrate content from {pattern}"
                ))
        
        # Check for old directory structures
        old_dirs = [
            "docs/getting-started",
            "docs/concepts", 
            "docs/guides"
        ]
        
        for old_dir in old_dirs:
            old_path = self.root_path / old_dir
            if old_path.exists() and any(old_path.iterdir()):
                self.report.add_issue(ValidationIssue(
                    file_path=old_dir,
                    line_number=0,
                    issue_type="legacy_directory_found",
                    severity="warning",
                    message=f"Legacy directory still contains files: {old_dir}",
                    suggestion=f"Migrate or remove content from {old_dir}"
                ))
    
    def _validate_audience_tags(self, md_files: List[Path]):
        """Validate audience tags in code examples"""
        print("🎯 Validating audience tags...")
        
        audience_specific_files = [
            ("ai-builders", "AI_BUILDER"),
            ("data-providers", "DATA_PROVIDER"), 
            ("standard-contributors", "STANDARD_CONTRIBUTOR")
        ]
        
        for file_path in md_files:
            if any(audience_dir in str(file_path) for audience_dir, _ in audience_specific_files):
                try:
                    content = file_path.read_text(encoding='utf-8')
                    
                    # Find expected audience for this file
                    expected_audience = None
                    for audience_dir, audience_tag in audience_specific_files:
                        if audience_dir in str(file_path):
                            expected_audience = audience_tag
                            break
                    
                    if expected_audience:
                        # Check if code blocks have appropriate audience tags
                        code_blocks = self.code_block_pattern.findall(content)
                        for i, (language, code) in enumerate(code_blocks):
                            if language == 'python' and 'adri' in code.lower():
                                if expected_audience not in code:
                                    self.report.add_issue(ValidationIssue(
                                        file_path=str(file_path),
                                        line_number=0,
                                        issue_type="incorrect_audience_tag",
                                        severity="warning",
                                        message=f"Code block {i + 1} should have {expected_audience} tag",
                                        suggestion=f"Add # [{expected_audience}] to code block"
                                    ))
                                    
                except Exception as e:
                    self.report.add_issue(ValidationIssue(
                        file_path=str(file_path),
                        line_number=0,
                        issue_type="audience_validation_error",
                        severity="error",
                        message=f"Could not validate audience tags: {e}"
                    ))

def generate_html_report(report: ValidationReport, output_path: str):
    """Generate HTML validation report"""
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>ADRI Documentation Validation Report</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .header { background: #f5f5f5; padding: 20px; border-radius: 5px; }
            .summary { display: flex; gap: 20px; margin: 20px 0; }
            .summary-card { background: #fff; border: 1px solid #ddd; padding: 15px; border-radius: 5px; flex: 1; }
            .error { color: #d32f2f; }
            .warning { color: #f57c00; }
            .info { color: #1976d2; }
            .issue { margin: 10px 0; padding: 10px; border-left: 4px solid #ddd; }
            .issue.error { border-left-color: #d32f2f; background: #ffebee; }
            .issue.warning { border-left-color: #f57c00; background: #fff3e0; }
            .issue.info { border-left-color: #1976d2; background: #e3f2fd; }
            .file-path { font-family: monospace; font-size: 0.9em; color: #666; }
            .suggestion { font-style: italic; color: #666; margin-top: 5px; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🔍 ADRI Documentation Validation Report</h1>
            <p><strong>Generated:</strong> {timestamp}</p>
            <p><strong>Files Checked:</strong> {total_files}</p>
        </div>
        
        <div class="summary">
            <div class="summary-card">
                <h3 class="error">❌ Errors</h3>
                <h2>{errors}</h2>
            </div>
            <div class="summary-card">
                <h3 class="warning">⚠️ Warnings</h3>
                <h2>{warnings}</h2>
            </div>
            <div class="summary-card">
                <h3 class="info">ℹ️ Info</h3>
                <h2>{info}</h2>
            </div>
        </div>
        
        <h2>Issues Found</h2>
        {issues_html}
    </body>
    </html>
    """
    
    issues_html = ""
    for issue in report.issues:
        suggestion_html = f'<div class="suggestion">💡 {issue.suggestion}</div>' if issue.suggestion else ""
        issues_html += f"""
        <div class="issue {issue.severity}">
            <strong>{issue.issue_type.replace('_', ' ').title()}</strong>
            <div class="file-path">{issue.file_path}:{issue.line_number}</div>
            <div>{issue.message}</div>
            {suggestion_html}
        </div>
        """
    
    html_content = html_template.format(
        timestamp=report.timestamp,
        total_files=report.total_files_checked,
        errors=report.summary.get('error', 0),
        warnings=report.summary.get('warning', 0),
        info=report.summary.get('info', 0),
        issues_html=issues_html
    )
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

def main():
    parser = argparse.ArgumentParser(description='Validate ADRI documentation')
    parser.add_argument('--root', default='adri', help='Root directory path')
    parser.add_argument('--report-format', choices=['html', 'json', 'text'], default='html', help='Report format')
    parser.add_argument('--output', default='validation_report', help='Output file prefix')
    parser.add_argument('--fix', action='store_true', help='Attempt to fix issues automatically')
    
    args = parser.parse_args()
    
    # Run validation
    validator = DocumentationValidator(args.root)
    report = validator.validate_all()
    
    # Generate report
    if args.report_format == 'html':
        output_file = f"{args.output}.html"
        generate_html_report(report, output_file)
        print(f"📊 HTML report generated: {output_file}")
    elif args.report_format == 'json':
        output_file = f"{args.output}.json"
        with open(output_file, 'w') as f:
            json.dump(asdict(report), f, indent=2)
        print(f"📊 JSON report generated: {output_file}")
    else:
        # Text output
        print("\n" + "="*60)
        print("📊 VALIDATION SUMMARY")
        print("="*60)
        print(f"Files checked: {report.total_files_checked}")
        print(f"Issues found: {len(report.issues)}")
        for severity, count in report.summary.items():
            print(f"  {severity}: {count}")
        
        if report.issues:
            print("\n" + "="*60)
            print("🔍 ISSUES FOUND")
            print("="*60)
            for issue in report.issues:
                print(f"\n{issue.severity.upper()}: {issue.issue_type}")
                print(f"File: {issue.file_path}:{issue.line_number}")
                print(f"Message: {issue.message}")
                if issue.suggestion:
                    print(f"Suggestion: {issue.suggestion}")
    
    # Exit with error code if issues found
    error_count = report.summary.get('error', 0)
    if error_count > 0:
        print(f"\n❌ Validation failed with {error_count} errors")
        sys.exit(1)
    else:
        print(f"\n✅ Validation passed!")
        sys.exit(0)

if __name__ == "__main__":
    main()
