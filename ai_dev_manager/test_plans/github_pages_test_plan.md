# GitHub Pages Test Plan

This document outlines the specific testing approach for GitHub Pages configuration in the ADRI project.

## Test Objectives

- Verify the GitHub Pages configuration works correctly for both private and public repository states
- Ensure all site URLs are consistent and configurable through a single source of truth
- Validate the GitHub Actions workflow for documentation deployment

## Test Scope

- Site configuration file validation
- MkDocs configuration file validation
- URL reference consistency across HTML files
- GitHub Actions workflow functionality
- URL migration process (private to public repository)

## Test Environment

- Local development environment
- GitHub Actions CI/CD pipeline
- GitHub Pages hosting environment

## Test Artifacts

- `site_config.yml`: Central URL configuration
- `mkdocs.yml`: MkDocs configuration using environment variables
- `.github/workflows/docs.yml`: GitHub Actions workflow
- `site/docs/`: Generated site files
- `index.html` and other HTML files with URLs

## Test Cases

### 1. Site Configuration Validation

**Test ID:** GHP-CONFIG-001  
**Description:** Verify the site_config.yml can be parsed and contains the correct URL  
**Steps:**
1. Run `python test_site_config.py`
2. Verify it successfully extracts the URL from the configuration file
3. Verify the URL is set as an environment variable

**Expected Result:** Script outputs the correct URL and sets it as an environment variable

### 2. MkDocs Build with Environment Variables

**Test ID:** GHP-BUILD-001  
**Description:** Verify MkDocs can build the site using the environment variable for site URL  
**Steps:**
1. Set the environment variable: `SITE_BASE_URL=https://example.com/`
2. Run `python -m mkdocs build`
3. Inspect the generated site files

**Expected Result:** Site is built successfully with the URL from the environment variable

### 3. URL Reference Consistency

**Test ID:** GHP-URL-001  
**Description:** Verify all URLs in HTML files are consistent with the configuration  
**Steps:**
1. Build the site with a specific test URL
2. Search for URL references in the generated HTML files
3. Verify all references use the configured URL

**Expected Result:** All URL references match the configured URL

### 4. GitHub Actions Workflow

**Test ID:** GHP-WORKFLOW-001  
**Description:** Verify the GitHub Actions workflow correctly sets environment variables and builds the site  
**Steps:**
1. Run a local simulation of the workflow steps
2. Verify environment variables are set correctly
3. Verify the site builds successfully

**Expected Result:** Workflow steps complete successfully with the correct environment variables

### 5. URL Migration Test

**Test ID:** GHP-MIGRATE-001  
**Description:** Verify the process of changing from auto-generated URL to organization URL  
**Steps:**
1. Update `site_config.yml` to use the organization URL pattern
2. Run the build process
3. Verify all references are updated correctly

**Expected Result:** All URL references are updated to the new URL pattern

## Test Data

- **Private Repository URL:** `https://probable-adventure-3jve6ry.pages.github.io/`
- **Public Repository URL:** `https://thinkevolvesolve.github.io/agent-data-readiness-index/`

## Test Prerequisites

1. Python 3.8+ installed
2. MkDocs and required plugins installed
3. GitHub CLI installed (for simulating workflow)

## Test Execution

### Automated Testing

Create a Python script that automates these tests:

```bash
# Run all GitHub Pages tests
python tests/infrastructure/test_github_pages.py

# Run specific test category
python tests/infrastructure/test_github_pages.py --category=configuration
```

### Manual Testing

For manual testing, follow these steps:

1. Set up the environment:
   ```bash
   pip install mkdocs mkdocs-material mkdocs-macros-plugin
   ```

2. Run the site configuration test:
   ```bash
   python test_site_config.py
   ```

3. Build the site with a test URL:
   ```bash
   SITE_BASE_URL=https://test-url.example.com/ python -m mkdocs build
   ```

4. Inspect the generated site files:
   ```bash
   grep -r "canonical" site/docs/
   ```

## Test Reporting

- Document test results in GitHub Issues
- Include screenshots of successful builds
- Track failed tests and create issues for them

## Maintenance

- Update this test plan when:
  - The GitHub Pages configuration changes
  - New URL references are added to templates
  - The GitHub Actions workflow is modified
  - The MkDocs configuration is updated

## Appendix: Test Checklist

- [ ] Verify site_config.yml contains the correct URL
- [ ] Verify environment variables are set correctly
- [ ] Verify MkDocs builds the site with the correct URL
- [ ] Verify all HTML files use the configured URL
- [ ] Verify GitHub Actions workflow sets environment variables correctly
- [ ] Verify URL migration process works correctly
