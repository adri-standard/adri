"""
Smoke Tests: ADRI Decorator Validation

Tests that all framework examples use @adri_protected decorators correctly.
No API calls - completely free to run.
"""

import ast
import sys
from pathlib import Path

import pytest

# Add examples directory to path
examples_dir = Path(__file__).parent.parent.parent.parent / "examples"
sys.path.insert(0, str(examples_dir))


class ADRIDecoratorVisitor(ast.NodeVisitor):
    """AST visitor to find @adri_protected decorators."""

    def __init__(self):
        self.adri_protected_functions = []
        self.all_functions = []
        self.imports_adri = False

    def visit_Import(self, node):
        """Check for ADRI imports."""
        for alias in node.names:
            if "adri" in alias.name:
                self.imports_adri = True

    def visit_ImportFrom(self, node):
        """Check for ADRI decorator imports."""
        if node.module and "adri" in node.module:
            self.imports_adri = True
            for alias in node.names:
                if alias.name == "adri_protected":
                    self.imports_adri = True

    def visit_FunctionDef(self, node):
        """Visit function definitions to find decorators."""
        self.all_functions.append(node.name)

        # Check for @adri_protected decorator
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name) and decorator.id == "adri_protected":
                self.adri_protected_functions.append(node.name)
            elif (
                isinstance(decorator, ast.Attribute)
                and decorator.attr == "adri_protected"
            ):
                self.adri_protected_functions.append(node.name)

        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        """Visit async function definitions."""
        self.visit_FunctionDef(node)  # Same logic as regular functions


class TestADRIDecorators:
    """Test ADRI decorator usage in framework examples."""

    def _analyze_example_file(self, file_path):
        """Analyze a Python file for ADRI decorator usage."""
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        try:
            tree = ast.parse(content)
            visitor = ADRIDecoratorVisitor()
            visitor.visit(tree)
            return visitor
        except SyntaxError as e:
            pytest.fail(f"Syntax error in {file_path}: {e}")

    def test_langchain_example_has_decorators(self):
        """Test LangChain example uses @adri_protected."""
        example_file = examples_dir / "langchain-customer-service.py"
        visitor = self._analyze_example_file(example_file)

        assert visitor.imports_adri, "Should import ADRI"
        assert (
            len(visitor.adri_protected_functions) > 0
        ), "Should have @adri_protected functions"

        # Check for actual decorated functions in the code
        expected_functions = [
            "process_customer_request",
            "handle_conversation",
            "execute_tool_call",
        ]
        found_protected = [
            f for f in expected_functions if f in visitor.adri_protected_functions
        ]
        assert (
            len(found_protected) > 0
        ), f"Should have protected functions from: {expected_functions}. Found: {visitor.adri_protected_functions}"

    def test_crewai_example_has_decorators(self):
        """Test CrewAI example uses @adri_protected."""
        example_file = examples_dir / "crewai-business-analysis.py"
        visitor = self._analyze_example_file(example_file)

        assert visitor.imports_adri, "Should import ADRI"
        assert (
            len(visitor.adri_protected_functions) > 0
        ), "Should have @adri_protected functions"

        # Check for actual decorated functions in the code
        expected_functions = [
            "coordinate_market_analysis",
            "process_structured_output",
            "execute_agent_tools",
        ]
        found_protected = [
            f for f in expected_functions if f in visitor.adri_protected_functions
        ]
        assert (
            len(found_protected) > 0
        ), f"Should have protected functions from: {expected_functions}. Found: {visitor.adri_protected_functions}"

    def test_autogen_example_has_decorators(self):
        """Test AutoGen example uses @adri_protected."""
        example_file = examples_dir / "autogen-research-collaboration.py"
        visitor = self._analyze_example_file(example_file)

        assert visitor.imports_adri, "Should import ADRI"
        assert (
            len(visitor.adri_protected_functions) > 0
        ), "Should have @adri_protected functions"

        # Check for actual decorated functions in the code
        expected_functions = [
            "start_conversation",
            "call_research_function",
            "process_message",
        ]
        found_protected = [
            f for f in expected_functions if f in visitor.adri_protected_functions
        ]
        assert (
            len(found_protected) > 0
        ), f"Should have protected functions from: {expected_functions}. Found: {visitor.adri_protected_functions}"

    def test_haystack_example_has_decorators(self):
        """Test Haystack example uses @adri_protected."""
        example_file = examples_dir / "haystack-knowledge-management.py"
        visitor = self._analyze_example_file(example_file)

        assert visitor.imports_adri, "Should import ADRI"
        assert (
            len(visitor.adri_protected_functions) > 0
        ), "Should have @adri_protected functions"

        # Check for actual decorated functions in the code
        expected_functions = [
            "search_documents",
            "haystack_document_indexing",
        ]
        found_protected = [
            f for f in expected_functions if f in visitor.adri_protected_functions
        ]
        assert (
            len(found_protected) > 0
        ), f"Should have protected functions from: {expected_functions}. Found: {visitor.adri_protected_functions}"

    def test_llamaindex_example_has_decorators(self):
        """Test LlamaIndex example uses @adri_protected."""
        example_file = examples_dir / "llamaindex-document-processing.py"
        visitor = self._analyze_example_file(example_file)

        assert visitor.imports_adri, "Should import ADRI"
        assert (
            len(visitor.adri_protected_functions) > 0
        ), "Should have @adri_protected functions"

        # Check for actual decorated functions in the code
        expected_functions = [
            "process_document_batch",
            "query_knowledge_base",
        ]
        found_protected = [
            f for f in expected_functions if f in visitor.adri_protected_functions
        ]
        assert (
            len(found_protected) > 0
        ), f"Should have protected functions from: {expected_functions}. Found: {visitor.adri_protected_functions}"

    def test_langgraph_example_has_decorators(self):
        """Test LangGraph example uses @adri_protected."""
        example_file = examples_dir / "langgraph-workflow-automation.py"
        visitor = self._analyze_example_file(example_file)

        assert visitor.imports_adri, "Should import ADRI"
        assert (
            len(visitor.adri_protected_functions) > 0
        ), "Should have @adri_protected functions"

        # Check for actual decorated functions in the code
        expected_functions = [
            "execute_analysis_workflow",
            "langgraph_chatbot_workflow",
            "langgraph_decision_workflow",
        ]
        found_protected = [
            f for f in expected_functions if f in visitor.adri_protected_functions
        ]
        assert (
            len(found_protected) > 0
        ), f"Should have protected functions from: {expected_functions}. Found: {visitor.adri_protected_functions}"

    def test_semantic_kernel_example_has_decorators(self):
        """Test Semantic Kernel example uses @adri_protected."""
        example_file = examples_dir / "semantic-kernel-ai-orchestration.py"
        visitor = self._analyze_example_file(example_file)

        assert visitor.imports_adri, "Should import ADRI"
        assert (
            len(visitor.adri_protected_functions) > 0
        ), "Should have @adri_protected functions"

        # Check for actual decorated functions in the code
        expected_functions = [
            "execute_ai_function",
            "semantic_kernel_planning_function",
        ]
        found_protected = [
            f for f in expected_functions if f in visitor.adri_protected_functions
        ]
        assert (
            len(found_protected) > 0
        ), f"Should have protected functions from: {expected_functions}. Found: {visitor.adri_protected_functions}"


class TestADRIImports:
    """Test that examples properly import ADRI components."""

    def test_all_examples_import_adri_protected(self):
        """Test that all examples import adri_protected decorator."""
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

            # Should import adri_protected
            assert (
                "adri_protected" in content
            ), f"{filename} should import adri_protected"

            # Should have proper import statement
            import_patterns = [
                "from adri.decorators.guard import adri_protected",
                "from adri.decorators import adri_protected",
                "import adri",
            ]

            has_import = any(pattern in content for pattern in import_patterns)
            assert has_import, f"{filename} should have proper ADRI import"


class TestDecoratorUsage:
    """Test proper usage patterns of ADRI decorators."""

    def test_decorators_are_used_correctly(self):
        """Test that @adri_protected decorators are used correctly."""
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

            # Count decorator usage
            decorator_count = content.count("@adri_protected")

            # Should have at least one decorator
            assert (
                decorator_count > 0
            ), f"{filename} should use @adri_protected decorator"

            # Should have reasonable number of decorators (not excessive)
            assert (
                decorator_count <= 10
            ), f"{filename} should not have excessive decorators ({decorator_count})"

    def test_main_functions_are_protected(self):
        """Test that main workflow functions are protected."""
        # This is a more sophisticated test that looks for patterns
        # indicating main workflow functions should be protected

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

            # Parse the file to find functions with specific patterns
            visitor = ADRIDecoratorVisitor()
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            try:
                tree = ast.parse(content)
                visitor.visit(tree)
            except SyntaxError:
                pytest.skip(f"Could not parse {filename}")

            # Look for functions that should likely be protected
            # (these are heuristics based on naming patterns)
            likely_main_functions = []
            for func_name in visitor.all_functions:
                if any(
                    keyword in func_name.lower()
                    for keyword in [
                        "workflow",
                        "pipeline",
                        "agent",
                        "process",
                        "execute",
                        "run",
                    ]
                ):
                    likely_main_functions.append(func_name)

            if likely_main_functions:
                # At least some of these should be protected
                protected_main = [
                    f
                    for f in likely_main_functions
                    if f in visitor.adri_protected_functions
                ]
                assert (
                    len(protected_main) > 0
                ), f"{filename} should protect main functions: {likely_main_functions}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
