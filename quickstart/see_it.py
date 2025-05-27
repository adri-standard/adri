#!/usr/bin/env python3
"""
ADRI Quickstart - SEE IT
Shows pre-generated ADRI output without any processing.
Zero dependencies - just shows what ADRI can find.
"""

import os

def show_crm_audit():
    """Display the pre-generated CRM audit report"""
    print("""
🔍 CRM AUDIT REPORT - AI STATUS AUDITOR
==========================================
Generated: 2025-05-27 10:30 AM

💰 REVENUE AT RISK
------------------
• 12 deals worth $340,575 missing close dates
  - Deal #OPP-0147: $45,230 (John Smith)
  - Deal #OPP-0089: $38,920 (Mary Johnson)
  - Deal #OPP-0203: $32,100 (David Lee)

• 8 deals worth $225,430 inactive for 21+ days
  Average days since activity: 34 days

🚨 PROCESS BREAKDOWNS
---------------------
• 23 active deals missing contact email
  Impact: Cannot execute email campaigns

• 15 opportunities have ownership conflicts
  - John Smith: 6 conflicts
  - Mary Johnson: 5 conflicts
  - David Lee: 4 conflicts

📊 DATA QUALITY SCORE: 68/100
-----------------------------
❌ Completeness: 55% - Missing critical fields
⚠️  Freshness: 60% - Stale activity data
✅ Validity: 85% - Most formats correct
✅ Consistency: 75% - Some ownership issues
✅ Plausibility: 90% - Values make sense

📋 IMMEDIATE ACTIONS REQUIRED
-----------------------------
1. Update close dates for negotiation deals
2. Review stale deals with: John S., Mary J.
3. Resolve account ownership conflicts
4. Collect email addresses for active opportunities

💡 THE AHA MOMENT:
"This would have taken me 4 hours to find manually!"
"Now I know exactly what to fix before the QBR!"

==========================================
✅ Full HTML report: crm_audit_report.html
✅ Detailed findings: crm_audit_business_report.txt
""")

def show_menu():
    """Display menu of available reports"""
    print("""
===========================================
ADRI QUICKSTART - See What ADRI Can Find!
===========================================

This shows pre-generated ADRI output to demonstrate
the kind of insights ADRI provides - in 30 seconds!

Available Reports:
1. CRM Audit (RevOps) - Revenue at risk
2. Inventory Analysis - Prevent over-ordering
3. Customer Data - Find duplicates & issues

Which report would you like to see? (1-3): """, end='')

def show_inventory_audit():
    """Display pre-generated inventory audit"""
    print("""
📦 INVENTORY AUDIT REPORT
==========================
Generated: 2025-05-27 10:45 AM

⚠️  CRITICAL FINDINGS
--------------------
• Data is 3 DAYS OLD (last updated: May 24)
  Risk: Ordering based on stale information

• 5 items show negative reorder thresholds
  - Widget E: -10 units (INVALID)
  - Part X23: -5 units (INVALID)

• 12 items below reorder point
  Total reorder value: $127,000

🚨 IMMEDIATE RISKS
-----------------
• About to auto-order 50,000 units
  Based on 3-day old data!
  Potential excess: $89,000

📊 DATA QUALITY SCORE: 42/100
-----------------------------
❌ Freshness: 15% - Data critically stale
❌ Validity: 45% - Invalid thresholds
⚠️  Completeness: 65% - Missing warehouses
✅ Consistency: 80% - Mostly aligned
✅ Plausibility: 75% - Reasonable values

💸 COST OF BAD DATA:
Without ADRI: $127,000 excess inventory
With ADRI: Problem caught before ordering

==========================
✅ Crisis averted!
""")

def show_customer_audit():
    """Display pre-generated customer audit"""
    print("""
👥 CUSTOMER DATA AUDIT
========================
Generated: 2025-05-27 11:00 AM

🔍 DUPLICATE RECORDS FOUND
--------------------------
• 47 potential duplicate customers
  - Same email, different IDs: 23
  - Same name + address: 18
  - Same phone number: 6

📧 CONTACT ISSUES
-----------------
• 156 customers with invalid emails
• 89 customers with disconnected phones
• 234 missing postal codes

🌍 LOCATION DATA PROBLEMS
-------------------------
• 45 invalid state/country combinations
• 78 addresses that don't geocode
• 12 customers in "Test City, XX"

📊 DATA QUALITY SCORE: 71/100
-----------------------------
⚠️  Validity: 65% - Format issues
✅ Completeness: 78% - Most fields present
❌ Consistency: 55% - Duplicates present
✅ Freshness: 82% - Recently updated
✅ Plausibility: 85% - Values reasonable

💰 BUSINESS IMPACT:
• Can't reach 20% of customers
• Duplicate marketing spend: ~$15K/month
• Shipping errors from bad addresses

========================
✅ Time to clean up!
""")

def main():
    """Main entry point"""
    # If outputs directory exists, offer to show files
    outputs_dir = os.path.join(os.path.dirname(__file__), 'outputs')
    
    show_menu()
    
    try:
        choice = input().strip()
        
        print("\n" + "="*50 + "\n")
        
        if choice == '1':
            show_crm_audit()
        elif choice == '2':
            show_inventory_audit()
        elif choice == '3':
            show_customer_audit()
        else:
            print("Invalid choice. Showing CRM audit by default.\n")
            show_crm_audit()
            
    except (KeyboardInterrupt, EOFError):
        print("\n\nGoodbye!")
        return
    
    print("""
🚀 NEXT STEPS:
--------------
1. Try it yourself: python try_it.py samples/crm_data.csv
2. Install ADRI: pip install adri
3. Run on your data: adri assess your_data.csv

Ready to find issues in YOUR data?
""")

if __name__ == "__main__":
    main()
