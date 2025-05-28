"""
Business-focused freshness assessments for discovery mode.

This module provides practical, business-oriented freshness checks
that work on raw data without requiring metadata.
"""

from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime, timedelta
import pandas as pd


class BusinessFreshnessChecker:
    """
    Provides business-focused freshness checks for common data patterns.
    """
    
    @staticmethod
    def check_crm_freshness(df) -> Tuple[int, List[str], List[str]]:
        """
        Check freshness issues specific to CRM data.
        
        Returns:
            Tuple of (issues_found, findings, recommendations)
        """
        issues = 0
        findings = []
        recommendations = []
        today = datetime.now()
        
        # Check for stale deals based on last activity
        if 'last_activity_date' in df.columns:
            stale_deals = []
            for idx, row in df.iterrows():
                if pd.notna(row['last_activity_date']):
                    try:
                        # Handle various date formats
                        if isinstance(row['last_activity_date'], str):
                            last_activity = datetime.strptime(row['last_activity_date'][:10], '%Y-%m-%d')
                        else:
                            last_activity = pd.to_datetime(row['last_activity_date'])
                            
                        days_old = (today - last_activity).days
                        
                        # Only check active deals
                        if 'stage' in df.columns and row.get('stage') not in ['closed-won', 'closed-lost']:
                            if days_old > 14:
                                amount = BusinessFreshnessChecker._parse_number(row.get('amount', 0))
                                stale_deals.append({
                                    'deal': row.get('deal_name', f'Row {idx+1}'),
                                    'days': days_old,
                                    'amount': amount
                                })
                    except:
                        pass
            
            if stale_deals:
                issues += 1
                total_stale_value = sum(d['amount'] for d in stale_deals)
                findings.append(f"⏰ {len(stale_deals)} deals worth ${total_stale_value:,.0f} inactive 14+ days")
                recommendations.append("Review and update stale opportunities")
        
        # Check overall data freshness
        date_columns = []
        for col in df.columns:
            if 'date' in col.lower() or 'updated' in col.lower():
                date_columns.append(col)
        
        if date_columns:
            # Find the most recent date across all date columns
            most_recent = None
            for col in date_columns:
                try:
                    col_max = pd.to_datetime(df[col]).max()
                    if pd.notna(col_max):
                        if most_recent is None or col_max > most_recent:
                            most_recent = col_max
                except:
                    pass
            
            if most_recent:
                days_old = (today - most_recent).days
                if days_old > 1:
                    issues += 1
                    findings.append(f"📅 Data is {days_old} days old")
                    recommendations.append("Update data more frequently for real-time decision making")
        
        return issues, findings, recommendations
    
    @staticmethod
    def check_inventory_freshness(df) -> Tuple[int, List[str], List[str]]:
        """
        Check freshness issues specific to inventory data.
        """
        issues = 0
        findings = []
        recommendations = []
        today = datetime.now()
        
        # Check last updated timestamp
        if 'last_updated' in df.columns:
            try:
                dates = pd.to_datetime(df['last_updated'])
                oldest = dates.min()
                newest = dates.max()
                
                if pd.notna(oldest):
                    days_old = (today - oldest).days
                    if days_old > 1:
                        issues += 1
                        findings.append(f"📅 Some inventory data is {days_old} days old")
                        recommendations.append("Ensure real-time inventory updates to prevent stockouts")
                        
                    # Check if updates are consistent
                    if pd.notna(newest):
                        update_spread = (newest - oldest).days
                        if update_spread > 3:
                            issues += 1
                            findings.append(f"⚠️ Inventory updates are inconsistent (spread: {update_spread} days)")
                            recommendations.append("Synchronize inventory updates across all locations")
            except:
                pass
        
        return issues, findings, recommendations
    
    @staticmethod
    def check_customer_freshness(df) -> Tuple[int, List[str], List[str]]:
        """
        Check freshness issues specific to customer data.
        """
        issues = 0
        findings = []
        recommendations = []
        today = datetime.now()
        
        # Check last contact or update dates
        date_columns = ['last_contact', 'last_updated', 'created_date', 'modified_date']
        found_date_col = None
        
        for col in date_columns:
            if col in df.columns:
                found_date_col = col
                break
        
        if found_date_col:
            try:
                dates = pd.to_datetime(df[found_date_col])
                # Check percentage of records updated recently
                recent = dates > (today - timedelta(days=90))
                recent_pct = (recent.sum() / len(dates)) * 100
                
                if recent_pct < 70:
                    issues += 1
                    findings.append(f"📅 Only {recent_pct:.0f}% of customer records updated in last 90 days")
                    recommendations.append("Implement regular customer data verification process")
            except:
                pass
        
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


def calculate_business_freshness_score(df, data_type: str = None) -> Tuple[float, List[str], List[str]]:
    """
    Calculate a business-focused freshness score.
    
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
    checker = BusinessFreshnessChecker()
    
    if data_type == 'crm':
        issues, findings, recommendations = checker.check_crm_freshness(df)
        total_issues += issues
        all_findings.extend(findings)
        all_recommendations.extend(recommendations)
        
    elif data_type == 'inventory':
        issues, findings, recommendations = checker.check_inventory_freshness(df)
        total_issues += issues
        all_findings.extend(findings)
        all_recommendations.extend(recommendations)
        
    elif data_type == 'customer':
        issues, findings, recommendations = checker.check_customer_freshness(df)
        total_issues += issues
        all_findings.extend(findings)
        all_recommendations.extend(recommendations)
    
    # Calculate score: Start at 95% (not perfect), deduct 15% per issue
    # Minimum score is 20% of the dimension max (4 out of 20)
    base_percentage = 95 - (total_issues * 15)
    base_percentage = max(20, base_percentage)
    
    # Convert percentage to score out of 20
    score = (base_percentage / 100) * 20
    
    # If no specific checks were run or no issues found, give a good score
    if not all_findings or total_issues == 0:
        score = 17  # 85% of 20
        all_findings.append("Data freshness appears acceptable")
    
    return score, all_findings, all_recommendations
