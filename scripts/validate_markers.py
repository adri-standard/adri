#!/usr/bin/env python3
"""
Validate feature markers in codebase.

This script validates that all @ADRI_FEATURE markers are well-formed
and follow the project's conventions. Can be used as a pre-commit hook.
"""

import sys
import yaml
from pathlib import Path
from typing import List, Tuple

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from feature_markers import (
    FeatureRegistry,
    FeatureScope,
    scan_codebase,
    validate_marker_pairs,
)


class ValidationError:
    """Represents a validation error."""
    def __init__(self, severity: str, message: str, file_path: str = "", line_num: int = 0):
        self.severity = severity  # ERROR or WARNING
        self.message = message
        self.file_path = file_path
        self.line_num = line_num
    
    def __str__(self):
        if self.file_path:
            return f"[{self.severity}] {self.file_path}:{self.line_num} - {self.message}"
        return f"[{self.severity}] {self.message}"


class MarkerValidator:
    """Validates feature markers according to project conventions."""
    
    def __init__(self, registry: FeatureRegistry, config: dict):
        self.registry = registry
        self.config = config
        self.errors: List[ValidationError] = []
        self.warnings: List[ValidationError] = []
    
    def validate_naming_conventions(self) -> None:
        """Check feature names follow conventions."""
        naming_config = self.config.get('feature_naming', {})
        domain_prefixes = naming_config.get('domain_prefixes', [])
        
        for feature in self.registry.features.values():
            # Check if name uses recommended domain prefix
            if domain_prefixes:
                has_prefix = any(feature.name.startswith(prefix) for prefix in domain_prefixes)
                if not has_prefix:
                    self.warnings.append(ValidationError(
                        'WARNING',
                        f"Feature '{feature.name}' doesn't use a recommended domain prefix: {', '.join(domain_prefixes)}",
                        feature.file_path,
                        feature.start_line
                    ))
            
            # Check for common anti-patterns
            if any(bad in feature.name.lower() for bad in ['temp', 'tmp', 'test', 'v1', 'v2', 'old', 'new']):
                self.warnings.append(ValidationError(
                    'WARNING',
                    f"Feature '{feature.name}' contains temporary or version-specific naming",
                    feature.file_path,
                    feature.start_line
                ))
    
    def validate_scope_consistency(self) -> None:
        """Check scope assignments make sense."""
        naming_config = self.config.get('feature_naming', {})
        scope_defaults = naming_config.get('scope_defaults', {})
        
        for feature in self.registry.features.values():
            # Check if scope matches expected default for prefix
            for prefix, expected_scope in scope_defaults.items():
                if feature.name.startswith(prefix):
                    expected_scope_enum = FeatureScope[expected_scope]
                    if feature.scope != expected_scope_enum:
                        self.warnings.append(ValidationError(
                            'WARNING',
                            f"Feature '{feature.name}' has scope {feature.scope.value} but prefix '{prefix}' suggests {expected_scope}",
                            feature.file_path,
                            feature.start_line
                        ))
    
    def validate_descriptions(self) -> None:
        """Check descriptions are meaningful."""
        for feature in self.registry.features.values():
            # Check for too-short descriptions
            if len(feature.description) < 10:
                self.warnings.append(ValidationError(
                    'WARNING',
                    f"Feature '{feature.name}' has very short description: '{feature.description}'",
                    feature.file_path,
                    feature.start_line
                ))
            
            # Check for placeholder descriptions
            if feature.description.lower() in ['todo', 'tbd', 'fix', 'fixme']:
                self.errors.append(ValidationError(
                    'ERROR',
                    f"Feature '{feature.name}' has placeholder description: '{feature.description}'",
                    feature.file_path,
                    feature.start_line
                ))
    
    def validate_all(self) -> Tuple[bool, List[ValidationError], List[ValidationError]]:
        """Run all validation checks."""
        self.errors = []
        self.warnings = []
        
        # Run validation checks
        self.validate_naming_conventions()
        self.validate_scope_consistency()
        self.validate_descriptions()
        
        # Success if no errors (warnings are okay)
        success = len(self.errors) == 0
        return success, self.errors, self.warnings


def load_config(config_path: Path) -> dict:
    """Load marker system configuration."""
    if not config_path.exists():
        # Return default configuration
        return {
            'scan': {
                'include_patterns': [
                    'src/**/*.py',
                    'scripts/**/*.py',
                    'docs/**/*.md',
                    '*.md',
                ],
                'exclude_patterns': [
                    '**/__pycache__/**',
                    '**/node_modules/**',
                    '**/.egg-info/**',
                    '**/build/**',
                    '**/dist/**',
                    'tests/**',
                ]
            },
            'feature_naming': {
                'domain_prefixes': [
                    'core_',
                    'cli_',
                    'api_',
                    'auth_',
                    'validator_',
                    'logging_',
                    'contracts_',
                    'analysis_',
                ],
                'scope_defaults': {
                    'core_': 'SHARED',
                    'cli_': 'OPEN_SOURCE',
                    'api_': 'ENTERPRISE',
                    'auth_': 'ENTERPRISE',
                    'validator_': 'OPEN_SOURCE',
                    'logging_': 'SHARED',
                    'contracts_': 'OPEN_SOURCE',
                    'analysis_': 'OPEN_SOURCE',
                }
            }
        }
    
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def validate_codebase(root_dir: Path, config: dict) -> Tuple[bool, List[str]]:
    """
    Validate all markers in codebase.
    
    Returns:
        (success, error_messages)
    """
    all_errors = []
    
    # Get scan configuration
    scan_config = config.get('scan', {})
    include_patterns = scan_config.get('include_patterns', ['**/*.py'])
    exclude_patterns = scan_config.get('exclude_patterns', [])
    
    print(f"Scanning codebase in {root_dir}...")
    
    # Scan for features
    try:
        features = scan_codebase(root_dir, include_patterns, exclude_patterns)
    except Exception as e:
        all_errors.append(str(e))
        return False, all_errors
    
    print(f"Found {len(features)} features")
    
    # Validate marker syntax
    print("Validating marker syntax...")
    syntax_errors = validate_marker_pairs(features)
    if syntax_errors:
        all_errors.extend(syntax_errors)
    
    # Build registry
    registry = FeatureRegistry()
    for feature in features.values():
        try:
            registry.add_feature(feature)
        except Exception as e:
            all_errors.append(str(e))
    
    # Validate dependencies
    print("Validating dependencies...")
    dep_errors = registry.validate_dependencies()
    if dep_errors:
        all_errors.extend(dep_errors)
    
    # Run custom validations
    print("Running convention checks...")
    validator = MarkerValidator(registry, config)
    success, errors, warnings = validator.validate_all()
    
    # Print warnings
    if warnings:
        print(f"\nFound {len(warnings)} warnings:")
        for warning in warnings:
            print(f"  {warning}")
    
    # Add validation errors
    for error in errors:
        all_errors.append(str(error))
    
    return len(all_errors) == 0, all_errors


def main() -> int:
    """Main entry point."""
    # Determine paths
    script_dir = Path(__file__).parent
    root_dir = script_dir.parent
    config_path = root_dir / '.adri-markers.yaml'
    
    print("=" * 70)
    print("ADRI Feature Marker Validator")
    print("=" * 70)
    print()
    
    # Load configuration
    try:
        config = load_config(config_path)
    except Exception as e:
        print(f"Error loading configuration: {e}")
        return 1
    
    # Validate codebase
    try:
        success, errors = validate_codebase(root_dir, config)
    except Exception as e:
        print(f"Error during validation: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    print()
    
    if success:
        print("=" * 70)
        print("SUCCESS: All markers are valid!")
        print("=" * 70)
        return 0
    else:
        print("=" * 70)
        print(f"FAILED: Found {len(errors)} errors")
        print("=" * 70)
        print()
        for error in errors:
            print(f"  - {error}")
        print()
        return 1


if __name__ == '__main__':
    sys.exit(main())
