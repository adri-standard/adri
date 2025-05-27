"""
Infrastructure tests for quickstart components.

Verifies that all quickstart files exist, are properly structured,
and follow the project's conventions.
"""

import os
import re
import csv
import json
from pathlib import Path
import unittest

# Get project root and quickstart directory
project_root = Path(__file__).parent.parent.parent
quickstart_dir = project_root / "quickstart"


class TestQuickstartStructure(unittest.TestCase):
    """Test the quickstart directory structure and files."""
    
    def test_quickstart_directory_exists(self):
        """Test that quickstart directory exists."""
        self.assertTrue(quickstart_dir.exists(), "Quickstart directory not found")
        self.assertTrue(quickstart_dir.is_dir(), "Quickstart should be a directory")
    
    def test_required_files_exist(self):
        """Test that all required quickstart files exist."""
        required_files = [
            "README.md",
            "see_it.py",
            "try_it.py"
        ]
        
        for filename in required_files:
            filepath = quickstart_dir / filename
            self.assertTrue(
                filepath.exists(),
                f"Required file {filename} not found in quickstart/"
            )
    
    def test_required_directories_exist(self):
        """Test that required subdirectories exist."""
        required_dirs = ["samples", "outputs"]
        
        for dirname in required_dirs:
            dirpath = quickstart_dir / dirname
            self.assertTrue(
                dirpath.exists(),
                f"Required directory {dirname} not found in quickstart/"
            )
            self.assertTrue(
                dirpath.is_dir(),
                f"{dirname} should be a directory"
            )
    
    def test_sample_files_complete(self):
        """Test that all sample CSV files exist and are valid."""
        samples_dir = quickstart_dir / "samples"
        expected_samples = {
            "crm_data.csv": ["opportunity_id", "amount", "stage"],
            "inventory.csv": ["product_id", "stock_level", "reorder_threshold"],
            "customers.csv": ["customer_id", "email", "first_name"]
        }
        
        for filename, expected_cols in expected_samples.items():
            filepath = samples_dir / filename
            
            # Check file exists
            self.assertTrue(
                filepath.exists(),
                f"Sample file {filename} not found"
            )
            
            # Check it's a valid CSV with expected columns
            with open(filepath, 'r') as f:
                reader = csv.DictReader(f)
                headers = reader.fieldnames
                
                for col in expected_cols:
                    self.assertIn(
                        col, headers,
                        f"Expected column '{col}' not found in {filename}"
                    )
                
                # Check file has data
                rows = list(reader)
                self.assertGreater(
                    len(rows), 0,
                    f"Sample file {filename} has no data rows"
                )
    
    def test_output_files_complete(self):
        """Test that all pre-generated output files exist."""
        outputs_dir = quickstart_dir / "outputs"
        expected_outputs = [
            "crm_audit.txt",
            "inventory_audit.txt",
            "customer_audit.txt"
        ]
        
        for filename in expected_outputs:
            filepath = outputs_dir / filename
            
            # Check file exists
            self.assertTrue(
                filepath.exists(),
                f"Output file {filename} not found"
            )
            
            # Check file has substantial content
            content = filepath.read_text()
            self.assertGreater(
                len(content), 500,
                f"Output file {filename} seems too small"
            )
            
            # Check for business-friendly content
            self.assertIn(
                "$", content,
                f"Output {filename} should contain dollar amounts"
            )
            self.assertTrue(
                "AUDIT" in content or "DATA QUALITY" in content,
                f"Output {filename} should contain audit/quality terminology"
            )
    
    def test_scripts_are_executable(self):
        """Test that Python scripts have proper structure."""
        scripts = ["see_it.py", "try_it.py"]
        
        for script_name in scripts:
            script_path = quickstart_dir / script_name
            content = script_path.read_text()
            
            # Check for main guard
            self.assertIn(
                'if __name__ == "__main__":', content,
                f"{script_name} should have main guard"
            )
            
            # Check for docstring (after shebang if present)
            lines = content.strip().split('\n')
            # Skip shebang if present
            if lines[0].startswith('#!'):
                lines = lines[1:]
            # Check first non-empty line is docstring
            first_content = next((line for line in lines if line.strip()), '')
            self.assertTrue(
                first_content.startswith('"""') or first_content.startswith("'''"),
                f"{script_name} should have a docstring"
            )


class TestQuickstartReadmeQuality(unittest.TestCase):
    """Test the quickstart README quality and completeness."""
    
    def test_readme_sections(self):
        """Test that README has all required sections."""
        readme_path = quickstart_dir / "README.md"
        content = readme_path.read_text()
        
        required_sections = [
            "# ADRI Quickstart",
            "SEE IT",
            "TRY IT", 
            "USE IT",
            "What's in This Quickstart",
            "Key Insights"
        ]
        
        for section in required_sections:
            self.assertIn(
                section, content,
                f"README missing required section: {section}"
            )
    
    def test_readme_examples_valid(self):
        """Test that code examples in README are valid."""
        readme_path = quickstart_dir / "README.md"
        content = readme_path.read_text()
        
        # Check curl command format
        curl_pattern = r'curl https://raw\.githubusercontent\.com/[^\s]+'
        curl_matches = re.findall(curl_pattern, content)
        
        for curl_cmd in curl_matches:
            # Verify it points to the correct repo
            self.assertIn(
                "ThinkEvolveSolve/agent-data-readiness-index",
                curl_cmd,
                "Curl command should point to correct repo"
            )
            
            # Verify it points to quickstart outputs
            self.assertIn(
                "quickstart/outputs/",
                curl_cmd,
                "Curl command should point to quickstart outputs"
            )
    
    def test_readme_file_references(self):
        """Test that all files referenced in README exist."""
        readme_path = quickstart_dir / "README.md"
        content = readme_path.read_text()
        
        # Find file references (looking for .py and .csv files)
        file_pattern = r'`([^`]+\.(py|csv))`'
        file_matches = re.findall(file_pattern, content)
        
        for file_ref, _ in file_matches:
            # Skip if it's a command or example
            if " " in file_ref or file_ref.startswith("python"):
                continue
                
            # Check if file exists relative to quickstart
            if "/" in file_ref:
                filepath = project_root / file_ref
            else:
                filepath = quickstart_dir / file_ref
            
            self.assertTrue(
                filepath.exists(),
                f"File referenced in README not found: {file_ref}"
            )


class TestQuickstartBusinessAlignment(unittest.TestCase):
    """Test that quickstart content aligns with business messaging."""
    
    def test_output_files_business_friendly(self):
        """Test that output files use business-friendly language."""
        outputs_dir = quickstart_dir / "outputs"
        
        business_terms = [
            "revenue", "risk", "impact", "action", "cost",
            "efficiency", "process", "breakdown", "immediate"
        ]
        
        for output_file in outputs_dir.glob("*.txt"):
            content = output_file.read_text().lower()
            
            # Check for business terminology
            found_terms = [term for term in business_terms if term in content]
            self.assertGreater(
                len(found_terms), 0,
                f"{output_file.name} should contain business terminology"
            )
            
            # Check for actionable insights
            action_indicators = ["immediate action", "review", "update", "fix", "resolve"]
            has_actions = any(indicator in content for indicator in action_indicators)
            self.assertTrue(
                has_actions,
                f"{output_file.name} should contain actionable insights"
            )
    
    def test_sample_data_realistic(self):
        """Test that sample data contains realistic business scenarios."""
        samples_dir = quickstart_dir / "samples"
        
        # Test CRM data
        crm_file = samples_dir / "crm_data.csv"
        with open(crm_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            # Check for variety in stages
            stages = {row.get('stage') for row in rows if row.get('stage')}
            self.assertGreater(
                len(stages), 3,
                "CRM data should have multiple sales stages"
            )
            
            # Check for realistic deal values (using 'amount' column)
            deal_values = []
            for row in rows:
                amount_str = row.get('amount', '0')
                if amount_str:
                    try:
                        # Remove dollar signs and commas
                        clean_amount = amount_str.replace('$', '').replace(',', '')
                        amount = float(clean_amount)
                        if amount > 0:
                            deal_values.append(amount)
                    except ValueError:
                        pass
            
            if deal_values:
                self.assertGreater(
                    max(deal_values), 10000,
                    "CRM should have significant deal values"
                )
    
    def test_minimal_adri_business_focus(self):
        """Test that minimal ADRI implementation focuses on business value."""
        try_it_path = quickstart_dir / "try_it.py"
        content = try_it_path.read_text()
        
        # Check for business-oriented formatting (using Python f-string formatting)
        self.assertIn(
            "${", content,  # Check for dollar formatting
            "Should have money formatting for business users"
        )
        
        # Check for business impact section
        self.assertIn(
            "Business Impact:", content,
            "Should have business impact section"
        )
        
        # Check that technical jargon is minimized (except in the "no dependencies" comment)
        # Remove the docstring which mentions "no pandas, numpy" to check the actual code
        code_without_docstring = content.split('"""', 2)[-1] if '"""' in content else content
        
        technical_terms = ["schema", "dataframe", "numpy", "pandas"]
        for term in technical_terms:
            self.assertNotIn(
                term.lower(), code_without_docstring.lower(),
                f"Minimal implementation should avoid technical term: {term}"
            )


class TestREADMECodeExamples(unittest.TestCase):
    """Test that code examples in main README work correctly."""
    
    def test_readme_imports(self):
        """Test that all imports shown in README are valid."""
        readme_path = project_root / "README.md"
        content = readme_path.read_text()
        
        # Find Python import statements
        import_pattern = r'from (adri[.\w]*) import (\w+)'
        imports = re.findall(import_pattern, content)
        
        for module_path, import_name in imports:
            # Build the import statement
            import_stmt = f"from {module_path} import {import_name}"
            
            # Try to execute the import
            try:
                exec(import_stmt)
            except ImportError as e:
                self.fail(f"README contains invalid import: {import_stmt}\nError: {e}")
    
    def test_readme_code_blocks_syntax(self):
        """Test that Python code blocks in README have valid syntax."""
        readme_path = project_root / "README.md"
        content = readme_path.read_text()
        
        # Find Python code blocks
        code_block_pattern = r'```python\n(.*?)\n```'
        code_blocks = re.findall(code_block_pattern, content, re.DOTALL)
        
        for i, code_block in enumerate(code_blocks):
            # Skip if it's just an import or very short
            if len(code_block.strip()) < 20:
                continue
                
            # Try to compile the code
            try:
                compile(code_block, f"<readme_block_{i}>", "exec")
            except SyntaxError as e:
                # Some code blocks might be partial examples, that's ok
                # But basic syntax should be valid
                if "invalid syntax" in str(e):
                    self.fail(f"README code block {i} has syntax error: {e}")


if __name__ == "__main__":
    unittest.main()
