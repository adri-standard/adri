"""
Remote Standards Catalog Client.

Provides list() and fetch() operations against a public standards catalog.
- Uses Python stdlib (urllib) for HTTP
- No third-party dependencies
- Designed for easy mocking in unit tests via a simple HttpAdapter
"""

from __future__ import annotations

import json
import os
import ssl
from dataclasses import dataclass, field
from typing import Any

# Minimal HTTP adapter using stdlib urllib for simple GET operations
try:
    from urllib.error import HTTPError, URLError
    from urllib.request import Request, urlopen
except Exception:  # pragma: no cover
    Request = None  # type: ignore
    urlopen = None  # type: ignore
    URLError = Exception  # type: ignore
    HTTPError = Exception  # type: ignore


@dataclass
class HttpResponse:
    """HTTP response container for UrlLibHttpAdapter GET requests."""

    status: int
    headers: dict[str, str]
    data: bytes
    url: str


class UrlLibHttpAdapter:
    """Simple HTTP adapter for GET using urllib."""

    def get(self, url: str, timeout: int = 10, verify: bool = True) -> HttpResponse:
        """Perform HTTPS GET and return HttpResponse. TLS validation is always enforced."""
        if Request is None or urlopen is None:
            raise RuntimeError("urllib is not available in this environment")

        # Enforce HTTPS scheme for security
        from urllib.parse import urlparse

        parsed = urlparse(url)
        if parsed.scheme.lower() != "https":
            raise ValueError("Only https URLs are allowed for catalog access")

        req = Request(url, method="GET")
        # Always use a verified TLS context (ignore 'verify' to avoid insecure configs)
        context = ssl.create_default_context()
        try:
            with urlopen(req, timeout=timeout, context=context) as resp:  # nosec B310
                status = getattr(resp, "status", 200)
                headers = {k.lower(): v for k, v in resp.headers.items()}
                data = resp.read()
                final_url = getattr(resp, "url", url)
                return HttpResponse(
                    status=status, headers=headers, data=data, url=final_url
                )
        except HTTPError as e:
            return HttpResponse(
                status=getattr(e, "code", 500), headers={}, data=b"", url=url
            )
        except URLError as e:
            # Network error
            raise ConnectionError(str(e)) from e


@dataclass
class CatalogConfig:
    """Configuration for the remote standards catalog client."""

    base_url: str
    timeout_secs: int = 10
    verify_tls: bool = True


@dataclass
class CatalogEntry:
    """Catalog entry describing an available standard in the remote catalog."""

    id: str
    name: str
    version: str
    description: str
    path: str
    tags: list[str] = field(default_factory=list)
    sha256: str | None = None


@dataclass
class CatalogListResponse:
    """Response payload for listing catalog entries."""

    entries: list[CatalogEntry]
    source_url: str


@dataclass
class FetchResult:
    """Fetch result containing the matched entry and the raw YAML bytes."""

    entry: CatalogEntry
    content_bytes: bytes


class CatalogClient:
    """Remote catalog client for listing and fetching ADRI standards."""

    def __init__(self, config: CatalogConfig, http: UrlLibHttpAdapter | None = None):
        """Initialize the catalog client with configuration and optional HTTP adapter."""
        if not config or not config.base_url:
            raise ValueError("CatalogConfig with a valid base_url is required")
        self.config = config
        self.http = http or UrlLibHttpAdapter()

    @staticmethod
    def resolve_base_url() -> str | None:
        """
        Resolve the catalog base URL from environment or ADRI/config.yaml.

        Priority:
          1) ADRI_STANDARDS_CATALOG_URL environment variable
          2) ADRI/config.yaml under adri.catalog.url
          3) None if not configured
        """
        # 1) Environment variable
        env_val = os.environ.get("ADRI_STANDARDS_CATALOG_URL")
        if env_val and env_val.strip():
            return env_val.strip()

        # 2) ADRI/config.yaml if available
        try:
            # Lazy import to avoid cycles
            from ..config.loader import ConfigurationLoader  # type: ignore

            loader = ConfigurationLoader()
            cfg = loader.get_active_config()
            if cfg and isinstance(cfg, dict):
                adri_cfg = cfg.get("adri", {})
                if isinstance(adri_cfg, dict):
                    catalog = adri_cfg.get("catalog", {})
                    if isinstance(catalog, dict):
                        url = catalog.get("url")
                        if url and isinstance(url, str) and url.strip():
                            return url.strip()
        except Exception:
            # No config available or failed to parse
            pass

        return None

    def _get_json(self, url: str) -> Any:
        resp = self.http.get(
            url, timeout=self.config.timeout_secs, verify=self.config.verify_tls
        )
        if resp.status != 200:
            raise RuntimeError(f"HTTP {resp.status} while fetching {url}")
        try:
            return json.loads(resp.data.decode("utf-8"))
        except Exception as e:
            raise ValueError(f"Invalid JSON from {url}: {e}") from e

    @staticmethod
    def _coerce_entry(d: dict[str, Any]) -> CatalogEntry:
        # Coerce/validate minimal fields with fallbacks
        entry_id = str(
            d.get("id") or d.get("name") or d.get("path") or "unknown"
        ).strip()
        name = str(d.get("name") or entry_id).strip()
        version = str(d.get("version") or "1.0.0").strip()
        description = str(d.get("description") or "").strip()
        path = str(d.get("path") or "").strip()
        tags = d.get("tags") or []
        if not isinstance(tags, list):
            tags = []
        sha256 = d.get("sha256")
        if sha256 is not None:
            sha256 = str(sha256)
        if not path:
            # Without a path we cannot fetch the YAML
            raise ValueError(f"Catalog entry '{entry_id}' missing required 'path'")
        return CatalogEntry(
            id=entry_id,
            name=name,
            version=version,
            description=description,
            path=path,
            tags=[str(t) for t in tags],
            sha256=sha256,
        )

    def list(self) -> CatalogListResponse:
        """Fetch the catalog index and return parsed entries."""
        index_url = self.config.base_url.rstrip("/") + "/index.json"
        payload = self._get_json(index_url)

        # Accept either {"entries": [...]} or a bare list
        raw_entries: list[dict[str, Any]]
        if (
            isinstance(payload, dict)
            and "entries" in payload
            and isinstance(payload["entries"], list)
        ):
            raw_entries = payload["entries"]
        elif isinstance(payload, list):
            raw_entries = payload
        else:
            raise ValueError(
                "Catalog index JSON must be a list or contain an 'entries' list"
            )

        entries: list[CatalogEntry] = []
        for item in raw_entries:
            if isinstance(item, dict):
                try:
                    coerced = self._coerce_entry(item)
                except Exception:
                    coerced = None
                if coerced is not None:
                    entries.append(coerced)

        return CatalogListResponse(entries=entries, source_url=index_url)

    def fetch(self, name_or_id: str) -> FetchResult:
        """Fetch a YAML standard by name or id. Name matching is exact, id preferred."""
        listing = self.list()

        # Prefer id matches
        by_id = [e for e in listing.entries if e.id == name_or_id]
        if by_id:
            entry = by_id[0]
        else:
            by_name = [e for e in listing.entries if e.name == name_or_id]
            if len(by_name) == 1:
                entry = by_name[0]
            elif len(by_name) > 1:
                raise ValueError(
                    f"Ambiguous catalog entry name '{name_or_id}' (multiple matches)"
                )
            else:
                raise KeyError(f"Catalog entry '{name_or_id}' not found")

        yaml_url = self.config.base_url.rstrip("/") + "/" + entry.path.lstrip("/")
        resp = self.http.get(
            yaml_url, timeout=self.config.timeout_secs, verify=self.config.verify_tls
        )
        if resp.status != 200:
            raise RuntimeError(f"HTTP {resp.status} while fetching {yaml_url}")

        return FetchResult(entry=entry, content_bytes=resp.data)
