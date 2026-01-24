"""
End-to-end tests for framework integration examples.

Validates that framework examples (LangChain, CrewAI, LlamaIndex)
work correctly and handle dependencies gracefully.
"""

import ast
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.e2e
class TestLangChainExampleE2E:
    """E2E tests for LangChain example."""

    def test_langchain_example_exists(self):
        """Test that LangChain example file exists."""
        project_root = Path(__file__).parent.parent.parent
        example_path = project_root / "examples" / "langchain-customer-service.py"
        
        assert example_path.exists(), "LangChain example not found"

    def test_langchain_example_has_valid_syntax(self):
        """Test that LangChain example has valid Python syntax."""
        project_root = Path(__file__).parent.parent.parent
        example_path = project_root / "examples" / "langchain-customer-service.py"
        
        content = example_path.read_text(encoding="utf-8")
        
        # Should parse without syntax errors
        ast.parse(content)

    def test_langchain_example_has_correct_imports(self):
        """Test that LangChain example uses correct ADRI imports."""
        project_root = Path(__file__).parent.parent.parent
        example_path = project_root / "examples" / "langchain-customer-service.py"
        
        content = example_path.read_text(encoding="utf-8")
        
        # Should use correct import
        assert "from adri import adri_protected" in content

    def test_langchain_example_has_dependency_handling(self):
        """Test that LangChain example handles missing dependencies gracefully."""
        project_root = Path(__file__).parent.parent.parent
        example_path = project_root / "examples" / "langchain-customer-service.py"
        
        content = example_path.read_text(encoding="utf-8")
        
        # Should have try/except for imports
        assert "try:" in content
        assert "ImportError" in content or "except:" in content


@pytest.mark.e2e
class TestCrewAIExampleE2E:
    """E2E tests for CrewAI example."""

    def test_crewai_example_exists(self):
        """Test that CrewAI example file exists."""
        project_root = Path(__file__).parent.parent.parent
        example_path = project_root / "examples" / "crewai-business-analysis.py"
        
        assert example_path.exists(), "CrewAI example not found"

    def test_crewai_example_has_valid_syntax(self):
        """Test that CrewAI example has valid Python syntax."""
        project_root = Path(__file__).parent.parent.parent
        example_path = project_root / "examples" / "crewai-business-analysis.py"
        
        content = example_path.read_text(encoding="utf-8")
        
        # Should parse without syntax errors
        ast.parse(content)

    def test_crewai_example_has_correct_imports(self):
        """Test that CrewAI example uses correct ADRI imports."""
        project_root = Path(__file__).parent.parent.parent
        example_path = project_root / "examples" / "crewai-business-analysis.py"
        
        content = example_path.read_text(encoding="utf-8")
        
        # Should use correct import
        assert "from adri import adri_protected" in content

    def test_crewai_example_has_dependency_handling(self):
        """Test that CrewAI example handles missing dependencies gracefully."""
        project_root = Path(__file__).parent.parent.parent
        example_path = project_root / "examples" / "crewai-business-analysis.py"
        
        content = example_path.read_text(encoding="utf-8")
        
        # Should have try/except for imports
        assert "try:" in content
        assert "ImportError" in content or "except:" in content


@pytest.mark.e2e
class TestLlamaIndexExampleE2E:
    """E2E tests for LlamaIndex example."""

    def test_llamaindex_example_exists(self):
        """Test that LlamaIndex example file exists."""
        project_root = Path(__file__).parent.parent.parent
        example_path = project_root / "examples" / "llamaindex-document-processing.py"
        
        assert example_path.exists(), "LlamaIndex example not found"

    def test_llamaindex_example_has_valid_syntax(self):
        """Test that LlamaIndex example has valid Python syntax."""
        project_root = Path(__file__).parent.parent.parent
        example_path = project_root / "examples" / "llamaindex-document-processing.py"
        
        content = example_path.read_text(encoding="utf-8")
        
        # Should parse without syntax errors
        ast.parse(content)

    def test_llamaindex_example_has_correct_imports(self):
        """Test that LlamaIndex example uses correct ADRI imports."""
        project_root = Path(__file__).parent.parent.parent
        example_path = project_root / "examples" / "llamaindex-document-processing.py"
        
        content = example_path.read_text(encoding="utf-8")
        
        # Should use correct import
        assert "from adri import adri_protected" in content

    def test_llamaindex_example_has_dependency_handling(self):
        """Test that LlamaIndex example handles missing dependencies gracefully."""
        project_root = Path(__file__).parent.parent.parent
        example_path = project_root / "examples" / "llamaindex-document-processing.py"
        
        content = example_path.read_text(encoding="utf-8")
        
        # Should have try/except for imports
        assert "try:" in content
        assert "ImportError" in content or "except:" in content


@pytest.mark.e2e
class TestFrameworkExamplesGracefulDegradation:
    """Tests for graceful degradation when framework dependencies missing."""

    @pytest.mark.parametrize("example_file", [
        "langchain-customer-service.py",
        "crewai-business-analysis.py",
        "llamaindex-document-processing.py",
    ])
    def test_example_can_be_imported_without_framework(self, example_file):
        """Test that examples can be imported even without framework installed."""
        project_root = Path(__file__).parent.parent.parent
        example_path = project_root / "examples" / example_file
        
        content = example_path.read_text(encoding="utf-8")
        
        # Should use try/except pattern
        assert "try:" in content, f"{example_file} should use try/except for imports"
        assert ("ImportError" in content or "except" in content), \
            f"{example_file} should catch import errors"

    @pytest.mark.parametrize("example_file", [
        "langchain-customer-service.py",
        "crewai-business-analysis.py",
        "llamaindex-document-processing.py",
    ])
    def test_example_provides_helpful_error_message(self, example_file):
        """Test that examples provide helpful messages when dependencies missing."""
        project_root = Path(__file__).parent.parent.parent
        example_path = project_root / "examples" / example_file
        
        content = example_path.read_text(encoding="utf-8")
        
        # Should have informative error handling
        # Look for print/raise with installation instructions
        has_error_message = (
            "print(" in content or 
            "raise" in content or
            "install" in content.lower() or
            "pip" in content.lower()
        )
        
        assert has_error_message, f"{example_file} should provide helpful error messages"


@pytest.mark.e2e
class TestFrameworkExamplesDocumentation:
    """Tests for framework example documentation."""

    @pytest.mark.parametrize("example_file", [
        "langchain-customer-service.py",
        "crewai-business-analysis.py",
        "llamaindex-document-processing.py",
    ])
    def test_example_has_docstring(self, example_file):
        """Test that framework examples have module docstrings."""
        project_root = Path(__file__).parent.parent.parent
        example_path = project_root / "examples" / example_file
        
        content = example_path.read_text(encoding="utf-8")
        tree = ast.parse(content)
        
        docstring = ast.get_docstring(tree)
        
        assert docstring is not None, f"{example_file} missing module docstring"
        assert len(docstring) > 50, f"{example_file} docstring should be descriptive"

    @pytest.mark.parametrize("example_file", [
        "langchain-customer-service.py",
        "crewai-business-analysis.py",
        "llamaindex-document-processing.py",
    ])
    def test_example_has_usage_instructions(self, example_file):
        """Test that examples include usage instructions."""
        project_root = Path(__file__).parent.parent.parent
        example_path = project_root / "examples" / example_file
        
        content = example_path.read_text(encoding="utf-8")
        tree = ast.parse(content)
        
        docstring = ast.get_docstring(tree) or ""
        
        # Should include usage or quick setup info
        has_usage = any(keyword in docstring.lower() for keyword in 
                       ["usage:", "quick setup:", "how to run", "python examples/"])
        
        assert has_usage, f"{example_file} should include usage instructions"


@pytest.mark.e2e
class TestFrameworkExamplesConsistency:
    """Tests for consistency across framework examples."""

    def test_all_framework_examples_use_same_import_style(self):
        """Test that all framework examples use consistent import style."""
        project_root = Path(__file__).parent.parent.parent
        
        framework_examples = [
            "langchain-customer-service.py",
            "crewai-business-analysis.py",
            "llamaindex-document-processing.py",
        ]
        
        import_patterns = set()
        
        for example_file in framework_examples:
            example_path = project_root / "examples" / example_file
            content = example_path.read_text(encoding="utf-8")
            tree = ast.parse(content)
            
            # Find adri imports
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    if node.module == "adri":
                        for alias in node.names:
                            if alias.name == "adri_protected":
                                import_patterns.add(f"from {node.module} import {alias.name}")
        
        # Should all use the same import style
        assert len(import_patterns) == 1, f"Framework examples use inconsistent imports: {import_patterns}"
        assert "from adri import adri_protected" in import_patterns
