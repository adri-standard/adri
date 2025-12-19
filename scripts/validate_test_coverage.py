#!/usr/bin/env python3
"""
Validate test coverage for marked features.

This script ensures that each marked feature has corresponding tests
in the appropriate test directory (open_source, shared, or enterprise).
"""

import sys
import yaml
from pathlib import Path
from typing import Dict, List

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from feature_markers import (
    FeatureMarker,
    FeatureRegistry,
    FeatureScope,
    scan_codebase,
)


class TestCoverageValidator:
    """Validates that features have appropriate test coverage."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.tests_dir = project_root / 'tests'
        self.coverage_issues: List[str] = []
    
    def get_expected_test_dir(self, scope: FeatureScope) -> Path:
        """Get the expected test directory for a feature scope."""
        if scope == FeatureScope.OPEN_SOURCE:
            return self.tests_dir / 'open_source'
        elif scope == FeatureScope.SHARED:
            return self.tests_dir / 'shared'
        elif scope == FeatureScope.ENTERPRISE:
            return self.tests_dir / 'enterprise'
        else:
            raise ValueError(f"Unknown scope: {scope}")
    
    def find_test_files_for_feature(self, feature: FeatureMarker) -> List[Path]:
        """Find test files that likely test this feature."""
        # Extract module name from feature file path
        file_path = Path(feature.file_path)
        module_name = file_path.stem  # e.g., "decorator.py" -> "decorator"
        
        # Get expected test directory
        test_dir = self.get_expected_test_dir(feature.scope)
        
        # Look for test files matching the module name
        test_files = []
        
        if test_dir.exists():
            # Common test file patterns
            patterns = [
                f"test_{module_name}.py",
                f"test_{module_name}_*.py",
                f"*_test_{module_name}.py",
            ]
            
            for pattern in patterns:
                test_files.extend(test_dir.glob(pattern))
        
        return test_files
    
    def validate_feature_coverage(self, feature: FeatureMarker) -> bool:
        """Validate that a feature has test coverage."""
        test_files = self.find_test_files_for_feature(feature)
        
        if not test_files:
            test_dir = self.get_expected_test_dir(feature.scope)
            module_name = Path(feature.file_path).stem
            
            self.coverage_issues.append(
                f"❌ Feature '{feature.name}' ({feature.scope.value}) lacks tests\n"
                f"   Source: {feature.file_path}\n"
                f"   Expected test file: {test_dir}/test_{module_name}.py"
            )
            return False
        
        return True
    
    def validate_all_features(self, features: Dict[str, FeatureMarker]) -> bool:
        """Validate test coverage for all features."""
        all_valid = True
        
        for feature in features.values():
            if not self.validate_feature_coverage(feature):
                all_valid = False
        
        return all_valid
    
    def generate_coverage_report(self, features: Dict[str, FeatureMarker]) -> str:
        """Generate a test coverage report."""
        total_features = len(features)
        features_with_tests = sum(
            1 for f in features.values() 
            if len(self.find_test_files_for_feature(f)) > 0
        )
        coverage_pct = (features_with_tests / total_features * 100) if total_features > 0 else 0
        
        lines = [
            "Test Coverage Report",
            "=" * 70,
            f"Total Features: {total_features}",
            f"Features with Tests: {features_with_tests}",
            f"Coverage: {coverage_pct:.1f}%",
            "",
        ]
        
        # Group by scope
        for scope in [FeatureScope.OPEN_SOURCE, FeatureScope.SHARED, FeatureScope.ENTERPRISE]:
            scope_features = [f for f in features.values() if f.scope == scope]
            if not scope_features:
                continue
            
            scope_with_tests = sum(
                1 for f in scope_features 
                if len(self.find_test_files_for_feature(f)) > 0
            )
            scope_pct = (scope_with_tests / len(scope_features) * 100) if scope_features else 0
            
            lines.append(f"{scope.value} Features:")
            lines.append(f"  Total: {len(scope_features)}")
            lines.append(f"  With Tests: {scope_with_tests}")
            lines.append(f"  Coverage: {scope_pct:.1f}%")
            lines.append("")
        
        return "\n".join(lines)
    
    def get_test_directory_stats(self) -> Dict[str, int]:
        """Get statistics about test directory organization."""
        stats = {}
        
        for scope in [FeatureScope.OPEN_SOURCE, FeatureScope.SHARED, FeatureScope.ENTERPRISE]:
            test_dir = self.get_expected_test_dir(scope)
            if test_dir.exists():
                test_files = list(test_dir.glob("test_*.py"))
                stats[scope.value] = len(test_files)
            else:
                stats[scope.value] = 0
        
        return stats


def load_config(config_path: Path) -> dict:
    """Load marker system configuration."""
    if not config_path.exists():
        return {
            'scan': {
                'include_patterns': ['src/**/*.py', 'scripts/**/*.py'],
                'exclude_patterns': [
                    '**/__pycache__/**',
                    '**/node_modules/**',
                    '**/.egg-info/**',
                    'tests/**',
                    'docs/**',
                    '*.md',
                ]
            }
        }
    
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def main() -> int:
    """Main entry point."""
    # Determine paths
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    config_path = project_root / '.adri-markers.yaml'
    
    print("=" * 70)
    print("ADRI Test Coverage Validator")
    print("=" * 70)
    print()
    
    # Load configuration
    try:
        config = load_config(config_path)
    except Exception as e:
        print(f"Error loading configuration: {e}")
        return 1
    
    # Scan for features
    scan_config = config.get('scan', {})
    include_patterns = scan_config.get('include_patterns', ['**/*.py'])
    exclude_patterns = scan_config.get('exclude_patterns', [])
    
    print(f"Scanning for features...")
    try:
        features = scan_codebase(project_root, include_patterns, exclude_patterns)
        print(f"Found {len(features)} features")
    except Exception as e:
        print(f"Error scanning codebase: {e}")
        return 1
    
    # Validate test coverage
    print("\nValidating test coverage...")
    validator = TestCoverageValidator(project_root)
    
    # Generate coverage report
    report = validator.generate_coverage_report(features)
    print("\n" + report)
    
    # Validate all features
    all_valid = validator.validate_all_features(features)
    
    # Show directory statistics
    stats = validator.get_test_directory_stats()
    print("Test Directory Organization:")
    for scope, count in stats.items():
        print(f"  {scope}: {count} test files")
    print()
    
    # Display issues
    if validator.coverage_issues:
        print("=" * 70)
        print(f"Coverage Issues ({len(validator.coverage_issues)}):")
        print("=" * 70)
        for issue in validator.coverage_issues:
            print(issue)
            print()
        
        print("=" * 70)
        print("ACTION REQUIRED")
        print("=" * 70)
        print("1. Create missing test files in appropriate directories:")
        print("   - tests/open_source/test_<module>.py for OPEN_SOURCE features")
        print("   - tests/shared/test_<module>.py for SHARED features")
        print("   - tests/enterprise/test_<module>.py for ENTERPRISE features")
        print()
        print("2. Or reorganize existing tests if they already exist elsewhere")
        print()
        return 1
    
    print("=" * 70)
    print("SUCCESS: All features have test coverage!")
    print("=" * 70)
    return 0


if __name__ == '__main__':
    sys.exit(main())
