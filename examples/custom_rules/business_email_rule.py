#!/usr/bin/env python3
"""
Business Email Rule - Example Custom ADRI Rule

This rule validates that email addresses are from business domains rather than
personal email providers. It's configurable to allow customization of which
domains are considered "personal".

Usage:
    python business_email_rule.py  # Run standalone demo
    
    # Or use in ADRI assessment:
    from business_email_rule import BusinessEmailRule
"""

from adri.rules.base import DiagnosticRule
from adri.rules.registry import RuleRegistry
import pandas as pd
from typing import Dict, Any


@RuleRegistry.register
class BusinessEmailRule(DiagnosticRule):
    """Ensures email addresses are from business domains, not personal ones."""
    
    rule_id = "custom.business_email"
    dimension = "validity"
    name = "Business Email Validation"
    description = "Checks that email addresses are from business domains"
    version = "1.0.0"
    
    def evaluate(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Check if email addresses are from business domains."""
        if 'email' not in data.columns:
            return {
                "score": self.params.get("weight", 1.0),
                "valid": True,
                "findings": ["No email column found to validate"]
            }
        
        # Default list of personal email domains
        personal_domains = self.params.get("personal_domains", [
            'gmail.com', 'yahoo.com', 'outlook.com', 'hotmail.com',
            'aol.com', 'icloud.com', 'mail.com', 'protonmail.com',
            'yahoo.co.uk', 'gmail.co.uk', 'live.com', 'msn.com',
            'me.com', 'mac.com', 'ymail.com', 'rocketmail.com'
        ])
        
        # Get non-null emails
        emails = data['email'].dropna()
        if len(emails) == 0:
            return {
                "score": self.params.get("weight", 1.0),
                "valid": True,
                "findings": ["No emails to validate"]
            }
        
        # Extract domains (handle invalid emails gracefully)
        domains = emails.str.lower().str.extract(r'@([^@\s]+)$')[0]
        valid_emails = domains.notna()
        
        if not valid_emails.any():
            return {
                "score": 0.0,
                "valid": False,
                "findings": ["No valid email addresses found"],
                "details": {"valid_email_count": 0}
            }
        
        # Check against personal domains
        personal_mask = domains.isin(personal_domains)
        personal_count = personal_mask.sum()
        valid_count = valid_emails.sum()
        business_count = valid_count - personal_count
        business_ratio = business_count / valid_count
        
        # Identify which personal domains were found
        found_personal = domains[personal_mask].value_counts().to_dict()
        
        findings = [
            f"Business email ratio: {business_ratio:.1%}",
            f"Found {personal_count} personal emails out of {valid_count} valid emails"
        ]
        
        if found_personal:
            top_personal = sorted(found_personal.items(), key=lambda x: x[1], reverse=True)[:3]
            findings.append(f"Top personal domains: {', '.join([f'{d} ({c})' for d, c in top_personal])}")
        
        return {
            "score": business_ratio * self.params.get("weight", 1.0),
            "valid": business_ratio >= self.params.get("threshold", 0.95),
            "findings": findings,
            "details": {
                "personal_count": int(personal_count),
                "business_count": int(business_count),
                "total_valid": int(valid_count),
                "business_ratio": business_ratio,
                "personal_domains_found": found_personal
            }
        }
    
    def generate_narrative(self, result: Dict[str, Any]) -> str:
        """Generate AI-friendly description of the results."""
        details = result.get("details", {})
        ratio = details.get("business_ratio", 0)
        personal = details.get("personal_count", 0)
        total = details.get("total_valid", 0)
        
        narrative = f"Email validation shows {ratio:.1%} business addresses. "
        
        if personal > 0:
            narrative += f"Found {personal} personal email addresses out of {total} total. "
            domains_found = details.get("personal_domains_found", {})
            if domains_found:
                narrative += f"Most common: {list(domains_found.keys())[0]}. "
        
        narrative += f"Rule {'passed' if result['valid'] else 'failed'}."
        return narrative


if __name__ == "__main__":
    """Standalone demo of the business email rule."""
    print("Business Email Rule Demo")
    print("=" * 50)
    
    # Create test data
    test_data = pd.DataFrame({
        'id': range(1, 11),
        'name': [f'User {i}' for i in range(1, 11)],
        'email': [
            'john.doe@acmecorp.com',      # Business
            'jane.smith@gmail.com',        # Personal
            'bob.wilson@enterprise.org',   # Business
            'alice@yahoo.com',             # Personal
            'charlie@customdomain.io',     # Business
            'david@outlook.com',           # Personal
            'eve@companyxyz.net',          # Business
            'frank@hotmail.com',           # Personal
            'grace@businessinc.com',       # Business
            'henry@icloud.com',            # Personal
        ]
    })
    
    print("\nTest Data:")
    print(test_data)
    
    # Create and configure rule
    rule = BusinessEmailRule()
    rule.params = {
        'weight': 1.0,
        'threshold': 0.60,  # Require 60% business emails for demo
        'personal_domains': [
            'gmail.com', 'yahoo.com', 'outlook.com', 
            'hotmail.com', 'icloud.com'
        ]
    }
    
    # Evaluate
    print("\nEvaluating...")
    result = rule.evaluate(test_data)
    
    print("\nResults:")
    print(f"Score: {result['score']:.2f}")
    print(f"Valid: {result['valid']}")
    print("\nFindings:")
    for finding in result['findings']:
        print(f"  - {finding}")
    
    print("\nDetails:")
    details = result['details']
    print(f"  Business emails: {details['business_count']}")
    print(f"  Personal emails: {details['personal_count']}")
    print(f"  Business ratio: {details['business_ratio']:.1%}")
    
    print("\nAI Narrative:")
    print(rule.generate_narrative(result))
    
    # Test with different threshold
    print("\n" + "=" * 50)
    print("Testing with stricter threshold (95%)...")
    rule.params['threshold'] = 0.95
    result2 = rule.evaluate(test_data)
    print(f"Valid: {result2['valid']}")
    print(f"Narrative: {rule.generate_narrative(result2)}")
