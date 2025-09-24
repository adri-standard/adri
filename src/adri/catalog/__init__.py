"""
ADRI Remote Standards Catalog package.

Exports:
- CatalogClient: Client for listing and fetching standards from a remote catalog
- CatalogConfig: Configuration for the catalog client
- CatalogEntry, CatalogListResponse, FetchResult: Typed results and entities
"""

from .client import (
    CatalogClient,
    CatalogConfig,
    CatalogEntry,
    CatalogListResponse,
    FetchResult,
)

__all__ = [
    "CatalogClient",
    "CatalogConfig",
    "CatalogEntry",
    "CatalogListResponse",
    "FetchResult",
]
