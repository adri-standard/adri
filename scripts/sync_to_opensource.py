#!/usr/bin/env python3
"""
DEPRECATED: This script has been replaced by extract_opensource.py

The marker-based extraction system has been replaced with simpler directory-based
extraction. Please use scripts/extract_opensource.py instead.

Old command:
    python scripts/sync_to_opensource.py

New command:
    python scripts/extract_opensource.py --output /path/to/opensource

The new approach:
- Copies src/adri/ directory wholesale (simpler, more reliable)
- Validates extracted code has no enterprise imports
- Generates sync reports
- Integrates with CI/CD for automated sync

This file is kept for reference but should not be used for new syncs.
"""

# DEPRECATED - DO NOT USE
# Use scripts/extract_opensource.py instead

import sys

print("=" * 70)
print("DEPRECATED: sync_to_opensource.py")
print("=" * 70)
print()
print("This script has been replaced by extract_opensource.py")
print()
print("Please use:")
print("  python scripts/extract_opensource.py --output /path/to/opensource")
print()
print("The new extraction system uses directory-based copying instead of")
print("marker-based extraction, making it simpler and more reliable.")
print("=" * 70)

sys.exit(1)

# Original deprecated code below (kept for reference)
"""
Sync OPEN_SOURCE and SHARED features to upstream repository.

This script extracts code marked with OPEN_SOURCE and SHARED scopes
from the enterprise repository and prepares it for syncing to the
open source repository.
"""

import argparse
import sys
from pathlib import Path
from typing import Dict, Set

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from feature_markers import (
    FeatureMarker,
    FeatureRegistry,
    FeatureScope,
    scan_codebase,
)


class SyncEngine:
    """Manages syncing of open source features to upstream repository."""
    
    def __init__(self, enterprise_repo: Path, config: dict):
        self.enterprise_repo = enterprise_repo
        self.config = config
        self.registry = FeatureRegistry()
    
    def load_features(self):
        """Load all features from the enterprise repository."""
        scan_config = self.config.get('scan', {})
        include_patterns = scan_config.get('include_patterns', ['**/*.py'])
        exclude_patterns = scan_config.get('exclude_patterns', [])
        
        print(f"Scanning enterprise repository: {self.enterprise_repo}")
        features = scan_codebase(
            self.enterprise_repo, 
            include_patterns, 
            exclude_patterns
        )
        
        for feature in features.values():
            self.registry.add_feature(feature)
        
        print(f"Loaded {len(self.registry.features)} features")
    
    def get_open_source_features(self) -> Dict[str, FeatureMarker]:
        """Get features that should be synced to open source."""
        open_source_features = {}
        
        for name, feature in self.registry.features.items():
            if feature.scope in (FeatureScope.OPEN_SOURCE, FeatureScope.SHARED):
                open_source_features[name] = feature
        
        return open_source_features
    
    def extract_feature_content(self, feature: FeatureMarker) -> str:
        """Extract the content of a feature from its file."""
        file_path = Path(feature.file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Extract lines between start_line and end_line (inclusive)
        feature_lines = lines[feature.start_line - 1:feature.end_line]
        
        return ''.join(feature_lines)
    
    def extract_file_with_features(self, file_path: Path, features: list[FeatureMarker]) -> str:
        """
        Extract a file with only OPEN_SOURCE and SHARED features.
        
        Args:
            file_path: Path to the file
            features: List of features in this file to extract
        
        Returns:
            File content with only open source features
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Track which lines to include
        included_lines = set()
        
        for feature in features:
            # Include all lines from start to end
            for line_num in range(feature.start_line, feature.end_line + 1):
                included_lines.add(line_num)
        
        # Build output with included lines
        output_lines = []
        for line_num, line in enumerate(lines, start=1):
            if line_num in included_lines:
                output_lines.append(line)
        
        return ''.join(output_lines)
    
    def get_files_with_open_source_features(self) -> Dict[Path, list[FeatureMarker]]:
        """Group open source features by file."""
        open_source_features = self.get_open_source_features()
        
        files_with_features: Dict[Path, list[FeatureMarker]] = {}
        
        for feature in open_source_features.values():
            file_path = Path(feature.file_path)
            
            if file_path not in files_with_features:
                files_with_features[file_path] = []
            
            files_with_features[file_path].append(feature)
        
        return files_with_features
    
    def get_test_directories_to_sync(self) -> list[Path]:
        """Get test directories that should be synced to open source."""
        tests_dir = self.enterprise_repo / 'tests'
        dirs_to_sync = []
        
        # Sync open_source and shared test directories
        for scope_dir in ['open_source', 'shared']:
            test_dir = tests_dir / scope_dir
            if test_dir.exists():
                dirs_to_sync.append(test_dir)
        
        # Also sync fixtures for these scopes
        for scope_dir in ['open_source', 'shared']:
            fixture_dir = tests_dir / 'fixtures' / scope_dir
            if fixture_dir.exists():
                dirs_to_sync.append(fixture_dir)
        
        return dirs_to_sync
    
    def preview_sync(self):
        """Preview what would be synced to open source."""
        open_source_features = self.get_open_source_features()
        test_dirs = self.get_test_directories_to_sync()
        
        print("\n" + "=" * 70)
        print("SYNC PREVIEW")
        print("=" * 70)
        print(f"\nFeatures to sync: {len(open_source_features)}")
        print(f"Total features: {len(self.registry.features)}")
        print(f"Percentage: {len(open_source_features) / len(self.registry.features) * 100:.1f}%")
        
        # Group by scope
        by_scope = {}
        for feature in open_source_features.values():
            scope = feature.scope.value
            if scope not in by_scope:
                by_scope[scope] = []
            by_scope[scope].append(feature)
        
        print("\nBy Scope:")
        for scope, features in sorted(by_scope.items()):
            print(f"  {scope}: {len(features)} features")
        
        # List source files
        files = self.get_files_with_open_source_features()
        print(f"\nSource Files: {len(files)}")
        
        for file_path in sorted(files.keys()):
            rel_path = file_path.relative_to(self.enterprise_repo)
            feature_count = len(files[file_path])
            print(f"  {rel_path} ({feature_count} features)")
        
        # List test directories
        if test_dirs:
            print(f"\nTest Directories: {len(test_dirs)}")
            for test_dir in test_dirs:
                rel_path = test_dir.relative_to(self.enterprise_repo)
                test_files = list(test_dir.glob("*.py")) if test_dir.exists() else []
                print(f"  {rel_path}/ ({len(test_files)} test files)")
        
        # Show feature list
        print("\nFeatures to sync:")
        for feature in sorted(open_source_features.values(), key=lambda f: f.name):
            deps = f" [deps: {', '.join(feature.dependencies)}]" if feature.dependencies else ""
            print(f"  - {feature.name} ({feature.scope.value}){deps}")
        
        print("\n" + "=" * 70)
    
    def extract_open_source_content(self, output_dir: Path, dry_run: bool = False):
        """
        Extract open source features and tests to output directory.
        
        Args:
            output_dir: Directory to write extracted files
            dry_run: If True, only show what would be extracted
        """
        files_with_features = self.get_files_with_open_source_features()
        test_dirs = self.get_test_directories_to_sync()
        
        total_items = len(files_with_features) + len(test_dirs)
        print(f"\nExtracting {len(files_with_features)} source files and {len(test_dirs)} test directories to: {output_dir}")
        
        if not dry_run:
            output_dir.mkdir(parents=True, exist_ok=True)
        
        # Extract source files
        print("\nSource Files:")
        for file_path, features in sorted(files_with_features.items()):
            # Get relative path from enterprise repo
            rel_path = file_path.relative_to(self.enterprise_repo)
            output_path = output_dir / rel_path
            
            print(f"  Extracting: {rel_path}")
            
            if not dry_run:
                # Ensure parent directory exists
                output_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Extract content with only open source features
                content = self.extract_file_with_features(file_path, features)
                
                # Write to output file
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(content)
        
        # Extract test directories
        if test_dirs:
            print("\nTest Directories:")
            import shutil
            for test_dir in test_dirs:
                rel_path = test_dir.relative_to(self.enterprise_repo)
                output_path = output_dir / rel_path
                
                print(f"  Extracting: {rel_path}/")
                
                if not dry_run:
                    if test_dir.exists():
                        # Copy entire directory
                        shutil.copytree(test_dir, output_path, dirs_exist_ok=True)
        
        if dry_run:
            print("\n[DRY RUN] No files were written")
        else:
            print(f"\nExtracted {len(files_with_features)} source files and {len(test_dirs)} test directories successfully")


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Sync OPEN_SOURCE and SHARED features to upstream repository'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview sync without making changes'
    )
    parser.add_argument(
        '--output-dir',
        type=Path,
        help='Output directory for extracted files (default: ./open_source_extract)'
    )
    parser.add_argument(
        '--preview',
        action='store_true',
        help='Show preview of what would be synced'
    )
    
    args = parser.parse_args()
    
    # Determine paths
    script_dir = Path(__file__).parent
    enterprise_repo = script_dir.parent
    config_path = enterprise_repo / '.adri-markers.yaml'
    
    # Default output directory
    if args.output_dir is None:
        args.output_dir = enterprise_repo / 'open_source_extract'
    
    print("=" * 70)
    print("ADRI Open Source Sync Engine")
    print("=" * 70)
    print()
    
    # Load configuration
    if config_path.exists():
        import yaml
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
    else:
        print(f"Warning: Config file not found at {config_path}")
        print("Using default configuration")
        config = {
            'scan': {
                'include_patterns': ['src/**/*.py', 'scripts/**/*.py'],
                'exclude_patterns': ['**/__pycache__/**', 'tests/**']
            }
        }
    
    # Initialize sync engine
    try:
        engine = SyncEngine(enterprise_repo, config)
        engine.load_features()
    except Exception as e:
        print(f"Error initializing sync engine: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # Show preview
    if args.preview or args.dry_run:
        engine.preview_sync()
    
    if args.preview:
        # Preview only, don't extract
        return 0
    
    # Extract features
    try:
        engine.extract_open_source_content(args.output_dir, dry_run=args.dry_run)
    except Exception as e:
        print(f"Error during extraction: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    print()
    print("=" * 70)
    print("SYNC COMPLETE")
    print("=" * 70)
    
    if not args.dry_run:
        print(f"\nExtracted files are in: {args.output_dir}")
        print("\nNext steps:")
        print(f"1. Review extracted files in {args.output_dir}")
        print("2. Copy to upstream repository")
        print("3. Create commit and PR in upstream repo")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
