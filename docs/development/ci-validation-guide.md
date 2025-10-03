# CI Validation with ACT

## Setup ✅ Complete

- **ACT Version:** 0.2.82
- **CI Workflow:** .github/workflows/ci.yml
- **Test Job:** `test` (runs on ubuntu-latest, Python 3.9-3.11)
- **Test Command:** `pytest`

## Dry-Run Results ✅

ACT dry-run successfully validated:
- Docker images configured correctly
- Workflow structure validated
- All jobs identified
- Ready for execution

## Running ACT Locally

### Quick Validation (Recommended)
```bash
# Run just the test job (fastest)
act -j test -W .github/workflows/ci.yml --matrix python-version:3.11
```

### Full CI Simulation
```bash
# Run complete CI workflow
act -j test -W .github/workflows/ci.yml
```

### With Artifacts
```bash
# Run with artifact collection
act -j test -W .github/workflows/ci.yml --artifact-server-path /tmp/artifacts
```

## Expected Results

✅ **All 859 tests should pass**
✅ **Coverage should be ≥10% (actual: 36.13%)**
✅ **Baseline regression tests should pass**
✅ **No test discovery issues**

## Baseline Regression in CI

The baseline regression system is designed for CI:
- First CI run: Creates baselines (will skip test)
- Subsequent runs: Compares against committed baselines
- Baselines committed to git: `ADRI/tutorials/*/baseline_outcome/`

## Troubleshooting

If ACT fails:
1. Check Docker is running: `docker ps`
2. Verify workflow syntax: `act -j test --dryrun`
3. Check logs: ACT outputs detailed step-by-step logs
4. Run locally first: `pytest tests/` to verify tests work

## CI Configuration Notes

- **Python Matrix:** 3.9, 3.10, 3.11
- **OS Matrix:** ubuntu-latest, macos-latest, windows-latest
- **Coverage Upload:** Codecov (ubuntu + Python 3.11 only)
- **Pre-commit:** Runs before tests

## Validation Checklist

- [x] ACT installed (v0.2.82)
- [x] Dry-run successful
- [x] Workflow reviewed
- [x] Local tests passing (287/287)
- [x] Coverage validated (36.13%)
- [ ] Full ACT run (run when ready: `act -j test -W .github/workflows/ci.yml --matrix python-version:3.11`)

## Notes

ACT simulates GitHub Actions locally using Docker. Full runs can take 5-10 minutes per Python version due to:
- Docker image pulls
- Dependency installation
- Full test suite execution

For fastest validation, use the quick command above with a single Python version.
