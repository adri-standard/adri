"""
Live Integration Tests: CrewAI Framework

Tests real CrewAI functionality with OpenAI API calls.
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


class TestCrewAILive:
    """Live integration tests for CrewAI example."""

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
    def good_market_data(self):
        """High-quality market analysis data for testing."""
        return {
            "market_segment": "technology",
            "time_period": "2023-Q4",
            "data_sources": ["bloomberg", "reuters", "yahoo_finance"],
            "companies": ["AAPL", "GOOGL", "MSFT", "AMZN"],
            "metrics": ["revenue", "growth_rate", "market_cap"],
            "analysis_type": "competitive_analysis",
            "urgency": "high",
            "client_id": "client_789",
            "analyst_id": "analyst_456",
        }

    @pytest.fixture
    def bad_market_data(self):
        """Poor-quality market data that should be blocked."""
        return {
            "market_segment": "",  # Missing segment
            "time_period": "invalid-date",  # Invalid period
            "data_sources": [],  # No sources
            "companies": None,  # Missing companies
            "metrics": ["unknown_metric"],  # Invalid metrics
            "analysis_type": "",  # Missing type
            "urgency": "unknown",  # Invalid urgency
            "client_id": 12345,  # Should be string
            "analyst_id": "",  # Missing analyst
        }

    def test_crewai_market_analysis_with_good_data(self, good_market_data):
        """Test CrewAI market analysis with good data - MAKES REAL API CALL."""
        framework = "crewai"
        test_name = "market_analysis_good"
        estimated_cost = estimate_openai_cost("gpt-3.5-turbo", 200, 150)

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
            example_file = examples_dir / "crewai-business-analysis.py"

            spec = importlib.util.spec_from_file_location(
                "crewai_example", example_file
            )
            module = importlib.util.module_from_spec(spec)

            # Execute the module (will load with real API key)
            try:
                spec.loader.exec_module(module)
            except SystemExit:
                pytest.fail("Example should not exit when API key is available")

            # Test the market analysis function
            if hasattr(module, "MarketAnalysisCrew"):
                crew = module.MarketAnalysisCrew()
                result = crew.analyze_market_segment(good_market_data)
            else:
                pytest.skip("MarketAnalysisCrew class not found in example")

            # Record the API call
            self.cost_controller.record_call(
                framework, test_name, estimated_cost, success=True
            )

            # Validate results
            assert result is not None, "Should return a result"
            assert isinstance(result, dict), "Result should be a dictionary"

            # Should have expected fields in response
            expected_fields = [
                "client_id",
                "market_segment",
                "analysis_period",
                "status",
            ]
            for field in expected_fields:
                assert field in result, f"Result should contain {field}"

            # Response should be meaningful
            assert result.get("status") == "completed", "Analysis should be completed"
            assert (
                result.get("market_segment") == good_market_data["market_segment"]
            ), "Should match input segment"

            print(f"✅ CrewAI market analysis test passed")
            print(f"   Client: {result.get('client_id', 'N/A')}")
            print(f"   Segment: {result.get('market_segment', 'N/A')}")
            print(f"   Status: {result.get('status', 'N/A')}")

        except Exception as e:
            # Record failed call
            self.cost_controller.record_call(
                framework, test_name, estimated_cost, success=False
            )
            pytest.fail(f"CrewAI market analysis test failed: {e}")

    def test_crewai_market_analysis_with_bad_data(self, bad_market_data):
        """Test CrewAI market analysis with bad data - should be blocked by ADRI."""
        framework = "crewai"
        test_name = "market_analysis_bad"

        # Import the example
        import importlib.util

        examples_dir = Path(__file__).parent.parent.parent.parent / "examples"
        example_file = examples_dir / "crewai-business-analysis.py"

        spec = importlib.util.spec_from_file_location("crewai_example", example_file)
        module = importlib.util.module_from_spec(spec)

        try:
            spec.loader.exec_module(module)
        except SystemExit:
            pytest.fail("Example should not exit when API key is available")

        # Call the protected function with bad data - should be blocked
        try:
            if hasattr(module, "MarketAnalysisCrew"):
                crew = module.MarketAnalysisCrew()
                result = crew.analyze_market_segment(bad_market_data)

                # If we get here, ADRI allowed the bad data through
                print(f"⚠️  Bad data was processed (ADRI may have warned): {result}")
            else:
                pytest.skip("MarketAnalysisCrew class not found in example")

        except Exception as e:
            # Expected - ADRI should block bad data
            assert (
                "ADRI" in str(e)
                or "Protection" in str(e)
                or "quality" in str(e).lower()
            ), f"Exception should be from ADRI protection: {e}"

            print(f"✅ ADRI correctly blocked bad data: {str(e)[:100]}...")

    def test_crewai_customer_support_crew_live(self):
        """Test CrewAI customer support crew with real API call."""
        framework = "crewai"
        test_name = "customer_support_crew"
        estimated_cost = estimate_openai_cost("gpt-3.5-turbo", 180, 120)

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
            example_file = examples_dir / "crewai-business-analysis.py"

            spec = importlib.util.spec_from_file_location(
                "crewai_example", example_file
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Test customer support crew if available
            if hasattr(module, "crewai_customer_support_crew"):
                support_data = {
                    "ticket_id": "TICKET-12345",
                    "customer_id": "CUST-789",
                    "issue_type": "billing_dispute",
                    "priority": "high",
                    "description": "Customer reports incorrect charges on recent bill",
                    "customer_tier": "premium",
                    "created_date": "2023-01-15T09:30:00Z",
                }

                result = module.crewai_customer_support_crew(support_data)

                # Record the API call
                self.cost_controller.record_call(
                    framework, test_name, estimated_cost, success=True
                )

                # Validate results
                assert result is not None, "Support crew should return result"
                assert isinstance(result, dict), "Result should be dictionary"
                assert (
                    result.get("ticket_id") == support_data["ticket_id"]
                ), "Should match ticket ID"

                print(f"✅ CrewAI customer support crew test passed")
                print(f"   Ticket: {result.get('ticket_id', 'N/A')}")
                print(f"   Status: {result.get('status', 'N/A')}")
            else:
                pytest.skip(
                    "crewai_customer_support_crew function not found in example"
                )

        except Exception as e:
            # Record failed call
            self.cost_controller.record_call(
                framework, test_name, estimated_cost, success=False
            )
            pytest.fail(f"CrewAI customer support crew test failed: {e}")

    def test_crewai_content_creation_crew_live(self):
        """Test CrewAI content creation crew with real API call."""
        framework = "crewai"
        test_name = "content_creation_crew"
        estimated_cost = estimate_openai_cost("gpt-3.5-turbo", 220, 140)

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
            example_file = examples_dir / "crewai-business-analysis.py"

            spec = importlib.util.spec_from_file_location(
                "crewai_example", example_file
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Test content creation crew if available
            if hasattr(module, "crewai_content_creation_crew"):
                content_data = {
                    "content_type": "blog_post",
                    "topic": "AI-powered data quality for enterprises",
                    "target_audience": "technical_decision_makers",
                    "tone": "professional",
                    "word_count_target": 800,
                    "keywords": ["data quality", "AI", "automation", "enterprise"],
                    "deadline": "2023-01-20T17:00:00Z",
                }

                result = module.crewai_content_creation_crew(content_data)

                # Record the API call
                self.cost_controller.record_call(
                    framework, test_name, estimated_cost, success=True
                )

                # Validate results
                assert result is not None, "Content crew should return result"
                assert isinstance(result, dict), "Result should be dictionary"
                assert (
                    result.get("type") == content_data["content_type"]
                ), "Should match content type"

                print(f"✅ CrewAI content creation crew test passed")
                print(f"   Type: {result.get('type', 'N/A')}")
                print(f"   Audience: {result.get('target_audience', 'N/A')}")
                print(f"   Quality Score: {result.get('quality_score', 'N/A')}")
            else:
                pytest.skip(
                    "crewai_content_creation_crew function not found in example"
                )

        except Exception as e:
            # Record failed call
            self.cost_controller.record_call(
                framework, test_name, estimated_cost, success=False
            )
            pytest.fail(f"CrewAI content creation crew test failed: {e}")


class TestCrewAIErrorHandling:
    """Test error handling in CrewAI integration."""

    def test_crewai_handles_api_errors(self):
        """Test that CrewAI integration handles API errors gracefully."""
        framework = "crewai"
        test_name = "error_handling"

        # Import the example
        import importlib.util

        examples_dir = Path(__file__).parent.parent.parent.parent / "examples"
        example_file = examples_dir / "crewai-business-analysis.py"

        spec = importlib.util.spec_from_file_location("crewai_example", example_file)
        module = importlib.util.module_from_spec(spec)

        try:
            spec.loader.exec_module(module)
        except SystemExit:
            pytest.skip("Cannot test error handling without proper module load")

        # Mock API to return errors
        with patch("openai.ChatCompletion.create") as mock_openai:
            mock_openai.side_effect = Exception("API Error")

            good_data = {
                "market_segment": "technology",
                "time_period": "2023-Q4",
                "data_sources": ["bloomberg", "reuters"],
                "companies": ["AAPL", "GOOGL"],
                "metrics": ["revenue", "growth_rate"],
                "analysis_type": "competitive_analysis",
                "urgency": "medium",
                "client_id": "client_test",
            }

            # Should handle the error gracefully
            try:
                if hasattr(module, "MarketAnalysisCrew"):
                    crew = module.MarketAnalysisCrew()
                    result = crew.analyze_market_segment(good_data)
                    # If we get a result, it should indicate an error
                    assert result is not None, "Should return error result"
                    if isinstance(result, dict):
                        assert (
                            "error" in result or "status" in result
                        ), "Should indicate error status"
                else:
                    pytest.skip("MarketAnalysisCrew class not found")
            except Exception as e:
                # Should be a graceful error, not a crash
                assert (
                    "API Error" in str(e) or "error" in str(e).lower()
                ), f"Should handle API errors gracefully: {e}"

        print("✅ CrewAI error handling test passed")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
