#!/usr/bin/env python3
"""
Preflight check for open source readiness
Quick scan for critical issues before making repository public
"""

import os
import re
import json
from pathlib import Path
from typing import List, Dict, Tuple

class PreflightChecker:
    def __init__(self, root_path: str = "."):
        self.root_path = Path(root_path)
        self.issues = {
            "critical": [],
            "warning": [],
            "info": []
        }
        self.successes = []
        
    def check_test_outputs(self) -> None:
        """Find test output files that should be cleaned"""
        test_patterns = [
            "test_*.html",
            "test_*.json",
            "test_output.txt"
        ]
        
        test_files = []
        for pattern in test_patterns:
            test_files.extend(self.root_path.glob(pattern))
        
        if test_files:
            self.issues["critical"].append({
                "category": "Test Outputs",
                "files": [str(f.relative_to(self.root_path)) for f in test_files],
                "action": "Remove with: rm test_*.html test_*.json test_output.txt"
            })
        else:
            self.successes.append("No test output files found")
    
    def check_internal_references(self) -> None:
        """Scan for internal/private references"""
        patterns_to_check = [
            (r"ThinkEvolveSolve", "Personal/internal organization reference"),
            (r"internal\.", "Internal domain reference"),
            (r"private\.", "Private domain reference"),
            (r"TODO.*internal", "Internal TODO reference")
        ]
        
        files_to_scan = [
            "README.md",
            "CONTRIBUTING.md",
            "docs/*.md",
            "adri/**/*.py"
        ]
        
        found_references = []
        for file_pattern in files_to_scan:
            for file_path in self.root_path.glob(file_pattern):
                if file_path.is_file():
                    try:
                        content = file_path.read_text(encoding='utf-8')
                        for pattern, description in patterns_to_check:
                            matches = re.finditer(pattern, content, re.IGNORECASE)
                            for match in matches:
                                line_num = content[:match.start()].count('\n') + 1
                                found_references.append({
                                    "file": str(file_path.relative_to(self.root_path)),
                                    "line": line_num,
                                    "pattern": pattern,
                                    "description": description,
                                    "context": content.split('\n')[line_num-1].strip()
                                })
                    except Exception:
                        pass
        
        if found_references:
            self.issues["critical"].append({
                "category": "Internal References",
                "references": found_references[:5],  # Show first 5
                "total": len(found_references),
                "action": "Update references to use 'adri-standard' organization"
            })
        else:
            self.successes.append("No internal references found")
    
    def check_required_files(self) -> None:
        """Verify essential open source files exist"""
        required_files = {
            "README.md": "Project overview and getting started",
            "LICENSE": "Open source license",
            "CONTRIBUTING.md": "Contribution guidelines",
            "CODE_OF_CONDUCT.md": "Community code of conduct",
            "CHANGELOG.md": "Version history",
            ".gitignore": "Git ignore patterns"
        }
        
        missing_files = []
        for file_name, description in required_files.items():
            if not (self.root_path / file_name).exists():
                missing_files.append(f"{file_name} ({description})")
        
        if missing_files:
            self.issues["critical"].append({
                "category": "Missing Required Files",
                "files": missing_files,
                "action": "Create these essential files"
            })
        else:
            self.successes.append("All required files present")
    
    def check_community_files(self) -> None:
        """Check for community-oriented files"""
        community_files = {
            "SECURITY.md": "Security policy",
            ".github/ISSUE_TEMPLATE/bug_report.md": "Bug report template",
            ".github/ISSUE_TEMPLATE/feature_request.md": "Feature request template",
            ".github/PULL_REQUEST_TEMPLATE.md": "PR template",
            "GOVERNANCE.md": "Project governance",
            "CITATION.cff": "Citation information"
        }
        
        missing_files = []
        for file_path, description in community_files.items():
            if not (self.root_path / file_path).exists():
                missing_files.append(f"{file_path} ({description})")
        
        if missing_files:
            self.issues["warning"].append({
                "category": "Missing Community Files",
                "files": missing_files[:3],  # Show first 3
                "total": len(missing_files),
                "action": "Create these files for better community engagement"
            })
    
    def check_sensitive_patterns(self) -> None:
        """Look for potential secrets or sensitive data"""
        sensitive_patterns = [
            (r"(api[_-]?key|apikey)\s*[:=]\s*['\"]?[a-zA-Z0-9]{16,}", "API key"),
            (r"(secret|password|passwd|pwd)\s*[:=]\s*['\"]?[^\s]{8,}", "Secret/Password"),
            (r"(token)\s*[:=]\s*['\"]?[a-zA-Z0-9]{16,}", "Token"),
            (r"ssh-rsa\s+[a-zA-Z0-9+/]{100,}", "SSH key"),
            (r"-----BEGIN\s+(RSA|DSA|EC|OPENSSH)\s+PRIVATE\s+KEY-----", "Private key")
        ]
        
        exclude_dirs = {'.git', '__pycache__', 'htmlcov', 'venv', '.venv'}
        found_secrets = []
        
        for root, dirs, files in os.walk(self.root_path):
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            for file_name in files:
                if file_name.endswith(('.py', '.yaml', '.yml', '.json', '.env', '.sh')):
                    file_path = Path(root) / file_name
                    try:
                        content = file_path.read_text(encoding='utf-8')
                        for pattern, secret_type in sensitive_patterns:
                            if re.search(pattern, content, re.IGNORECASE):
                                found_secrets.append({
                                    "file": str(file_path.relative_to(self.root_path)),
                                    "type": secret_type
                                })
                                break
                    except Exception:
                        pass
        
        if found_secrets:
            self.issues["critical"].append({
                "category": "Potential Secrets",
                "secrets": found_secrets[:3],  # Show first 3
                "total": len(found_secrets),
                "action": "Remove secrets and use environment variables"
            })
        else:
            self.successes.append("No obvious secrets detected")
    
    def check_dev_artifacts(self) -> None:
        """Find development files that shouldn't be public"""
        dev_artifacts = {
            "htmlcov": "Coverage report directory",
            "Local_Archive": "Local archive directory",
            ".coverage": "Coverage data file",
            "*.pyc": "Python bytecode files",
            "__pycache__": "Python cache directories",
            ".env": "Environment files",
            "venv": "Virtual environment",
            ".venv": "Virtual environment",
            "*.log": "Log files",
            ".DS_Store": "macOS metadata"
        }
        
        found_artifacts = []
        for artifact, description in dev_artifacts.items():
            if "*" in artifact:
                # It's a pattern
                matches = list(self.root_path.rglob(artifact))
                if matches:
                    found_artifacts.append(f"{artifact} ({len(matches)} files)")
            else:
                # It's a specific file/dir
                path = self.root_path / artifact
                if path.exists():
                    found_artifacts.append(f"{artifact} ({description})")
        
        if found_artifacts:
            self.issues["warning"].append({
                "category": "Development Artifacts",
                "artifacts": found_artifacts[:5],  # Show first 5
                "total": len(found_artifacts),
                "action": "Add to .gitignore and remove from repository"
            })
    
    def check_repository_size(self) -> None:
        """Check if repository size is reasonable"""
        try:
            # Check .git directory size
            git_size = sum(f.stat().st_size for f in Path(self.root_path / ".git").rglob("*") if f.is_file())
            git_size_mb = git_size / (1024 * 1024)
            
            if git_size_mb > 100:
                self.issues["warning"].append({
                    "category": "Repository Size",
                    "size": f"{git_size_mb:.1f} MB",
                    "action": "Consider using git-filter-branch to reduce size"
                })
            else:
                self.successes.append(f"Repository size OK ({git_size_mb:.1f} MB)")
        except Exception:
            pass
    
    def generate_report(self) -> str:
        """Generate a formatted report"""
        report = []
        report.append("=" * 50)
        report.append("ADRI Open Source Preflight Check")
        report.append("=" * 50)
        report.append("")
        
        # Critical issues
        if self.issues["critical"]:
            report.append("🚨 CRITICAL ISSUES (Must fix before going public)")
            report.append("-" * 50)
            for issue in self.issues["critical"]:
                report.append(f"\n❌ {issue['category']}:")
                if "files" in issue:
                    for f in issue["files"][:5]:
                        report.append(f"   - {f}")
                    if "total" in issue and issue["total"] > 5:
                        report.append(f"   ... and {issue['total'] - 5} more")
                if "references" in issue:
                    for ref in issue["references"]:
                        report.append(f"   - {ref['file']}:{ref['line']} - {ref['description']}")
                    if issue["total"] > 5:
                        report.append(f"   ... and {issue['total'] - 5} more")
                if "secrets" in issue:
                    for secret in issue["secrets"]:
                        report.append(f"   - {secret['file']} ({secret['type']})")
                    if issue["total"] > 3:
                        report.append(f"   ... and {issue['total'] - 3} more")
                report.append(f"   [Action: {issue['action']}]")
        
        # Warnings
        if self.issues["warning"]:
            report.append("\n⚠️  WARNINGS (Recommended fixes)")
            report.append("-" * 50)
            for issue in self.issues["warning"]:
                report.append(f"\n⚠️  {issue['category']}:")
                if "files" in issue:
                    for f in issue["files"][:3]:
                        report.append(f"   - {f}")
                    if "total" in issue and issue["total"] > 3:
                        report.append(f"   ... and {issue['total'] - 3} more")
                if "artifacts" in issue:
                    for artifact in issue["artifacts"]:
                        report.append(f"   - {artifact}")
                    if issue["total"] > 5:
                        report.append(f"   ... and {issue['total'] - 5} more")
                if "size" in issue:
                    report.append(f"   - Current size: {issue['size']}")
                report.append(f"   [Action: {issue['action']}]")
        
        # Successes
        if self.successes:
            report.append("\n✅ PASSED CHECKS")
            report.append("-" * 50)
            for success in self.successes:
                report.append(f"✓ {success}")
        
        # Summary
        report.append("\n" + "=" * 50)
        critical_count = len(self.issues["critical"])
        warning_count = len(self.issues["warning"])
        
        if critical_count == 0 and warning_count == 0:
            report.append("🎉 Repository is ready for open source!")
        else:
            report.append(f"📊 Summary: {critical_count} critical issues, {warning_count} warnings")
            if critical_count > 0:
                report.append("   ⚠️  Fix critical issues before making repository public")
        
        report.append("=" * 50)
        
        return "\n".join(report)
    
    def run_all_checks(self) -> None:
        """Run all preflight checks"""
        print("Running preflight checks...")
        self.check_test_outputs()
        self.check_internal_references()
        self.check_required_files()
        self.check_community_files()
        self.check_sensitive_patterns()
        self.check_dev_artifacts()
        self.check_repository_size()
    
    def save_report(self, filename: str = "preflight_report.txt") -> None:
        """Save report to file"""
        report = self.generate_report()
        with open(filename, 'w') as f:
            f.write(report)
        print(f"\nReport saved to: {filename}")


def main():
    """Run the preflight checker"""
    checker = PreflightChecker()
    checker.run_all_checks()
    
    # Print report
    print(checker.generate_report())
    
    # Save report
    checker.save_report()


if __name__ == "__main__":
    main()
