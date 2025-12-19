#!/usr/bin/env python3
"""
Generate FEATURE_REGISTRY.md from code markers.

This script scans the codebase for @ADRI_FEATURE markers and generates
a human-readable registry in markdown format for governance and review.
"""

import sys
import yaml
from pathlib import Path
from typing import List

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from feature_markers import (
    FeatureRegistry,
    scan_codebase,
    validate_marker_pairs,
)


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
            }
        }
    
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def generate_registry(root_dir: Path, config: dict) -> str:
    """
    Generate feature registry from codebase scan.
    
    Args:
        root_dir: Root directory of codebase
        config: Configuration dictionary
    
    Returns:
        Markdown content for registry
    """
    # Get scan configuration
    scan_config = config.get('scan', {})
    include_patterns = scan_config.get('include_patterns', ['**/*.py'])
    exclude_patterns = scan_config.get('exclude_patterns', [])
    
    print(f"Scanning codebase in {root_dir}...")
    print(f"Include patterns: {include_patterns}")
    print(f"Exclude patterns: {exclude_patterns}")
    
    # Scan for features
    features = scan_codebase(root_dir, include_patterns, exclude_patterns)
    
    print(f"Found {len(features)} features")
    
    # Validate markers
    print("Validating markers...")
    validation_errors = validate_marker_pairs(features)
    if validation_errors:
        print("Validation errors found:")
        for error in validation_errors:
            print(f"  - {error}")
        sys.exit(1)
    
    # Build registry
    registry = FeatureRegistry()
    for feature in features.values():
        registry.add_feature(feature)
    
    # Validate dependencies
    print("Validating dependencies...")
    dep_errors = registry.validate_dependencies()
    if dep_errors:
        print("Dependency validation errors:")
        for error in dep_errors:
            print(f"  - {error}")
        sys.exit(1)
    
    # Generate markdown
    print("Generating registry markdown...")
    markdown_content = registry.to_markdown()
    
    # Add statistics
    open_source_count = len(registry.get_open_source_features())
    enterprise_count = len(registry.get_enterprise_features())
    
    stats_section = f"""
## Statistics

- **Open Source Features (OPEN_SOURCE + SHARED):** {open_source_count}
- **Enterprise-Only Features:** {enterprise_count}
- **Total Features:** {len(features)}

## Dependency Graph

The features are organized in dependency order. When syncing to open source,
features will be extracted in the order that respects their dependencies.

"""
    
    # Insert stats after the header
    parts = markdown_content.split('---\n')
    if len(parts) >= 2:
        markdown_content = parts[0] + '---\n' + stats_section + '\n'.join(parts[1:])
    
    # Add footer
    footer = """
---

## Notes

This registry is auto-generated. Do not edit manually.
To update, run: `python scripts/generate_feature_registry.py`

Review this file in git diffs to approve feature scope decisions before committing.
"""
    
    markdown_content += footer
    
    return markdown_content


def write_registry(content: str, output_path: Path) -> None:
    """Write registry to file."""
    print(f"Writing registry to {output_path}...")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Registry written successfully: {output_path}")


def main() -> int:
    """Main entry point."""
    # Determine paths
    script_dir = Path(__file__).parent
    root_dir = script_dir.parent
    config_path = root_dir / '.adri-markers.yaml'
    output_path = root_dir / 'FEATURE_REGISTRY.md'
    
    print("=" * 70)
    print("ADRI Feature Registry Generator")
    print("=" * 70)
    print()
    
    # Load configuration
    try:
        config = load_config(config_path)
    except Exception as e:
        print(f"Error loading configuration: {e}")
        return 1
    
    # Generate registry
    try:
        content = generate_registry(root_dir, config)
    except Exception as e:
        print(f"Error generating registry: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # Write to file
    try:
        write_registry(content, output_path)
    except Exception as e:
        print(f"Error writing registry: {e}")
        return 1
    
    print()
    print("=" * 70)
    print("SUCCESS: Registry generated successfully!")
    print("=" * 70)
    print()
    print("Next steps:")
    print("1. Review FEATURE_REGISTRY.md for accuracy")
    print("2. Check git diff to see what changed")
    print("3. Commit the registry alongside your code changes")
    print()
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
