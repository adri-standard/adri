"""
Demonstrate loading custom configuration and tracking overridden settings.

This script shows how to load a custom configuration file and tracks
which settings were overridden compared to the defaults.
"""

import sys
from pathlib import Path

# Add parent directory to path if running as script
if __name__ == "__main__":
    parent_dir = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(parent_dir))

import pandas as pd
import numpy as np
import json

from adri.config import Configuration, get_config, set_config
from adri.rules import RuleRegistry

# Import rule modules to register rules
import adri.rules.validity
import adri.rules.plausibility


def create_sample_data(rows=100):
    """Create a small sample DataFrame for testing."""
    # Same as in example_evaluation.py but with fewer rows
    np.random.seed(42)  # For reproducibility
    
    # Create data with some quality issues
    df = pd.DataFrame({
        'id': [f"ID-{str(i).zfill(5)}" for i in range(rows)],
        'numeric_col': np.random.normal(50, 10, rows),
    })
    
    # Add some outliers
    for i in range(0, rows, 20):
        if i < len(df):
            df.loc[i, 'numeric_col'] = np.random.choice([200, -50, 300])
    
    return df


def compare_rule_results(rule_id, data, default_config, custom_config):
    """Compare rule results with default and custom config."""
    print(f"\n=== Comparing results for {rule_id} ===")
    
    # Create rule with default config
    default_rule_config = default_config.get_rule_config(rule_id)
    default_rule = RuleRegistry.create_rule(rule_id, default_rule_config)
    
    # Evaluate with default config
    default_result = default_rule.evaluate(data)
    default_narrative = default_rule.generate_narrative(default_result)
    
    # Create rule with custom config
    custom_rule_config = custom_config.get_rule_config(rule_id)
    custom_rule = RuleRegistry.create_rule(rule_id, custom_rule_config)
    
    # Evaluate with custom config
    custom_result = custom_rule.evaluate(data)
    custom_narrative = custom_rule.generate_narrative(custom_result)
    
    # Print comparison
    print("\nDEFAULT CONFIG RESULTS:")
    print(f"Score: {default_result.get('score', 0)}/{default_rule_config.get('weight', 0)}")
    print(f"Valid: {default_result.get('valid', False)}")
    print(f"Narrative: {default_narrative[:100]}...")
    
    print("\nCUSTOM CONFIG RESULTS:")
    print(f"Score: {custom_result.get('score', 0)}/{custom_rule_config.get('weight', 0)}")
    print(f"Valid: {custom_result.get('valid', False)}")
    print(f"Narrative: {custom_narrative[:100]}...")
    
    # Print differences in config
    overrides = custom_config.get_overridden_settings().get(rule_id, {})
    if overrides:
        print("\nCUSTOM CONFIG OVERRIDES:")
        for param, values in overrides.items():
            print(f"{param}: {values['default']} -> {values['custom']}")


def main():
    """Load custom configuration and show differences."""
    print("=== ADRI Custom Configuration Demo ===\n")
    
    # Load default configuration
    default_config = Configuration()
    
    # Load custom configuration
    config_path = Path(__file__).parent / "example_config.yaml"
    custom_config = Configuration.from_file(str(config_path))
    
    # Set as global config
    set_config(custom_config)
    
    # Show which settings were overridden
    overridden = custom_config.get_overridden_settings()
    
    print(f"Loaded custom configuration from: {config_path}")
    print(f"Found {len(overridden)} rules with overridden settings")
    
    # Print overridden settings
    for rule_id, params in overridden.items():
        print(f"\n{rule_id}:")
        for param, values in params.items():
            print(f"  {param}: {values['default']} -> {values['custom']}")
    
    # Create sample data
    print("\nCreating sample data...")
    sample_df = create_sample_data(100)
    
    # Compare results with default and custom config
    rule_ids = [
        "plausibility.outlier_detection",
        "validity.type_consistency"
    ]
    
    for rule_id in rule_ids:
        if rule_id in overridden:
            compare_rule_results(rule_id, sample_df, default_config, custom_config)
    
    # Show which dimensions have custom weights
    print("\n=== Dimension Weights ===")
    
    default_weights = default_config.get_assessment_config()["dimension_weights"]
    custom_weights = custom_config.get_assessment_config()["dimension_weights"]
    
    print("\nDefault dimension weights:")
    print(json.dumps(default_weights, indent=2))
    
    print("\nCustom dimension weights:")
    print(json.dumps(custom_weights, indent=2))
    
    # Report information example
    print("\n=== Assessment Report Example ===")
    print("\nA full assessment report would include:")
    print("1. Overall ADRI score")
    print("2. Dimension scores")
    print("3. Individual rule results")
    print("4. Customization information:")
    print(f"   - Used {len(overridden)} custom rule settings")
    
    dimension_changes = []
    for dimension, weight in custom_weights.items():
        if weight != default_weights.get(dimension, 1.0):
            dimension_changes.append(f"{dimension} (weight: {weight})")
    
    if dimension_changes:
        print(f"   - Used custom weights for {len(dimension_changes)} dimensions: {', '.join(dimension_changes)}")
    
    print("5. Rule narratives for AI consumption")


if __name__ == "__main__":
    main()
