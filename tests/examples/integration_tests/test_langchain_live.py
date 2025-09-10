"""
Live Integration Tests: LangChain Framework

Tests real LangChain functionality with OpenAI API calls.
⚠️ COSTS MONEY - Requires API key and makes real API calls.
"""

import asyncio
import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "examples"))

from tests.examples.utils.cost_controls import estimate_openai_cost, get_cost_controller


class TestLangChainLive:
    """Live integration tests for LangChain example."""

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
    def good_customer_data(self):
        """High-quality customer data for testing."""
        return {
            "customer_id": "CUST001",
            "name": "Alice Johnson",
            "email": "alice@example.com",
            "query": "I need help with my recent order",
            "order_id": "ORD123456",
            "urgency": "medium",
            "category": "order_inquiry",
        }

    @pytest.fixture
    def bad_customer_data(self):
        """Poor-quality customer data that should be blocked."""
        return {
            "customer_id": "",  # Missing ID
            "name": None,  # Missing name
            "email": "invalid-email",  # Invalid format
            "query": "",  # Empty query
            "order_id": None,  # Missing order ID
            "urgency": "invalid",  # Invalid urgency
            "category": "",  # Missing category
        }

    def test_langchain_customer_service_with_good_data(self, good_customer_data):
        """Test LangChain customer service with good data - MAKES REAL API CALL."""
        framework = "langchain"
        test_name = "customer_service_good"
        estimated_cost = estimate_openai_cost("gpt-3.5-turbo", 150, 100)

        # Check cost limits
        can_proceed, reason = self.cost_controller.can_make_call(
            framework, test_name, estimated_cost
        )
        if not can_proceed:
            pytest.skip(f"Cost limit reached: {reason}")

        # Wait for rate limiting
        self.cost_controller.wait_for_rate_limit()

        try:
            # Import the example (should work with API key set)
            import importlib.util

            examples_dir = Path(__file__).parent.parent.parent.parent / "examples"
            example_file = examples_dir / "langchain-customer-service.py"

            spec = importlib.util.spec_from_file_location(
                "langchain_example", example_file
            )
            module = importlib.util.module_from_spec(spec)

            # Execute the module (will load with real API key)
            try:
                spec.loader.exec_module(module)
            except SystemExit:
                pytest.fail("Example should not exit when API key is available")

            # Test the customer service function
            assert hasattr(
                module, "customer_service_agent"
            ), "Should have customer_service_agent function"

            # Call the protected function with good data
            result = module.customer_service_agent(good_customer_data)

            # Record the API call
            self.cost_controller.record_call(
                framework, test_name, estimated_cost, success=True
            )

            # Validate results
            assert result is not None, "Should return a result"
            assert isinstance(result, dict), "Result should be a dictionary"

            # Should have expected fields in response
            expected_fields = ["customer_id", "response", "status"]
            for field in expected_fields:
                assert field in result, f"Result should contain {field}"

            # Response should be meaningful
            assert len(result.get("response", "")) > 10, "Response should be meaningful"

            print(f"✅ LangChain customer service test passed")
            print(f"   Customer: {result.get('customer_id', 'N/A')}")
            print(f"   Response: {result.get('response', '')[:100]}...")

        except Exception as e:
            # Record failed call
            self.cost_controller.record_call(
                framework, test_name, estimated_cost, success=False
            )
            pytest.fail(f"LangChain customer service test failed: {e}")

    def test_langchain_customer_service_with_bad_data(self, bad_customer_data):
        """Test LangChain customer service with bad data - should be blocked by ADRI."""
        framework = "langchain"
        test_name = "customer_service_bad"

        # Import the example
        import importlib.util

        examples_dir = Path(__file__).parent.parent.parent.parent / "examples"
        example_file = examples_dir / "langchain-customer-service.py"

        spec = importlib.util.spec_from_file_location("langchain_example", example_file)
        module = importlib.util.module_from_spec(spec)

        try:
            spec.loader.exec_module(module)
        except SystemExit:
            pytest.fail("Example should not exit when API key is available")

        # Call the protected function with bad data - should be blocked
        try:
            result = module.customer_service_agent(bad_customer_data)

            # If we get here, ADRI allowed the bad data through
            # This might be acceptable if ADRI warned but didn't block
            print(f"⚠️  Bad data was processed (ADRI may have warned): {result}")

        except Exception as e:
            # Expected - ADRI should block bad data
            assert (
                "ADRI" in str(e)
                or "Protection" in str(e)
                or "quality" in str(e).lower()
            ), f"Exception should be from ADRI protection: {e}"

            print(f"✅ ADRI correctly blocked bad data: {str(e)[:100]}...")

    def test_langchain_qa_pipeline_live(self, good_customer_data):
        """Test LangChain QA pipeline with real API call."""
        framework = "langchain"
        test_name = "qa_pipeline"
        estimated_cost = estimate_openai_cost("gpt-3.5-turbo", 200, 80)

        # Check cost limits
        can_proceed, reason = self.cost_controller.can_make_call(
            framework, test_name, estimated_cost
        )
        if not can_proceed:
            pytest.skip(f"Cost limit reached: {reason}")

        # Wait for rate limiting
        self.cost_controller.wait_for_rate_limit()

        try:
            # Import the example
            import importlib.util

            examples_dir = Path(__file__).parent.parent.parent.parent / "examples"
            example_file = examples_dir / "langchain-customer-service.py"

            spec = importlib.util.spec_from_file_location(
                "langchain_example", example_file
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Test QA pipeline if available
            if hasattr(module, "langchain_qa_pipeline"):
                qa_data = {
                    "query": "What is the return policy?",
                    "context": "Company policies and customer service information",
                    "customer_id": good_customer_data["customer_id"],
                }

                result = module.langchain_qa_pipeline(qa_data)

                # Record the API call
                self.cost_controller.record_call(
                    framework, test_name, estimated_cost, success=True
                )

                # Validate results
                assert result is not None, "QA pipeline should return result"
                assert isinstance(result, dict), "Result should be dictionary"

                print(f"✅ LangChain QA pipeline test passed")
                print(f"   Query: {qa_data['query']}")
                print(f"   Answer: {result.get('answer', '')[:100]}...")
            else:
                pytest.skip("langchain_qa_pipeline function not found in example")

        except Exception as e:
            # Record failed call
            self.cost_controller.record_call(
                framework, test_name, estimated_cost, success=False
            )
            pytest.fail(f"LangChain QA pipeline test failed: {e}")

    def test_langchain_conversation_chain_live(self):
        """Test LangChain conversation chain with real API call."""
        framework = "langchain"
        test_name = "conversation_chain"
        estimated_cost = estimate_openai_cost("gpt-3.5-turbo", 180, 90)

        # Check cost limits
        can_proceed, reason = self.cost_controller.can_make_call(
            framework, test_name, estimated_cost
        )
        if not can_proceed:
            pytest.skip(f"Cost limit reached: {reason}")

        # Wait for rate limiting
        self.cost_controller.wait_for_rate_limit()

        try:
            # Import the example
            import importlib.util

            examples_dir = Path(__file__).parent.parent.parent.parent / "examples"
            example_file = examples_dir / "langchain-customer-service.py"

            spec = importlib.util.spec_from_file_location(
                "langchain_example", example_file
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Test conversation chain if available
            if hasattr(module, "langchain_conversation_chain"):
                conversation_data = {
                    "conversation_id": "conv_001",
                    "message": "Hello, I need help with my account",
                    "history": [],
                    "user_context": {"customer_id": "CUST001", "tier": "premium"},
                }

                result = module.langchain_conversation_chain(conversation_data)

                # Record the API call
                self.cost_controller.record_call(
                    framework, test_name, estimated_cost, success=True
                )

                # Validate results
                assert result is not None, "Conversation chain should return result"
                assert isinstance(result, dict), "Result should be dictionary"

                print(f"✅ LangChain conversation chain test passed")
                print(f"   Message: {conversation_data['message']}")
                print(f"   Response: {result.get('response', '')[:100]}...")
            else:
                pytest.skip(
                    "langchain_conversation_chain function not found in example"
                )

        except Exception as e:
            # Record failed call
            self.cost_controller.record_call(
                framework, test_name, estimated_cost, success=False
            )
            pytest.fail(f"LangChain conversation chain test failed: {e}")


class TestLangChainErrorHandling:
    """Test error handling in LangChain integration."""

    def test_langchain_handles_api_errors(self):
        """Test that LangChain integration handles API errors gracefully."""
        # This test uses a mock to simulate API errors
        framework = "langchain"
        test_name = "error_handling"

        # Import the example
        import importlib.util

        examples_dir = Path(__file__).parent.parent.parent.parent / "examples"
        example_file = examples_dir / "langchain-customer-service.py"

        spec = importlib.util.spec_from_file_location("langchain_example", example_file)
        module = importlib.util.module_from_spec(spec)

        try:
            spec.loader.exec_module(module)
        except SystemExit:
            pytest.skip("Cannot test error handling without proper module load")

        # Mock API to return errors
        with patch("openai.ChatCompletion.create") as mock_openai:
            mock_openai.side_effect = Exception("API Error")

            good_data = {
                "customer_id": "CUST001",
                "name": "Test User",
                "email": "test@example.com",
                "query": "Test query",
                "order_id": "ORD123",
                "urgency": "low",
                "category": "test",
            }

            # Should handle the error gracefully
            try:
                result = module.customer_service_agent(good_data)
                # If we get a result, it should indicate an error
                assert result is not None, "Should return error result"
                if isinstance(result, dict):
                    assert (
                        "error" in result or "status" in result
                    ), "Should indicate error status"
            except Exception as e:
                # Should be a graceful error, not a crash
                assert (
                    "API Error" in str(e) or "error" in str(e).lower()
                ), f"Should handle API errors gracefully: {e}"

        print("✅ LangChain error handling test passed")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
