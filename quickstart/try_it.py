#!/usr/bin/env python3
"""
ADRI Quickstart - TRY IT
Minimal ADRI implementation using only Python standard library.
No pandas, numpy, or other dependencies required!
"""

import csv
import json
import sys
from datetime import datetime, timedelta
from collections import defaultdict
import re
import os

class MinimalADRI:
    """Simplified ADRI assessor - demonstrates core concepts without dependencies"""
    
    def __init__(self):
        self.dimensions = {
            'validity': 20,
            'completeness': 20,
            'freshness': 20,
            'consistency': 20,
            'plausibility': 20
        }
        self.issues = defaultdict(list)
        self.scores = {}
        
    def assess_csv(self, filepath):
        """Main assessment function"""
        print(f"\n🔍 Analyzing: {filepath}")
        print("=" * 50)
        
        # Read the CSV file
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                headers = reader.fieldnames
        except Exception as e:
            print(f"❌ Error reading file: {e}")
            return
            
        if not rows:
            print("❌ No data found in file!")
            return
            
        print(f"✅ Loaded {len(rows)} rows with {len(headers)} columns")
        
        # Run assessments based on filename patterns
        if 'crm' in filepath.lower() or 'opportunity' in filepath.lower():
            self._assess_crm_data(rows, headers)
        elif 'inventory' in filepath.lower():
            self._assess_inventory_data(rows, headers)
        elif 'customer' in filepath.lower():
            self._assess_customer_data(rows, headers)
        else:
            # Generic assessment
            self._assess_generic_data(rows, headers)
            
        # Calculate scores
        self._calculate_scores()
        
        # Generate report
        self._generate_report()
        
    def _assess_crm_data(self, rows, headers):
        """CRM-specific assessments"""
        # Completeness checks
        critical_fields = ['close_date', 'contact_email', 'amount', 'stage']
        missing_close_dates = 0
        missing_emails = 0
        late_stage_no_close = []
        
        # Freshness checks
        stale_deals = []
        today = datetime.now()
        
        # Consistency checks
        ownership_conflicts = 0
        
        # Validity checks
        invalid_amounts = 0
        
        for idx, row in enumerate(rows):
            # Check completeness
            if row.get('stage') in ['negotiation', 'proposal'] and not row.get('close_date'):
                missing_close_dates += 1
                amount = self._parse_number(row.get('amount', '0'))
                if amount > 0:
                    late_stage_no_close.append({
                        'deal': row.get('deal_name', f'Row {idx+1}'),
                        'amount': amount,
                        'owner': row.get('owner', 'Unknown')
                    })
                    
            if row.get('stage') not in ['closed-won', 'closed-lost'] and not row.get('contact_email'):
                missing_emails += 1
                
            # Check freshness
            if 'last_activity_date' in row and row['last_activity_date']:
                try:
                    last_activity = datetime.strptime(row['last_activity_date'][:10], '%Y-%m-%d')
                    days_old = (today - last_activity).days
                    if days_old > 14 and row.get('stage') not in ['closed-won', 'closed-lost']:
                        stale_deals.append({
                            'deal': row.get('deal_name', f'Row {idx+1}'),
                            'days': days_old,
                            'amount': self._parse_number(row.get('amount', '0'))
                        })
                except:
                    pass
                    
            # Check consistency
            if row.get('owner') and row.get('account_owner') and row['owner'] != row['account_owner']:
                ownership_conflicts += 1
                
            # Check validity
            amount = self._parse_number(row.get('amount', '0'))
            if amount < 0:
                invalid_amounts += 1
                
        # Store issues
        if late_stage_no_close:
            total_at_risk = sum(d['amount'] for d in late_stage_no_close)
            self.issues['completeness'].append(
                f"💰 {len(late_stage_no_close)} deals worth ${total_at_risk:,.0f} missing close dates"
            )
            
        if missing_emails > 0:
            self.issues['completeness'].append(
                f"📧 {missing_emails} active deals missing contact emails"
            )
            
        if stale_deals:
            stale_value = sum(d['amount'] for d in stale_deals)
            self.issues['freshness'].append(
                f"⏰ {len(stale_deals)} deals worth ${stale_value:,.0f} inactive 14+ days"
            )
            
        if ownership_conflicts > 0:
            self.issues['consistency'].append(
                f"🔄 {ownership_conflicts} opportunities have ownership conflicts"
            )
            
        if invalid_amounts > 0:
            self.issues['validity'].append(
                f"❌ {invalid_amounts} deals have invalid amounts"
            )
            
    def _assess_inventory_data(self, rows, headers):
        """Inventory-specific assessments"""
        # Freshness check
        if 'last_updated' in headers:
            dates = []
            for row in rows:
                if row.get('last_updated'):
                    try:
                        date = datetime.strptime(row['last_updated'][:10], '%Y-%m-%d')
                        dates.append(date)
                    except:
                        pass
            if dates:
                oldest = min(dates)
                days_old = (datetime.now() - oldest).days
                if days_old > 1:
                    self.issues['freshness'].append(
                        f"📅 Data is {days_old} days old - risk of stale inventory levels"
                    )
                    
        # Validity checks
        invalid_thresholds = 0
        for row in rows:
            threshold = self._parse_number(row.get('reorder_threshold', '0'))
            if threshold < 0:
                invalid_thresholds += 1
                
        if invalid_thresholds > 0:
            self.issues['validity'].append(
                f"❌ {invalid_thresholds} items have negative reorder thresholds"
            )
            
        # Completeness
        missing_warehouse = sum(1 for row in rows if not row.get('warehouse'))
        if missing_warehouse > 0:
            self.issues['completeness'].append(
                f"🏭 {missing_warehouse} items missing warehouse location"
            )
            
    def _assess_customer_data(self, rows, headers):
        """Customer-specific assessments"""
        # Check for duplicates (consistency)
        emails = defaultdict(list)
        phones = defaultdict(list)
        
        for idx, row in enumerate(rows):
            if row.get('email'):
                emails[row['email']].append(idx)
            if row.get('phone'):
                phones[row['phone']].append(idx)
                
        duplicate_emails = sum(1 for email, indices in emails.items() if len(indices) > 1)
        duplicate_phones = sum(1 for phone, indices in phones.items() if len(indices) > 1)
        
        if duplicate_emails > 0:
            self.issues['consistency'].append(
                f"👥 {duplicate_emails} duplicate email addresses found"
            )
            
        # Validity checks
        invalid_emails = 0
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        for row in rows:
            if row.get('email') and not re.match(email_pattern, row['email']):
                invalid_emails += 1
                
        if invalid_emails > 0:
            self.issues['validity'].append(
                f"📧 {invalid_emails} invalid email addresses"
            )
            
    def _assess_generic_data(self, rows, headers):
        """Generic assessments for any data type"""
        # Completeness
        total_cells = len(rows) * len(headers)
        empty_cells = 0
        
        for row in rows:
            for header in headers:
                if not row.get(header, '').strip():
                    empty_cells += 1
                    
        completeness_pct = ((total_cells - empty_cells) / total_cells) * 100
        if completeness_pct < 80:
            self.issues['completeness'].append(
                f"📊 Only {completeness_pct:.0f}% of data cells are populated"
            )
            
    def _parse_number(self, value):
        """Safely parse a number from string"""
        if not value:
            return 0
        try:
            # Remove currency symbols and commas
            clean = str(value).replace('$', '').replace(',', '').strip()
            return float(clean)
        except:
            return 0
            
    def _calculate_scores(self):
        """Calculate dimension scores based on issues found"""
        # Simple scoring: start at 100% and deduct for issues
        for dimension in self.dimensions:
            if dimension in self.issues and self.issues[dimension]:
                # Deduct 15 points per issue, minimum score of 20
                score = max(20, 100 - (len(self.issues[dimension]) * 15))
            else:
                score = 95  # Not perfect, but no issues found
                
            self.scores[dimension] = score
            
    def _generate_report(self):
        """Generate business-friendly report"""
        overall_score = sum(self.scores.values()) / len(self.scores)
        
        print("\n" + "="*50)
        print("📊 ADRI ASSESSMENT RESULTS")
        print("="*50)
        
        print(f"\n🎯 Overall Data Quality Score: {overall_score:.0f}/100")
        
        if overall_score >= 80:
            print("✅ Status: GOOD - Data is ready for AI agents")
        elif overall_score >= 60:
            print("⚠️  Status: FAIR - Some issues need attention")
        else:
            print("❌ Status: POOR - Significant issues found")
            
        print("\n📈 Dimension Scores:")
        print("-" * 30)
        for dimension, score in self.scores.items():
            icon = "✅" if score >= 80 else "⚠️" if score >= 60 else "❌"
            print(f"{icon} {dimension.capitalize()}: {score:.0f}%")
            
        if any(self.issues.values()):
            print("\n🔍 Key Findings:")
            print("-" * 30)
            for dimension, issues in self.issues.items():
                if issues:
                    print(f"\n{dimension.upper()}:")
                    for issue in issues:
                        print(f"  • {issue}")
                        
        print("\n💡 Business Impact:")
        print("-" * 30)
        if overall_score < 60:
            print("⚠️  Using this data with AI agents could lead to:")
            print("  • Incorrect automated decisions")
            print("  • Financial losses from bad predictions")
            print("  • Customer dissatisfaction")
        else:
            print("✅ With some improvements, this data can enable:")
            print("  • Reliable AI-powered automation")
            print("  • Confident decision making")
            print("  • Scalable agent workflows")
            
        print("\n🚀 Next Steps:")
        print("-" * 30)
        print("1. Address the issues identified above")
        print("2. Install full ADRI for detailed analysis:")
        print("   pip install adri")
        print("3. Run comprehensive assessment:")
        print("   adri assess your_data.csv --output report")
        print("\n" + "="*50)


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python try_it.py <csv_file>")
        print("\nExample:")
        print("  python try_it.py samples/crm_data.csv")
        sys.exit(1)
        
    filepath = sys.argv[1]
    
    if not os.path.exists(filepath):
        print(f"❌ Error: File not found: {filepath}")
        sys.exit(1)
        
    # Create and run assessment
    assessor = MinimalADRI()
    assessor.assess_csv(filepath)
    

if __name__ == "__main__":
    main()
