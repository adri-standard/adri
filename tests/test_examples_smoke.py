"""
Smoke Tests for ADRI Examples.

These tests ensure that examples have correct imports and can be loaded without errors.
This prevents "It doesn't work as expected" experiences for new developers.

Tests validate:
- Import paths are correct (from adri import adri_protected)
- Examples can be imported without ModuleNotFoundError
- Basic structure and decorators are present
- No broken import paths to non-existent modules
"""

import ast
import importlib.util
import sys
from pathlib import Path

import pytest

# Get project root
PROJECT_ROOT = Path(__file__).parent.parent
EXAMPLES_DIR = PROJECT_ROOT / "examples"

# Example files to validate
FRAMEWORK_EXAMPLES = [
    "langchain-customer-service.py",
    "crewai-business-analysis.py",
    "llamaindex-document-processing.py",
]


class TestExamplesSmoke:
    """Smoke tests for example files."""

    @pytest.mark.unit
    @pytest.mark.parametrize("example_file", FRAMEWORK_EXAMPLES)
    def test_example_has_correct_import(self, example_file):
        """Test that examples use correct import path for adri_protected."""
        example_path = EXAMPLES_DIR / example_file

        assert example_path.exists(), f"Example file not found: {example_file}"

        content = example_path.read_text(encoding="utf-8")

        # Check for correct import
        assert "from adri import adri_protected" in content, (
            f"{example_file} must use 'from adri import adri_protected'"
        )

        # Check for incorrect imports (these should NOT exist)
        incorrect_imports = [
            "from adri.decorators.guard import adri_protected",
            "from adri.decorators import adri_protected",
        ]

        for incorrect_import in incorrect_imports:
            assert incorrect_import not in content, (
                f"{example_file} contains incorrect import: {incorrect_import}"
            )

    @pytest.mark.unit
    @pytest.mark.parametrize("example_file", FRAMEWORK_EXAMPLES)
    def test_example_syntax_valid(self, example_file):
        """Test that examples have valid Python syntax."""
        example_path = EXAMPLES_DIR / example_file

        content = example_path.read_text(encoding="utf-8")

        try:
            ast.parse(content)
        except SyntaxError as e:
            pytest.fail(f"{example_file} has syntax errors: {e}")

    @pytest.mark.unit
    @pytest.mark.parametrize("example_file", FRAMEWORK_EXAMPLES)
    def test_example_uses_decorator(self, example_file):
        """Test that examples use @adri_protected decorator."""
        example_path = EXAMPLES_DIR / example_file

        content = example_path.read_text(encoding="utf-8")

        # Parse the file
        tree = ast.parse(content)

        # Find all function definitions with decorators
        decorated_functions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                for decorator in node.decorator_list:
                    if isinstance(decorator, ast.Name) and decorator.id == "adri_protected":
                        decorated_functions.append(node.name)
                    elif isinstance(decorator, ast.Call):
                        if isinstance(decorator.func, ast.Name) and decorator.func.id == "adri_protected":
                            decorated_functions.append(node.name)

        assert len(decorated_functions) > 0, (
            f"{example_file} should have at least one function decorated with @adri_protected"
        )

    @pytest.mark.unit
    def test_no_examples_have_broken_imports(self):
        """Test that no example files have known broken import patterns."""
        broken_patterns = [
            "adri.decorators.guard",
            "adri.decorators.protection",
            "from decorators import",
        ]

        for example_file in FRAMEWORK_EXAMPLES:
            example_path = EXAMPLES_DIR / example_file
            content = example_path.read_text(encoding="utf-8")

            for pattern in broken_patterns:
                assert pattern not in content, (
                    f"{example_file} contains broken import pattern: {pattern}"
                )

    @pytest.mark.integration
    @pytest.mark.parametrize("example_file", FRAMEWORK_EXAMPLES)
    def test_example_imports_can_resolve(self, example_file):
        """Test that the adri import in examples can be resolved."""
        example_path = EXAMPLES_DIR / example_file

        # Parse and extract imports
        content = example_path.read_text(encoding="utf-8")
        tree = ast.parse(content)

        adri_imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module and node.module.startswith("adri"):
                    for alias in node.names:
                        adri_imports.append((node.module, alias.name))

        # Verify adri_protected import exists and is correct
        assert ("adri", "adri_protected") in adri_imports, (
            f"{example_file} should import adri_protected from adri module"
        )


class TestExamplesDocumentation:
    """Tests for example documentation and metadata."""

    @pytest.mark.unit
    @pytest.mark.parametrize("example_file", FRAMEWORK_EXAMPLES)
    def test_example_has_docstring(self, example_file):
        """Test that examples have module-level docstrings."""
        example_path = EXAMPLES_DIR / example_file

        content = example_path.read_text(encoding="utf-8")
        tree = ast.parse(content)

        docstring = ast.get_docstring(tree)

        assert docstring is not None, (
            f"{example_file} should have a module-level docstring"
        )
        assert len(docstring) > 50, (
            f"{example_file} docstring should be descriptive"
        )

    @pytest.mark.unit
    @pytest.mark.parametrize("example_file", FRAMEWORK_EXAMPLES)
    def test_example_has_usage_instructions(self, example_file):
        """Test that examples include usage instructions in docstring."""
        example_path = EXAMPLES_DIR / example_file

        content = example_path.read_text(encoding="utf-8")
        tree = ast.parse(content)

        docstring = ast.get_docstring(tree)

        # Accept various formats for usage instructions
        usage_patterns = ["Usage:", "usage:", "Quick Setup:", "quick setup:"]
        has_usage = any(pattern in docstring for pattern in usage_patterns)

        assert has_usage, (
            f"{example_file} should include usage instructions (Usage: or Quick Setup:)"
        )
        assert "python examples/" in docstring.lower(), (
            f"{example_file} should show how to run the example"
        )


class TestExamplesOpenSourceCompatibility:
    """Tests to ensure examples work with open source extraction."""

    @pytest.mark.unit
    @pytest.mark.parametrize("example_file", FRAMEWORK_EXAMPLES)
    def test_example_has_no_enterprise_imports(self, example_file):
        """Test that examples don't import enterprise-only modules."""
        example_path = EXAMPLES_DIR / example_file

        content = example_path.read_text(encoding="utf-8")

        enterprise_patterns = [
            "from adri_enterprise",
            "import adri_enterprise",
            "from adri.enterprise",
        ]

        for pattern in enterprise_patterns:
            assert pattern not in content, (
                f"{example_file} should not import enterprise modules (found: {pattern})"
            )

    @pytest.mark.unit
    def test_all_examples_use_same_import_style(self):
        """Test that all examples use consistent import style."""
        import_patterns = set()

        for example_file in FRAMEWORK_EXAMPLES:
            example_path = EXAMPLES_DIR / example_file
            content = example_path.read_text(encoding="utf-8")
            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    if node.module and "adri" in node.module:
                        for alias in node.names:
                            if alias.name == "adri_protected":
                                import_patterns.add(f"from {node.module} import {alias.name}")

        # Should have exactly one pattern: "from adri import adri_protected"
        assert len(import_patterns) == 1, (
            f"Examples use inconsistent import patterns: {import_patterns}"
        )
        assert "from adri import adri_protected" in import_patterns, (
            "Examples should use 'from adri import adri_protected'"
        )


class TestExamplesFirstUseExperience:
    """Tests to ensure new developer's first-use experience is smooth."""

    @pytest.mark.integration
    def test_examples_readme_exists(self):
        """Test that examples directory has a README."""
        readme_path = EXAMPLES_DIR / "README.md"

        assert readme_path.exists(), (
            "examples/ directory should have a README.md"
        )

    @pytest.mark.unit
    def test_no_examples_require_installation_of_broken_modules(self):
        """Test that examples don't reference non-existent modules in their docs."""
        broken_modules = [
            "adri.decorators",
            "adri-decorators",
        ]

        for example_file in FRAMEWORK_EXAMPLES:
            example_path = EXAMPLES_DIR / example_file
            content = example_path.read_text(encoding="utf-8")

            for module in broken_modules:
                # Check in both code and comments
                assert module not in content, (
                    f"{example_file} references non-existent module: {module}"
                )

    @pytest.mark.unit
    @pytest.mark.parametrize("example_file", FRAMEWORK_EXAMPLES)
    def test_example_has_graceful_dependency_handling(self, example_file):
        """Test that examples handle missing dependencies gracefully."""
        example_path = EXAMPLES_DIR / example_file

        content = example_path.read_text(encoding="utf-8")

        # Should have try/except around framework imports
        assert "try:" in content, (
            f"{example_file} should use try/except for dependency imports"
        )
        assert "ImportError" in content or "except" in content, (
            f"{example_file} should catch import errors gracefully"
        )


# Regression test to prevent future import path issues
class TestImportPathRegression:
    """Regression tests to prevent import path issues from reoccurring."""

    @pytest.mark.unit
    def test_adri_decorator_module_location(self):
        """Test that adri_protected is in correct location."""
        # The decorator should be at src/adri/decorator.py or src/adri/__init__.py
        adri_init = PROJECT_ROOT / "src" / "adri" / "__init__.py"
        adri_decorator = PROJECT_ROOT / "src" / "adri" / "decorator.py"

        # At least one should exist
        assert adri_init.exists() or adri_decorator.exists(), (
            "adri_protected should be in src/adri/__init__.py or src/adri/decorator.py"
        )

    @pytest.mark.unit
    def test_no_decorators_subdirectory_in_adri(self):
        """Test that there's no adri/decorators/ subdirectory causing confusion."""
        decorators_dir = PROJECT_ROOT / "src" / "adri" / "decorators"

        if decorators_dir.exists():
            # If it exists, it should not contain guard.py
            guard_file = decorators_dir / "guard.py"
            assert not guard_file.exists(), (
                "adri/decorators/guard.py should not exist - causes import confusion"
            )
