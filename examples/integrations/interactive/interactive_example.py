"""
Example demonstrating the ADRI interactive mode.

This script shows how to use the ADRI interactive mode programmatically.
"""

import os
import sys
import pandas as pd
from pathlib import Path

# Add the parent directory to the path so we can import adri
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from adri.interactive import run_interactive_mode


def create_sample_data():
    """Create a sample CSV file for demonstration."""
    # Create a sample dataframe
    df = pd.DataFrame({
        'id': [1, 2, 3, 4, 5],
        'name': ['Alice', 'Bob', 'Charlie', 'David', 'Eve'],
        'age': [25, 30, 35, 40, 45],
        'email': ['alice@example.com', 'bob@example.com', 'charlie@example.com', 
                 'david@example.com', 'eve@example.com'],
        'score': [85, 90, 75, 95, 80]
    })
    
    # Save to a CSV file
    sample_path = Path(__file__).parent / "sample_data.csv"
    df.to_csv(sample_path, index=False)
    
    return sample_path


def main():
    """Run the interactive mode example."""
    print("ADRI Interactive Mode Example")
    print("============================")
    print()
    print("This example demonstrates how to use the ADRI interactive mode.")
    print("It will create a sample CSV file and then run the interactive mode.")
    print()
    print("In a real application, you would typically run the interactive mode")
    print("directly from the command line with:")
    print("  adri interactive")
    print()
    print("Press Enter to continue...")
    input()
    
    # Create sample data
    sample_path = create_sample_data()
    print(f"Created sample data at: {sample_path}")
    print()
    
    # Run interactive mode
    try:
        print("Running interactive mode...")
        print("Follow the prompts to assess the sample data.")
        print()
        run_interactive_mode()
    except KeyboardInterrupt:
        print("\nInteractive mode interrupted.")
    finally:
        # Clean up
        if os.path.exists(sample_path):
            os.remove(sample_path)
            print(f"Removed sample data file: {sample_path}")


if __name__ == "__main__":
    main()
