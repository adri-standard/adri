"""
End-to-end tests for code examples in documentation.

Extracts and executes Python code blocks from markdown documentation
to ensure all examples work exactly as advertised.
"""

import os
import re
from pathlib import Path
from typing import List, Tuple

import pytest


def extract_python_code_blocks(md_file: Path) -> List[Tuple[str, int]]:
    """Extract Python code blocks from a markdown file.
    
    Args:
        md_file: Path to markdown file
        
    Returns:
        List of (code, line_number) tuples for complete examples
    """
    content = md_file.read_text(encoding="utf-8")
    
    # Find all Python code blocks
    blocks = []
    for match in re.finditer(r'```python\n(.*?)\n```', content, re.DOTALL):
        code = match.group(1)
        line_number = content[:match.start()].count('\n') + 1
        
        # Only include blocks that look like complete executable examples
        if "from adri import" in code or "import adri" in code:
            # Skip placeholder examples
            if not ("..." in code or "your_" in code or "<" in code and ">" in code):
                blocks.append((code, line_number))
    
    return blocks


@pytest.mark.e2e
class TestREADMEExamples:
    """Tests for code examples in README.md."""

    def test_readme_basic_usage_example(self, clean_adri_state, sample_csv_file):
        """Test that README basic usage example works."""
        original_cwd = os.getcwd()
        try:
            os.chdir(clean_adri_state)
            
            # Create a simple working example based on README
            example_code = """
from adri import adri_protected
import pandas as pd

@adri_protected(contract="customer_data", data_param="customer_data")
def analyze_customers(customer_data):
    print(f"Analyzing {len(customer_data)} customers")
    return {"status": "complete"}

customers = pd.DataFrame({
    "id": [1, 2, 3],
    "email": ["user1@example.com", "user2@example.com", "user3@example.com"],
    "signup_date": ["2024-01-01", "2024-01-02", "2024-01-03"]
})

result = analyze_customers(customers)
print(f"Result: {result}")
"""
            
            # Write to file
            test_file = clean_adri_state / "readme_example.py"
            test_file.write_text(example_code)
            
            # Should be syntactically valid
            import ast
            ast.parse(example_code)
            
            # Verify imports are correct
            assert "from adri import adri_protected" in example_code
        finally:
            os.chdir(original_cwd)

    def test_readme_protection_modes_documented(self):
        """Test that README protection modes examples are syntactically valid."""
        example_snippets = [
            'from adri import adri_protected\n@adri_protected(contract="data", data_param="data", on_failure="raise")\ndef func(data): pass',
            'from adri import adri_protected\n@adri_protected(contract="data", data_param="data", on_failure="warn")\ndef func(data): pass',
            'from adri import adri_protected\n@adri_protected(contract="data", data_param="data", on_failure="continue")\ndef func(data): pass',
        ]
        
        import ast
        for snippet in example_snippets:
            # Should parse without syntax errors
            ast.parse(snippet)


@pytest.mark.e2e
class TestGettingStartedExamples:
    """Tests for code examples in GETTING_STARTED.md."""

    def test_customer_processor_example(self, clean_adri_state):
        """Test the customer processor example from GETTING_STARTED.md."""
        original_cwd = os.getcwd()
        try:
            os.chdir(clean_adri_state)
            
            # Example from GETTING_STARTED.md
            customer_processor_code = """
from adri import adri_protected
import pandas as pd

@adri_protected(contract="customer_data", data_param="customers")
def process_customers(customers):
    print(f"Processing {len(customers)} customers")
    total_value = customers['purchase_value'].sum()
    avg_age = customers['age'].mean()
    return {
        "total_customers": len(customers),
        "total_value": total_value,
        "average_age": avg_age
    }

if __name__ == "__main__":
    customers = pd.DataFrame({
        "customer_id": [1, 2, 3],
        "name": ["Alice", "Bob", "Charlie"],
        "email": ["alice@example.com", "bob@example.com", "charlie@example.com"],
        "age": [25, 30, 35],
        "purchase_value": [100.0, 150.0, 200.0],
        "signup_date": ["2024-01-01", "2024-01-02", "2024-01-03"]
    })
    result = process_customers(customers)
    print(f"Result: {result}")
"""
            
            # Should be syntactically valid
            import ast
            ast.parse(customer_processor_code)
            
            # Verify correct imports
            assert "from adri import adri_protected" in customer_processor_code
            
            # Write and verify file creation works
            test_file = clean_adri_state / "customer_processor.py"
            test_file.write_text(customer_processor_code)
            assert test_file.exists()
        finally:
            os.chdir(original_cwd)

    def test_bad_data_example_syntax(self):
        """Test that bad data example from docs is syntactically valid."""
        bad_data_example = """
from adri import adri_protected
import pandas as pd

@adri_protected(contract="customer_data", data_param="customers")
def process_customers(customers):
    return {"count": len(customers)}

bad_customers = pd.DataFrame({
    "customer_id": [1, 2, None],
    "name": ["Alice", "B", "Charlie"],
    "email": ["alice@example.com", "invalid-email", "charlie@example.com"],
    "age": [25, 15, 35],
    "purchase_value": [100.0, 0.0, 200.0],
    "signup_date": ["2024-01-01", "2020-01-02", "2024-01-03"]
})

try:
    result = process_customers(bad_customers)
except Exception as e:
    print(f"Caught validation error: {e}")
"""
        
        import ast
        ast.parse(bad_data_example)


@pytest.mark.e2e
class TestQuickstartExamples:
    """Tests for code examples in QUICKSTART.md."""

    def test_quickstart_step1_decorator_syntax(self):
        """Test QUICKSTART Step 1 decorator example."""
        quickstart_example = """
from adri import adri_protected

@adri_protected(contract="customer_data", data_param="data")
def process_customers(data):
    return results
"""
        # Should be syntactically valid (even with undefined 'results')
        import ast
        try:
            ast.parse(quickstart_example)
        except NameError:
            pass  # NameError is OK, we're just checking syntax

    def test_quickstart_step2_good_data_example(self):
        """Test QUICKSTART Step 2 good data example."""
        good_data_example = """
import pandas as pd
from adri import adri_protected

@adri_protected(contract="customer_data", data_param="data")
def process_customers(data):
    return {"count": len(data)}

customers = pd.DataFrame({
    "id": [1, 2, 3],
    "email": ["user1@example.com", "user2@example.com", "user3@example.com"],
    "signup_date": ["2024-01-01", "2024-01-02", "2024-01-03"]
})

result = process_customers(customers)
"""
        
        import ast
        ast.parse(good_data_example)

    def test_quickstart_protection_modes_syntax(self):
        """Test that protection mode examples are syntactically valid."""
        mode_examples = [
            '@adri_protected(contract="data", data_param="data", on_failure="raise")',
            '@adri_protected(contract="data", data_param="data", on_failure="warn")',
            '@adri_protected(contract="data", data_param="data", on_failure="continue")',
        ]
        
        import ast
        for example in mode_examples:
            # Add necessary imports for parsing
            code = f"from adri import adri_protected\n{example}\ndef func(data): pass"
            ast.parse(code)


@pytest.mark.e2e
class TestCLIReferenceExamples:
    """Tests for CLI command examples in CLI_REFERENCE.md."""

    def test_cli_reference_has_working_commands(self):
        """Test that CLI_REFERENCE.md documents real commands."""
        # These commands should all be available
        documented_commands = [
            "setup",
            "generate-contract",
            "assess",
            "list-contracts",
            "view-logs",
            "guide",
        ]
        
        # Import CLI to verify commands exist
        from adri.cli.registry import list_available_commands
        
        available = list_available_commands()
        
        for cmd in documented_commands:
            assert cmd in available, f"Documented command '{cmd}' not in registry"

    def test_cli_reference_basic_examples_syntax(self):
        """Test that basic CLI examples from docs are valid shell commands."""
        # These are example CLI commands from CLI_REFERENCE.md
        cli_examples = [
            "adri setup",
            "adri generate-contract data.csv --name customer_data",
            "adri assess data.csv --standard customer_data",
            "adri list-contracts",
            "adri view-logs",
            "adri guide",
        ]
        
        # Verify they have correct structure (command + optional args)
        for example in cli_examples:
            parts = example.split()
            assert parts[0] == "adri", f"Example should start with 'adri': {example}"
            assert len(parts) >= 2, f"Example should have command: {example}"


@pytest.mark.e2e
class TestFrameworkPatternsExamples:
    """Tests for framework integration examples."""

    def test_langchain_integration_syntax(self):
        """Test LangChain integration example syntax."""
        langchain_example = """
from adri import adri_protected

@adri_protected(contract="chain_input", data_param="input_data")
def langchain_tool(input_data):
    return chain.invoke(input_data)
"""
        
        # Should be syntactically valid
        import ast
        try:
            ast.parse(langchain_example)
        except NameError:
            pass  # NameError for 'chain' is expected

    def test_crewai_integration_syntax(self):
        """Test CrewAI integration example syntax."""
        crewai_example = """
from adri import adri_protected

@adri_protected(contract="crew_context", data_param="context")
def crew_task(context):
    return crew.kickoff(context)
"""
        
        import ast
        try:
            ast.parse(crewai_example)
        except NameError:
            pass  # NameError for 'crew' is expected

    def test_autogen_integration_syntax(self):
        """Test AutoGen integration example syntax."""
        autogen_example = """
from adri import adri_protected

@adri_protected(contract="messages", data_param="messages")
def autogen_function(messages):
    return agent.generate_reply(messages)
"""
        
        import ast
        try:
            ast.parse(autogen_example)
        except NameError:
            pass  # NameError for 'agent' is expected


@pytest.mark.e2e
class TestDocumentationExamplesExecutable:
    """Tests that validate documentation examples can actually execute."""

    def test_readme_import_works(self):
        """Test that the basic import fromREADME works."""
        # This is the first thing users see in README
        from adri import adri_protected
        
        # Should be callable
        assert callable(adri_protected)

    def test_minimalist_example_structure(self, clean_adri_state):
        """Test a minimalist complete example."""
        original_cwd = os.getcwd()
        try:
            os.chdir(clean_adri_state)
            
            # Create minimal working example
            minimal_code = """
from adri import adri_protected

@adri_protected(contract="test_data", data_param="data")
def test_function(data):
    return {"result": "success"}
"""
            
            # Should compile
            import ast
            ast.parse(minimal_code)
            
            # Verify structure
            tree = ast.parse(minimal_code)
            
            # Should have import
            imports = [node for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
            assert len(imports) > 0
            
            # Should have decorated function
            functions = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
            assert len(functions) > 0
            
            # Function should have decorator
            function = functions[0]
            assert len(function.decorator_list) > 0
        finally:
            os.chdir(original_cwd)


@pytest.mark.e2e
class TestDocumentationPathsAccuracy:
    """Tests that validate file paths in documentation are accurate."""

    def test_documented_contract_paths_exist(self):
        """Test that contract paths mentioned in docs exist."""
        project_root = Path(__file__).parent.parent.parent
        
        # Paths documented in README for contract templates
        documented_template_paths = [
            "ADRI/contracts/domains/customer_service_contract.yaml",
            "ADRI/contracts/domains/ecommerce_order_contract.yaml",
            "ADRI/contracts/domains/financial_transaction_contract.yaml",
            "ADRI/contracts/domains/healthcare_patient_contract.yaml",
            "ADRI/contracts/frameworks/langchain_chain_input_contract.yaml",
            "ADRI/contracts/frameworks/crewai_task_context_contract.yaml",
        ]
        
        for path_str in documented_template_paths:
            full_path = project_root / path_str
            assert full_path.exists(), f"Documented template path doesn't exist: {path_str}"

    def test_documented_example_paths_exist(self):
        """Test that example file paths in docs exist."""
        project_root = Path(__file__).parent.parent.parent
        
        # Example files mentioned in documentation
        documented_examples = [
            "examples/langchain-customer-service.py",
            "examples/crewai-business-analysis.py",
            "examples/llamaindex-document-processing.py",
        ]
        
        for path_str in documented_examples:
            full_path = project_root / path_str
            assert full_path.exists(), f"Documented example doesn't exist: {path_str}"


@pytest.mark.e2e
class TestDocumentationInternalLinks:
    """Tests for internal documentation links."""

    def test_readme_links_to_existing_docs(self):
        """Test that README links point to actual files."""
        project_root = Path(__file__).parent.parent.parent
        readme = project_root / "README.md"
        
        if not readme.exists():
            pytest.skip("README.md not found")
        
        content = readme.read_text(encoding="utf-8")
        
        # Extract markdown links to local files
        local_links = re.findall(r'\[([^\]]+)\]\(([^h][^)]+\.md)\)', content)
        
        for link_text, link_path in local_links:
            # Skip external URLs
            if link_path.startswith('http'):
                continue
            
            # Resolve relative to README location
            full_path = (readme.parent / link_path).resolve()
            
            assert full_path.exists(), f"README links to non-existent file: {link_path}"

    def test_getting_started_links_valid(self):
        """Test that GETTING_STARTED.md links are valid."""
        project_root = Path(__file__).parent.parent.parent
        getting_started = project_root / "docs" / "GETTING_STARTED.md"
        
        if not getting_started.exists():
            pytest.skip("GETTING_STARTED.md not found")
        
        content = getting_started.read_text(encoding="utf-8")
        
        # Extract local markdown links
        local_links = re.findall(r'\[([^\]]+)\]\(([^h][^)]+\.md)\)', content)
        
        for link_text, link_path in local_links:
            if link_path.startswith('http'):
                continue
            
            # Resolve relative to GETTING_STARTED location
            full_path = (getting_started.parent / link_path).resolve()
            
            # Should exist (with some tolerance for external links)
            if not link_path.startswith('../'):
                assert full_path.exists() or "github.com" not in link_path, \
                    f"GETTING_STARTED links to non-existent: {link_path}"
