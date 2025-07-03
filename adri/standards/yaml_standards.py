"""
YAML Standards module for ADRI.
Provides compatibility layer for legacy imports.
"""

from typing import Any, Dict, List, Optional

from .loader import StandardsLoader


class YAMLStandards:
    """Legacy compatibility class for YAML standards."""

    def __init__(self):
        self.loader = StandardsLoader()

    def list_standards(self) -> List[str]:
        """List all available standards."""
        return self.loader.list_available_standards()

    def load_standard(self, standard_name: str) -> Optional[Dict[str, Any]]:
        """Load a specific standard by name."""
        try:
            return self.loader.load_standard(standard_name)
        except Exception:
            return None

    def validate_standard(self, standard_data: Dict[str, Any]) -> bool:
        """Validate a standard structure."""
        required_fields = ["standard_id", "version", "description"]
        return all(field in standard_data for field in required_fields)
