# Release Process for ADRI

This document outlines the step-by-step process for creating and publishing new releases of the Agent Data Readiness Index (ADRI) package. Following this process ensures consistent versioning, proper documentation, and smooth publication.

**Important**: For security guidelines related to PyPI tokens and credentials, refer to [SECURITY.md](docs/SECURITY.md).

## 1. Determine the Version Number

The ADRI project follows [Semantic Versioning](https://semver.org/). Determine the appropriate version increment based on the nature of your changes:

- **MAJOR version (x.0.0)**: Incompatible API changes or scoring methodology changes
- **MINOR version (0.x.0)**: Backwards-compatible feature additions or enhancements
- **PATCH version (0.0.x)**: Backwards-compatible bug fixes

Refer to `VERSIONS.md` for detailed versioning policies, especially around scoring methodology changes.

## 2. Update Version Information

Update the version in all necessary files:

```bash
# Version must be updated in these files (ensure they all match):
1. adri/version.py  (__version__ variable)
2. pyproject.toml   (version field)
```

If this is a MAJOR version upgrade, also update:
- `__min_compatible_version__` in `adri/version.py`
- `__score_compatible_versions__` in `adri/version.py`

## 3. Update Documentation

### Update CHANGELOG.md

1. Move any entries from the "Unreleased" section to a new section for the new version
2. Add the release date
3. Ensure all significant changes are documented under appropriate categories (Added, Changed, Fixed, etc.)

Example:
```markdown
## [0.2.0] - 2025-04-30

### Added
- New file connector for CSV, Excel, and Parquet files
- Support for API rate limiting

### Fixed
- Inconsistent score calculation in validity dimension
```

### Update VERSIONS.md

If this is a MAJOR or MINOR version that affects compatibility:

1. Update the version compatibility matrix
2. Add a new detailed section for the version
3. Document any changes to scoring methodology

## 4. Create a Pull Request

1. Create a branch named `release/vX.Y.Z`
2. Commit all the above changes
3. Push the branch and create a pull request
4. Ensure all CI tests pass
5. Get approvals from at least two maintainers

## 5. Merge and Tag

After the PR is approved:

1. Merge the PR to main
2. Create and push a tag:
```bash
git checkout main
git pull
git tag -a vX.Y.Z -m "Release vX.Y.Z"
git push origin vX.Y.Z
```

## 6. Create a GitHub Release

1. Go to the "Releases" page in the GitHub repository
2. Click "Draft a new release"
3. Select the tag you just created
4. Use "vX.Y.Z" as the release title
5. Copy the relevant section from CHANGELOG.md into the description
6. Publish the release

This will automatically trigger the GitHub Actions workflow in `.github/workflows/publish.yml` to build and publish the package to PyPI.

## 7. Verify the Release

After the GitHub Actions workflow completes:

1. Check that the package is available on PyPI: https://pypi.org/project/adri/
2. Install the new version locally and verify basic functionality:
```bash
pip install -U adri
python -c "import adri; print(adri.__version__)"
```

## 8. Announce the Release

Announce the new version on appropriate channels (mailing lists, chat, social media, etc.) highlighting key features and improvements.

## Manual Publishing (if needed)

If the GitHub Actions workflow fails, you can publish manually using the `scripts/publish_pypi.sh` script:

```bash
# Publish to TestPyPI first
./scripts/publish_pypi.sh --test

# If that works, publish to PyPI
./scripts/publish_pypi.sh
```

## Hotfix Process

For urgent fixes that can't wait for the next regular release:

1. Create a `hotfix/vX.Y.Z` branch from the latest tag
2. Make the necessary changes
3. Update version numbers and documentation
4. Follow steps 4-8 above

## Version Check Script

You can verify that all version references are consistent with:

```bash
python -c "from adri.version import __version__; import re; \
pyproject = re.search(r'version = \"([^\"]+)\"', open('pyproject.toml').read()).group(1); \
print(f'version.py: {__version__}, pyproject.toml: {pyproject}'); \
assert __version__ == pyproject, 'Version mismatch!'"

<!-- ---------------------------------------------
TEST COVERAGE
----------------------------------------------
This document's processes are tested through:

1. Infrastructure tests:
   - tests/infrastructure/test_version_infrastructure.py (release documentation structure)
   - tests/infrastructure/test_version_infrastructure.py (version file consistency)

2. Integration tests:
   - tests/integration/test_publishing.py (TestPyPI publishing workflow)

3. CI/CD validation:
   - .github/workflows/publish.yml (automated release process)
   - .github/workflows/test-publishing.yml (test publishing process)

4. Scripts tested:
   - scripts/publish_pypi.sh (manual publishing script)
   - scripts/verify_version.py (version verification)

Complete test coverage details are documented in:
docs/test_coverage/RELEASE_PROCESS_test_coverage.md
--------------------------------------------- -->
