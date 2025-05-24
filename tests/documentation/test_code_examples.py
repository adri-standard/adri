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

from base_doc_test import BaseDocumentationTest, TestResult
from utils.code_extractor import CodeExtractor, CodeBlock, CodeBlockType


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
        """Determine if a code block should be skipped"""
        code = block.code.strip()
        
        # Skip pseudo-code or placeholder examples
        skip_patterns = [
            '# ... rest of',
            '# TODO:',
            '# Add your',
            '# Your code here',
            '...',  # Ellipsis indicating incomplete code
            'pass  # Implement',
        ]
        
        if any(pattern in code for pattern in skip_patterns):
            return True
        
        # Skip if it's just comments
        non_comment_lines = [line for line in code.split('\n') 
                           if line.strip() and not line.strip().startswith('#')]
        if not non_comment_lines:
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
        """Get setup code needed for the example"""
        setup_lines = [
            "import sys",
            "import os",
            f"sys.path.insert(0, '{self.project_root}')",
            f"os.chdir('{self.test_data_dir}')",
        ]
        
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
        
        return '\n'.join(setup_lines)
    
    def _execute_code_safely(self, code: str, block: CodeBlock) -> TestResult:
        """Execute code in a safe environment with timeout"""
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
