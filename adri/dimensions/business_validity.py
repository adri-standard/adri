"""
Business-focused validity assessments for discovery mode.

This module provides practical, business-oriented validity checks
that work on raw data without requiring metadata.
"""

import re
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime, timedelta
import pandas as pd


class BusinessValidityChecker:
    """
    Provides business-focused validity checks for common data patterns.
    """
    
    @staticmethod
    def check_crm_validity(df) -> Tuple[int, List[str], List[str]]:
        """
        Check validity issues specific to CRM data.
        
        Returns:
            Tuple of (issues_found, findings, recommendations)
        """
        issues = 0
        findings = []
        recommendations = []
        
        # Check for invalid amounts
        if 'amount' in df.columns:
            invalid_amounts = df['amount'].apply(lambda x: 
                BusinessValidityChecker._parse_number(x) < 0 
                if pd.notna(x) else False
            ).sum()
            
            if invalid_amounts > 0:
                issues += 1
                findings.append(f"❌ {invalid_amounts} deals have negative amounts")
                recommendations.append("Fix negative amounts in deal records")
        
        # Check for invalid email formats
        if 'contact_email' in df.columns:
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            invalid_emails = df['contact_email'].apply(lambda x: 
                not re.match(email_pattern, str(x)) 
                if pd.notna(x) and str(x).strip() else False
            ).sum()
            
            if invalid_emails > 0:
                issues += 1
                findings.append(f"📧 {invalid_emails} invalid email addresses")
                recommendations.append("Correct invalid email formats")
        
        # Check for invalid stage values
        if 'stage' in df.columns:
            valid_stages = ['prospecting', 'qualification', 'needs-analysis', 
                          'proposal', 'negotiation', 'closed-won', 'closed-lost']
            invalid_stages = ~df['stage'].isin(valid_stages + [None, ''])
            invalid_count = invalid_stages.sum()
            
            if invalid_count > 0:
                issues += 1
                findings.append(f"🎯 {invalid_count} opportunities have invalid stage values")
                recommendations.append("Standardize sales stage values")
        
        return issues, findings, recommendations
    
    @staticmethod
    def check_inventory_validity(df) -> Tuple[int, List[str], List[str]]:
        """
        Check validity issues specific to inventory data.
        """
        issues = 0
        findings = []
        recommendations = []
        
        # Check for negative thresholds
        if 'reorder_threshold' in df.columns:
            negative_thresholds = df['reorder_threshold'].apply(lambda x: 
                BusinessValidityChecker._parse_number(x) < 0 
                if pd.notna(x) else False
            ).sum()
            
            if negative_thresholds > 0:
                issues += 1
                findings.append(f"❌ {negative_thresholds} items have negative reorder thresholds")
                recommendations.append("Set valid reorder thresholds (must be >= 0)")
        
        # Check for negative quantities
        if 'quantity_on_hand' in df.columns:
            negative_qty = df['quantity_on_hand'].apply(lambda x: 
                BusinessValidityChecker._parse_number(x) < 0 
                if pd.notna(x) else False
            ).sum()
            
            if negative_qty > 0:
                issues += 1
                findings.append(f"📦 {negative_qty} items show negative inventory")
                recommendations.append("Investigate and correct negative inventory values")
        
        return issues, findings, recommendations
    
    @staticmethod
    def check_customer_validity(df) -> Tuple[int, List[str], List[str]]:
        """
        Check validity issues specific to customer data.
        """
        issues = 0
        findings = []
        recommendations = []
        
        # Check email validity
        if 'email' in df.columns:
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            invalid_emails = df['email'].apply(lambda x: 
                not re.match(email_pattern, str(x)) 
                if pd.notna(x) and str(x).strip() else False
            ).sum()
            
            if invalid_emails > 0:
                issues += 1
                findings.append(f"📧 {invalid_emails} invalid email addresses")
                recommendations.append("Validate and correct email formats")
        
        # Check phone number formats (basic check)
        if 'phone' in df.columns:
            # Simple check for reasonable phone number length
            invalid_phones = df['phone'].apply(lambda x: 
                len(str(x).strip()) < 7 or len(str(x).strip()) > 20
                if pd.notna(x) and str(x).strip() else False
            ).sum()
            
            if invalid_phones > 0:
                issues += 1
                findings.append(f"📞 {invalid_phones} invalid phone numbers")
                recommendations.append("Standardize phone number formats")
        
        return issues, findings, recommendations
    
    @staticmethod
    def _parse_number(value):
        """Safely parse a number from various formats."""
        if pd.isna(value):
            return 0
        try:
            # Handle pandas numeric types
            if isinstance(value, (int, float)):
                return float(value)
            # Remove currency symbols and commas
            clean = str(value).replace('$', '').replace(',', '').strip()
            return float(clean)
        except:
            return 0


def calculate_business_validity_score(df, data_type: str = None) -> Tuple[float, List[str], List[str]]:
    """
    Calculate a business-focused validity score.
    
    This scoring method starts at 100% and deducts points for issues found,
    similar to the quickstart approach.
    
    Args:
        df: DataFrame to assess
        data_type: Type of data ('crm', 'inventory', 'customer', or None for auto-detect)
        
    Returns:
        Tuple of (score 0-20, findings, recommendations)
    """
    try:
        import pandas as pd
    except ImportError:
        # If pandas not available, return a moderate score
        return 10.0, ["Unable to perform business validity checks without pandas"], []
    
    # Auto-detect data type if not specified
    if data_type is None:
        columns_lower = [col.lower() for col in df.columns]
        if any('opportunity' in col or 'deal' in col or 'amount' in col for col in columns_lower):
            data_type = 'crm'
        elif any('inventory' in col or 'warehouse' in col or 'reorder' in col for col in columns_lower):
            data_type = 'inventory'
        elif any('customer' in col or 'email' in col for col in columns_lower):
            data_type = 'customer'
    
    # Initialize
    total_issues = 0
    all_findings = []
    all_recommendations = []
    
    # Run appropriate checks
    checker = BusinessValidityChecker()
    
    if data_type == 'crm':
        issues, findings, recommendations = checker.check_crm_validity(df)
        total_issues += issues
        all_findings.extend(findings)
        all_recommendations.extend(recommendations)
        
    elif data_type == 'inventory':
        issues, findings, recommendations = checker.check_inventory_validity(df)
        total_issues += issues
        all_findings.extend(findings)
        all_recommendations.extend(recommendations)
        
    elif data_type == 'customer':
        issues, findings, recommendations = checker.check_customer_validity(df)
        total_issues += issues
        all_findings.extend(findings)
        all_recommendations.extend(recommendations)
    
    # Calculate score: Start at 95% (not perfect), deduct 15% per issue
    # Minimum score is 20% of the dimension max (4 out of 20)
    base_percentage = 95 - (total_issues * 15)
    base_percentage = max(20, base_percentage)
    
    # Convert percentage to score out of 20
    score = (base_percentage / 100) * 20
    
    # If no specific checks were run, give a moderate score
    if not all_findings:
        score = 12  # 60% of 20
        all_findings.append("No business-specific validity issues detected")
    
    return score, all_findings, all_recommendations
