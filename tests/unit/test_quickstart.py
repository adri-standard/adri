"""
Unit tests for quickstart components.

This ensures the zero-dependency quickstart scripts work correctly
and produce the expected business-friendly output.
"""

import os
import sys
import subprocess
from pathlib import Path
import tempfile
import pytest
from unittest.mock import patch, mock_open

# Add the quickstart directory to the path so we can import the modules
quickstart_dir = Path(__file__).parent.parent.parent / "quickstart"
sys.path.insert(0, str(quickstart_dir))


class TestTryItScript:
    """Test the zero-dependency try_it.py script."""
    
    def test_minimal_adri_initialization(self):
        """Test that MinimalADRI can be initialized."""
        from try_it import MinimalADRI
        assessor = MinimalADRI()
        assert assessor is not None
        assert hasattr(assessor, 'assess_csv')
    
    def test_parse_number(self):
        """Test number parsing function."""
        from try_it import MinimalADRI
        assessor = MinimalADRI()
        
        assert assessor._parse_number("1000") == 1000
        assert assessor._parse_number("$1,500.50") == 1500.50
        assert assessor._parse_number("") == 0
        assert assessor._parse_number("invalid") == 0
    
    def test_script_execution(self):
        """Test that the script can be executed without errors."""
        # Create a test CSV
        test_data = "opportunity_id,amount,stage,close_date\n1,50000,negotiation,\n2,75000,proposal,2025-06-01\n"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='_crm.csv', delete=False) as f:
            f.write(test_data)
            temp_path = f.name
        
        try:
            # Run the script as a subprocess
            result = subprocess.run(
                [sys.executable, str(quickstart_dir / "try_it.py"), temp_path],
                capture_output=True,
                text=True
            )
            
            # Check it ran successfully
            assert result.returncode == 0
            
            # Check output contains expected elements
            output = result.stdout
            assert "ADRI ASSESSMENT RESULTS" in output
            assert "Overall Data Quality Score:" in output
            assert "/100" in output
            assert "Business Impact:" in output
        finally:
            os.unlink(temp_path)


class TestSeeItScript:
    """Test the see_it.py script menu system."""
    
    def test_show_crm_audit_function(self):
        """Test the show_crm_audit function displays expected content."""
        from see_it import show_crm_audit
        import io
        import sys
        
        # Capture output
        captured_output = io.StringIO()
        sys.stdout = captured_output
        
        try:
            show_crm_audit()
            output = captured_output.getvalue()
            
            # Check key content
            assert 'CRM AUDIT REPORT' in output
            assert '$340,575' in output  # Revenue at risk
            assert 'missing close dates' in output
            assert 'DATA QUALITY SCORE: 68/100' in output
        finally:
            sys.stdout = sys.__stdout__
    
    def test_see_it_script_execution(self):
        """Test that see_it.py can be executed."""
        # Run with option 1 (CRM)
        result = subprocess.run(
            [sys.executable, str(quickstart_dir / "see_it.py")],
            input="1\n",
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        output = result.stdout
        
        # Check menu displayed
        assert "ADRI QUICKSTART" in output
        assert "Available Reports:" in output
        
        # Check CRM content displayed
        assert "CRM AUDIT REPORT" in output
        assert "REVENUE AT RISK" in output
    
    def test_output_files_exist(self):
        """Test that pre-generated output files exist."""
        outputs_dir = quickstart_dir / "outputs"
        
        expected_files = [
            "crm_audit.txt",
            "inventory_audit.txt",
            "customer_audit.txt"
        ]
        
        for filename in expected_files:
            filepath = outputs_dir / filename
            assert filepath.exists(), f"Output file {filename} not found"
            
            # Check file is not empty
            content = filepath.read_text()
            assert len(content) > 100, f"Output file {filename} appears empty"
            
            # Check for key indicators
            assert "AUDIT" in content or "DATA QUALITY" in content


class TestQuickstartSamples:
    """Test the sample data files."""
    
    def test_sample_files_exist(self):
        """Test that all sample CSV files exist."""
        samples_dir = quickstart_dir / "samples"
        
        expected_files = [
            "crm_data.csv",
            "inventory.csv",
            "customers.csv"
        ]
        
        for filename in expected_files:
            filepath = samples_dir / filename
            assert filepath.exists(), f"Sample file {filename} not found"
    
    def test_crm_data_structure(self):
        """Test CRM sample data has expected structure."""
        import csv
        
        crm_file = quickstart_dir / "samples" / "crm_data.csv"
        with open(crm_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            # Check we have data
            assert len(rows) > 0
            
            # Check expected columns exist
            expected_cols = ['opportunity_id', 'amount', 'stage']
            first_row = rows[0]
            for col in expected_cols:
                assert col in first_row, f"Expected column {col} not found"
            
            # Check for realistic issues
            missing_close_dates = sum(1 for row in rows if not row.get('close_date'))
            assert missing_close_dates > 0, "Sample should have missing close dates"
    
    def test_inventory_data_issues(self):
        """Test inventory sample has realistic data issues."""
        import csv
        
        inv_file = quickstart_dir / "samples" / "inventory.csv"
        with open(inv_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            # Check for negative reorder thresholds
            negative_thresholds = [
                row for row in rows 
                if row.get('reorder_threshold') and float(row['reorder_threshold']) < 0
            ]
            assert len(negative_thresholds) > 0, "Sample should have negative thresholds"
    
    def test_customer_data_issues(self):
        """Test customer sample has data quality issues."""
        import csv
        
        cust_file = quickstart_dir / "samples" / "customers.csv"
        with open(cust_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            # Check for data issues
            # There's a duplicate name (John Smith) with different details
            names = [(row.get('first_name'), row.get('last_name')) for row in rows]
            assert len(names) != len(set(names)), "Sample should have duplicate names"
            
            # Check for invalid data
            invalid_emails = sum(1 for row in rows if '@' not in row.get('email', '') or '.' not in row.get('email', '').split('@')[-1])
            assert invalid_emails > 0, "Sample should have invalid email formats"


# Clean up sys.path after tests
def teardown_module(module):
    """Remove quickstart from path after tests."""
    if str(quickstart_dir) in sys.path:
        sys.path.remove(str(quickstart_dir))
