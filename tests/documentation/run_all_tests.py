"""
Phase 5: Comprehensive documentation test runner with enhanced reporting
"""
import sys
import os
import yaml
import argparse
import unittest
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import json

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from test_code_examples import TestCodeExamples
from test_links import TestLinks
from test_vision_alignment import TestVisionAlignment
from test_content_structure import TestContentStructure


class DocumentationTestRunner:
    """Comprehensive test runner for all documentation tests"""
    
    def __init__(self, config_path: str = None):
        self.project_root = project_root
        self.config = self._load_config(config_path)
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'phases': {},
            'summary': {}
        }
    
    def _load_config(self, config_path: str = None) -> Dict:
        """Load test configuration"""
        if config_path is None:
            config_path = self.project_root / "tests/documentation/test_config.yaml"
        
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def run_all_tests(self, phases: List[str] = None) -> bool:
        """Run all documentation tests"""
        print("=" * 80)
        print("ADRI Documentation Test Suite")
        print("=" * 80)
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Configuration: {self.config.get('documentation', {}).get('paths', [])}")
        print("=" * 80 + "\n")
        
        # Define test phases
        test_phases = {
            'code': {
                'name': 'Code Examples',
                'test_class': TestCodeExamples,
                'enabled': self.config.get('code_testing', {}).get('enabled', True)
            },
            'links': {
                'name': 'Link Validation',
                'test_class': TestLinks,
                'enabled': self.config.get('link_validation', {}).get('enabled', True)
            },
            'vision': {
                'name': 'Vision Alignment',
                'test_class': TestVisionAlignment,
                'enabled': self.config.get('vision_alignment', {}).get('enabled', True)
            },
            'structure': {
                'name': 'Content Structure',
                'test_class': TestContentStructure,
                'enabled': self.config.get('content_structure', {}).get('enabled', True)
            }
        }
        
        # Filter phases if specified
        if phases:
            test_phases = {k: v for k, v in test_phases.items() if k in phases}
        
        # Run each phase
        all_passed = True
        for phase_id, phase_info in test_phases.items():
            if not phase_info['enabled']:
                print(f"\n⏭️  Skipping {phase_info['name']} (disabled in config)")
                continue
            
            print(f"\n{'#' * 80}")
            print(f"# Phase: {phase_info['name']}")
            print(f"{'#' * 80}\n")
            
            # Run tests
            suite = unittest.TestLoader().loadTestsFromTestCase(phase_info['test_class'])
            runner = unittest.TextTestRunner(verbosity=2)
            result = runner.run(suite)
            
            # Store results
            phase_passed = result.wasSuccessful()
            self.results['phases'][phase_id] = {
                'name': phase_info['name'],
                'passed': phase_passed,
                'tests_run': result.testsRun,
                'failures': len(result.failures),
                'errors': len(result.errors),
                'skipped': len(result.skipped) if hasattr(result, 'skipped') else 0
            }
            
            if not phase_passed:
                all_passed = False
        
        # Generate summary
        self._generate_summary()
        
        # Generate reports
        if self.config.get('reporting', {}).get('generate_html', True):
            self._generate_html_report()
        
        if self.config.get('reporting', {}).get('generate_markdown', True):
            self._generate_markdown_report()
        
        # Generate GitHub Actions output if enabled
        if self.config.get('reporting', {}).get('github_actions', {}).get('enabled', False):
            self._generate_github_actions_output()
        
        return all_passed
    
    def _generate_summary(self):
        """Generate test summary"""
        total_tests = sum(p['tests_run'] for p in self.results['phases'].values())
        total_failures = sum(p['failures'] for p in self.results['phases'].values())
        total_errors = sum(p['errors'] for p in self.results['phases'].values())
        total_passed = total_tests - total_failures - total_errors
        
        self.results['summary'] = {
            'total_tests': total_tests,
            'passed': total_passed,
            'failed': total_failures,
            'errors': total_errors,
            'pass_rate': (total_passed / total_tests * 100) if total_tests > 0 else 0
        }
        
        # Print summary
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {total_passed} ({self.results['summary']['pass_rate']:.1f}%)")
        print(f"Failed: {total_failures}")
        print(f"Errors: {total_errors}")
        print("=" * 80)
    
    def _generate_html_report(self):
        """Generate comprehensive HTML report"""
        output_path = Path(self.config['reporting']['html_output_path'])
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>ADRI Documentation Test Report</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 30px;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .summary-card {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            border: 1px solid #e9ecef;
        }}
        .summary-card h3 {{
            margin: 0 0 10px 0;
            color: #495057;
            font-size: 14px;
            text-transform: uppercase;
        }}
        .summary-card .value {{
            font-size: 36px;
            font-weight: bold;
            margin: 0;
        }}
        .passed {{ color: #28a745; }}
        .failed {{ color: #dc3545; }}
        .warning {{ color: #ffc107; }}
        .info {{ color: #17a2b8; }}
        .phase {{
            margin: 20px 0;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 8px;
            border-left: 4px solid #dee2e6;
        }}
        .phase.success {{ border-color: #28a745; }}
        .phase.failure {{ border-color: #dc3545; }}
        .phase-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .phase-stats {{
            display: flex;
            gap: 20px;
            font-size: 14px;
        }}
        .timestamp {{
            color: #6c757d;
            font-size: 14px;
            text-align: right;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #e9ecef;
            text-align: center;
            color: #6c757d;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📚 ADRI Documentation Test Report</h1>
        <p class="timestamp">Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <div class="summary">
            <div class="summary-card">
                <h3>Total Tests</h3>
                <p class="value info">{self.results['summary']['total_tests']}</p>
            </div>
            <div class="summary-card">
                <h3>Passed</h3>
                <p class="value passed">{self.results['summary']['passed']}</p>
            </div>
            <div class="summary-card">
                <h3>Failed</h3>
                <p class="value failed">{self.results['summary']['failed']}</p>
            </div>
            <div class="summary-card">
                <h3>Pass Rate</h3>
                <p class="value {'passed' if self.results['summary']['pass_rate'] >= 80 else 'warning'}">{self.results['summary']['pass_rate']:.1f}%</p>
            </div>
        </div>
        
        <h2>Test Phases</h2>
"""
        
        for phase_id, phase_data in self.results['phases'].items():
            status_class = 'success' if phase_data['passed'] else 'failure'
            status_icon = '✅' if phase_data['passed'] else '❌'
            
            html_content += f"""
        <div class="phase {status_class}">
            <div class="phase-header">
                <h3>{status_icon} {phase_data['name']}</h3>
                <div class="phase-stats">
                    <span>Tests: {phase_data['tests_run']}</span>
                    <span>Failed: {phase_data['failures']}</span>
                    <span>Errors: {phase_data['errors']}</span>
                </div>
            </div>
        </div>
"""
        
        html_content += """
        <div class="footer">
            <p>ADRI - Agent Data Readiness Index</p>
            <p>Documentation tests ensure code examples work, links are valid, and content aligns with vision.</p>
        </div>
    </div>
</body>
</html>
"""
        
        with open(output_path, 'w') as f:
            f.write(html_content)
        
        print(f"\n📊 HTML report generated: {output_path}")
    
    def _generate_markdown_report(self):
        """Generate Markdown summary report"""
        output_path = Path(self.config['reporting']['markdown_output_path'])
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        md_content = f"""# ADRI Documentation Test Report

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary

| Metric | Value |
|--------|-------|
| Total Tests | {self.results['summary']['total_tests']} |
| Passed | {self.results['summary']['passed']} |
| Failed | {self.results['summary']['failed']} |
| Pass Rate | {self.results['summary']['pass_rate']:.1f}% |

## Test Phases

"""
        
        for phase_id, phase_data in self.results['phases'].items():
            status = '✅ PASSED' if phase_data['passed'] else '❌ FAILED'
            md_content += f"""### {phase_data['name']} {status}

- Tests Run: {phase_data['tests_run']}
- Failures: {phase_data['failures']}
- Errors: {phase_data['errors']}

"""
        
        md_content += """---

*This report was automatically generated by the ADRI Documentation Test Suite.*
"""
        
        with open(output_path, 'w') as f:
            f.write(md_content)
        
        print(f"📝 Markdown report generated: {output_path}")
    
    def _generate_github_actions_output(self):
        """Generate output for GitHub Actions"""
        # Write summary to GitHub Actions
        if os.environ.get('GITHUB_ACTIONS'):
            summary_file = os.environ.get('GITHUB_STEP_SUMMARY')
            if summary_file:
                with open(summary_file, 'a') as f:
                    f.write("\n## 📚 Documentation Test Results\n\n")
                    f.write(f"- **Total Tests**: {self.results['summary']['total_tests']}\n")
                    f.write(f"- **Passed**: {self.results['summary']['passed']}\n")
                    f.write(f"- **Failed**: {self.results['summary']['failed']}\n")
                    f.write(f"- **Pass Rate**: {self.results['summary']['pass_rate']:.1f}%\n")
        
        # Save results as JSON for other tools
        results_path = self.project_root / "tests/documentation/reports/results.json"
        results_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(results_path, 'w') as f:
            json.dump(self.results, f, indent=2)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Run ADRI documentation tests')
    parser.add_argument(
        '--config',
        help='Path to test configuration file',
        default=None
    )
    parser.add_argument(
        '--phases',
        help='Comma-separated list of phases to run (code,links,vision,structure)',
        default=None
    )
    parser.add_argument(
        '--skip-external',
        action='store_true',
        help='Skip external link validation'
    )
    
    args = parser.parse_args()
    
    # Parse phases
    phases = None
    if args.phases:
        phases = [p.strip() for p in args.phases.split(',')]
    
    # Set environment variable for skipping external links
    if args.skip_external:
        os.environ['SKIP_EXTERNAL_LINKS'] = '1'
    
    # Run tests
    runner = DocumentationTestRunner(args.config)
    success = runner.run_all_tests(phases)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
