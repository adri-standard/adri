#!/usr/bin/env python3
"""
Analyze differences between enterprise and upstream for marked files.

Compares each marked file against upstream/main to identify what's truly
enterprise-specific vs what's just renaming (contract/standard).
"""

import subprocess
import sys
import yaml
from pathlib import Path
from typing import Dict, List, Tuple

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))

from feature_markers import scan_codebase, FeatureMarker, FeatureScope


def get_diff_stats(file_path: str) -> Tuple[int, int]:
    """Get diff statistics for a file."""
    try:
        result = subprocess.run(
            ['git', 'diff', '--numstat', 'upstream/main..HEAD', '--', file_path],
            capture_output=True,
            text=True,
            check=True
        )
        
        if result.stdout.strip():
            parts = result.stdout.strip().split()
            added = int(parts[0]) if parts[0] != '-' else 0
            removed = int(parts[1]) if parts[1] != '-' else 0
            return (added, removed)
    except:
        pass
    
    return (0, 0)


def count_renaming_lines(file_path: str) -> int:
    """Count lines that are just contract/standard renaming."""
    try:
        result = subprocess.run(
            ['git', 'diff', 'upstream/main..HEAD', '--', file_path],
            capture_output=True,
            text=True,
            check=True
        )
        
        renaming_count = 0
        for line in result.stdout.split('\n'):
            if line.startswith('+') or line.startswith('-'):
                # Skip diff markers
                if line.startswith('+++') or line.startswith('---'):
                    continue
                
                # Check for contract/standard renaming
                lower = line.lower()
                if 'standard' in lower or 'contract' in lower:
                    if ('standard' in lower and 'contract' not in lower) or \
                       ('contract' in lower and 'standard' not in lower):
                        renaming_count += 1
        
        return renaming_count
    except:
        return 0


def get_enterprise_specific_additions(file_path: str) -> List[str]:
    """Identify enterprise-specific additions (heuristic)."""
    additions = []
    
    try:
        result = subprocess.run(
            ['git', 'diff', 'upstream/main..HEAD', '--', file_path],
            capture_output=True,
            text=True,
            check=True
        )
        
        for line in result.stdout.split('\n'):
            if line.startswith('+') and not line.startswith('+++'):
                # Look for enterprise indicators
                if any(keyword in line.lower() for keyword in ['verodat', 'enterprise', 'license', 'proprietary']):
                    additions.append(line.strip())
        
    except:
        pass
    
    return additions


def analyze_file(feature: FeatureMarker) -> Dict:
    """Analyze a single file's diff."""
    file_path = feature.file_path
    
    # Get diff stats
    added, removed = get_diff_stats(file_path)
    
    # Count renaming lines
    renaming = count_renaming_lines(file_path)
    
    # Find enterprise additions
    enterprise_additions = get_enterprise_specific_additions(file_path)
    
    # Calculate real changes (non-renaming)
    real_changes = max(0, added + removed - (renaming * 2))
    
    return {
        'feature': feature.name,
        'scope': feature.scope.value,
        'file': file_path,
        'total_lines_changed': added + removed,
        'added': added,
        'removed': removed,
        'renaming_lines': renaming,
        'real_changes': real_changes,
        'enterprise_additions': enterprise_additions,
        'recommendation': 'NEEDS_REVIEW' if enterprise_additions else 'SCOPE_OK'
    }


def main():
    """Main entry point."""
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    config_path = project_root / '.adri-markers.yaml'
    
    print("=" * 80)
    print("ADRI Enterprise Diff Analysis")
    print("=" * 80)
    print()
    
    # Load config
    if config_path.exists():
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
    else:
        config = {
            'scan': {
                'include_patterns': ['src/**/*.py'],
                'exclude_patterns': ['**/__pycache__/**', 'tests/**']
            }
        }
    
    # Scan for features
    scan_config = config.get('scan', {})
    features = scan_codebase(
        project_root,
        scan_config.get('include_patterns', ['**/*.py']),
        scan_config.get('exclude_patterns', [])
    )
    
    print(f"Analyzing {len(features)} marked files against upstream/main...\n")
    
    # Analyze each feature
    results = []
    for feature in features.values():
        analysis = analyze_file(feature)
        results.append(analysis)
    
    # Sort by scope then by file
    results.sort(key=lambda x: (x['scope'], x['file']))
    
    # Display results by scope
    for scope in ['OPEN_SOURCE', 'SHARED', 'ENTERPRISE']:
        scope_results = [r for r in results if r['scope'] == scope]
        if not scope_results:
            continue
        
        print(f"\n{scope} Features ({len(scope_results)}):")
        print("=" * 80)
        
        for result in scope_results:
            print(f"\nFeature: {result['feature']}")
            print(f"File: {Path(result['file']).relative_to(project_root)}")
            print(f"Changes: +{result['added']}/-{result['removed']} lines")
            print(f"Renaming: ~{result['renaming_lines']} lines (contract/standard)")
            print(f"Real changes: ~{result['real_changes']} lines")
            
            if result['enterprise_additions']:
                print(f"⚠️  Enterprise additions found: {len(result['enterprise_additions'])} lines")
                print("First 3 enterprise lines:")
                for line in result['enterprise_additions'][:3]:
                    print(f"  {line[:100]}")
            
            print(f"Status: {result['recommendation']}")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    needs_review = [r for r in results if r['recommendation'] == 'NEEDS_REVIEW']
    scope_ok = [r for r in results if r['recommendation'] == 'SCOPE_OK']
    
    print(f"Scope appears correct: {len(scope_ok)} files")
    print(f"Needs review: {len(needs_review)} files")
    
    if needs_review:
        print("\nFiles needing review:")
        for result in needs_review:
            print(f"  - {result['feature']} ({result['scope']}) - {len(result['enterprise_additions'])} enterprise lines")
    
    return 0 if not needs_review else 1


if __name__ == '__main__':
    sys.exit(main())
