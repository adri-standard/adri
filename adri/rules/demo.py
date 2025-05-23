"""
Demo script for ADRI rule registry.

This script demonstrates how to use the ADRI rule registry and rule classes.
It can be used as a simple example or for testing that the rule system works.
"""

import sys
import json
import logging
from pathlib import Path

# Add parent directory to path if running as script
if __name__ == "__main__":
    parent_dir = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(parent_dir))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

from adri.rules import RuleRegistry
from adri.config import get_config

# Import rule modules to register rules
import adri.rules.validity
import adri.rules.plausibility


def demo_rule_registry():
    """Demonstrate the use of the rule registry."""
    print("\n=== ADRI Rule Registry Demo ===\n")
    
    # Get all registered rules
    all_rules = RuleRegistry.list_rules()
    print(f"Total registered rules: {len(all_rules)}")
    
    # Get rules by dimension
    dimensions = RuleRegistry.get_dimensions()
    print(f"Dimensions with rules: {', '.join(dimensions)}\n")
    
    # Print rules by dimension
    for dimension in dimensions:
        rules = RuleRegistry.get_rules_by_dimension(dimension)
        print(f"{dimension.capitalize()} dimension rules: {len(rules)}")
        for rule_id, rule_class in rules.items():
            print(f"  - {rule_id}: {rule_class.__name__}")
    
    print("\n=== Creating Rule Instances ===\n")
    
    # Create rule instances with default parameters
    config = get_config()
    
    # Get rule config
    outlier_rule_config = config.get_rule_config("plausibility.outlier_detection")
    print(f"Outlier rule config: {json.dumps(outlier_rule_config, indent=2)}")
    
    # Create rule instance
    outlier_rule = RuleRegistry.create_rule("plausibility.outlier_detection", outlier_rule_config)
    
    # Show rule metadata
    print(f"\nRule metadata: {json.dumps(outlier_rule.get_metadata(), indent=2)}")
    
    # Create rule with custom parameters
    custom_params = {
        "enabled": True,
        "method": "iqr",
        "threshold": 2.5,
        "weight": 3.0
    }
    
    custom_rule = RuleRegistry.create_rule("plausibility.outlier_detection", custom_params)
    print(f"\nCustom rule params: {json.dumps(custom_rule.params, indent=2)}")
    
    print("\n=== Rule Grid ===\n")
    
    # Generate rule grid
    grid = RuleRegistry.get_rule_grid()
    
    for dimension, rules in grid.items():
        print(f"{dimension.capitalize()} Dimension: {len(rules)} rules")
        for rule in rules:
            print(f"  - {rule['id']}: {rule['name']}")
            print(f"    {rule['description']}")
            print(f"    Parameters: {', '.join([p['name'] for p in rule['parameters']])}")
            print()
    
    # Generate markdown grid
    markdown = RuleRegistry.generate_markdown_grid()
    
    # Save to file
    output_file = Path(__file__).parent / "rule_grid.md"
    with open(output_file, "w") as f:
        f.write(markdown)
        
    print(f"Markdown grid saved to: {output_file}")


if __name__ == "__main__":
    demo_rule_registry()
