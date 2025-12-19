#!/usr/bin/env python3
"""
ADRI Standard Migration Script
Converts ADRI v1 standards to v2 format with field categories and derivation rules.

Usage:
    python migrate_adri_standards.py <input_file> <output_file> [--dry-run]
    
    Options:
        --dry-run: Preview changes without writing output file
        --verbose: Show detailed migration decisions
"""

import yaml
import sys
import argparse
from pathlib import Path
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass
from enum import Enum

class FieldCategory(Enum):
    """Field category classification"""
    STANDARD = "standard"
    AI_DECISION = "ai_decision"
    AI_NARRATIVE = "ai_narrative"

@dataclass
class MigrationDecision:
    """Record of migration decision for a field"""
    field_name: str
    category: FieldCategory
    reasoning: str
    confidence: str
    actions_taken: List[str]
    warnings: List[str] = None
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []

class ADRIMigrator:
    """Migrates ADRI v1 standards to v2 format"""
    
    def __init__(self, verbose=False):
        self.verbose = verbose
        self.decisions = []
        self.warnings = []
    
    def migrate_standard(self, v1_standard: Dict) -> Tuple[Dict, List[MigrationDecision]]:
        """
        Migrate v1 standard to v2 format.
        Returns (v2_standard, migration_decisions)
        """
        self.decisions = []
        self.warnings = []
        
        # Create v2 structure
        v2_standard = self._copy_metadata(v1_standard)
        
        # Migrate field requirements
        v1_fields = v1_standard.get('requirements', {}).get('field_requirements', {})
        v2_fields = {}
        
        for field_name, field_spec in v1_fields.items():
            v2_field, decision = self._migrate_field(field_name, field_spec)
            v2_fields[field_name] = v2_field
            self.decisions.append(decision)
        
        # Update structure
        if 'requirements' not in v2_standard:
            v2_standard['requirements'] = {}
        v2_standard['requirements']['field_requirements'] = v2_fields
        
        # Copy dimension requirements
        if 'dimension_requirements' in v1_standard.get('requirements', {}):
            v2_standard['requirements']['dimension_requirements'] = \
                v1_standard['requirements']['dimension_requirements']
        
        # Add migration metadata
        v2_standard = self._add_migration_metadata(v2_standard, v1_standard)
        
        return v2_standard, self.decisions
    
    def _copy_metadata(self, v1_standard: Dict) -> Dict:
        """Copy top-level metadata from v1 standard"""
        v2 = {}
        
        # Copy standards section
        if 'standards' in v1_standard:
            v2['standards'] = v1_standard['standards'].copy()
            # Update version
            if 'version' in v2['standards']:
                major = v2['standards']['version'].split('.')[0]
                v2['standards']['version'] = f"{major}.0.0"  # Bump to new major version
        elif 'contracts' in v1_standard:
            # Old format used 'contracts'
            v2['standards'] = v1_standard['contracts'].copy()
        
        # Copy requirements structure
        if 'requirements' in v1_standard:
            v2['requirements'] = {
                'overall_minimum': v1_standard['requirements'].get('overall_minimum'),
                'strict_schema_match': v1_standard['requirements'].get('strict_schema_match')
            }
        
        return v2
    
    def _migrate_field(self, field_name: str, field_spec: Dict) -> Tuple[Dict, MigrationDecision]:
        """
        Migrate a single field specification.
        Returns (v2_field_spec, migration_decision)
        """
        # Determine field category
        category, reasoning = self._classify_field(field_name, field_spec)
        
        actions = []
        warnings = []
        
        # Start with copy of original spec
        v2_spec = field_spec.copy()
        
        # Add field_category
        v2_spec['field_category'] = category.value
        actions.append(f"Set field_category to '{category.value}'")
        
        # Category-specific transformations
        if category == FieldCategory.AI_DECISION:
            v2_spec, new_actions, new_warnings = self._transform_decision_field(
                field_name, v2_spec
            )
            actions.extend(new_actions)
            warnings.extend(new_warnings)
        
        elif category == FieldCategory.AI_NARRATIVE:
            v2_spec, new_actions, new_warnings = self._transform_narrative_field(
                field_name, v2_spec
            )
            actions.extend(new_actions)
            warnings.extend(new_warnings)
        
        # Create decision record
        confidence = self._assess_confidence(category, field_name, field_spec)
        decision = MigrationDecision(
            field_name=field_name,
            category=category,
            reasoning=reasoning,
            confidence=confidence,
            actions_taken=actions,
            warnings=warnings
        )
        
        return v2_spec, decision
    
    def _classify_field(self, field_name: str, field_spec: Dict) -> Tuple[FieldCategory, str]:
        """
        Classify field into category based on heuristics.
        Returns (category, reasoning)
        """
        # Check for explicit AI pattern fields (uppercase names with specific suffixes)
        if field_name.isupper():
            if any(field_name.endswith(suffix) for suffix in ['_RATIONALE', '_SUMMARY', '_FACTORS', '_RECOMMENDATIONS', '_DESCRIPTION', '_NARRATIVE']):
                return (
                    FieldCategory.AI_NARRATIVE,
                    f"Uppercase field ending with narrative suffix"
                )
            elif any(field_name.endswith(suffix) for suffix in ['_LEVEL', '_STATUS', '_SCORE', '_TYPE', '_CLASS', '_CATEGORY']):
                return (
                    FieldCategory.AI_DECISION,
                    f"Uppercase field ending with decision suffix"
                )
        
        # Check for derivation logic in allowed_values (v1 pattern)
        allowed_values = field_spec.get('allowed_values')
        if isinstance(allowed_values, dict) and self._has_derivation_logic(allowed_values):
            return (
                FieldCategory.AI_DECISION,
                "Has derivation logic in allowed_values structure"
            )
        
        # Check if has is_derived flag
        if field_spec.get('is_derived', False):
            # Could be decision or narrative - check type
            if field_spec.get('type') in ['string', 'array'] and \
               ('min_length' in str(field_spec.get('constraints', [])) or
                'max_length' in str(field_spec.get('constraints', []))):
                return (
                    FieldCategory.AI_NARRATIVE,
                    "Marked as derived with text type and length constraints"
                )
            else:
                return (
                    FieldCategory.AI_DECISION,
                    "Marked as derived with enum or numeric type"
                )
        
        # Check for array types with narrative-like names
        if field_spec.get('type') == 'array':
            if any(term in field_name.lower() for term in ['factor', 'recommendation', 'issue', 'item']):
                return (
                    FieldCategory.AI_NARRATIVE,
                    "Array type with narrative content indicators"
                )
        
        # Check for long text fields (likely narrative)
        constraints = field_spec.get('constraints', [])
        has_long_text = False
        for constraint in constraints:
            if constraint.get('type') == 'max_length' and constraint.get('value', 0) > 200:
                has_long_text = True
                break
        
        if has_long_text and field_spec.get('type') == 'string':
            return (
                FieldCategory.AI_NARRATIVE,
                "Long text field (>200 chars) suggesting narrative content"
            )
        
        # Default to STANDARD
        return (
            FieldCategory.STANDARD,
            "No AI pattern detected - regular data field"
        )
    
    def _has_derivation_logic(self, allowed_values: Dict) -> bool:
        """Check if allowed_values dict contains derivation logic"""
        for value_def in allowed_values.values():
            if isinstance(value_def, dict):
                if 'derivation_rule' in value_def or 'precedence' in value_def:
                    return True
        return False
    
    def _transform_decision_field(
        self,
        field_name: str,
        field_spec: Dict
    ) -> Tuple[Dict, List[str], List[str]]:
        """Transform AI decision field to v2 format"""
        actions = []
        warnings = []
        
        # Extract derivation rules if present in old format
        allowed_values = field_spec.get('allowed_values')
        
        if isinstance(allowed_values, dict) and self._has_derivation_logic(allowed_values):
            # Convert old format to new format
            derivation, clean_values = self._extract_derivation_rules(allowed_values)
            
            if derivation:
                field_spec['derivation'] = derivation
                actions.append("Extracted derivation rules to separate section")
            
            # Replace complex allowed_values with simple list
            field_spec['allowed_values'] = clean_values
            actions.append("Simplified allowed_values to list format")
        
        # Remove old metadata that's now in derivation
        if 'derivation_metadata' in field_spec:
            del field_spec['derivation_metadata']
            actions.append("Removed old derivation_metadata (preserved in derivation.metadata)")
        
        if 'is_derived' in field_spec:
            del field_spec['is_derived']
            actions.append("Removed is_derived flag (implicit in derivation presence)")
        
        # Add warning if no derivation could be extracted
        if 'derivation' not in field_spec and 'allowed_values' in field_spec:
            warnings.append(
                "Could not auto-generate derivation rules - manual review recommended"
            )
        
        return field_spec, actions, warnings
    
    def _transform_narrative_field(
        self,
        field_name: str,
        field_spec: Dict
    ) -> Tuple[Dict, List[str], List[str]]:
        """Transform AI narrative field to v2 format"""
        actions = []
        warnings = []
        
        # Remove semantic constraints (should only have structural)
        constraints = field_spec.get('constraints', [])
        filtered_constraints = []
        removed_constraints = []
        
        for constraint in constraints:
            constraint_type = constraint.get('type')
            # Keep only structural constraints
            if constraint_type in ['min_length', 'max_length', 'not_null', 'min_items', 'max_items']:
                filtered_constraints.append(constraint)
            else:
                removed_constraints.append(constraint_type)
        
        if removed_constraints:
            field_spec['constraints'] = filtered_constraints
            actions.append(f"Removed semantic constraints: {', '.join(removed_constraints)}")
        
        # Add reasoning guidance template
        guidance = self._generate_reasoning_guidance(field_name, field_spec)
        if guidance:
            field_spec['reasoning_guidance'] = guidance
            actions.append("Generated reasoning_guidance template")
        
        # Remove derivation if present (narratives shouldn't have derivation)
        if 'derivation' in field_spec:
            del field_spec['derivation']
            actions.append("Removed derivation (not applicable to narratives)")
            warnings.append("Narrative field had derivation rules - removed")
        
        return field_spec, actions, warnings
    
    def _extract_derivation_rules(self, allowed_values: Dict) -> Tuple[Dict, List[str]]:
        """
        Extract derivation rules from old allowed_values format.
        Returns (derivation_dict, clean_values_list)
        """
        rules = []
        clean_values = []
        
        # Sort by precedence
        sorted_items = sorted(
            allowed_values.items(),
            key=lambda x: x[1].get('precedence', 999) if isinstance(x[1], dict) else 999
        )
        
        for value, value_def in sorted_items:
            clean_values.append(value)
            
            if not isinstance(value_def, dict):
                continue
            
            derivation_rule = value_def.get('derivation_rule', {})
            if not derivation_rule:
                continue
            
            # Convert to v2 rule format
            rule = {
                'precedence': value_def.get('precedence', len(rules) + 1),
                'value': value,
                'note': value_def.get('definition', '')
            }
            
            # Extract condition logic
            logic = derivation_rule.get('logic', '')
            if logic and not logic.startswith('TODO'):
                # Clean up logic string
                condition = logic.replace(f"THEN '{value}'", '').replace(f'THEN "{value}"', '')
                condition = condition.replace('IF ', ' ').strip()
                rule['condition'] = condition
            else:
                # Mark as needing review
                rule['condition'] = "TODO: Define condition"
                rule['needs_review'] = True
            
            rules.append(rule)
        
        # Check if last rule should be default
        if rules and rules[-1].get('condition') in ['TODO: Define condition', 'DEFAULT']:
            rules[-1]['is_default'] = True
            rules[-1].pop('condition', None)
        
        derivation = {
            'strategy': 'ordered_precedence',
            'inputs': derivation_rule.get('inputs', []) if derivation_rule else [],
            'rules': rules,
            'metadata': {
                'auto_generated': True,
                'confidence': 'medium',
                'note': 'Migrated from v1 format - review recommended'
            }
        }
        
        return derivation, clean_values
    
    def _generate_reasoning_guidance(self, field_name: str, field_spec: Dict) -> str:
        """Generate reasoning guidance template for narrative field"""
        templates = {
            'RATIONALE': 'Explain the reasoning for this assessment based on available data.\n\nConsider relevant factors and provide specific details.',
            'SUMMARY': 'Provide a concise summary of key points.\n\nFocus on the most important information for decision-makers.',
            'FACTORS': 'List specific factors identified from the data.\n\nFormat as short, actionable phrases (5-15 words each).',
            'RECOMMENDATIONS': 'Provide actionable recommendations based on the analysis.\n\nFormat as specific action statements.',
            'DESCRIPTION': 'Describe the situation based on available data.\n\nInclude relevant context and details.',
            'NARRATIVE': 'Provide a detailed narrative explanation.\n\nEnsure clarity and completeness.'
        }
        
        # Match on suffix
        for suffix, template in templates.items():
            if field_name.endswith(suffix):
                return template
        
        # Generic template
        return 'Provide detailed reasoning for this field.\n\nBase your response on available data.'
    
    def _assess_confidence(
        self,
        category: FieldCategory,
        field_name: str,
        field_spec: Dict
    ) -> str:
        """Assess confidence in category classification"""
        
        # High confidence indicators
        if field_name.isupper() and category != FieldCategory.STANDARD:
            return 'high'
        
        if 'derivation_rule' in str(field_spec) and category == FieldCategory.AI_DECISION:
            return 'high'
        
        if 'RATIONALE' in field_name and category == FieldCategory.AI_NARRATIVE:
            return 'high'
        
        # Medium confidence
        if field_spec.get('is_derived') and category != FieldCategory.STANDARD:
            return 'medium'
        
        # Low confidence
        if category == FieldCategory.STANDARD:
            return 'high'  # Default classification is safe
        
        return 'medium'
    
    def _add_migration_metadata(self, v2_standard: Dict, v1_standard: Dict) -> Dict:
        """Add migration metadata to v2 standard"""
        if 'metadata' not in v2_standard:
            v2_standard['metadata'] = {}
        
        # Count field categories
        field_requirements = v2_standard.get('requirements', {}).get('field_requirements', {})
        category_counts = {
            'standard_fields': 0,
            'ai_decision_fields': 0,
            'ai_narrative_fields': 0
        }
        
        for field_spec in field_requirements.values():
            category = field_spec.get('field_category', 'standard')
            if category == 'standard':
                category_counts['standard_fields'] += 1
            elif category == 'ai_decision':
                category_counts['ai_decision_fields'] += 1
            elif category == 'ai_narrative':
                category_counts['ai_narrative_fields'] += 1
        
        category_counts['total_fields'] = sum(category_counts.values())
        
        v2_standard['metadata']['field_category_summary'] = category_counts
        v2_standard['metadata']['migration_info'] = {
            'migrated_from_version': v1_standard.get('standards', {}).get('version',
                                     v1_standard.get('contracts', {}).get('version', 'unknown')),
            'migration_date': '2025-01-11',
            'migration_tool': 'migrate_adri_standards.py v1.0',
            'manual_review_recommended': any(d.confidence != 'high' for d in self.decisions)
        }
        
        return v2_standard
    
    def print_migration_report(self):
        """Print detailed migration report"""
        print("\n" + "="*80)
        print("MIGRATION REPORT")
        print("="*80 + "\n")
        
        # Summary
        total = len(self.decisions)
        by_category = {
            'standard': 0,
            'ai_decision': 0,
            'ai_narrative': 0
        }
        by_confidence = {'high': 0, 'medium': 0, 'low': 0}
        needs_review = 0
        
        for decision in self.decisions:
            by_category[decision.category.value] += 1
            by_confidence[decision.confidence] += 1
            if decision.warnings or decision.confidence == 'medium':
                needs_review += 1
        
        print(f"Total Fields Migrated: {total}")
        print(f"  - Standard: {by_category['standard']}")
        print(f"  - AI Decision: {by_category['ai_decision']}")
        print(f"  - AI Narrative: {by_category['ai_narrative']}")
        print()
        print(f"Confidence Distribution:")
        print(f"  - High: {by_confidence['high']}")
        print(f"  - Medium: {by_confidence['medium']}")
        print(f"  - Low: {by_confidence['low']}")
        print()
        print(f"Fields Needing Review: {needs_review}")
        print()
        
        # Detailed decisions
        if self.verbose:
            print("-" * 80)
            print("DETAILED DECISIONS")
            print("-" * 80 + "\n")
            
            for decision in self.decisions:
                print(f"Field: {decision.field_name}")
                print(f"  Category: {decision.category.value}")
                print(f"  Confidence: {decision.confidence}")
                print(f"  Reasoning: {decision.reasoning}")
                print(f"  Actions:")
                for action in decision.actions_taken:
                    print(f"    - {action}")
                if decision.warnings:
                    print(f"  Warnings:")
                    for warning in decision.warnings:
                        print(f"    ⚠️  {warning}")
                print()
        else:
            # Just show fields needing review
            review_fields = [d for d in self.decisions if d.warnings or d.confidence != 'high']
            if review_fields:
                print("-" * 80)
                print("FIELDS NEEDING REVIEW")
                print("-" * 80 + "\n")
                for decision in review_fields:
                    print(f"• {decision.field_name} ({decision.category.value}, {decision.confidence} confidence)")
                    if decision.warnings:
                        for warning in decision.warnings:
                            print(f"  ⚠️  {warning}")
                print()

def main():
    parser = argparse.ArgumentParser(description='Migrate ADRI v1 standard to v2 format')
    parser.add_argument('input_file', help='Input YAML file (v1 standard)')
    parser.add_argument('output_file', help='Output YAML file (v2 standard)')
    parser.add_argument('--dry-run', action='store_true', help='Preview without writing output')
    parser.add_argument('--verbose', action='store_true', help='Show detailed decisions')
    
    args = parser.parse_args()
    
    # Load input file
    print(f"Loading {args.input_file}...")
    try:
        with open(args.input_file, 'r') as f:
            v1_standard = yaml.safe_load(f)
    except Exception as e:
        print(f"Error loading input file: {e}")
        sys.exit(1)
    
    # Migrate
    print("Migrating standard to v2 format...")
    migrator = ADRIMigrator(verbose=args.verbose)
    v2_standard, decisions = migrator.migrate_standard(v1_standard)
    
    # Print report
    migrator.print_migration_report()
    
    # Write output
    if not args.dry_run:
        print(f"Writing output to {args.output_file}...")
        try:
            with open(args.output_file, 'w') as f:
                yaml.dump(v2_standard, f, default_flow_style=False, sort_keys=False, width=100)
            print(f"✓ Migration complete! Output written to {args.output_file}")
            print("\nNext steps:")
            print("1. Review fields with warnings or medium/low confidence")
            print("2. Validate migrated standard with ADRI validator")
            print("3. Test with sample data")
        except Exception as e:
            print(f"Error writing output file: {e}")
            sys.exit(1)
    else:
        print("\n✓ Dry run complete - no files written")
        print(f"\nRun without --dry-run to write output to {args.output_file}")

if __name__ == '__main__':
    main()
