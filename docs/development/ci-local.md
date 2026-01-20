# Local CI Reproduction (without .actrc)

This guide explains how to reliably reproduce our GitHub CI locally using ACT without relying on a root-level .actrc. The repository root must remain clean to satisfy the validate-root-structure job.

Key changes:
- .actrc is intentionally removed and ignored by Git to keep the root clean.
- All ACT commands now pass flags explicitly from scripts.
- CI workflow fixed to emit coverage XML for Codecov and to avoid invalid matrix references in artifact names.

References:
- Example ACT config preserved at: docs/tools/actrc.example
- CI workflow: .github/workflows/ci.yml
- Local runners:
  - scripts/local-ci-test.sh (quick, mirrors essentials)
  - scripts/comprehensive-act-test.sh (full, matrix and reporting)

--------------------------------------------------------------------------------

Requirements
- Docker running and available to your user
- ACT v0.2.81+ (nektos/act)
- Python 3.11+ with pip
- Node.js and npm for docs build (optional but recommended for parity)
- Pre-commit hooks installed (pip install pre-commit) and run once: pre-commit install

Install ACT
- macOS: brew install act
- Linux: curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash

--------------------------------------------------------------------------------

ACT flags used (explicit, no .actrc)
We use a consistent set of flags to match GitHub’s environment:

--container-architecture linux/amd64
-P ubuntu-latest=ghcr.io/catthehacker/ubuntu:full-latest
--env CI=true
--env GITHUB_ACTIONS=true
--artifact-server-addr 127.0.0.1
--artifact-server-port 0

These are already wired into the scripts via the ACT_FLAGS variable. You do not need to pass them manually.

--------------------------------------------------------------------------------

Quick local CI mirror
Use this for a fast confidence run that mirrors GitHub CI essentials:

bash scripts/local-ci-test.sh

What it does:
- Runs pre-commit hooks with auto-fix detection (fail-fast for real failures)
- Executes pytest (like CI), then validates path resolution logic
- Optionally builds docs if docs/ exists
- Spot-checks ACT workflow execution using explicit flags and timeouts

Timeouts prevent local hangs. If Docker/ACT is not available, the workflow testing part is skipped while still running unit tests and docs build.

--------------------------------------------------------------------------------

Full local CI compatibility (comprehensive)
Use this for a thorough pre-PR validation including matrix and artifact checks:

bash scripts/comprehensive-act-test.sh

What it does in addition to the quick run:
- Verifies prerequisites (ACT, Docker, Python testing deps)
- Runs main CI workflows via ACT with explicit flags/env
- Performs OS/Python-version matrix runs (3.10, 3.11, 3.12)
- Validates inter-workflow dependencies if present
- Performs coverage, artifact and performance checks
- Generates a JSON and text report under tests/coverage/act-logs/

Reports:
- JSON: tests/coverage/act-logs/comprehensive-test-report.json
- Text: tests/coverage/act-logs/comprehensive-test-report.txt

--------------------------------------------------------------------------------

CI workflow fixes included
- Coverage XML for Codecov:
  The test job now ensures pytest emits an XML report to tests/coverage/coverage.xml
  via:
  mkdir -p tests/coverage
  pytest --cov=adri --cov-report=term-missing --cov-report=xml:tests/coverage/coverage.xml

- Artifact upload naming:
  The non-matrix build-test job uploads artifacts with a constant name (adri-build-3.11),
  removing invalid references to matrix contexts.

--------------------------------------------------------------------------------

Troubleshooting

1) ACT cannot pull image or no node in runner
- Ensure Docker is running and you have network access to pull catthehacker/ubuntu:act-latest
- The scripts set the image mapping with -P ubuntu-latest=ghcr.io/catthehacker/ubuntu:full-latest and bind the artifact server to a random free port to avoid conflicts
- If ACT fails on JavaScript-based actions due to node, prefer running on Ubuntu images above

2) ACT hangs or runs indefinitely
- Scripts use timeout around ACT to prevent hangs
- Kill residual Docker containers and retry:
  docker ps -a
  docker rm -f <container_id>

3) Codecov upload fails locally
- Codecov upload runs only on Ubuntu + Python 3.11 in CI
- Local runs are for coverage generation parity; upload step is handled by GitHub CI

4) Root structure validation fails
- Ensure no extra files exist at repo root
- .actrc is intentionally gitignored; if it reappears locally, it will not be committed
- Move internal planning docs to archive/ or docs/, or add to .gitignore if build artifacts

5) Permission or PATH issues
- Verify act, docker, python, node are available in PATH
- On macOS, ensure Docker Desktop is running and has sufficient resources

--------------------------------------------------------------------------------

FAQ

Q: Why is .actrc removed?
A: Our root validator enforces a clean root. A root-level .actrc is flagged as unauthorized. We preserve a sample at docs/tools/actrc.example for reference, but scripts pass flags explicitly to ACT.

Q: How do I replicate GitHub’s environment?
A: Use the provided scripts. They export CI=true and GITHUB_ACTIONS=true, force linux/amd64, and map ubuntu-latest to catthehacker/ubuntu:act-latest to match CI as closely as possible.

Q: Do I need to manually pass ACT flags?
A: No. The scripts define ACT_FLAGS and apply them on every act invocation, so runs are consistent even without .actrc.

--------------------------------------------------------------------------------

Pre-PR checklist (local)
- Run the quick mirror:
  bash scripts/local-ci-test.sh

- Run the comprehensive validation:
  bash scripts/comprehensive-act-test.sh

- Review:
  - Unit test results
  - Docs build (if applicable)
  - Comprehensive report under tests/coverage/act-logs/

If all checks pass locally, push your branch/PR; CI should pass with parity.
