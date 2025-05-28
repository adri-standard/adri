"""
Business-focused completeness assessments for discovery mode.

This module provides practical, business-oriented completeness checks
that work on raw data without requiring metadata.
"""

from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime
import pandas as pd


class BusinessCompletenessChecker:
    """
    Provides business-focused completeness checks for common data patterns.
    """
    
    @staticmethod
    def check_crm_completeness(df) -> Tuple[int, List[str], List[str]]:
        """
        Check completeness issues specific to CRM data.
        
        Returns:
            Tuple of (issues_found, findings, recommendations)
        """
        issues = 0
        findings = []
        recommendations = []
        
        # Check for missing close dates in late stage deals
        if 'stage' in df.columns and 'close_date' in df.columns:
            late_stage_deals = df[df['stage'].isin(['negotiation', 'proposal'])]
            missing_close_dates = late_stage_deals[late_stage_deals['close_date'].isna() | (late_stage_deals['close_date'] == '')]
            
            if len(missing_close_dates) > 0:
                issues += 1
                # Calculate total amount at risk
                if 'amount' in df.columns:
                    total_at_risk = missing_close_dates['amount'].apply(lambda x: BusinessCompletenessChecker._parse_number(x)).sum()
                    findings.append(f"💰 {len(missing_close_dates)} deals worth ${total_at_risk:,.0f} missing close dates")
                else:
                    findings.append(f"💰 {len(missing_close_dates)} deals missing close dates")
                recommendations.append("Update close dates for negotiation/proposal stage deals")
        
        # Check for missing contact emails in active deals
        if 'stage' in df.columns and 'contact_email' in df.columns:
            active_deals = df[~df['stage'].isin(['closed-won', 'closed-lost'])]
            missing_emails = active_deals[active_deals['contact_email'].isna() | (active_deals['contact_email'] == '')]
            
            if len(missing_emails) > 0:
                issues += 1
                findings.append(f"📧 {len(missing_emails)} active deals missing contact emails")
                recommendations.append("Collect email addresses for active opportunities")
        
        # Check for missing owners
        if 'owner' in df.columns:
            missing_owners = df[df['owner'].isna() | (df['owner'] == '')]
            if len(missing_owners) > 0:
                issues += 1
                findings.append(f"👤 {len(missing_owners)} deals missing owners")
                recommendations.append("Assign owners to all opportunities")
        
        return issues, findings, recommendations
    
    @staticmethod
    def check_inventory_completeness(df) -> Tuple[int, List[str], List[str]]:
        """
        Check completeness issues specific to inventory data.
        """
        issues = 0
        findings = []
        recommendations = []
        
        # Check for missing warehouse locations
        if 'warehouse' in df.columns:
            missing_warehouse = df[df['warehouse'].isna() | (df['warehouse'] == '')]
            if len(missing_warehouse) > 0:
                issues += 1
                findings.append(f"🏭 {len(missing_warehouse)} items missing warehouse location")
                recommendations.append("Assign warehouse locations to all inventory items")
        
        # Check for missing SKUs
        if 'sku' in df.columns:
            missing_sku = df[df['sku'].isna() | (df['sku'] == '')]
            if len(missing_sku) > 0:
                issues += 1
                findings.append(f"🏷️ {len(missing_sku)} items missing SKU")
                recommendations.append("Assign SKUs to all inventory items")
        
        return issues, findings, recommendations
    
    @staticmethod
    def check_customer_completeness(df) -> Tuple[int, List[str], List[str]]:
        """
        Check completeness issues specific to customer data.
        """
        issues = 0
        findings = []
        recommendations = []
        
        # Check for missing emails
        if 'email' in df.columns:
            missing_emails = df[df['email'].isna() | (df['email'] == '')]
            if len(missing_emails) > 0:
                issues += 1
                findings.append(f"📧 {len(missing_emails)} customers missing email addresses")
                recommendations.append("Collect email addresses for all customers")
        
        # Check for missing names
        if 'name' in df.columns or 'customer_name' in df.columns:
            name_col = 'name' if 'name' in df.columns else 'customer_name'
            missing_names = df[df[name_col].isna() | (df[name_col] == '')]
            if len(missing_names) > 0:
                issues += 1
                findings.append(f"👤 {len(missing_names)} customers missing names")
                recommendations.append("Ensure all customers have names recorded")
        
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


def calculate_business_completeness_score(df, data_type: str = None) -> Tuple[float, List[str], List[str]]:
    """
    Calculate a business-focused completeness score.
    
    This scoring method starts at 100% and deducts points for issues found,
    similar to the quickstart approach.
    
    Args:
        df: DataFrame to assess
        data_type: Type of data ('crm', 'inventory', 'customer', or None for auto-detect)
        
    Returns:
        Tuple of (score 0-20, findings, recommendations)
    """
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
    checker = BusinessCompletenessChecker()
    
    if data_type == 'crm':
        issues, findings, recommendations = checker.check_crm_completeness(df)
        total_issues += issues
        all_findings.extend(findings)
        all_recommendations.extend(recommendations)
        
    elif data_type == 'inventory':
        issues, findings, recommendations = checker.check_inventory_completeness(df)
        total_issues += issues
        all_findings.extend(findings)
        all_recommendations.extend(recommendations)
        
    elif data_type == 'customer':
        issues, findings, recommendations = checker.check_customer_completeness(df)
        total_issues += issues
        all_findings.extend(findings)
        all_recommendations.extend(recommendations)
    
    # Also check general completeness
    total_cells = len(df) * len(df.columns)
    empty_cells = df.isna().sum().sum() + (df == '').sum().sum()
    completeness_pct = ((total_cells - empty_cells) / total_cells) * 100 if total_cells > 0 else 100
    
    if completeness_pct < 80:
        total_issues += 1
        all_findings.append(f"📊 Only {completeness_pct:.0f}% of data cells are populated")
        all_recommendations.append("Improve overall data completeness")
    
    # Calculate score: Start at 95% (not perfect), deduct 15% per issue
    # Minimum score is 20% of the dimension max (4 out of 20)
    base_percentage = 95 - (total_issues * 15)
    base_percentage = max(20, base_percentage)
    
    # Convert percentage to score out of 20
    score = (base_percentage / 100) * 20
    
    # If no specific checks were run, give a moderate score
    if not all_findings:
        score = 15  # 75% of 20
        all_findings.append("General completeness appears acceptable")
    
    return score, all_findings, all_recommendations
