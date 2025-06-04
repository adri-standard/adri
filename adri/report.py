"""
ADRI Score Report generation and handling.

This module provides the ADRIScoreReport class that encapsulates the results
of an ADRI assessment and provides methods to save, load, and visualize reports.
"""

import json
import logging
import warnings
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union

import matplotlib.pyplot as plt
import pandas as pd
from jinja2 import Environment, FileSystemLoader

from .version import (
    __version__,
    is_version_compatible,
    get_score_compatibility_message
)

logger = logging.getLogger(__name__)


class ADRIScoreReport:
    """ADRI Score Report - Data quality assessment results."""

    def __init__(
        self,
        source_name: str,
        source_type: str,
        source_metadata: Dict[str, Any],
        assessment_time: Optional[datetime] = None,
        adri_version: Optional[str] = None,
        assessment_config: Optional[Dict[str, Any]] = None,
        template_match: Optional[Dict[str, Any]] = None,
        assessment_mode: Optional[str] = None,
    ):
        """
        Initialize an ADRI Score Report.

        Args:
            source_name: Name of the assessed data source
            source_type: Type of data source (file, database, api, etc.)
            source_metadata: Metadata about the data source
            assessment_time: When the assessment was performed
            adri_version: Version of the ADRI tool used for assessment
            assessment_config: Configuration used for the assessment
            template_match: Information about template matching
            assessment_mode: Mode of assessment (discovery or validation)
        """
        self.source_name = source_name
        self.source_type = source_type
        self.source_metadata = source_metadata
        self.assessment_time = assessment_time or datetime.now()
        self.adri_version = adri_version or __version__
        self.assessment_config = assessment_config or {}
        
        # These will be populated by populate_from_dimension_results
        self.overall_score = 0
        self.dimension_results = {}
        
        # Template evaluation results (if assessed against templates)
        self.template_evaluations = []
        
        # Enhanced metadata for future provenance support
        self.metadata = {
            "assessed_at": self.assessment_time.isoformat(),
            "adri_version": self.adri_version,
            "assessment_mode": assessment_mode or "discovery",
            "template": template_match or {
                "id": None,
                "version": None,
                "match_confidence": None,
                "match_type": None
            }
        }
        
        # Placeholder for future provenance implementation
        self.provenance = None  # Will hold hashes, signatures, etc.
    
    def validate(self) -> Dict[str, Any]:
        """
        Validate the report structure and values.
        
        Returns:
            Dict with validation results:
            - is_valid: bool indicating if report is valid
            - errors: list of validation errors
            - warnings: list of validation warnings
        """
        errors = []
        warnings = []
        
        # Check overall score range
        if not 0 <= self.overall_score <= 100:
            errors.append(f"Overall score {self.overall_score} out of valid range [0-100]")
        
        # Check required fields
        if not self.source_name:
            errors.append("Missing required field: source_name")
        if not self.source_type:
            errors.append("Missing required field: source_type")
        if not self.assessment_time:
            errors.append("Missing required field: assessment_time")
        
        # Check dimension results
        expected_dimensions = {"validity", "completeness", "freshness", "consistency", "plausibility"}
        actual_dimensions = set(self.dimension_results.keys())
        
        missing_dimensions = expected_dimensions - actual_dimensions
        if missing_dimensions:
            errors.append(f"Missing dimensions: {missing_dimensions}")
        
        extra_dimensions = actual_dimensions - expected_dimensions
        if extra_dimensions:
            warnings.append(f"Unexpected dimensions: {extra_dimensions}")
        
        # Validate each dimension
        for dim_name, dim_result in self.dimension_results.items():
            # Check score range
            if "score" not in dim_result:
                errors.append(f"Dimension '{dim_name}' missing 'score' field")
            else:
                score = dim_result["score"]
                if not isinstance(score, (int, float)):
                    errors.append(f"Dimension '{dim_name}' score must be numeric, got {type(score).__name__}")
                elif not 0 <= score <= 20:
                    errors.append(f"Dimension '{dim_name}' score {score} out of valid range [0-20]")
            
            # Check findings and recommendations structure
            if "findings" in dim_result and not isinstance(dim_result["findings"], list):
                errors.append(f"Dimension '{dim_name}' findings must be a list")
            if "recommendations" in dim_result and not isinstance(dim_result["recommendations"], list):
                errors.append(f"Dimension '{dim_name}' recommendations must be a list")
        
        # Calculate expected total score
        if not errors and not missing_dimensions:  # Only check if all required dimensions present
            # For extra dimensions, just check that the overall score is reasonable
            if extra_dimensions:
                # With extra dimensions, overall score could be higher than 100
                min_expected = sum(
                    self.dimension_results[dim]["score"] 
                    for dim in expected_dimensions 
                    if dim in self.dimension_results
                )
                if self.overall_score < min_expected:
                    errors.append(
                        f"Overall score {self.overall_score} is less than sum of standard dimensions {min_expected}"
                    )
            else:
                # Without extra dimensions, should match exactly
                expected_total = sum(
                    self.dimension_results[dim]["score"] 
                    for dim in expected_dimensions 
                    if dim in self.dimension_results
                )
                if abs(self.overall_score - expected_total) > 0.01:  # Allow small floating point differences
                    errors.append(
                        f"Overall score {self.overall_score} doesn't match sum of dimensions {expected_total}"
                    )
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    @classmethod
    def validate_json(cls, path: Union[str, Path]) -> Dict[str, Any]:
        """
        Validate a report JSON file without fully loading it.
        
        Args:
            path: Path to the report JSON file
            
        Returns:
            Dict with validation results
        """
        try:
            # Load and validate JSON structure
            with open(path, "r") as f:
                data = json.load(f)
            
            # Check top-level structure
            if "adri_score_report" not in data:
                return {
                    "is_valid": False,
                    "errors": ["Invalid format: missing 'adri_score_report' root key"],
                    "warnings": []
                }
            
            # Load as report and validate
            report = cls.from_dict(data)
            return report.validate()
            
        except json.JSONDecodeError as e:
            return {
                "is_valid": False,
                "errors": [f"Invalid JSON: {str(e)}"],
                "warnings": []
            }
        except Exception as e:
            return {
                "is_valid": False,
                "errors": [f"Failed to load report: {str(e)}"],
                "warnings": []
            }

    def populate_from_dimension_results(self, dimension_results: Dict[str, Dict[str, Any]]):
        """
        Populate the report with results from dimension assessments.

        Args:
            dimension_results: Dictionary of results for each dimension
        """
        self.dimension_results = dimension_results
        
        # Calculate overall score (sum of all dimension scores, max 100)
        dimension_scores = [d["score"] for d in dimension_results.values()]
        self.overall_score = sum(dimension_scores)  # Sum of all dimensions (5 * 20 = 100 max)

    def _calculate_grade(self) -> str:
        """
        Calculate letter grade based on overall score.

        Returns:
            str: Letter grade (A, B, C, D, or F)
        """
        if self.overall_score >= 90:
            return "A"
        elif self.overall_score >= 80:
            return "B"
        elif self.overall_score >= 70:
            return "C"
        elif self.overall_score >= 60:
            return "D"
        else:
            return "F"

    def _get_status(self) -> str:
        """
        Get simplified status based on overall score.

        Returns:
            str: Status description
        """
        if self.overall_score >= 80:
            return "AI Ready"
        elif self.overall_score >= 60:
            return "Needs Attention"
        else:
            return "Not AI Ready"

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the report to a dictionary structure.

        Returns:
            Dict: Dictionary representation of the report
        """
        return {
            "adri_score_report": {
                "report_version": "1.0.0",
                "adri_version": self.adri_version,
                "generated_at": self.assessment_time.isoformat(),
                
                "summary": {
                    "overall_score": self.overall_score,
                    "grade": self._calculate_grade(),
                    "status": self._get_status(),
                    "data_source": self.source_name
                },
                
                "dimensions": self.dimension_results,  # Include full details
                
                "metadata": self.metadata,
                
                "provenance": self.provenance  # None for now, ready for future
            }
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ADRIScoreReport":
        """
        Create a report from a dictionary.

        Args:
            data: Dictionary representation of a report

        Returns:
            ADRIScoreReport: Reconstructed report object
        """
        # Only support the new format
        if "adri_score_report" not in data:
            raise ValueError("Invalid report format. Expected 'adri_score_report' structure.")
            
        report_data = data["adri_score_report"]
        
        # Create basic metadata from the new structure
        source_metadata = report_data.get("metadata", {})
        
        report = cls(
            source_name=report_data["summary"]["data_source"],
            source_type="file",  # Default since not stored in new format
            source_metadata=source_metadata,
            assessment_time=datetime.fromisoformat(report_data["generated_at"]),
            adri_version=report_data.get("adri_version"),
        )
        
        # Set the scores
        report.overall_score = report_data["summary"]["overall_score"]
        
        # Set dimension results (includes scores, findings, recommendations)
        report.dimension_results = report_data["dimensions"]
        
        return report

    def save_json(self, path: Union[str, Path]):
        """
        Save the report to a JSON file.

        Args:
            path: Path to save the report
        """
        # Ensure proper file extension
        path = Path(path)
        if not path.suffix:
            path = path.with_suffix('.adri_score_report.json')
        elif path.suffix == '.json':
            # Replace .json with .adri_score_report.json
            path = path.with_suffix('').with_suffix('.adri_score_report.json')
            
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)
        logger.info(f"ADRI Score Report saved to {path}")

    @classmethod
    def load_json(cls, path: Union[str, Path]) -> "ADRIScoreReport":
        """
        Load a report from a JSON file.

        Args:
            path: Path to the report file

        Returns:
            ADRIScoreReport: Loaded report
        """
        with open(path, "r") as f:
            data = json.load(f)
            
        return cls.from_dict(data)

    def generate_radar_chart(self, save_path: Optional[Union[str, Path]] = None):
        """
        Generate a radar chart visualization of the dimension scores.

        Args:
            save_path: Optional path to save the chart
        """
        # Extract dimension names and scores
        dimensions = list(self.dimension_results.keys())
        scores = [self.dimension_results[dim]["score"] for dim in dimensions]
        
        # Create radar chart
        fig, ax = plt.subplots(figsize=(10, 8), subplot_kw={"polar": True})
        
        # Compute angles for each dimension
        angles = [n / float(len(dimensions)) * 2 * 3.14159 for n in range(len(dimensions))]
        angles += angles[:1]  # Close the loop
        
        # Add scores and close loop
        scores += scores[:1]
        
        # Plot data
        ax.plot(angles, scores, linewidth=2, linestyle="solid")
        ax.fill(angles, scores, alpha=0.25)
        
        # Fix axis to start at top and correct direction
        ax.set_theta_offset(3.14159 / 2)
        ax.set_theta_direction(-1)
        
        # Set axis labels
        plt.xticks(angles[:-1], [d.title() for d in dimensions])
        
        # Set y-axis
        ax.set_rlabel_position(0)
        plt.yticks([5, 10, 15, 20], ["5", "10", "15", "20"], color="grey", size=8)
        plt.ylim(0, 20)
        
        # Add title
        plt.title(
            f"ADRI Score Report: {self.source_name}\n"
            f"Overall Score: {self.overall_score:.1f}/100 (Grade: {self._calculate_grade()})",
            size=15,
            y=1.1,
        )
        
        if save_path:
            plt.savefig(save_path, bbox_inches="tight")
            logger.info(f"Radar chart saved to {save_path}")
        return fig

    def save_html(self, path: Union[str, Path]):
        """
        Save the report as an HTML file.

        Args:
            path: Path to save the HTML report
        """
        # Get the directory where this module is located
        module_dir = Path(__file__).parent
        templates_dir = module_dir / "templates"
        
        # Check if the template file exists
        template_file = templates_dir / "report_template.html"
        if not template_file.exists():
            raise FileNotFoundError(f"Template file not found: {template_file}")
        
        # Configure Jinja2
        env = Environment(loader=FileSystemLoader(str(templates_dir)))
        template = env.get_template("report_template.html")
        
        # Generate radar chart and encode it in base64
        import tempfile
        import base64
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            self.generate_radar_chart(tmp.name)
            with open(tmp.name, "rb") as img_file:
                radar_b64 = base64.b64encode(img_file.read()).decode("utf-8")
        
        # Render HTML template
        html_content = template.render(
            report=self,
            radar_chart_b64=radar_b64,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            adri_version=self.adri_version,
            assessment_config=self.assessment_config,
            grade=self._calculate_grade(),
            status=self._get_status()
        )
        
        # Save the rendered HTML report
        with open(path, "w", encoding="utf-8") as f:
            f.write(html_content)
        logger.info(f"HTML report saved to {path}")

    def print_summary(self):
        """Print a summary of the report to the console."""
        print(f"\n✨ ADRI Score Report")
        print("━" * 40)
        print(f"Overall Score: {self.overall_score}/100 (Grade: {self._calculate_grade()})")
        print(f"Status: {self._get_status()} {'✅' if self.overall_score >= 80 else '❌'}")
        
        print("\nDimension Scores:")
        for dim, results in self.dimension_results.items():
            score = results['score']
            bar_length = int(score)
            bar = "█" * bar_length + "░" * (20 - bar_length)
            print(f"• {dim.title():<14} {score:>2}/20 {bar}")
        
        # Count total findings across all dimensions
        total_findings = sum(
            len(results.get('findings', [])) 
            for results in self.dimension_results.values()
        )
        if total_findings > 0:
            print(f"\nFound {total_findings} issues that need attention.")
            print(f"Run 'adri show {self.source_name}' for details.")
        
        print(f"\nReport saved: {self.source_name}.adri_score_report.json")
        print(f"ADRI v{self.adri_version} | Generated: {self.assessment_time.strftime('%Y-%m-%d %H:%M:%S')}")
