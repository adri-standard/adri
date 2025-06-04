"""
Integration tests for quickstart workflow.

Tests the complete SEE IT → TRY IT → USE IT flow and verifies
that quickstart scripts work together with ADRI components.
"""

import os
import sys
import subprocess
import tempfile
from pathlib import Path
import pytest
import json

# Get project root
project_root = Path(__file__).parent.parent.parent
quickstart_dir = project_root / "quickstart"


class TestQuickstartWorkflow:
    """Test the complete quickstart user journey."""
    
    def test_see_it_workflow(self):
        """Test the SEE IT step - viewing pre-generated output."""
        output_file = quickstart_dir / "outputs" / "crm_audit.txt"
        
        # Verify the file exists and contains expected content
        assert output_file.exists()
        content = output_file.read_text()
        
        # Check for key business insights
        assert "REVENUE AT RISK" in content
        assert "$" in content  # Dollar amounts
        assert "missing close dates" in content
        assert "DATA QUALITY SCORE" in content
    
    def test_try_it_workflow(self):
        """Test the TRY IT step - running assessment without ADRI installed."""
        # Run the try_it.py script on sample data
        script_path = quickstart_dir / "try_it.py"
        sample_path = quickstart_dir / "samples" / "crm_data.csv"
        
        result = subprocess.run(
            [sys.executable, str(script_path), str(sample_path)],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, f"Script failed: {result.stderr}"
        
        # Check output contains expected elements
        output = result.stdout
        assert "ADRI ASSESSMENT RESULTS" in output
        assert "Overall Data Quality Score:" in output
        assert "Business Impact:" in output
        assert "Key Findings:" in output
    
    def test_use_it_workflow(self):
        """Test the USE IT step - using full ADRI on quickstart data."""
        # This tests that quickstart data works with full ADRI
        from adri.assessor import DataSourceAssessor
        
        sample_path = quickstart_dir / "samples" / "crm_data.csv"
        assessor = DataSourceAssessor()
        report = assessor.assess_file(sample_path)
        
        # Verify assessment works
        assert report is not None
        assert report.overall_score >= 0
        assert report.overall_score <= 100
        assert len(report.dimension_results) == 5
    
    def test_progressive_engagement_flow(self):
        """Test that each step builds on the previous one."""
        # Step 1: SEE IT - Check pre-generated output exists
        crm_output = quickstart_dir / "outputs" / "crm_audit.txt"
        assert crm_output.exists()
        see_it_content = crm_output.read_text()
        
        # Step 2: TRY IT - Run minimal assessment
        script_path = quickstart_dir / "try_it.py"
        sample_path = quickstart_dir / "samples" / "crm_data.csv"
        
        result = subprocess.run(
            [sys.executable, str(script_path), str(sample_path)],
            capture_output=True,
            text=True
        )
        try_it_output = result.stdout
        
        # Step 3: USE IT - Full assessment
        from adri.assessor import DataSourceAssessor
        assessor = DataSourceAssessor()
        report = assessor.assess_file(sample_path)
        
        # Verify progression of detail
        # SEE IT shows business impact
        assert "$" in see_it_content
        assert "REVENUE AT RISK" in see_it_content
        
        # TRY IT shows assessment scores
        assert "Overall Data Quality Score:" in try_it_output
        assert "/100" in try_it_output
        
        # USE IT provides full programmatic access
        assert hasattr(report, 'dimension_results')
        assert hasattr(report, 'save_html')


class TestQuickstartDataCompatibility:
    """Test that quickstart sample data works with various ADRI features."""
    
    def test_guard_with_quickstart_data(self):
        """Test ADRI guard functionality with quickstart samples."""
        from adri.integrations.guard import adri_guarded
        
        @adri_guarded(min_score=50)  # Lower threshold for test
        def process_data(data_source):
            return f"Processing {data_source}"
        
        # Test with different sample files
        samples = ["crm_data.csv", "inventory.csv", "customers.csv"]
        
        for sample in samples:
            sample_path = str(quickstart_dir / "samples" / sample)
            
            # Should either pass or raise ValueError with clear message
            try:
                result = process_data(sample_path)
                assert "Processing" in result
            except ValueError as e:
                error_msg = str(e)
                assert "Data quality insufficient" in error_msg
                assert "ADRI Score:" in error_msg
                assert "/100" in error_msg
    
    def test_cli_with_quickstart_data(self):
        """Test CLI assessment with quickstart samples."""
        sample_path = quickstart_dir / "samples" / "inventory.csv"
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_base = Path(tmpdir) / "test_report"
            
            result = subprocess.run(
                [
                    "adri", "assess",
                    "--source", str(sample_path),
                    "--output", str(output_base)
                ],
                capture_output=True,
                text=True
            )
            
            # Check CLI ran successfully
            assert result.returncode == 0, f"CLI failed: {result.stderr}"
            
            # Check outputs were created
            assert (output_base.with_suffix('.json')).exists()
            assert (output_base.with_suffix('.html')).exists()
            
            # Verify JSON report structure
            with open(output_base.with_suffix('.json'), 'r') as f:
                report_data = json.load(f)
                assert 'overall_score' in report_data
                assert 'dimension_results' in report_data
    
    def test_report_generation_with_quickstart_data(self):
        """Test that reports can be generated from quickstart data."""
        from adri.assessor import DataSourceAssessor
        
        sample_path = quickstart_dir / "samples" / "customers.csv"
        assessor = DataSourceAssessor()
        report = assessor.assess_file(sample_path)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Test JSON report
            json_path = Path(tmpdir) / "test_report.json"
            report.save_json(str(json_path))
            # The save_json method changes the filename to .adri_score_report.json
            expected_json_path = Path(tmpdir) / "test_report.adri_score_report.json"
            assert expected_json_path.exists()
            
            # Test HTML report
            html_path = Path(tmpdir) / "test_report.html"
            report.save_html(str(html_path))
            assert html_path.exists()
            
            # Verify HTML contains expected content
            html_content = html_path.read_text()
            # Check that it's an ADRI report
            assert "agent data readiness index" in html_content.lower()
            # Check for dimensions or score indicators
            assert "dimension" in html_content.lower() or "validity" in html_content.lower() or "completeness" in html_content.lower()


class TestQuickstartExampleAlignment:
    """Test that quickstart examples align with main documentation."""
    
    def test_readme_quickstart_consistency(self):
        """Test that README examples match quickstart functionality."""
        # Read the main README
        readme_path = project_root / "README.md"
        readme_content = readme_path.read_text()
        
        # Check that quickstart or examples are mentioned
        assert "quickstart" in readme_content.lower() or "examples/" in readme_content
        
        # Check that key example files are mentioned or exist
        assert "template_guard_demo.py" in readme_content or (project_root / "examples" / "template_guard_demo.py").exists()
    
    def test_quickstart_readme_exists(self):
        """Test that quickstart has its own README."""
        quickstart_readme = quickstart_dir / "README.md"
        assert quickstart_readme.exists()
        
        content = quickstart_readme.read_text()
        
        # Check for essential sections
        assert "SEE IT" in content
        assert "TRY IT" in content
        assert "USE IT" in content
        # Check for the journey concept (may be called different things)
        assert "Journey" in content or "3-Step" in content or "Steps" in content
