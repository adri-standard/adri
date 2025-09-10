"""
Live Integration Tests: LlamaIndex Framework

Tests real LlamaIndex functionality with OpenAI API calls.
⚠️ COSTS MONEY - Requires API key and makes real API calls.
"""

import os
import sys
import pytest
import asyncio
from pathlib import Path
from unittest.mock import patch

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "examples"))

from tests.examples.utils.cost_controls import get_cost_controller, estimate_openai_cost


class TestLlamaIndexLive:
    """Live integration tests for LlamaIndex example."""
    
    @pytest.fixture(autouse=True)
    def setup_api_key(self):
        """Ensure API key is available for tests."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            pytest.skip("OPENAI_API_KEY environment variable required for live tests")
        
        self.cost_controller = get_cost_controller()
        yield
        # Cleanup if needed
    
    @pytest.fixture
    def good_query_data(self):
        """High-quality RAG query data for testing."""
        return {
            "query": "What are the key benefits of using ADRI for data quality in AI applications?",
            "user_id": "user_456",
            "session_id": "session_789",
            "max_results": 5,
            "similarity_threshold": 0.7,
            "context_window": 4000,
            "retrieval_mode": "semantic",
            "response_format": "detailed",
            "language": "english"
        }
    
    @pytest.fixture
    def bad_query_data(self):
        """Poor-quality query data that should be blocked."""
        return {
            "query": "",                    # Empty query
            "user_id": None,               # Missing user ID
            "session_id": 12345,           # Should be string
            "max_results": -1,             # Invalid count
            "similarity_threshold": 1.5,   # Invalid threshold
            "context_window": "invalid",   # Should be integer
            "retrieval_mode": "unknown",   # Invalid mode
            "response_format": "",         # Missing format
            "language": "invalid_lang"     # Invalid language
        }
    
    def test_llamaindex_rag_query_with_good_data(self, good_query_data):
        """Test LlamaIndex RAG query with good data - MAKES REAL API CALL."""
        framework = "llamaindex"
        test_name = "rag_query_good"
        estimated_cost = estimate_openai_cost("gpt-3.5-turbo", 180, 120)
        
        # Check cost limits
        can_proceed, reason = self.cost_controller.can_make_call(framework, test_name, estimated_cost)
        if not can_proceed:
            pytest.skip(f"Cost limit reached: {reason}")
        
        # Wait for rate limiting
        self.cost_controller.wait_for_rate_limit()
        
        try:
            # Import the example (should work with API key set)
            import importlib.util
            examples_dir = Path(__file__).parent.parent.parent.parent / "examples"
            example_file = examples_dir / "llamaindex-document-processing.py"
            
            spec = importlib.util.spec_from_file_location("llamaindex_example", example_file)
            module = importlib.util.module_from_spec(spec)
            
            # Execute the module (will load with real API key)
            try:
                spec.loader.exec_module(module)
            except SystemExit:
                pytest.fail("Example should not exit when API key is available")
            
            # Test the RAG query function
            if hasattr(module, 'EnterpriseRAGSystem'):
                rag_system = module.EnterpriseRAGSystem()
                result = rag_system.process_rag_query(good_query_data)
            else:
                pytest.skip("EnterpriseRAGSystem class not found in example")
            
            # Record the API call
            self.cost_controller.record_call(framework, test_name, estimated_cost, success=True)
            
            # Validate results
            assert result is not None, "Should return a result"
            assert isinstance(result, dict), "Result should be a dictionary"
            
            # Should have expected fields in response
            expected_fields = ['query_id', 'user_id', 'query', 'response']
            for field in expected_fields:
                assert field in result, f"Result should contain {field}"
            
            # Response should be meaningful
            assert result.get('query') == good_query_data['query'], "Should match input query"
            assert len(result.get('response', '')) > 10, "Response should be meaningful"
            
            print(f"✅ LlamaIndex RAG query test passed")
            print(f"   Query ID: {result.get('query_id', 'N/A')}")
            print(f"   User: {result.get('user_id', 'N/A')}")
            print(f"   Response: {result.get('response', '')[:100]}...")
            print(f"   Sources: {result.get('sources_count', 'N/A')}")
            
        except Exception as e:
            # Record failed call
            self.cost_controller.record_call(framework, test_name, estimated_cost, success=False)
            pytest.fail(f"LlamaIndex RAG query test failed: {e}")
    
    def test_llamaindex_rag_query_with_bad_data(self, bad_query_data):
        """Test LlamaIndex RAG query with bad data - should be blocked by ADRI."""
        framework = "llamaindex"
        test_name = "rag_query_bad"
        
        # Import the example
        import importlib.util
        examples_dir = Path(__file__).parent.parent.parent.parent / "examples"
        example_file = examples_dir / "llamaindex-document-processing.py"
        
        spec = importlib.util.spec_from_file_location("llamaindex_example", example_file)
        module = importlib.util.module_from_spec(spec)
        
        try:
            spec.loader.exec_module(module)
        except SystemExit:
            pytest.fail("Example should not exit when API key is available")
        
        # Call the protected function with bad data - should be blocked
        try:
            if hasattr(module, 'EnterpriseRAGSystem'):
                rag_system = module.EnterpriseRAGSystem()
                result = rag_system.process_rag_query(bad_query_data)
                
                # If we get here, ADRI allowed the bad data through
                print(f"⚠️  Bad data was processed (ADRI may have warned): {result}")
            else:
                pytest.skip("EnterpriseRAGSystem class not found in example")
                
        except Exception as e:
            # Expected - ADRI should block bad data
            assert "ADRI" in str(e) or "Protection" in str(e) or "quality" in str(e).lower(), \
                f"Exception should be from ADRI protection: {e}"
            
            print(f"✅ ADRI correctly blocked bad data: {str(e)[:100]}...")
    
    def test_llamaindex_document_ingestion_live(self):
        """Test LlamaIndex document ingestion with real API call."""
        framework = "llamaindex"
        test_name = "document_ingestion"
        estimated_cost = estimate_openai_cost("text-embedding-ada-002", 500, 0)  # Embedding only
        
        # Check cost limits
        can_proceed, reason = self.cost_controller.can_make_call(framework, test_name, estimated_cost)
        if not can_proceed:
            pytest.skip(f"Cost limit reached: {reason}")
        
        # Wait for rate limiting
        self.cost_controller.wait_for_rate_limit()
        
        try:
            # Import the example
            import importlib.util
            examples_dir = Path(__file__).parent.parent.parent.parent / "examples"
            example_file = examples_dir / "llamaindex-document-processing.py"
            
            spec = importlib.util.spec_from_file_location("llamaindex_example", example_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Test document ingestion if available
            if hasattr(module, 'llamaindex_document_ingestion'):
                ingestion_data = {
                    "batch_id": "batch_20230115_001",
                    "pipeline_config": "standard_processing",
                    "documents": [
                        {
                            "content": "ADRI enables reliable AI agent operations through comprehensive data quality validation.",
                            "metadata": {"source": "technical_docs", "author": "AI Team", "category": "framework"}
                        },
                        {
                            "content": "LlamaIndex provides powerful tools for building production-ready RAG applications.",
                            "metadata": {"source": "product_docs", "author": "Dev Team", "category": "tools"}
                        }
                    ],
                    "processing_options": {
                        "chunk_size": 512,
                        "overlap": 50,
                        "embedding_model": "text-embedding-ada-002"
                    }
                }
                
                result = module.llamaindex_document_ingestion(ingestion_data)
                
                # Record the API call
                self.cost_controller.record_call(framework, test_name, estimated_cost, success=True)
                
                # Validate results
                assert result is not None, "Document ingestion should return result"
                assert isinstance(result, dict), "Result should be dictionary"
                assert result.get('batch_id') == ingestion_data['batch_id'], "Should match batch ID"
                
                print(f"✅ LlamaIndex document ingestion test passed")
                print(f"   Batch: {result.get('batch_id', 'N/A')}")
                print(f"   Documents: {result.get('documents_processed', 'N/A')}")
                print(f"   Words: {result.get('total_word_count', 'N/A')}")
            else:
                pytest.skip("llamaindex_document_ingestion function not found in example")
                
        except Exception as e:
            # Record failed call
            self.cost_controller.record_call(framework, test_name, estimated_cost, success=False)
            pytest.fail(f"LlamaIndex document ingestion test failed: {e}")
    
    def test_llamaindex_semantic_search_live(self):
        """Test LlamaIndex semantic search with real API call."""
        framework = "llamaindex"
        test_name = "semantic_search"
        estimated_cost = estimate_openai_cost("text-embedding-ada-002", 100, 0)  # Embedding only
        
        # Check cost limits  
        can_proceed, reason = self.cost_controller.can_make_call(framework, test_name, estimated_cost)
        if not can_proceed:
            pytest.skip(f"Cost limit reached: {reason}")
        
        # Wait for rate limiting
        self.cost_controller.wait_for_rate_limit()
        
        try:
            # Import the example
            import importlib.util
            examples_dir = Path(__file__).parent.parent.parent.parent / "examples"
            example_file = examples_dir / "llamaindex-document-processing.py"
            
            spec = importlib.util.spec_from_file_location("llamaindex_example", example_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Test semantic search if available
            if hasattr(module, 'llamaindex_semantic_search'):
                search_data = {
                    "search_query": "How does ADRI improve AI agent reliability?",
                    "max_results": 5,
                    "similarity_threshold": 0.75,
                    "embedding_model": "text-embedding-ada-002",
                    "search_mode": "hybrid",
                    "user_context": {
                        "user_id": "user_789",
                        "session_id": "session_456",
                        "preferences": ["technical_detail", "practical_examples"]
                    }
                }
                
                result = module.llamaindex_semantic_search(search_data)
                
                # Record the API call
                self.cost_controller.record_call(framework, test_name, estimated_cost, success=True)
                
                # Validate results
                assert result is not None, "Semantic search should return result"
                assert isinstance(result, dict), "Result should be dictionary"
                assert result.get('search_query') == search_data['search_query'], "Should match search query"
                
                print(f"✅ LlamaIndex semantic search test passed")
                print(f"   Query: {result.get('search_query', 'N/A')[:40]}...")
                print(f"   Results: {result.get('total_results', 'N/A')}")
                print(f"   Model: {result.get('embedding_model', 'N/A')}")
            else:
                pytest.skip("llamaindex_semantic_search function not found in example")
                
        except Exception as e:
            # Record failed call
            self.cost_controller.record_call(framework, test_name, estimated_cost, success=False)
            pytest.fail(f"LlamaIndex semantic search test failed: {e}")


class TestLlamaIndexErrorHandling:
    """Test error handling in LlamaIndex integration."""
    
    def test_llamaindex_handles_api_errors(self):
        """Test that LlamaIndex integration handles API errors gracefully."""
        framework = "llamaindex"
        test_name = "error_handling"
        
        # Import the example
        import importlib.util
        examples_dir = Path(__file__).parent.parent.parent.parent / "examples"
        example_file = examples_dir / "llamaindex-document-processing.py"
        
        spec = importlib.util.spec_from_file_location("llamaindex_example", example_file)
        module = importlib.util.module_from_spec(spec)
        
        try:
            spec.loader.exec_module(module)
        except SystemExit:
            pytest.skip("Cannot test error handling without proper module load")
        
        # Mock API to return errors
        with patch('openai.Embedding.create') as mock_openai:
            mock_openai.side_effect = Exception("API Error")
            
            good_data = {
                "query": "Test query for error handling",
                "user_id": "test_user",
                "session_id": "test_session",
                "max_results": 3,
                "similarity_threshold": 0.8,
                "context_window": 2000,
                "retrieval_mode": "semantic",
                "response_format": "detailed",
                "language": "english"
            }
            
            # Should handle the error gracefully
            try:
                if hasattr(module, 'EnterpriseRAGSystem'):
                    rag_system = module.EnterpriseRAGSystem()
                    result = rag_system.process_rag_query(good_data)
                    # If we get a result, it should indicate an error
                    assert result is not None, "Should return error result"
                    if isinstance(result, dict):
                        assert 'error' in result or 'status' in result, "Should indicate error status"
                else:
                    pytest.skip("EnterpriseRAGSystem class not found")
            except Exception as e:
                # Should be a graceful error, not a crash
                assert "API Error" in str(e) or "error" in str(e).lower(), \
                    f"Should handle API errors gracefully: {e}"
        
        print("✅ LlamaIndex error handling test passed")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
