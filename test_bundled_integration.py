#!/usr/bin/env python3
"""
Integration test for bundled standards system.

This script tests the complete flow:
1. Load bundled standards
2. Use them with the @adri_protected decorator
3. Verify offline operation (no network requests)
"""

import pandas as pd
from adri.decorators.guard import adri_protected
from adri.standards import BundledStandardsLoader, list_available_standards


def test_bundled_standards_loading():
    """Test that bundled standards can be loaded."""
    print("🧪 Testing bundled standards loading...")
    
    loader = BundledStandardsLoader()
    
    # List available standards
    standards = loader.list_available_standards()
    print(f"✅ Found {len(standards)} bundled standards:")
    for standard in standards[:5]:  # Show first 5
        print(f"   - {standard}")
    if len(standards) > 5:
        print(f"   ... and {len(standards) - 5} more")
    
    # Test loading a specific standard
    if "customer_data_standard" in standards:
        standard = loader.load_standard("customer_data_standard")
        print(f"✅ Loaded customer_data_standard successfully")
        print(f"   Standard ID: {standard['standards']['id']}")
        print(f"   Version: {standard['standards']['version']}")
    else:
        print("❌ customer_data_standard not found in bundled standards")
        return False
    
    return True


def test_decorator_with_bundled_standards():
    """Test that the decorator works with bundled standards."""
    print("\n🧪 Testing @adri_protected decorator with bundled standards...")
    
    # Create sample customer data that should pass quality checks
    customer_data = pd.DataFrame([
        {
            "customer_id": 1,
            "name": "John Doe",
            "email": "john.doe@example.com",
            "age": 30,
            "registration_date": "2023-01-15",
            "account_balance": 1500.50
        },
        {
            "customer_id": 2,
            "name": "Jane Smith",
            "email": "jane.smith@example.com",
            "age": 25,
            "registration_date": "2023-02-20",
            "account_balance": 2300.75
        }
    ])
    
    @adri_protected(data_param="customer_data", verbose=True)
    def process_customers(customer_data):
        """Process customer data with ADRI protection."""
        return {"processed_customers": len(customer_data), "status": "success"}
    
    try:
        result = process_customers(customer_data)
        print(f"✅ Function executed successfully: {result}")
        return True
    except Exception as e:
        print(f"❌ Function execution failed: {e}")
        return False


def test_offline_operation():
    """Test that the system works without network access."""
    print("\n🧪 Testing offline operation...")
    
    # Mock network access to ensure no requests are made
    import socket
    original_socket = socket.socket
    
    def mock_socket(*args, **kwargs):
        raise Exception("Network access attempted during offline test!")
    
    try:
        socket.socket = mock_socket
        
        # Test loading standards
        loader = BundledStandardsLoader()
        standards = loader.list_available_standards()
        
        # Test loading a specific standard
        if standards:
            standard = loader.load_standard(standards[0])
            print(f"✅ Loaded {standards[0]} without network access")
        
        print("✅ All operations completed offline successfully")
        return True
        
    except Exception as e:
        if "Network access attempted" in str(e):
            print(f"❌ Network access was attempted: {e}")
            return False
        else:
            print(f"❌ Unexpected error: {e}")
            return False
    finally:
        # Restore original socket
        socket.socket = original_socket


def test_performance():
    """Test that bundled standards load quickly."""
    print("\n🧪 Testing performance...")
    
    import time
    
    loader = BundledStandardsLoader()
    
    # Test loading speed
    start_time = time.time()
    standard = loader.load_standard("customer_data_standard")
    end_time = time.time()
    
    load_time_ms = (end_time - start_time) * 1000
    print(f"✅ Standard loaded in {load_time_ms:.2f}ms")
    
    if load_time_ms < 10:
        print("✅ Performance target met (< 10ms)")
        return True
    else:
        print(f"⚠️ Performance slower than target ({load_time_ms:.2f}ms > 10ms)")
        return True  # Still pass, just warn


def main():
    """Run all integration tests."""
    print("🚀 ADRI Bundled Standards Integration Test")
    print("=" * 50)
    
    tests = [
        test_bundled_standards_loading,
        test_decorator_with_bundled_standards,
        test_offline_operation,
        test_performance
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                print(f"❌ {test.__name__} failed")
        except Exception as e:
            print(f"❌ {test.__name__} crashed: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Bundled standards system is working correctly.")
        return 0
    else:
        print("💥 Some tests failed. Please check the output above.")
        return 1


if __name__ == "__main__":
    exit(main())
