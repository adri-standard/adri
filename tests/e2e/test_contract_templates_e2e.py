"""
End-to-end tests for ADRI contract templates.

Validates that all advertised contract templates in the ADRI/contracts/
directory work correctly with real data assessments.
"""

import os
from pathlib import Path

import pandas as pd
import pytest
import yaml

from adri.cli import assess_command, generate_standard_command, setup_command


@pytest.mark.e2e
class TestBusinessDomainTemplatesE2E:
    """E2E tests for business domain contract templates."""

    def test_customer_service_template_exists_and_valid(self):
        """Test customer service template exists and is valid YAML."""
        project_root = Path(__file__).parent.parent.parent
        template_path = project_root / "ADRI" / "contracts" / "domains" / "customer_service_contract.yaml"
        
        assert template_path.exists(), "Customer service template not found"
        
        # Should load as valid YAML
        with open(template_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        assert data is not None
        assert isinstance(data, dict)

    def test_ecommerce_order_template_valid(self):
        """Test e-commerce order template is valid."""
        project_root = Path(__file__).parent.parent.parent
        template_path = project_root / "ADRI" / "contracts" / "domains" / "ecommerce_order_contract.yaml"
        
        assert template_path.exists(), "E-commerce template not found"
        
        with open(template_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        assert data is not None
        assert isinstance(data, dict)

    def test_financial_transaction_template_valid(self):
        """Test financial transaction template is valid."""
        project_root = Path(__file__).parent.parent.parent
        template_path = project_root / "ADRI" / "contracts" / "domains" / "financial_transaction_contract.yaml"
        
        assert template_path.exists(), "Financial template not found"
        
        with open(template_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        assert data is not None
        assert isinstance(data, dict)


@pytest.mark.e2e
class TestAIFrameworkTemplatesE2E:
    """E2E tests for AI framework contract templates."""

    def test_langchain_template_exists_and_valid(self):
        """Test LangChain template exists and is valid."""
        project_root = Path(__file__).parent.parent.parent
        template_path = project_root / "ADRI" / "contracts" / "frameworks" / "langchain_chain_input_contract.yaml"
        
        assert template_path.exists(), "LangChain template not found"
        
        with open(template_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        assert data is not None
        assert isinstance(data, dict)

    def test_crewai_template_exists_and_valid(self):
        """Test CrewAI template exists and is valid."""
        project_root = Path(__file__).parent.parent.parent
        template_path = project_root / "ADRI" / "contracts" / "frameworks" / "crewai_task_context_contract.yaml"
        
        assert template_path.exists(), "CrewAI template not found"
        
        with open(template_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        assert data is not None
        assert isinstance(data, dict)

    def test_llamaindex_template_exists_and_valid(self):
        """Test LlamaIndex template exists and is valid."""
        project_root = Path(__file__).parent.parent.parent
        template_path = project_root / "ADRI" / "contracts" / "frameworks" / "llamaindex_document_contract.yaml"
        
        assert template_path.exists(), "LlamaIndex template not found"
        
        with open(template_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        assert data is not None
        assert isinstance(data, dict)


@pytest.mark.e2e
class TestGenericTemplatesE2E:
    """E2E tests for generic contract templates."""

    def test_api_response_template_valid(self):
        """Test API response template is valid."""
        project_root = Path(__file__).parent.parent.parent
        template_path = project_root / "ADRI" / "contracts" / "api_response_template.yaml"
        
        # Template might be in templates/ or root
        if not template_path.exists():
            template_path = project_root / "ADRI" / "contracts" / "templates" / "api_response_template.yaml"
        
        if template_path.exists():
            with open(template_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            assert data is not None
            assert isinstance(data, dict)


@pytest.mark.e2e
class TestTemplatesWithRealData:
    """Tests that validate templates work with actual data."""

    def test_template_can_be_used_for_assessment(self, clean_adri_state, sample_csv_file):
        """Test that a generated contract can be used for assessment."""
        original_cwd = os.getcwd()
        try:
            os.chdir(clean_adri_state)
            
            # Setup ADRI
            setup_exit = setup_command(force=True, project_name="test", guide=False)
            assert setup_exit == 0
            
            # Generate a contract from data using absolute path
            gen_exit = generate_standard_command(
                data_path=str(sample_csv_file.absolute()),
                force=True,
                output=None,
                guide=False
            )
            assert gen_exit == 0
            
            # Find generated contract
            contracts_dir = clean_adri_state / "ADRI" / "contracts"
            contract_files = list(contracts_dir.glob("*.yaml"))
            
            if len(contract_files) > 0:
                contract_file = contract_files[0]
                
                # Use it for assessment with absolute path
                assess_exit = assess_command(
                    data_path=str(sample_csv_file.absolute()),
                    standard_path=str(contract_file.absolute()),
                    output_path=None,
                    guide=False
                )
                
                # Should pass - assessing same data used to generate contract
                assert assess_exit == 0, "Assessment should pass when using same data that generated the contract"
        finally:
            os.chdir(original_cwd)

    def test_template_with_matching_data_succeeds(self, clean_adri_state):
        """Test that template with well-matched data succeeds assessment."""
        original_cwd = os.getcwd()
        try:
            os.chdir(clean_adri_state)
            
            # Setup
            setup_command(force=True, project_name="test", guide=False)
            
            # Create very clean data
            clean_data = pd.DataFrame({
                "id": [1, 2, 3, 4, 5],
                "name": ["Alice", "Bob", "Charlie", "David", "Eve"],
                "email": ["alice@example.com", "bob@example.com", "charlie@example.com", 
                         "david@example.com", "eve@example.com"],
                "age": [25, 30, 35, 40, 45],
                "created": ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05"]
            })
            
            data_file = clean_adri_state / "clean_data.csv"
            clean_data.to_csv(data_file, index=False)
            
            # Generate contract using absolute path
            gen_exit = generate_standard_command(
                data_path=str(data_file.absolute()),
                force=True,
                output=None,
                guide=False
            )
            assert gen_exit == 0
            
            # Find contract
            contracts_dir = clean_adri_state / "ADRI" / "contracts"
            contract_files = list(contracts_dir.glob("*.yaml"))
            
            if len(contract_files) > 0:
                contract_file = contract_files[0]
                
                # Assess same clean data - should pass
                assess_exit = assess_command(
                    data_path=str(data_file.absolute()),
                    standard_path=str(contract_file.absolute()),
                    output_path=None,
                    guide=False
                )
                
                # Should succeed with clean data
                assert assess_exit == 0
        finally:
            os.chdir(original_cwd)


@pytest.mark.e2e
class TestTemplateCustomization:
    """Tests for template customization workflow."""

    def test_template_can_be_copied_and_modified(self):
        """Test that templates can be copied and customized."""
        project_root = Path(__file__).parent.parent.parent
        template_dir = project_root / "ADRI" / "contracts" / "domains"
        
        if not template_dir.exists():
            pytest.skip("Contract templates directory not found")
        
        # Find any template
        template_files = list(template_dir.glob("*.yaml"))
        
        if len(template_files) == 0:
            pytest.skip("No templates found")
        
        template_file = template_files[0]
        
        # Should be readable
        with open(template_file, 'r', encoding='utf-8') as f:
            original_data = yaml.safe_load(f)
        
        assert original_data is not None
        
        # Create a modified copy (just change metadata)
        modified_data = original_data.copy()
        if isinstance(modified_data, dict):
            modified_data['custom_field'] = 'test_value'
            
            # Should be serializable back to YAML
            yaml_output = yaml.dump(modified_data)
            assert len(yaml_output) > 0


@pytest.mark.e2e
class TestTemplateDocumentationAccuracy:
    """Tests that validate template documentation is accurate."""

    def test_readme_lists_existing_business_templates(self):
        """Test that README lists templates that actually exist."""
        project_root = Path(__file__).parent.parent.parent
        readme = project_root / "README.md"
        
        if not readme.exists():
            pytest.skip("README.md not found")
        
        content = readme.read_text(encoding="utf-8")
        
        # Templates mentioned in README
        template_names = [
            "customer_service_contract.yaml",
            "ecommerce_order_contract.yaml",
            "financial_transaction_contract.yaml",
            "healthcare_patient_contract.yaml",
        ]
        
        for template_name in template_names:
            # Check if mentioned in README
            if template_name.replace("_contract.yaml", "").replace("_", " ").title() in content:
                # Verify template exists
                template_path = project_root / "ADRI" / "contracts" / "domains" / template_name
                assert template_path.exists(), f"README mentions {template_name} but file doesn't exist"

    def test_readme_lists_existing_framework_templates(self):
        """Test that README AI framework templates exist."""  
        project_root = Path(__file__).parent.parent.parent
        
        framework_templates = [
            "langchain_chain_input_contract.yaml",
            "crewai_task_context_contract.yaml",
            "llamaindex_document_contract.yaml",
        ]
        
        for template_name in framework_templates:
            template_path = project_root / "ADRI" / "contracts" / "frameworks" / template_name
            assert template_path.exists(), f"Framework template {template_name} not found"
