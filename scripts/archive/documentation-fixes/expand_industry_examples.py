#!/usr/bin/env python3
"""
Expand industry-specific examples for ADRI.
This script creates comprehensive examples for different industries.
"""

import os
from pathlib import Path

def create_industry_examples():
    """Create comprehensive industry-specific examples."""
    print("🏭 Creating industry-specific examples...")
    
    # Get the project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    docs_dir = project_root / "docs"
    
    # Create industry examples
    create_financial_examples(docs_dir)
    create_healthcare_examples(docs_dir)
    create_retail_examples(docs_dir)
    create_manufacturing_examples(docs_dir)
    create_logistics_examples(docs_dir)
    
    print("✅ Industry-specific examples created!")

def create_financial_examples(docs_dir):
    """Create financial services examples."""
    print("  💰 Creating financial services examples...")
    
    # KYC Data Assessment
    kyc_content = """# KYC Data Assessment

Know Your Customer (KYC) data quality is critical for regulatory compliance and risk management.

## Assessment Configuration

```python
<!-- audience: data-providers -->
from adri import Assessor
from adri.templates import TemplateLoader

# Load financial services template
loader = TemplateLoader()
template = loader.load('financial_kyc')
assessor = template.create_assessor()

# Configure for KYC requirements
assessor.configure({
    'completeness': {
        'required_fields': [
            'customer_id', 'full_name', 'date_of_birth',
            'address', 'identification_number', 'source_of_funds'
        ],
        'threshold': 0.98  # Very high threshold for compliance
    },
    'validity': {
        'patterns': {
            'identification_number': r'^[A-Z0-9]{8,12}$',
            'phone_number': r'^\+?[1-9]\d{1,14}$'
        }
    },
    'freshness': {
        'max_age_days': 365,  # Annual review requirement
        'critical_fields': ['address', 'source_of_funds']
    }
})
```

## Risk Assessment Integration

```python
<!-- audience: ai-builders -->
from adri.integrations import Guard

class KYCGuard(Guard):
    def __init__(self):
        super().__init__(
            dimensions=['completeness', 'validity', 'freshness'],
            thresholds={
                'completeness': 0.98,
                'validity': 0.95,
                'freshness': 0.90
            }
        )
    
    def assess_customer_risk(self, customer_data):
        # Run ADRI assessment
        results = self.assess(customer_data)
        
        # Calculate risk score
        risk_score = self._calculate_risk_score(results)
        
        # Determine action
        if risk_score > 0.8:
            return "APPROVE"
        elif risk_score > 0.6:
            return "MANUAL_REVIEW"
        else:
            return "REJECT"
    
    def _calculate_risk_score(self, results):
        # Weight dimensions by regulatory importance
        weights = {
            'completeness': 0.4,
            'validity': 0.3,
            'freshness': 0.3
        }
        
        weighted_score = sum(
            results[dim].score * weights[dim]
            for dim in weights
        )
        
        return weighted_score
```

## Regulatory Reporting

```python
<!-- audience: data-providers -->
# Generate compliance report
compliance_report = assessor.generate_compliance_report(
    data=customer_data,
    regulations=['AML', 'KYC', 'GDPR'],
    format='regulatory'
)

# Export for audit
compliance_report.export('kyc_compliance_report.pdf')
```

## Key Metrics

- **Completeness**: >98% (Regulatory requirement)
- **Validity**: >95% (Data format compliance)
- **Freshness**: <365 days (Annual review cycle)
- **Consistency**: >90% (Cross-system validation)
"""

    # Transaction Data Assessment
    transaction_content = """# Transaction Data Assessment

Real-time transaction data quality for fraud detection and financial analysis.

## Real-Time Assessment

```python
<!-- audience: ai-builders -->
from adri.integrations import StreamingGuard
import asyncio

class TransactionGuard(StreamingGuard):
    def __init__(self):
        super().__init__(
            dimensions=['validity', 'plausibility', 'consistency'],
            real_time=True
        )
    
    async def assess_transaction(self, transaction):
        # Real-time assessment
        results = await self.assess_async(transaction)
        
        # Fraud detection logic
        fraud_indicators = self._detect_fraud_indicators(
            transaction, results
        )
        
        if fraud_indicators['high_risk']:
            await self._flag_transaction(transaction)
        
        return results
    
    def _detect_fraud_indicators(self, transaction, results):
        indicators = {
            'high_risk': False,
            'reasons': []
        }
        
        # Check plausibility scores
        if results.plausibility.score < 0.3:
            indicators['high_risk'] = True
            indicators['reasons'].append('Unusual transaction pattern')
        
        # Check amount validity
        if transaction['amount'] > 10000 and results.validity.score < 0.8:
            indicators['high_risk'] = True
            indicators['reasons'].append('Large amount with data quality issues')
        
        return indicators
```

## Batch Processing

```python
<!-- audience: data-providers -->
from adri.connectors import DatabaseConnector
from adri.assessment_modes import BatchMode

# Connect to transaction database
connector = DatabaseConnector(
    connection_string="postgresql://user:pass@host/transactions"
)

# Configure batch assessment
batch_assessor = Assessor(mode=BatchMode(
    batch_size=10000,
    parallel=True,
    n_jobs=4
))

# Process daily transactions
daily_transactions = connector.query("""
    SELECT * FROM transactions 
    WHERE date = CURRENT_DATE
""")

results = batch_assessor.assess(daily_transactions)

# Generate daily quality report
quality_report = results.generate_report(
    template='financial_daily',
    include_trends=True
)
```

## Performance Monitoring

```python
<!-- audience: ai-builders -->
from adri.monitoring import QualityMonitor

monitor = QualityMonitor(
    metrics=['completeness', 'validity', 'plausibility'],
    alert_thresholds={
        'completeness': 0.95,
        'validity': 0.90,
        'plausibility': 0.85
    }
)

# Set up real-time alerts
monitor.setup_alerts(
    email=['risk-team@bank.com'],
    slack_webhook='https://hooks.slack.com/...',
    escalation_rules={
        'critical': 'immediate',
        'warning': '15_minutes'
    }
)
```
"""

    # Risk Assessment
    risk_content = """# Risk Assessment Data Quality

Comprehensive risk assessment data quality for financial institutions.

## Credit Risk Assessment

```python
<!-- audience: ai-builders -->
from adri import Assessor
from adri.rules import CreditRiskRules

class CreditRiskAssessor:
    def __init__(self):
        self.assessor = Assessor()
        self.assessor.add_rules(CreditRiskRules())
    
    def assess_loan_application(self, application_data):
        # Core ADRI assessment
        results = self.assessor.assess(application_data)
        
        # Credit-specific validations
        credit_score = self._calculate_credit_score(
            application_data, results
        )
        
        # Risk categorization
        risk_category = self._categorize_risk(credit_score)
        
        return {
            'adri_results': results,
            'credit_score': credit_score,
            'risk_category': risk_category,
            'recommendation': self._get_recommendation(risk_category)
        }
    
    def _calculate_credit_score(self, data, results):
        # Combine ADRI scores with credit factors
        base_score = results.overall_score
        
        # Adjust for credit-specific factors
        if data.get('income_verified') and results.validity.score > 0.9:
            base_score += 0.1
        
        if data.get('employment_stable') and results.consistency.score > 0.8:
            base_score += 0.05
        
        return min(base_score, 1.0)
    
    def _categorize_risk(self, score):
        if score >= 0.8:
            return "LOW_RISK"
        elif score >= 0.6:
            return "MEDIUM_RISK"
        else:
            return "HIGH_RISK"
```

## Market Risk Data

```python
<!-- audience: data-providers -->
from adri.connectors import MarketDataConnector
from adri.dimensions import FreshnessRules

# Configure market data assessment
market_assessor = Assessor()
market_assessor.configure({
    'freshness': {
        'max_age_seconds': 30,  # Real-time requirement
        'critical_fields': ['price', 'volume', 'timestamp']
    },
    'plausibility': {
        'price_change_threshold': 0.1,  # 10% max change
        'volume_spike_threshold': 3.0   # 3x normal volume
    }
})

# Assess market data feed
market_data = MarketDataConnector('bloomberg_feed').get_latest()
results = market_assessor.assess(market_data)

# Alert on data quality issues
if results.freshness.score < 0.9:
    alert_trading_desk("Stale market data detected")

if results.plausibility.score < 0.7:
    alert_risk_management("Unusual market data patterns")
```

## Regulatory Capital Calculation

```python
<!-- audience: standard-contributors -->
from adri.rules.base import Rule

class RegulatoryCapitalRule(Rule):
    """Custom rule for regulatory capital data quality."""
    
    def __init__(self):
        super().__init__(
            name="regulatory_capital_quality",
            dimension="validity"
        )
    
    def evaluate(self, data):
        issues = []
        score = 1.0
        
        # Check required Basel III fields
        required_fields = [
            'tier1_capital', 'tier2_capital', 'risk_weighted_assets',
            'leverage_ratio', 'liquidity_coverage_ratio'
        ]
        
        for field in required_fields:
            if field not in data or data[field] is None:
                issues.append(f"Missing required field: {field}")
                score -= 0.2
        
        # Validate capital ratios
        if 'tier1_capital' in data and 'risk_weighted_assets' in data:
            tier1_ratio = data['tier1_capital'] / data['risk_weighted_assets']
            if tier1_ratio < 0.06:  # Minimum 6% requirement
                issues.append("Tier 1 capital ratio below regulatory minimum")
                score -= 0.3
        
        return self.create_result(
            passed=len(issues) == 0,
            score=max(score, 0.0),
            details={'issues': issues}
        )
```
"""

    # Write financial examples
    financial_dir = docs_dir / "examples" / "by-industry" / "financial"
    financial_dir.mkdir(parents=True, exist_ok=True)
    
    (financial_dir / "kyc-data.md").write_text(kyc_content, encoding='utf-8')
    (financial_dir / "transactions.md").write_text(transaction_content, encoding='utf-8')
    (financial_dir / "risk-assessment.md").write_text(risk_content, encoding='utf-8')

def create_healthcare_examples(docs_dir):
    """Create healthcare examples."""
    print("  🏥 Creating healthcare examples...")
    
    # Patient Data Assessment
    patient_content = """# Patient Data Quality Assessment

Healthcare data quality for patient safety and regulatory compliance.

## HIPAA Compliance Assessment

```python
<!-- audience: data-providers -->
from adri import Assessor
from adri.templates import TemplateLoader

# Load healthcare template
loader = TemplateLoader()
template = loader.load('healthcare_hipaa')
assessor = template.create_assessor()

# Configure for HIPAA requirements
assessor.configure({
    'completeness': {
        'required_fields': [
            'patient_id', 'medical_record_number', 'date_of_birth',
            'emergency_contact', 'insurance_information'
        ],
        'threshold': 0.95
    },
    'validity': {
        'patterns': {
            'medical_record_number': r'^MRN\d{8}$',
            'date_of_birth': r'^\d{4}-\d{2}-\d{2}$'
        }
    },
    'privacy': {
        'pii_detection': True,
        'anonymization_check': True
    }
})
```

## Clinical Decision Support

```python
<!-- audience: ai-builders -->
from adri.integrations import ClinicalGuard

class PatientSafetyGuard(ClinicalGuard):
    def __init__(self):
        super().__init__(
            dimensions=['completeness', 'validity', 'consistency'],
            clinical_context=True
        )
    
    def assess_patient_record(self, patient_data):
        # Run ADRI assessment
        results = self.assess(patient_data)
        
        # Clinical safety checks
        safety_score = self._calculate_safety_score(results)
        
        # Generate alerts if needed
        if safety_score < 0.8:
            self._generate_safety_alert(patient_data, results)
        
        return {
            'quality_results': results,
            'safety_score': safety_score,
            'clinical_recommendations': self._get_recommendations(results)
        }
    
    def _calculate_safety_score(self, results):
        # Weight dimensions by clinical importance
        weights = {
            'completeness': 0.4,  # Missing data can be dangerous
            'validity': 0.3,      # Incorrect data format
            'consistency': 0.3    # Conflicting information
        }
        
        return sum(
            results[dim].score * weights[dim]
            for dim in weights
        )
    
    def _generate_safety_alert(self, patient_data, results):
        alert = {
            'patient_id': patient_data['patient_id'],
            'severity': 'HIGH' if results.overall_score < 0.6 else 'MEDIUM',
            'issues': [],
            'timestamp': datetime.now()
        }
        
        if results.completeness.score < 0.8:
            alert['issues'].append('Critical patient data missing')
        
        if results.validity.score < 0.7:
            alert['issues'].append('Invalid data format detected')
        
        # Send to clinical team
        self.send_alert(alert)
```

## Drug Interaction Checking

```python
<!-- audience: ai-builders -->
from adri.rules import DrugInteractionRules

class MedicationGuard:
    def __init__(self):
        self.assessor = Assessor()
        self.assessor.add_rules(DrugInteractionRules())
    
    def assess_medication_order(self, order_data):
        # Assess data quality
        results = self.assessor.assess(order_data)
        
        # Check for drug interactions
        interactions = self._check_interactions(order_data)
        
        # Validate dosage
        dosage_valid = self._validate_dosage(order_data)
        
        return {
            'data_quality': results,
            'interactions': interactions,
            'dosage_valid': dosage_valid,
            'safe_to_dispense': self._is_safe_to_dispense(
                results, interactions, dosage_valid
            )
        }
    
    def _check_interactions(self, order_data):
        # Implementation would check against drug interaction database
        return {'high_risk': [], 'moderate_risk': [], 'low_risk': []}
    
    def _validate_dosage(self, order_data):
        # Validate dosage against patient weight, age, etc.
        return True
    
    def _is_safe_to_dispense(self, quality, interactions, dosage):
        return (
            quality.overall_score > 0.9 and
            len(interactions['high_risk']) == 0 and
            dosage
        )
```
"""

    # Medical Records
    records_content = """# Medical Records Data Quality

Electronic Health Records (EHR) data quality assessment and improvement.

## EHR Data Assessment

```python
<!-- audience: data-providers -->
from adri.connectors import EHRConnector
from adri.assessment_modes import ClinicalMode

# Connect to EHR system
ehr_connector = EHRConnector(
    system='epic',
    credentials={'api_key': 'your_api_key'}
)

# Configure clinical assessment mode
clinical_assessor = Assessor(mode=ClinicalMode(
    include_clinical_rules=True,
    hipaa_compliance=True,
    interoperability_check=True
))

# Assess patient records
patient_records = ehr_connector.get_patient_data(
    patient_ids=['12345', '67890'],
    include_history=True
)

results = clinical_assessor.assess(patient_records)

# Generate clinical quality report
clinical_report = results.generate_report(
    template='clinical_quality',
    include_recommendations=True,
    compliance_check=['HIPAA', 'HL7_FHIR']
)
```

## Interoperability Assessment

```python
<!-- audience: standard-contributors -->
from adri.rules.base import Rule

class HL7FHIRComplianceRule(Rule):
    """Rule to check HL7 FHIR compliance."""
    
    def __init__(self):
        super().__init__(
            name="hl7_fhir_compliance",
            dimension="validity"
        )
    
    def evaluate(self, data):
        issues = []
        score = 1.0
        
        # Check FHIR resource structure
        if 'resourceType' not in data:
            issues.append("Missing FHIR resourceType")
            score -= 0.3
        
        # Validate required FHIR elements
        resource_type = data.get('resourceType')
        required_elements = self._get_required_elements(resource_type)
        
        for element in required_elements:
            if element not in data:
                issues.append(f"Missing required FHIR element: {element}")
                score -= 0.1
        
        # Check data types
        type_issues = self._validate_data_types(data, resource_type)
        issues.extend(type_issues)
        score -= len(type_issues) * 0.05
        
        return self.create_result(
            passed=len(issues) == 0,
            score=max(score, 0.0),
            details={'issues': issues, 'fhir_version': '4.0.1'}
        )
    
    def _get_required_elements(self, resource_type):
        # FHIR required elements by resource type
        requirements = {
            'Patient': ['identifier', 'name'],
            'Observation': ['status', 'code', 'subject'],
            'Medication': ['code'],
            'Encounter': ['status', 'class', 'subject']
        }
        return requirements.get(resource_type, [])
```

## Clinical Trial Data

```python
<!-- audience: data-providers -->
from adri.templates import ClinicalTrialTemplate

# Configure for clinical trial
trial_template = ClinicalTrialTemplate(
    study_phase='Phase_III',
    regulatory_requirements=['FDA_21CFR11', 'ICH_GCP'],
    data_standards=['CDISC_SDTM', 'CDISC_ADaM']
)

trial_assessor = trial_template.create_assessor()

# Assess trial data
trial_data = load_trial_data('study_001')
results = trial_assessor.assess(trial_data)

# Generate regulatory submission report
submission_report = results.generate_regulatory_report(
    format='FDA_submission',
    include_statistical_analysis=True
)
```
"""

    # Clinical Trials
    trials_content = """# Clinical Trials Data Quality

Data quality standards for clinical research and regulatory submissions.

## FDA Submission Preparation

```python
<!-- audience: data-providers -->
from adri.regulatory import FDASubmissionAssessor

class ClinicalTrialQuality:
    def __init__(self, study_id, phase):
        self.study_id = study_id
        self.phase = phase
        self.assessor = FDASubmissionAssessor(phase=phase)
    
    def prepare_submission(self, trial_data):
        # Comprehensive quality assessment
        results = self.assessor.assess(trial_data)
        
        # Check regulatory requirements
        regulatory_compliance = self._check_regulatory_compliance(
            trial_data, results
        )
        
        # Generate submission package
        submission_package = self._create_submission_package(
            results, regulatory_compliance
        )
        
        return submission_package
    
    def _check_regulatory_compliance(self, data, results):
        compliance = {
            '21_CFR_11': self._check_21cfr11(data),
            'ICH_GCP': self._check_ich_gcp(data),
            'CDISC_SDTM': self._check_cdisc_sdtm(data)
        }
        return compliance
    
    def _create_submission_package(self, results, compliance):
        return {
            'quality_summary': results.summary(),
            'compliance_report': compliance,
            'data_files': self._prepare_data_files(),
            'statistical_analysis': self._generate_statistical_report()
        }
```

## Adverse Event Monitoring

```python
<!-- audience: ai-builders -->
from adri.monitoring import AdverseEventMonitor

class SafetyMonitor:
    def __init__(self):
        self.monitor = AdverseEventMonitor()
        self.assessor = Assessor()
    
    def monitor_adverse_events(self, event_data):
        # Assess data quality
        quality_results = self.assessor.assess(event_data)
        
        # Safety signal detection
        safety_signals = self._detect_safety_signals(event_data)
        
        # Risk assessment
        risk_level = self._assess_risk_level(
            quality_results, safety_signals
        )
        
        # Generate alerts if needed
        if risk_level == 'HIGH':
            self._generate_safety_alert(event_data, safety_signals)
        
        return {
            'quality_score': quality_results.overall_score,
            'safety_signals': safety_signals,
            'risk_level': risk_level
        }
    
    def _detect_safety_signals(self, event_data):
        # Implementation would use statistical methods
        # to detect unusual patterns in adverse events
        return {
            'new_signals': [],
            'trending_events': [],
            'severity_changes': []
        }
    
    def _assess_risk_level(self, quality, signals):
        if quality.overall_score < 0.7:
            return 'HIGH'  # Poor data quality is high risk
        
        if len(signals['new_signals']) > 0:
            return 'HIGH'
        
        if len(signals['trending_events']) > 2:
            return 'MEDIUM'
        
        return 'LOW'
```

## Real-World Evidence

```python
<!-- audience: data-providers -->
from adri.connectors import RealWorldDataConnector

# Connect to real-world data sources
rwd_connector = RealWorldDataConnector([
    'claims_database',
    'electronic_health_records',
    'patient_registries'
])

# Configure for real-world evidence study
rwe_assessor = Assessor()
rwe_assessor.configure({
    'completeness': {
        'longitudinal_coverage': 0.8,  # 80% follow-up coverage
        'outcome_capture': 0.9         # 90% outcome capture
    },
    'validity': {
        'coding_standards': ['ICD10', 'CPT', 'HCPCS'],
        'data_provenance': True
    },
    'consistency': {
        'cross_source_validation': True,
        'temporal_consistency': True
    }
})

# Assess real-world data
rwd_data = rwd_connector.extract_cohort(
    inclusion_criteria={'age': '>=18', 'diagnosis': 'diabetes'},
    study_period={'start': '2020-01-01', 'end': '2023-12-31'}
)

results = rwe_assessor.assess(rwd_data)

# Generate evidence quality report
evidence_report = results.generate_report(
    template='real_world_evidence',
    include_bias_assessment=True,
    regulatory_context='FDA_RWE_guidance'
)
```
"""

    # Write healthcare examples
    healthcare_dir = docs_dir / "examples" / "by-industry" / "healthcare"
    healthcare_dir.mkdir(parents=True, exist_ok=True)
    
    (healthcare_dir / "patient-data.md").write_text(patient_content, encoding='utf-8')
    (healthcare_dir / "medical-records.md").write_text(records_content, encoding='utf-8')
    (healthcare_dir / "clinical-trials.md").write_text(trials_content, encoding='utf-8')

def create_retail_examples(docs_dir):
    """Create retail examples."""
    print("  🛒 Creating retail examples...")
    
    # Customer Analytics
    customer_content = """# Customer Analytics Data Quality

Customer data quality for personalization and marketing effectiveness.

## Customer 360 Assessment

```python
<!-- audience: data-providers -->
from adri import Assessor
from adri.connectors import MultiSourceConnector

# Connect to multiple customer data sources
connector = MultiSourceConnector([
    {'type': 'database', 'source': 'crm_system'},
    {'type': 'api', 'source': 'web_analytics'},
    {'type': 'file', 'source': 'loyalty_program'},
    {'type': 'streaming', 'source': 'mobile_app'}
])

# Configure customer data assessment
customer_assessor = Assessor()
customer_assessor.configure({
    'completeness': {
        'required_fields': [
            'customer_id', 'email', 'purchase_history',
            'preferences', 'demographics'
        ],
        'cross_source_validation': True
    },
    'consistency': {
        'identity_resolution': True,
        'duplicate_detection': True
    },
    'freshness': {
        'behavioral_data': {'max_age_days': 30},
        'demographic_data': {'max_age_days': 365}
    }
})

# Load and assess customer data
customer_data = connector.load_customer_360()
results = customer_assessor.assess(customer_data)

# Generate customer data quality report
quality_report = results.generate_report(
    template='customer_360',
    include_segmentation_impact=True
)
```

## Personalization Engine

```python
<!-- audience: ai-builders -->
from adri.integrations import PersonalizationGuard

class RecommendationGuard(PersonalizationGuard):
    def __init__(self):
        super().__init__(
            dimensions=['completeness', 'freshness', 'consistency'],
            personalization_context=True
        )
    
    def assess_for_recommendations(self, customer_data):
        # Assess data quality
        results = self.assess(customer_data)
        
        # Calculate personalization readiness
        personalization_score = self._calculate_personalization_score(
            customer_data, results
        )
        
        # Determine recommendation strategy
        strategy = self._select_recommendation_strategy(
            personalization_score, results
        )
        
        return {
            'quality_results': results,
            'personalization_score': personalization_score,
            'recommendation_strategy': strategy
        }
    
    def _calculate_personalization_score(self, data, results):
        # Weight factors for personalization effectiveness
        factors = {
            'purchase_history_completeness': 0.3,
            'behavioral_data_freshness': 0.25,
            'preference_data_quality': 0.25,
            'demographic_completeness': 0.2
        }
        
        score = 0.0
        
        # Purchase history
        if 'purchase_history' in data and len(data['purchase_history']) > 5:
            score += factors['purchase_history_completeness']
        
        # Behavioral data freshness
        if results.freshness.score > 0.8:
            score += factors['behavioral_data_freshness']
        
        # Preference data
        if 'preferences' in data and results.validity.score > 0.9:
            score += factors['preference_data_quality']
        
        # Demographics
        if results.completeness.score > 0.8:
            score += factors['demographic_completeness']
        
        return score
    
    def _select_recommendation_strategy(self, score, results):
        if score > 0.8:
            return "PERSONALIZED"
        elif score > 0.5:
            return "SEGMENT_BASED"
        else:
            return "POPULAR_ITEMS"
```

## Marketing Campaign Assessment

```python
<!-- audience: ai-builders -->
from adri.marketing import CampaignDataAssessor

class MarketingQualityGuard:
    def __init__(self):
        self.assessor = CampaignDataAssessor()
    
    def assess_campaign_readiness(self, campaign_data):
        # Assess target audience data quality
        audience_quality = self.assessor.assess_audience_data(
            campaign_data['target_audience']
        )
        
        # Assess campaign content data
        content_quality = self.assessor.assess_content_data(
            campaign_data['content']
        )
        
        # Calculate campaign readiness score
        readiness_score = self._calculate_readiness_score(
            audience_quality, content_quality
        )
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            audience_quality, content_quality, readiness_score
        )
        
        return {
            'audience_quality': audience_quality,
            'content_quality': content_quality,
            'readiness_score': readiness_score,
            'recommendations': recommendations,
            'launch_approved': readiness_score > 0.8
        }
    
    def _calculate_readiness_score(self, audience_quality, content_quality):
        return (audience_quality.overall_score * 0.6 + 
                content_quality.overall_score * 0.4)
    
    def _generate_recommendations(self, audience_quality, content_quality, score):
        recommendations = []
        
        if audience_quality.completeness.score < 0.8:
            recommendations.append(
                "Improve audience data completeness before launch"
            )
        
        if content_quality.validity.score < 0.9:
            recommendations.append(
                "Review content data formats and validation"
            )
        
        if score < 0.8:
            recommendations.append(
                "Campaign data quality below launch threshold"
            )
        
        return recommendations
```
"""

    # Product Catalog
    catalog_content = """# Product Catalog Data Quality

Product information management and catalog data quality assessment.

## Product Information Management

```python
<!-- audience: data-providers -->
from
