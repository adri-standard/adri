"""
Smoke Tests: Import Validation for Framework Examples

Tests that all framework examples can be imported and have basic structure.
No API calls - completely free to run.
"""

import importlib.util
import sys
from pathlib import Path

import pytest

# Add examples directory to path
examples_dir = Path(__file__).parent.parent.parent.parent / "examples"
sys.path.insert(0, str(examples_dir))


class TestFrameworkImports:
    """Test that all framework examples can be imported."""

    @pytest.fixture
    def examples_directory(self):
        """Get the examples directory path."""
        return examples_dir

    def test_langchain_example_imports(self, examples_directory):
        """Test LangChain example can be imported."""
        example_file = examples_directory / "langchain-customer-service.py"
        assert example_file.exists(), "langchain-customer-service.py should exist"

        # Test import without executing
        spec = importlib.util.spec_from_file_location("langchain_example", example_file)
        assert spec is not None, "Could not create module spec"

        module = importlib.util.module_from_spec(spec)
        assert module is not None, "Could not create module"

        # Import should work (may skip some parts due to missing API key)
        try:
            spec.loader.exec_module(module)
        except SystemExit:
            # Expected - example exits when no API key
            pass

    def test_crewai_example_imports(self, examples_directory):
        """Test CrewAI example can be imported."""
        example_file = examples_directory / "crewai-business-analysis.py"
        assert example_file.exists(), "crewai-business-analysis.py should exist"

        spec = importlib.util.spec_from_file_location("crewai_example", example_file)
        assert spec is not None, "Could not create module spec"

        module = importlib.util.module_from_spec(spec)
        assert module is not None, "Could not create module"

        try:
            spec.loader.exec_module(module)
        except SystemExit:
            # Expected - example exits when no API key
            pass

    def test_autogen_example_imports(self, examples_directory):
        """Test AutoGen example can be imported."""
        example_file = examples_directory / "autogen-research-collaboration.py"
        assert example_file.exists(), "autogen-research-collaboration.py should exist"

        spec = importlib.util.spec_from_file_location("autogen_example", example_file)
        assert spec is not None, "Could not create module spec"

        module = importlib.util.module_from_spec(spec)
        assert module is not None, "Could not create module"

        try:
            spec.loader.exec_module(module)
        except SystemExit:
            # Expected - example exits when no API key
            pass

    def test_haystack_example_imports(self, examples_directory):
        """Test Haystack example can be imported."""
        example_file = examples_directory / "haystack-knowledge-management.py"
        assert example_file.exists(), "haystack-knowledge-management.py should exist"

        spec = importlib.util.spec_from_file_location("haystack_example", example_file)
        assert spec is not None, "Could not create module spec"

        module = importlib.util.module_from_spec(spec)
        assert module is not None, "Could not create module"

        try:
            spec.loader.exec_module(module)
        except SystemExit:
            # Expected - example exits when no API key
            pass

    def test_llamaindex_example_imports(self, examples_directory):
        """Test LlamaIndex example can be imported."""
        example_file = examples_directory / "llamaindex-document-processing.py"
        assert example_file.exists(), "llamaindex-document-processing.py should exist"

        spec = importlib.util.spec_from_file_location(
            "llamaindex_example", example_file
        )
        assert spec is not None, "Could not create module spec"

        module = importlib.util.module_from_spec(spec)
        assert module is not None, "Could not create module"

        try:
            spec.loader.exec_module(module)
        except SystemExit:
            # Expected - example exits when no API key
            pass

    def test_langgraph_example_imports(self, examples_directory):
        """Test LangGraph example can be imported."""
        example_file = examples_directory / "langgraph-workflow-automation.py"
        assert example_file.exists(), "langgraph-workflow-automation.py should exist"

        spec = importlib.util.spec_from_file_location("langgraph_example", example_file)
        assert spec is not None, "Could not create module spec"

        module = importlib.util.module_from_spec(spec)
        assert module is not None, "Could not create module"

        try:
            spec.loader.exec_module(module)
        except SystemExit:
            # Expected - example exits when no API key
            pass

    def test_semantic_kernel_example_imports(self, examples_directory):
        """Test Semantic Kernel example can be imported."""
        example_file = examples_directory / "semantic-kernel-ai-orchestration.py"
        assert example_file.exists(), "semantic-kernel-ai-orchestration.py should exist"

        spec = importlib.util.spec_from_file_location(
            "semantic_kernel_example", example_file
        )
        assert spec is not None, "Could not create module spec"

        module = importlib.util.module_from_spec(spec)
        assert module is not None, "Could not create module"

        try:
            spec.loader.exec_module(module)
        except SystemExit:
            # Expected - example exits when no API key
            pass


class TestFrameworkStructure:
    """Test basic structure of framework examples."""

    def test_all_examples_exist(self):
        """Test that all expected example files exist."""
        expected_files = [
            "langchain-customer-service.py",
            "crewai-business-analysis.py",
            "autogen-research-collaboration.py",
            "haystack-knowledge-management.py",
            "llamaindex-document-processing.py",
            "langgraph-workflow-automation.py",
            "semantic-kernel-ai-orchestration.py",
        ]

        for filename in expected_files:
            file_path = examples_dir / filename
            assert file_path.exists(), f"Example file {filename} should exist"
            assert file_path.is_file(), f"{filename} should be a file"
            assert file_path.stat().st_size > 0, f"{filename} should not be empty"

    def test_examples_have_shebang(self):
        """Test that all examples have proper shebang."""
        example_files = [
            "langchain-customer-service.py",
            "crewai-business-analysis.py",
            "autogen-research-collaboration.py",
            "haystack-knowledge-management.py",
            "llamaindex-document-processing.py",
            "langgraph-workflow-automation.py",
            "semantic-kernel-ai-orchestration.py",
        ]

        for filename in example_files:
            file_path = examples_dir / filename
            with open(file_path, "r", encoding="utf-8") as f:
                first_line = f.readline().strip()
                assert first_line.startswith("#!"), f"{filename} should have shebang"
                assert (
                    "python" in first_line.lower()
                ), f"{filename} should have Python shebang"

    def test_examples_have_docstrings(self):
        """Test that all examples have proper docstrings."""
        example_files = [
            "langchain-customer-service.py",
            "crewai-business-analysis.py",
            "autogen-research-collaboration.py",
            "haystack-knowledge-management.py",
            "llamaindex-document-processing.py",
            "langgraph-workflow-automation.py",
            "semantic-kernel-ai-orchestration.py",
        ]

        for filename in example_files:
            file_path = examples_dir / filename
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

                # Should have a module docstring
                assert '"""' in content, f"{filename} should have docstring"

                # Should mention ADRI
                assert "ADRI" in content, f"{filename} should mention ADRI"

                # Should mention the framework
                framework_name = filename.split("-")[0]
                assert (
                    framework_name.lower() in content.lower()
                ), f"{filename} should mention {framework_name}"

    def test_examples_have_api_key_checks(self):
        """Test that all examples check for API keys."""
        example_files = [
            "langchain-customer-service.py",
            "crewai-business-analysis.py",
            "autogen-research-collaboration.py",
            "haystack-knowledge-management.py",
            "llamaindex-document-processing.py",
            "langgraph-workflow-automation.py",
            "semantic-kernel-ai-orchestration.py",
        ]

        for filename in example_files:
            file_path = examples_dir / filename
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

                # Should check for OpenAI API key
                assert (
                    "OPENAI_API_KEY" in content
                ), f"{filename} should check for OPENAI_API_KEY"

                # Should have error handling for missing key
                assert (
                    "sys.exit" in content or "exit(" in content
                ), f"{filename} should exit when no API key"


class TestExamplesREADME:
    """Test that examples README is comprehensive."""

    def test_readme_exists(self):
        """Test that examples README exists."""
        readme_file = examples_dir / "README.md"
        assert readme_file.exists(), "examples/README.md should exist"
        assert readme_file.stat().st_size > 0, "README should not be empty"

    def test_readme_mentions_frameworks(self):
        """Test that README mentions all frameworks."""
        readme_file = examples_dir / "README.md"
        with open(readme_file, "r", encoding="utf-8") as f:
            content = f.read().lower()

        frameworks = [
            "langchain",
            "crewai",
            "autogen",
            "haystack",
            "llamaindex",
            "langgraph",
            "semantic",  # For semantic kernel
        ]

        for framework in frameworks:
            assert framework in content, f"README should mention {framework}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
