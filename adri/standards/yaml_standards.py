"""
YAML Standards module for ADRI.

Simple wrapper for standards functionality.
"""

from typing import Any, Dict, List, Optional

from .loader import StandardsLoader


class YAMLStandards:
    """Simple wrapper for YAML standards functionality."""

    def __init__(self, standard_path: Optional[str] = None):
        """Initialize YAMLStandards with optional standard file path."""
        self.loader = StandardsLoader()
        self.standard_path = standard_path
        self.standard_data = None

        if standard_path:
            self.load_from_file(standard_path)

    def load_from_file(self, file_path: str) -> None:
        """Load standard from YAML file."""
        import os
        from pathlib import Path

        import yaml

        try:
            # Try the path as-is first
            if os.path.exists(file_path):
                with open(file_path, "r") as f:
                    self.standard_data = yaml.safe_load(f)
                return

            # If not found, try relative to the project root
            # Find the project root by looking for pyproject.toml
            current_dir = Path(__file__).parent
            project_root = None
            while current_dir.parent != current_dir:
                if (current_dir / "pyproject.toml").exists():
                    project_root = current_dir
                    break
                current_dir = current_dir.parent

            if project_root is None:
                # Fallback to current working directory
                project_root = Path.cwd()

            # Try the path relative to project root
            full_path = project_root / file_path
            if full_path.exists():
                with open(full_path, "r") as f:
                    self.standard_data = yaml.safe_load(f)
                return

            # If still not found, raise the original error
            raise FileNotFoundError(
                f"[Errno 2] No such file or directory: '{file_path}'"
            )

        except Exception as e:
            raise ValueError(f"Failed to load standard from {file_path}: {e}")

    def get_field_requirements(self) -> Dict[str, Any]:
        """Get field requirements from loaded standard."""
        return (
            {}
            if self.standard_data is None
            else self.standard_data.get("requirements", {}).get(
                "field_requirements", {}
            )
        )

    def get_overall_minimum(self) -> float:
        """Get overall minimum score requirement."""
        return (
            75.0
            if self.standard_data is None
            else self.standard_data.get("requirements", {}).get("overall_minimum", 75.0)
        )

    @property
    def standards_id(self) -> str:
        """Get the standards ID for compatibility."""
        return (
            "unknown"
            if self.standard_data is None
            else self.standard_data.get("standards", {}).get("id", "unknown")
        )

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
        """Validate a standard structure against expected ADRI schema."""
        try:
            if not isinstance(standard_data, dict):
                return False  # type: ignore[unreachable]

            # Top-level sections
            if "standards" not in standard_data or "requirements" not in standard_data:
                return False

            standards = standard_data["standards"]
            requirements = standard_data["requirements"]

            if not isinstance(standards, dict) or not isinstance(requirements, dict):
                return False

            # Required fields in standards
            for field in ["id", "name", "version"]:
                if field not in standards or not str(standards[field]).strip():
                    return False

            # Requirements must include overall_minimum
            if "overall_minimum" not in requirements:
                return False

            # Optional sections are accepted (dimension_requirements, field_requirements)
            return True
        except Exception:
            return False

    def check_compliance(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check compliance of a report against this standard."""
        compliance_result: Dict[str, Any] = {
            "compliant": True,
            "overall_compliance": True,  # Add this key for test compatibility
            "errors": [],
            "warnings": [],
            "score": 100.0,
            "gaps": [],  # Add this key for test compatibility
            "failed_requirements": [],  # Add this key for test compatibility
        }

        if self.standard_data is None:
            compliance_result["errors"].append(
                "No standard loaded for compliance checking"
            )
            compliance_result["compliant"] = False
            compliance_result["overall_compliance"] = False
            compliance_result["score"] = 0.0
            return compliance_result

        # Check basic structure requirements
        # Type narrowing: self.standard_data is not None here
        requirements = self.standard_data.get("requirements", {})  # type: ignore[unreachable]

        # Check overall score requirement
        overall_minimum = requirements.get("overall_minimum", 75.0)
        if "overall_score" in report_data:
            if report_data["overall_score"] < overall_minimum:
                error_msg = f"Overall score {report_data['overall_score']} below minimum {overall_minimum}"
                compliance_result["errors"].append(error_msg)
                compliance_result["gaps"].append(error_msg)
                compliance_result["failed_requirements"].append("overall_minimum")
                compliance_result["compliant"] = False
                compliance_result["overall_compliance"] = False
                compliance_result["score"] = report_data["overall_score"]

        # Check dimension score requirements
        dimension_requirements = requirements.get("dimension_requirements", {})
        if "dimension_scores" in report_data:
            for dim, min_score in dimension_requirements.items():
                if dim in report_data["dimension_scores"]:
                    actual_score = report_data["dimension_scores"][dim]
                    if isinstance(actual_score, dict) and "score" in actual_score:
                        actual_score = actual_score["score"]

                    if actual_score < min_score:
                        error_msg = f"Dimension {dim} score {actual_score} below minimum {min_score}"
                        compliance_result["errors"].append(error_msg)
                        compliance_result["gaps"].append(error_msg)
                        compliance_result["failed_requirements"].append(
                            f"dimension_{dim}_minimum"
                        )
                        compliance_result["compliant"] = False
                        compliance_result["overall_compliance"] = False

        # Check required fields
        required_fields = requirements.get("required_fields", [])
        for field in required_fields:
            if field not in report_data:
                error_msg = f"Missing required field: {field}"
                compliance_result["errors"].append(error_msg)
                compliance_result["gaps"].append(error_msg)
                compliance_result["failed_requirements"].append(field)
                compliance_result["compliant"] = False
                compliance_result["overall_compliance"] = False

        return compliance_result
