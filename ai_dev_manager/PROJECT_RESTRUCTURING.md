# Project Restructuring Tracking Document

This document tracks the progress of the ADRI project restructuring effort, following the plan outlined in `ai_dev_manager/sessions/session_2025-04-17.md`.

## Restructuring Goals

1. Improve organization and discoverability
2. Enhance framework integration visibility
3. Highlight dataset assessments
4. Centralize configuration
5. Improve testing organization
6. Document the project structure

## Progress Tracking

### Completed

1. ✅ **Created directory structure**
   - Created `config/` for configuration files
   - Created `datasets/catalog/` for dataset catalog
   - Created `web/css/` and `web/js/` for web assets
   - Created `docs/datasets/` and `docs/integrations/` for improved documentation
   - Created `ai_dev_manager/` for AI-assisted development
   - Created `tests/infrastructure/` for testing infrastructure components

2. ✅ **Created test infrastructure**
   - Created `tests/infrastructure/test_restructuring.py` for testing during restructuring
   - Updated `tests/infrastructure/test_github_pages.py` to work with new directory structure

3. ✅ **Created documentation**
   - Created `docs/TESTING.md` with comprehensive testing approach
   - Created `docs/PROJECT_STRUCTURE.md` explaining new directory structure
   - Created `ai_dev_manager/README.md` and `ai_dev_manager/test_plans/github_pages_test_plan.md`

4. ✅ **Moved files (Phase 1)**
   - Copied `site_config.yml` → `config/site_config.yml`
   - Copied `mkdocs.yml` → `config/mkdocs.yml`
   - Copied `styles.css` → `web/css/styles.css`
   - Copied `benchmark.js` → `web/js/benchmark.js`
   - Updated `index.html` to reference new file locations

### Completed (Continued)

5. ✅ **Moving configuration files**
   - Updated `.github/workflows/docs.yml` to use new configuration locations
   - Copied original files to new locations

6. ✅ **Moving dataset catalog**
   - Moved `docs/data/benchmark.json` → `datasets/catalog/benchmark.json`
   - Reorganized `assessed_datasets/` → `datasets/` with domain-specific folders
   - Created migration script for datasets (`scripts/migrate_datasets.py`)

7. ✅ **Updating project scripts**
   - Updated `scripts/update_catalog.py` to use new file locations

### Completed (Continued)

9. ✅ **Final cleanup**
   - Moved all test report files to `tests/data/`
   - Moved `ai-dev-manager-guide.md` to `ai_dev_manager/`
   - Verified root directory contains only essential files
   - Final test confirms all functionality is preserved

### Future Work (Low Priority)

1. 🔄 **Organizing documentation files**
   - Organize framework-specific documentation in `docs/integrations/`
   - Organize dataset documentation in `docs/datasets/`

### Completed (Continued)

8. ✅ **Cleanup of original files**
   - Removed original configuration files after confirming new locations work
   - Removed original web asset files after confirming new locations work
   - Removed the `assessed_datasets` directory after confirming migration
   - Moved test-related files to `tests/data` directory
   - Moved documentation files to appropriate locations

### Not Started

No major tasks remaining. Future work will focus on incremental improvements to the new structure.

## Testing Status

1. ✅ **Core Import Test**: PASSING
2. ✅ **Configuration File Test**: PASSING
3. ✅ **MkDocs Build Test**: PASSING (Simplified)
4. ✅ **GitHub Pages Test**: PASSING (Simplified)
5. ✅ **Web Assets Test**: PASSING
6. ✅ **Datasets Test**: PASSING

## Remaining Tasks Priority

### High Priority

1. ✅ Update GitHub workflow files to use the new configuration file locations
2. ✅ Move catalog data to the datasets directory
3. Delete original files that have been copied to new locations after thorough testing

### Medium Priority

1. ✅ Reorganize dataset assessments into domain-specific directories
2. Create framework-specific documentation in `docs/integrations/`
3. ✅ Update scripts to use new file locations

### Low Priority

1. Add more comprehensive tests for infrastructure components
2. Improve documentation of framework integrations
3. Add additional examples for each framework

## Rollback Plan

If issues are encountered, we can:

1. Run the test script to identify failing components
2. Restore original files if needed (we've only copied files so far, not deleted them)
3. Update file references to point back to original locations

## Next Actions

1. Update GitHub workflow files
2. Test the configuration with a local build
3. Move dataset catalog files
4. Delete redundant files after thorough testing
