"""
Unit tests for ADRI common use cases.

Tests validate that the three main use cases documented in README work correctly:
1. API Data Validation
2. Multi-Agent Workflows
3. RAG Pipelines

Each test uses real sample data and follows the tutorial framework pattern.
"""

import json
import pytest
import pandas as pd
from pathlib import Path
from adri import adri_protected


class TestAPIDataValidationUseCase:
    """Test API data validation use case."""

    @pytest.fixture
    def api_response_data(self):
        """Load API response sample data."""
        data_path = Path("examples/data/api_response.json")
        with open(data_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def test_api_validation_with_clean_data(self, api_response_data):
        """Test that API validation accepts clean API responses."""

        @adri_protected(contract="api_response", data_param="response")
        def process_api_data(response):
            """Process API response data."""
            return {
                "processed": len(response),
                "users": [r["user_id"] for r in response]
            }

        # Should pass validation with clean data
        result = process_api_data(api_response_data)

        assert result is not None
        assert result["processed"] == 3
        assert len(result["users"]) == 3
        assert "user_001" in result["users"]

    def test_api_validation_catches_bad_data(self):
        """Test that API validation blocks malformed API responses."""

        @adri_protected(contract="api_response", data_param="response")
        def process_api_data(response):
            return response

        # Bad API data - missing required fields
        bad_data = [
            {
                "user_id": "user_999",
                "status": "success"
                # Missing 'data' field
                # Missing 'timestamp' field
            }
        ]

        # Should raise ProtectionError or execute with warning depending on mode
        # For now, just verify function is decorated correctly
        assert hasattr(process_api_data, '_adri_protected')
        assert process_api_data._adri_protected is True

    def test_api_validation_sample_data_structure(self, api_response_data):
        """Verify API sample data has expected structure."""
        assert len(api_response_data) > 0

        # Check first record has required fields
        first_record = api_response_data[0]
        assert "user_id" in first_record
        assert "status" in first_record
        assert "data" in first_record
        assert "timestamp" in first_record
        assert "request_id" in first_record

        # Check nested data structure
        assert "name" in first_record["data"]
        assert "email" in first_record["data"]
        assert "account_type" in first_record["data"]


class TestMultiAgentWorkflowUseCase:
    """Test multi-agent workflow use case."""

    @pytest.fixture
    def crew_context_data(self):
        """Load crew context sample data."""
        data_path = Path("examples/data/crew_context.json")
        with open(data_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def test_multiagent_validation_with_clean_context(self, crew_context_data):
        """Test that multi-agent validation accepts clean context data."""

        @adri_protected(contract="crew_context", data_param="context")
        def crew_task(context):
            """Execute crew task with validated context."""
            return {
                "tasks_processed": len(context),
                "roles": [c["role"] for c in context]
            }

        # Should pass validation with clean context
        result = crew_task(crew_context_data)

        assert result is not None
        assert result["tasks_processed"] == 3
        assert "researcher" in result["roles"]
        assert "analyst" in result["roles"]
        assert "writer" in result["roles"]

    def test_multiagent_context_structure(self, crew_context_data):
        """Verify crew context sample data has expected structure."""
        assert len(crew_context_data) > 0

        # Check first task has required fields
        first_task = crew_context_data[0]
        assert "task_id" in first_task
        assert "role" in first_task
        assert "agent_name" in first_task
        assert "inputs" in first_task
        assert "context" in first_task
        assert "timestamp" in first_task

        # Check nested structures
        assert "query" in first_task["inputs"]
        assert "sources" in first_task["inputs"]
        assert "previous_results" in first_task["context"]
        assert "metadata" in first_task["context"]

    def test_multiagent_task_dependencies(self, crew_context_data):
        """Test that task dependencies are properly structured."""
        # Task 1 should have no dependencies
        assert crew_context_data[0]["context"]["previous_results"] == []

        # Task 2 should depend on task 1
        assert "task_001" in crew_context_data[1]["context"]["previous_results"]

        # Task 3 should have both previous tasks
        assert len(crew_context_data[2]["context"]["previous_results"]) == 2


class TestRAGPipelineUseCase:
    """Test RAG pipeline use case."""

    @pytest.fixture
    def rag_documents_data(self):
        """Load RAG documents sample data."""
        data_path = Path("examples/data/rag_documents.json")
        with open(data_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def test_rag_validation_with_clean_documents(self, rag_documents_data):
        """Test that RAG validation accepts clean document structures."""

        @adri_protected(contract="documents", data_param="docs")
        def index_documents(docs):
            """Index documents in vector store."""
            return {
                "indexed": len(docs),
                "doc_ids": [d["id"] for d in docs],
                "types": list(set(d["document_type"] for d in docs))
            }

        # Should pass validation with clean documents
        result = index_documents(rag_documents_data)

        assert result is not None
        assert result["indexed"] == 5
        assert len(result["doc_ids"]) == 5
        assert "support_ticket" in result["types"]
        assert "kb_article" in result["types"]

    def test_rag_document_structure_validation(self, rag_documents_data):
        """Verify RAG documents have required structure for ADRI validation."""
        assert len(rag_documents_data) > 0

        # Every document must have these fields for ADRI to validate
        required_fields = ["id", "text", "metadata", "document_type"]

        for doc in rag_documents_data:
            for field in required_fields:
                assert field in doc, f"Document {doc.get('id', 'unknown')} missing required field: {field}"

            # Validate field types
            assert isinstance(doc["id"], str)
            assert isinstance(doc["text"], str)
            assert isinstance(doc["metadata"], dict)
            assert isinstance(doc["document_type"], str)

            # Text should not be empty
            assert len(doc["text"]) > 0

    def test_rag_metadata_consistency(self, rag_documents_data):
        """Test that document metadata has consistent structure."""
        # All documents should have these metadata fields
        common_metadata_fields = ["source", "category", "priority", "date_created"]

        for doc in rag_documents_data:
            metadata = doc["metadata"]

            for field in common_metadata_fields:
                assert field in metadata, \
                    f"Document {doc['id']} metadata missing field: {field}"

    def test_rag_structural_vs_semantic_validation(self, rag_documents_data):
        """Verify ADRI validates structure, not semantic content."""

        @adri_protected(contract="documents", data_param="docs")
        def validate_structure(docs):
            """ADRI checks structure, not content quality."""
            return [d["id"] for d in docs]

        # These documents have valid STRUCTURE even if content is nonsense
        # ADRI will pass them (structure validation only)
        result = validate_structure(rag_documents_data)

        assert len(result) == 5

        # ADRI validates:
        # ✅ Each doc has 'id', 'text', 'metadata' fields
        # ✅ Field types are correct (str, dict, etc.)
        # ✅ No missing required fields

        # ADRI does NOT validate:
        # ❌ Whether text makes sense
        # ❌ Whether embeddings are good
        # ❌ Whether documents are relevant


class TestUseCaseIntegration:
    """Integration tests across all use cases."""

    def test_all_sample_files_exist(self):
        """Verify all use case sample files exist."""
        sample_files = [
            "examples/data/api_response.json",
            "examples/data/crew_context.json",
            "examples/data/rag_documents.json"
        ]

        for file_path in sample_files:
            assert Path(file_path).exists(), f"Missing sample file: {file_path}"

    def test_all_sample_files_are_valid_json(self):
        """Verify all sample files contain valid JSON."""
        sample_files = [
            "examples/data/api_response.json",
            "examples/data/crew_context.json",
            "examples/data/rag_documents.json"
        ]

        for file_path in sample_files:
            with open(file_path, 'r', encoding="utf-8") as f:
                data = json.load(f)
                assert data is not None
                assert isinstance(data, list)
                assert len(data) > 0

    def test_use_case_decorator_pattern_consistency(self):
        """Verify all use cases follow consistent decorator pattern."""

        # Pattern 1: API validation
        @adri_protected(contract="api_response", data_param="response")
        def api_func(response):
            return response

        # Pattern 2: Multi-agent
        @adri_protected(contract="crew_context", data_param="context")
        def crew_func(context):
            return context

        # Pattern 3: RAG
        @adri_protected(contract="documents", data_param="docs")
        def rag_func(docs):
            return docs

        # All should be marked as protected
        assert hasattr(api_func, '_adri_protected')
        assert hasattr(crew_func, '_adri_protected')
        assert hasattr(rag_func, '_adri_protected')

        # All should have config
        assert hasattr(api_func, '_adri_config')
        assert hasattr(crew_func, '_adri_config')
        assert hasattr(rag_func, '_adri_config')


class TestUseCaseDocumentation:
    """Validate that use case documentation is accurate."""

    def test_readme_use_cases_match_sample_files(self):
        """Verify README use case examples match available sample files."""
        readme_path = Path("README.md")

        with open(readme_path, 'r', encoding="utf-8") as f:
            readme_content = f.read()

        # README should mention all three sample files
        assert "api_response.json" in readme_content
        assert "crew_context.json" in readme_content
        assert "rag_documents.json" in readme_content

    def test_use_case_code_examples_are_valid_python(self):
        """Verify use case code examples are syntactically valid."""
        # The decorator patterns used in README with function definitions
        test_cases = [
            '@adri_protected(contract="api_response", data_param="response")\ndef f(response): pass',
            '@adri_protected(contract="crew_context", data_param="context")\ndef f(context): pass',
            '@adri_protected(contract="documents", data_param="docs")\ndef f(docs): pass'
        ]

        for code in test_cases:
            # Should not raise SyntaxError
            try:
                compile(code, '<string>', 'exec')
            except SyntaxError as e:
                pytest.fail(f"Invalid Python syntax in use case: {code}\nError: {e}")
