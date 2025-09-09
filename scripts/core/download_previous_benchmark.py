#!/usr/bin/env python3
"""Download previous benchmark artifacts from GitHub Actions."""

import json
import os
import sys
import zipfile
from io import BytesIO
from pathlib import Path
from typing import Optional

import requests


class BenchmarkArtifactDownloader:
    """Download and manage benchmark artifacts from GitHub Actions."""

    def __init__(self, repo_owner: str, repo_name: str, token: Optional[str] = None):
        """Initialize the downloader with repository information."""
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.token = token or os.environ.get("GITHUB_TOKEN")
        self.api_base = f"https://api.github.com/repos/{repo_owner}/{repo_name}"
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
        }
        if self.token:
            self.headers["Authorization"] = f"token {self.token}"

    def get_workflow_runs(
        self,
        workflow_name: str,
        branch: str = "main",
        status: str = "success",
        limit: int = 10,
    ) -> list:
        """Get recent workflow runs for the specified workflow."""
        url = f"{self.api_base}/actions/workflows/{workflow_name}/runs"
        params = {"branch": branch, "status": status, "per_page": limit}

        response = requests.get(url, headers=self.headers, params=params)
        if response.status_code != 200:
            print(f"Error fetching workflow runs: {response.status_code}")
            print(response.text)
            return []

        data = response.json()
        return data.get("workflow_runs", [])

    def get_run_artifacts(self, run_id: int) -> list:
        """Get artifacts for a specific workflow run."""
        url = f"{self.api_base}/actions/runs/{run_id}/artifacts"

        response = requests.get(url, headers=self.headers)
        if response.status_code != 200:
            print(f"Error fetching artifacts: {response.status_code}")
            return []

        data = response.json()
        return data.get("artifacts", [])

    def download_artifact(self, artifact_id: int, output_path: str) -> bool:
        """Download a specific artifact."""
        url = f"{self.api_base}/actions/artifacts/{artifact_id}/zip"

        response = requests.get(url, headers=self.headers, allow_redirects=True)
        if response.status_code != 200:
            print(f"Error downloading artifact: {response.status_code}")
            return False

        # Extract the zip content
        try:
            with zipfile.ZipFile(BytesIO(response.content)) as zip_file:
                # List files in the archive
                file_list = zip_file.namelist()

                # Look for benchmark result files
                for file_name in file_list:
                    if file_name.endswith(".json"):
                        # Extract the JSON file
                        content = zip_file.read(file_name)
                        with open(output_path, "wb") as f:
                            f.write(content)
                        return True

            print("No JSON file found in artifact")
            return False

        except zipfile.BadZipFile:
            print("Downloaded artifact is not a valid zip file")
            return False

    def find_previous_benchmark(
        self,
        workflow_name: str,
        branch: str = "main",
        artifact_name: str = "benchmark-results",
    ) -> Optional[str]:
        """Find and download the most recent benchmark artifact."""
        print(f"Looking for previous benchmarks on branch '{branch}'...")

        # Get recent successful workflow runs
        runs = self.get_workflow_runs(workflow_name, branch)
        if not runs:
            print("No successful workflow runs found")
            return None

        # Search for benchmark artifacts in recent runs
        for run in runs:
            run_id = run["id"]
            commit_sha = run["head_sha"][:8]
            print(f"Checking run {run_id} (commit {commit_sha})...")

            artifacts = self.get_run_artifacts(run_id)
            for artifact in artifacts:
                if artifact["name"] == artifact_name:
                    print(f"Found benchmark artifact from commit {commit_sha}")

                    # Download the artifact
                    output_path = f"previous-benchmark-{commit_sha}.json"
                    if self.download_artifact(artifact["id"], output_path):
                        print(f"Downloaded to {output_path}")
                        return output_path
                    break

        print("No benchmark artifacts found in recent runs")
        return None

    def get_base_branch_benchmark(
        self,
        base_branch: str = "main",
        workflow_name: str = "test.yml",
        artifact_name: str = "benchmark-results",
    ) -> Optional[str]:
        """Download benchmark from base branch for PR comparison."""
        print(f"Fetching benchmark from base branch '{base_branch}'...")
        return self.find_previous_benchmark(workflow_name, base_branch, artifact_name)

    def cache_benchmark(self, file_path: str, cache_dir: str = ".benchmark-cache"):
        """Cache benchmark results locally for development."""
        cache_path = Path(cache_dir)
        cache_path.mkdir(exist_ok=True)

        # Read the benchmark data
        with open(file_path, "r") as f:
            data = json.load(f)

        # Extract metadata if available
        commit_sha = data.get("commit_sha", "unknown")
        timestamp = data.get("timestamp", "unknown")

        # Save to cache with metadata in filename
        cache_file = cache_path / f"benchmark-{commit_sha}-{timestamp}.json"
        with open(cache_file, "w") as f:
            json.dump(data, f, indent=2)

        print(f"Cached benchmark to {cache_file}")
        return str(cache_file)

    def get_cached_benchmark(
        self, cache_dir: str = ".benchmark-cache"
    ) -> Optional[str]:
        """Get the most recent cached benchmark."""
        cache_path = Path(cache_dir)
        if not cache_path.exists():
            return None

        # Find all cached benchmarks
        cache_files = list(cache_path.glob("benchmark-*.json"))
        if not cache_files:
            return None

        # Return the most recent one
        latest = max(cache_files, key=lambda p: p.stat().st_mtime)
        print(f"Using cached benchmark: {latest}")
        return str(latest)


def main():
    """Main function for CLI usage."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Download previous benchmark artifacts"
    )
    parser.add_argument(
        "--repo", required=True, help="Repository in format 'owner/name'"
    )
    parser.add_argument("--branch", default="main", help="Branch to fetch from")
    parser.add_argument("--workflow", default="test.yml", help="Workflow file name")
    parser.add_argument("--artifact", default="benchmark-results", help="Artifact name")
    parser.add_argument("--output", help="Output file path")
    parser.add_argument("--token", help="GitHub token (or set GITHUB_TOKEN env var)")
    parser.add_argument(
        "--cache", action="store_true", help="Cache the downloaded benchmark"
    )
    parser.add_argument(
        "--use-cache", action="store_true", help="Use cached benchmark if available"
    )

    args = parser.parse_args()

    # Parse repository
    parts = args.repo.split("/")
    if len(parts) != 2:
        print(f"Invalid repository format: {args.repo}")
        print("Expected format: owner/name")
        sys.exit(1)

    repo_owner, repo_name = parts

    # Initialize downloader
    downloader = BenchmarkArtifactDownloader(repo_owner, repo_name, args.token)

    # Check for cached benchmark first if requested
    if args.use_cache:
        cached = downloader.get_cached_benchmark()
        if cached:
            if args.output and cached != args.output:
                import shutil

                shutil.copy(cached, args.output)
                print(f"Copied cached benchmark to {args.output}")
            sys.exit(0)

    # Download the benchmark
    result = downloader.find_previous_benchmark(
        args.workflow, args.branch, args.artifact
    )

    if result:
        # Cache if requested
        if args.cache:
            downloader.cache_benchmark(result)

        # Move to desired output location if specified
        if args.output and result != args.output:
            import shutil

            shutil.move(result, args.output)
            print(f"Moved to {args.output}")
            result = args.output

        print(f"Successfully downloaded benchmark to {result}")
        sys.exit(0)
    else:
        print("Failed to download previous benchmark")
        sys.exit(1)


if __name__ == "__main__":
    main()
