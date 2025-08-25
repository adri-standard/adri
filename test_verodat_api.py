#!/usr/bin/env python3
"""
Direct Verodat API Test
Tests the API key and workspace access directly.
"""

import json
import os

import requests

# Set the API key
API_KEY = "AUTOLOAD_API_KEY"
BASE_URL = "https://verodat.io/api/v3"


def test_api_connection():
    """Test basic API connection and authentication."""
    print("=" * 60)
    print("VERODAT API DIAGNOSTIC TEST")
    print("=" * 60)
    print(f"API Key: {'*' * 20}{API_KEY[-10:]}")
    print(f"Base URL: {BASE_URL}")
    print()

    # Test 1: Check API key validity with a simple endpoint
    print("1. Testing API Authentication with ApiKey prefix...")
    headers = {"Authorization": f"ApiKey {API_KEY}", "Content-Type": "application/json"}

    # Try to get workspace info
    workspace_id = 236
    url = f"{BASE_URL}/workspaces/{workspace_id}"

    print(f"   Testing: GET {url}")
    response = requests.get(url, headers=headers)
    print(f"   Response Status: {response.status_code}")

    if response.status_code == 200:
        print("   ✓ API authentication successful!")
        print(f"   Response: {response.text[:200]}...")
    elif response.status_code == 401:
        print("   ✗ Authentication failed (401)")
        print(f"   Response: {response.text}")
    elif response.status_code == 404:
        print("   ✗ Workspace not found (404)")
        print("   The workspace ID might be incorrect")
    else:
        print(f"   ✗ Unexpected status: {response.status_code}")
        print(f"   Response: {response.text}")

    print()

    # Test 2: Try without prefix (raw key)
    print("2. Testing Authorization with raw API key...")
    headers2 = {"Authorization": API_KEY, "Content-Type": "application/json"}

    response2 = requests.get(url, headers=headers2)
    print(f"   Response Status: {response2.status_code}")

    if response2.status_code == 200:
        print("   ✓ Alternative auth format works!")
        print(f"   Response: {response2.text[:200]}...")
    else:
        print(f"   ✗ Alternative format failed: {response2.status_code}")

    print()

    # Test 3: Test upload endpoint
    print("3. Testing Upload Endpoint...")
    schedule_request_id = 588
    upload_url = f"{BASE_URL}/workspaces/{workspace_id}/schedule-request/{schedule_request_id}/autoload/upload"

    print(f"   Testing: POST {upload_url}")

    # Try with Bearer token
    test_data = {
        "data": [
            {
                "header": [
                    {"name": "assessment_id", "type": "string"},
                    {"name": "timestamp", "type": "string"},
                ]
            },
            {"rows": [["TEST_001", "2025-08-11T23:00:00Z"]]},
        ]
    }

    response3 = requests.post(upload_url, headers=headers, json=test_data)
    print(f"   Response Status: {response3.status_code}")

    if response3.status_code in [200, 201, 202]:
        print("   ✓ Upload endpoint accessible!")
        print(f"   Response: {response3.text[:200]}...")
    elif response3.status_code == 401:
        print("   ✗ Authentication failed for upload")
        print(f"   Response: {response3.text}")
    elif response3.status_code == 404:
        print("   ✗ Schedule request ID not found")
    else:
        print(f"   ✗ Upload failed: {response3.status_code}")
        print(f"   Response: {response3.text}")

    print()
    print("=" * 60)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 60)
    print()
    print("Summary:")
    print("- If authentication is failing, the API key may be invalid or expired")
    print("- If workspace/schedule requests are not found, the IDs may be incorrect")
    print("- Check with your Verodat admin for correct configuration values")


if __name__ == "__main__":
    test_api_connection()
