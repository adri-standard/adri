import os
import shutil
import tempfile
from pathlib import Path

import pandas as pd
import yaml

from src.adri.cli.commands.setup import SetupCommand
from src.adri.cli.commands.generate_contract import GenerateContractCommand
from src.adri.validator.engine import ValidationEngine


def test_generate_standard_enriched_and_training_pass_guarantee():
    # Arrange: isolated temp project
    temp_dir = tempfile.mkdtemp()
    try:
        os.chdir(temp_dir)

        # Initialize ADRI project (creates tutorials and config)
        setup_cmd = SetupCommand()
        rc = setup_cmd.execute({"project_name": "enriched_gen_test", "guide": True, "force": False})
        assert rc == 0
        data_path = "ADRI/tutorials/invoice_processing/invoice_data.csv"

        # Act: generate enriched contract from the clean training data
        gen_cmd = GenerateContractCommand()
        rc = gen_cmd.execute({"data_path": data_path, "force": True, "guide": False, "output": None})
        assert rc == 0

        # Locate generated contract
        std_path = Path("ADRI/dev/contracts/invoice_data_ADRI_standard.yaml")
        assert std_path.exists(), "Expected generated contract at ADRI/dev/contracts/"

        # Load contract YAML
        with open(std_path, 'r', encoding='utf-8') as f:
            std = yaml.safe_load(f)

        # Assert: record_identification populated (at root level)
        rid = std.get("record_identification", {})
        pk_fields = rid.get("primary_key_fields", [])
        assert isinstance(pk_fields, list) and len(pk_fields) >= 1

        # Assert: field requirements enriched
        req = std.get("requirements", {})
        field_reqs = req.get("field_requirements", {})
        assert isinstance(field_reqs, dict) and len(field_reqs) > 0

        # Check a few specific fields from sample tutorial data
        assert "invoice_id" in field_reqs
        assert "amount" in field_reqs
        assert "status" in field_reqs

        inv_req = field_reqs["invoice_id"]
        amt_req = field_reqs["amount"]
        status_req = field_reqs["status"]

        # invoice_id: string length constraints present
        if inv_req.get("type") == "string":
            assert "min_length" in inv_req
            assert "max_length" in inv_req
            assert inv_req["min_length"] >= 0
            assert inv_req["max_length"] >= inv_req["min_length"]

        # amount: numeric range present
        if amt_req.get("type") in ("integer", "float"):
            assert "min_value" in amt_req
            assert "max_value" in amt_req
            assert float(amt_req["max_value"]) >= float(amt_req["min_value"])

        # status: likely string with small enum set -> allowed_values present
        # allowed_values can be None, a list, or an enriched dict format
        if status_req.get("type") == "string":
            allowed = status_req.get("allowed_values")
            if allowed is not None:
                # Handle both old list format and new enriched dict format
                if isinstance(allowed, list):
                    assert len(allowed) <= 30, f"Too many allowed values: {len(allowed)}"
                elif isinstance(allowed, dict):
                    # Enriched format has category names as keys
                    assert len(allowed) <= 30, f"Too many allowed values: {len(allowed)}"
                else:
                    raise AssertionError(f"Unexpected allowed_values type: {type(allowed)}")

        # Training-pass guarantee: assessing the training data must pass
        df = pd.read_csv(data_path)
        engine = ValidationEngine()
        result = engine.assess_with_standard_dict(df, std)
        assert result.passed is True
        assert result.overall_score >= req.get("overall_minimum", 75.0)

    finally:
        # Use Windows-safe temp directory cleanup
        import time
        for attempt in range(5):
            try:
                shutil.rmtree(temp_dir)
                break
            except (PermissionError, OSError) as e:
                if attempt < 4:
                    time.sleep(0.1 * (attempt + 1))
                    continue
                try:
                    import subprocess
                    subprocess.run(['rmdir', '/S', '/Q', temp_dir], shell=True, check=False)
                except Exception:
                    pass
