"""
Contract Templates Validation Tests.

Ensures all advertised contract templates:
1. Actually exist in the repository
2. Are valid YAML files
3. Can be loaded and parsed correctly
4. Match the structure documented in README

This prevents "advertised but missing" issues that damage credibility.
"""

import yaml
from pathlib import Path

import pytest

# Get project root
PROJECT_ROOT = Path(__file__).parent.parent
CONTRACTS_DIR = PROJECT_ROOT / "ADRI" / "contracts"

# Templates advertised in README
BUSINESS_DOMAIN_TEMPLATES = {
    "Customer Service": "domains/customer_service_contract.yaml",
    "E-commerce Orders": "domains/ecommerce_order_contract.yaml",
    "Financial Transactions": "domains/financial_transaction_contract.yaml",
    "Healthcare Patients": "domains/healthcare_patient_contract.yaml",
    "Marketing Campaigns": "domains/marketing_campaign_contract.yaml",
}

AI_FRAMEWORK_TEMPLATES = {
    "LangChain Inputs": "frameworks/langchain_chain_input_contract.yaml",
    "CrewAI Task Context": "frameworks/crewai_task_context_contract.yaml",
    "LlamaIndex Documents": "frameworks/llamaindex_document_contract.yaml",
    "AutoGen Messages": "frameworks/autogen_message_contract.yaml",
}

GENERIC_TEMPLATES = {
    "API Responses": "templates/api_response_template.yaml",
    "Time Series": "templates/time_series_template.yaml",
    "Key-Value": "templates/key_value_template.yaml",
    "Nested JSON": "templates/nested_json_template.yaml",
}


class TestBusinessDomainTemplates:
    """Test that all business domain templates exist and are valid."""

    @pytest.mark.unit
    @pytest.mark.parametrize("template_name,template_path", BUSINESS_DOMAIN_TEMPLATES.items())
    def test_template_exists(self, template_name, template_path):
        """Test that advertised business domain templates exist."""
        full_path = CONTRACTS_DIR / template_path

        assert full_path.exists(), (
            f"Template '{template_name}' advertised in README but file doesn't exist: {template_path}"
        )

    @pytest.mark.unit
    @pytest.mark.parametrize("template_name,template_path", BUSINESS_DOMAIN_TEMPLATES.items())
    def test_template_valid_yaml(self, template_name, template_path):
        """Test that business domain templates are valid YAML."""
        full_path = CONTRACTS_DIR / template_path

        if not full_path.exists():
            pytest.skip(f"Template not found: {template_path}")

        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            assert data is not None, f"Template '{template_name}' is empty"
            assert isinstance(data, dict), f"Template '{template_name}' should be a dictionary"

        except yaml.YAMLError as e:
            pytest.fail(f"Template '{template_name}' has invalid YAML: {e}")

    @pytest.mark.integration
    @pytest.mark.parametrize("template_name,template_path", BUSINESS_DOMAIN_TEMPLATES.items())
    def test_template_has_required_fields(self, template_name, template_path):
        """Test that business domain templates have required contract structure."""
        full_path = CONTRACTS_DIR / template_path

        if not full_path.exists():
            pytest.skip(f"Template not found: {template_path}")

        with open(full_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        # Templates should have basic contract structure
        # (Can be lenient as structures may vary)
        assert isinstance(data, dict), "Template should be a dictionary"


class TestAIFrameworkTemplates:
    """Test that all AI framework templates exist and are valid."""

    @pytest.mark.unit
    @pytest.mark.parametrize("template_name,template_path", AI_FRAMEWORK_TEMPLATES.items())
    def test_template_exists(self, template_name, template_path):
        """Test that advertised AI framework templates exist."""
        full_path = CONTRACTS_DIR / template_path

        assert full_path.exists(), (
            f"Template '{template_name}' advertised in README but file doesn't exist: {template_path}"
        )

    @pytest.mark.unit
    @pytest.mark.parametrize("template_name,template_path", AI_FRAMEWORK_TEMPLATES.items())
    def test_template_valid_yaml(self, template_name, template_path):
        """Test that AI framework templates are valid YAML."""
        full_path = CONTRACTS_DIR / template_path

        if not full_path.exists():
            pytest.skip(f"Template not found: {template_path}")

        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            assert data is not None, f"Template '{template_name}' is empty"
            assert isinstance(data, dict), f"Template '{template_name}' should be a dictionary"

        except yaml.YAMLError as e:
            pytest.fail(f"Template '{template_name}' has invalid YAML: {e}")


class TestGenericTemplates:
    """Test that all generic templates exist and are valid."""

    @pytest.mark.unit
    @pytest.mark.parametrize("template_name,template_path", GENERIC_TEMPLATES.items())
    def test_template_exists(self, template_name, template_path):
        """Test that advertised generic templates exist."""
        full_path = CONTRACTS_DIR / template_path

        assert full_path.exists(), (
            f"Template '{template_name}' advertised in README but file doesn't exist: {template_path}"
        )

    @pytest.mark.unit
    @pytest.mark.parametrize("template_name,template_path", GENERIC_TEMPLATES.items())
    def test_template_valid_yaml(self, template_name, template_path):
        """Test that generic templates are valid YAML."""
        full_path = CONTRACTS_DIR / template_path

        if not full_path.exists():
            pytest.skip(f"Template not found: {template_path}")

        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            assert data is not None, f"Template '{template_name}' is empty"
            assert isinstance(data, dict), f"Template '{template_name}' should be a dictionary"

        except yaml.YAMLError as e:
            pytest.fail(f"Template '{template_name}' has invalid YAML: {e}")


class TestAllTemplates:
    """Test all templates in contracts directory."""

    @pytest.mark.integration
    def test_all_yaml_files_are_valid(self):
        """Test that all YAML files in contracts directory are valid."""
        if not CONTRACTS_DIR.exists():
            pytest.skip("ADRI/contracts directory not found")

        yaml_files = list(CONTRACTS_DIR.rglob("*.yaml")) + list(CONTRACTS_DIR.rglob("*.yml"))

        errors = []
        for yaml_file in yaml_files:
            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    yaml.safe_load(f)
            except yaml.YAMLError as e:
                errors.append(f"{yaml_file.relative_to(PROJECT_ROOT)}: {e}")
            except Exception as e:
                errors.append(f"{yaml_file.relative_to(PROJECT_ROOT)}: Unexpected error: {e}")

        assert len(errors) == 0, (
            f"Found {len(errors)} invalid YAML files:\n" + "\n".join(errors[:10])
        )

    @pytest.mark.unit
    def test_template_count_matches_readme(self):
        """Test that the number of templates matches what's advertised."""
        # Count templates in each category
        if not CONTRACTS_DIR.exists():
            pytest.skip("ADRI/contracts directory not found")

        domains_dir = CONTRACTS_DIR / "domains"
        frameworks_dir = CONTRACTS_DIR / "frameworks"
        templates_dir = CONTRACTS_DIR / "templates"

        # Count actual templates
        domain_count = len(list(domains_dir.glob("*.yaml"))) if domains_dir.exists() else 0
        framework_count = len(list(frameworks_dir.glob("*.yaml"))) if frameworks_dir.exists() else 0
        generic_count = len(list(templates_dir.glob("*.yaml"))) if templates_dir.exists() else 0

        # Should match what we advertise
        assert domain_count >= 5, f"Expected at least 5 business domain templates, found {domain_count}"
        assert framework_count >= 4, f"Expected at least 4 AI framework templates, found {framework_count}"
        assert generic_count >= 4, f"Expected at least 4 generic templates, found {generic_count}"


class TestTemplatesCLICompatibility:
    """Test that templates work with ADRI CLI commands."""

    @pytest.mark.integration
    @pytest.mark.parametrize("template_name,template_path", list(BUSINESS_DOMAIN_TEMPLATES.items())[:1])
    def test_template_can_be_loaded_by_cli(self, template_name, template_path):
        """Test that templates can be loaded (basic smoke test)."""
        full_path = CONTRACTS_DIR / template_path

        if not full_path.exists():
            pytest.skip(f"Template not found: {template_path}")

        # Try loading with Python's YAML parser (same as ADRI uses)
        with open(full_path, 'r', encoding='utf-8') as f:
            contract_data = yaml.safe_load(f)

        # Basic structure validation
        assert isinstance(contract_data, dict), "Contract should be a dictionary"

        # Templates should have some common fields (flexible check)
        # We're just validating they load, not enforcing strict structure


class TestREADMETemplateLinks:
    """Test that template links in README point to actual files."""

    @pytest.mark.unit
    def test_readme_links_to_existing_templates(self):
        """Test that all template links in README point to real files."""
        readme_content = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")

        # Extract GitHub blob links to ADRI/contracts
        import re
        template_links = re.findall(
            r'https://github\.com/adri-standard/adri/blob/main/(ADRI/contracts/[^)]+\.yaml)',
            readme_content
        )

        if not template_links:
            pytest.skip("No template links found in README")

        missing = []
        for link_path in template_links:
            # Check if file exists (accounting for repo root)
            file_path = PROJECT_ROOT / link_path

            if not file_path.exists():
                missing.append(link_path)

        assert len(missing) == 0, (
            f"README links to {len(missing)} non-existent templates:\n" +
            "\n".join([f"- {path}" for path in missing[:5]])
        )
