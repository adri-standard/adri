"""
Comprehensive tests for api_verodat_bridge feature (ENTERPRISE).

Tests the Verodat API integration for enterprise users.
"""

import unittest
from unittest.mock import patch, MagicMock

from adri_enterprise.logging.verodat import send_to_verodat


class TestVerodatBridge(unittest.TestCase):
    """Test Verodat API bridge functionality."""
    
    def test_send_to_verodat_success(self):
        """Test successful data upload to Verodat API."""
        assessment_data = {
            "assessment_id": "test_001",
            "overall_score": 85.5,
            "passed": True
        }
        
        with patch('requests.post') as mock_post:
            # Mock successful response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response
            
            result = send_to_verodat(
                assessment_data,
                "https://api.verodat.com/upload",
                "test-api-key"
            )
            
            self.assertTrue(result)
            mock_post.assert_called_once()
    
    def test_send_to_verodat_failure(self):
        """Test handling of failed upload to Verodat API."""
        assessment_data = {
            "assessment_id": "test_001",
            "overall_score": 85.5
        }
        
        with patch('requests.post') as mock_post:
            # Mock failed response
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_post.return_value = mock_response
            
            result = send_to_verodat(
                assessment_data,
                "https://api.verodat.com/upload",
                "test-api-key"
            )
            
            self.assertFalse(result)
    
    def test_send_to_verodat_network_error(self):
        """Test handling of network errors."""
        assessment_data = {"assessment_id": "test_001"}
        
        with patch('requests.post') as mock_post:
            # Mock network error
            mock_post.side_effect = Exception("Network error")
            
            result = send_to_verodat(
                assessment_data,
                "https://api.verodat.com/upload",
                "test-api-key"
            )
            
            self.assertFalse(result)
    
    def test_send_to_verodat_auth_headers(self):
        """Test that authentication headers are set correctly."""
        assessment_data = {"test": "data"}
        
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response
            
            send_to_verodat(
                assessment_data,
                "https://api.verodat.com/upload",
                "my-secret-key"
            )
            
            # Verify headers were set
            call_kwargs = mock_post.call_args[1]
            self.assertIn("headers", call_kwargs)
            headers = call_kwargs["headers"]
            self.assertEqual(headers["Authorization"], "ApiKey my-secret-key")
            self.assertEqual(headers["Content-Type"], "application/json")
    
    def test_send_to_verodat_timeout(self):
        """Test that timeout is configured."""
        assessment_data = {"test": "data"}
        
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response
            
            send_to_verodat(
                assessment_data,
                "https://api.verodat.com/upload",
                "api-key"
            )
            
            # Verify timeout was set
            call_kwargs = mock_post.call_args[1]
            self.assertIn("timeout", call_kwargs)
            self.assertEqual(call_kwargs["timeout"], 30)
    
    def test_send_to_verodat_json_payload(self):
        """Test that data is sent as JSON payload."""
        assessment_data = {
            "assessment_id": "test_001",
            "score": 85.5,
            "passed": True
        }
        
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response
            
            send_to_verodat(
                assessment_data,
                "https://api.verodat.com/upload",
                "api-key"
            )
            
            # Verify JSON payload was sent
            call_kwargs = mock_post.call_args[1]
            self.assertIn("json", call_kwargs)
            
            # Verify request was made (implementation batches data internally)
            mock_post.assert_called_once()
            
            # Verify headers were set correctly
            self.assertIn("headers", call_kwargs)
            self.assertEqual(call_kwargs["headers"]["Content-Type"], "application/json")


class TestVerodatIntegration(unittest.TestCase):
    """Integration tests for Verodat API bridge."""
    
    @patch('requests.post')
    def test_complete_upload_workflow(self, mock_post):
        """Test complete upload workflow."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        # Simulate complete assessment data
        assessment_data = {
            "assessment_id": "adri_20240101_100000_abc123",
            "timestamp": "2024-01-01T10:00:00Z",
            "overall_score": 88.5,
            "passed": True,
            "dimension_scores": {
                "validity": 18.0,
                "completeness": 19.0,
                "consistency": 17.5,
                "freshness": 18.5,
                "plausibility": 15.5
            },
            "data_row_count": 150,
            "standard_id": "customer_data_standard"
        }
        
        result = send_to_verodat(
            assessment_data,
            "https://api.verodat.com/assessments",
            "enterprise-api-key-12345"
        )
        
        self.assertTrue(result)
        
        # Verify API was called with correct parameters
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        
        # Verify URL
        self.assertEqual(call_args[0][0], "https://api.verodat.com/assessments")
        
        # Verify authentication
        headers = call_args[1]["headers"]
        self.assertIn("ApiKey enterprise-api-key-12345", headers["Authorization"])


class TestVerodatErrorHandling(unittest.TestCase):
    """Test error handling for Verodat integration."""
    
    @patch('requests.post')
    def test_handles_400_error(self, mock_post):
        """Test handling of 400 Bad Request."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_post.return_value = mock_response
        
        result = send_to_verodat(
            {"test": "data"},
            "https://api.verodat.com/upload",
            "api-key"
        )
        
        self.assertFalse(result)
    
    @patch('requests.post')
    def test_handles_401_unauthorized(self, mock_post):
        """Test handling of 401 Unauthorized."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_post.return_value = mock_response
        
        result = send_to_verodat(
            {"test": "data"},
            "https://api.verodat.com/upload",
            "invalid-key"
        )
        
        self.assertFalse(result)
    
    @patch('requests.post')
    def test_handles_timeout(self, mock_post):
        """Test handling of request timeout."""
        import requests
        mock_post.side_effect = requests.Timeout("Request timed out")
        
        result = send_to_verodat(
            {"test": "data"},
            "https://api.verodat.com/upload",
            "api-key"
        )
        
        self.assertFalse(result)
    
    @patch('requests.post')
    def test_handles_connection_error(self, mock_post):
        """Test handling of connection errors."""
        import requests
        mock_post.side_effect = requests.ConnectionError("Connection failed")
        
        result = send_to_verodat(
            {"test": "data"},
            "https://api.verodat.com/upload",
            "api-key"
        )
        
        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()
