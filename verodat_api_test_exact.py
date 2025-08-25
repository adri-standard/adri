#!/usr/bin/env python3
"""
Exact Verodat API Call Test
Shows the exact request being made for debugging with Verodat support.
"""

import requests
import json
from datetime import datetime

def test_exact_api_call():
    """Show exact API call format."""
    print("=" * 60)
    print("EXACT VERODAT API CALL TEST")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    # Configuration
    API_KEY = 'YOUR_API_KEY_HERE'  # Replace with actual key
    BASE_URL = 'https://verodat.io/api/v3'
    WORKSPACE_ID = 236
    SCHEDULE_REQUEST_ID = 588
    
    print("CONFIGURATION:")
    print(f"  API Key: {API_KEY}")
    print(f"  Base URL: {BASE_URL}")
    print(f"  Workspace ID: {WORKSPACE_ID}")
    print(f"  Schedule Request ID: {SCHEDULE_REQUEST_ID}")
    print()
    
    # Build the exact URL
    url = f"{BASE_URL}/workspaces/{WORKSPACE_ID}/schedule-request/{SCHEDULE_REQUEST_ID}/autoload/upload"
    
    # Build the exact headers
    headers = {
        "Authorization": f"ApiKey {API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Build the exact payload
    payload = {
        "data": [
            {
                "header": [
                    {"name": "assessment_id", "type": "string"},
                    {"name": "timestamp", "type": "date"},
                    {"name": "adri_version", "type": "string"},
                    {"name": "function_name", "type": "string"},
                    {"name": "overall_score", "type": "numeric"},
                    {"name": "passed", "type": "string"},
                    {"name": "data_row_count", "type": "numeric"}
                ]
            },
            {
                "rows": [
                    [
                        "TEST_001",
                        "2025-08-11T23:00:00Z",
                        "3.0.0",
                        "test_function",
                        86.1,
                        "TRUE",
                        5
                    ]
                ]
            }
        ]
    }
    
    print("EXACT REQUEST DETAILS:")
    print(f"  Method: POST")
    print(f"  URL: {url}")
    print()
    
    print("HEADERS:")
    for key, value in headers.items():
        print(f"  {key}: {value}")
    print()
    
    print("PAYLOAD:")
    print(json.dumps(payload, indent=2))
    print()
    
    print("=" * 60)
    print("MAKING REQUEST...")
    print("=" * 60)
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Headers:")
        for key, value in response.headers.items():
            if key.lower() in ['content-type', 'date', 'server']:
                print(f"  {key}: {value}")
        print()
        print("Response Body:")
        print(response.text)
        
        if response.status_code == 200:
            print()
            print("✅ SUCCESS! API call worked!")
        elif response.status_code == 401:
            print()
            print("❌ AUTHENTICATION FAILED")
            print("Possible issues:")
            print("1. API key is invalid or expired")
            print("2. API key doesn't have access to workspace 236")
            print("3. Authorization header format is incorrect")
        elif response.status_code == 404:
            print()
            print("❌ NOT FOUND")
            print("Possible issues:")
            print("1. Workspace ID 236 doesn't exist")
            print("2. Schedule Request ID 588 doesn't exist")
            print("3. URL endpoint has changed")
        else:
            print()
            print(f"❌ UNEXPECTED ERROR: {response.status_code}")
            
    except Exception as e:
        print(f"❌ REQUEST FAILED: {e}")
    
    print()
    print("=" * 60)
    print("CURL EQUIVALENT:")
    print("=" * 60)
    print("You can test this same request using curl:")
    print()
    print(f'''curl -X POST "{url}" \\
  -H "Authorization: ApiKey {API_KEY}" \\
  -H "Content-Type: application/json" \\
  -d '{json.dumps(payload)}'
''')

if __name__ == "__main__":
    test_exact_api_call()
