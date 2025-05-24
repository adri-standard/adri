"""
Code extraction utilities for documentation testing
"""
import re
import ast
import textwrap
from typing import List, Tuple, Dict, Optional
from enum import Enum
from dataclasses import dataclass


class CodeBlockType(Enum):
    """Types of code blocks found in documentation"""
    INLINE = "inline"          # Single line or expression
    SNIPPET = "snippet"        # Partial code example
    COMPLETE = "complete"      # Full runnable script
    INTERACTIVE = "interactive" # >>> style examples
    

@dataclass
class CodeBlock:
    """Container for extracted code block"""
    code: str
    language: str
    line_number: int
    block_type: CodeBlockType
    context: str  # Surrounding text for context
    file_path: str
    
    
class CodeExtractor:
    """Extract and classify code blocks from markdown documentation"""
    
    @staticmethod
    def extract_from_markdown(filepath: str) -> List[CodeBlock]:
        """Extract all code blocks from a markdown file"""
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        code_blocks = []
        
        # Extract fenced code blocks
        fenced_blocks = CodeExtractor._extract_fenced_blocks(content, filepath)
        code_blocks.extend(fenced_blocks)
        
        # Extract inline code
        inline_blocks = CodeExtractor._extract_inline_code(content, filepath)
        code_blocks.extend(inline_blocks)
        
        # Extract interactive examples
        interactive_blocks = CodeExtractor._extract_interactive_examples(content, filepath)
        code_blocks.extend(interactive_blocks)
        
        return code_blocks
    
    @staticmethod
    def _extract_fenced_blocks(content: str, filepath: str) -> List[CodeBlock]:
        """Extract ```language ... ``` blocks"""
        blocks = []
        lines = content.split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Check for code block start
            match = re.match(r'^```(\w*)', line.strip())
            if match:
                language = match.group(1) or 'text'
                start_line = i + 1
                code_lines = []
                i += 1
                
                # Get context (previous non-empty line)
                context = ""
                for j in range(i-2, max(0, i-10), -1):
                    if lines[j].strip() and not lines[j].strip().startswith('```'):
                        context = lines[j].strip()
                        break
                
                # Collect code until closing ```
                while i < len(lines) and not lines[i].strip().startswith('```'):
                    code_lines.append(lines[i])
                    i += 1
                
                if code_lines and language.lower() in ['python', 'py']:
                    code = '\n'.join(code_lines)
                    block_type = CodeExtractor._classify_code_block(code)
                    
                    blocks.append(CodeBlock(
                        code=code,
                        language=language,
                        line_number=start_line,
                        block_type=block_type,
                        context=context,
                        file_path=filepath
                    ))
            i += 1
        
        return blocks
    
    @staticmethod
    def _extract_inline_code(content: str, filepath: str) -> List[CodeBlock]:
        """Extract `code` inline blocks that look like Python"""
        blocks = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            # Find inline code blocks
            inline_matches = re.findall(r'`([^`]+)`', line)
            
            for code in inline_matches:
                # Check if it looks like Python code
                if CodeExtractor._looks_like_python(code):
                    blocks.append(CodeBlock(
                        code=code,
                        language='python',
                        line_number=i + 1,
                        block_type=CodeBlockType.INLINE,
                        context=line.strip(),
                        file_path=filepath
                    ))
        
        return blocks
    
    @staticmethod
    def _extract_interactive_examples(content: str, filepath: str) -> List[CodeBlock]:
        """Extract >>> style interactive examples"""
        blocks = []
        lines = content.split('\n')
        
        i = 0
        while i < len(lines):
            if lines[i].strip().startswith('>>>'):
                # Start of interactive example
                start_line = i + 1
                example_lines = []
                context = ""
                
                # Get context
                for j in range(i-1, max(0, i-5), -1):
                    if lines[j].strip() and not lines[j].strip().startswith(('>>>', '...')):
                        context = lines[j].strip()
                        break
                
                # Collect all >>> and ... lines
                while i < len(lines) and (
                    lines[i].strip().startswith('>>>') or 
                    lines[i].strip().startswith('...') or
                    (i > 0 and lines[i-1].strip().startswith(('>>>', '...')) and lines[i].strip())
                ):
                    example_lines.append(lines[i])
                    i += 1
                
                if example_lines:
                    # Convert interactive to runnable code
                    code = CodeExtractor._interactive_to_runnable(example_lines)
                    
                    blocks.append(CodeBlock(
                        code=code,
                        language='python',
                        line_number=start_line,
                        block_type=CodeBlockType.INTERACTIVE,
                        context=context,
                        file_path=filepath
                    ))
            else:
                i += 1
        
        return blocks
    
    @staticmethod
    def _classify_code_block(code: str) -> CodeBlockType:
        """Classify the type of code block"""
        lines = [line for line in code.strip().split('\n') if line.strip()]
        
        if not lines:
            return CodeBlockType.INLINE
        
        # Check if it's a complete script
        try:
            # Try to parse as complete Python code
            ast.parse(code)
            
            # Check for common complete script indicators
            has_imports = any(line.strip().startswith(('import ', 'from ')) for line in lines)
            has_main = '__main__' in code
            has_functions = 'def ' in code
            has_classes = 'class ' in code
            
            if has_main or (has_imports and (has_functions or has_classes)):
                return CodeBlockType.COMPLETE
            elif len(lines) > 5:
                return CodeBlockType.SNIPPET
            else:
                return CodeBlockType.INLINE
                
        except SyntaxError:
            # If it doesn't parse, it's likely a snippet
            return CodeBlockType.SNIPPET
    
    @staticmethod
    def _looks_like_python(code: str) -> bool:
        """Check if a piece of code looks like Python"""
        python_keywords = [
            'import', 'from', 'def', 'class', 'if', 'else', 'elif',
            'for', 'while', 'return', 'yield', 'lambda', 'with',
            'try', 'except', 'finally', 'raise', 'assert'
        ]
        
        python_builtins = [
            'print', 'len', 'range', 'list', 'dict', 'set', 'tuple',
            'str', 'int', 'float', 'bool', 'open', 'file'
        ]
        
        # Check for Python-like syntax
        if any(keyword in code for keyword in python_keywords):
            return True
        
        if any(builtin in code for builtin in python_builtins):
            return True
        
        # Check for common Python patterns
        patterns = [
            r'^\s*\w+\s*=\s*',  # Variable assignment
            r'^\s*\w+\(',       # Function call
            r'\w+\.\w+',        # Attribute access
            r'\[.*\]',          # List notation
            r'\{.*\}',          # Dict/set notation
            r':\s*$',           # Colon ending (for blocks)
        ]
        
        return any(re.search(pattern, code) for pattern in patterns)
    
    @staticmethod
    def _interactive_to_runnable(lines: List[str]) -> str:
        """Convert interactive >>> examples to runnable code"""
        code_lines = []
        
        for line in lines:
            if line.strip().startswith('>>>'):
                # Remove >>> and add the code
                code_lines.append(line.replace('>>>', '', 1).lstrip())
            elif line.strip().startswith('...'):
                # Remove ... and add the code (continuation)
                code_lines.append(line.replace('...', '', 1).lstrip())
            elif line.strip() and not line.strip().startswith(('>>>', '...')):
                # This is output - add as a comment
                code_lines.append(f"# Expected output: {line.strip()}")
        
        return '\n'.join(code_lines)
    
    @staticmethod
    def prepare_code_for_execution(block: CodeBlock) -> str:
        """Prepare code block for safe execution"""
        code = block.code.strip()
        
        # For inline code, we might need to add print statements
        if block.block_type == CodeBlockType.INLINE:
            # If it's just an expression, print it
            if not any(keyword in code for keyword in ['=', 'import', 'from', 'def', 'class']):
                code = f"print({code})"
        
        # For snippets, we might need to add imports
        elif block.block_type == CodeBlockType.SNIPPET:
            # Check if ADRI imports are needed
            if any(term in code for term in ['DataSourceAssessor', 'Guard', 'adri']):
                if 'import adri' not in code and 'from adri' not in code:
                    code = "from adri import *\n\n" + code
        
        return code
