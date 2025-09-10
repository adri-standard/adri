#!/usr/bin/env python3
"""Enhanced commit message validator with helpful error messages and suggestions."""

import re
import sys
from typing import List, Tuple, Optional


class CommitMessageValidator:
    """Validates commit messages with enhanced error reporting."""
    
    # Valid conventional commit types
    VALID_TYPES = [
        'feat', 'fix', 'docs', 'style', 'refactor', 'perf', 
        'test', 'build', 'ci', 'chore', 'revert'
    ]
    
    # ADRI-specific scopes
    ADRI_SCOPES = [
        'core', 'cli', 'decorators', 'analysis', 'config', 'standards',
        'utils', 'examples', 'tests', 'docs', 'ci', 'release'
    ]
    
    # Conventional commit pattern
    COMMIT_PATTERN = re.compile(
        r'^(?P<type>\w+)(?:\((?P<scope>[\w-]+)\))?: (?P<description>.+)$'
    )
    
    def __init__(self):
        self.errors: List[str] = []
        self.suggestions: List[str] = []
        
    def validate(self, commit_message: str) -> Tuple[bool, List[str], List[str]]:
        """
        Validate commit message and return detailed feedback.
        
        Args:
            commit_message: The commit message to validate
            
        Returns:
            Tuple of (is_valid, errors, suggestions)
        """
        self.errors = []
        self.suggestions = []
        
        # Clean the message
        message = commit_message.strip()
        
        # Skip merge commits and revert commits with special formats
        if (message.startswith('Merge ') or 
            message.startswith('Revert ') or
            message.startswith('Initial commit') or
            message.startswith('WIP:')):
            return True, [], []
        
        # Check basic format
        match = self.COMMIT_PATTERN.match(message)
        
        if not match:
            self._analyze_format_errors(message)
            self._provide_format_suggestions(message)
        else:
            commit_type = match.group('type')
            scope = match.group('scope')
            description = match.group('description')
            
            self._validate_type(commit_type)
            self._validate_scope(scope)
            self._validate_description(description)
            
            if not self.errors:
                self._provide_success_feedback(message)
        
        return len(self.errors) == 0, self.errors, self.suggestions
    
    def _analyze_format_errors(self, message: str) -> None:
        """Analyze what's wrong with the message format."""
        # Check if it starts with a type
        if ':' not in message:
            self.errors.append("Missing colon (:) after commit type")
            self._suggest_colon_fix(message)
        elif not re.match(r'^\w+', message):
            self.errors.append("Commit message must start with a type (feat, fix, docs, etc.)")
        else:
            # Has colon but wrong format
            parts = message.split(':', 1)
            if len(parts) == 2:
                type_part = parts[0].strip()
                if '(' in type_part and ')' not in type_part:
                    self.errors.append("Unclosed scope parenthesis")
                elif ')' in type_part and '(' not in type_part:
                    self.errors.append("Missing opening parenthesis for scope")
                elif not parts[1].strip():
                    self.errors.append("Missing commit description after colon")
                elif not parts[1].startswith(' '):
                    self.errors.append("Missing space after colon")
    
    def _validate_type(self, commit_type: str) -> None:
        """Validate the commit type."""
        if commit_type not in self.VALID_TYPES:
            self.errors.append(f"Invalid commit type: '{commit_type}'")
            self._suggest_similar_type(commit_type)
    
    def _validate_scope(self, scope: Optional[str]) -> None:
        """Validate the scope if present."""
        if scope and scope not in self.ADRI_SCOPES:
            self.suggestions.append(f"Consider using an ADRI scope: {', '.join(self.ADRI_SCOPES)}")
    
    def _validate_description(self, description: str) -> None:
        """Validate the description part."""
        if len(description) > 72:
            self.errors.append(f"Description too long ({len(description)} chars, max 72)")
        
        if description.endswith('.'):
            self.errors.append("Description should not end with a period")
        
        if description and description[0].isupper():
            self.suggestions.append("Consider using lowercase for the first letter (imperative mood)")
    
    def _suggest_colon_fix(self, message: str) -> None:
        """Suggest how to fix missing colon."""
        words = message.split()
        if words:
            first_word = words[0].lower()
            # Try to guess the intended type
            if any(t in first_word for t in self.VALID_TYPES):
                matching_type = next((t for t in self.VALID_TYPES if t in first_word), 'feat')
                rest = ' '.join(words[1:]) if len(words) > 1 else message
                self.suggestions.append(f"Did you mean: '{matching_type}: {rest}'?")
            else:
                self.suggestions.append(f"Try: 'feat: {message}' or 'fix: {message}'")
    
    def _suggest_similar_type(self, invalid_type: str) -> None:
        """Suggest similar valid types."""
        invalid_lower = invalid_type.lower()
        
        # Direct mappings for common mistakes
        type_mappings = {
            'feature': 'feat',
            'add': 'feat',
            'new': 'feat',
            'update': 'feat',
            'bugfix': 'fix',
            'bug': 'fix',
            'hotfix': 'fix',
            'documentation': 'docs',
            'doc': 'docs',
            'cleanup': 'chore',
            'maintenance': 'chore',
            'improve': 'perf',
            'optimize': 'perf',
            'testing': 'test',
        }
        
        if invalid_lower in type_mappings:
            suggested = type_mappings[invalid_lower]
            self.suggestions.append(f"Did you mean '{suggested}' instead of '{invalid_type}'?")
        else:
            # Find closest match by edit distance
            closest = min(self.VALID_TYPES, key=lambda t: self._edit_distance(invalid_lower, t))
            if self._edit_distance(invalid_lower, closest) <= 2:
                self.suggestions.append(f"Did you mean '{closest}' instead of '{invalid_type}'?")
    
    def _edit_distance(self, s1: str, s2: str) -> int:
        """Calculate edit distance between two strings."""
        if len(s1) < len(s2):
            return self._edit_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    
    def _provide_format_suggestions(self, message: str) -> None:
        """Provide format examples and suggestions."""
        self.suggestions.extend([
            "",
            "📖 Correct format: type(scope): description",
            "",
            "✅ Examples:",
            "  feat: add user authentication system",
            "  fix(core): resolve memory leak in data processor", 
            "  docs: update API reference for new endpoints",
            "  refactor(cli): simplify command parsing logic",
            "",
            f"🏷️  Valid types: {', '.join(self.VALID_TYPES)}",
            f"🎯 ADRI scopes: {', '.join(self.ADRI_SCOPES)}",
        ])
    
    def _provide_success_feedback(self, message: str) -> None:
        """Provide positive feedback for valid messages."""
        self.suggestions.append(f"✅ Perfect! Commit message follows conventional format.")


def main():
    """Main entry point for the commit message validator."""
    if len(sys.argv) != 2:
        print("Usage: enhanced_commit_validator.py <commit-message-file>")
        sys.exit(1)
    
    commit_msg_file = sys.argv[1]
    
    try:
        with open(commit_msg_file, 'r', encoding='utf-8') as f:
            commit_message = f.read().strip()
    except (IOError, OSError) as e:
        print(f"Error reading commit message file: {e}")
        sys.exit(1)
    
    # Skip empty messages
    if not commit_message:
        sys.exit(0)
    
    validator = CommitMessageValidator()
    is_valid, errors, suggestions = validator.validate(commit_message)
    
    if not is_valid:
        print("❌ Commit message format error:")
        print(f"\nYour message: \"{commit_message}\"")
        print("\n🔍 Issues found:")
        for i, error in enumerate(errors, 1):
            print(f"  {i}. {error}")
        
        if suggestions:
            print("\n💡 Suggestions:")
            for suggestion in suggestions:
                if suggestion:  # Skip empty lines in terminal output
                    print(f"  {suggestion}")
                else:
                    print()
        
        print("\n📚 Need help? Check CONTRIBUTING.md for more examples.")
        sys.exit(1)
    else:
        # Valid message - optional positive feedback
        if suggestions:
            for suggestion in suggestions:
                if suggestion.startswith("✅"):
                    print(suggestion)
        sys.exit(0)


if __name__ == '__main__':
    main()
