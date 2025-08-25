"""Allow ADRI package to be run as a module.

This module enables running the ADRI validator using:
    python -m adri

This is equivalent to running the 'adri' command directly.
"""

from .cli.commands import main

if __name__ == "__main__":
    main()
