"""
Standards Cache Cleanup Fixture.

Ensures standards are reloaded fresh for each test, preventing stale cached values.
"""

import pytest


@pytest.fixture(autouse=True, scope="function")
def clear_standards_cache():
    """Clear standards parser cache before each test."""
    try:
        from adri.contracts.parser import ContractsParser
        # Create instance to access cache, but use env var from conftest
        import os
        if "ADRI_STANDARDS_PATH" in os.environ:
            try:
                parser = ContractsParser()
                parser.clear_cache()
            except Exception:
                # If initialization fails, that's ok - cache doesn't exist yet
                pass
    except ImportError:
        # If parser module doesn't exist, no cache to clear
        pass

    yield

    # Clear again after test to prevent pollution
    try:
        from adri.contracts.parser import ContractsParser
        import os
        if "ADRI_STANDARDS_PATH" in os.environ:
            try:
                parser = ContractsParser()
                parser.clear_cache()
            except Exception:
                pass
    except ImportError:
        pass
