"""
Tests for the show-config CLI command.
"""

import json
import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path

from adri.cli.commands import show_config_command
from adri.config.manager import ConfigManager


class TestShowConfigCommand(unittest.TestCase):
    """Test cases for the show-config command."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_config = {
            'adri': {
                'version': '2.0',
                'project_name': 'Test Project',
                'environments': {
                    'development': {
                        'paths': {
                            'standards': './test/dev/standards',
                            'assessments': './test/dev/assessments',
                            'training_data': './test/dev/training-data'
                        }
                    },
                    'production': {
                        'paths': {
                            'standards': './test/prod/standards',
                            'assessments': './test/prod/assessments',
                            'training_data': './test/prod/training-data'
                        }
                    }
                },
                'default_environment': 'development',
                'assessment': {
                    'caching': {
                        'enabled': True,
                        'strategy': 'content_hash',
                        'ttl': '24h'
                    },
                    'output': {
                        'format': 'json',
                        'include_recommendations': True,
                        'include_raw_scores': False
                    },
                    'performance': {
                        'max_rows': 1000000,
                        'timeout': '5m'
                    }
                },
                'generation': {
                    'default_thresholds': {
                        'completeness_min': 85,
                        'validity_min': 90,
                        'consistency_min': 80,
                        'freshness_max_age': '7d',
                        'plausibility_outlier_threshold': 3.0
                    }
                }
            }
        }
    
    @patch('adri.cli.commands.ConfigManager')
    @patch('builtins.print')
    def test_show_config_no_config_found(self, mock_print, mock_config_manager):
        """Test show-config when no configuration is found."""
        # Setup
        mock_manager = MagicMock()
        mock_manager.get_active_config.return_value = None
        mock_config_manager.return_value = mock_manager
        
        # Execute
        result = show_config_command()
        
        # Verify
        self.assertEqual(result, 1)
        mock_print.assert_any_call("❌ No ADRI configuration found")
        mock_print.assert_any_call("💡 Run 'adri setup' to initialize ADRI in this project")
    
    @patch('adri.cli.commands.ConfigManager')
    @patch('builtins.print')
    def test_show_config_invalid_config(self, mock_print, mock_config_manager):
        """Test show-config with invalid configuration."""
        # Setup
        mock_manager = MagicMock()
        mock_manager.get_active_config.return_value = {'invalid': 'config'}
        mock_manager.validate_config.return_value = False
        mock_config_manager.return_value = mock_manager
        
        # Execute
        result = show_config_command()
        
        # Verify
        self.assertEqual(result, 1)
        mock_print.assert_any_call("❌ Invalid configuration structure")
    
    @patch('adri.cli.commands.ConfigManager')
    @patch('builtins.print')
    def test_show_config_human_format(self, mock_print, mock_config_manager):
        """Test show-config with human-readable format."""
        # Setup
        mock_manager = MagicMock()
        mock_manager.get_active_config.return_value = self.test_config
        mock_manager.validate_config.return_value = True
        mock_config_manager.return_value = mock_manager
        
        # Execute
        result = show_config_command(format_type="human")
        
        # Verify
        self.assertEqual(result, 0)
        
        # Check that key information is printed
        printed_calls = [str(call) for call in mock_print.call_args_list]
        printed_text = ' '.join(printed_calls)
        
        self.assertIn("📋 ADRI Configuration", printed_text)
        self.assertIn("Test Project", printed_text)
        self.assertIn("Development Paths", printed_text)
        self.assertIn("Production Paths", printed_text)
        self.assertIn("Assessment Settings", printed_text)
        self.assertIn("Generation Thresholds", printed_text)
    
    @patch('adri.cli.commands.ConfigManager')
    @patch('builtins.print')
    def test_show_config_json_format(self, mock_print, mock_config_manager):
        """Test show-config with JSON format."""
        # Setup
        mock_manager = MagicMock()
        mock_manager.get_active_config.return_value = self.test_config
        mock_manager.validate_config.return_value = True
        mock_config_manager.return_value = mock_manager
        
        # Execute
        result = show_config_command(format_type="json")
        
        # Verify
        self.assertEqual(result, 0)
        
        # Check that JSON is printed
        printed_calls = [call[0][0] for call in mock_print.call_args_list]
        self.assertEqual(len(printed_calls), 1)
        
        # Verify it's valid JSON
        json_output = json.loads(printed_calls[0])
        self.assertIn("config", json_output)
        self.assertIn("active_environment", json_output)
        self.assertEqual(json_output["active_environment"], "development")
    
    @patch('adri.cli.commands.ConfigManager')
    @patch('builtins.print')
    def test_show_config_specific_environment(self, mock_print, mock_config_manager):
        """Test show-config for specific environment."""
        # Setup
        mock_manager = MagicMock()
        mock_manager.get_active_config.return_value = self.test_config
        mock_manager.validate_config.return_value = True
        mock_config_manager.return_value = mock_manager
        
        # Execute
        result = show_config_command(environment="production")
        
        # Verify
        self.assertEqual(result, 0)
        
        # Check that only production paths are shown
        printed_calls = [str(call) for call in mock_print.call_args_list]
        printed_text = ' '.join(printed_calls)
        
        self.assertIn("Production Paths", printed_text)
        self.assertNotIn("Development Paths", printed_text)
    
    @patch('adri.cli.commands.ConfigManager')
    @patch('builtins.print')
    def test_show_config_paths_only(self, mock_print, mock_config_manager):
        """Test show-config with paths-only option."""
        # Setup
        mock_manager = MagicMock()
        mock_manager.get_active_config.return_value = self.test_config
        mock_manager.validate_config.return_value = True
        mock_config_manager.return_value = mock_manager
        
        # Execute
        result = show_config_command(paths_only=True)
        
        # Verify
        self.assertEqual(result, 0)
        
        # Check that only paths are shown
        printed_calls = [str(call) for call in mock_print.call_args_list]
        printed_text = ' '.join(printed_calls)
        
        self.assertIn("Development Paths", printed_text)
        self.assertIn("Production Paths", printed_text)
        self.assertNotIn("ADRI Configuration", printed_text)
        self.assertNotIn("Assessment Settings", printed_text)
        self.assertNotIn("Generation Thresholds", printed_text)
    
    @patch('adri.cli.commands.ConfigManager')
    @patch('builtins.print')
    def test_show_config_with_validation(self, mock_print, mock_config_manager):
        """Test show-config with validation enabled."""
        # Setup
        mock_manager = MagicMock()
        mock_manager.get_active_config.return_value = self.test_config
        mock_manager.validate_config.return_value = True
        
        # Mock validation results
        validation_results = {
            'valid': True,
            'errors': [],
            'warnings': ['Test warning'],
            'path_status': {
                'development.standards': {
                    'exists': True,
                    'is_directory': True,
                    'readable': True,
                    'writable': True,
                    'file_count': 2
                },
                'development.assessments': {
                    'exists': True,
                    'is_directory': True,
                    'readable': True,
                    'writable': True,
                    'file_count': 0
                }
            }
        }
        mock_manager.validate_paths.return_value = validation_results
        mock_config_manager.return_value = mock_manager
        
        # Execute
        result = show_config_command(validate=True)
        
        # Verify
        self.assertEqual(result, 0)
        
        # Check that validation results are shown
        printed_calls = [str(call) for call in mock_print.call_args_list]
        printed_text = ' '.join(printed_calls)
        
        self.assertIn("Path Validation", printed_text)
        self.assertIn("Configuration is valid", printed_text)
        self.assertIn("(2 files)", printed_text)
        self.assertIn("(0 files)", printed_text)
    
    @patch('adri.cli.commands.ConfigManager')
    @patch('builtins.print')
    def test_show_config_validation_errors(self, mock_print, mock_config_manager):
        """Test show-config with validation errors."""
        # Setup
        mock_manager = MagicMock()
        mock_manager.get_active_config.return_value = self.test_config
        mock_manager.validate_config.return_value = True
        
        # Mock validation results with errors
        validation_results = {
            'valid': False,
            'errors': ['Path not readable: /test/path'],
            'warnings': ['Directory is empty'],
            'path_status': {}
        }
        mock_manager.validate_paths.return_value = validation_results
        mock_config_manager.return_value = mock_manager
        
        # Execute
        result = show_config_command(validate=True)
        
        # Verify
        self.assertEqual(result, 0)
        
        # Check that errors are shown
        printed_calls = [str(call) for call in mock_print.call_args_list]
        printed_text = ' '.join(printed_calls)
        
        self.assertIn("Configuration has errors", printed_text)
        self.assertIn("Path not readable", printed_text)
        self.assertIn("Directory is empty", printed_text)
    
    @patch('adri.cli.commands.ConfigManager')
    @patch('builtins.print')
    def test_show_config_nonexistent_environment(self, mock_print, mock_config_manager):
        """Test show-config with non-existent environment."""
        # Setup
        mock_manager = MagicMock()
        mock_manager.get_active_config.return_value = self.test_config
        mock_manager.validate_config.return_value = True
        mock_config_manager.return_value = mock_manager
        
        # Execute
        result = show_config_command(environment="nonexistent")
        
        # Verify
        self.assertEqual(result, 0)
        
        # Check that error message is shown
        printed_calls = [str(call) for call in mock_print.call_args_list]
        printed_text = ' '.join(printed_calls)
        
        self.assertIn("Environment 'nonexistent' not found", printed_text)
    
    @patch('adri.cli.commands.ConfigManager')
    @patch('builtins.print')
    def test_show_config_exception_handling(self, mock_print, mock_config_manager):
        """Test show-config exception handling."""
        # Setup
        mock_manager = MagicMock()
        mock_manager.get_active_config.side_effect = Exception("Test error")
        mock_config_manager.return_value = mock_manager
        
        # Execute
        result = show_config_command()
        
        # Verify
        self.assertEqual(result, 1)
        mock_print.assert_any_call("❌ Error: Failed to show configuration: Test error")


if __name__ == '__main__':
    unittest.main()
