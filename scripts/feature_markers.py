"""
Core marker parsing library for ADRI feature management system.

This module provides the foundational classes and functions for parsing,
validating, and managing feature markers in the codebase.
"""

import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


class FeatureScope(Enum):
    """Feature scope classification."""
    OPEN_SOURCE = "OPEN_SOURCE"  # Goes to open source repo
    ENTERPRISE = "ENTERPRISE"     # Enterprise-only feature
    SHARED = "SHARED"            # Core shared by both repos


class FeatureStatus(Enum):
    """Feature lifecycle status."""
    ACTIVE = "ACTIVE"            # Current production feature
    DEPRECATED = "DEPRECATED"     # Being phased out
    EXPERIMENTAL = "EXPERIMENTAL" # Under development


@dataclass
class FeatureMarker:
    """Represents a single feature marker in the codebase."""
    name: str
    scope: FeatureScope
    description: str
    file_path: str
    start_line: int
    end_line: int
    dependencies: List[str] = field(default_factory=list)
    status: FeatureStatus = FeatureStatus.ACTIVE
    
    def validate(self) -> List[str]:
        """Validate marker completeness and consistency."""
        errors = []
        
        if not self.name:
            errors.append(f"Feature name cannot be empty at {self.file_path}:{self.start_line}")
        
        if not self.description:
            errors.append(f"Feature {self.name} missing description at {self.file_path}:{self.start_line}")
        
        if self.end_line <= self.start_line:
            errors.append(f"Feature {self.name} has invalid line range at {self.file_path}")
        
        # Check for invalid characters in name
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', self.name):
            errors.append(f"Feature {self.name} has invalid name format (must start with letter, contain only alphanumeric and underscore)")
        
        return errors
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            'name': self.name,
            'scope': self.scope.value,
            'description': self.description,
            'file_path': self.file_path,
            'start_line': self.start_line,
            'end_line': self.end_line,
            'dependencies': self.dependencies,
            'status': self.status.value
        }
    
    def __hash__(self):
        """Make hashable for set operations."""
        return hash(self.name)
    
    def __eq__(self, other):
        """Equality based on feature name."""
        if not isinstance(other, FeatureMarker):
            return False
        return self.name == other.name


class FeatureRegistry:
    """Container for all features with dependency management."""
    
    def __init__(self):
        self.features: Dict[str, FeatureMarker] = {}
        self.last_generated: Optional[datetime] = None
    
    def add_feature(self, marker: FeatureMarker) -> None:
        """Add feature to registry."""
        if marker.name in self.features:
            existing = self.features[marker.name]
            raise ValueError(
                f"Duplicate feature name '{marker.name}' found in:\n"
                f"  - {existing.file_path}:{existing.start_line}\n"
                f"  - {marker.file_path}:{marker.start_line}"
            )
        self.features[marker.name] = marker
    
    def get_by_scope(self, scope: FeatureScope) -> List[FeatureMarker]:
        """Get all features with given scope."""
        return [f for f in self.features.values() if f.scope == scope]
    
    def get_open_source_features(self) -> List[FeatureMarker]:
        """Get features that should go to open source (OPEN_SOURCE + SHARED)."""
        return [
            f for f in self.features.values() 
            if f.scope in (FeatureScope.OPEN_SOURCE, FeatureScope.SHARED)
        ]
    
    def get_enterprise_features(self) -> List[FeatureMarker]:
        """Get enterprise-only features."""
        return self.get_by_scope(FeatureScope.ENTERPRISE)
    
    def validate_dependencies(self) -> List[str]:
        """Ensure all dependency references exist."""
        errors = []
        
        for feature in self.features.values():
            for dep_name in feature.dependencies:
                if dep_name not in self.features:
                    errors.append(
                        f"Feature '{feature.name}' references unknown dependency '{dep_name}' "
                        f"at {feature.file_path}:{feature.start_line}"
                    )
                else:
                    # Check scope compatibility
                    dep_feature = self.features[dep_name]
                    if feature.scope == FeatureScope.OPEN_SOURCE:
                        if dep_feature.scope == FeatureScope.ENTERPRISE:
                            errors.append(
                                f"Feature '{feature.name}' (OPEN_SOURCE) cannot depend on "
                                f"'{dep_name}' (ENTERPRISE) at {feature.file_path}:{feature.start_line}"
                            )
        
        return errors
    
    def topological_sort(self) -> List[str]:
        """Return features in dependency order (dependencies before dependents)."""
        # Build adjacency list
        graph: Dict[str, List[str]] = {name: [] for name in self.features}
        in_degree: Dict[str, int] = {name: 0 for name in self.features}
        
        for feature in self.features.values():
            for dep_name in feature.dependencies:
                if dep_name in graph:  # Only valid dependencies
                    graph[dep_name].append(feature.name)
                    in_degree[feature.name] += 1
        
        # Kahn's algorithm
        queue = [name for name, degree in in_degree.items() if degree == 0]
        result = []
        
        while queue:
            # Sort for deterministic output
            queue.sort()
            node = queue.pop(0)
            result.append(node)
            
            for neighbor in graph[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        # Check for cycles
        if len(result) != len(self.features):
            missing = set(self.features.keys()) - set(result)
            raise ValueError(f"Circular dependency detected involving features: {missing}")
        
        return result
    
    def to_markdown(self) -> str:
        """Generate markdown registry."""
        lines = [
            "# ADRI Feature Registry",
            "",
            f"**Last Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            f"**Total Features:** {len(self.features)}",
            "",
            "---",
            ""
        ]
        
        # Group by scope
        for scope in [FeatureScope.OPEN_SOURCE, FeatureScope.SHARED, FeatureScope.ENTERPRISE]:
            features = self.get_by_scope(scope)
            if not features:
                continue
            
            lines.append(f"## {scope.value} Features ({len(features)})")
            lines.append("")
            lines.append("| Feature | Description | Files | Status | Dependencies |")
            lines.append("|---------|-------------|-------|--------|--------------|")
            
            # Sort by name
            for feature in sorted(features, key=lambda f: f.name):
                deps_str = ", ".join(feature.dependencies) if feature.dependencies else "-"
                status_emoji = "✅" if feature.status == FeatureStatus.ACTIVE else "⚠️"
                lines.append(
                    f"| {feature.name} | {feature.description} | "
                    f"{Path(feature.file_path).name} | {status_emoji} {feature.status.value} | {deps_str} |"
                )
            
            lines.append("")
        
        return "\n".join(lines)


class MarkerParser:
    """Parses feature marker syntax from code comments."""
    
    # Regex pattern for marker lines
    MARKER_START_PATTERN = re.compile(
        r'@ADRI_FEATURE\[(\w+),\s*scope=(\w+)(?:,\s*status=(\w+))?(?:,\s*deps=\[([\w,\s]+)\])?\]'
    )
    
    MARKER_END_PATTERN = re.compile(
        r'@ADRI_FEATURE_END\[(\w+)\]'
    )
    
    DESCRIPTION_PATTERN = re.compile(
        r'Description:\s*(.+)'
    )
    
    def parse_line(self, line: str) -> Optional[Tuple[str, FeatureScope, Optional[FeatureStatus], List[str]]]:
        """
        Parse a single marker start line.
        
        Returns: (name, scope, status, dependencies) or None if not a marker
        """
        match = self.MARKER_START_PATTERN.search(line)
        if not match:
            return None
        
        name = match.group(1)
        scope_str = match.group(2)
        status_str = match.group(3)
        deps_str = match.group(4)
        
        # Parse scope
        try:
            scope = FeatureScope[scope_str]
        except KeyError:
            raise ValueError(f"Invalid scope '{scope_str}' in marker (must be OPEN_SOURCE, ENTERPRISE, or SHARED)")
        
        # Parse status (optional)
        status = None
        if status_str:
            try:
                status = FeatureStatus[status_str]
            except KeyError:
                raise ValueError(f"Invalid status '{status_str}' in marker (must be ACTIVE, DEPRECATED, or EXPERIMENTAL)")
        
        # Parse dependencies (optional)
        dependencies = []
        if deps_str:
            dependencies = [d.strip() for d in deps_str.split(',') if d.strip()]
        
        return (name, scope, status, dependencies)
    
    def parse_file(self, filepath: Path) -> List[FeatureMarker]:
        """
        Parse all markers in a file.
        
        Returns: List of FeatureMarker objects
        """
        markers = []
        current_marker: Optional[Dict] = None
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except (IOError, UnicodeDecodeError) as e:
            # Skip binary files or files we can't read
            return []
        
        for line_num, line in enumerate(lines, start=1):
            # Check for start marker
            start_match = self.parse_line(line)
            if start_match:
                if current_marker:
                    raise ValueError(
                        f"Nested marker detected: Started '{current_marker['name']}' at line {current_marker['start_line']}, "
                        f"but found new marker at line {line_num} in {filepath}"
                    )
                
                name, scope, status, dependencies = start_match
                current_marker = {
                    'name': name,
                    'scope': scope,
                    'status': status or FeatureStatus.ACTIVE,
                    'dependencies': dependencies,
                    'start_line': line_num,
                    'description': ''
                }
                continue
            
            # Check for description (must come after start marker)
            if current_marker and not current_marker['description']:
                desc_match = self.DESCRIPTION_PATTERN.search(line)
                if desc_match:
                    current_marker['description'] = desc_match.group(1).strip()
                    continue
            
            # Check for end marker
            end_match = self.MARKER_END_PATTERN.search(line)
            if end_match:
                end_name = end_match.group(1)
                
                if not current_marker:
                    raise ValueError(
                        f"End marker for '{end_name}' at line {line_num} has no matching start marker in {filepath}"
                    )
                
                if end_name != current_marker['name']:
                    raise ValueError(
                        f"Mismatched markers: Started '{current_marker['name']}' at line {current_marker['start_line']}, "
                        f"but ended with '{end_name}' at line {line_num} in {filepath}"
                    )
                
                # Create marker
                marker = FeatureMarker(
                    name=current_marker['name'],
                    scope=current_marker['scope'],
                    description=current_marker['description'] or f"Feature {current_marker['name']}",
                    file_path=str(filepath),
                    start_line=current_marker['start_line'],
                    end_line=line_num,
                    dependencies=current_marker['dependencies'],
                    status=current_marker['status']
                )
                
                markers.append(marker)
                current_marker = None
        
        # Check for unclosed marker
        if current_marker:
            raise ValueError(
                f"Unclosed marker '{current_marker['name']}' started at line {current_marker['start_line']} in {filepath}"
            )
        
        return markers


def scan_codebase(root_dir: Path, include_patterns: List[str], exclude_patterns: List[str]) -> Dict[str, FeatureMarker]:
    """
    Recursively scan codebase for markers.
    
    Args:
        root_dir: Root directory to scan
        include_patterns: List of glob patterns to include (e.g., "*.py", "src/**/*.py")
        exclude_patterns: List of glob patterns to exclude
    
    Returns:
        Dictionary of feature name -> FeatureMarker
    """
    parser = MarkerParser()
    registry = FeatureRegistry()
    
    # Collect all files matching include patterns
    files_to_scan: Set[Path] = set()
    for pattern in include_patterns:
        files_to_scan.update(root_dir.glob(pattern))
    
    # Remove excluded files
    for pattern in exclude_patterns:
        excluded = set(root_dir.glob(pattern))
        files_to_scan -= excluded
    
    # Parse each file
    errors = []
    for filepath in sorted(files_to_scan):
        if filepath.is_file():
            try:
                markers = parser.parse_file(filepath)
                for marker in markers:
                    registry.add_feature(marker)
            except Exception as e:
                errors.append(f"Error parsing {filepath}: {e}")
    
    if errors:
        raise ValueError("Errors found while scanning codebase:\n" + "\n".join(errors))
    
    return registry.features


def validate_marker_pairs(features: Dict[str, FeatureMarker]) -> List[str]:
    """
    Validate that all markers are well-formed.
    
    Args:
        features: Dictionary of feature markers
    
    Returns:
        List of validation error messages
    """
    errors = []
    
    for feature in features.values():
        feature_errors = feature.validate()
        errors.extend(feature_errors)
    
    return errors


def build_dependency_graph(features: Dict[str, FeatureMarker]) -> Dict[str, List[str]]:
    """
    Build feature dependency mapping.
    
    Args:
        features: Dictionary of feature markers
    
    Returns:
        Dictionary mapping feature name -> list of features that depend on it
    """
    graph: Dict[str, List[str]] = {name: [] for name in features}
    
    for feature in features.values():
        for dep_name in feature.dependencies:
            if dep_name in graph:
                graph[dep_name].append(feature.name)
    
    return graph
