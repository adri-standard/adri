#!/usr/bin/env python3
"""
Generate Feature Catalogs for ADRI.

Scans the codebase to identify control points (CLI commands, decorator parameters,
API methods) and generates business-facing feature documentation for both
open source and enterprise tiers.

Usage:
    python scripts/generate_feature_catalog.py

Outputs:
    - OPEN_SOURCE_FEATURES.md - Features available in open source
    - ENTERPRISE_FEATURES.md - All features (OS + Enterprise)
"""

import ast
import inspect
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any


@dataclass
class ControlPoint:
    """Represents a user-facing control point (CLI command, parameter, etc.)."""
    name: str
    type: str  # "cli_command", "decorator_param", "api_method", "logging_feature"
    scope: str  # "OPEN_SOURCE" or "ENTERPRISE"
    description: str
    usage_example: str
    file_path: str


class FeatureCatalogGenerator:
    """Generates business-facing feature catalogs."""

    def __init__(self, repo_root: Path):
        """
        Initialize catalog generator.

        Args:
            repo_root: Path to repository root
        """
        self.repo_root = Path(repo_root)
        self.control_points: List[ControlPoint] = []

    def scan_all(self) -> None:
        """Scan all features and generate control points."""
        print("Scanning ADRI codebase for features...")
        
        # Scan open source decorator parameters
        self.scan_decorator_params(
            self.repo_root / "src" / "adri" / "decorator.py",
            scope="OPEN_SOURCE"
        )
        
        # Scan enterprise decorator parameters
        self.scan_decorator_params(
            self.repo_root / "src" / "adri_enterprise" / "decorator.py",
            scope="ENTERPRISE"
        )
        
        # Scan CLI commands
        self.scan_cli_commands(
            self.repo_root / "src" / "adri" / "cli" / "commands",
            scope="OPEN_SOURCE"
        )
        
        # Scan logging features
        self.scan_logging_features()
        
        print(f"  ✓ Found {len(self.control_points)} control points")

    def scan_decorator_params(self, decorator_file: Path, scope: str) -> None:
        """
        Scan decorator parameters from decorator file.

        Args:
            decorator_file: Path to decorator.py file
            scope: OPEN_SOURCE or ENTERPRISE
        """
        if not decorator_file.exists():
            return

        try:
            content = decorator_file.read_text()
            tree = ast.parse(content)
            
            # Find the adri_protected function
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == "adri_protected":
                    # Extract parameters
                    for arg in node.args.args:
                        param_name = arg.arg
                        
                        # Skip 'self' or internal params
                        if param_name in ['self']:
                            continue
                        
                        # Determine if enterprise-only param
                        enterprise_params = [
                            'reasoning_mode', 'store_prompt', 'store_response',
                            'llm_config', 'workflow_context', 'data_provenance'
                        ]
                        param_scope = "ENTERPRISE" if param_name in enterprise_params else scope
                        
                        # Extract description from docstring
                        description = self._extract_param_description(content, param_name)
                        
                        # Create usage example
                        usage_example = f'@adri_protected({param_name}=...)'
                        
                        self.control_points.append(ControlPoint(
                            name=param_name,
                            type="decorator_param",
                            scope=param_scope,
                            description=description,
                            usage_example=usage_example,
                            file_path=str(decorator_file.relative_to(self.repo_root))
                        ))
                        
        except Exception as e:
            print(f"  Warning: Failed to scan {decorator_file}: {e}")

    def scan_cli_commands(self, cli_dir: Path, scope: str) -> None:
        """
        Scan CLI commands from commands directory.

        Args:
            cli_dir: Path to CLI commands directory
            scope: OPEN_SOURCE or ENTERPRISE
        """
        if not cli_dir.exists():
            return

        for cmd_file in cli_dir.glob("*.py"):
            if cmd_file.name == "__init__.py":
                continue
                
            try:
                content = cmd_file.read_text()
                
                # Extract command name from filename
                cmd_name = cmd_file.stem
                
                # Extract description from module docstring
                tree = ast.parse(content)
                description = ast.get_docstring(tree) or f"{cmd_name} command"
                description = description.split('\n')[0]  # First line only
                
                # Create usage example
                usage_example = f'adri {cmd_name.replace("_", "-")} [options]'
                
                self.control_points.append(ControlPoint(
                    name=f"adri {cmd_name.replace('_', '-')}",
                    type="cli_command",
                    scope=scope,
                    description=description,
                    usage_example=usage_example,
                    file_path=str(cmd_file.relative_to(self.repo_root))
                ))
                
            except Exception as e:
                print(f"  Warning: Failed to scan {cmd_file}: {e}")

    def scan_logging_features(self) -> None:
        """Scan logging features."""
        # Open source: LocalLogger
        self.control_points.append(ControlPoint(
            name="LocalLogger",
            type="logging_feature",
            scope="OPEN_SOURCE",
            description="JSONL-based local audit logging for assessments",
            usage_example="LocalLogger(config={'enabled': True, 'log_dir': './logs'})",
            file_path="src/adri/logging/local.py"
        ))
        
        # Enterprise: VerodatLogger
        self.control_points.append(ControlPoint(
            name="VerodatLogger",
            type="logging_feature",
            scope="ENTERPRISE",
            description="Centralized logging via Verodat API with batch processing",
            usage_example="VerodatLogger(api_url='...', api_key='...')",
            file_path="src/adri_enterprise/logging/verodat.py"
        ))
        
        # Enterprise: ReasoningLogger
        self.control_points.append(ControlPoint(
            name="ReasoningLogger",
            type="logging_feature",
            scope="ENTERPRISE",
            description="AI reasoning step logging for prompts and responses",
            usage_example="ReasoningLogger(log_dir='./logs')",
            file_path="src/adri_enterprise/logging/reasoning.py"
        ))

    def _extract_param_description(self, content: str, param_name: str) -> str:
        """Extract parameter description from docstring."""
        # Simple extraction - look for param in Args section
        lines = content.split('\n')
        in_args = False
        for i, line in enumerate(lines):
            if 'Args:' in line:
                in_args = True
                continue
            if in_args and param_name in line and ':' in line:
                # Extract description after the colon
                desc = line.split(':', 1)[1].strip()
                return desc if desc else f"{param_name} parameter"
        
        return f"{param_name} parameter"

    def generate_catalog(self, scope: str) -> str:
        """
        Generate feature catalog markdown for specified scope.

        Args:
            scope: "OPEN_SOURCE" or "ENTERPRISE"

        Returns:
            Markdown-formatted feature catalog
        """
        # Filter control points by scope
        if scope == "OPEN_SOURCE":
            points = [cp for cp in self.control_points if cp.scope == "OPEN_SOURCE"]
            title = "ADRI Open Source Features"
            intro = """
This document catalogs all features available in the open source ADRI package.
These features are community-driven and freely available under the Apache 2.0 license.
"""
        else:  # ENTERPRISE
            points = self.control_points  # All features
            title = "ADRI Enterprise Features"
            intro = """
This document catalogs all features available in ADRI Enterprise, including both
open source features and enterprise-exclusive capabilities.
"""

        # Group by type
        by_type: Dict[str, List[ControlPoint]] = {}
        for point in points:
            if point.type not in by_type:
                by_type[point.type] = []
            by_type[point.type].append(point)

        # Generate markdown
        lines = [
            f"# {title}",
            "",
            intro.strip(),
            "",
            "## Table of Contents",
            "",
        ]

        # Add TOC
        type_names = {
            "decorator_param": "Decorator Parameters",
            "cli_command": "CLI Commands",
            "logging_feature": "Logging Features",
            "api_method": "API Methods",
        }
        
        for type_key in sorted(by_type.keys()):
            type_name = type_names.get(type_key, type_key.replace('_', ' ').title())
            lines.append(f"- [{type_name}](#{type_key.replace('_', '-')})")
        
        lines.extend(["", "---", ""])

        # Add sections
        for type_key in sorted(by_type.keys()):
            type_name = type_names.get(type_key, type_key.replace('_', ' ').title())
            lines.extend([
                f"## {type_name}",
                "",
            ])
            
            # Add each control point
            for point in sorted(by_type[type_key], key=lambda x: x.name):
                badge = "🔵 Open Source" if point.scope == "OPEN_SOURCE" else "🟢 Enterprise"
                lines.extend([
                    f"### `{point.name}` {badge}",
                    "",
                    point.description,
                    "",
                    "**Usage:**",
                    "```python",
                    point.usage_example,
                    "```",
                    "",
                    f"**Location:** `{point.file_path}`",
                    "",
                    "---",
                    "",
                ])

        return "\n".join(lines)

    def _extract_param_description(self, content: str, param_name: str) -> str:
        """Extract parameter description from docstring."""
        lines = content.split('\n')
        in_args = False
        for i, line in enumerate(lines):
            if 'Args:' in line:
                in_args = True
                continue
            if in_args and param_name in line and ':' in line:
                desc = line.split(':', 1)[1].strip()
                return desc if desc else f"{param_name} parameter"
        
        return f"{param_name} parameter"


def main():
    """Main entry point."""
    repo_root = Path.cwd()
    
    print("=" * 70)
    print("ADRI Feature Catalog Generator")
    print("=" * 70)
    print()
    
    # Create generator
    generator = FeatureCatalogGenerator(repo_root)
    
    # Scan all features
    generator.scan_all()
    print()
    
    # Generate open source catalog
    print("Generating OPEN_SOURCE_FEATURES.md...")
    os_catalog = generator.generate_catalog("OPEN_SOURCE")
    os_file = repo_root / "docs" / "OPEN_SOURCE_FEATURES.md"
    os_file.parent.mkdir(parents=True, exist_ok=True)
    os_file.write_text(os_catalog)
    print(f"  ✓ Saved to {os_file}")
    print()
    
    # Generate enterprise catalog
    print("Generating ENTERPRISE_FEATURES.md...")
    ent_catalog = generator.generate_catalog("ENTERPRISE")
    ent_file = repo_root / "docs" / "ENTERPRISE_FEATURES.md"
    ent_file.write_text(ent_catalog)
    print(f"  ✓ Saved to {ent_file}")
    print()
    
    print("=" * 70)
    print("Feature Catalogs Generated Successfully")
    print("=" * 70)


if __name__ == "__main__":
    main()
