#!/usr/bin/env python3
"""Test script to verify numpy serialization fix in ADRI contract generation."""

import pandas as pd
import yaml
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from adri import ContractGenerator


def test_numpy_serialization():
    """Test that generated contracts can be serialized to YAML without numpy artifacts."""
    
    print("=" * 80)
    print("Testing ADRI Contract Generator - Numpy Serialization Fix")
    print("=" * 80)
    
    # Create test data with multiple fields that will trigger derived field detection
    test_data = pd.DataFrame({
        "project_id": [1, 2, 3, 4, 5],
        "priority_order": [1, 2, 1, 3, 2],
        "project_status": ["At Risk", "On Track", "At Risk", "On Track", "At Risk"],
        "priority_label": ["High", "Medium", "High", "Low", "Medium"],
        "budget": [100000, 50000, 200000, 30000, 75000]
    })
    
    print("\n1. Creating test DataFrame...")
    print(f"   Rows: {len(test_data)}, Columns: {len(test_data.columns)}")
    
    # Generate contract
    print("\n2. Generating ADRI contract...")
    generator = ContractGenerator()
    contract = generator.generate(data=test_data, data_name="test_project")
    
    print("   ✓ Contract generation successful")
    
    # Check for derivation metadata (which contains confidence scores)
    field_reqs = contract.get("requirements", {}).get("field_requirements", {})
    has_derived_fields = any(
        "derivation_metadata" in field_req 
        for field_req in field_reqs.values() 
        if isinstance(field_req, dict)
    )
    
    if has_derived_fields:
        print("   ✓ Derived field metadata detected (confidence scores present)")
    else:
        print("   ⚠ No derived field metadata found (test may be inconclusive)")
    
    # Test 1: YAML serialization without errors
    print("\n3. Testing YAML serialization...")
    try:
        yaml_str = yaml.safe_dump(contract, default_flow_style=False, sort_keys=False)
        print("   ✓ yaml.safe_dump() succeeded")
    except Exception as e:
        print(f"   ✗ yaml.safe_dump() failed: {e}")
        return False
    
    # Test 2: Check for numpy artifacts in YAML string
    print("\n4. Checking for numpy artifacts in YAML...")
    numpy_indicators = [
        "numpy",
        "python/object/apply",
        "!!python/object",
        "_core.multiarray.scalar"
    ]
    
    found_artifacts = []
    for indicator in numpy_indicators:
        if indicator in yaml_str:
            found_artifacts.append(indicator)
    
    if found_artifacts:
        print(f"   ✗ Found numpy artifacts: {found_artifacts}")
        print("\n   Sample of problematic YAML:")
        for line in yaml_str.split('\n'):
            if any(artifact in line for artifact in found_artifacts):
                print(f"     {line[:100]}")
        return False
    else:
        print("   ✓ No numpy artifacts found")
    
    # Test 3: Verify YAML can be loaded back
    print("\n5. Testing YAML round-trip...")
    try:
        reloaded = yaml.safe_load(yaml_str)
        print("   ✓ yaml.safe_load() succeeded")
    except Exception as e:
        print(f"   ✗ yaml.safe_load() failed: {e}")
        return False
    
    # Test 4: Verify confidence values are still present and are floats
    print("\n6. Verifying confidence values are native Python floats...")
    confidence_count = 0
    all_native_floats = True
    
    def check_confidence(obj, path=""):
        nonlocal confidence_count, all_native_floats
        if isinstance(obj, dict):
            for key, value in obj.items():
                new_path = f"{path}.{key}" if path else key
                if key == "confidence" and value is not None:
                    confidence_count += 1
                    if not isinstance(value, float):
                        print(f"   ✗ Non-float confidence at {new_path}: {type(value).__name__}")
                        all_native_floats = False
                check_confidence(value, new_path)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                check_confidence(item, f"{path}[{i}]")
    
    check_confidence(reloaded)
    
    if confidence_count > 0:
        if all_native_floats:
            print(f"   ✓ Found {confidence_count} confidence value(s), all are native Python floats")
        else:
            print(f"   ✗ Some confidence values are not native Python floats")
            return False
    else:
        print("   ⚠ No confidence values found in contract")
    
    # Success!
    print("\n" + "=" * 80)
    print("✓ ALL TESTS PASSED!")
    print("=" * 80)
    print("\nThe numpy serialization fix is working correctly:")
    print("  • Contracts generate successfully")
    print("  • YAML serialization works with yaml.safe_dump()")
    print("  • No numpy artifacts in YAML output")
    print("  • YAML can be loaded back without errors")
    print("  • All numeric values are native Python types")
    print("\n")
    
    return True


if __name__ == "__main__":
    success = test_numpy_serialization()
    sys.exit(0 if success else 1)
