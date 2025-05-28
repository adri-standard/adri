"""Test that ADRI architecture decisions are properly enforced."""

import pytest
from pathlib import Path
import tempfile
import os

from adri.assessor import DataSourceAssessor
from adri.connectors.base import BaseConnector
from adri.connectors.file import FileConnector


class TestArchitectureEnforcement:
    """Test that ADRI enforces single dataset assessment architecture."""
    
    def test_assessor_single_file_only(self):
        """Test that assessor only supports single file assessment."""
        assessor = DataSourceAssessor()
        
        # Verify correct methods exist
        assert hasattr(assessor, 'assess_file')
        assert hasattr(assessor, 'assess_api')
        assert hasattr(assessor, 'assess_database')
        
        # Verify multi-dataset methods don't exist
        assert not hasattr(assessor, 'assess_multiple_files')
        assert not hasattr(assessor, 'assess_files')
        assert not hasattr(assessor, 'assess_datasets')
    
    def test_file_connector_single_file_only(self):
        """Test that file connector only handles single files."""
        # Create a temporary test file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("id,value\n1,test\n")
            test_file = f.name
        
        try:
            # FileConnector should work with single file
            connector = FileConnector(test_file)
            assert connector.file_path == Path(test_file)
            
            # Should not accept list of files
            with pytest.raises(TypeError):
                FileConnector([test_file, "another.csv"])
                
        finally:
            os.unlink(test_file)
    
    def test_assessor_rejects_file_list(self):
        """Test that assessor rejects lists of files."""
        assessor = DataSourceAssessor()
        
        # Create test files
        files = []
        for i in range(3):
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
                f.write(f"id,value\n{i},test{i}\n")
                files.append(f.name)
        
        try:
            # Should reject list of files
            with pytest.raises(TypeError):
                assessor.assess_file(files)
            
            # Should reject tuple of files
            with pytest.raises(TypeError):
                assessor.assess_file(tuple(files))
                
        finally:
            for f in files:
                os.unlink(f)
    
    def test_no_cross_dataset_validation(self):
        """Test that ADRI doesn't provide cross-dataset validation."""
        assessor = DataSourceAssessor()
        
        # Create two related test files
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("customer_id,name\n1,Alice\n2,Bob\n")
            customers_file = f.name
            
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("order_id,customer_id,amount\n1,1,100\n2,3,200\n")  # customer_id 3 doesn't exist
            orders_file = f.name
        
        try:
            # Assess each file independently
            customers_report = assessor.assess_file(customers_file)
            orders_report = assessor.assess_file(orders_file)
            
            # Both should succeed independently
            assert customers_report is not None
            assert orders_report is not None
            
            # No method to validate relationships
            assert not hasattr(assessor, 'validate_relationship')
            assert not hasattr(assessor, 'check_referential_integrity')
            
        finally:
            os.unlink(customers_file)
            os.unlink(orders_file)
    
    def test_template_universality(self):
        """Test that templates work universally without org-specific logic."""
        from adri.templates.yaml_template import YAMLTemplate
        
        # Create a universal template
        template_content = """
template:
  id: "customer-master"
  version: "2.0.0"
  name: "Customer Master Data"
  description: "Universal template for customer data"
  category: "master-data"
  authority: "Data Quality Team"
  
requirements:
  minimum_overall_score: 80
  dimension_requirements:
    validity:
      minimum_score: 18
    completeness:
      minimum_score: 17
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(template_content)
            template_file = f.name
        
        try:
            # Load template
            template = YAMLTemplate.from_file(template_file)
            
            # Template should not have org-specific fields
            assert not hasattr(template, 'organization')
            assert not hasattr(template, 'company')
            
            # Should work with any customer data regardless of source
            assert template.template_id == "customer-master"
            assert template.template_data['template']['category'] == "master-data"
            
        finally:
            os.unlink(template_file)
    
    def test_agent_view_pattern_as_workaround(self):
        """Test that agent view pattern works as intended workaround."""
        import pandas as pd
        
        # Create multi-table data
        customers = pd.DataFrame({
            'customer_id': [1, 2, 3],
            'name': ['Alice', 'Bob', 'Charlie']
        })
        
        orders = pd.DataFrame({
            'order_id': [1, 2, 3],
            'customer_id': [1, 2, 1],
            'amount': [100, 200, 150]
        })
        
        # Create denormalized view (the workaround)
        order_summary = orders.groupby('customer_id').agg({
            'order_id': 'count',
            'amount': ['sum', 'mean']
        }).reset_index()
        
        # Flatten the multi-level columns
        order_summary.columns = ['customer_id', 'order_count', 'total_amount', 'avg_amount']
        
        # Merge with customers
        agent_view = customers.merge(order_summary, on='customer_id', how='left')
        
        # Save as single file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            agent_view.to_csv(f.name, index=False)
            view_file = f.name
        
        try:
            # Can assess the denormalized view as single dataset
            assessor = DataSourceAssessor()
            report = assessor.assess_file(view_file)
            
            assert report is not None
            assert 0 <= report.overall_score <= 100
            
        finally:
            os.unlink(view_file)
    
    def test_composition_over_extension(self):
        """Test that ADRI encourages composition with other tools."""
        assessor = DataSourceAssessor()
        
        # ADRI should provide data about quality, not transform data
        assert not hasattr(assessor, 'join_datasets')
        assert not hasattr(assessor, 'merge_files')
        assert not hasattr(assessor, 'transform_data')
        
        # ADRI focuses on assessment
        assert hasattr(assessor, 'assess_file')
        
        # Results are meant to be used by other tools
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("id,value\n1,test\n")
            test_file = f.name
        
        try:
            report = assessor.assess_file(test_file)
            
            # Report provides data that other tools can use
            assert hasattr(report, 'to_dict')
            assert hasattr(report, 'save_json')
            
            # Other tools can consume this data
            report_data = report.to_dict()
            assert 'overall_score' in report_data
            assert 'dimension_results' in report_data
            
        finally:
            os.unlink(test_file)
