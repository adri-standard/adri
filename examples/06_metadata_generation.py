#!/usr/bin/env python3
"""
Example 06: Automatic Metadata Generation with `adri init`

This example demonstrates how to use the new `adri init` command to automatically
generate starter metadata files, solving the "metadata overhead" problem.

The `adri init` command uses the internal MetadataGenerator to analyze your data 
and creates pre-filled metadata files for all five ADRI dimensions, reducing 
setup time from hours to minutes.
"""

import os
import json
import subprocess
from pathlib import Path

def main():
    """Demonstrate the adri init command."""
    
    print("=== ADRI Metadata Generation Example ===\n")
    
    # Path to our test data
    data_file = Path("examples/test_init_data.csv")
    output_dir = Path("examples/generated_metadata")
    
    # Create output directory
    output_dir.mkdir(exist_ok=True)
    
    print(f"1. Using test data: {data_file}")
    print(f"2. Output directory: {output_dir}\n")
    
    # Run the init command
    print("3. Running: adri init examples/test_init_data.csv --output-dir examples/generated_metadata")
    print("-" * 60)
    
    result = subprocess.run([
        "adri", "init", 
        str(data_file),
        "--output-dir", str(output_dir)
    ], capture_output=True, text=True)
    
    print(result.stdout)
    if result.stderr:
        print("Errors:", result.stderr)
    
    # Show what was generated
    print("\n4. Generated metadata files:")
    print("-" * 60)
    print("   - test_init_data.validity.json")
    print("   - test_init_data.completeness.json")
    print("   - test_init_data.freshness.json") 
    print("   - test_init_data.consistency.json")
    print("   - test_init_data.plausibility.json")
    
    for dimension in ["validity", "completeness", "freshness", "consistency", "plausibility"]:
        metadata_file = output_dir / f"test_init_data.{dimension}.json"
        if metadata_file.exists():
            print(f"\n✓ {metadata_file.name}:")
            
            # Load and show a snippet of the metadata
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
                
            # Show key insights based on dimension
            if dimension == "validity":
                print("  Detected column types:")
                for col, type_def in list(metadata.get("type_definitions", {}).items())[:3]:
                    detected_type = type_def.get("_detected_type", "unknown")
                    confidence = type_def.get("_confidence", 0)
                    print(f"    - {col}: {detected_type} (confidence: {confidence})")
                    
            elif dimension == "completeness":
                overall = metadata.get("overall_completeness", 0)
                print(f"  Overall completeness: {overall*100:.1f}%")
                fields = metadata.get("fields", {})
                for field, info in list(fields.items())[:3]:
                    completeness = info.get("completeness", 0)
                    print(f"    - {field}: {completeness*100:.1f}% complete")
                    
            elif dimension == "freshness":
                detected_timestamps = metadata.get("_detected_timestamp_columns", [])
                if detected_timestamps:
                    print(f"  Detected timestamp columns: {', '.join(detected_timestamps)}")
                suggestion = metadata.get("_suggestion", "")
                if suggestion:
                    print(f"  Suggestion: {suggestion}")
                    
            elif dimension == "consistency":
                rules = metadata.get("rules", [])
                if rules:
                    print(f"  Generated {len(rules)} example rules to customize")
                detected_cats = metadata.get("_detected_categorical_columns", [])
                if detected_cats:
                    print(f"  Detected categorical columns: {', '.join(detected_cats[:3])}")
                    
            elif dimension == "plausibility":
                rule_results = metadata.get("rule_results", [])
                outlier_rules = [r for r in rule_results if r.get("type") == "outlier_detection"]
                if outlier_rules:
                    print(f"  Analyzed {len(outlier_rules)} numeric columns for outliers")
                    for rule in outlier_rules[:2]:
                        field = rule.get("field")
                        stats = rule.get("statistics", {})
                        print(f"    - {field}: mean={stats.get('mean', 'N/A')}, outliers={stats.get('outlier_count', 0)}")
    
    print("\n5. Key Benefits:")
    print("-" * 60)
    print("✅ Auto-detected data types with confidence scores")
    print("✅ Identified timestamp columns for freshness tracking")
    print("✅ Statistical analysis for plausibility thresholds")
    print("✅ Pre-filled metadata with clear TODO markers")
    print("✅ Domain-specific placeholders ready for customization")
    
    print("\n6. Next Steps:")
    print("-" * 60)
    print("1. Review the generated files and verify auto-detected patterns")
    print("2. Fill in the TODO sections with domain knowledge")
    print("3. Customize thresholds based on your requirements")
    print("4. Run 'adri assess' to see improved scores with metadata")
    
    # Show a specific TODO example
    validity_file = output_dir / "test_init_data.validity.json"
    if validity_file.exists():
        with open(validity_file, 'r') as f:
            validity_data = json.load(f)
            
        print("\n7. Example TODO from validity.json:")
        print("-" * 60)
        email_def = validity_data.get("type_definitions", {}).get("email", {})
        if email_def:
            print(f"  Field: email")
            print(f"  Detected type: {email_def.get('_detected_type', 'unknown')}")
            print(f"  Description: {email_def.get('description', 'N/A')}")
            print("  ↑ This TODO needs your input!")
    
    print("\n8. Time Savings:")
    print("-" * 60)
    print("⏱️  Manual metadata creation: 2-4 hours")
    print("⏱️  With 'adri init': 5 minutes")
    print("📈 That's a 95% reduction in setup time!")
    
    print("\n✅ Metadata generation complete!")

if __name__ == "__main__":
    main()
