"""
Test-Driven Development for ADRI Framework Examples

This module tests all framework-specific examples to ensure they:
1. Import correctly
2. Have the @adri_protected decorator
3. Handle good data properly
4. Handle bad data properly
5. Follow the expected patterns
"""

import importlib.util
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pandas as pd
import pytest

# Add examples directory to path
examples_dir = Path(__file__).parent.parent / "examples"
sys.path.insert(0, str(examples_dir))


@pytest.mark.slow
class TestFrameworkExamples:
    """Test framework-specific examples."""

    @pytest.fixture
    def good_customer_data(self):
        """High-quality customer data for testing."""
        return pd.DataFrame(
            {
                "customer_id": ["CUST001", "CUST002", "CUST003"],
                "name": ["Alice Johnson", "Bob Smith", "Charlie Brown"],
                "email": [
                    "alice@example.com",
                    "bob@example.com",
                    "charlie@example.com",
                ],
                "age": [28, 34, 45],
                "account_balance": [1250.50, 3400.75, 890.25],
            }
        )

    @pytest.fixture
    def bad_customer_data(self):
        """Poor-quality customer data for testing."""
        return pd.DataFrame(
            {
                "customer_id": [None, None, ""],
                "name": ["", None, ""],
                "email": ["invalid-email", "", "not-an-email"],
                "age": [-5, None, 200],
                "account_balance": [None, "invalid", None],
            }
        )


class TestLangChainExamples(TestFrameworkExamples):
    """Test LangChain framework examples."""

    def test_langchain_basic_example_exists(self):
        """Test that langchain_basic.py exists and can be imported."""
        example_file = examples_dir / "langchain_basic.py"
        assert example_file.exists(), "langchain_basic.py should exist"

        # Test import
        spec = importlib.util.spec_from_file_location("langchain_basic", example_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Should have a protected function
        assert hasattr(
            module, "customer_service_agent"
        ), "Should have customer_service_agent function"
        assert hasattr(
            module.customer_service_agent, "__wrapped__"
        ), "Function should be decorated"

    def test_langchain_basic_with_good_data(self, good_customer_data):
        """Test LangChain basic example with good data."""
        # Import the example
        example_file = examples_dir / "langchain_basic.py"
        spec = importlib.util.spec_from_file_location("langchain_basic", example_file)
        module = importlib.util.module_from_spec(spec)

        # Mock LangChain dependencies
        with patch.dict(
            "sys.modules",
            {
                "langchain": Mock(),
                "langchain.llms": Mock(),
                "langchain.prompts": Mock(),
                "langchain.chains": Mock(),
            },
        ):
            spec.loader.exec_module(module)

            # Should execute without error
            result = module.customer_service_agent(good_customer_data)
            assert result is not None

    def test_langchain_basic_with_bad_data(self, bad_customer_data):
        """Test LangChain basic example with bad data (should handle gracefully)."""
        example_file = examples_dir / "langchain_basic.py"
        spec = importlib.util.spec_from_file_location("langchain_basic", example_file)
        module = importlib.util.module_from_spec(spec)

        with patch.dict(
            "sys.modules",
            {
                "langchain": Mock(),
                "langchain.llms": Mock(),
                "langchain.prompts": Mock(),
                "langchain.chains": Mock(),
            },
        ):
            spec.loader.exec_module(module)

            # ADRI should handle bad data gracefully (either block or warn)
            # The important thing is that the decorator is working
            try:
                result = module.customer_service_agent(bad_customer_data)
                # If we get here, ADRI allowed the function to run (maybe with warnings)
                assert result is not None
            except Exception as e:
                # ADRI blocked the function due to poor data quality - this is expected
                assert "ADRI Protection: BLOCKED" in str(e) or "ProtectionError" in str(
                    type(e).__name__
                )
                # Test passes - ADRI is working correctly by blocking bad data


class TestCrewAIExamples(TestFrameworkExamples):
    """Test CrewAI framework examples."""

    def test_crewai_basic_example_exists(self):
        """Test that crewai_basic.py exists and can be imported."""
        example_file = examples_dir / "crewai_basic.py"
        assert example_file.exists(), "crewai_basic.py should exist"

        spec = importlib.util.spec_from_file_location("crewai_basic", example_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        assert hasattr(
            module, "market_analysis_crew"
        ), "Should have market_analysis_crew function"
        assert hasattr(
            module.market_analysis_crew, "__wrapped__"
        ), "Function should be decorated"

    def test_crewai_basic_with_good_data(self, good_customer_data):
        """Test CrewAI basic example with good data."""
        example_file = examples_dir / "crewai_basic.py"
        spec = importlib.util.spec_from_file_location("crewai_basic", example_file)
        module = importlib.util.module_from_spec(spec)

        with patch.dict(
            "sys.modules",
            {
                "crewai": Mock(),
            },
        ):
            spec.loader.exec_module(module)
            result = module.market_analysis_crew(good_customer_data)
            assert result is not None


class TestAutoGenExamples(TestFrameworkExamples):
    """Test AutoGen framework examples."""

    def test_autogen_basic_example_exists(self):
        """Test that autogen_basic.py exists and can be imported."""
        example_file = examples_dir / "autogen_basic.py"
        assert example_file.exists(), "autogen_basic.py should exist"

        spec = importlib.util.spec_from_file_location("autogen_basic", example_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        assert hasattr(
            module, "multi_agent_conversation"
        ), "Should have multi_agent_conversation function"
        assert hasattr(
            module.multi_agent_conversation, "__wrapped__"
        ), "Function should be decorated"


class TestLlamaIndexExamples(TestFrameworkExamples):
    """Test LlamaIndex framework examples."""

    def test_llamaindex_basic_example_exists(self):
        """Test that llamaindex_basic.py exists and can be imported."""
        example_file = examples_dir / "llamaindex_basic.py"
        assert example_file.exists(), "llamaindex_basic.py should exist"

        spec = importlib.util.spec_from_file_location("llamaindex_basic", example_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        assert hasattr(
            module, "rag_query_engine"
        ), "Should have rag_query_engine function"
        assert hasattr(
            module.rag_query_engine, "__wrapped__"
        ), "Function should be decorated"


class TestHaystackExamples(TestFrameworkExamples):
    """Test Haystack framework examples."""

    def test_haystack_basic_example_exists(self):
        """Test that haystack_basic.py exists and can be imported."""
        example_file = examples_dir / "haystack_basic.py"
        assert example_file.exists(), "haystack_basic.py should exist"

        spec = importlib.util.spec_from_file_location("haystack_basic", example_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        assert hasattr(
            module, "document_search_pipeline"
        ), "Should have document_search_pipeline function"
        assert hasattr(
            module.document_search_pipeline, "__wrapped__"
        ), "Function should be decorated"


class TestSemanticKernelExamples(TestFrameworkExamples):
    """Test Semantic Kernel framework examples."""

    def test_semantic_kernel_basic_example_exists(self):
        """Test that semantic_kernel_basic.py exists and can be imported."""
        example_file = examples_dir / "semantic_kernel_basic.py"
        assert example_file.exists(), "semantic_kernel_basic.py should exist"

        spec = importlib.util.spec_from_file_location(
            "semantic_kernel_basic", example_file
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        assert hasattr(
            module, "kernel_function"
        ), "Should have kernel_function function"
        assert hasattr(
            module.kernel_function, "__wrapped__"
        ), "Function should be decorated"


class TestLangGraphExamples(TestFrameworkExamples):
    """Test LangGraph framework examples."""

    def test_langgraph_basic_example_exists(self):
        """Test that langgraph_basic.py exists and can be imported."""
        example_file = examples_dir / "langgraph_basic.py"
        assert example_file.exists(), "langgraph_basic.py should exist"

        spec = importlib.util.spec_from_file_location("langgraph_basic", example_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        assert hasattr(module, "graph_workflow"), "Should have graph_workflow function"
        assert hasattr(
            module.graph_workflow, "__wrapped__"
        ), "Function should be decorated"


class TestGenericExamples(TestFrameworkExamples):
    """Test generic Python examples."""

    def test_generic_basic_example_exists(self):
        """Test that generic_basic.py exists and can be imported."""
        example_file = examples_dir / "generic_basic.py"
        assert example_file.exists(), "generic_basic.py should exist"

        spec = importlib.util.spec_from_file_location("generic_basic", example_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        assert hasattr(module, "data_processor"), "Should have data_processor function"
        assert hasattr(
            module.data_processor, "__wrapped__"
        ), "Function should be decorated"


class TestExamplesREADME:
    """Test that examples README is comprehensive."""

    def test_examples_readme_exists(self):
        """Test that examples README exists."""
        readme_file = examples_dir / "README.md"
        assert readme_file.exists(), "examples/README.md should exist"

    def test_examples_readme_has_all_frameworks(self):
        """Test that README mentions all framework examples."""
        readme_file = examples_dir / "README.md"
        content = readme_file.read_text()

        frameworks = [
            "langchain",
            "crewai",
            "autogen",
            "llamaindex",
            "haystack",
            "semantic_kernel",
            "langgraph",
            "generic",
        ]

        for framework in frameworks:
            assert (
                framework.lower() in content.lower()
            ), f"README should mention {framework}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
