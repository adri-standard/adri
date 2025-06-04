"""
Example 3: Data Team Contract - The Communication Bridge

This example demonstrates how ADRI serves as a shared language between
AI engineers and data teams, enabling clear communication about data
quality requirements and progress tracking.

Real scenario: A fraud detection agent requires data from multiple
internal systems, and both teams need to track quality improvements.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from adri.assessor import DataSourceAssessor
from adri.config import Config

def simulate_data_team_journey():
    """Shows how data teams use ADRI to deliver quality data."""
    
    print("=" * 60)
    print("SCENARIO: Building a Fraud Detection Agent")
    print("=" * 60)
    
    print("\n📋 AI Engineer provides ADRI requirements:")
    print("-" * 40)
    
    # Define fraud detection requirements
    fraud_requirements = Config()
    fraud_requirements.set("template", "fraud-detection-v1")
    fraud_requirements.set("dimensions.freshness.max_age_minutes", 30)
    fraud_requirements.set("dimensions.completeness.required_fields", [
        "transaction_id", "amount", "merchant_id", "user_id", 
        "timestamp", "location", "previous_fraud_flag"
    ])
    fraud_requirements.set("dimensions.consistency.cross_references", {
        "user_id": "users_table",
        "merchant_id": "merchants_table"
    })
    fraud_requirements.set("minimum_score", 90)  # High stakes = high standards
    
    print("Template: fraud-detection-v1")
    print("Minimum Score: 90/100 (high-risk application)")
    print("Critical Requirements:")
    print("  • Real-time data (< 30 minutes old)")
    print("  • All transaction fields must be present")
    print("  • User/merchant IDs must exist in reference tables")
    print("  • Historical fraud indicators required")
    
    # Simulate Day 1 - Initial assessment
    print("\n\n📅 Day 1 - Data Team's First Attempt:")
    print("-" * 40)
    
    day1_data = pd.DataFrame({
        'transaction_id': ['T001', 'T002', 'T003', 'T004', 'T005'],
        'amount': [100.50, 2500.00, 45.00, None, 1200.00],
        'merchant_id': ['M123', 'M456', 'M789', 'M999', 'M111'],
        'user_id': ['U001', 'U002', None, 'U004', 'U005'],
        'timestamp': [
            datetime.now() - timedelta(hours=2),  # Too old!
            datetime.now() - timedelta(hours=1),  # Too old!
            datetime.now() - timedelta(minutes=20),
            datetime.now() - timedelta(minutes=15),
            datetime.now() - timedelta(minutes=5)
        ],
        'location': ['NY', 'CA', 'TX', 'FL', None],
        # Missing: previous_fraud_flag entirely!
    })
    
    day1_data.to_csv('fraud_data_day1.csv', index=False)
    
    assessor = DataSourceAssessor(config=fraud_requirements)
    day1_report = assessor.assess_file('fraud_data_day1.csv')
    
    print(f"📊 ADRI Score: {day1_report.overall_score}/100 ❌")
    print("\n🔍 Gap Analysis (automatically generated):")
    print("  • Freshness: 40% of data exceeds 30-minute threshold")
    print("  • Completeness: Missing 'previous_fraud_flag' field")
    print("  • Completeness: 20% missing user_id values")
    print("  • Validity: NULL amount in transaction T004")
    
    # Simulate Day 3 - Improvements
    print("\n\n📅 Day 3 - After Data Pipeline Updates:")
    print("-" * 40)
    
    day3_data = pd.DataFrame({
        'transaction_id': ['T101', 'T102', 'T103', 'T104', 'T105'],
        'amount': [100.50, 2500.00, 45.00, 750.00, 1200.00],
        'merchant_id': ['M123', 'M456', 'M789', 'M999', 'M111'],
        'user_id': ['U001', 'U002', 'U003', 'U004', 'U005'],
        'timestamp': [
            datetime.now() - timedelta(minutes=25),
            datetime.now() - timedelta(minutes=20),
            datetime.now() - timedelta(minutes=15),
            datetime.now() - timedelta(minutes=10),
            datetime.now() - timedelta(minutes=5)
        ],
        'location': ['NY', 'CA', 'TX', 'FL', 'WA'],
        'previous_fraud_flag': [False, False, True, False, False]  # Added!
    })
    
    day3_data.to_csv('fraud_data_day3.csv', index=False)
    day3_report = assessor.assess_file('fraud_data_day3.csv')
    
    print(f"📊 ADRI Score: {day3_report.overall_score}/100 {'✅' if day3_report.overall_score >= 90 else '❌'}")
    print("\n✅ Improvements Made:")
    print("  • Added missing 'previous_fraud_flag' field")
    print("  • Fixed NULL values in critical fields")
    print("  • Upgraded data pipeline for real-time updates")
    print("  • All data now within 30-minute freshness window")
    
    # Show the collaboration benefit
    print("\n\n🤝 The Power of Shared Understanding:")
    print("-" * 40)
    
    print("AI Engineer View:")
    print("  ```python")
    print("  # Check if data is ready for production")
    print("  if adri_score >= 90:")
    print("      deploy_fraud_agent()")
    print("  else:")
    print("      print('Waiting for data team improvements')")
    print("  ```")
    
    print("\nData Engineer View:")
    print("  ```python")
    print("  # Track daily progress")
    print("  daily_scores = [67, 74, 78, 85, 92]")
    print("  for day, score in enumerate(daily_scores):")
    print("      print(f'Day {day+1}: {score}/100')")
    print("  ```")
    
    print("\nManagement View:")
    print("  'Clear progress tracking: 67→92 in 5 days'")
    print("  'Objective readiness criteria met'")
    print("  'No ambiguity about production readiness'")

def demonstrate_continuous_monitoring():
    """Shows how ADRI enables continuous quality tracking."""
    
    print("\n\n" + "=" * 60)
    print("CONTINUOUS MONITORING: Maintaining Quality")
    print("=" * 60)
    
    print("\n📊 Production Monitoring Dashboard:")
    print("-" * 40)
    
    # Simulate quality over time
    hours = ['9 AM', '10 AM', '11 AM', '12 PM', '1 PM']
    scores = [94, 92, 88, 76, 91]
    
    for hour, score in zip(hours, scores):
        bar = "█" * (score // 5)
        status = "🟢" if score >= 90 else "🟡" if score >= 80 else "🔴"
        print(f"{hour}: {bar} {score}/100 {status}")
    
    print("\n⚠️  Alert at 12 PM: Score dropped to 76/100")
    print("📧 Automated notification sent to data team")
    print("🔍 Root cause: Database replication lag")
    print("✅ Fixed by 1 PM: Score back to 91/100")
    
    print("\n💡 Benefits of Continuous ADRI Monitoring:")
    print("  • Proactive issue detection")
    print("  • Clear accountability")
    print("  • Measurable SLAs")
    print("  • Automated alerting")

def show_collaboration_patterns():
    """Demonstrates effective collaboration patterns."""
    
    print("\n\n" + "=" * 60)
    print("COLLABORATION PATTERNS: Working Together")
    print("=" * 60)
    
    print("\n1️⃣ Sprint Planning:")
    print("   AI Engineer: 'We need ADRI score ≥ 85 for launch'")
    print("   Data Engineer: 'Current score is 72, I can get to 85 by Friday'")
    print("   Product Manager: 'Perfect, that aligns with our timeline'")
    
    print("\n2️⃣ Debugging Sessions:")
    print("   AI Engineer: 'Agent predictions are off'")
    print("   Data Engineer: 'Let me check... ADRI shows freshness at 11/20'")
    print("   Both: 'Found it! The ETL job has been failing since yesterday'")
    
    print("\n3️⃣ Quality Reviews:")
    print("   Weekly Report: 'Average ADRI score: 91.3/100'")
    print("   Trend: 'Improved from 87.2 last month'")
    print("   Action: 'Maintain current data quality practices'")

if __name__ == "__main__":
    simulate_data_team_journey()
    demonstrate_continuous_monitoring()
    show_collaboration_patterns()
    
    print("\n\n" + "=" * 60)
    print("🎯 KEY TAKEAWAY: ADRI creates a shared language that")
    print("   transforms finger-pointing into productive collaboration.")
    print("=" * 60)
    
    # Clean up
    import os
    for file in ['fraud_data_day1.csv', 'fraud_data_day3.csv']:
        if os.path.exists(file):
            os.remove(file)
