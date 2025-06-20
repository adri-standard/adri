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
    audience: str = "AI_BUILDER"  # Default to AI_BUILDER audience
    
    
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
        
        # Extract code blocks from within docstrings
        docstring_blocks = CodeExtractor._extract_docstring_code_blocks(content, filepath)
        code_blocks.extend(docstring_blocks)
        
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
                nested_backticks = 0
                while i < len(lines):
                    if lines[i].strip().startswith('```'):
                        if nested_backticks > 0:
                            # This is a closing backtick for a nested code block
                            nested_backticks -= 1
                            code_lines.append(lines[i])
                        else:
                            # This is the closing backtick for our code block
                            break
                    elif '```' in lines[i].strip() and not lines[i].strip().startswith('```'):
                        # This might be a nested code block start
                        nested_backticks += 1
                        code_lines.append(lines[i])
                    else:
                        code_lines.append(lines[i])
                    i += 1
                
                if code_lines and language.lower() in ['python', 'py']:
                    code = '\n'.join(code_lines)
                    block_type = CodeExtractor._classify_code_block(code)
                    
                    # Detect audience tag
                    audience = CodeExtractor._detect_audience_tag(code)
                    
                    blocks.append(CodeBlock(
                        code=code,
                        language=language,
                        line_number=start_line,
                        block_type=block_type,
                        context=context,
                        file_path=filepath,
                        audience=audience
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
                    
                    # Detect audience tag
                    audience = CodeExtractor._detect_audience_tag(code)
                    
                    blocks.append(CodeBlock(
                        code=code,
                        language='python',
                        line_number=start_line,
                        block_type=CodeBlockType.INTERACTIVE,
                        context=context,
                        file_path=filepath,
                        audience=audience
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
            elif len(lines) > 1 and has_imports:
                # If it has imports and multiple lines, it's a snippet
                return CodeBlockType.SNIPPET
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
    def _extract_docstring_code_blocks(content: str, filepath: str) -> List[CodeBlock]:
        """Extract code blocks that are nested within docstrings"""
        blocks = []
        lines = content.split('\n')
        
        # Find function definitions with docstrings
        i = 0
        while i < len(lines):
            if lines[i].strip().startswith('def ') and i+1 < len(lines):
                # Found a function definition, look for docstring
                func_line = i
                docstring_start = None
                docstring_end = None
                
                # Look for docstring start
                j = i + 1
                while j < len(lines) and docstring_start is None:
                    if '"""' in lines[j] or "'''" in lines[j]:
                        docstring_start = j
                    elif not lines[j].strip().startswith((' ', '\t')) and lines[j].strip():
                        # If we hit a non-indented line that's not empty, we're out of the function
                        break
                    j += 1
                
                if docstring_start is not None:
                    # Found docstring start, now find docstring end
                    quote_type = '"""' if '"""' in lines[docstring_start] else "'''"
                    j = docstring_start + 1
                    while j < len(lines) and docstring_end is None:
                        if quote_type in lines[j]:
                            docstring_end = j
                        elif not lines[j].strip().startswith((' ', '\t')) and lines[j].strip():
                            # If we hit a non-indented line that's not empty, we're out of the function
                            break
                        j += 1
                    
                    if docstring_start is not None and docstring_end is not None:
                        # Now look for code blocks within the docstring
                        docstring_lines = lines[docstring_start:docstring_end+1]
                        in_code_block = False
                        code_block_start = None
                        code_block_lines = []
                        language = None
                        
                        for k, line in enumerate(docstring_lines):
                            if '```' in line and not in_code_block:
                                # Start of code block
                                in_code_block = True
                                code_block_start = k + docstring_start
                                match = re.search(r'```(\w*)', line.strip())
                                language = match.group(1) if match else 'text'
                                continue
                            elif '```' in line and in_code_block:
                                # End of code block
                                in_code_block = False
                                if code_block_lines and language and language.lower() in ['python', 'py']:
                                    # Get context (function name and docstring description)
                                    context = lines[func_line].strip()
                                    if docstring_start + 1 < code_block_start:
                                        # Add first line of docstring as context if available
                                        first_doc_line = lines[docstring_start + 1].strip().strip('"""').strip("'''").strip()
                                        if first_doc_line:
                                            context += " - " + first_doc_line
                                    
                                    code = '\n'.join(code_block_lines)
                                    block_type = CodeExtractor._classify_code_block(code)
                                    
                                    # Detect audience tag
                                    audience = CodeExtractor._detect_audience_tag(code)
                                    
                                    blocks.append(CodeBlock(
                                        code=code,
                                        language=language,
                                        line_number=code_block_start + 1,
                                        block_type=block_type,
                                        context=context,
                                        file_path=filepath,
                                        audience=audience
                                    ))
                                code_block_lines = []
                                continue
                            
                            if in_code_block:
                                # Inside code block, collect lines
                                # Remove common indentation from docstring
                                stripped_line = line.lstrip()
                                if stripped_line:  # Only process non-empty lines
                                    code_block_lines.append(stripped_line)
            i += 1
        
        return blocks
    
    @staticmethod
    def _detect_audience_tag(code: str) -> str:
        """Detect audience tag in code block"""
        # Look for audience tags in the first 5 lines
        lines = code.split('\n')[:5]
        
        # Define audience tag patterns
        audience_patterns = {
            r'#\s*\[AI_BUILDER\]': "AI_BUILDER",
            r'#\s*\[STANDARD_CONTRIBUTOR\]': "STANDARD_CONTRIBUTOR",
            r'#\s*\[DATA_PROVIDER\]': "DATA_PROVIDER"
        }
        
        # Check for audience tags
        for line in lines:
            for pattern, audience in audience_patterns.items():
                if re.search(pattern, line):
                    return audience
        
        # Default to AI_BUILDER if no tag is found
        return "AI_BUILDER"
    
    @staticmethod
    def prepare_code_for_execution(block: CodeBlock) -> str:
        """Prepare code block for safe execution"""
        code = block.code.strip()
        
        # Skip docstrings with incomplete triple quotes
        if code.startswith('def ') and '"""' in code:
            # Check if the docstring is properly closed
            if code.count('"""') < 2:
                # This is an incomplete docstring, add a closing triple quote
                code += '\n    """'
        
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
