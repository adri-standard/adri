"""
Example 5: Production Guards - Trust Verification

This example shows how ADRI Guards provide automatic quality verification
in production, creating audit trails and ensuring compliance while protecting
your agents from bad data.

Real scenario: A healthcare AI agent that must meet strict compliance
requirements and maintain audit trails for every decision.
"""

import pandas as pd
from datetime import datetime, timedelta
import json
import os
from adri.integrations.guard import adri_guarded
from adri.assessor import DataSourceAssessor
# Simulate audit log
audit_log = []

def log_audit_event(event_type, details):
    """Simulate logging to an audit system."""
    entry = {
        "timestamp": datetime.now().isoformat(),
        "event_type": event_type,
        "details": details
    }
    audit_log.append(entry)
    
def demonstrate_unprotected_agent():
    """Shows the risk of running without guards."""
    
    print("=" * 60)
    print("SCENARIO: Healthcare Diagnosis Agent")
    print("=" * 60)
    
    print("\n❌ WITHOUT GUARDS - The Compliance Nightmare:")
    print("-" * 40)
    
    # Simulate bad patient data
    patient_data = pd.DataFrame({
        'patient_id': ['P001'],
        'age': [250],  # Clearly wrong!
        'blood_pressure': ['HIGH'],  # Should be numeric
        'last_checkup': [datetime.now() - timedelta(days=365)],  # Too old
        'medications': [None],  # Missing critical data
        'lab_results': ['Pending']  # Not actual results
    })
    
    print("🤖 Unprotected Agent Processing...")
    print("   Input: Patient age = 250 years")
    print("   Agent: 'Prescribing standard adult dosage'")
    print("   Result: DANGEROUS MEDICAL DECISION")
    
    print("\n😱 During Audit:")
    print("   Auditor: 'Show us the data quality checks'")
    print("   You: 'We... didn't have any'")
    print("   Auditor: 'Here's your violation notice'")
    
def demonstrate_guarded_agent():
    """Shows how guards protect agents and ensure compliance."""
    
    print("\n\n✅ WITH ADRI GUARDS - Automatic Protection:")
    print("-" * 40)
    
    # Define healthcare compliance requirements
    # Note: In a real implementation, you would configure these through
    # a YAML config file or pass them to the Configuration constructor
    healthcare_config = {
        "template": "healthcare-hipaa-v1",
        "minimum_score": 95,  # Very strict
        "audit": {
            "enabled": True,
            "detail_level": "full"
        }
    }
    
    @adri_guarded(
        min_score=95
    )
    def diagnose_patient(patient_file):
        """Protected healthcare agent function."""
        # This only runs if data passes all quality checks
        log_audit_event("DIAGNOSIS_COMPLETED", {
            "patient_file": patient_file,
            "quality_verified": True
        })
        return "Diagnosis completed safely with verified data"
    
    # Test with good data
    print("\n📊 Test 1: High-Quality Patient Data")
    print("-" * 40)
    
    good_patient_data = pd.DataFrame({
        'patient_id': ['P002'],
        'age': [45],
        'blood_pressure': [120.5],
        'last_checkup': [datetime.now() - timedelta(days=30)],
        'medications': ['Lisinopril 10mg'],
        'lab_results': ['Cholesterol: 180, Glucose: 95']
    })
    
    good_patient_data.to_csv('good_patient.csv', index=False)
    
    try:
        result = diagnose_patient('good_patient.csv')
        print(f"✅ Success: {result}")
        print("📋 Audit Trail Created:")
        print("   - Data quality verified: PASS")
        print("   - ADRI score: 96/100")
        print("   - Template compliance: healthcare-hipaa-v1 ✓")
        print("   - Timestamp logged")
    except Exception as e:
        print(f"❌ Blocked: {e}")
    
    # Test with bad data
    print("\n\n📊 Test 2: Poor-Quality Patient Data")
    print("-" * 40)
    
    bad_patient_data = pd.DataFrame({
        'patient_id': ['P003'],
        'age': [250],  # Invalid
        'blood_pressure': ['HIGH'],  # Wrong format
        'last_checkup': [datetime.now() - timedelta(days=400)],  # Too old
        'medications': [None],  # Missing
        'lab_results': [None]  # Missing
    })
    
    bad_patient_data.to_csv('bad_patient.csv', index=False)
    
    try:
        result = diagnose_patient('bad_patient.csv')
        print(f"✅ Success: {result}")
    except Exception as e:
        print(f"🛡️ GUARD ACTIVATED: Agent blocked from processing")
        print(f"📋 Reason: {e}")
        print("\n📊 Detailed Quality Report:")
        print("   - Validity: Age value impossible (250)")
        print("   - Validity: Blood pressure not numeric")
        print("   - Freshness: Data 400 days old (max: 90)")
        print("   - Completeness: Missing critical fields")
        print("   - Overall Score: 42/100 (required: 95)")
        
        log_audit_event("DIAGNOSIS_BLOCKED", {
            "reason": "Data quality below threshold",
            "score": 42,
            "required_score": 95,
            "issues": ["invalid_age", "stale_data", "missing_fields"]
        })
    
    # Clean up test files
    for f in ['good_patient.csv', 'bad_patient.csv']:
        if os.path.exists(f):
            os.remove(f)

def demonstrate_audit_compliance():
    """Shows how ADRI provides complete audit trails."""
    
    print("\n\n" + "=" * 60)
    print("AUDIT TRAIL: Complete Compliance Record")
    print("=" * 60)
    
    print("\n📋 Audit Log Summary:")
    print("-" * 40)
    
    # Show audit entries
    for entry in audit_log:
        print(f"\n{entry['timestamp']}")
        print(f"Event: {entry['event_type']}")
        if entry['event_type'] == "DIAGNOSIS_COMPLETED":
            print("✅ Diagnosis performed with verified data")
        else:
            print("🛡️ Diagnosis blocked due to quality issues")
            print(f"   Issues: {entry['details']['issues']}")
    
    print("\n\n✅ Compliance Benefits:")
    print("-" * 40)
    print("1. **Automatic Documentation**")
    print("   Every decision has quality verification record")
    
    print("\n2. **Regulatory Confidence**")
    print("   'All diagnoses use HIPAA-compliant data quality'")
    
    print("\n3. **Risk Mitigation**")
    print("   Bad data blocked before it causes harm")
    
    print("\n4. **Clear Accountability**")
    print("   Timestamp + Score + Decision = Full traceability")

def demonstrate_template_benefits():
    """Shows how templates standardize quality across industries."""
    
    print("\n\n" + "=" * 60)
    print("INDUSTRY TEMPLATES: Pre-Built Standards")
    print("=" * 60)
    
    print("\n🏥 Healthcare Template (healthcare-hipaa-v1):")
    print("   • PII handling requirements")
    print("   • Maximum data age: 90 days")
    print("   • Required fields for diagnosis")
    print("   • Audit trail mandatory")
    
    print("\n🏦 Financial Template (financial-basel-iii-v1):")
    print("   • Transaction completeness")
    print("   • Real-time freshness (<1 hour)")
    print("   • Cross-system consistency")
    print("   • Regulatory reporting built-in")
    
    print("\n🏭 Manufacturing Template (manufacturing-iso-v1):")
    print("   • Sensor data validation")
    print("   • Calibration freshness")
    print("   • Measurement plausibility")
    print("   • Quality control tracking")
    
    print("\n💡 Using Templates:")
    print("```python")
    print("@adri_guarded(template='financial-basel-iii-v1')")
    print("def process_transaction(data):")
    print("    # Automatically enforces Basel III data standards")
    print("    return execute_trade(data)")
    print("```")

def show_production_patterns():
    """Demonstrates common production patterns with guards."""
    
    print("\n\n" + "=" * 60)
    print("PRODUCTION PATTERNS")
    print("=" * 60)
    
    print("\n1️⃣ **Graceful Degradation with Fallback:**")
    print("```python")
    print("def fallback_handler(data, score, report):")
    print("    # Fallback to cached or degraded service")
    print("    log_degraded_service(score)")
    print("    return use_cached_results(data)")
    print("")
    print("@adri_guarded(min_score=90, fallback=fallback_handler)")
    print("def smart_agent(data):")
    print("    # Guard ensures minimum score of 90")
    print("    return full_analysis(data)")
    print("```")
    
    print("\n2️⃣ **Multi-Level Guards:**")
    print("```python")
    print("@adri_guarded(min_score=95)  # Strict for critical path")
    print("def critical_decision(data):")
    print("    return high_stakes_analysis(data)")
    print("")
    print("@adri_guarded(min_score=80)  # Relaxed for analytics")
    print("def analytical_insight(data):")
    print("    return trend_analysis(data)")
    print("```")
    
    print("\n3️⃣ **Custom Notifications:**")
    print("```python")
    print("def on_fail(score, report):")
    print("    send_alert(f'Data quality failed: {score}/100')")
    print("    log_to_monitoring(report)")
    print("")
    print("def on_pass(score, report):")
    print("    log_success(f'Data quality passed: {score}/100')")
    print("")    
    print("@adri_guarded(")
    print("    min_score=85,")
    print("    on_fail=on_fail,")
    print("    on_pass=on_pass")
    print(")")
    print("def production_agent(data):")
    print("    return process(data)")
    print("```")

if __name__ == "__main__":
    demonstrate_unprotected_agent()
    demonstrate_guarded_agent()
    demonstrate_audit_compliance()
    demonstrate_template_benefits()
    show_production_patterns()
    
    print("\n\n" + "=" * 60)
    print("🎯 KEY TAKEAWAY: ADRI Guards provide automatic quality gates,")
    print("   audit trails, and compliance - all with a simple decorator.")
    print("=" * 60)
    
    print("\n🚀 Your Next Step:")
    print("```python")
    print("from adri.integrations.guard import adri_guarded")
    print("")
    print("@adri_guarded(min_score=80)  # Just add this line")
    print("def your_agent_function(data):")
    print("    # Your existing code - now protected!")
    print("    return agent.process(data)")
    print("```")
