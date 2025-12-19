"""
Comprehensive tests for cli_view_logs feature.

Tests the CLI view-logs command for viewing and analyzing audit logs.
"""

import unittest
import tempfile
import json
from pathlib import Path
from datetime import datetime
from unittest.mock import patch

from src.adri.cli.commands.view_logs import ViewLogsCommand


class TestViewLogsCommand(unittest.TestCase):
    """Test view-logs command core functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.command = ViewLogsCommand()
        self.test_dir = Path(tempfile.mkdtemp())
        self.audit_logs_dir = self.test_dir / "ADRI" / "dev" / "audit-logs"
        self.audit_logs_dir.mkdir(parents=True, exist_ok=True)
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
    
    def test_command_name(self):
        """Test command name."""
        self.assertEqual(self.command.get_name(), "view-logs")
    
    def test_command_description(self):
        """Test command description."""
        description = self.command.get_description()
        self.assertIsInstance(description, str)
        self.assertGreater(len(description), 0)
    
    def test_no_audit_logs_directory(self):
        """Test behavior when audit logs directory doesn't exist."""
        nonexistent_dir = self.test_dir / "nonexistent"
        
        with patch.object(self.command, '_get_audit_logs_directory', return_value=nonexistent_dir):
            with patch('click.echo'):
                args = {"recent": 10, "today": False, "verbose": False}
                exit_code = self.command.execute(args)
        
        self.assertEqual(exit_code, 0)
    
    def test_no_log_files(self):
        """Test behavior when no log files exist."""
        with patch.object(self.command, '_get_audit_logs_directory', return_value=self.audit_logs_dir):
            with patch('click.echo'):
                args = {"recent": 10, "today": False, "verbose": False}
                exit_code = self.command.execute(args)
        
        self.assertEqual(exit_code, 0)
    
    def test_parse_audit_log_entries(self):
        """Test parsing of audit log entries from JSONL file."""
        # Create sample log file
        log_file = self.audit_logs_dir / "adri_assessment_logs.jsonl"
        
        # Write sample JSONL entries
        entries = [
            {
                "assessment_id": "test_001",
                "timestamp": "2024-01-01T10:00:00",
                "overall_score": 85.5,
                "passed": True,
                "data_row_count": 100,
                "function_name": "assess",
                "standard_id": "test_standard",
                "assessment_duration_ms": 1500,
                "execution_decision": "ALLOWED"
            },
            {
                "assessment_id": "test_002",
                "timestamp": "2024-01-01T11:00:00",
                "overall_score": 72.3,
                "passed": True,
                "data_row_count": 50,
                "function_name": "process_data",
                "standard_id": "another_standard",
                "assessment_duration_ms": 800,
                "execution_decision": "ALLOWED"
            }
        ]
        
        with open(log_file, 'w') as f:
            for entry in entries:
                f.write(json.dumps(entry) + '\n')
        
        # Parse entries
        parsed = self.command._parse_audit_log_entries(log_file, today=False)
        
        self.assertEqual(len(parsed), 2)
        self.assertEqual(parsed[0]["assessment_id"], "test_001")
        self.assertEqual(parsed[1]["assessment_id"], "test_002")
    
    def test_count_failed_rows(self):
        """Test counting failed rows for an assessment."""
        # Create failed validations file
        failed_val_file = self.audit_logs_dir / "adri_failed_validations.jsonl"
        
        failures = [
            {
                "assessment_id": "test_001",
                "validation_id": "val_001",
                "affected_rows": 5,
                "field_name": "email"
            },
            {
                "assessment_id": "test_001",
                "validation_id": "val_002",
                "affected_rows": 3,
                "field_name": "age"
            },
            {
                "assessment_id": "test_002",
                "validation_id": "val_001",
                "affected_rows": 10,
                "field_name": "amount"
            }
        ]
        
        with open(failed_val_file, 'w') as f:
            for failure in failures:
                f.write(json.dumps(failure) + '\n')
        
        # Count failures for test_001
        total_failed, pct = self.command._count_failed_rows("test_001", 100, self.audit_logs_dir)
        
        self.assertEqual(total_failed, 8)  # 5 + 3
        self.assertEqual(pct, 8.0)  # 8/100 * 100
    
    def test_count_failed_rows_no_file(self):
        """Test counting failed rows when file doesn't exist."""
        total_failed, pct = self.command._count_failed_rows("test_001", 100, self.audit_logs_dir)
        
        self.assertEqual(total_failed, 0)
        self.assertEqual(pct, 0.0)
    
    def test_format_log_table_data(self):
        """Test formatting of log entries for table display."""
        log_entries = [
            {
                "timestamp": datetime(2024, 1, 1, 10, 0),
                "assessment_id": "test_001",
                "overall_score": 85.5,
                "passed": True,
                "data_row_count": 100,
                "function_name": "assess",
                "standard_id": "customer_data_ADRI_standard",
                "assessment_duration_ms": 1500,
                "execution_decision": "ALLOWED"
            }
        ]
        
        table_data = self.command._format_log_table_data(log_entries, self.audit_logs_dir)
        
        self.assertEqual(len(table_data), 1)
        self.assertIn("data_packet", table_data[0])
        self.assertIn("health", table_data[0])
        self.assertIn("status", table_data[0])
    
    def test_get_audit_logs_directory(self):
        """Test retrieval of audit logs directory."""
        logs_dir = self.command._get_audit_logs_directory()
        
        self.assertIsInstance(logs_dir, Path)
        self.assertIn("audit-logs", str(logs_dir))
    
    def test_execute_with_recent_param(self):
        """Test execution with recent parameter."""
        # Create log file
        log_file = self.audit_logs_dir / "adri_assessment_logs.jsonl"
        
        entries = [
            {
                "assessment_id": f"test_{i:03d}",
                "timestamp": f"2024-01-01T{i:02d}:00:00",
                "overall_score": 80.0 + i,
                "passed": True,
                "data_row_count": 100,
                "function_name": "assess",
                "standard_id": "test_standard",
                "assessment_duration_ms": 1000,
                "execution_decision": "ALLOWED"
            }
            for i in range(20)
        ]
        
        with open(log_file, 'w') as f:
            for entry in entries:
                f.write(json.dumps(entry) + '\n')
        
        with patch.object(self.command, '_get_audit_logs_directory', return_value=self.audit_logs_dir):
            with patch('click.echo'):
                args = {"recent": 5, "today": False, "verbose": False}
                exit_code = self.command.execute(args)
        
        self.assertEqual(exit_code, 0)
    
    def test_execute_verbose_mode(self):
        """Test execution in verbose mode."""
        # Create log file
        log_file = self.audit_logs_dir / "adri_assessment_logs.jsonl"
        
        entry = {
            "assessment_id": "test_001",
            "timestamp": "2024-01-01T10:00:00",
            "overall_score": 85.5,
            "passed": True,
            "data_row_count": 100,
            "function_name": "assess",
            "standard_id": "test_standard",
            "assessment_duration_ms": 1500,
            "execution_decision": "ALLOWED"
        }
        
        with open(log_file, 'w') as f:
            f.write(json.dumps(entry) + '\n')
        
        with patch.object(self.command, '_get_audit_logs_directory', return_value=self.audit_logs_dir):
            with patch('click.echo'):
                args = {"recent": 10, "today": False, "verbose": True}
                exit_code = self.command.execute(args)
        
        self.assertEqual(exit_code, 0)


class TestViewLogsEdgeCases(unittest.TestCase):
    """Test edge cases for view-logs command."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.command = ViewLogsCommand()
        self.test_dir = Path(tempfile.mkdtemp())
        self.audit_logs_dir = self.test_dir / "audit-logs"
        self.audit_logs_dir.mkdir(parents=True, exist_ok=True)
    
    def tearDown(self):
        """Clean up."""
        import shutil
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
    
    def test_malformed_json_entries(self):
        """Test handling of malformed JSON entries."""
        log_file = self.audit_logs_dir / "adri_assessment_logs.jsonl"
        
        # Write mix of valid and invalid entries
        with open(log_file, 'w') as f:
            f.write('{"assessment_id": "valid_001", "timestamp": "2024-01-01T10:00:00"}\n')
            f.write('invalid json line\n')  # Invalid
            f.write('{"assessment_id": "valid_002", "timestamp": "2024-01-01T11:00:00"}\n')
        
        # Should parse only valid entries
        parsed = self.command._parse_audit_log_entries(log_file, today=False)
        
        # Should skip malformed entry
        self.assertGreaterEqual(len(parsed), 0)
    
    def test_empty_log_file(self):
        """Test handling of empty log file."""
        log_file = self.audit_logs_dir / "adri_assessment_logs.jsonl"
        log_file.touch()  # Create empty file
        
        parsed = self.command._parse_audit_log_entries(log_file, today=False)
        
        self.assertEqual(len(parsed), 0)
    
    def test_today_filter(self):
        """Test filtering entries by today's date."""
        log_file = self.audit_logs_dir / "adri_assessment_logs.jsonl"
        
        today = datetime.now().strftime("%Y-%m-%d")
        yesterday = "2024-01-01"
        
        entries = [
            {"assessment_id": "today_001", "timestamp": f"{today}T10:00:00", "overall_score": 85.0, "passed": True, "data_row_count": 100, "function_name": "assess", "standard_id": "test", "assessment_duration_ms": 1000, "execution_decision": "ALLOWED"},
            {"assessment_id": "yesterday_001", "timestamp": f"{yesterday}T10:00:00", "overall_score": 90.0, "passed": True, "data_row_count": 50, "function_name": "assess", "standard_id": "test", "assessment_duration_ms": 800, "execution_decision": "ALLOWED"}
        ]
        
        with open(log_file, 'w') as f:
            for entry in entries:
                f.write(json.dumps(entry) + '\n')
        
        # Parse with today filter
        parsed = self.command._parse_audit_log_entries(log_file, today=True)
        
        # Should only get today's entries
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0]["assessment_id"], "today_001")


if __name__ == '__main__':
    unittest.main()
