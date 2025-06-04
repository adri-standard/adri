#!/usr/bin/env python3
"""
ADRI Template TDD Runner
Helps run and validate template tests
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path
from typing import List, Dict, Tuple
import yaml
import json
from datetime import datetime


class TemplateTDDRunner:
    """Manages test-driven template development"""
    
    def __init__(self):
        self.dev_path = Path(__file__).parent.parent / "adri" / "templates" / "development"
        self.tests_path = self.dev_path / "tests"
        self.templates_path = self.dev_path / "templates"
        
    def run_tests(self, specific_test: str = None, verbose: bool = True) -> Tuple[bool, str]:
        """Run template tests"""
        cmd = ["python3", "-m", "pytest"]
        
        if specific_test:
            test_file = self.tests_path / f"test_{specific_test}.py"
            if not test_file.exists():
                return False, f"Test file not found: {test_file}"
            cmd.append(str(test_file))
        else:
            cmd.append(str(self.tests_path))
        
        if verbose:
            cmd.append("-v")
        
        # Add color output
        cmd.extend(["--color=yes", "--tb=short"])
        
        # Run tests
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        success = result.returncode == 0
        output = result.stdout + result.stderr
        
        return success, output
    
    def get_test_status(self) -> Dict[str, str]:
        """Get status of all template tests"""
        status = {}
        
        # Define expected test files
        templates = [
            "invoice_processing",
            "crm_opportunities", 
            "inventory_management",
            "patient_records",
            "support_tickets"
        ]
        
        for template in templates:
            test_file = self.tests_path / f"test_{template}.py"
            template_file = self.templates_path / f"{template.replace('_', '-')}-v1.0.0.yaml"
            
            if not test_file.exists():
                status[template] = "⚪ Not Started"
            elif not template_file.exists():
                status[template] = "🔴 Tests Only"
            else:
                # Run test to check if passing
                success, _ = self.run_tests(template, verbose=False)
                if success:
                    status[template] = "🟢 All Pass"
                else:
                    status[template] = "🟡 In Progress"
        
        return status
    
    def create_template_stub(self, template_name: str):
        """Create a minimal template stub to start TDD"""
        template_file = self.templates_path / f"{template_name.replace('_', '-')}-v1.0.0.yaml"
        
        if template_file.exists():
            print(f"❌ Template already exists: {template_file}")
            return
        
        # Create minimal structure
        stub = {
            "template": {
                "id": f"category/{template_name.replace('_', '-')}-v1.0.0",
                "name": template_name.replace('_', ' ').title(),
                "version": "1.0.0",
                "description": f"Template for {template_name.replace('_', ' ')} - UNDER DEVELOPMENT"
            },
            "pattern_matching": {
                "required_columns": []
            },
            "requirements": {
                "overall_minimum": 70
            },
            "dimensions": {
                "validity": {"rules": []},
                "completeness": {"rules": []},
                "consistency": {"rules": []},
                "freshness": {"rules": []},
                "plausibility": {"rules": []}
            }
        }
        
        template_file.parent.mkdir(parents=True, exist_ok=True)
        with open(template_file, 'w') as f:
            yaml.dump(stub, f, default_flow_style=False, sort_keys=False)
        
        print(f"✅ Created template stub: {template_file}")
        print("   Now run tests and add rules to make them pass!")
    
    def coverage_report(self):
        """Generate test coverage report"""
        cmd = [
            "python3", "-m", "pytest",
            str(self.tests_path),
            "--cov=.",
            "--cov-report=html",
            "--cov-report=term"
        ]
        
        subprocess.run(cmd)
        print("\n📊 Coverage report generated in htmlcov/")
    
    def watch_mode(self, template: str = None):
        """Run tests in watch mode"""
        cmd = ["python3", "-m", "pytest-watch"]
        
        if template:
            cmd.extend(["-p", f"test_{template}.py"])
        
        cmd.append(str(self.tests_path))
        
        print("👀 Running tests in watch mode (Ctrl+C to exit)")
        subprocess.run(cmd)
    
    def validate_template(self, template_name: str) -> List[str]:
        """Validate a template meets all requirements"""
        issues = []
        
        template_file = self.templates_path / f"{template_name.replace('_', '-')}-v1.0.0.yaml"
        
        if not template_file.exists():
            issues.append("Template file does not exist")
            return issues
        
        with open(template_file) as f:
            template = yaml.safe_load(f)
        
        # Check structure
        if not template.get("template", {}).get("id"):
            issues.append("Missing template ID")
        
        if not template.get("pattern_matching", {}).get("required_columns"):
            issues.append("No required columns defined")
        
        # Check dimensions
        dimensions = template.get("dimensions", {})
        for dim in ["validity", "completeness", "consistency", "freshness", "plausibility"]:
            if not dimensions.get(dim, {}).get("rules"):
                issues.append(f"No rules defined for {dim} dimension")
        
        # Check thresholds
        min_score = template.get("requirements", {}).get("overall_minimum", 0)
        if min_score < 70:
            issues.append(f"Minimum score too low: {min_score} (should be >= 70)")
        
        return issues
    
    def report(self):
        """Generate status report"""
        print("\n" + "="*60)
        print("📊 ADRI Template Development Status Report")
        print("="*60)
        print(f"\n📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Test status
        print("\n📋 Template Status:")
        print("-" * 40)
        status = self.get_test_status()
        for template, state in status.items():
            print(f"  {template:<25} {state}")
        
        # Summary stats
        total = len(status)
        completed = sum(1 for s in status.values() if "All Pass" in s)
        in_progress = sum(1 for s in status.values() if "In Progress" in s)
        tests_only = sum(1 for s in status.values() if "Tests Only" in s)
        
        print("\n📈 Summary:")
        print(f"  Total Templates: {total}")
        print(f"  ✅ Completed: {completed}")
        print(f"  🟡 In Progress: {in_progress}")
        print(f"  🔴 Tests Only: {tests_only}")
        print(f"  ⚪ Not Started: {total - completed - in_progress - tests_only}")
        
        print("\n" + "="*60)


def main():
    parser = argparse.ArgumentParser(description="ADRI Template TDD Runner")
    
    parser.add_argument("command", choices=["test", "status", "create", "validate", "coverage", "watch", "report"],
                       help="Command to run")
    parser.add_argument("template", nargs="?", help="Specific template to target")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    runner = TemplateTDDRunner()
    
    if args.command == "test":
        success, output = runner.run_tests(args.template, args.verbose)
        print(output)
        sys.exit(0 if success else 1)
    
    elif args.command == "status":
        status = runner.get_test_status()
        for template, state in status.items():
            print(f"{template:<30} {state}")
    
    elif args.command == "create":
        if not args.template:
            print("❌ Please specify a template name")
            sys.exit(1)
        runner.create_template_stub(args.template)
    
    elif args.command == "validate":
        if not args.template:
            print("❌ Please specify a template name")
            sys.exit(1)
        issues = runner.validate_template(args.template)
        if issues:
            print(f"❌ Validation failed for {args.template}:")
            for issue in issues:
                print(f"  - {issue}")
        else:
            print(f"✅ Template {args.template} is valid")
    
    elif args.command == "coverage":
        runner.coverage_report()
    
    elif args.command == "watch":
        runner.watch_mode(args.template)
    
    elif args.command == "report":
        runner.report()


if __name__ == "__main__":
    main()
