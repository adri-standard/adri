# Implementation Plan

[Overview]
Complete setuptools_scm integration and open source launch preparation for ADRI, including legacy file archival, automatic version management, GitHub Actions CI/CD pipeline, and PyPI publishing workflow.

This implementation transforms ADRI from an internal project with manual versioning to a professional open source package with automated version management, clean repository structure, and production-ready release pipeline. The plan addresses archiving legacy development files, implementing setuptools_scm for Git-based versioning, establishing GitHub Actions workflows for testing and publishing, and preparing the project for public release starting with version 4.0.0.

The implementation prioritizes clean separation between development artifacts and production code, ensures proper semantic versioning through Git tags, and establishes a robust CI/CD pipeline that publishes to PyPI Test for validation before promoting to PyPI Live with manual approval.

[Types]
Configuration structures and workflow definitions for the setuptools_scm integration and CI/CD pipeline.

Key configuration types include:
- **VersionConfig**: setuptools_scm configuration with version scheme, local scheme, and write target
- **WorkflowConfig**: GitHub Actions workflow configurations for CI, testing, and publishing
- **ArchiveStructure**: Organized directory structure for legacy files and development artifacts
- **ReleaseConfig**: PyPI publishing configuration with test and production environments
- **BranchProtection**: GitHub branch protection rules and PR requirements

setuptools_scm version configuration:
```toml
[tool.setuptools_scm]
version_scheme = "post-release"
local_scheme = "node-and-date"
write_to = "src/adri/_version.py"
fallback_version = "4.0.0"
```

GitHub Actions workflow types:
- **CIWorkflow**: Pull request testing and validation
- **ReleaseWorkflow**: Tag-based release with PyPI publishing
- **TestWorkflow**: Automated testing across Python versions

[Files]
Archive reorganization, configuration updates, and new workflow files for the complete setuptools_scm and open source setup.

**Files to Archive:**
- `archive/internal-docs/`: Move IMPLEMENTATION_CHECKLIST.md, DEMO_LAUNCH_SUMMARY.md, DEPLOYMENT_GUIDE.md, coverage_improvement_plan.md, bandit_security_resolution_plan.md, folder_restructure_plan.md
- `archive/legacy-builds/`: Move dist/, adri.egg-info/, coverage.json
- `archive/development-artifacts/`: Move test_logs/, logs/, htmlcov/, backup/, development/, MagicMock/, .benchmarks/
- `archive/temp-files/`: Move nonexistent_standard.yaml, subdir/, adri_test_env/
- `archive/cache/`: Move .pytest_cache/, .mypy_cache/

**Configuration Files to Modify:**
- `pyproject.toml`: Remove hardcoded version, add setuptools_scm configuration, add build dependencies
- `src/adri/__init__.py`: Import version from setuptools_scm generated file
- `src/adri/version.py`: Simplify to use setuptools_scm, remove complex fallback logic

**New Files to Create:**
- `.github/workflows/ci.yml`: Continuous integration workflow for pull requests
- `.github/workflows/release.yml`: Release workflow for tag-based publishing
- `.github/workflows/test.yml`: Testing workflow across Python versions
- `.github/PULL_REQUEST_TEMPLATE.md`: PR template for open source contributions
- `.github/ISSUE_TEMPLATE/bug_report.md`: Bug report template
- `.github/ISSUE_TEMPLATE/feature_request.md`: Feature request template
- `archive/README.md`: Documentation for archived files

**Files to Keep (Open Source Ready):**
- Core documentation: README.md, ARCHITECTURE.md, CHANGELOG.md, CONTRIBUTING.md, LICENSE, SECURITY.md
- User guides: QUICK_START.md, examples/, docs/, demos/
- Source code: src/, tests/, pyproject.toml
- Development tools: .pre-commit-config.yaml, .commitlintrc.json, .flake8, .gitignore

[Functions]
Version management functions and CI/CD pipeline functions for the setuptools_scm integration.

**Version Management Functions:**
- `get_version()`: Replaced by setuptools_scm automatic detection from git tags
- `_get_version_from_metadata()`: Simplified to use setuptools_scm generated version
- `is_version_compatible()`: Updated to work with setuptools_scm versioning scheme
- `get_version_info()`: Modified to use setuptools_scm version information

**Archive Management Functions:**
- `create_archive_structure()`: Create organized archive directory structure
- `move_legacy_files()`: Move identified legacy files to appropriate archive locations
- `update_gitignore()`: Add archive/ directory and remove obsolete ignore patterns
- `cleanup_build_artifacts()`: Remove generated build files that will be recreated

**CI/CD Pipeline Functions:**
- `validate_version_tag()`: Validate git tag format for releases (v4.0.0 format)
- `build_and_test()`: Execute test suite and build package
- `publish_to_test_pypi()`: Publish to PyPI Test environment
- `publish_to_live_pypi()`: Publish to PyPI Live with manual approval
- `update_changelog()`: Automatic changelog generation from git commits

[Classes]
Configuration and workflow management classes for the setuptools_scm and open source infrastructure.

**VersionManager**: 
- Location: `src/adri/version.py`
- Purpose: Simplified version management using setuptools_scm
- Key methods: `get_version()`, `get_build_info()`, `is_compatible()`
- Inheritance: Replaces complex fallback logic with setuptools_scm integration

**ArchiveManager**:
- Location: New utility class for archival process
- Purpose: Organize and move legacy files to archive structure
- Key methods: `create_structure()`, `move_files()`, `validate_archive()`
- Dependencies: pathlib, shutil for file operations

**ReleaseWorkflow**:
- Location: GitHub Actions workflow configuration
- Purpose: Automated release pipeline from git tags to PyPI
- Key stages: build, test, publish-test, manual-approval, publish-live
- Integration: setuptools_scm for version detection, PyPI trusted publishing

**CIWorkflow**:
- Location: GitHub Actions CI configuration  
- Purpose: Pull request validation and testing
- Key stages: lint, test-matrix, coverage, security-scan
- Matrix: Python 3.10, 3.11, 3.12 across ubuntu-latest, windows-latest, macos-latest

[Dependencies]
Build system and CI/CD dependencies for setuptools_scm integration and workflow automation.

**Build Dependencies (pyproject.toml):**
```toml
[build-system]
requires = ["setuptools>=61.0", "setuptools_scm[toml]>=6.2", "wheel"]
build-backend = "setuptools.build_meta"
```

**New Development Dependencies:**
- `setuptools_scm[toml]>=6.2`: Automatic version management from git tags
- `build>=0.8.0`: Modern Python package building
- `twine>=4.0.0`: Secure PyPI publishing

**GitHub Actions Dependencies:**
- `actions/checkout@v4`: Repository checkout
- `actions/setup-python@v4`: Python environment setup
- `pypa/gh-action-pypi-publish@release/v1`: Trusted PyPI publishing
- `actions/upload-artifact@v3`: Build artifact management

**Removed Dependencies:**
- Manual version management code in `src/adri/version.py`
- Complex TOML parsing libraries (tomllib/tomli) no longer needed for version detection
- Custom version fallback mechanisms

[Testing]
Testing strategy for setuptools_scm integration and validation of the new workflow.

**Version Testing:**
- Test automatic version detection from git tags
- Validate development version formatting (4.0.1.dev23+g1234567)
- Test version compatibility checking with new scheme
- Verify fallback version behavior when no git tags exist

**Archive Testing:**
- Validate archive structure creation
- Test file movement without data loss
- Verify gitignore updates exclude archive directory
- Confirm no required files moved to archive

**CI/CD Testing:**
- Test GitHub Actions workflow on feature branches
- Validate PyPI Test publishing with test version tags
- Test manual approval process for PyPI Live publishing
- Verify build artifacts and documentation generation

**Integration Testing:**
- Test package installation from PyPI Test
- Validate CLI functionality with setuptools_scm versions
- Test import behavior with generated version file
- Verify version reporting in package metadata

**Test Files to Update:**
- `tests/test_version.py`: Update for setuptools_scm integration
- `tests/test_package_info.py`: Validate package metadata with automatic versioning
- Add `tests/test_archive.py`: Test archive structure and file organization
- Add `tests/test_workflows.py`: Validate GitHub Actions workflow configurations

[Implementation Order]
Systematic implementation sequence to minimize disruption and ensure successful setuptools_scm integration and open source launch.

**PHASE 1: LOCAL PREPARATION (Current Repository)**
*All work done in your existing local repository first*

1. **Update .gitignore for Archive Protection**
   - Add `archive/` directory to .gitignore
   - Add `src/adri/_version.py` (setuptools_scm generated file) to .gitignore
   - Commit updated .gitignore before archiving files
   - **USER ACTION REQUIRED**: Review and approve .gitignore changes

2. **Archive Legacy Files**
   - Create archive directory structure
   - Move development artifacts and internal documentation
   - Validate no essential files archived
   - Test that archive/ is properly ignored by git

2. **Configure setuptools_scm**
   - Update pyproject.toml with setuptools_scm configuration
   - Add setuptools_scm to build dependencies
   - Remove hardcoded version from pyproject.toml
   - Configure version file generation to src/adri/_version.py

3. **Simplify Version Management**
   - Replace complex version.py logic with setuptools_scm integration
   - Update src/adri/__init__.py to import from generated version file
   - Test version detection from git environment
   - Add fallback version for development environments

4. **Create Initial Git Tag**
   - Tag current commit as v4.0.0 to establish version baseline
   - Test setuptools_scm version detection from tag
   - Verify package build with correct version
   - Validate version appears correctly in built artifacts

5. **Set Up GitHub Actions Workflows**
   - Create CI workflow for pull request testing
   - Create release workflow for tag-based publishing
   - Configure PyPI Test and Live publishing
   - Set up manual approval for production releases

6. **Create Open Source Governance Files**
   - Add PR and issue templates for community contributions
   - Update CONTRIBUTING.md with new release process
   - Create branch protection rules documentation
   - Add security policy and code of conduct

7. **Test Local Build Process**
   - Test package building with python -m build
   - Validate generated version in built packages
   - Test installation from local wheels
   - Verify CLI functionality with new versioning

8. **Test CI/CD Pipeline**
   - Create test branch and pull request to validate CI
   - Create test tag to validate release workflow
   - Test publishing to PyPI Test environment
   - Validate manual approval process for PyPI Live

9. **Update Documentation**
   - Update README.md with new installation instructions
   - Update ARCHITECTURE.md with setuptools_scm integration
   - Add release process documentation
   - Update CHANGELOG.md with v4.0.0 release notes

10. **Prepare Repository for Public Release**
    - Review all files for sensitive information
    - Validate open source license compliance
    - Test complete workflow from tag to PyPI Live
    - Prepare initial v4.0.0 release announcement
    - **USER ACTION REQUIRED**: Review and approve final state for public release

**PHASE 2: PUBLIC REPOSITORY CREATION**
*User-driven repository management and initial release*

11. **Create Fresh Public Repository**
    - **USER ACTION REQUIRED**: Delete existing https://github.com/adri-standard/adri repository
    - **USER ACTION REQUIRED**: Create new clean public repository with same name
    - **USER ACTION REQUIRED**: Configure branch protection rules (protect main branch, require PR reviews)
    - **USER ACTION REQUIRED**: Set up PyPI trusted publishing configuration in repository secrets
    - **TECHNICAL QUESTION**: Do you want to enable GitHub Pages for documentation?

12. **Push Clean Codebase to New Repository**
    - Add new repository as remote origin
    - Push all prepared code (archive/ will be automatically excluded by .gitignore)
    - Push v4.0.0 tag to trigger initial release workflow
    - **USER ACTION REQUIRED**: Monitor first GitHub Actions run for any configuration issues

13. **Validate Public CI/CD Pipeline**
    - Monitor CI workflow execution in public repository
    - Test PyPI Test publishing from new repository
    - **USER ACTION REQUIRED**: Manually approve PyPI Live publishing after validation
    - Verify all GitHub Actions complete successfully

**PHASE 3: PRODUCTION RELEASE**
*Official v4.0.0 launch and post-release activities*

14. **Publish Official v4.0.0 Release**
    - Verify package availability on PyPI Live
    - Test installation from PyPI in clean environment
    - Create GitHub release with release notes
    - **USER ACTION REQUIRED**: Announce release on relevant channels

15. **Post-Release Validation**
    - Validate all documentation links and examples work with public package
    - Monitor for any community feedback or issues
    - Set up issue templates and community guidelines
    - **ONGOING QUESTION**: How do you want to handle community support and contributions?

16. **Establish Ongoing Workflow**
    - Document release process for future versions
    - Set up monitoring for CI/CD pipeline health
    - Create contributor onboarding documentation
    - Plan next release cycle and features

17. **Clean Up and Celebrate**
    - Remove temporary archive files not needed for open source
    - Update local development setup documentation
    - Archive this implementation plan
    - **Celebrate successful open source launch!** 🚀

**KEY USER DECISIONS NEEDED DURING IMPLEMENTATION:**
- Step 1: Approve .gitignore changes
- Step 10: Final review before public release  
- Step 11: Repository creation and GitHub settings
- Step 12: Monitor first GitHub Actions runs
- Step 13: Manual approval for PyPI Live publishing
- Step 14: Release announcement strategy
- Step 15: Community support approach
