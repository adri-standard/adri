#!/usr/bin/env python3
"""
Error categorization system for batch processing flake8 errors.

Classifies flake8 errors by type, severity, and fix complexity to enable
incremental processing that prevents Cline interface overload.
"""

import re
from enum import Enum
from typing import Dict, List, NamedTuple, Optional


class ErrorSeverity(Enum):
    """Error severity levels for prioritization."""
    CRITICAL = 1    # Syntax errors, undefined variables
    HIGH = 2        # Import issues, logical errors  
    MEDIUM = 3      # Style violations, formatting
    LOW = 4         # Trailing whitespace, blank lines


class ErrorCategory(Enum):
    """Categories of flake8 errors for batch processing."""
    SYNTAX = "syntax"
    UNDEFINED_VARS = "undefined_vars"
    IMPORTS = "imports"
    FORMATTING = "formatting"
    STYLE = "style"
    DOCSTRINGS = "docstrings"
    COMPLEXITY = "complexity"


class FlakeError(NamedTuple):
    """Structured representation of a flake8 error."""
    file_path: str
    line_number: int
    column_number: int
    error_code: str
    error_message: str
    category: ErrorCategory
    severity: ErrorSeverity
    fix_complexity: int  # 1-5 scale, 1=simple, 5=complex


class ErrorCategorizer:
    """Categorizes and prioritizes flake8 errors for batch processing."""
    
    # Error code mappings to categories and severities
    ERROR_MAPPINGS = {
        # Syntax errors - CRITICAL
        'E999': (ErrorCategory.SYNTAX, ErrorSeverity.CRITICAL, 5),
        
        # Undefined variables - CRITICAL
        'F821': (ErrorCategory.UNDEFINED_VARS, ErrorSeverity.CRITICAL, 4),
        'F822': (ErrorCategory.UNDEFINED_VARS, ErrorSeverity.CRITICAL, 4),
        
        # Import issues - HIGH
        'F401': (ErrorCategory.IMPORTS, ErrorSeverity.HIGH, 2),
        'F402': (ErrorCategory.IMPORTS, ErrorSeverity.HIGH, 3),
        'F403': (ErrorCategory.IMPORTS, ErrorSeverity.HIGH, 3),
        'F404': (ErrorCategory.IMPORTS, ErrorSeverity.HIGH, 2),
        'F405': (ErrorCategory.IMPORTS, ErrorSeverity.HIGH, 3),
        'E402': (ErrorCategory.IMPORTS, ErrorSeverity.HIGH, 2),
        
        # Formatting issues - MEDIUM/LOW
        'W291': (ErrorCategory.FORMATTING, ErrorSeverity.LOW, 1),    # trailing whitespace
        'W292': (ErrorCategory.FORMATTING, ErrorSeverity.LOW, 1),    # no newline at end
        'W293': (ErrorCategory.FORMATTING, ErrorSeverity.LOW, 1),    # blank line with whitespace
        'W391': (ErrorCategory.FORMATTING, ErrorSeverity.LOW, 1),    # blank line at end
        
        # Style issues - MEDIUM
        'E501': (ErrorCategory.STYLE, ErrorSeverity.MEDIUM, 2),      # line too long
        'E302': (ErrorCategory.STYLE, ErrorSeverity.MEDIUM, 1),      # expected 2 blank lines
        'E303': (ErrorCategory.STYLE, ErrorSeverity.MEDIUM, 1),      # too many blank lines
        'E261': (ErrorCategory.STYLE, ErrorSeverity.MEDIUM, 1),      # at least two spaces before inline comment
        
        # Docstring issues - MEDIUM
        'D100': (ErrorCategory.DOCSTRINGS, ErrorSeverity.MEDIUM, 2), # missing docstring in public module
        'D101': (ErrorCategory.DOCSTRINGS, ErrorSeverity.MEDIUM, 2), # missing docstring in public class
        'D102': (ErrorCategory.DOCSTRINGS, ErrorSeverity.MEDIUM, 2), # missing docstring in public method
        'D103': (ErrorCategory.DOCSTRINGS, ErrorSeverity.MEDIUM, 2), # missing docstring in public function
        
        # Complexity issues - HIGH
        'C901': (ErrorCategory.COMPLEXITY, ErrorSeverity.HIGH, 4),   # too complex
    }
    
    def __init__(self):
        """Initialize the error categorizer."""
        self.flake8_pattern = re.compile(
            r'^(.+):(\d+):(\d+):\s+([A-Z]\d+)\s+(.+)$'
        )
    
    def parse_flake8_output(self, flake8_output: str) -> List[FlakeError]:
        """
        Parse flake8 output into structured error objects.
        
        Args:
            flake8_output: Raw flake8 command output
            
        Returns:
            List of FlakeError objects
        """
        errors = []
        
        for line in flake8_output.strip().split('\n'):
            if not line.strip():
                continue
                
            match = self.flake8_pattern.match(line.strip())
            if not match:
                continue
                
            file_path, line_num, col_num, error_code, message = match.groups()
            
            # Get category, severity, and complexity from mappings
            category, severity, complexity = self.ERROR_MAPPINGS.get(
                error_code, 
                (ErrorCategory.STYLE, ErrorSeverity.MEDIUM, 2)  # default
            )
            
            error = FlakeError(
                file_path=file_path,
                line_number=int(line_num),
                column_number=int(col_num),
                error_code=error_code,
                error_message=message,
                category=category,
                severity=severity,
                fix_complexity=complexity
            )
            
            errors.append(error)
            
        return errors
    
    def categorize_errors(self, errors: List[FlakeError]) -> Dict[ErrorCategory, List[FlakeError]]:
        """
        Group errors by category for batch processing.
        
        Args:
            errors: List of FlakeError objects
            
        Returns:
            Dictionary mapping categories to error lists
        """
        categorized = {}
        
        for error in errors:
            if error.category not in categorized:
                categorized[error.category] = []
            categorized[error.category].append(error)
            
        return categorized
    
    def prioritize_errors(self, errors: List[FlakeError]) -> List[FlakeError]:
        """
        Sort errors by priority (severity, then complexity, then line number).
        
        Args:
            errors: List of FlakeError objects
            
        Returns:
            Sorted list with highest priority errors first
        """
        return sorted(errors, key=lambda e: (
            e.severity.value,           # Lower number = higher priority
            -e.fix_complexity,          # Higher complexity = higher priority
            e.file_path,                # Alphabetical file ordering
            e.line_number               # Line number ordering
        ))
    
    def get_fix_strategy(self, error: FlakeError) -> str:
        """
        Get recommended fix strategy for an error.
        
        Args:
            error: FlakeError object
            
        Returns:
            String describing fix strategy
        """
        strategies = {
            ErrorCategory.SYNTAX: "Manual review required - syntax error needs careful analysis",
            ErrorCategory.UNDEFINED_VARS: "Check variable definitions and imports",
            ErrorCategory.IMPORTS: "Remove unused imports or reorganize import statements", 
            ErrorCategory.FORMATTING: "Automated fix - remove whitespace or add newlines",
            ErrorCategory.STYLE: "Automated fix - adjust formatting and spacing",
            ErrorCategory.DOCSTRINGS: "Add missing docstrings following project conventions",
            ErrorCategory.COMPLEXITY: "Refactor to reduce complexity - may require code restructuring"
        }
        
        return strategies.get(error.category, "Review and fix according to error message")
    
    def get_batch_size_recommendation(self, category: ErrorCategory) -> int:
        """
        Get recommended batch size for a category of errors.
        
        Args:
            category: ErrorCategory
            
        Returns:
            Recommended number of errors to fix in one batch
        """
        batch_sizes = {
            ErrorCategory.SYNTAX: 1,        # One at a time - complex
            ErrorCategory.UNDEFINED_VARS: 3, # Small batches - medium complexity
            ErrorCategory.IMPORTS: 5,       # Medium batches - simpler
            ErrorCategory.FORMATTING: 15,   # Large batches - very simple
            ErrorCategory.STYLE: 10,        # Medium-large batches - simple
            ErrorCategory.DOCSTRINGS: 5,    # Medium batches - requires thought
            ErrorCategory.COMPLEXITY: 2,    # Small batches - complex
        }
        
        return batch_sizes.get(category, 5)  # default batch size


def main():
    """Demo function for testing the categorizer."""
    import subprocess
    
    # Get flake8 output
    try:
        result = subprocess.run(
            ['python', '-m', 'flake8', '--config=development/config/.flake8', '.'],
            capture_output=True,
            text=True,
            cwd='.'
        )
        flake8_output = result.stdout
    except Exception as e:
        print(f"Error running flake8: {e}")
        return
    
    # Categorize errors
    categorizer = ErrorCategorizer()
    errors = categorizer.parse_flake8_output(flake8_output)
    
    print(f"Found {len(errors)} total errors")
    print("\nError Summary by Category:")
    
    categorized = categorizer.categorize_errors(errors)
    for category, error_list in categorized.items():
        print(f"  {category.value}: {len(error_list)} errors")
        batch_size = categorizer.get_batch_size_recommendation(category)
        print(f"    Recommended batch size: {batch_size}")
    
    print("\nTop 5 Priority Errors:")
    prioritized = categorizer.prioritize_errors(errors)
    for i, error in enumerate(prioritized[:5]):
        print(f"  {i+1}. {error.file_path}:{error.line_number} - {error.error_code}: {error.error_message}")
        print(f"     Severity: {error.severity.name}, Strategy: {categorizer.get_fix_strategy(error)}")


if __name__ == "__main__":
    main()
