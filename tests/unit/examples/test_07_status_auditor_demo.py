"""
Unit tests for the AI Status Auditor demo example.

Tests verify that the demo correctly:
1. Generates sample CRM data with expected issues
2. Creates proper ADRI metadata files
3. Translates technical results to business language
4. Demonstrates the value proposition
"""

import unittest
from unittest.mock import patch, MagicMock, mock_open
import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta
from pathlib import Path
import sys
import os

# Add examples directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'examples'))

# Import the module to test
import importlib.util
spec = importlib.util.spec_from_file_location(
    "status_auditor_demo",
    os.path.join(os.path.dirname(__file__), '..', '..', '..', 'examples', '07_status_auditor_demo.py')
)
status_auditor_demo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(status_auditor_demo)


class TestStatusAuditorDemo(unittest.TestCase):
    """Test the AI Status Auditor demo functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Set random seed for reproducibility
        np.random.seed(42)
        
    def test_create_sample_crm_data(self):
        """Test that sample CRM data is created with expected issues"""
        # Mock file operations
        with patch('pandas.DataFrame.to_csv'):
            csv_path, df = status_auditor_demo.create_sample_crm_data()
            
        # Verify data structure
        self.assertEqual(len(df), 200)
        self.assertIn('opportunity_id', df.columns)
        self.assertIn('stage', df.columns)
        self.assertIn('amount', df.columns)
        self.assertIn('close_date', df.columns)
        self.assertIn('contact_email', df.columns)
        
        # Verify intentional data quality issues exist
        # 1. Missing close dates in late stages
        late_stage_deals = df[df['stage'].isin(['negotiation', 'proposal'])]
        missing_close_dates = late_stage_deals['close_date'].isna().sum()
        self.assertGreater(missing_close_dates, 0, "Should have missing close dates")
        
        # 2. Stale deals (old activity)
        active_deals = df[~df['stage'].isin(['closed-won', 'closed-lost'])]
        stale_deals = active_deals[active_deals['days_since_last_activity'] > 14]
        self.assertGreater(len(stale_deals), 0, "Should have stale deals")
        
        # 3. Missing contact emails
        missing_emails = df['contact_email'].isna().sum()
        self.assertGreater(missing_emails, 0, "Should have missing emails")
        
        # 4. Ownership conflicts
        ownership_conflicts = df[df['owner'] != df['account_owner']]
        self.assertEqual(len(ownership_conflicts), 30, "Should have exactly 30 ownership conflicts")
        
    def test_create_revops_metadata(self):
        """Test ADRI metadata creation for RevOps audit"""
        # Mock file operations
        mock_files = {}
        
        def mock_open_func(filename, mode='r'):
            if mode == 'w':
                mock_files[filename] = MagicMock()
                return mock_files[filename]
            return MagicMock()
        
        with patch('builtins.open', mock_open_func):
            status_auditor_demo.create_revops_metadata()
        
        # Verify all 5 dimension files were created
        expected_files = [
            'crm_audit_demo.validity.json',
            'crm_audit_demo.completeness.json',
            'crm_audit_demo.freshness.json',
            'crm_audit_demo.consistency.json',
            'crm_audit_demo.plausibility.json'
        ]
        
        for filename in expected_files:
            self.assertIn(filename, mock_files, f"Should create {filename}")
            
        # Verify JSON content was written
        for filename, mock_file in mock_files.items():
            # Check that json.dump was called
            write_calls = mock_file.__enter__().write.call_args_list
            self.assertGreater(len(write_calls), 0, f"Should write content to {filename}")
            
    def test_translate_to_business_language(self):
        """Test translation of ADRI results to business language"""
        # Create sample data
        df = pd.DataFrame({
            'opportunity_id': ['OPP-001', 'OPP-002', 'OPP-003'],
            'deal_name': ['Deal 1', 'Deal 2', 'Deal 3'],
            'stage': ['negotiation', 'proposal', 'qualification'],
            'amount': [50000, 75000, 30000],
            'close_date': [pd.NaT, pd.NaT, datetime.now()],
            'owner': ['John Smith', 'Mary Johnson', 'John Smith'],
            'account_owner': ['John Smith', 'John Smith', 'John Smith'],  # Mismatch for Mary
            'contact_email': [None, 'test@test.com', None],
            'days_since_last_activity': [20, 5, 30],
            'last_activity_date': [
                datetime.now() - timedelta(days=20),
                datetime.now() - timedelta(days=5),
                datetime.now() - timedelta(days=30)
            ]
        })
        
        # Mock assessment results
        mock_results = {
            'overall_score': 65,
            'dimension_scores': {
                'validity': 85,
                'completeness': 55,
                'freshness': 60,
                'consistency': 75,
                'plausibility': 90
            }
        }
        
        # Generate report
        report = status_auditor_demo.translate_to_business_language(mock_results, df)
        
        # Verify report content
        self.assertIn('CRM AUDIT REPORT', report)
        self.assertIn('NEEDS ATTENTION', report)  # Score is 65
        self.assertIn('REVENUE AT RISK', report)
        self.assertIn('2 deals worth $125,000 missing close dates', report)
        self.assertIn('PROCESS BREAKDOWNS', report)
        self.assertIn('ownership conflicts', report)
        self.assertIn('IMMEDIATE ACTIONS', report)
        
    def test_business_impact_identification(self):
        """Test that business impacts are correctly identified"""
        # Create data with specific issues
        df = pd.DataFrame({
            'opportunity_id': [f'OPP-{i:03d}' for i in range(10)],
            'deal_name': [f'Deal {i}' for i in range(10)],  # Add deal_name column
            'stage': ['negotiation'] * 5 + ['closed-won'] * 3 + ['qualification'] * 2,
            'amount': [100000] * 10,
            'close_date': [pd.NaT] * 5 + [datetime.now()] * 5,
            'owner': ['Owner1'] * 10,
            'account_owner': ['Owner1'] * 7 + ['Owner2'] * 3,
            'contact_email': [None] * 4 + ['email@test.com'] * 6,
            'days_since_last_activity': [30] * 3 + [5] * 7,
            'last_activity_date': [datetime.now() - timedelta(days=d) 
                                  for d in [30] * 3 + [5] * 7]
        })
        
        mock_results = {'overall_score': 50, 'dimension_scores': {}}
        report = status_auditor_demo.translate_to_business_language(mock_results, df)
        
        # Verify specific business impacts are identified
        self.assertIn('$500,000 missing close dates', report)  # 5 deals at 100k each
        self.assertIn('3 opportunities have ownership conflicts', report)
        
    @patch('pandas.DataFrame.to_csv')
    @patch('builtins.open', new_callable=mock_open)
    @patch('adri.assessor.DataSourceAssessor')
    def test_main_workflow(self, mock_assessor, mock_file, mock_to_csv):
        """Test the complete demo workflow"""
        # Mock assessor
        mock_assessor_instance = MagicMock()
        mock_assessor.return_value = mock_assessor_instance
        # Mock assess_file to raise exception for demo behavior
        mock_assessor_instance.assess_file.side_effect = Exception("Expected for demo")
        
        # Capture print output
        with patch('builtins.print') as mock_print:
            status_auditor_demo.main()
        
        # Verify workflow steps
        print_calls = [call[0][0] for call in mock_print.call_args_list if call[0]]
        
        # Check for key workflow markers
        workflow_markers = [
            "AI STATUS AUDITOR DEMO",
            "Creating sample CRM data",
            "Creating ADRI audit rules",
            "Running ADRI assessment",
            "Generating business audit report",
            "THE AHA MOMENT"
        ]
        
        for marker in workflow_markers:
            self.assertTrue(
                any(marker in str(call) for call in print_calls),
                f"Workflow should include: {marker}"
            )
            
    def test_demo_demonstrates_all_dimensions(self):
        """Test that demo showcases all 5 ADRI dimensions"""
        # Create metadata files and verify all dimensions are covered
        metadata_content = {}
        
        # Mock open to track file writes
        def mock_open_func(filename, mode='r'):
            if mode == 'w':
                mock_file = MagicMock()
                # Store reference to track what gets written
                metadata_content[filename] = {'file': mock_file, 'data': None}
                return mock_file
            return MagicMock()
            
        def capture_json_dump(data, file, **kwargs):
            # Find which file this is by checking stored references
            for filename, info in metadata_content.items():
                if info['file'] == file or info['file'].__enter__() == file:
                    info['data'] = data
                    break
                    
        with patch('builtins.open', mock_open_func):
            with patch('json.dump', side_effect=capture_json_dump):
                status_auditor_demo.create_revops_metadata()
        
        # Verify each dimension has rules with business impact
        dimensions = ['validity', 'completeness', 'freshness', 'consistency', 'plausibility']
        
        for dim in dimensions:
            filename = f'crm_audit_demo.{dim}.json'
            self.assertIn(filename, metadata_content, f"Should create {filename}")
            data = metadata_content[filename]['data']
            self.assertIsNotNone(data, f"Should write data to {filename}")
            self.assertIn('rules', data, f"{dim} should have rules defined")
                         
    def test_actionable_output(self):
        """Test that output provides actionable recommendations"""
        # Create minimal data
        df = pd.DataFrame({
            'opportunity_id': ['OPP-001'],
            'stage': ['negotiation'],
            'amount': [50000],
            'close_date': [pd.NaT],
            'owner': ['John Smith'],
            'account_owner': ['Mary Johnson'],
            'contact_email': [None],
            'days_since_last_activity': [30],
            'deal_name': ['Big Deal'],
            'last_activity_date': [datetime.now() - timedelta(days=30)]
        })
        
        results = {'overall_score': 40, 'dimension_scores': {}}
        report = status_auditor_demo.translate_to_business_language(results, df)
        
        # Verify actionable items
        self.assertIn('IMMEDIATE ACTIONS', report)
        self.assertIn('Update close dates', report)
        self.assertIn('Review stale deals', report)
        
    def test_realistic_data_patterns(self):
        """Test that generated data follows realistic patterns"""
        with patch('pandas.DataFrame.to_csv'):
            _, df = status_auditor_demo.create_sample_crm_data()
        
        # Check realistic distributions
        stage_distribution = df['stage'].value_counts()
        self.assertGreater(stage_distribution['proposal'], stage_distribution['closed-won'],
                          "More deals should be in pipeline than closed")
        
        # Check amounts follow log-normal distribution (realistic for deals)
        amounts = df['amount'].values
        self.assertGreater(amounts.max(), amounts.mean() * 3,
                          "Should have some large deals (log-normal distribution)")
        
        # Check ownership is distributed among team
        unique_owners = df['owner'].nunique()
        self.assertEqual(unique_owners, 5, "Should have 5 sales reps")


if __name__ == '__main__':
    unittest.main()
