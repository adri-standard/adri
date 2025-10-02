"""
CatalogClient unit tests for remote standards catalog.
Covers: resolve_base_url, list(), fetch() with mocked HTTP adapter, and error paths.
"""

import os
import json
import tempfile
import shutil
import unittest
from pathlib import Path
from typing import Dict

from src.adri.catalog.client import (
    CatalogClient,
    CatalogConfig,
    HttpResponse,
)


class MockHttp:
    """Simple mock HTTP adapter for CatalogClient"""

    def __init__(self, responses: Dict[str, HttpResponse]):
        self.responses = responses

    def get(self, url: str, timeout: int = 10, verify: bool = True) -> HttpResponse:
        if url not in self.responses:
            # Simulate network error if not found
            return HttpResponse(status=404, headers={}, data=b"", url=url)
        return self.responses[url]


class TestCatalogClient(unittest.TestCase):
    def setUp(self):
        self.base_url = "https://example.com/catalog"
        self.index_url = f"{self.base_url}/index.json"

        # Prepare index payload with valid and invalid entries
        index_entries = [
            {
                "id": "std1",
                "name": "Standard One",
                "version": "1.0.0",
                "description": "Test standard one",
                "path": "std1.yaml",
                "tags": ["alpha"],
            },
            {
                # Missing path -> should be skipped
                "id": "no_path",
                "name": "No Path",
                "version": "1.0.0",
                "description": "invalid",
            },
            {
                "id": "dupname1",
                "name": "dup",
                "version": "1.0.0",
                "path": "dup1.yaml",
            },
            {
                "id": "dupname2",
                "name": "dup",
                "version": "1.0.0",
                "path": "dup2.yaml",
            },
        ]
        self.index_bytes = json.dumps({"entries": index_entries}).encode("utf-8")

        self.yaml_std1 = b"standards:\n  id: std1\n  name: Standard One\nrequirements:\n  overall_minimum: 75.0\n"
        self.yaml_dup1 = b"standards:\n  id: dupname1\n  name: dup\nrequirements:\n  overall_minimum: 80.0\n"

        self.responses = {
            self.index_url: HttpResponse(
                status=200, headers={}, data=self.index_bytes, url=self.index_url
            ),
            f"{self.base_url}/std1.yaml": HttpResponse(
                status=200, headers={}, data=self.yaml_std1, url=f"{self.base_url}/std1.yaml"
            ),
            f"{self.base_url}/dup1.yaml": HttpResponse(
                status=200, headers={}, data=self.yaml_dup1, url=f"{self.base_url}/dup1.yaml"
            ),
        }

    def test_resolve_base_url_from_env(self):
        old = os.environ.get("ADRI_STANDARDS_CATALOG_URL")
        try:
            os.environ["ADRI_STANDARDS_CATALOG_URL"] = "https://catalog.example.org/base"
            val = CatalogClient.resolve_base_url()
            self.assertEqual(val, "https://catalog.example.org/base")
        finally:
            if old is None:
                del os.environ["ADRI_STANDARDS_CATALOG_URL"]
            else:
                os.environ["ADRI_STANDARDS_CATALOG_URL"] = old

    def test_list_parses_entries_and_skips_invalid(self):
        client = CatalogClient(CatalogConfig(base_url=self.base_url), http=MockHttp(self.responses))
        listing = client.list()
        self.assertEqual(listing.source_url, self.index_url)
        # Should include std1 + dupname1 + dupname2 (3 entries), skip no_path
        self.assertEqual(len(listing.entries), 3)
        ids = {e.id for e in listing.entries}
        self.assertIn("std1", ids)
        self.assertIn("dupname1", ids)
        self.assertIn("dupname2", ids)

    def test_fetch_by_id_success(self):
        client = CatalogClient(CatalogConfig(base_url=self.base_url), http=MockHttp(self.responses))
        res = client.fetch("std1")
        self.assertEqual(res.entry.id, "std1")
        self.assertGreater(len(res.content_bytes), 0)

    def test_fetch_by_name_ambiguous_raises(self):
        client = CatalogClient(CatalogConfig(base_url=self.base_url), http=MockHttp(self.responses))
        with self.assertRaises(ValueError):
            client.fetch("dup")

    def test_list_http_non_200_raises(self):
        bad_responses = {
            self.index_url: HttpResponse(status=500, headers={}, data=b"", url=self.index_url)
        }
        client = CatalogClient(CatalogConfig(base_url=self.base_url), http=MockHttp(bad_responses))
        with self.assertRaises(RuntimeError):
            client.list()

    def test_list_invalid_json_raises(self):
        bad_json_responses = {
            self.index_url: HttpResponse(status=200, headers={}, data=b"{not json", url=self.index_url)
        }
        client = CatalogClient(CatalogConfig(base_url=self.base_url), http=MockHttp(bad_json_responses))
        with self.assertRaises(ValueError):
            client.list()

    def test_fetch_yaml_non_200_raises(self):
        # Provide index OK but missing YAML resource -> 404
        client = CatalogClient(CatalogConfig(base_url=self.base_url), http=MockHttp(self.responses))
        # Remove std1.yaml to cause 404
        del self.responses[f"{self.base_url}/std1.yaml"]
        with self.assertRaises(RuntimeError):
            client.fetch("std1")


if __name__ == "__main__":
    unittest.main()
