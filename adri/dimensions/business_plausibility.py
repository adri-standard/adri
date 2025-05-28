"""
Business-focused plausibility assessments for discovery mode.

This module provides practical, business-oriented plausibility checks
that work on raw data without requiring metadata.
"""

from typing import Dict, List, Tuple, Any, Optional
import pandas as pd
import numpy as np


class BusinessPlausibilityChecker:
    """
    Provides business-focused plausibility checks for common data patterns.
    """
    
    @staticmethod
    def check_crm_plausibility(df) -> Tuple[int, List[str], List[str]]:
        """
        Check plausibility issues specific to CRM data.
        
        Returns:
            Tuple of (issues_found, findings, recommendations)
        """
        issues = 0
        findings = []
        recommendations = []
        
        # Check for realistic deal amounts
        if 'amount' in df.columns:
            amounts = df['amount'].apply(lambda x: BusinessPlausibilityChecker._parse_number(x))
            
            # Check for extreme values
            if len(amounts) > 0:
                non_zero_amounts = amounts[amounts > 0]
                if len(non_zero_amounts) > 0:
                    avg_amount = non_zero_amounts.mean()
                    max_amount = non_zero_amounts.max()
                    
                    # Check if max is more than 100x average (outlier)
                    if max_amount > avg_amount * 100:
                        issues += 1
                        findings.append(f"💰 Deal amounts range from ${non_zero_amounts.min():,.0f} to ${max_amount:,.0f} (avg: ${avg_amount:,.0f})")
                        recommendations.append("Verify extreme deal values are accurate")
        
        # Check win rate plausibility
        if 'stage' in df.columns:
            total_closed = len(df[df['stage'].isin(['closed-won', 'closed-lost'])])
            if total_closed > 0:
                won_deals = len(df[df['stage'] == 'closed-won'])
                win_rate = (won_deals / total_closed) * 100
                
                # Win rates below 10% or above 90% are unusual
                if win_rate < 10 or win_rate > 90:
                    issues += 1
                    findings.append(f"🎯 Win rate: {win_rate:.0f}% ({won_deals}/{total_closed} deals)")
                    recommendations.append("Review sales process - win rate appears unusual")
        
        # Check stage distribution
        if 'stage' in df.columns:
            stage_dist = df['stage'].value_counts()
            total_deals = len(df)
            
            # Check if too many deals in one stage
            for stage, count in stage_dist.items():
                pct = (count / total_deals) * 100
                if pct > 50 and stage not in ['closed-won', 'closed-lost']:
                    issues += 1
                    findings.append(f"📊 {pct:.0f}% of deals in '{stage}' stage")
                    recommendations.append(f"Review pipeline - high concentration in {stage} stage")
                    break
        
        return issues, findings, recommendations
    
    @staticmethod
    def check_inventory_plausibility(df) -> Tuple[int, List[str], List[str]]:
        """
        Check plausibility issues specific to inventory data.
        """
        issues = 0
        findings = []
        recommendations = []
        
        # Check quantity vs threshold ratios
        if 'quantity_on_hand' in df.columns and 'reorder_threshold' in df.columns:
            quantities = df['quantity_on_hand'].apply(lambda x: BusinessPlausibilityChecker._parse_number(x))
            thresholds = df['reorder_threshold'].apply(lambda x: BusinessPlausibilityChecker._parse_number(x))
            
            # Check for items with very high stock relative to reorder threshold
            high_stock_items = df[(quantities > thresholds * 10) & (thresholds > 0)]
            if len(high_stock_items) > 0:
                issues += 1
                findings.append(f"📦 {len(high_stock_items)} items have 10x+ their reorder threshold")
                recommendations.append("Review overstocked items to reduce carrying costs")
        
        # Check price reasonableness
        if 'unit_price' in df.columns:
            prices = df['unit_price'].apply(lambda x: BusinessPlausibilityChecker._parse_number(x))
            positive_prices = prices[prices > 0]
            
            if len(positive_prices) > 0:
                avg_price = positive_prices.mean()
                max_price = positive_prices.max()
                min_price = positive_prices.min()
                
                # Check for extreme price variations
                if max_price > min_price * 1000:
                    issues += 1
                    findings.append(f"💵 Prices range from ${min_price:.2f} to ${max_price:.2f}")
                    recommendations.append("Verify extreme price variations are correct")
        
        return issues, findings, recommendations
    
    @staticmethod
    def check_customer_plausibility(df) -> Tuple[int, List[str], List[str]]:
        """
        Check plausibility issues specific to customer data.
        """
        issues = 0
        findings = []
        recommendations = []
        
        # Check for test/fake data
        test_indicators = ['test', 'demo', 'fake', 'sample', 'xxx']
        
        for col in ['name', 'customer_name', 'email']:
            if col in df.columns:
                test_records = df[df[col].str.lower().str.contains('|'.join(test_indicators), na=False)]
                if len(test_records) > 0:
                    issues += 1
                    findings.append(f"🧪 {len(test_records)} potential test records found")
                    recommendations.append("Remove test data from production dataset")
                    break
        
        # Check email domain distribution
        if 'email' in df.columns:
            email_domains = df['email'].str.extract(r'@(.+)$')[0]
            domain_counts = email_domains.value_counts()
            
            # Check if any domain has more than 50% of emails
            if len(domain_counts) > 0:
                top_domain_pct = (domain_counts.iloc[0] / len(df)) * 100
                if top_domain_pct > 50:
                    issues += 1
                    findings.append(f"📧 {top_domain_pct:.0f}% of emails from single domain: {domain_counts.index[0]}")
                    recommendations.append("Verify email domain concentration is expected")
        
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


def calculate_business_plausibility_score(df, data_type: str = None) -> Tuple[float, List[str], List[str]]:
    """
    Calculate a business-focused plausibility score.
    
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
    checker = BusinessPlausibilityChecker()
    
    if data_type == 'crm':
        issues, findings, recommendations = checker.check_crm_plausibility(df)
        total_issues += issues
        all_findings.extend(findings)
        all_recommendations.extend(recommendations)
        
    elif data_type == 'inventory':
        issues, findings, recommendations = checker.check_inventory_plausibility(df)
        total_issues += issues
        all_findings.extend(findings)
        all_recommendations.extend(recommendations)
        
    elif data_type == 'customer':
        issues, findings, recommendations = checker.check_customer_plausibility(df)
        total_issues += issues
        all_findings.extend(findings)
        all_recommendations.extend(recommendations)
    
    # General plausibility checks
    # Check for reasonable data size
    if len(df) < 10:
        total_issues += 1
        all_findings.append(f"📊 Dataset has only {len(df)} records")
        all_recommendations.append("Ensure sufficient data for meaningful analysis")
    
    # Calculate score: Start at 95% (not perfect), deduct 15% per issue
    # Minimum score is 20% of the dimension max (4 out of 20)
    base_percentage = 95 - (total_issues * 15)
    base_percentage = max(20, base_percentage)
    
    # Convert percentage to score out of 20
    score = (base_percentage / 100) * 20
    
    # If no specific checks were run, give a moderate score
    if not all_findings:
        score = 15  # 75% of 20
        all_findings.append("General plausibility appears acceptable")
    
    return score, all_findings, all_recommendations
