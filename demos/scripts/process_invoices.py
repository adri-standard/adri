#!/usr/bin/env python3
"""
ADRI Demo: Invoice Processing Agent

Practical demonstration of using ADRI to protect an invoice processing agent.
Shows the new src/ layout imports and modern ADRI architecture.
"""

import sys
from pathlib import Path

# Add src directory to path for demo
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

import pandas as pd

from adri import adri_protected

# Sample invoice data for demonstration
SAMPLE_INVOICES = [
    {
        "invoice_id": "INV-2024-001",
        "vendor_name": "Acme Corp",
        "amount": 1250.00,
        "currency": "USD",
        "date": "2024-01-15",
        "status": "pending",
        "email": "billing@acme.com",
    },
    {
        "invoice_id": "INV-2024-002",
        "vendor_name": "TechSupply Inc",
        "amount": 875.50,
        "currency": "USD",
        "date": "2024-01-18",
        "status": "approved",
        "email": "accounts@techsupply.com",
    },
    {
        "invoice_id": "INV-2024-003",
        "vendor_name": "Office Solutions",
        "amount": 324.99,
        "currency": "USD",
        "date": "2024-01-20",
        "status": "pending",
        "email": "billing@officesolutions.com",
    },
]


@adri_protected(
    standard="invoice_data_standard",
    data_param="invoice_data",
    min_score=85,
    dimensions={
        "validity": 18,  # Amounts and emails must be valid
        "completeness": 19,  # All required fields must be present
        "consistency": 16,  # Date and currency formats must be consistent
    },
    on_failure="raise",  # Block processing of bad invoice data
    verbose=True,
)
def process_invoice_batch(invoice_data):
    """
    Process a batch of invoices with ADRI data quality protection.

    Args:
        invoice_data: DataFrame containing invoice records

    Returns:
        Processing results with approval decisions
    """
    print(f"🧾 Processing {len(invoice_data)} invoices...")

    results = []
    total_amount = 0

    for _, invoice in invoice_data.iterrows():
        # Extract invoice details
        invoice_id = invoice["invoice_id"]
        vendor = invoice["vendor_name"]
        amount = invoice["amount"]
        status = invoice["status"]

        # Business logic for invoice processing
        if amount > 1000:
            approval_required = True
            processing_priority = "high"
        else:
            approval_required = False
            processing_priority = "standard"

        # Simulate payment processing decision
        if status == "approved" or not approval_required:
            payment_status = "scheduled"
            total_amount += amount
        else:
            payment_status = "pending_approval"

        result = {
            "invoice_id": invoice_id,
            "vendor": vendor,
            "amount": amount,
            "approval_required": approval_required,
            "priority": processing_priority,
            "payment_status": payment_status,
        }

        results.append(result)
        print(f"  📄 {invoice_id}: {vendor} - ${amount:,.2f} ({payment_status})")

    summary = {
        "total_invoices": len(results),
        "total_amount": total_amount,
        "invoices_scheduled": len(
            [r for r in results if r["payment_status"] == "scheduled"]
        ),
        "invoices_pending": len(
            [r for r in results if r["payment_status"] == "pending_approval"]
        ),
        "results": results,
    }

    print(f"\n💰 Total Amount: ${total_amount:,.2f}")
    print(
        f"📊 Scheduled: {summary['invoices_scheduled']}, Pending: {summary['invoices_pending']}"
    )

    return summary


def main():
    """Run the invoice processing demo."""
    print("🚀 ADRI Invoice Processing Demo")
    print("=" * 40)

    # Convert sample data to DataFrame
    invoice_df = pd.DataFrame(SAMPLE_INVOICES)

    print(f"📥 Input Data: {len(invoice_df)} invoices")
    print(f"📊 Total Value: ${invoice_df['amount'].sum():,.2f}")
    print()

    try:
        # Process invoices with ADRI protection
        results = process_invoice_batch(invoice_df)

        print("\n✅ Invoice processing completed successfully!")
        print("🛡️  ADRI ensured data quality throughout the process")

    except Exception as e:
        print(f"\n❌ Invoice processing failed: {e}")
        print(
            "\n💡 This demonstrates ADRI protecting your agent from poor quality data"
        )
        print("   Fix the data quality issues and try again!")

        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
