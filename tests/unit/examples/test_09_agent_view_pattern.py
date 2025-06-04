"""Test the agent view pattern example (09_agent_view_pattern.py)."""

import pytest
import subprocess
import sys
import os
import pandas as pd
import tempfile
import json
from unittest.mock import patch, MagicMock
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "examples"))


class TestAgentViewPattern:
    """Test the agent view pattern example."""
    
    def test_example_runs_without_errors(self):
        """Test that the example script runs without errors."""
        # Run the example script
        result = subprocess.run(
            [sys.executable, str(project_root / "examples" / "templates" / "09_agent_view_pattern.py")],
            capture_output=True,
            text=True,
            cwd=str(project_root)
        )
        
        # Check that it completed successfully
        assert result.returncode == 0, f"Script failed with stderr: {result.stderr}"
        
        # Check for expected output sections
        output = result.stdout
        assert "AGENT VIEW PATTERN: Assessing Complex Data as Single Datasets" in output
        assert "Step 1: The Challenge" in output
        assert "Step 2: Creating Sample Multi-Table Data" in output
        assert "Step 3: Creating Denormalized Agent View" in output
        assert "Step 4: Creating Custom Template for Agent View" in output
        assert "Step 5: Assessing View with Custom Template" in output
        assert "Step 6: Benefits of This Approach" in output
        assert "MORE AGENT VIEW EXAMPLES" in output
    
    def test_create_sample_data(self):
        """Test the create_sample_data function."""
        # Import the module correctly
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "agent_view_pattern", 
            str(project_root / "examples" / "templates" / "09_agent_view_pattern.py")
        )
        agent_view_pattern = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(agent_view_pattern)
        
        create_sample_data = agent_view_pattern.create_sample_data
        
        customers, orders, tickets = create_sample_data()
        
        # Check customers
        assert len(customers) == 100
        assert set(customers.columns) == {'customer_id', 'name', 'email', 'created_date', 'lifetime_value'}
        assert customers['customer_id'].min() == 1
        assert customers['customer_id'].max() == 100
        
        # Check orders
        assert len(orders) > 0  # Should have some orders
        assert set(orders.columns) == {'order_id', 'customer_id', 'order_date', 'order_total'}
        
        # Check tickets
        assert len(tickets) >= 0  # May or may not have tickets
        assert set(tickets.columns) == {'ticket_id', 'customer_id', 'created_date', 'satisfaction_score'}
    
    def test_create_agent_view(self):
        """Test the create_agent_view function."""
        # Import the module correctly
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "agent_view_pattern", 
            str(project_root / "examples" / "templates" / "09_agent_view_pattern.py")
        )
        agent_view_pattern = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(agent_view_pattern)
        
        create_sample_data = agent_view_pattern.create_sample_data
        create_agent_view = agent_view_pattern.create_agent_view
        
        # Create sample data
        customers, orders, tickets = create_sample_data()
        
        # Create agent view
        agent_view = create_agent_view(customers, orders, tickets)
        
        # Check structure
        assert len(agent_view) == 100  # Should have all customers
        expected_columns = {
            'customer_id', 'name', 'email', 'created_date', 'lifetime_value',
            'total_orders', 'last_order_date', 'total_order_value', 'avg_order_value',
            'total_tickets', 'avg_satisfaction', 'days_since_last_order'
        }
        assert set(agent_view.columns) == expected_columns
        
        # Check data quality issues were introduced
        # Some emails should be missing (every 20th row)
        assert agent_view['email'].isna().sum() > 0
        
        # Some lifetime values should be negative (every 15th row)
        assert (agent_view['lifetime_value'] < 0).sum() > 0
    
    def test_create_agent_view_template(self):
        """Test the create_agent_view_template function."""
        # Import the module correctly
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "agent_view_pattern", 
            str(project_root / "examples" / "templates" / "09_agent_view_pattern.py")
        )
        agent_view_pattern = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(agent_view_pattern)
        
        create_agent_view_template = agent_view_pattern.create_agent_view_template
        
        template_file = create_agent_view_template()
        
        # Check file was created
        assert os.path.exists(template_file)
        
        # Load and validate template
        with open(template_file, 'r') as f:
            template_content = f.read()
        
        # Parse YAML
        import yaml
        template_data = yaml.safe_load(template_content)
        
        # Check template structure
        assert 'template' in template_data
        assert template_data['template']['id'] == 'customer-360-agent-view'
        assert template_data['template']['version'] == '1.0.0'
        
        # Check requirements
        assert 'requirements' in template_data
        assert 'dimension_requirements' in template_data['requirements']
        assert 'minimum_overall_score' in template_data['requirements']
        
        # Check dimensions
        dimensions = template_data['requirements']['dimension_requirements']
        assert set(dimensions.keys()) == {'validity', 'completeness', 'freshness', 'consistency', 'plausibility'}
        
        # Clean up
        os.unlink(template_file)
    
    def test_agent_view_assessment_integration(self):
        """Test that agent views can be assessed as single datasets."""
        # Import the module correctly
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "agent_view_pattern", 
            str(project_root / "examples" / "templates" / "09_agent_view_pattern.py")
        )
        agent_view_pattern = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(agent_view_pattern)
        
        create_sample_data = agent_view_pattern.create_sample_data
        create_agent_view = agent_view_pattern.create_agent_view
        create_agent_view_template = agent_view_pattern.create_agent_view_template
        
        from adri.assessor import DataSourceAssessor
        from adri.templates.yaml_template import YAMLTemplate
        
        # Create test data
        customers, orders, tickets = create_sample_data()
        agent_view = create_agent_view(customers, orders, tickets)
        
        # Save view to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            agent_view.to_csv(f.name, index=False)
            view_file = f.name
        
        # Create template
        template_file = create_agent_view_template()
        
        try:
            # Load template and assess
            template = YAMLTemplate.from_file(template_file)
            assessor = DataSourceAssessor()
            report = assessor.assess_file(view_file)
            
            # Verify assessment
            assert report is not None
            assert 0 <= report.overall_score <= 100
            
            # Evaluate against template
            evaluation = template.evaluate(report)
            assert evaluation is not None
            assert hasattr(evaluation, 'compliant')
            
            # Check dimension results
            assert 'validity' in report.dimension_results
            assert 'completeness' in report.dimension_results
            assert 'freshness' in report.dimension_results
            assert 'consistency' in report.dimension_results
            assert 'plausibility' in report.dimension_results
            
        finally:
            # Clean up
            os.unlink(view_file)
            os.unlink(template_file)
    
    def test_multiple_agent_views_concept(self):
        """Test that different agent views can have different templates."""
        from adri.templates.yaml_template import YAMLTemplate
        
        # Create different templates for different agent views
        sales_template = """
template:
  id: "sales-forecast-agent-view"
  version: "1.0.0"
  name: "Sales Forecast Agent View"
  category: "agent-views"
  authority: "Sales Operations Team"
  
requirements:
  minimum_overall_score: 90
  dimension_requirements:
    freshness:
      minimum_score: 19  # Very fresh data required
    plausibility:
      minimum_score: 18  # Accurate forecasts need plausible data
"""
        
        inventory_template = """
template:
  id: "inventory-reorder-agent-view"
  version: "1.0.0"
  name: "Inventory Reorder Agent View"
  category: "agent-views"
  authority: "Supply Chain Team"
  
requirements:
  minimum_overall_score: 85
  dimension_requirements:
    completeness:
      minimum_score: 19  # Can't have missing inventory data
    consistency:
      minimum_score: 18  # Stock levels must be consistent
"""
        
        # Save templates
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(sales_template)
            sales_file = f.name
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(inventory_template)
            inventory_file = f.name
        
        try:
            # Load templates
            sales_tmpl = YAMLTemplate.from_file(sales_file)
            inventory_tmpl = YAMLTemplate.from_file(inventory_file)
            
            # Verify different requirements
            sales_requirements = sales_tmpl.get_requirements()
            inventory_requirements = inventory_tmpl.get_requirements()
            
            assert sales_requirements['dimension_requirements']['freshness']['minimum_score'] == 19
            assert inventory_requirements['dimension_requirements']['completeness']['minimum_score'] == 19
            
            # Verify different overall requirements
            assert sales_requirements.get('minimum_overall_score', 0) == 90
            assert inventory_requirements.get('minimum_overall_score', 0) == 85
            
        finally:
            os.unlink(sales_file)
            os.unlink(inventory_file)
    
    def test_agent_view_pattern_validates_single_dataset_focus(self):
        """Test that the agent view pattern maintains ADRI's single dataset focus."""
        from adri.assessor import DataSourceAssessor
        
        assessor = DataSourceAssessor()
        
        # Verify assessor can only handle single files
        assert hasattr(assessor, 'assess_file')
        assert not hasattr(assessor, 'assess_multiple_files')
        
        # Verify trying to assess multiple files would fail
        with pytest.raises(TypeError):
            assessor.assess_file(["file1.csv", "file2.csv"])
