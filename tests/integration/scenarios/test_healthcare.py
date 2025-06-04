"""Test healthcare scenario: medical data completeness."""

import pytest
import tempfile
import os
import pandas as pd
import numpy as np

from adri.assessor import DataSourceAssessor


class TestHealthcareScenario:
    """Test real-world healthcare data scenarios."""
    
    def test_missing_critical_test_results(self):
        """Test handling of missing critical medical test results."""
        # Create patient data with missing test results
        data = pd.DataFrame({
            'patient_id': ['P001', 'P002', 'P003', 'P004', 'P005'],
            'name': ['Alice Smith', 'Bob Jones', 'Charlie Brown', 'Diana Ross', 'Eve Wilson'],
            'blood_glucose': [95, np.nan, 110, np.nan, 102],  # Missing for P002, P004
            'blood_pressure_systolic': [120, 130, np.nan, 140, 125],  # Missing for P003
            'blood_pressure_diastolic': [80, 85, np.nan, 90, 82],  # Missing for P003
            'cholesterol_total': [180, 210, 195, np.nan, np.nan],  # Missing for P004, P005
            'diagnosis_code': ['E11.9', 'I10', 'E78.5', 'I10', 'E11.9'],
            'test_date': pd.date_range('2025-01-01', periods=5, freq='D')
        })
        
        # Add completeness metadata
        completeness_metadata = {
            "required_fields": [
                "patient_id", "name", "blood_glucose", 
                "blood_pressure_systolic", "blood_pressure_diastolic"
            ],
            "critical_fields": [
                "blood_glucose",  # Critical for diabetes patients
                "blood_pressure_systolic",  # Critical for hypertension
                "blood_pressure_diastolic"
            ],
            "missing_value_handling": {
                "blood_glucose": "request_test",
                "cholesterol_total": "use_previous_if_available"
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            data.to_csv(f.name, index=False)
            test_file = f.name
            
        # Create completeness metadata file
        import json
        completeness_file = test_file.replace('.csv', '.completeness.json')
        with open(completeness_file, 'w') as f:
            json.dump(completeness_metadata, f)
        
        try:
            # Assess the data
            assessor = DataSourceAssessor()
            report = assessor.assess_file(test_file)
            
            # Completeness should be significantly impacted
            completeness_score = report.dimension_results['completeness']['score']
            assert completeness_score <= 15, "Missing critical fields should impact completeness score"
            
            # Just verify the dimension was assessed
            assert 'completeness' in report.dimension_results
            assert report.dimension_results['completeness']['score'] >= 0
            
        finally:
            os.unlink(test_file)
            if os.path.exists(completeness_file):
                os.unlink(completeness_file)
    
    def test_medical_data_consistency(self):
        """Test medical data consistency rules."""
        # Create data with medical inconsistencies
        data = pd.DataFrame({
            'patient_id': ['P001', 'P002', 'P003'],
            'age': [45, 30, 65],
            'diagnosis_code': ['O80', 'E66.9', 'H25.9'],  # Pregnancy, Obesity, Cataracts
            'gender': ['M', 'F', 'F'],  # Male with pregnancy diagnosis!
            'bmi': [32.5, 18.5, 28.0],  # P002 has obesity diagnosis but normal BMI
            'prescribed_medication': ['Insulin', 'Metformin', 'Timolol'],
            'allergies': ['Penicillin', 'None', 'Sulfa drugs'],
            'medication_contraindications': ['None', 'None', 'Beta-blockers']  # P003 prescribed contraindicated med
        })
        
        # Add consistency rules
        consistency_metadata = {
            "rules": [
                {
                    "name": "Pregnancy diagnosis gender check",
                    "type": "cross_field",
                    "condition": "diagnosis_code.startswith('O')",
                    "requirement": "gender == 'F'"
                },
                {
                    "name": "BMI consistency with obesity diagnosis",
                    "type": "cross_field",
                    "condition": "diagnosis_code == 'E66.9'",
                    "requirement": "bmi >= 30"
                },
                {
                    "name": "Medication contraindication check",
                    "type": "cross_field",
                    "fields": ["prescribed_medication", "medication_contraindications"]
                }
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            data.to_csv(f.name, index=False)
            test_file = f.name
            
        # Create consistency metadata file
        import json
        consistency_file = test_file.replace('.csv', '.consistency.json')
        with open(consistency_file, 'w') as f:
            json.dump(consistency_metadata, f)
        
        try:
            # Assess consistency
            assessor = DataSourceAssessor()
            report = assessor.assess_file(test_file)
            
            # Consistency should be impacted by violations
            consistency_score = report.dimension_results['consistency']['score']
            assert consistency_score <= 15, "Medical inconsistencies should impact consistency score"
            
            # Should not be in the highest readiness tiers
            assert not any(level in report.readiness_level for level in ["Advanced", "Proficient"])
            
        finally:
            os.unlink(test_file)
            if os.path.exists(consistency_file):
                os.unlink(consistency_file)
    
    def test_medical_data_plausibility(self):
        """Test medical data plausibility checks."""
        # Create data with implausible medical values
        data = pd.DataFrame({
            'patient_id': range(1, 11),
            'heart_rate': [72, 68, 250, 75, 30, 80, 90, 65, 70, 85],  # 250 and 30 are implausible
            'body_temperature_f': [98.6, 99.1, 112.0, 98.2, 97.8, 86.0, 98.5, 99.0, 98.7, 98.4],  # 112 and 86 implausible
            'blood_oxygen_saturation': [98, 97, 99, 45, 96, 98, 97, 150, 98, 95],  # 45 and 150 are impossible
            'white_blood_cell_count': [7500, 8200, 150000, 6800, 7200, 9000, 0, 8500, 7800, 8100]  # Extreme values
        })
        
        # Add plausibility rules
        plausibility_metadata = {
            "rules": [
                {
                    "name": "Heart rate plausibility",
                    "field": "heart_rate",
                    "min": 40,
                    "max": 200,
                    "typical_range": [60, 100]
                },
                {
                    "name": "Body temperature plausibility",
                    "field": "body_temperature_f",
                    "min": 95.0,
                    "max": 106.0,
                    "typical_range": [97.0, 99.5]
                },
                {
                    "name": "Oxygen saturation plausibility",
                    "field": "blood_oxygen_saturation",
                    "min": 70,
                    "max": 100,
                    "typical_range": [95, 100]
                },
                {
                    "name": "WBC count plausibility",
                    "field": "white_blood_cell_count",
                    "min": 2000,
                    "max": 30000,
                    "typical_range": [4500, 11000]
                }
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            data.to_csv(f.name, index=False)
            test_file = f.name
            
        # Create plausibility metadata file
        import json
        plausibility_file = test_file.replace('.csv', '.plausibility.json')
        with open(plausibility_file, 'w') as f:
            json.dump(plausibility_metadata, f)
        
        try:
            # Assess plausibility
            assessor = DataSourceAssessor()
            report = assessor.assess_file(test_file)
            
            # Plausibility should be impacted by impossible values
            plausibility_score = report.dimension_results['plausibility']['score']
            assert plausibility_score <= 15, "Implausible medical values should impact plausibility score"
            
            # Just verify the dimension was assessed
            assert 'plausibility' in report.dimension_results
            assert report.dimension_results['plausibility']['score'] >= 0
            
        finally:
            os.unlink(test_file)
            if os.path.exists(plausibility_file):
                os.unlink(plausibility_file)
