#!/usr/bin/env python3
"""
Thin launcher for ADRI CLI used in integration tests.

This script delegates to the Click CLI defined in adri.cli.commands.main().
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path to ensure imports work
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from adri.cli.commands import main
except ImportError as e:
    print(f"Error importing ADRI CLI: {e}")
    print(f"Python path: {sys.path}")
    print(f"Current directory: {os.getcwd()}")
    print(f"Script location: {__file__}")
    sys.exit(1)

if __name__ == "__main__":
    # main() returns a Click CLI group; calling it executes the CLI
    try:
        main()
    except SystemExit as e:
        sys.exit(e.code)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
