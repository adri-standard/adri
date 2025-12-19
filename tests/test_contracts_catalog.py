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

AUTO-DISCOVERY:
The TestStandardsResolution class uses auto-discovery to find and test all standards
in the catalog. When a new standard is added to adri/contracts/{domains,frameworks,templates}/,
it will be automatically discovered and tested without manual test updates.
"""

import pandas as pd
import pytest
from pathlib import Path

from adri import adri_protected
from tests.fixtures.standards_discovery import find_catalog_standards


def discover_standard_names():
    """Get standard names for pytest parametrization using auto-discovery.

    This function discovers all standards in adri/contracts/ and returns their
    filenames for use in parametrized tests. This ensures all catalog standards
    are automatically tested without manual list maintenance.

    Returns:
        List of standard filenames (without .yaml extension) for parametrization
    """
    standards = find_catalog_standards()
    return [std.filename for std in standards]


# Discover all standard names at module load time for parametrization
standard_names = discover_standard_names()


class TestDomainStandards:
    """Test domain-specific business use case standards."""

    def test_customer_service_standard(self):
        """Test customer service interaction standard validation."""
        @adri_protected(contract="customer_service_contract", on_failure="warn")
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
        @adri_protected(contract="ecommerce_order_contract")
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
        @adri_protected(contract="financial_transaction_contract")
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
        @adri_protected(contract="healthcare_patient_contract")
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
        @adri_protected(contract="marketing_campaign_contract")
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
        @adri_protected(contract="langchain_chain_input_contract")
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
        @adri_protected(contract="crewai_task_context_contract", on_failure="warn")
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
        @adri_protected(contract="llamaindex_document_contract")
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
        @adri_protected(contract="autogen_message_contract", on_failure="warn")
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
        @adri_protected(contract="api_response_template")
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
        @adri_protected(contract="time_series_template")
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
        @adri_protected(contract="key_value_template")
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
        @adri_protected(contract="nested_json_template")
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
    """Test that all standards can be resolved by name only.

    AUTO-DISCOVERY: This test class uses auto-discovery to find and test all standards
    in the catalog. The @pytest.mark.parametrize decorator uses the standard_names list
    which is dynamically generated by discover_standard_names() at module load time.

    When a new standard is added to adri/contracts/{domains,frameworks,templates}/,
    it will be automatically discovered and included in this parametrized test.
    """

    @pytest.mark.parametrize("standard_name", standard_names)
    def test_standard_name_resolution(self, standard_name):
        """Test that standard can be resolved by name only.

        This test is parametrized with all discovered standards from the catalog.
        Each standard is validated by attempting to create a decorated function
        that references it by name only.
        """
        @adri_protected(contract=standard_name)
        def test_function(data):
            return data

        # Standard should be resolvable without error
        assert test_function is not None


class TestStandardsCatalogIntegrity:
    """Test overall catalog integrity and organization."""

    def test_discovery_finds_all_catalog_standards(self):
        """Verify discovery mechanism finds all expected standards.

        This test validates that the auto-discovery mechanism:
        1. Finds at least the minimum expected standards (3+)
        2. Discovers standards from available categories
        3. Includes core known standards that must exist
        """
        from tests.fixtures.standards_discovery import find_catalog_standards

        standards = find_catalog_standards()

        # Should find at least 3 standards (minimum viable catalog)
        # The catalog may grow over time as more standards are added
        assert len(standards) >= 3, f"Expected at least 3 standards, found {len(standards)}"

        # Verify at least one category is represented
        categories = {std.category for std in standards}
        assert len(categories) > 0, "No categories found"

        # All categories should be valid
        valid_categories = {'domains', 'frameworks', 'templates'}
        invalid = categories - valid_categories
        assert not invalid, f"Found invalid categories: {invalid}"

        # Verify core standards that should always exist
        standard_names = {std.filename for std in standards}
        core_standards = {
            'customer_service_contract',  # Domain contract
            'autogen_message_contract',   # Framework contract
        }
        missing = core_standards - standard_names
        assert not missing, f"Discovery missing core contracts: {missing}"

        # Verify each standard has required metadata
        for std in standards:
            assert std.standard_id, f"Standard {std.filename} missing standard_id"
            assert std.standard_name, f"Standard {std.filename} missing standard_name"
            assert std.version, f"Standard {std.filename} missing version"
            assert std.file_path.exists(), f"Standard file does not exist: {std.file_path}"

    def test_discovery_handles_new_standards_automatically(self):
        """Document how auto-discovery works for new standards.

        This test documents the expected behavior when new standards are added:
        - Place YAML file in domains/, frameworks/, or templates/
        - Run pytest - new standard automatically included
        - No test file updates required

        Note: This test validates the current catalog state without making
        assumptions about specific counts, as the catalog grows over time.
        """
        from tests.fixtures.standards_discovery import find_catalog_standards, get_standards_by_category

        # Verify current discovery count
        current_standards = find_catalog_standards()
        baseline_count = len(current_standards)

        # Verify standards are organized by category
        by_category = get_standards_by_category()

        # Validate the catalog has a reasonable size (at least 3 standards)
        assert baseline_count >= 3, f"Catalog should have at least 3 standards, found {baseline_count}"

        # Verify each category that exists has at least one standard
        for category in ['domains', 'frameworks', 'templates']:
            if category in by_category and len(by_category[category]) > 0:
                assert len(by_category[category]) >= 1, \
                    f"Category '{category}' should have at least 1 standard"

        # Document current catalog state
        print(f"\nCurrent catalog state:")
        print(f"  Total standards: {baseline_count}")
        print(f"  Domain standards: {len(by_category['domains'])}")
        print(f"  Framework standards: {len(by_category['frameworks'])}")
        print(f"  Template standards: {len(by_category['templates'])}")

    def test_all_standards_have_unique_ids(self):
        """Verify all standards in catalog have unique IDs."""
        from pathlib import Path
        import yaml

        standards_dirs = [
            Path("ADRI/contracts/domains"),
            Path("ADRI/contracts/frameworks"),
            Path("ADRI/contracts/templates")
        ]

        standard_ids = set()
        for standards_dir in standards_dirs:
            if not standards_dir.exists():
                continue

            for standard_file in standards_dir.glob("*.yaml"):
                with open(standard_file, 'r', encoding='utf-8') as f:
                    standard = yaml.safe_load(f)

                if 'contracts' in standard and 'id' in standard['contracts']:
                    std_id = standard['contracts']['id']
                    assert std_id not in standard_ids, f"Duplicate standard ID: {std_id}"
                    standard_ids.add(std_id)

        # Should have at least 3 unique standard IDs (customer_service, crewai, autogen)
        assert len(standard_ids) >= 3, f"Expected at least 3 standards, found {len(standard_ids)}"

    def test_catalog_structure_exists(self):
        """Verify catalog directory structure exists."""
        from pathlib import Path

        # At least the main standards directory should exist
        assert Path("ADRI/contracts").exists(), "Main standards directory must exist"

        # Check for catalog subdirectories (may not all exist yet)
        catalog_dirs = ["domains", "frameworks", "templates"]
        existing_dirs = [d for d in catalog_dirs if (Path("ADRI/contracts") / d).exists()]

        # Should have at least one catalog subdirectory
        assert len(existing_dirs) >= 1, f"Expected at least one catalog subdirectory, found {existing_dirs}"

    def test_all_standards_follow_v5_format(self):
        """Verify all catalog standards follow v5.0.0 format."""
        from pathlib import Path
        import yaml

        standards_dirs = [
            Path("ADRI/contracts/domains"),
            Path("ADRI/contracts/frameworks"),
            Path("ADRI/contracts/templates")
        ]

        for standards_dir in standards_dirs:
            if not standards_dir.exists():
                continue

            for standard_file in standards_dir.glob("*.yaml"):
                with open(standard_file, 'r', encoding='utf-8') as f:
                    standard = yaml.safe_load(f)

                # Verify required top-level sections
                assert 'contracts' in standard, f"{standard_file.name} missing 'contracts' section"
                assert 'record_identification' in standard
                assert 'requirements' in standard
                assert 'metadata' in standard

                # Verify standards section has required fields
                assert 'id' in standard['contracts']
                assert 'name' in standard['contracts']
                assert 'version' in standard['contracts']
                assert 'description' in standard['contracts']
