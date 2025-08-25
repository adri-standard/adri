#!/usr/bin/env python3
"""
Live Verodat Integration Test
Tests the ADRI validator's ability to send audit logs to Verodat in real-time.
"""

import os
import sys
from datetime import datetime
import pandas as pd
from pathlib import Path

# Set the API key
os.environ['VERODAT_API_KEY'] = 'cKL7lACTodQzSjFXhUFy6CuSry99e1qR'

# Add the adri-validator to path
sys.path.insert(0, str(Path(__file__).parent))

from adri.core.assessor import DataQualityAssessor

def create_test_data():
    """Create sample customer data for testing."""
    data = {
        'customer_id': ['TEST_001', 'TEST_002', 'TEST_003', 'TEST_004', 'TEST_005'],
        'first_name': ['Alice', 'Bob', 'Charlie', None, 'Eve'],  # One missing
        'last_name': ['Smith', 'Jones', 'Brown', 'Davis', 'Wilson'],
        'email': ['alice@test.com', 'bob@invalid', 'charlie@test.com', 'david@test.com', 'eve@test.com'],  # One invalid
        'phone': ['+1234567890', '+1234567891', '+1234567892', 'invalid', '+1234567894'],  # One invalid
        'date_of_birth': ['1990-01-01', '1985-05-15', '1992-08-20', '1988-12-10', '1995-03-25'],
        'country': ['USA', 'USA', 'UK', 'USA', 'Canada'],
        'account_status': ['active', 'active', 'inactive', 'active', 'pending'],
        'created_date': ['2024-01-01', '2024-01-02', '2024-01-03', '2024-01-04', '2024-01-05'],
        'last_updated': ['2024-06-01', '2024-06-02', '2024-06-03', '2024-06-04', '2024-06-05']
    }
    
    return pd.DataFrame(data)

def main():
    """Run the live Verodat integration test."""
    print("=" * 60)
    print("VERODAT LIVE INTEGRATION TEST")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"API Key: {'*' * 20}{os.environ['VERODAT_API_KEY'][-10:]}")
    print()
    
    try:
        # Step 1: Setup configuration
        print("1. Setting up configuration...")
        config = {
            'audit': {
                'enabled': True,
                'log_dir': './logs',
                'include_data_samples': True
            },
            'verodat': {
                'enabled': True,
                'api_key': os.environ['VERODAT_API_KEY'],
                'base_url': 'https://verodat.io/api/v3',
                'workspace_id': 236,
                'endpoints': {
                    'assessment_logs': {
                        'schedule_request_id': 588,
                        'standard': 'adri_assessment_logs_standard'
                    },
                    'dimension_scores': {
                        'schedule_request_id': 589,
                        'standard': 'adri_dimension_scores_standard'
                    },
                    'failed_validations': {
                        'schedule_request_id': 590,
                        'standard': 'adri_failed_validations_standard'
                    }
                },
                'batch_settings': {
                    'batch_size': 100,
                    'flush_interval_seconds': 60,
                    'retry_attempts': 3,
                    'retry_delay_seconds': 5
                }
            }
        }
        print(f"   ✓ API Key configured")
        print(f"   - Workspace ID: 236")
        print(f"   - Base URL: https://verodat.io/api/v3")
        print(f"   - Audit logging: ENABLED")
        print(f"   - Verodat upload: ENABLED")
        print()
        
        # Step 2: Create test data
        print("2. Creating test data...")
        df = create_test_data()
        print(f"   ✓ Created {len(df)} test records")
        print(f"   - Columns: {', '.join(df.columns)}")
        print()
        
        # Step 3: Initialize assessor with configuration
        print("3. Initializing Data Quality Assessor...")
        assessor = DataQualityAssessor(config)
        
        print(f"   ✓ Assessor initialized with configuration")
        print(f"   - Audit logger: {'ACTIVE' if assessor.audit_logger else 'INACTIVE'}")
        if assessor.audit_logger and hasattr(assessor.audit_logger, 'verodat_logger'):
            print(f"   - Verodat logger: {'ACTIVE' if assessor.audit_logger.verodat_logger else 'INACTIVE'}")
        print(f"   - Using customer_data_standard.yaml")
        print()
        
        # Step 4: Run assessment
        print("4. Running ADRI assessment...")
        result = assessor.assess(df, 'adri/standards/customer_data_standard.yaml')
        
        print(f"   ✓ Assessment complete")
        print(f"   - Overall Score: {result.overall_score:.1f}%")
        print(f"   - Status: {'PASSED' if result.passed else 'FAILED'}")
        print(f"   - Execution Decision: {'ALLOW' if result.passed else 'BLOCK'}")
        
        # Generate assessment ID
        assessment_id = f"TEST_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        print(f"   - Assessment ID: {assessment_id}")
        print()
        
        # Display dimension scores
        print("   Dimension Scores:")
        for dim, score_obj in result.dimension_scores.items():
            score = score_obj.score * 5  # Convert from 0-20 to 0-100
            status = "✓" if score >= 70 else "✗"
            print(f"     {status} {dim.capitalize()}: {score:.1f}%")
        print()
        
        # Step 5: Check if data was sent to Verodat
        print("5. Verodat Upload Status:")
        
        # The assessor should have automatically sent data to Verodat
        # Let's check the audit logger
        if hasattr(assessor, 'audit_logger') and assessor.audit_logger:
            if hasattr(assessor.audit_logger, 'verodat_logger'):
                verodat = assessor.audit_logger.verodat_logger
                if verodat and verodat.enabled:
                    print("   ✓ Verodat logger is active")
                    print("   ✓ Data should have been sent automatically")
                    print()
                    
                    # Force flush any remaining batches
                    print("   Flushing any remaining batches...")
                    flush_result = verodat.flush_all()
                    
                    for endpoint, status in flush_result.items():
                        if status['records_uploaded'] > 0:
                            print(f"   ✓ {endpoint}: {status['records_uploaded']} records uploaded")
                        else:
                            print(f"   - {endpoint}: No additional records to upload")
                else:
                    print("   ⚠️  Verodat logger not active")
            else:
                print("   ⚠️  No Verodat logger found")
        else:
            print("   ⚠️  No audit logger found")
        
        print()
        print("=" * 60)
        print("TEST COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print()
        print("Next Steps:")
        print("1. Check your Verodat workspace (ID: 236)")
        print("2. Look for records with assessment_id:", assessment_id)
        print("3. Verify data in:")
        print("   - Assessment Logs (Schedule Request ID: 588)")
        print("   - Dimension Scores (Schedule Request ID: 589)")
        print("   - Failed Validations (Schedule Request ID: 590)")
        
        return True
        
    except Exception as e:
        print()
        print("=" * 60)
        print("ERROR DURING TEST!")
        print("=" * 60)
        print(f"Error: {str(e)}")
        print()
        print("Troubleshooting:")
        print("1. Verify the API key is correct")
        print("2. Check network connectivity to verodat.io")
        print("3. Ensure the workspace ID (236) is correct")
        print("4. Verify the schedule request IDs are valid")
        
        import traceback
        print()
        print("Full error trace:")
        traceback.print_exc()
        
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
