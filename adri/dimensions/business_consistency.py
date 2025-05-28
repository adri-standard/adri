"""
Business-focused consistency assessments for discovery mode.

This module provides practical, business-oriented consistency checks
that work on raw data without requiring metadata.
"""

from typing import Dict, List, Tuple, Any, Optional
import pandas as pd
import numpy as np


class BusinessConsistencyChecker:
    """
    Provides business-focused consistency checks for common data patterns.
    """
    
    @staticmethod
    def check_crm_consistency(df) -> Tuple[int, List[str], List[str]]:
        """
        Check consistency issues specific to CRM data.
        
        Returns:
            Tuple of (issues_found, findings, recommendations)
        """
        issues = 0
        findings = []
        recommendations = []
        
        # Check for duplicate opportunities
        if 'deal_name' in df.columns:
            duplicates = df.duplicated(subset=['deal_name'], keep=False)
            duplicate_count = duplicates.sum()
            if duplicate_count > 0:
                issues += 1
                findings.append(f"🔄 {duplicate_count // 2} duplicate opportunities found")
                recommendations.append("Resolve duplicate opportunity records")
        
        # Check stage progression consistency
        if 'stage' in df.columns and 'close_date' in df.columns:
            # Closed deals should have close dates
            closed_deals = df[df['stage'].isin(['closed-won', 'closed-lost'])]
            missing_close_dates = closed_deals[closed_deals['close_date'].isna() | (closed_deals['close_date'] == '')]
            if len(missing_close_dates) > 0:
                issues += 1
                findings.append(f"🔴 {len(missing_close_dates)} closed deals missing close dates")
                recommendations.append("Add close dates to all closed opportunities")
        
        # Check amount consistency
        if 'amount' in df.columns and 'stage' in df.columns:
            # Closed-lost deals shouldn't have value (or should be 0)
            closed_lost = df[df['stage'] == 'closed-lost']
            if len(closed_lost) > 0:
                non_zero_lost = closed_lost[closed_lost['amount'].apply(
                    lambda x: BusinessConsistencyChecker._parse_number(x) > 0
                )]
                if len(non_zero_lost) > 0:
                    issues += 1
                    findings.append(f"💸 {len(non_zero_lost)} closed-lost deals have non-zero amounts")
                    recommendations.append("Zero out amounts for closed-lost opportunities")
        
        # Check owner assignment consistency
        if 'owner' in df.columns and 'stage' in df.columns:
            active_deals = df[~df['stage'].isin(['closed-won', 'closed-lost'])]
            unassigned = active_deals[active_deals['owner'].isna() | (active_deals['owner'] == '')]
            if len(unassigned) > 0:
                issues += 1
                findings.append(f"👤 {len(unassigned)} active deals have no owner assigned")
                recommendations.append("Assign owners to all active opportunities")
        
        return issues, findings, recommendations
    
    @staticmethod
    def check_inventory_consistency(df) -> Tuple[int, List[str], List[str]]:
        """
        Check consistency issues specific to inventory data.
        """
        issues = 0
        findings = []
        recommendations = []
        
        # Check for duplicate SKUs
        if 'sku' in df.columns:
            sku_duplicates = df[df['sku'].notna() & (df['sku'] != '')].duplicated(subset=['sku'], keep=False)
            duplicate_count = sku_duplicates.sum()
            if duplicate_count > 0:
                issues += 1
                findings.append(f"🔄 {duplicate_count // 2} duplicate SKUs found")
                recommendations.append("Resolve duplicate SKU entries")
        
        # Check quantity vs threshold consistency
        if 'quantity_on_hand' in df.columns and 'reorder_threshold' in df.columns:
            # Items below reorder threshold should be flagged
            below_threshold = df[
                (df['quantity_on_hand'].apply(lambda x: BusinessConsistencyChecker._parse_number(x)) < 
                 df['reorder_threshold'].apply(lambda x: BusinessConsistencyChecker._parse_number(x)))
            ]
            if len(below_threshold) > 0:
                issues += 1
                findings.append(f"📦 {len(below_threshold)} items below reorder threshold")
                recommendations.append("Review and reorder low inventory items")
        
        # Check warehouse location consistency
        if 'warehouse' in df.columns and 'sku' in df.columns:
            # Same SKU shouldn't be in multiple warehouses (unless intended)
            sku_warehouse_groups = df[df['sku'].notna() & (df['sku'] != '')].groupby('sku')['warehouse'].nunique()
            multi_warehouse_skus = sku_warehouse_groups[sku_warehouse_groups > 1]
            if len(multi_warehouse_skus) > 0:
                issues += 1
                findings.append(f"🏭 {len(multi_warehouse_skus)} SKUs found in multiple warehouses")
                recommendations.append("Verify multi-warehouse SKU distribution is intentional")
        
        return issues, findings, recommendations
    
    @staticmethod
    def check_customer_consistency(df) -> Tuple[int, List[str], List[str]]:
        """
        Check consistency issues specific to customer data.
        """
        issues = 0
        findings = []
        recommendations = []
        
        # Check for duplicate customers (by email)
        if 'email' in df.columns:
            email_duplicates = df[df['email'].notna() & (df['email'] != '')].duplicated(subset=['email'], keep=False)
            duplicate_count = email_duplicates.sum()
            if duplicate_count > 0:
                issues += 1
                findings.append(f"🔄 {duplicate_count // 2} duplicate customer emails found")
                recommendations.append("Merge duplicate customer records")
        
        # Check name consistency
        if 'name' in df.columns or 'customer_name' in df.columns:
            name_col = 'name' if 'name' in df.columns else 'customer_name'
            # Check for inconsistent formatting (e.g., all caps, all lower)
            all_caps = df[df[name_col].notna() & (df[name_col] == df[name_col].str.upper())]
            all_lower = df[df[name_col].notna() & (df[name_col] == df[name_col].str.lower())]
            
            formatting_issues = len(all_caps) + len(all_lower)
            if formatting_issues > 0:
                issues += 1
                findings.append(f"📝 {formatting_issues} customers have inconsistent name formatting")
                recommendations.append("Standardize customer name formatting")
        
        return issues, findings, recommendations
    
    @staticmethod
    def _parse_number(value):
        """Safely parse a number from various formats."""
        if pd.isna(value):
            return 0
        try:
            if isinstance(value, (int, float)):
                return float(value)
            clean = str(value).replace('$', '').replace(',', '').strip()
            return float(clean)
        except:
            return 0


def calculate_business_consistency_score(df, data_type: str = None) -> Tuple[float, List[str], List[str]]:
    """
    Calculate a business-focused consistency score.
    
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
    checker = BusinessConsistencyChecker()
    
    if data_type == 'crm':
        issues, findings, recommendations = checker.check_crm_consistency(df)
        total_issues += issues
        all_findings.extend(findings)
        all_recommendations.extend(recommendations)
        
    elif data_type == 'inventory':
        issues, findings, recommendations = checker.check_inventory_consistency(df)
        total_issues += issues
        all_findings.extend(findings)
        all_recommendations.extend(recommendations)
        
    elif data_type == 'customer':
        issues, findings, recommendations = checker.check_customer_consistency(df)
        total_issues += issues
        all_findings.extend(findings)
        all_recommendations.extend(recommendations)
    
    # Also check general consistency (data types, formats)
    # Check for consistent data types within columns
    type_issues = 0
    for col in df.columns:
        # Skip if all values are NaN
        if df[col].notna().sum() == 0:
            continue
            
        # Check if column has mixed types
        non_null_values = df[col].dropna()
        if len(non_null_values) > 0:
            types = non_null_values.apply(type).unique()
            if len(types) > 1:
                # Allow for int/float mixing
                if not (set(types).issubset({int, float, np.int64, np.float64})):
                    type_issues += 1
    
    if type_issues > 0:
        total_issues += 1
        all_findings.append(f"🔢 {type_issues} columns have mixed data types")
        all_recommendations.append("Standardize data types within columns")
    
    # Calculate score: Start at 95% (not perfect), deduct 15% per issue
    # Minimum score is 20% of the dimension max (4 out of 20)
    base_percentage = 95 - (total_issues * 15)
    base_percentage = max(20, base_percentage)
    
    # Convert percentage to score out of 20
    score = (base_percentage / 100) * 20
    
    # If no specific checks were run, give a moderate score
    if not all_findings:
        score = 15  # 75% of 20
        all_findings.append("General consistency appears acceptable")
    
    return score, all_findings, all_recommendations
