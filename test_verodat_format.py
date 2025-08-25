#!/usr/bin/env python3
"""Test script to verify Verodat data format matches the required schema."""

import json
import yaml
from datetime import datetime
from adri.core.audit_logger import AuditRecord
from adri.core.verodat_logger import VerodatLogger

def load_verodat_config():
    """Load the Verodat configuration provided by the user."""
    verodat_schema = {
        "data_stores": [
            {
                "name": "adri_assessment_logs",
                "target_fields": [
                    {"name": "assessment_id", "type": "string"},
                    {"name": "log_timestamp", "type": "date"},
                    {"name": "adri_version", "type": "string"},
                    {"name": "assessment_type", "type": "string"},
                    {"name": "function_name", "type": "string"},
                    {"name": "module_path", "type": "string"},
                    {"name": "environment", "type": "string"},
                    {"name": "hostname", "type": "string"},
                    {"name": "process_id", "type": "integer"},
                    {"name": "standard_id", "type": "string"},
                    {"name": "standard_version", "type": "string"},
                    {"name": "standard_checksum", "type": "string"},
                    {"name": "data_row_count", "type": "integer"},
                    {"name": "data_column_count", "type": "integer"},
                    {"name": "data_columns", "type": "string"},
                    {"name": "data_checksum", "type": "string"},
                    {"name": "overall_score", "type": "number"},
                    {"name": "required_score", "type": "number"},
                    {"name": "passed", "type": "string"},
                    {"name": "execution_decision", "type": "string"},
                    {"name": "failure_mode", "type": "string"},
                    {"name": "function_executed", "type": "string"},
                    {"name": "assessment_duration_ms", "type": "integer"},
                    {"name": "rows_per_second", "type": "number"},
                    {"name": "cache_used", "type": "string"}
                ]
            },
            {
                "name": "adri_dimension_scores",
                "target_fields": [
                    {"name": "assessment_id", "type": "string"},
                    {"name": "dimension_name", "type": "string"},
                    {"name": "dimension_score", "type": "number"},
                    {"name": "dimension_passed", "type": "string"},
                    {"name": "issues_found", "type": "integer"},
                    {"name": "details", "type": "string"},
                    {"name": "G360_VERSION_KEY", "type": "string"}
                ]
            },
            {
                "name": "adri_failed_validations",
                "target_fields": [
                    {"name": "assessment_id", "type": "string"},
                    {"name": "validation_id", "type": "string"},
                    {"name": "dimension", "type": "string"},
                    {"name": "field_name", "type": "string"},
                    {"name": "issue_type", "type": "string"},
                    {"name": "affected_rows", "type": "integer"},
                    {"name": "affected_percentage", "type": "number"},
                    {"name": "sample_failures", "type": "string"},
                    {"name": "remediation", "type": "string"},
                    {"name": "G360_VERSION_KEY", "type": "string"}
                ]
            }
        ]
    }
    return verodat_schema

def create_test_record():
    """Create a test audit record with all required fields."""
    record = AuditRecord(
        assessment_id="adri_20250111_120000_abc123",
        timestamp=datetime.now(),
        adri_version="2.0.0"
    )
    
    # Update standard information
    record.standard_applied = {
        "standard_id": "test_standard",
        "standard_version": "1.0.0",
        "standard_checksum": "sha256_hash_here",
        "standard_path": "/path/to/standard"
    }
    
    # Update execution context
    record.execution_context.update({
        "function_name": "test_function",
        "module_path": "test.module.path",
        "environment": "PRODUCTION",
        "hostname": "test-server",
        "process_id": 12345
    })
    
    # Update data fingerprint
    record.data_fingerprint = {
        "row_count": 1000,
        "column_count": 10,
        "columns": ["col1", "col2", "col3"],
        "data_checksum": "data_checksum_here"
    }
    
    # Update assessment results
    record.assessment_results = {
        "overall_score": 85.5,
        "required_score": 70.0,
        "passed": True,
        "execution_decision": "ALLOWED",
        "function_executed": True,
        "dimension_scores": {
            "validity": 18.0,
            "completeness": 17.5,
            "consistency": 16.0,
            "timeliness": 19.0,
            "uniqueness": 15.0
        },
        "failed_checks": [
            {
                "dimension": "consistency",
                "field_name": "test_field",
                "issue_type": "invalid_format",
                "affected_rows": 10,
                "affected_percentage": 1.0,
                "sample_failures": ["row1", "row2"],
                "remediation": "Fix the format"
            }
        ]
    }
    
    # Update performance metrics
    record.performance_metrics = {
        "assessment_duration_ms": 500,
        "rows_per_second": 2000.0,
        "cache_used": False
    }
    
    # Update action taken
    record.action_taken = {
        "decision": "ALLOW",
        "failure_mode": "warn",
        "function_executed": True,
        "remediation_suggested": []
    }
    
    # For compatibility with verodat_logger
    record.environment = "PRODUCTION"
    record.hostname = "test-server"
    record.process_id = 12345
    record.standard_metadata = record.standard_applied  # Alias for verodat_logger
    record.cache_info = {"cache_used": False}
    
    return record

def verify_payload_format(payload, schema):
    """Verify that the payload matches the expected Verodat schema."""
    print("=" * 80)
    print("VERIFYING PAYLOAD FORMAT")
    print("=" * 80)
    
    # Extract header and rows from payload
    header = payload[0]['header']
    rows = payload[1]['rows']
    
    # Get expected fields from schema
    expected_fields = [field['name'] for field in schema['target_fields']]
    
    # Check header
    print(f"\nDataset: {schema['name']}")
    print(f"Expected fields: {len(expected_fields)}")
    print(f"Header fields: {len(header)}")
    
    header_names = [h['name'] for h in header]
    
    # Check for missing fields
    missing_fields = set(expected_fields) - set(header_names)
    if missing_fields:
        print(f"❌ Missing fields: {missing_fields}")
    else:
        print("✅ All expected fields present in header")
    
    # Check for extra fields
    extra_fields = set(header_names) - set(expected_fields)
    if extra_fields:
        print(f"⚠️  Extra fields: {extra_fields}")
    
    # Check field order
    if header_names == expected_fields:
        print("✅ Field order matches expected")
    else:
        print("⚠️  Field order differs:")
        print(f"  Expected: {expected_fields[:5]}...")
        print(f"  Actual:   {header_names[:5]}...")
    
    # Check data types
    print("\nField Type Validation:")
    for i, expected_field in enumerate(schema['target_fields']):
        if i < len(header):
            actual_field = header[i]
            expected_type = expected_field['type']
            actual_type = actual_field.get('type', 'unknown')
            
            # Map Verodat types
            type_mapping = {
                'string': 'string',
                'integer': 'numeric',
                'number': 'numeric',
                'date': 'date'
            }
            expected_verodat_type = type_mapping.get(expected_type, expected_type)
            
            if actual_type == expected_verodat_type:
                print(f"  ✅ {expected_field['name']}: {expected_type} -> {actual_type}")
            else:
                print(f"  ❌ {expected_field['name']}: expected {expected_verodat_type}, got {actual_type}")
    
    # Check sample row data
    if rows:
        print(f"\nSample Row Data ({len(rows)} rows):")
        for i, field in enumerate(expected_fields[:5]):  # Show first 5 fields
            if i < len(rows[0]):
                value = rows[0][i]
                print(f"  {field}: {value}")
    
    return len(missing_fields) == 0

def main():
    """Main test function."""
    print("Testing Verodat Data Format Compliance")
    print("=" * 80)
    
    # Load schema
    schema = load_verodat_config()
    
    # Create Verodat logger with test config
    config = {
        'enabled': True,
        'api_key': 'test_key',
        'base_url': 'https://verodat.io/api/v3',
        'workspace_id': 'test_workspace',
        'endpoints': {
            'assessment_logs': {
                'schedule_request_id': 'test_id',
                'standard': 'adri_assessment_logs_standard'
            },
            'dimension_scores': {
                'schedule_request_id': 'test_id',
                'standard': 'adri_dimension_scores_standard'
            },
            'failed_validations': {
                'schedule_request_id': 'test_id',
                'standard': 'adri_failed_validations_standard'
            }
        }
    }
    
    logger = VerodatLogger(config)
    
    # Create test record
    record = create_test_record()
    
    # Test each dataset type
    results = {}
    
    # Test assessment_logs
    print("\n1. Testing ASSESSMENT_LOGS format:")
    payload = logger._prepare_payload([record], 'assessment_logs')
    results['assessment_logs'] = verify_payload_format(
        payload, 
        next(ds for ds in schema['data_stores'] if ds['name'] == 'adri_assessment_logs')
    )
    
    # Test dimension_scores
    print("\n2. Testing DIMENSION_SCORES format:")
    payload = logger._prepare_payload([record], 'dimension_scores')
    results['dimension_scores'] = verify_payload_format(
        payload,
        next(ds for ds in schema['data_stores'] if ds['name'] == 'adri_dimension_scores')
    )
    
    # Test failed_validations
    print("\n3. Testing FAILED_VALIDATIONS format:")
    payload = logger._prepare_payload([record], 'failed_validations')
    results['failed_validations'] = verify_payload_format(
        payload,
        next(ds for ds in schema['data_stores'] if ds['name'] == 'adri_failed_validations')
    )
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    all_passed = all(results.values())
    
    for dataset, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{dataset}: {status}")
    
    if all_passed:
        print("\n🎉 All datasets match the Verodat schema!")
    else:
        print("\n⚠️  Some datasets do not match the Verodat schema.")
        print("Please review the field mappings in verodat_logger.py")
    
    return all_passed

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
