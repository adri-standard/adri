#!/usr/bin/env python3
"""
AI Status Auditor Demo - RevOps CRM Audit

This example demonstrates how ADRI can be used to create a business-focused
audit tool that identifies workflow breakdowns in CRM data.

The demo shows:
1. Loading CRM data with common issues
2. Running ADRI assessment with custom rules
3. Translating results to business language
4. Generating actionable audit report
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
from pathlib import Path
from typing import Dict, List, Any

from adri.assessor import DataSourceAssessor


def create_sample_crm_data():
    """Generate realistic CRM data with common issues"""
    
    # Set seed for reproducibility
    np.random.seed(42)
    
    # Generate 200 opportunities
    n_records = 200
    
    # Create base data
    data = {
        'opportunity_id': [f'OPP-{i:04d}' for i in range(n_records)],
        'account_name': [f'Company {i % 50}' for i in range(n_records)],
        'deal_name': [f'Deal {i}' for i in range(n_records)],
        'stage': np.random.choice([
            'prospecting', 'qualification', 'proposal', 
            'negotiation', 'closed-won', 'closed-lost'
        ], n_records, p=[0.15, 0.20, 0.25, 0.20, 0.10, 0.10]),
        'amount': np.random.lognormal(10, 1.5, n_records).round(2),
        'owner': np.random.choice([
            'John Smith', 'Mary Johnson', 'David Lee', 
            'Sarah Wilson', 'Mike Brown'
        ], n_records),
        'created_date': [
            datetime.now() - timedelta(days=np.random.randint(1, 180))
            for _ in range(n_records)
        ]
    }
    
    df = pd.DataFrame(data)
    
    # Add close dates (with issues)
    df['close_date'] = pd.NaT
    for idx in df.index:
        if df.loc[idx, 'stage'] in ['negotiation', 'proposal', 'closed-won', 'closed-lost']:
            # 30% missing close dates in late stages (ISSUE!)
            if np.random.random() > 0.3:
                df.loc[idx, 'close_date'] = (
                    df.loc[idx, 'created_date'] + 
                    timedelta(days=np.random.randint(30, 120))
                )
    
    # Add last activity dates
    df['last_activity_date'] = df['created_date'].copy()
    for idx in df.index:
        if df.loc[idx, 'stage'] not in ['closed-won', 'closed-lost']:
            # Some deals have very old activity (ISSUE!)
            days_ago = np.random.choice(
                [1, 7, 14, 30, 60], 
                p=[0.3, 0.3, 0.2, 0.15, 0.05]
            )
            df.loc[idx, 'last_activity_date'] = datetime.now() - timedelta(days=int(days_ago))
    
    # Add contact email (with missing data)
    df['contact_email'] = [
        f'contact{i}@company{i%50}.com' if np.random.random() > 0.2 else None
        for i in range(n_records)
    ]
    
    # Add account owner (with mismatches)
    df['account_owner'] = df['owner'].copy()
    # Create ownership conflicts (ISSUE!)
    conflict_indices = np.random.choice(df.index, size=30, replace=False)
    for idx in conflict_indices:
        other_owners = ['John Smith', 'Mary Johnson', 'David Lee', 'Sarah Wilson', 'Mike Brown']
        other_owners.remove(df.loc[idx, 'owner'])
        df.loc[idx, 'account_owner'] = np.random.choice(other_owners)
    
    # Calculate derived fields
    df['days_since_last_activity'] = (
        (datetime.now() - df['last_activity_date']).dt.days
    )
    
    # Save to CSV
    csv_path = Path('crm_audit_demo.csv')
    df.to_csv(csv_path, index=False)
    print(f"✅ Created sample CRM data: {csv_path}")
    
    return csv_path, df


def create_revops_metadata():
    """Create ADRI metadata for RevOps audit rules"""
    
    # Validity rules
    validity_metadata = {
        "description": "CRM data format and type validation",
        "rules": [
            {
                "name": "valid_email_format",
                "field": "contact_email",
                "type": "email",
                "required": False
            },
            {
                "name": "valid_stage_values",
                "field": "stage",
                "allowed_values": [
                    "prospecting", "qualification", "proposal",
                    "negotiation", "closed-won", "closed-lost"
                ]
            },
            {
                "name": "positive_deal_amount",
                "field": "amount",
                "min_value": 0
            }
        ]
    }
    
    # Completeness rules
    completeness_metadata = {
        "description": "Required fields for different stages",
        "rules": [
            {
                "name": "close_date_required",
                "condition": "stage in ['negotiation', 'proposal', 'closed-won', 'closed-lost']",
                "required_fields": ["close_date"],
                "business_impact": "Cannot forecast revenue accurately"
            },
            {
                "name": "contact_email_for_active_deals",
                "condition": "stage not in ['closed-won', 'closed-lost']",
                "required_fields": ["contact_email"],
                "business_impact": "Cannot execute email campaigns"
            }
        ]
    }
    
    # Freshness rules
    freshness_metadata = {
        "description": "Activity recency requirements",
        "rules": [
            {
                "name": "active_deal_staleness",
                "field": "last_activity_date",
                "max_age_days": 14,
                "condition": "stage not in ['closed-won', 'closed-lost']",
                "business_impact": "Deals likely to go cold"
            }
        ]
    }
    
    # Consistency rules
    consistency_metadata = {
        "description": "Cross-field validation",
        "rules": [
            {
                "name": "owner_consistency",
                "check": "owner == account_owner",
                "business_impact": "Confusion in account ownership"
            }
        ]
    }
    
    # Plausibility rules
    plausibility_metadata = {
        "description": "Business logic validation",
        "rules": [
            {
                "name": "reasonable_deal_size",
                "field": "amount",
                "outlier_detection": "iqr",
                "multiplier": 3.0,
                "business_impact": "Potential data entry errors"
            }
        ]
    }
    
    # Save metadata files
    base_name = 'crm_audit_demo'
    
    with open(f'{base_name}.validity.json', 'w') as f:
        json.dump(validity_metadata, f, indent=2)
    
    with open(f'{base_name}.completeness.json', 'w') as f:
        json.dump(completeness_metadata, f, indent=2)
    
    with open(f'{base_name}.freshness.json', 'w') as f:
        json.dump(freshness_metadata, f, indent=2)
    
    with open(f'{base_name}.consistency.json', 'w') as f:
        json.dump(consistency_metadata, f, indent=2)
    
    with open(f'{base_name}.plausibility.json', 'w') as f:
        json.dump(plausibility_metadata, f, indent=2)
    
    print("✅ Created ADRI metadata files for RevOps audit")


def translate_to_business_language(assessment_results: Dict[str, Any], df: pd.DataFrame) -> str:
    """Convert ADRI assessment results to business-focused audit report"""
    
    report_lines = []
    report_lines.append("🔍 CRM AUDIT REPORT")
    report_lines.append("=" * 50)
    report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    report_lines.append("")
    
    # Overall score
    overall_score = assessment_results.get('overall_score', 0)
    status = "✅ HEALTHY" if overall_score > 80 else "⚠️ NEEDS ATTENTION" if overall_score > 60 else "❌ CRITICAL"
    report_lines.append(f"Overall Health: {status} ({overall_score:.0f}%)")
    report_lines.append("")
    
    # Revenue at risk analysis
    report_lines.append("💰 REVENUE AT RISK")
    report_lines.append("-" * 30)
    
    # Deals missing close dates
    late_stage_mask = df['stage'].isin(['negotiation', 'proposal'])
    missing_close_date_mask = df['close_date'].isna()
    at_risk_deals = df[late_stage_mask & missing_close_date_mask]
    
    if len(at_risk_deals) > 0:
        total_at_risk = at_risk_deals['amount'].sum()
        report_lines.append(f"• {len(at_risk_deals)} deals worth ${total_at_risk:,.0f} missing close dates")
        top_deals = at_risk_deals.nlargest(3, 'amount')[['deal_name', 'amount', 'owner']]
        for _, deal in top_deals.iterrows():
            report_lines.append(f"  - {deal['deal_name']}: ${deal['amount']:,.0f} ({deal['owner']})")
    
    # Stale opportunities
    active_mask = ~df['stage'].isin(['closed-won', 'closed-lost'])
    stale_mask = df['days_since_last_activity'] > 14
    stale_deals = df[active_mask & stale_mask]
    
    if len(stale_deals) > 0:
        stale_value = stale_deals['amount'].sum()
        avg_days = stale_deals['days_since_last_activity'].mean()
        report_lines.append(f"• {len(stale_deals)} deals worth ${stale_value:,.0f} inactive for {avg_days:.0f}+ days")
    
    report_lines.append("")
    
    # Process breakdowns
    report_lines.append("🚨 PROCESS BREAKDOWNS")
    report_lines.append("-" * 30)
    
    # Missing contact emails
    active_no_email = df[active_mask & df['contact_email'].isna()]
    if len(active_no_email) > 0:
        report_lines.append(f"• {len(active_no_email)} active deals missing contact email")
        report_lines.append("  Impact: Cannot execute email campaigns")
    
    # Ownership conflicts
    ownership_conflicts = df[df['owner'] != df['account_owner']]
    if len(ownership_conflicts) > 0:
        report_lines.append(f"• {len(ownership_conflicts)} opportunities have ownership conflicts")
        conflict_owners = ownership_conflicts['owner'].value_counts().head(3)
        for owner, count in conflict_owners.items():
            report_lines.append(f"  - {owner}: {count} conflicts")
    
    report_lines.append("")
    
    # Immediate actions
    report_lines.append("📋 IMMEDIATE ACTIONS")
    report_lines.append("-" * 30)
    
    if len(at_risk_deals) > 0:
        report_lines.append("1. Update close dates for deals in negotiation/proposal stages")
    
    if len(stale_deals) > 0:
        top_stale_owners = stale_deals['owner'].value_counts().head(3)
        owners_list = ", ".join(top_stale_owners.index)
        report_lines.append(f"2. Review stale deals with: {owners_list}")
    
    if len(ownership_conflicts) > 0:
        report_lines.append("3. Resolve account ownership conflicts to clarify responsibilities")
    
    if len(active_no_email) > 0:
        report_lines.append("4. Collect email addresses for active opportunities")
    
    report_lines.append("")
    
    # Data quality breakdown
    report_lines.append("📊 DATA QUALITY BREAKDOWN")
    report_lines.append("-" * 30)
    
    dimensions = assessment_results.get('dimension_scores', {})
    for dimension, score in dimensions.items():
        status_icon = "✅" if score > 80 else "⚠️" if score > 60 else "❌"
        report_lines.append(f"{status_icon} {dimension.capitalize()}: {score:.0f}%")
    
    return "\n".join(report_lines)


def main():
    """Run the AI Status Auditor demo"""
    
    print("\n🚀 AI STATUS AUDITOR DEMO - RevOps CRM Audit")
    print("=" * 60)
    
    # Step 1: Create sample data
    print("\n1️⃣ Creating sample CRM data with common issues...")
    csv_path, df = create_sample_crm_data()
    
    print(f"\n📊 Data Summary:")
    print(f"   - Total opportunities: {len(df)}")
    print(f"   - Total pipeline value: ${df[df['stage'].isin(['proposal', 'negotiation'])]['amount'].sum():,.0f}")
    print(f"   - Active deals: {len(df[~df['stage'].isin(['closed-won', 'closed-lost'])])}")
    
    # Step 2: Create ADRI metadata
    print("\n2️⃣ Creating ADRI audit rules...")
    create_revops_metadata()
    
    # Step 3: Run ADRI assessment
    print("\n3️⃣ Running ADRI assessment...")
    assessor = DataSourceAssessor()
    
    try:
        # Use assess_file method from DataSourceAssessor
        report = assessor.assess_file(str(csv_path))
        
        # Convert report to dict format for compatibility
        results = report.to_dict()
        
        # Generate HTML report
        report.save_html('crm_audit_report.html')
        print(f"✅ Generated detailed HTML report: crm_audit_report.html")
        
    except Exception as e:
        print(f"Note: Full assessment requires all metadata files. Error: {e}")
        # Create mock results for demo
        results = {
            'overall_score': 68,
            'dimension_scores': {
                'validity': 85,
                'completeness': 55,
                'freshness': 60,
                'consistency': 75,
                'plausibility': 90
            }
        }
    
    # Step 4: Generate business-focused audit report
    print("\n4️⃣ Generating business audit report...")
    audit_report = translate_to_business_language(results, df)
    
    # Display the report
    print("\n" + "=" * 60)
    print(audit_report)
    print("=" * 60)
    
    # Save the business report
    with open('crm_audit_business_report.txt', 'w') as f:
        f.write(audit_report)
    print("\n✅ Saved business report: crm_audit_business_report.txt")
    
    # Show the value proposition
    print("\n💡 THE AHA MOMENT:")
    print("   'This would have taken me 4 hours to find manually!'")
    print("   'Now I know exactly what to fix before the QBR!'")
    print("   'We can prevent these deals from going stale!'")
    
    # Clean up demo files (optional)
    print("\n🧹 Demo complete! Generated files:")
    print("   - crm_audit_demo.csv (sample data)")
    print("   - crm_audit_demo.*.json (ADRI metadata)")
    print("   - crm_audit_report.html (detailed ADRI report)")
    print("   - crm_audit_business_report.txt (business audit)")


if __name__ == "__main__":
    main()
