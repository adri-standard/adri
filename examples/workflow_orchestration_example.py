"""
ADRI Workflow Orchestration Example.

Demonstrates how to use workflow_context and data_provenance parameters
for compliance-grade audit trails in multi-step AI workflows.
"""

import pandas as pd
from datetime import datetime
from adri import adri_protected


# Example 1: Simple workflow step with execution tracking
@adri_protected(
    data_param="customer_data",
    standard_name="customer_data_standard",
    workflow_context={
        "run_id": "run_20250110_153000_abc123",
        "workflow_id": "customer_onboarding_v2",
        "workflow_version": "2.1.0",
        "step_id": "validate_customer_info",
        "step_sequence": 1,
        "run_at_utc": datetime.utcnow().isoformat() + "Z",
        "data_source_type": "verodat_query",
    },
    data_provenance={
        "source_type": "verodat_query",
        "verodat_query_id": 12345,
        "verodat_account_id": 91,
        "verodat_workspace_id": 161,
        "verodat_run_at_utc": "2025-01-10T14:30:00Z",
        "verodat_query_sql": "SELECT * FROM customers WHERE status='active'",
        "data_retrieved_at_utc": datetime.utcnow().isoformat() + "Z",
        "record_count": 150,
    },
)
def validate_customer_data(customer_data: pd.DataFrame) -> pd.DataFrame:
    """Validate customer data in workflow step 1."""
    # Your business logic here
    return customer_data


# Example 2: Workflow step with file-based provenance
@adri_protected(
    data_param="invoice_data",
    standard_name="invoice_data_standard",
    workflow_context={
        "run_id": "run_20250110_153000_abc123",
        "workflow_id": "invoice_processing_v1",
        "workflow_version": "1.0.0",
        "step_id": "validate_invoices",
        "step_sequence": 2,
        "run_at_utc": datetime.utcnow().isoformat() + "Z",
        "data_source_type": "file",
    },
    data_provenance={
        "source_type": "file",
        "file_path": "/data/invoices/batch_2025_01.csv",
        "file_size_bytes": 524288,
        "file_hash": "sha256:abc123...",
        "data_retrieved_at_utc": datetime.utcnow().isoformat() + "Z",
        "record_count": 1000,
    },
)
def process_invoices(invoice_data: pd.DataFrame) -> pd.DataFrame:
    """Process invoices in workflow step 2."""
    # Your invoice processing logic
    return invoice_data


# Example 3: Workflow step with API provenance
@adri_protected(
    data_param="market_data",
    standard_name="market_data_standard",
    workflow_context={
        "run_id": "run_20250110_153000_abc123",
        "workflow_id": "market_analysis_v3",
        "workflow_version": "3.2.1",
        "step_id": "fetch_market_data",
        "step_sequence": 1,
        "run_at_utc": datetime.utcnow().isoformat() + "Z",
        "data_source_type": "api",
    },
    data_provenance={
        "source_type": "api",
        "api_endpoint": "https://api.market-data.com/v1/quotes",
        "api_http_method": "GET",
        "api_response_hash": "sha256:def456...",
        "data_retrieved_at_utc": datetime.utcnow().isoformat() + "Z",
        "record_count": 500,
        "notes": "Real-time market data from primary feed",
    },
)
def fetch_market_data(market_data: pd.DataFrame) -> pd.DataFrame:
    """Fetch and validate market data from API."""
    # Your market data logic
    return market_data


# Example 4: Workflow step using output from previous step
@adri_protected(
    data_param="enriched_data",
    standard_name="enriched_customer_standard",
    workflow_context={
        "run_id": "run_20250110_153000_abc123",
        "workflow_id": "customer_onboarding_v2",
        "workflow_version": "2.1.0",
        "step_id": "enrich_customer_data",
        "step_sequence": 2,
        "run_at_utc": datetime.utcnow().isoformat() + "Z",
        "data_source_type": "previous_step",
    },
    data_provenance={
        "source_type": "previous_step",
        "previous_step_id": "validate_customer_info",
        "previous_execution_id": "exec_20250110_153045_xyz789",
        "data_retrieved_at_utc": datetime.utcnow().isoformat() + "Z",
        "record_count": 150,
        "notes": "Enriched with demographic data",
    },
)
def enrich_customer_data(enriched_data: pd.DataFrame) -> pd.DataFrame:
    """Enrich customer data in workflow step 2."""
    # Your enrichment logic
    return enriched_data


# Example 5: Complete multi-step workflow
def run_complete_workflow():
    """Execute a complete multi-step workflow with full audit trail."""

    # Generate unique run ID for this workflow execution
    run_id = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}_workflow"

    # Step 1: Load and validate customer data
    customer_data = pd.DataFrame({
        "customer_id": [1, 2, 3],
        "name": ["Alice", "Bob", "Charlie"],
        "email": ["alice@example.com", "bob@example.com", "charlie@example.com"],
    })

    validated_customers = validate_customer_data(customer_data)

    # Step 2: Process invoices for these customers
    invoice_data = pd.DataFrame({
        "invoice_id": [101, 102, 103],
        "customer_id": [1, 2, 3],
        "amount": [100.50, 200.75, 150.25],
    })

    processed_invoices = process_invoices(invoice_data)

    print(f"✅ Workflow {run_id} completed successfully!")
    print(f"📊 Customers processed: {len(validated_customers)}")
    print(f"📊 Invoices processed: {len(processed_invoices)}")
    print(f"\n📝 Audit trail logged to:")
    print(f"   - adri_workflow_executions.csv")
    print(f"   - adri_data_provenance.csv")
    print(f"   - adri_assessment_logs.csv")


if __name__ == "__main__":
    # Enable audit logging in configuration
    import os
    os.environ["ADRI_AUDIT_ENABLED"] = "true"
    os.environ["ADRI_AUDIT_LOG_LOCATION"] = "./logs"

    run_complete_workflow()
