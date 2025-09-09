#!/usr/bin/env python3
"""
PyPI Version Management Module for ADRI Validator.

This module provides PyPI-first version management by querying PyPI APIs
to determine current versions and calculate next valid versions based on
change types. It eliminates synchronization issues by using PyPI as the
single source of truth.

Key Features:
- Query production PyPI and TestPyPI for current versions
- Automatic next version calculation based on change type
- Version normalization and conflict resolution
- Caching and fallback mechanisms
- Integration with existing VERSION.json for audit trail
"""

import json
import re
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen


class PyPIError(Exception):
    """Custom exception for PyPI-related errors."""

    pass


class PyPIManager:
    """Manages PyPI-first version discovery and calculation."""

    def __init__(self, package_name: str = "adri", cache_ttl_minutes: int = 5):
        """
        Initialize PyPI manager.

        Args:
            package_name: Name of the package on PyPI
            cache_ttl_minutes: Cache TTL in minutes to avoid rate limiting
        """
        self.package_name = package_name
        self.cache_ttl = timedelta(minutes=cache_ttl_minutes)
        self.cache = {}

        # PyPI endpoints
        self.pypi_api_base = "https://pypi.org/pypi"
        self.testpypi_api_base = "https://test.pypi.org/pypi"

        # Version file for fallback
        self.version_file = self._find_version_file()

    def _find_version_file(self) -> Path:
        """Find VERSION.json file."""
        # Check current directory first, then parent
        for path in [Path("VERSION.json"), Path("../VERSION.json")]:
            if path.exists():
                return path
        raise FileNotFoundError("VERSION.json not found")

    def _make_request(self, url: str, timeout: int = 10) -> Dict:
        """
        Make HTTP request to PyPI API with error handling.

        Args:
            url: API endpoint URL
            timeout: Request timeout in seconds

        Returns:
            JSON response as dictionary

        Raises:
            PyPIError: If request fails
        """
        try:
            req = Request(url)
            req.add_header("User-Agent", "ADRI-Validator-Release-Tool/1.0")

            with urlopen(req, timeout=timeout) as response:
                if response.status == 200:
                    return json.loads(response.read().decode("utf-8"))
                else:
                    raise PyPIError(f"HTTP {response.status} from {url}")

        except HTTPError as e:
            if e.code == 404:
                raise PyPIError(f"Package '{self.package_name}' not found on PyPI")
            else:
                raise PyPIError(f"HTTP error {e.code}: {e.reason}")
        except URLError as e:
            raise PyPIError(f"Network error: {e.reason}")
        except json.JSONDecodeError as e:
            raise PyPIError(f"Invalid JSON response: {e}")
        except Exception as e:
            raise PyPIError(f"Unexpected error: {e}")

    def _get_cached_or_fetch(self, cache_key: str, url: str) -> Optional[Dict]:
        """
        Get data from cache or fetch from API.

        Args:
            cache_key: Key for caching
            url: API URL to fetch from

        Returns:
            API response data or None if failed
        """
        # Check cache first
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if datetime.now() - timestamp < self.cache_ttl:
                return cached_data

        # Fetch fresh data
        try:
            data = self._make_request(url)
            self.cache[cache_key] = (data, datetime.now())
            return data
        except PyPIError as e:
            print(f"Warning: Failed to fetch from {url}: {e}")
            return None

    def get_pypi_versions(
        self, include_prereleases: bool = True
    ) -> Dict[str, List[str]]:
        """
        Get all versions from production PyPI.

        Args:
            include_prereleases: Include pre-release versions

        Returns:
            Dict with 'releases' and 'latest' keys
        """
        url = f"{self.pypi_api_base}/{self.package_name}/json"
        data = self._get_cached_or_fetch(f"pypi_{self.package_name}", url)

        if not data:
            return {"releases": [], "latest": None}

        # Extract versions
        all_versions = list(data.get("releases", {}).keys())

        # Filter prereleases if requested
        if not include_prereleases:
            all_versions = [v for v in all_versions if not self._is_prerelease(v)]

        # Sort versions (most recent first)
        sorted_versions = self._sort_versions(all_versions, reverse=True)

        return {
            "releases": sorted_versions,
            "latest": sorted_versions[0] if sorted_versions else None,
            "info": data.get("info", {}),
        }

    def get_testpypi_versions(
        self, include_prereleases: bool = True
    ) -> Dict[str, List[str]]:
        """
        Get all versions from TestPyPI.

        Args:
            include_prereleases: Include pre-release versions

        Returns:
            Dict with 'releases' and 'latest' keys
        """
        url = f"{self.testpypi_api_base}/{self.package_name}/json"
        data = self._get_cached_or_fetch(f"testpypi_{self.package_name}", url)

        if not data:
            return {"releases": [], "latest": None}

        # Extract versions
        all_versions = list(data.get("releases", {}).keys())

        # Filter prereleases if requested
        if not include_prereleases:
            all_versions = [v for v in all_versions if not self._is_prerelease(v)]

        # Sort versions (most recent first)
        sorted_versions = self._sort_versions(all_versions, reverse=True)

        return {
            "releases": sorted_versions,
            "latest": sorted_versions[0] if sorted_versions else None,
            "info": data.get("info", {}),
        }

    def get_current_production_version(self) -> Optional[str]:
        """
        Get the current production version from PyPI.

        Returns:
            Latest production version or None if not found
        """
        try:
            pypi_data = self.get_pypi_versions(include_prereleases=False)
            return pypi_data.get("latest")
        except Exception as e:
            print(f"Warning: Could not get production version: {e}")
            return self._get_fallback_version("current_release")

    def get_current_testpypi_version(self) -> Optional[str]:
        """
        Get the current TestPyPI version.

        Returns:
            Latest TestPyPI version or None if not found
        """
        try:
            testpypi_data = self.get_testpypi_versions(include_prereleases=True)
            return testpypi_data.get("latest")
        except Exception as e:
            print(f"Warning: Could not get TestPyPI version: {e}")
            return self._get_fallback_version("current_testpypi")

    def _get_fallback_version(self, version_key: str) -> Optional[str]:
        """
        Get version from VERSION.json as fallback.

        Args:
            version_key: Key in VERSION.json to read

        Returns:
            Version string or None
        """
        try:
            with open(self.version_file, "r") as f:
                data = json.load(f)
                return data.get(version_key)
        except Exception as e:
            print(f"Warning: Could not read fallback version: {e}")
            return None

    def _is_prerelease(self, version: str) -> bool:
        """Check if version is a pre-release."""
        prerelease_patterns = [
            r".*-alpha.*",
            r".*-beta.*",
            r".*-rc.*",
            r".*-dev.*",
            r".*a\d+.*",
            r".*b\d+.*",
            r".*rc\d+.*",
        ]
        return any(
            re.match(pattern, version, re.IGNORECASE) for pattern in prerelease_patterns
        )

    def _sort_versions(self, versions: List[str], reverse: bool = False) -> List[str]:
        """
        Sort versions using semantic versioning rules.

        Args:
            versions: List of version strings
            reverse: Sort in descending order

        Returns:
            Sorted list of versions
        """

        def version_key(version: str) -> Tuple:
            """Create sort key for version string."""
            try:
                # Handle pre-release versions
                base_version = version.split("-")[0]
                parts = base_version.split(".")

                # Pad to 3 parts for consistent comparison
                while len(parts) < 3:
                    parts.append("0")

                # Convert to integers for proper numeric sorting
                major, minor, patch = [int(p) for p in parts[:3]]

                # Pre-release versions sort before release versions
                is_prerelease = self._is_prerelease(version)

                return (major, minor, patch, not is_prerelease, version)
            except (ValueError, IndexError):
                # Fallback for malformed versions
                return (0, 0, 0, False, version)

        return sorted(versions, key=version_key, reverse=reverse)

    def parse_version(self, version: str) -> Tuple[int, int, int, Optional[str]]:
        """
        Parse semantic version string.

        Args:
            version: Version string (e.g., "3.1.0" or "3.1.0-beta.1")

        Returns:
            Tuple of (major, minor, patch, prerelease)

        Raises:
            ValueError: If version format is invalid
        """
        pattern = r"^(\d+)\.(\d+)\.(\d+)(?:-(.+))?$"
        match = re.match(pattern, version)

        if not match:
            raise ValueError(f"Invalid version format: '{version}'")

        major, minor, patch, prerelease = match.groups()
        return int(major), int(minor), int(patch), prerelease

    def calculate_next_version(self, current_version: str, change_type: str) -> str:
        """
        Calculate next version based on current version and change type.

        Args:
            current_version: Current version (e.g., "3.0.0")
            change_type: Type of change ("patch", "minor", "major")

        Returns:
            Next version string

        Raises:
            ValueError: If inputs are invalid
        """
        if change_type.lower() not in ["patch", "minor", "major"]:
            raise ValueError(
                f"Invalid change type: {change_type}. Must be patch, minor, or major"
            )

        major, minor, patch, prerelease = self.parse_version(current_version)

        if change_type.lower() == "patch":
            return f"{major}.{minor}.{patch + 1}"
        elif change_type.lower() == "minor":
            return f"{major}.{minor + 1}.0"
        elif change_type.lower() == "major":
            return f"{major + 1}.0.0"

    def calculate_next_versions(self, current_version: str) -> Dict[str, str]:
        """
        Calculate all possible next versions.

        Args:
            current_version: Current version

        Returns:
            Dict with patch, minor, and major next versions
        """
        if not current_version:
            # If no current version, start with 0.1.0
            return {"patch": "0.1.1", "minor": "0.2.0", "major": "1.0.0"}

        return {
            "patch": self.calculate_next_version(current_version, "patch"),
            "minor": self.calculate_next_version(current_version, "minor"),
            "major": self.calculate_next_version(current_version, "major"),
        }

    def version_exists_on_pypi(
        self, version: str, check_testpypi: bool = True
    ) -> Dict[str, bool]:
        """
        Check if version exists on PyPI platforms.

        Args:
            version: Version to check
            check_testpypi: Also check TestPyPI

        Returns:
            Dict with existence status for each platform
        """
        result = {"pypi": False, "testpypi": False}

        # Check production PyPI
        try:
            pypi_data = self.get_pypi_versions(include_prereleases=True)
            result["pypi"] = version in pypi_data.get("releases", [])
        except Exception as e:
            print(f"Warning: Could not check PyPI for version {version}: {e}")

        # Check TestPyPI
        if check_testpypi:
            try:
                testpypi_data = self.get_testpypi_versions(include_prereleases=True)
                result["testpypi"] = version in testpypi_data.get("releases", [])
            except Exception as e:
                print(f"Warning: Could not check TestPyPI for version {version}: {e}")

        return result

    def sync_version_json_with_pypi(self, dry_run: bool = False) -> Dict[str, str]:
        """
        Synchronize VERSION.json with actual PyPI state.

        Args:
            dry_run: If True, show what would be updated without changing files

        Returns:
            Dict showing what was/would be updated
        """
        try:
            # Get current PyPI versions
            current_production = self.get_current_production_version()
            current_testpypi = self.get_current_testpypi_version()

            # Load current VERSION.json
            with open(self.version_file, "r") as f:
                version_data = json.load(f)

            updates = {}

            # Update production version if different
            if (
                current_production
                and version_data.get("current_release") != current_production
            ):
                updates["current_release"] = {
                    "old": version_data.get("current_release"),
                    "new": current_production,
                }
                if not dry_run:
                    version_data["current_release"] = current_production

            # Update TestPyPI version if different
            if (
                current_testpypi
                and version_data.get("current_testpypi") != current_testpypi
            ):
                updates["current_testpypi"] = {
                    "old": version_data.get("current_testpypi"),
                    "new": current_testpypi,
                }
                if not dry_run:
                    version_data["current_testpypi"] = current_testpypi

            # Update next allowed versions based on production version
            if current_production:
                next_versions = self.calculate_next_versions(current_production)
                if version_data.get("next_allowed") != next_versions:
                    updates["next_allowed"] = {
                        "old": version_data.get("next_allowed"),
                        "new": next_versions,
                    }
                    if not dry_run:
                        version_data["next_allowed"] = next_versions

            # Save if not dry run and updates were made
            if not dry_run and updates:
                version_data["metadata"]["last_updated"] = (
                    datetime.utcnow().isoformat() + "Z"
                )
                version_data["metadata"]["sync_source"] = "PyPI API"

                with open(self.version_file, "w") as f:
                    json.dump(version_data, f, indent=2)

            return updates

        except Exception as e:
            raise PyPIError(f"Failed to sync VERSION.json: {e}")

    def get_version_status_report(self) -> Dict:
        """
        Generate comprehensive version status report.

        Returns:
            Dict with current status across all platforms
        """
        try:
            # Get PyPI versions
            current_production = self.get_current_production_version()
            current_testpypi = self.get_current_testpypi_version()

            # Get VERSION.json data
            version_json_data = {}
            try:
                with open(self.version_file, "r") as f:
                    version_json_data = json.load(f)
            except Exception as e:
                print(f"Warning: Could not read VERSION.json: {e}")

            # Check synchronization status
            sync_status = {
                "production_synced": current_production
                == version_json_data.get("current_release"),
                "testpypi_synced": current_testpypi
                == version_json_data.get("current_testpypi"),
                "needs_sync": False,
            }
            sync_status["needs_sync"] = not (
                sync_status["production_synced"] and sync_status["testpypi_synced"]
            )

            # Get next versions
            next_versions = (
                self.calculate_next_versions(current_production)
                if current_production
                else {}
            )

            return {
                "current_versions": {
                    "production_pypi": current_production,
                    "test_pypi": current_testpypi,
                    "version_json_production": version_json_data.get("current_release"),
                    "version_json_testpypi": version_json_data.get("current_testpypi"),
                },
                "sync_status": sync_status,
                "next_versions": next_versions,
                "recommendations": self._get_recommendations(
                    sync_status, current_production, version_json_data
                ),
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }

        except Exception as e:
            return {"error": str(e), "timestamp": datetime.utcnow().isoformat() + "Z"}

    def _get_recommendations(
        self, sync_status: Dict, current_production: str, version_json_data: Dict
    ) -> List[str]:
        """Generate recommendations based on current status."""
        recommendations = []

        if sync_status["needs_sync"]:
            recommendations.append(
                "Run 'python pypi_manager.py --sync' to synchronize VERSION.json with PyPI"
            )

        if not current_production:
            recommendations.append(
                "No production version found on PyPI - consider initial release"
            )

        if version_json_data.get("current_release") and current_production:
            if version_json_data["current_release"] != current_production:
                recommendations.append(
                    f"VERSION.json shows {version_json_data['current_release']} but PyPI has {current_production}"
                )

        if not recommendations:
            recommendations.append(
                "All versions are synchronized - ready for next release"
            )

        return recommendations


def main():
    """Provide CLI interface for PyPI management."""
    import argparse

    parser = argparse.ArgumentParser(description="ADRI PyPI Version Manager")
    parser.add_argument(
        "--package", default="adri", help="Package name (default: adri)"
    )
    parser.add_argument("--current", action="store_true", help="Show current versions")
    parser.add_argument(
        "--status", action="store_true", help="Show detailed status report"
    )
    parser.add_argument(
        "--sync", action="store_true", help="Sync VERSION.json with PyPI"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be synced without making changes",
    )
    parser.add_argument("--next", help="Calculate next version (patch/minor/major)")
    parser.add_argument(
        "--check-version", help="Check if specific version exists on PyPI"
    )

    args = parser.parse_args()

    try:
        manager = PyPIManager(package_name=args.package)

        if args.current:
            print("📦 Current Versions:")
            print(f"Production PyPI: {manager.get_current_production_version()}")
            print(f"TestPyPI: {manager.get_current_testpypi_version()}")

        elif args.status:
            print("📊 Version Status Report:")
            status = manager.get_version_status_report()
            print(json.dumps(status, indent=2))

        elif args.sync:
            print("🔄 Synchronizing VERSION.json with PyPI...")
            updates = manager.sync_version_json_with_pypi(dry_run=args.dry_run)
            if updates:
                action = "Would update" if args.dry_run else "Updated"
                print(f"✅ {action} {len(updates)} fields:")
                for field, change in updates.items():
                    print(f"  • {field}: {change['old']} → {change['new']}")
            else:
                print("✅ No updates needed - already synchronized")

        elif args.next:
            current = manager.get_current_production_version()
            if current:
                next_version = manager.calculate_next_version(current, args.next)
                print(f"📈 Next {args.next} version: {current} → {next_version}")
            else:
                print("❌ No current production version found")

        elif args.check_version:
            exists = manager.version_exists_on_pypi(args.check_version)
            print(f"🔍 Version {args.check_version} exists:")
            print(f"  PyPI: {'✅' if exists['pypi'] else '❌'}")
            print(f"  TestPyPI: {'✅' if exists['testpypi'] else '❌'}")

        else:
            # Default: show status
            status = manager.get_version_status_report()
            print("📊 ADRI Version Status:")
            print(f"Production PyPI: {status['current_versions']['production_pypi']}")
            print(f"TestPyPI: {status['current_versions']['test_pypi']}")
            print(
                f"Sync Status: {'✅ Synchronized' if not status['sync_status']['needs_sync'] else '⚠️ Needs Sync'}"
            )

            if status["sync_status"]["needs_sync"]:
                print("\n💡 Recommendations:")
                for rec in status["recommendations"]:
                    print(f"  • {rec}")

    except PyPIError as e:
        print(f"❌ PyPI Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
