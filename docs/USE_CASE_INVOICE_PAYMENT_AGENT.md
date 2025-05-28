# Use Case: Invoice Payment Agent with ADRI

## Executive Summary

This document demonstrates how ADRI (Agent Data Readiness Index) enables reliable, high-stakes agent workflows using an invoice payment automation scenario. It shows how data quality assurance can transform a risky automation into a trusted business process.

**Key Value**: Enable agents to make $50K+ payment decisions with 99.9% reliability by ensuring data quality before processing.

## Table of Contents

1. [The Business Problem](#the-business-problem)
2. [Solution Architecture](#solution-architecture)
3. [Implementation Guide](#implementation-guide)
4. [Demo Scenario](#demo-scenario)
5. [Integration Patterns](#integration-patterns)
6. [Metrics and ROI](#metrics-and-roi)
7. [Next Steps](#next-steps)

## The Business Problem

### Current State
- Fortune 500 companies process millions of invoices annually
- Manual review costs $15-30 per invoice
- 2% error rate leads to millions in duplicate payments or fraud
- Companies want automation but can't risk payment errors

### The Reliability Gap
Organizations attempting to automate invoice approval face critical data issues:
- **Vendor master data**: Duplicates, outdated banking information
- **Purchase order data**: Mismatched amounts, missing entries
- **Contract data**: Expired terms, incomplete records
- **Invoice data**: OCR errors, format inconsistencies

Without reliable data, agents make costly mistakes that destroy trust in automation.

## Solution Architecture

### High-Level Flow

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌──────────┐
│   Invoice   │────▶│ ADRI Quality │────▶│    Agent    │────▶│ Payment  │
│   Arrives   │     │    Check     │     │  Decision   │     │ Approved │
└─────────────┘     └──────────────┘     └─────────────┘     └──────────┘
                            │                     │
                            ▼                     ▼
                    ┌──────────────┐     ┌─────────────┐
                    │ Quality Fail │     │Human Review │
                    │    Alert     │     │  Required   │
                    └──────────────┘     └─────────────┘
```

### Component Details

1. **Data Sources** (Monitored by ADRI)
   - `vendors.csv` - Vendor master data with banking details
   - `purchase_orders.csv` - Active POs with approved amounts
   - `contracts.csv` - Contract terms and validity periods
   - `invoices.csv` - Incoming invoices for processing

2. **ADRI Assessment**
   - Validates data quality across 5 dimensions
   - Generates quality scores for each data source
   - Blocks processing if quality below thresholds

3. **Payment Agent**
   - Simple decision logic that relies on data quality
   - Only processes invoices when data meets standards
   - Full audit trail of quality scores for each decision

## Implementation Guide

### Step 1: Baseline Data Quality Assessment

```bash
# Export current data sources
python export_data.py --source vendors > vendors.csv
python export_data.py --source purchase_orders > purchase_orders.csv
python export_data.py --source contracts > contracts.csv

# Generate ADRI metadata
adri init vendors.csv
adri init purchase_orders.csv
adri init contracts.csv

# Run baseline assessment
adri assess vendors.csv
adri assess purchase_orders.csv
adri assess contracts.csv
```

### Step 2: Define Quality Requirements

```python
# quality_requirements.py
QUALITY_REQUIREMENTS = {
    'vendors': {
        'min_score': 95,
        'critical_dimensions': ['validity', 'completeness'],
        'specific_checks': {
            'bank_account_format': 'valid_iban',
            'tax_id': 'not_null',
            'active_status': 'boolean'
        }
    },
    'purchase_orders': {
        'min_score': 90,
        'critical_dimensions': ['freshness', 'consistency'],
        'specific_checks': {
            'amount': 'positive_number',
            'approval_date': 'within_365_days'
        }
    },
    'contracts': {
        'min_score': 95,
        'critical_dimensions': ['freshness', 'validity'],
        'specific_checks': {
            'expiry_date': 'future_date',
            'signed_status': 'true'
        }
    }
}
```

### Step 3: Implement the Agent with ADRI Guard

```python
# invoice_payment_agent.py
from adri import DataSourceAssessor, adri_guarded
from quality_requirements import QUALITY_REQUIREMENTS
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class InvoicePaymentAgent:
    def __init__(self):
        self.assessor = DataSourceAssessor()
        self.quality_requirements = QUALITY_REQUIREMENTS
        
    @adri_guarded(min_score=95)
    def process_invoice(self, invoice_id, data_source="vendors.csv"):
        """Process invoice with ADRI quality checks"""
        
        # The @adri_guarded decorator ensures data quality before this function runs
        
        # Assess all data sources
        quality_reports = {}
        for source_name, path in {
            'vendors': 'vendors.csv',
            'purchase_orders': 'purchase_orders.csv',
            'contracts': 'contracts.csv'
        }.items():
            report = self.assessor.assess_file(path)
            quality_reports[source_name] = report
            
            if report.overall_score < self.quality_requirements[source_name]['min_score']:
                logger.warning(f"Data quality check failed for {source_name}")
                return {
                    'invoice_id': invoice_id,
                    'status': 'blocked',
                    'reason': f'{source_name} data quality below threshold',
                    'quality_score': report.overall_score,
                    'action_required': 'human_review'
                }
        
        # Step 2: Load invoice data (quality assured)
        invoice = self._load_invoice(invoice_id)
        vendor = self._load_vendor(invoice['vendor_id'])
        po = self._load_purchase_order(invoice['po_number'])
        contract = self._load_contract(invoice['contract_id'])
        
        # Step 3: Apply business logic (simple for demo)
        decision = self._make_payment_decision(invoice, vendor, po, contract)
        
        # Step 4: Return decision with audit trail
        return {
            'invoice_id': invoice_id,
            'status': decision['status'],
            'amount': invoice['amount'],
            'vendor': vendor['name'],
            'quality_scores': {k: v.overall_score for k, v in quality_reports.items()},
            'decision_timestamp': datetime.now().isoformat(),
            'audit_trail': {
                'data_quality': {k: v.to_dict() for k, v in quality_reports.items()},
                'business_logic': decision['reasoning']
            }
        }
```

### Step 4: Continuous Monitoring Setup

```yaml
# adri_monitoring.yaml
monitoring:
  name: "Invoice Payment Data Quality"
  frequency: "*/10 * * * *"  # Every 10 minutes
  
  data_sources:
    - name: "vendors"
      path: "vendors.csv"
      thresholds:
        validity: 95
        completeness: 98
        consistency: 90
      alerts:
        - type: "slack"
          webhook: "${SLACK_WEBHOOK_URL}"
          message: "Vendor data quality dropped below threshold"
          
    - name: "purchase_orders"
      path: "purchase_orders.csv"
      thresholds:
        freshness: 90
        consistency: 95
      alerts:
        - type: "email"
          to: "data-team@company.com"
          subject: "PO Data Quality Alert"
          
    - name: "contracts"
      path: "contracts.csv"
      thresholds:
        freshness: 95
        validity: 98
      alerts:
        - type: "pagerduty"
          service_key: "${PAGERDUTY_KEY}"
          severity: "high"
```

## Demo Scenario

### Setup: Prepare Demo Data

```python
# demo_data_generator.py
import pandas as pd
import random
from datetime import datetime, timedelta

def generate_demo_data():
    """Generate realistic demo data with intentional quality issues"""
    
    # Vendors (with some quality issues)
    vendors = []
    for i in range(100):
        vendor = {
            'vendor_id': f'V{i:04d}',
            'name': f'Vendor {i}',
            'tax_id': f'TAX{i:06d}' if i % 10 != 0 else None,  # 10% missing
            'bank_account': f'IBAN{i:020d}' if i % 15 != 0 else 'INVALID',  # Some invalid
            'active': True if i % 20 != 0 else False
        }
        vendors.append(vendor)
    
    # Purchase Orders (with freshness issues)
    pos = []
    for i in range(200):
        days_old = random.randint(1, 500)  # Some are too old
        po = {
            'po_number': f'PO{i:06d}',
            'vendor_id': f'V{random.randint(0, 99):04d}',
            'amount': round(random.uniform(1000, 100000), 2),
            'created_date': (datetime.now() - timedelta(days=days_old)).isoformat(),
            'status': 'approved'
        }
        pos.append(po)
    
    # Save demo data
    pd.DataFrame(vendors).to_csv('demo_vendors.csv', index=False)
    pd.DataFrame(pos).to_csv('demo_purchase_orders.csv', index=False)
```

### Demo Flow Script

```python
# demo_script.py
"""
ADRI Invoice Payment Demo
Shows how data quality prevents costly payment errors
"""

print("=== ADRI Invoice Payment Demo ===\n")

# 1. Show the risky invoice
print("📄 New Invoice Received:")
print("   Invoice ID: INV-2024-0521")
print("   Vendor: Acme Supplies")
print("   Amount: $50,000")
print("   Status: Pending Approval\n")

input("Press Enter to process without ADRI...")

# 2. Demonstrate failure without ADRI
print("❌ Processing without quality checks...")
print("   ⚠️  Payment sent to WRONG ACCOUNT!")
print("   💸 $50,000 sent to inactive vendor's old bank\n")

input("Press Enter to try with ADRI...")

# 3. Run ADRI assessment
print("✅ Running ADRI Quality Assessment...")
os.system("adri assess demo_vendors.csv")
print("\n🔍 ADRI Found Issues:")
print("   - Vendor 'Acme Supplies' marked as INACTIVE")
print("   - Bank account format INVALID")
print("   - Last update: 18 months ago\n")

# 4. Show agent decision with ADRI
print("🤖 Agent Decision with ADRI Guard:")
print("   Status: BLOCKED")
print("   Reason: Vendor data quality below threshold (65%)")
print("   Action: Escalated to human review")
print("   Result: 💰 $50,000 payment error PREVENTED\n")

# 5. Fix and retry
input("Press Enter to fix data and retry...")
print("👨‍💼 Human review completed:")
print("   - Vendor status updated to ACTIVE")
print("   - New bank account verified")
print("   - Contract renewed\n")

print("✅ Re-running with updated data...")
print("   ADRI Score: 98% - PASSED")
print("   Payment: APPROVED")
print("   $50,000 sent to correct account\n")

print("🎯 Demo Summary:")
print("   Without ADRI: $50,000 loss")
print("   With ADRI: $0 loss + peace of mind")
```

## Integration Patterns

### Pattern 1: Verodat Platform Integration

```python
# verodat_integration.py
from verodat import DataSupply
from adri import ADRIClient

class VerodatInvoiceAgent:
    def __init__(self, verodat_config):
        self.verodat = DataSupply(verodat_config)
        self.adri_client = ADRIClient()
        
    def process_invoice_with_verodat(self, invoice_id):
        """Use Verodat as the data quality broker"""
        
        # Verodat maintains ADRI scores for all connected sources
        quality_report = self.verodat.get_quality_report([
            'erp.vendors',
            'finance.purchase_orders',
            'legal.contracts'
        ])
        
        if quality_report.overall_score < 95:
            # Verodat can trigger data refresh/cleanup
            self.verodat.request_data_improvement(quality_report.issues)
            return {'status': 'pending_data_quality'}
        
        # Get quality-assured data from Verodat
        invoice_context = self.verodat.get_invoice_context(invoice_id)
        
        # Process with confidence
        return self.make_payment_decision(invoice_context)
```

### Pattern 2: LangChain Integration

```python
# langchain_integration.py
from langchain.agents import Tool, initialize_agent, AgentType
from langchain.llms import OpenAI
from adri.integrations.langchain import create_adri_tool

# Create ADRI tool for LangChain
adri_tool = create_adri_tool(min_score=90)

# Create payment approval agent
payment_agent = initialize_agent(
    tools=[adri_tool],
    llm=OpenAI(temperature=0),
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True
)

# Agent automatically checks data quality before decisions
result = payment_agent.run(
    "Check if vendors.csv meets quality requirements for payment processing"
)
```

## Metrics and ROI

### Key Performance Indicators

1. **Error Prevention**
   - Baseline: 2% payment error rate = $2M annual loss
   - With ADRI: 0.01% error rate = $10K annual loss
   - Savings: $1.99M annually

2. **Processing Efficiency**
   - Manual review: $20 per invoice × 1M invoices = $20M
   - Automated (with ADRI): $0.50 per invoice = $500K
   - Savings: $19.5M annually

3. **Time to Deploy**
   - Without quality assurance: 6-12 months of testing
   - With ADRI: 4-6 weeks to production
   - Time saved: 5-11 months

### ROI Calculation

```
Investment:
- ADRI implementation: $50K (one-time)
- Verodat platform: $10K/month
- Total Year 1: $170K

Returns:
- Error prevention: $1.99M
- Process efficiency: $19.5M
- Total Year 1: $21.49M

ROI: 12,641% (126x return)
Payback period: 3 days
```

## Next Steps

### For Developers

1. **Try the Demo**
   ```bash
   git clone https://github.com/adri/invoice-demo
   cd invoice-demo
   python demo_script.py
   ```

2. **Implement in Your Agent**
   - Add ADRI checks at data ingestion points
   - Define quality thresholds for your use case
   - Set up monitoring and alerts

3. **Contribute**
   - Share your quality requirements
   - Add industry-specific rules
   - Improve integration patterns

### For Organizations

1. **Pilot Program**
   - Select high-value, repetitive process
   - Implement ADRI guards
   - Measure error reduction

2. **Scale Adoption**
   - Standardize quality requirements
   - Deploy Verodat for enterprise data management
   - Train teams on ADRI principles

3. **Join the Community**
   - Share success stories
   - Contribute industry templates
   - Shape ADRI standards

---

## Resources

- [ADRI Documentation](https://github.com/adri/docs)
- [Verodat Platform](https://verodat.com)
- Example Code Repository (Coming Soon)
- Community Forum (Coming Soon)

## Contact

For questions about this use case or to discuss implementation:
- Email: use-cases@adri.dev
- Slack: #invoice-automation channel

## Purpose & Test Coverage

**Why this file exists**: Demonstrates a high-stakes enterprise use case where ADRI enables automated invoice payment agents by ensuring data quality before processing financial transactions.

**Key responsibilities**:
- Illustrate the business problem of unreliable payment automation
- Show implementation with ADRI quality guards
- Provide concrete code examples and integration patterns
- Demonstrate ROI calculations and metrics
- Guide organizations through adoption steps

**Test coverage**: This document's examples, claims, and features should be verified by tests documented in [invoice_payment_agent_test_coverage.md](./test_coverage/invoice_payment_agent_test_coverage.md)
