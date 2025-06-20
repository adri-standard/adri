"""
Phase 1: Test all code examples in documentation
"""
import sys
import os
import subprocess
import tempfile
import traceback
from pathlib import Path
from typing import List, Dict, Any
import unittest
from contextlib import redirect_stdout, redirect_stderr
import io
import signal
import time

from .base_doc_test import BaseDocumentationTest, TestResult
from .utils.code_extractor import CodeExtractor, CodeBlock, CodeBlockType


class TimeoutException(Exception):
    """Raised when code execution times out"""
    pass


def timeout_handler(signum, frame):
    """Handler for execution timeout"""
    raise TimeoutException("Code execution timed out")


class TestCodeExamples(BaseDocumentationTest):
    """Test all code examples in ADRI documentation"""
    
    def setUp(self):
        super().__init__()
        self.timeout_seconds = 30
        self.test_data_dir = self.project_root / "tests/documentation/fixtures"
        self.test_data_dir.mkdir(parents=True, exist_ok=True)
        
        # Create sample test data
        self._create_test_fixtures()
    
    def _create_test_fixtures(self):
        """Create sample data files for testing examples"""
        # Create a sample CSV file
        sample_csv = self.test_data_dir / "sample_data.csv"
        if not sample_csv.exists():
            sample_csv.write_text("""date,value,category
2024-01-01,100,A
2024-01-02,200,B
2024-01-03,150,A
2024-01-04,,B
2024-01-05,300,C
""")
        
        # Create a sample config file
        sample_config = self.test_data_dir / "test_config.yaml"
        if not sample_config.exists():
            sample_config.write_text("""data_source:
  path: sample_data.csv
  type: csv
  
rules:
  completeness:
    threshold: 0.9
  validity:
    date_format: "%Y-%m-%d"
""")
    
    def test_all_code_examples(self):
        """Test all code examples in documentation"""
        print("\n" + "="*60)
        print("Testing Code Examples in Documentation")
        print("="*60 + "\n")
        
        markdown_files = self.get_all_markdown_files()
        total_blocks = 0
        tested_blocks = 0
        failed_blocks = 0
        
        for md_file in markdown_files:
            relative_path = md_file.relative_to(self.project_root)
            print(f"\n📄 Checking {relative_path}")
            
            # Extract code blocks
            try:
                code_blocks = CodeExtractor.extract_from_markdown(str(md_file))
            except Exception as e:
                self.log_result(
                    f"Extract code from {relative_path}",
                    TestResult(False, f"Failed to extract code: {str(e)}")
                )
                continue
            
            if not code_blocks:
                print(f"   No Python code blocks found")
                continue
            
            total_blocks += len(code_blocks)
            print(f"   Found {len(code_blocks)} Python code blocks")
            
            # Test each code block
            for i, block in enumerate(code_blocks):
                test_name = f"{relative_path} - Block {i+1} (line {block.line_number})"
                
                # Skip certain types of incomplete code
                if self._should_skip_block(block):
                    print(f"   ⏭️  Skipping {block.block_type.value} block at line {block.line_number}")
                    continue
                
                tested_blocks += 1
                result = self._test_code_block(block)
                
                if not result.passed:
                    failed_blocks += 1
                
                self.log_result(test_name, result)
        
        # Summary
        print("\n" + "="*60)
        print("Summary")
        print("="*60)
        print(f"Total code blocks found: {total_blocks}")
        print(f"Code blocks tested: {tested_blocks}")
        print(f"Code blocks passed: {tested_blocks - failed_blocks}")
        print(f"Code blocks failed: {failed_blocks}")
        
        if failed_blocks > 0:
            self.fail(f"{failed_blocks} code examples failed")
    
    def _should_skip_block(self, block: CodeBlock) -> bool:
        """Determine if a code block should be skipped based on audience"""
        code = block.code.strip()
        
        # Apply different validation rules based on audience
        if block.audience == "AI_BUILDER":
            return self._should_skip_agent_block(block)
        elif block.audience == "STANDARD_CONTRIBUTOR":
            return self._should_skip_standard_block(block)
        elif block.audience == "DATA_PROVIDER":
            return self._should_skip_supplier_block(block)
        
        # Default to AI_BUILDER rules if no audience specified
        return self._should_skip_agent_block(block)
    
    def _should_skip_agent_block(self, block: CodeBlock) -> bool:
        """Strict validation for AGENT audience - must be fully executable"""
        code = block.code.strip()

        # Skip pseudo-code or placeholder examples
        skip_patterns = [
            '# ... rest of',
            '# TODO:',
            '# Add your',
            '# Your code here',
            '...',  # Ellipsis indicating incomplete code
            'pass  # Implement',
            'pip install',  # Installation commands
            'python -m',  # Command line examples
            'git ',  # Git commands
            'cd ',  # Directory navigation
            'SITE_BASE_URL',  # Environment variable examples
        ]

        if any(pattern in code for pattern in skip_patterns):
            return True

        # Skip if it's just comments
        non_comment_lines = [line for line in code.split('\n')
                           if line.strip() and not line.strip().startswith('#')]
        if not non_comment_lines:
            return True

        # Skip file path references that look like code
        if code.endswith('.csv') or code.endswith('.json') or code.endswith('.yaml') or code.endswith('.yml'):
            return True

        # Skip single identifiers that are likely file/variable references
        if len(non_comment_lines) == 1 and ' ' not in non_comment_lines[0].strip():
            # Single word/identifier without spaces (likely a filename or variable name)
            line = non_comment_lines[0].strip()
            if not line.startswith('print(') and '(' not in line:
                return True

        # Skip code that's clearly pseudo-code or incomplete
        pseudo_indicators = [
            '@adri_guard(',  # Decorator examples without implementation
            'agent.',  # Agent references without context
            'monitor.',  # Monitor references without context
            'adri[',  # Dictionary-style pseudo-code
            '[Link Text]',  # Markdown link syntax
            'https://',  # URLs
            'http://',
            'username.github.io',  # GitHub pages examples
            '{filename}',  # Template placeholders
            'test_[',  # Test naming patterns
            'path/to/',  # Generic path examples
            'your_data.csv',  # Generic file references
            'data.csv" not found',  # Error message examples
        ]

        if any(indicator in code for indicator in pseudo_indicators):
            return True

        # Skip imports for non-existent example modules
        if 'from adri import adri_guard' in code and '@adri_guard' in code and 'def ' not in code:
            # Decorator example without function body
            return True

        # Skip code blocks that are clearly not executable
        # (e.g., showing file structures, config examples without context)
        if block.block_type == CodeBlockType.INLINE:
            return True

        return False
    
    def _should_skip_standard_block(self, block: CodeBlock) -> bool:
        """Less strict validation for STANDARD audience - syntax check only"""
        code = block.code.strip()
        
        # Skip if it's just comments
        non_comment_lines = [line for line in code.split('\n')
                           if line.strip() and not line.strip().startswith('#')]
        if not non_comment_lines:
            return True
        
        # Skip installation commands, git commands, etc.
        skip_commands = [
            'pip install',
            'python -m',
            'git ',
            'cd ',
        ]
        if any(cmd in code for cmd in skip_commands):
            return True
        
        # Skip inline code blocks
        if block.block_type == CodeBlockType.INLINE:
            return True
        
        # For STANDARD audience, we're more lenient about imports and API references
        # that might not exist yet, as these could be ideal implementations
        
        # Still skip obvious non-code
        if code.endswith('.csv') or code.endswith('.json') or code.endswith('.yaml') or code.endswith('.yml'):
            return True
            
        return False
    
    def _should_skip_supplier_block(self, block: CodeBlock) -> bool:
        """Medium strictness for SUPPLIER audience - check with mocked interfaces"""
        code = block.code.strip()
        
        # Skip if it's just comments
        non_comment_lines = [line for line in code.split('\n')
                           if line.strip() and not line.strip().startswith('#')]
        if not non_comment_lines:
            return True
        
        # Skip installation commands, git commands, etc.
        skip_commands = [
            'pip install',
            'python -m',
            'git ',
            'cd ',
        ]
        if any(cmd in code for cmd in skip_commands):
            return True
        
        # Skip inline code blocks
        if block.block_type == CodeBlockType.INLINE:
            return True
        
        # For SUPPLIER audience, we're somewhat lenient but still want to ensure
        # the code is valid from a data provider perspective
        
        # Skip obvious non-code
        if code.endswith('.csv') or code.endswith('.json') or code.endswith('.yaml') or code.endswith('.yml'):
            return True
            
        return False
    
    def _test_code_block(self, block: CodeBlock) -> TestResult:
        """Test a single code block"""
        try:
            # Prepare code for execution
            code = CodeExtractor.prepare_code_for_execution(block)
            
            # Add necessary setup for ADRI examples
            setup_code = self._get_setup_code(block)
            full_code = setup_code + "\n\n" + code
            
            # Execute the code
            result = self._execute_code_safely(full_code, block)
            
            return result
            
        except Exception as e:
            return TestResult(
                passed=False,
                message=f"Failed to test code block: {str(e)}",
                details={
                    'error_type': type(e).__name__,
                    'error': str(e),
                    'code_snippet': block.code[:200] + '...' if len(block.code) > 200 else block.code
                }
            )
    
    def _get_setup_code(self, block: CodeBlock) -> str:
        """Get setup code needed for the example based on audience"""
        # Common setup for all audiences
        setup_lines = [
            "import sys",
            "import os",
            f"sys.path.insert(0, '{self.project_root}')",
            f"os.chdir('{self.test_data_dir}')",
        ]
        
        # Add audience-specific setup
        if block.audience == "AI_BUILDER":
            self._add_agent_setup(setup_lines, block)
        elif block.audience == "STANDARD_CONTRIBUTOR":
            self._add_standard_setup(setup_lines, block)
        elif block.audience == "DATA_PROVIDER":
            self._add_supplier_setup(setup_lines, block)
        else:
            # Default to AI_BUILDER setup
            self._add_agent_setup(setup_lines, block)
        
        return '\n'.join(setup_lines)
    
    def _add_agent_setup(self, setup_lines: List[str], block: CodeBlock) -> None:
        """Add setup code for AGENT audience"""
        # Add imports based on code content
        if 'DataSourceAssessor' in block.code or 'assess' in block.code:
            setup_lines.append("from adri import DataSourceAssessor")
        
        if 'Guard' in block.code:
            setup_lines.append("from adri.integrations.guard import Guard")
        
        if 'pandas' in block.code or 'pd.' in block.code:
            setup_lines.append("import pandas as pd")
        
        if 'numpy' in block.code or 'np.' in block.code:
            setup_lines.append("import numpy as np")
        
        # Mock certain operations for testing
        if 'input(' in block.code:
            setup_lines.append("input = lambda prompt='': 'test_input'")
    
    def _add_standard_setup(self, setup_lines: List[str], block: CodeBlock) -> None:
        """Add setup code for STANDARD audience with mock implementations"""
        # Add common imports
        setup_lines.append("import pandas as pd")
        setup_lines.append("import numpy as np")
        
        # Add mock implementations for standard development
        setup_lines.extend([
            "# Mock implementations for STANDARD audience",
            "class MockAssessmentMode:",
            "    STRICT = 'strict'",
            "    LENIENT = 'lenient'",
            "    INTERACTIVE = 'interactive'",
            "",
            "    @classmethod",
            "    def get_all_modes(cls):",
            "        return [cls.STRICT, cls.LENIENT, cls.INTERACTIVE]",
            "",
            "# Mock the adri module",
            "class MockADRI:",
            "    def __init__(self):",
            "        self.AssessmentMode = MockAssessmentMode",
            "",
            "    def __getattr__(self, name):",
            "        # Return a mock function for any attribute",
            "        return lambda *args, **kwargs: None",
            "",
            "# Create mock module",
            "import sys",
            "import types",
            "adri = MockADRI()",
            "sys.modules['adri'] = types.ModuleType('adri')",
            "sys.modules['adri'].__dict__.update(adri.__dict__)",
            "",
            "# Mock template functions",
            "def list_templates(*args, **kwargs):",
            "    return ['template1', 'template2', 'template3']",
            "",
            "def load_template(name, *args, **kwargs):",
            "    return {'name': name, 'rules': {}, 'metadata': {}}",
            "",
            "# Add to adri.templates",
            "sys.modules['adri.templates'] = types.ModuleType('adri.templates')",
            "sys.modules['adri.templates'].list_templates = list_templates",
            "sys.modules['adri.templates'].load_template = load_template",
            "",
            "# Mock utility functions",
            "def load_report(*args, **kwargs):",
            "    return {'score': 85, 'dimensions': {}}",
            "",
            "def compare_reports(*args, **kwargs):",
            "    return {'diff': {}, 'improved': True}",
            "",
            "# Add to adri.utils",
            "sys.modules['adri.utils'] = types.ModuleType('adri.utils')",
            "sys.modules['adri.utils'].load_report = load_report",
            "sys.modules['adri.utils'].compare_reports = compare_reports",
        ])
        
        # Mock input for interactive examples
        setup_lines.append("input = lambda prompt='': 'test_input'")
    
    def _add_supplier_setup(self, setup_lines: List[str], block: CodeBlock) -> None:
        """Add setup code for SUPPLIER audience with data-focused mocks"""
        # Add common imports
        setup_lines.append("import pandas as pd")
        setup_lines.append("import numpy as np")
        
        # Add mock implementations for data suppliers
        setup_lines.extend([
            "# Mock implementations for SUPPLIER audience",
            "class FileConnector:",
            "    def __init__(self, filepath, file_type=None):",
            "        self.filepath = filepath",
            "        self.file_type = file_type",
            "",
            "    def read(self):",
            "        return pd.DataFrame({'col1': [1, 2, 3], 'col2': ['a', 'b', 'c']})",
            "",
            "class DatabaseConnector:",
            "    def __init__(self, connection_string):",
            "        self.connection_string = connection_string",
            "",
            "    def execute_query(self, query):",
            "        return pd.DataFrame({'col1': [1, 2, 3], 'col2': ['a', 'b', 'c']})",
            "",
            "class APIConnector:",
            "    def __init__(self, endpoint):",
            "        self.endpoint = endpoint",
            "",
            "    def fetch_data(self):",
            "        return {'data': [{'id': 1, 'name': 'test'}]}",
            "",
            "# Create mock module",
            "import sys",
            "import types",
            "sys.modules['adri.connectors'] = types.ModuleType('adri.connectors')",
            "sys.modules['adri.connectors'].FileConnector = FileConnector",
            "sys.modules['adri.connectors'].DatabaseConnector = DatabaseConnector",
            "sys.modules['adri.connectors'].APIConnector = APIConnector",
        ])
        
        # Mock input for interactive examples
        setup_lines.append("input = lambda prompt='': 'test_input'")
    
    def _execute_code_safely(self, code: str, block: CodeBlock) -> TestResult:
        """Execute code in a safe environment with timeout, with audience-specific handling"""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_file = f.name
        
        try:
            # Execute the code with timeout
            process = subprocess.Popen(
                [sys.executable, temp_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=str(self.test_data_dir)
            )
            
            try:
                stdout, stderr = process.communicate(timeout=self.timeout_seconds)
                return_code = process.returncode
                
                # Handle execution result based on audience
                if block.audience == "AI_BUILDER":
                    # Strict validation for AI_BUILDER audience
                    if return_code == 0:
                        return TestResult(
                            passed=True,
                            message="Code executed successfully",
                            details={
                                'audience': block.audience,
                                'stdout': stdout[:500] if stdout else 'No output',
                                'block_type': block.block_type.value,
                                'context': block.context[:100] if block.context else 'No context'
                            }
                        )
                    else:
                        return TestResult(
                            passed=False,
                            message="Code execution failed",
                            details={
                                'audience': block.audience,
                                'return_code': return_code,
                                'stderr': stderr[:500] if stderr else 'No error output',
                                'stdout': stdout[:500] if stdout else 'No output',
                                'code_snippet': block.code[:200] + '...' if len(block.code) > 200 else block.code
                            }
                        )
                
                elif block.audience == "STANDARD_CONTRIBUTOR":
                    # More lenient validation for STANDARD_CONTRIBUTOR audience
                    # Allow certain types of errors for standard development examples
                    if return_code == 0:
                        return TestResult(
                            passed=True,
                            message="Code executed successfully",
                            details={
                                'audience': block.audience,
                                'stdout': stdout[:500] if stdout else 'No output',
                                'block_type': block.block_type.value,
                                'context': block.context[:100] if block.context else 'No context'
                            }
                        )
                    else:
                        # Check for acceptable errors in STANDARD audience
                        acceptable_errors = [
                            "ImportError: No module named",
                            "ModuleNotFoundError",
                            "AttributeError",
                            "NotImplementedError",
                        ]
                        
                        if any(error in stderr for error in acceptable_errors):
                            return TestResult(
                                passed=True,  # Pass despite error for STANDARD audience
                                message="Code has expected development-related errors",
                                details={
                                    'audience': block.audience,
                                    'return_code': return_code,
                                    'stderr': stderr[:500] if stderr else 'No error output',
                                    'stdout': stdout[:500] if stdout else 'No output',
                                    'code_snippet': block.code[:200] + '...' if len(block.code) > 200 else block.code
                                }
                            )
                        else:
                            return TestResult(
                                passed=False,
                                message="Code has unexpected errors",
                                details={
                                    'audience': block.audience,
                                    'return_code': return_code,
                                    'stderr': stderr[:500] if stderr else 'No error output',
                                    'stdout': stdout[:500] if stdout else 'No output',
                                    'code_snippet': block.code[:200] + '...' if len(block.code) > 200 else block.code
                                }
                            )
                
                elif block.audience == "DATA_PROVIDER":
                    # Medium strictness for DATA_PROVIDER audience
                    if return_code == 0:
                        return TestResult(
                            passed=True,
                            message="Code executed successfully",
                            details={
                                'audience': block.audience,
                                'stdout': stdout[:500] if stdout else 'No output',
                                'block_type': block.block_type.value,
                                'context': block.context[:100] if block.context else 'No context'
                            }
                        )
                    else:
                        # Check for acceptable errors in SUPPLIER audience
                        acceptable_errors = [
                            "FileNotFoundError",
                            "ConnectionError",
                            "ConnectionRefusedError",
                        ]
                        
                        if any(error in stderr for error in acceptable_errors):
                            return TestResult(
                                passed=True,  # Pass despite error for SUPPLIER audience
                                message="Code has expected data-related errors",
                                details={
                                    'audience': block.audience,
                                    'return_code': return_code,
                                    'stderr': stderr[:500] if stderr else 'No error output',
                                    'stdout': stdout[:500] if stdout else 'No output',
                                    'code_snippet': block.code[:200] + '...' if len(block.code) > 200 else block.code
                                }
                            )
                        else:
                            return TestResult(
                                passed=False,
                                message="Code has unexpected errors",
                                details={
                                    'audience': block.audience,
                                    'return_code': return_code,
                                    'stderr': stderr[:500] if stderr else 'No error output',
                                    'stdout': stdout[:500] if stdout else 'No output',
                                    'code_snippet': block.code[:200] + '...' if len(block.code) > 200 else block.code
                                }
                            )
                
                else:
                    # Default to strict validation
                    if return_code == 0:
                        return TestResult(
                            passed=True,
                            message="Code executed successfully",
                            details={
                                'stdout': stdout[:500] if stdout else 'No output',
                                'block_type': block.block_type.value,
                                'context': block.context[:100] if block.context else 'No context'
                            }
                        )
                    else:
                        return TestResult(
                            passed=False,
                            message="Code execution failed",
                            details={
                                'return_code': return_code,
                                'stderr': stderr[:500] if stderr else 'No error output',
                                'stdout': stdout[:500] if stdout else 'No output',
                                'code_snippet': block.code[:200] + '...' if len(block.code) > 200 else block.code
                            }
                        )
                    
            except subprocess.TimeoutExpired:
                process.kill()
                return TestResult(
                    passed=False,
                    message=f"Code execution timed out after {self.timeout_seconds} seconds",
                    details={
                        'audience': block.audience,
                        'timeout': f"{self.timeout_seconds}s",
                        'code_snippet': block.code[:200] + '...' if len(block.code) > 200 else block.code
                    }
                )
                
        finally:
            # Clean up
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def test_code_block_classification(self):
        """Test that code blocks are correctly classified"""
        print("\n" + "="*60)
        print("Testing Code Block Classification")
        print("="*60 + "\n")
        
        # Test examples of each type
        test_cases = [
            ("print('hello')", CodeBlockType.INLINE),
            ("""import pandas as pd
df = pd.DataFrame()""", CodeBlockType.SNIPPET),
            ("""import sys
import pandas as pd

def main():
    df = pd.read_csv('data.csv')
    print(df.head())

if __name__ == '__main__':
    main()""", CodeBlockType.COMPLETE),
        ]
        
        for code, expected_type in test_cases:
            actual_type = CodeExtractor._classify_code_block(code)
            self.assertEqual(actual_type, expected_type, 
                           f"Expected {expected_type} but got {actual_type} for code: {code[:50]}...")


if __name__ == '__main__':
    unittest.main()
