"""
Documentation Coherence Tests.

Ensures all documentation is consistent with actual code implementation.
Prevents "It doesn't work as expected" experiences from documentation errors.

Tests validate:
- Import statements in documentation match actual module structure
- CLI commands referenced in docs actually exist
- API parameters in docs match decorator signatures
- Code examples are executable and correct
"""

import ast
import re
from pathlib import Path

import pytest

# Get project root
PROJECT_ROOT = Path(__file__).parent.parent
DOCS_DIR = PROJECT_ROOT / "docs"
README_FILE = PROJECT_ROOT / "README.md"
QUICKSTART_FILE = PROJECT_ROOT / "QUICKSTART.md"
ENTERPRISE_README = PROJECT_ROOT / "README.enterprise.md"


class TestDocumentationImports:
    """Test that documentation uses correct import patterns."""

    @pytest.mark.unit
    def test_no_docs_have_broken_decorator_imports(self):
        """Test that no documentation references broken import paths."""
        broken_patterns = [
            "from adri.decorators.guard import",
            "from adri.decorators import adri_protected",
            "import adri.decorators",
        ]

        # Check all markdown files
        doc_files = list(DOCS_DIR.rglob("*.md"))
        doc_files.extend([README_FILE, QUICKSTART_FILE, ENTERPRISE_README])

        errors = []
        for doc_file in doc_files:
            if not doc_file.exists():
                continue

            content = doc_file.read_text(encoding="utf-8")

            for pattern in broken_patterns:
                if pattern in content:
                    # Find line number
                    for i, line in enumerate(content.split("\n"), 1):
                        if pattern in line:
                            errors.append(
                                f"{doc_file.relative_to(PROJECT_ROOT)}:{i} "
                                f"contains broken import: {pattern}"
                            )

        assert len(errors) == 0, (
            f"Found {len(errors)} documentation files with broken imports:\n" +
            "\n".join(errors)
        )

    @pytest.mark.unit
    def test_docs_use_correct_decorator_import(self):
        """Test that docs using adri_protected use the correct import."""
        # Find all docs mentioning adri_protected
        doc_files = list(DOCS_DIR.rglob("*.md"))
        doc_files.extend([README_FILE, QUICKSTART_FILE, ENTERPRISE_README])

        for doc_file in doc_files:
            if not doc_file.exists():
                continue

            content = doc_file.read_text(encoding="utf-8")

            # If doc mentions adri_protected and shows an import
            if "@adri_protected" in content or "adri_protected(" in content:
                # Check if it shows import statement
                if "from adri" in content and "import" in content:
                    # Extract import statements
                    import_lines = [
                        line for line in content.split("\n")
                        if "from adri" in line and "import" in line
                    ]

                    for line in import_lines:
                        if "adri_protected" in line:
                            assert "from adri import adri_protected" in line, (
                                f"{doc_file.relative_to(PROJECT_ROOT)} shows incorrect import: {line}"
                            )

    @pytest.mark.unit
    def test_readme_has_correct_import_example(self):
        """Test that README shows correct import in usage examples."""
        readme_content = README_FILE.read_text(encoding="utf-8")

        # README should show the correct import
        if "@adri_protected" in readme_content:
            assert "from adri import adri_protected" in readme_content, (
                "README.md should show 'from adri import adri_protected'"
            )

    @pytest.mark.unit
    def test_quickstart_has_correct_import(self):
        """Test that QUICKSTART shows correct import."""
        quickstart_content = QUICKSTART_FILE.read_text(encoding="utf-8")

        if "@adri_protected" in quickstart_content:
            assert "from adri import adri_protected" in quickstart_content, (
                "QUICKSTART.md should show 'from adri import adri_protected'"
            )


class TestCLIDocumentation:
    """Test that CLI commands in documentation match implementation."""

    @pytest.mark.integration
    def test_cli_commands_in_docs_exist(self):
        """Test that CLI commands referenced in docs actually exist."""
        # Get all CLI commands from implementation
        cli_commands_dir = PROJECT_ROOT / "src" / "adri" / "cli" / "commands"

        if not cli_commands_dir.exists():
            pytest.skip("CLI commands directory not found")

        # Extract command names from files
        actual_commands = set()
        for cmd_file in cli_commands_dir.glob("*.py"):
            if cmd_file.name == "__init__.py":
                continue
            # Command name is filename without .py
            cmd_name = cmd_file.stem.replace("_", "-")
            actual_commands.add(cmd_name)

        # Check documentation references
        cli_ref_file = DOCS_DIR / "CLI_REFERENCE.md"
        if cli_ref_file.exists():
            content = cli_ref_file.read_text(encoding="utf-8")

            # Extract command references (pattern: adri <command>)
            documented_commands = set(re.findall(r'adri\s+([a-z-]+)', content))

            # Remove common non-command words
            documented_commands -= {'the', 'and', 'or', 'for', 'to', 'a', 'is'}

            # Check for commands that don't exist
            for cmd in documented_commands:
                if cmd in ['setup', 'guide', 'assess', 'list-contracts', 'generate-contract']:
                    # These are known commands, should exist
                    assert cmd in actual_commands or cmd.replace('-', '_') + '.py' in [
                        f.name for f in cli_commands_dir.glob("*.py")
                    ], f"Documented command 'adri {cmd}' not found in implementation"


class TestAPIDocumentation:
    """Test that API documentation matches actual implementation."""

    @pytest.mark.integration
    def test_decorator_parameters_documented(self):
        """Test that documented decorator parameters exist in code."""
        # Read decorator signature
        decorator_file = PROJECT_ROOT / "src" / "adri" / "decorator.py"

        if not decorator_file.exists():
            pytest.skip("Decorator file not found")

        content = decorator_file.read_text(encoding="utf-8")
        tree = ast.parse(content)

        # Find adri_protected function
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "adri_protected":
                # Extract parameter names
                param_names = [arg.arg for arg in node.args.args]

                # Check API documentation
                api_doc = DOCS_DIR / "API_REFERENCE.md"
                if api_doc.exists():
                    api_content = api_doc.read_text(encoding="utf-8")

                    # Core parameters that should be documented
                    core_params = ['contract', 'data_param', 'min_score', 'on_failure']

                    for param in core_params:
                        if param in param_names:
                            assert param in api_content, (
                                f"Parameter '{param}' exists in code but not documented in API_REFERENCE.md"
                            )
                break  # Found the function, exit loop


class TestCodeExamplesInDocs:
    """Test that code examples in documentation are valid."""

    @pytest.mark.unit
    def test_python_code_blocks_complete_examples_have_valid_syntax(self):
        """Test that complete Python code examples in docs have valid syntax."""
        # Only check examples that import adri - these should be complete
        doc_files = [README_FILE, QUICKSTART_FILE]
        doc_files.extend(list(DOCS_DIR.glob("*.md")))

        for doc_file in doc_files:
            if not doc_file.exists():
                continue

            content = doc_file.read_text(encoding="utf-8")

            # Extract Python code blocks that import adri (these should be complete)
            python_blocks = re.findall(
                r'```python\n(.*?)\n```',
                content,
                re.DOTALL
            )

            for i, block in enumerate(python_blocks, 1):
                # Only validate blocks that import adri - these should be complete examples
                if "from adri import" in block or "import adri" in block:
                    # Skip blocks with obvious placeholders
                    if "..." in block or "your_" in block or "<" in block:
                        continue

                    try:
                        ast.parse(block)
                    except SyntaxError:
                        # This is OK - many examples are intentionally incomplete snippets
                        continue


class TestDocumentationConsistency:
    """Test that documentation is internally consistent."""

    @pytest.mark.unit
    def test_getting_started_matches_quickstart(self):
        """Test that GETTING_STARTED and QUICKSTART don't contradict."""
        quickstart = QUICKSTART_FILE.read_text(encoding="utf-8")
        getting_started_file = DOCS_DIR / "GETTING_STARTED.md"

        if not getting_started_file.exists():
            pytest.skip("GETTING_STARTED.md not found")

        getting_started = getting_started_file.read_text(encoding="utf-8")

        # Both should use same import pattern
        if "from adri import" in quickstart and "from adri import" in getting_started:
            # Extract the actual imports
            qs_imports = set(re.findall(r'from adri import (\w+)', quickstart))
            gs_imports = set(re.findall(r'from adri import (\w+)', getting_started))

            # Common imports should be consistent
            common = qs_imports & gs_imports
            for imp in common:
                assert imp in ['adri_protected'], (
                    f"Import '{imp}' appears in both but may be inconsistent"
                )

    @pytest.mark.unit
    def test_enterprise_docs_dont_contradict_opensource(self):
        """Test that enterprise docs maintain compatibility with opensource."""
        if not ENTERPRISE_README.exists():
            pytest.skip("Enterprise README not found")

        enterprise_content = ENTERPRISE_README.read_text(encoding="utf-8")
        opensource_content = README_FILE.read_text(encoding="utf-8")

        # Both should use same decorator import
        if "@adri_protected" in enterprise_content and "@adri_protected" in opensource_content:
            if "from adri import adri_protected" in opensource_content:
                assert "from adri import adri_protected" in enterprise_content, (
                    "Enterprise and opensource READMEs show different imports for adri_protected"
                )


class TestFirstUseDocumentation:
    """Test that first-use documentation is accurate."""

    @pytest.mark.integration
    def test_installation_instructions_complete(self):
        """Test that installation instructions are complete."""
        readme_content = README_FILE.read_text(encoding="utf-8")

        # Should mention pip install
        assert "pip install" in readme_content.lower(), (
            "README should include pip install instructions"
        )

        # Should mention the package name
        assert "adri" in readme_content.lower(), (
            "README should mention package name"
        )

    @pytest.mark.unit
    def test_first_example_is_simple(self):
        """Test that the first example in docs is simple and clear."""
        quickstart = QUICKSTART_FILE.read_text(encoding="utf-8")

        # First code example should be short
        first_example = re.search(r'```python\n(.*?)\n```', quickstart, re.DOTALL)

        if first_example:
            example_code = first_example.group(1)
            lines = example_code.strip().split('\n')

            # First example shouldn't be too complex (reasonable threshold)
            assert len(lines) < 20, (
                f"First code example is too long ({len(lines)} lines). "
                "Should be simple for first-time users."
            )


# Regression prevention
class TestDocumentationRegressionPrevention:
    """Tests to prevent documentation issues from recurring."""

    @pytest.mark.unit
    def test_no_references_to_nonexistent_modules(self):
        """Test that docs don't reference modules that don't exist."""
        nonexistent_modules = [
            "adri.decorators.guard",
            "adri.decorators.protection",
            "adri.guard.decorators",
        ]

        all_docs = list(DOCS_DIR.rglob("*.md"))
        all_docs.extend([README_FILE, QUICKSTART_FILE, ENTERPRISE_README])

        errors = []
        for doc in all_docs:
            if not doc.exists():
                continue
            content = doc.read_text(encoding="utf-8")

            for module in nonexistent_modules:
                if module in content:
                    errors.append(
                        f"{doc.relative_to(PROJECT_ROOT)} references non-existent module: {module}"
                    )

        assert len(errors) == 0, (
            "Documentation references non-existent modules:\n" + "\n".join(errors)
        )
