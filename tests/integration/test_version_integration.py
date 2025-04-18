"""
Integration tests for the version management system.

These tests verify that version information is properly propagated through
the assessment process and CLI operations.
"""

import json
import os
import tempfile
import unittest
from pathlib import Path

from adri.version import __version__
from adri.cli import main


class TestVersionIntegration(unittest.TestCase):
    """Test the integration of version management with CLI and reports."""

    def setUp(self):
        """Set up test environment."""
        # Create a temporary directory for test outputs
        self.temp_dir = tempfile.TemporaryDirectory()
        
        # Create a path for a sample data file
        self.test_data_dir = Path(__file__).parent.parent / "data"
        self.test_data_file = self.test_data_dir / "sample_data.csv"
        
        # Create output paths
        self.output_prefix = Path(self.temp_dir.name) / "test_output"

    def tearDown(self):
        """Clean up test environment."""
        self.temp_dir.cleanup()

    def test_cli_embeds_version_in_report(self):
        """Test that CLI operation embeds correct version in reports."""
        # Skip if test data file doesn't exist
        if not self.test_data_file.exists():
            self.skipTest(f"Test data file not found: {self.test_data_file}")
        
        # Run CLI to assess the sample data
        args = [
            "assess",
            "--source", str(self.test_data_file),
            "--output", str(self.output_prefix),
            "--format", "json"
        ]
        
        # Temporarily capture stdout to prevent CLI output during tests
        import sys
        from io import StringIO
        original_stdout = sys.stdout
        sys.stdout = StringIO()
        
        try:
            # Run CLI with arguments
            exit_code = main(args)
            self.assertEqual(exit_code, 0, "CLI should exit with code 0")
            
            # Check that the output file exists
            output_file = Path(f"{self.output_prefix}.json")
            self.assertTrue(output_file.exists(), f"Output file {output_file} should exist")
            
            # Read the output file
            with open(output_file, "r") as f:
                report_data = json.load(f)
            
            # Check that version was embedded correctly
            self.assertIn("adri_version", report_data, "Report should contain adri_version field")
            self.assertEqual(report_data["adri_version"], __version__,
                           f"Report should contain current version {__version__}")
            
        finally:
            # Restore stdout
            sys.stdout = original_stdout

    def test_version_consistency_script(self):
        """Test that the version consistency script correctly identifies consistency."""
        # Get path to the verify_version.py script
        script_path = Path(__file__).parent.parent.parent / "scripts" / "verify_version.py"
        if not script_path.exists():
            self.skipTest(f"Version verification script not found at {script_path}")
        
        # Run the script as a module
        import runpy
        import sys
        
        # Save original argv and stdout
        original_argv = sys.argv
        original_stdout = sys.stdout
        
        # Capture stdout
        from io import StringIO
        captured_output = StringIO()
        sys.stdout = captured_output
        
        try:
            # Run the script
            sys.argv = ["verify_version.py"]
            exit_code = 0
            try:
                runpy.run_path(str(script_path), run_name="__main__")
            except SystemExit as e:
                exit_code = e.code
            
            # Check the exit code
            self.assertEqual(exit_code, 0, "Version verification script should exit with code 0")
            
            # Check the output
            output = captured_output.getvalue()
            self.assertIn("Success", output, "Script should report success")
            self.assertIn(__version__, output, f"Script should mention current version {__version__}")
            
        finally:
            # Restore argv and stdout
            sys.argv = original_argv
            sys.stdout = original_stdout


if __name__ == "__main__":
    unittest.main()
