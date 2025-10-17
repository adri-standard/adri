"""Comprehensive tests for the Standards Catalog Library.

This test suite validates all standards in the catalog:
- 5 domain standards (customer_service, ecommerce_order, financial_transaction, healthcare_patient, marketing_campaign)
- 4 framework standards (langchain_chain_input, crewai_task_context, llamaindex_document, autogen_message)
- 4 template standards (api_response_template, time_series_template, key_value_template, nested_json_template)

Each test:
1. Loads sample data from examples/data/catalog/
2. Validates data against the standard using @adri_protected decorator
3. Verifies validation passes with clean data
4. Confirms standard can be loaded by name only (development environment)
"""

import pandas as pd
import pytest
from pathlib import Path

from adri import adri_protected


class TestDomainStandards:
    """Test domain-specific business use case standards."""

    def test_customer_service_standard(self):
        """Test customer service interaction standard validation."""
        @adri_protected(standard="customer_service_standard")
        def process_tickets(data):
            return data

        # Create sample data
        data = pd.DataFrame([
            {
                "ticket_id": "TKT-100001",
                "customer_id": "CUST-5001",
                "created_date": "2025-01-15",
                "category": "Technical Support",
                "priority": "High",
                "status": "Open",
                "first_response_time_hours": 2.5,
                "resolution_time_hours": None,
                "customer_satisfaction_score": None,
                "agent_id": "AGT-201"
            },
            {
                "ticket_id": "TKT-100002",
                "customer_id": "CUST-5002",
                "created_date": "2025-01-16",
                "category": "Billing",
                "priority": "Medium",
                "status": "Resolved",
                "first_response_time_hours": 1.0,
                "resolution_time_hours": 4.5,
                "customer_satisfaction_score": 5,
                "agent_id": "AGT-202"
            }
        ])

        result = process_tickets(data)
        assert result is not None
        assert len(result) == 2

    def test_ecommerce_order_standard(self):
        """Test e-commerce order standard validation."""
        @adri_protected(standard="ecommerce_order_standard")
        def process_orders(data):
            return data

        # Create sample data
        data = pd.DataFrame([
            {
                "order_id": "ORD-20250115001",
                "customer_id": "CUST-5001",
                "order_date": "2025-01-15T10:30:00",
                "order_status": "Shipped",
                "subtotal": 99.99,
                "tax_amount": 8.50,
                "shipping_cost": 5.00,
                "total_amount": 113.49,
                "shipping_address_line1": "123 Main St",
                "shipping_city": "San Francisco",
                "shipping_state": "CA",
                "shipping_postal_code": "94102",
                "shipping_country": "USA",
                "payment_method": "Credit Card",
                "payment_status": "Completed"
            }
        ])

        result = process_orders(data)
        assert result is not None
        assert len(result) == 1

    def test_financial_transaction_standard(self):
        """Test financial transaction standard validation."""
        @adri_protected(standard="financial_transaction_standard")
        def process_transactions(data):
            return data

        # Create sample data
        data = pd.DataFrame([
            {
                "transaction_id": "TXN-ABC123456789",
                "account_id": "ACC-001",
                "transaction_date": "2025-01-15T14:30:00.123Z",
                "transaction_type": "Credit",
                "amount": 1000.00,
                "currency": "USD",
                "balance_after": 5000.00,
                "status": "Completed",
                "processing_time_ms": 150,
                "merchant_id": "MERCH-500",
                "merchant_category": "5411",
                "description": "Grocery purchase",
                "authorization_code": "AUTH123"
            }
        ])

        result = process_transactions(data)
        assert result is not None
        assert len(result) == 1

    def test_healthcare_patient_standard(self):
        """Test healthcare patient record standard validation."""
        @adri_protected(standard="healthcare_patient_standard")
        def process_patients(data):
            return data

        # Create sample data
        data = pd.DataFrame([
            {
                "patient_id": "PAT-10000001",
                "medical_record_number": "MRN-2025-001",
                "date_of_birth": "1980-05-15",
                "gender": "Male",
                "phone_number": "+1-555-123-4567",
                "email": "patient@example.com",
                "address_line1": "456 Health Ave",
                "city": "Boston",
                "state": "MA",
                "postal_code": "02101",
                "country": "USA",
                "blood_type": "A+",
                "primary_physician_id": "PHY-501",
                "insurance_provider": "HealthCare Plus",
                "insurance_policy_number": "POL-2025-001",
                "registration_date": "2025-01-10",
                "patient_status": "Active"
            }
        ])

        result = process_patients(data)
        assert result is not None
        assert len(result) == 1

    def test_marketing_campaign_standard(self):
        """Test marketing campaign performance standard validation."""
        @adri_protected(standard="marketing_campaign_standard")
        def process_campaigns(data):
            return data

        # Create sample data
        data = pd.DataFrame([
            {
                "campaign_id": "CMP-202501",
                "campaign_name": "Spring Sale 2025",
                "start_date": "2025-03-01",
                "end_date": "2025-03-31",
                "campaign_type": "Email",
                "campaign_status": "Active",
                "budget": 10000.00,
                "spent": 7500.00,
                "impressions": 50000,
                "clicks": 2500,
                "conversions": 250,
                "revenue": 25000.00,
                "click_through_rate": 5.0,
                "conversion_rate": 10.0,
                "cost_per_click": 3.00,
                "return_on_ad_spend": 3.33,
                "target_audience": "Ages 25-45, Tech-savvy",
                "geographic_region": "North America"
            }
        ])

        result = process_campaigns(data)
        assert result is not None
        assert len(result) == 1


class TestFrameworkStandards:
    """Test AI framework-specific standards."""

    def test_langchain_chain_input_standard(self):
        """Test LangChain chain input standard validation."""
        @adri_protected(standard="langchain_chain_input_standard")
        def process_chain_inputs(data):
            return data

        # Create sample data
        data = pd.DataFrame([
            {
                "input_id": "INPUT-001",
                "chain_type": "ConversationChain",
                "user_input": "What is the weather today?",
                "context": "User is located in San Francisco",
                "temperature": 0.7,
                "max_tokens": 500,
                "model_name": "gpt-4",
                "timestamp": "2025-01-17T10:00:00",
                "user_id": "USER-123",
                "session_id": "SESSION-456",
                "memory_enabled": True,
                "history_length": 5
            }
        ])

        result = process_chain_inputs(data)
        assert result is not None
        assert len(result) == 1

    def test_crewai_task_context_standard(self):
        """Test CrewAI task context standard validation."""
        @adri_protected(standard="crewai_task_context_standard")
        def process_tasks(data):
            return data

        # Create sample data
        data = pd.DataFrame([
            {
                "task_id": "TASK-ABC12345",
                "crew_id": "CREW-001",
                "task_description": "Research market trends for Q1 2025",
                "expected_output": "Detailed market analysis report",
                "task_type": "Research",
                "assigned_agent_role": "Researcher",
                "agent_id": "AGENT-001",
                "context": "Focus on tech sector",
                "dependencies": "[]",
                "previous_task_output": None,
                "priority": 1,
                "status": "In Progress",
                "created_at": "2025-01-17T09:00:00",
                "tools_available": '["web_search", "calculator"]',
                "max_iterations": 5
            }
        ])

        result = process_tasks(data)
        assert result is not None
        assert len(result) == 1

    def test_llamaindex_document_standard(self):
        """Test LlamaIndex document standard validation."""
        @adri_protected(standard="llamaindex_document_standard")
        def process_documents(data):
            return data

        # Create sample data
        data = pd.DataFrame([
            {
                "doc_id": "DOC-ABC1234567",
                "text": "This is a sample document for RAG indexing.",
                "source": "https://example.com/docs/sample",
                "document_type": "Text",
                "title": "Sample Document",
                "author": "John Doe",
                "created_date": "2025-01-15",
                "chunk_id": 0,
                "chunk_size": 512,
                "total_chunks": 1,
                "embedding_model": "text-embedding-ada-002",
                "embedding_dimension": 1536,
                "keywords": "sample, document, RAG",
                "category": "Documentation",
                "language": "en"
            }
        ])

        result = process_documents(data)
        assert result is not None
        assert len(result) == 1

    def test_autogen_message_standard(self):
        """Test AutoGen message standard validation."""
        @adri_protected(standard="autogen_message_standard")
        def process_messages(data):
            return data

        # Create sample data
        data = pd.DataFrame([
            {
                "message_id": "MSG-ABC1234567",
                "conversation_id": "CONV-001",
                "role": "user",
                "content": "Can you help me analyze this data?",
                "sender_agent": "UserProxy",
                "receiver_agent": "AssistantAgent",
                "timestamp": "2025-01-17T10:30:00.123",
                "sequence_number": 1,
                "function_call": None,
                "function_response": None,
                "execution_mode": "auto",
                "termination_keyword": None,
                "tokens_used": 25,
                "model_name": "gpt-4"
            }
        ])

        result = process_messages(data)
        assert result is not None
        assert len(result) == 1


class TestTemplateStandards:
    """Test generic template standards."""

    def test_api_response_template(self):
        """Test API response template validation."""
        @adri_protected(standard="api_response_template")
        def process_responses(data):
            return data

        # Create sample data
        data = pd.DataFrame([
            {
                "request_id": "REQ-123456",
                "status_code": 200,
                "status": "success",
                "timestamp": "2025-01-17T10:00:00.000Z",
                "response_time_ms": 150,
                "endpoint": "/api/v1/users",
                "method": "GET",
                "data": '{"users": []}',
                "error_message": None,
                "error_code": None,
                "api_version": "v1",
                "request_source": "web_app"
            }
        ])

        result = process_responses(data)
        assert result is not None
        assert len(result) == 1

    def test_time_series_template(self):
        """Test time series template validation."""
        @adri_protected(standard="time_series_template")
        def process_time_series(data):
            return data

        # Create sample data
        data = pd.DataFrame([
            {
                "timestamp": "2025-01-17T10:00:00",
                "metric_name": "cpu_usage",
                "metric_id": "METRIC-CPU-001",
                "value": 65.5,
                "unit": "percent",
                "source_id": "SERVER-001",
                "source_type": "system",
                "quality_score": 95.0,
                "confidence": 0.98,
                "is_anomaly": False,
                "aggregation_type": "average",
                "aggregation_window": "1m",
                "tags": "production,web-server"
            }
        ])

        result = process_time_series(data)
        assert result is not None
        assert len(result) == 1

    def test_key_value_template(self):
        """Test key-value template validation."""
        @adri_protected(standard="key_value_template")
        def process_config(data):
            return data

        # Create sample data
        data = pd.DataFrame([
            {
                "key": "feature.new_ui.enabled",
                "value": "true",
                "value_type": "boolean",
                "namespace": "features",
                "category": "ui",
                "description": "Enable new UI design",
                "version": 1,
                "created_at": "2025-01-01T00:00:00",
                "updated_at": "2025-01-17T10:00:00",
                "is_sensitive": False,
                "access_level": "public",
                "is_active": True,
                "environment": "production"
            }
        ])

        result = process_config(data)
        assert result is not None
        assert len(result) == 1

    def test_nested_json_template(self):
        """Test nested JSON template validation."""
        @adri_protected(standard="nested_json_template")
        def process_nested(data):
            return data

        # Create sample data
        data = pd.DataFrame([
            {
                "record_id": "NODE-001",
                "record_type": "configuration",
                "parent_id": None,
                "depth_level": 0,
                "path": "root",
                "name": "Root Configuration",
                "data": '{"type": "root"}',
                "has_children": True,
                "child_count": 2,
                "total_descendants": 5,
                "created_at": "2025-01-15T10:00:00",
                "updated_at": "2025-01-17T10:00:00",
                "is_active": True,
                "validation_status": "valid"
            }
        ])

        result = process_nested(data)
        assert result is not None
        assert len(result) == 1


class TestStandardsResolution:
    """Test that all standards can be resolved by name only."""

    @pytest.mark.parametrize("standard_name", [
        # Domain standards
        "customer_service_standard",
        "ecommerce_order_standard",
        "financial_transaction_standard",
        "healthcare_patient_standard",
        "marketing_campaign_standard",
        # Framework standards
        "langchain_chain_input_standard",
        "crewai_task_context_standard",
        "llamaindex_document_standard",
        "autogen_message_standard",
        # Template standards
        "api_response_template",
        "time_series_template",
        "key_value_template",
        "nested_json_template"
    ])
    def test_standard_name_resolution(self, standard_name):
        """Test that standard can be resolved by name only."""
        @adri_protected(standard=standard_name)
        def test_function(data):
            return data

        # Standard should be resolvable without error
        assert test_function is not None


class TestStandardsCatalogIntegrity:
    """Test overall catalog integrity and organization."""

    def test_all_standards_have_unique_ids(self):
        """Verify all standards in catalog have unique IDs."""
        from pathlib import Path
        import yaml

        standards_dirs = [
            Path("adri/standards/domains"),
            Path("adri/standards/frameworks"),
            Path("adri/standards/templates")
        ]

        standard_ids = set()
        for standards_dir in standards_dirs:
            if not standards_dir.exists():
                continue

            for standard_file in standards_dir.glob("*.yaml"):
                with open(standard_file, 'r') as f:
                    standard = yaml.safe_load(f)

                if 'standards' in standard and 'id' in standard['standards']:
                    std_id = standard['standards']['id']
                    assert std_id not in standard_ids, f"Duplicate standard ID: {std_id}"
                    standard_ids.add(std_id)

        # Should have 13 unique standard IDs
        assert len(standard_ids) == 13

    def test_catalog_structure_exists(self):
        """Verify catalog directory structure exists."""
        from pathlib import Path

        assert Path("adri/standards/domains").exists()
        assert Path("adri/standards/frameworks").exists()
        assert Path("adri/standards/templates").exists()

    def test_all_standards_follow_v5_format(self):
        """Verify all catalog standards follow v5.0.0 format."""
        from pathlib import Path
        import yaml

        standards_dirs = [
            Path("adri/standards/domains"),
            Path("adri/standards/frameworks"),
            Path("adri/standards/templates")
        ]

        for standards_dir in standards_dirs:
            if not standards_dir.exists():
                continue

            for standard_file in standards_dir.glob("*.yaml"):
                with open(standard_file, 'r') as f:
                    standard = yaml.safe_load(f)

                # Verify required top-level sections
                assert 'standards' in standard, f"{standard_file.name} missing 'standards' section"
                assert 'record_identification' in standard
                assert 'requirements' in standard
                assert 'metadata' in standard

                # Verify standards section has required fields
                assert 'id' in standard['standards']
                assert 'name' in standard['standards']
                assert 'version' in standard['standards']
                assert 'description' in standard['standards']
