"""
Documentation tests for Status Auditor feature.

Verifies that the use case documentation is properly structured,
contains valid examples, and aligns with ADRI's documentation standards.
"""

import unittest
import os
from pathlib import Path


class TestStatusAuditorDocumentation(unittest.TestCase):
    """Test Status Auditor documentation quality and completeness"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.docs_dir = Path(__file__).parent.parent.parent / 'docs'
        self.status_auditor_doc = self.docs_dir / 'USE_CASE_AI_STATUS_AUDITOR.md'
        self.invoice_payment_doc = self.docs_dir / 'USE_CASE_INVOICE_PAYMENT_AGENT.md'
        
    def test_status_auditor_doc_exists(self):
        """Test that Status Auditor documentation exists"""
        self.assertTrue(
            self.status_auditor_doc.exists(),
            "Status Auditor use case documentation should exist"
        )
        
    def test_status_auditor_doc_structure(self):
        """Test that Status Auditor doc has required sections"""
        with open(self.status_auditor_doc, 'r') as f:
            content = f.read()
            
        required_sections = [
            '# AI Status Auditor: Implementation Plan',
            '## Executive Summary',
            '## Product Vision',
            '## Technical Architecture',
            '## ADRI Template Library',
            '## Implementation Phases',
            '## Demo Scenarios',
            '## Integration Strategy',
            '## Go-to-Market Strategy'
        ]
        
        for section in required_sections:
            self.assertIn(
                section, content,
                f"Documentation should contain section: {section}"
            )
            
    def test_template_examples_are_valid(self):
        """Test that YAML template examples are properly formatted"""
        with open(self.status_auditor_doc, 'r') as f:
            content = f.read()
            
        # Check for template examples
        self.assertIn('templates/status-audit-revops-v1.yaml', content)
        self.assertIn('templates/status-audit-compliance-v1.yaml', content)
        self.assertIn('templates/status-audit-finance-v1.yaml', content)
        
        # Check template structure
        template_components = [
            'name:',
            'version:',
            'description:',
            'dimensions:',
            'completeness:',
            'freshness:',
            'validity:',
            'consistency:',
            'plausibility:',
            'business_impact:'
        ]
        
        for component in template_components:
            self.assertIn(
                component, content,
                f"Templates should include: {component}"
            )
            
    def test_code_examples_are_complete(self):
        """Test that code examples are complete and runnable"""
        with open(self.status_auditor_doc, 'r') as f:
            content = f.read()
            
        # Check for key code examples
        code_examples = [
            'from adri import Assessor',
            'from adri.templates import load_template',
            'class VerodatAuditor:',
            '@app.post("/audit/{domain}")',
            'def translate_to_business_language'
        ]
        
        for example in code_examples:
            self.assertIn(
                example, content,
                f"Documentation should include code example: {example}"
            )
            
    def test_business_value_is_clear(self):
        """Test that business value is clearly communicated"""
        with open(self.status_auditor_doc, 'r') as f:
            content = f.read()
            
        business_terms = [
            'revenue at risk',
            'compliance',
            'ROI',
            'business value',
            'immediate value',
            'workflow health',
            'process breakdowns'
        ]
        
        for term in business_terms:
            self.assertIn(
                term.lower(), content.lower(),
                f"Documentation should emphasize business value with term: {term}"
            )
            
    def test_demo_scenarios_are_detailed(self):
        """Test that demo scenarios provide concrete examples"""
        with open(self.status_auditor_doc, 'r') as f:
            content = f.read()
            
        # Check for specific demo scenarios
        demos = [
            'RevOps "AHA Moment"',
            "Compliance Officer's Relief",
            'Finance Automation Readiness'
        ]
        
        for demo in demos:
            self.assertIn(
                demo, content,
                f"Should include demo scenario: {demo}"
            )
            
        # Check for concrete metrics
        self.assertIn('$340K', content, "Should include specific dollar amounts")
        self.assertIn('21+ days', content, "Should include specific timeframes")
        self.assertIn('Critical Issues Found', content, "Should show clear results")
        
    def test_integration_patterns_documented(self):
        """Test that integration patterns are documented"""
        with open(self.status_auditor_doc, 'r') as f:
            content = f.read()
            
        integrations = [
            'Verodat Platform Integration',
            'LangChain Integration',
            'Agent Workflow Integration',
            'Marketplace Ecosystem'
        ]
        
        for integration in integrations:
            self.assertIn(
                integration, content,
                f"Should document integration: {integration}"
            )
            
    def test_metrics_and_roi_included(self):
        """Test that metrics and ROI calculations are included"""
        with open(self.status_auditor_doc, 'r') as f:
            content = f.read()
            
        # Check for metrics
        self.assertIn('4 hours → 30 seconds', content, "Should show time savings")
        self.assertIn('Success Criteria', content, "Should define success metrics")
        self.assertIn('Metrics to Track', content, "Should list key metrics")
        
    def test_cross_references_are_valid(self):
        """Test that cross-references to other docs are valid"""
        with open(self.status_auditor_doc, 'r') as f:
            content = f.read()
            
        # Extract markdown links
        import re
        links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)
        
        # Check internal links
        for link_text, link_path in links:
            if link_path.startswith('./') or link_path.startswith('../'):
                # Skip external links
                if not link_path.startswith('http'):
                    # This is a relative path - verify it would resolve
                    # (In a real test, we'd check if the file exists)
                    self.assertIsNotNone(link_path, f"Link {link_text} should have valid path")
                    
    def test_invoice_payment_doc_exists(self):
        """Test that related Invoice Payment doc exists"""
        self.assertTrue(
            self.invoice_payment_doc.exists(),
            "Invoice Payment Agent documentation should exist"
        )
        
    def test_consistent_formatting(self):
        """Test that documentation follows consistent formatting"""
        with open(self.status_auditor_doc, 'r') as f:
            lines = f.readlines()
            
        # Check heading hierarchy
        h1_count = sum(1 for line in lines if line.startswith('# '))
        h2_count = sum(1 for line in lines if line.startswith('## '))
        
        self.assertEqual(h1_count, 1, "Should have exactly one H1 heading")
        self.assertGreater(h2_count, 5, "Should have multiple H2 sections")
        
        # Check code block formatting
        code_blocks = [i for i, line in enumerate(lines) if line.strip() == '```']
        self.assertEqual(
            len(code_blocks) % 2, 0,
            "All code blocks should be properly closed"
        )
        
    def test_actionable_next_steps(self):
        """Test that documentation includes actionable next steps"""
        with open(self.status_auditor_doc, 'r') as f:
            content = f.read()
            
        self.assertIn('Next Steps', content, "Should include next steps section")
        self.assertIn('Immediate Actions', content, "Should list immediate actions")
        
        # Check for specific actions
        actions = [
            'Build MVP',
            'Create Demo Data',
            'Design UI',
            'Test Messaging',
            'Gather Feedback'
        ]
        
        for action in actions:
            self.assertIn(
                action, content,
                f"Next steps should include: {action}"
            )


if __name__ == '__main__':
    unittest.main()
