# Security Guidelines for ADRI

This document outlines security best practices for the Agent Data Readiness Index (ADRI) project, particularly regarding authentication credentials and API tokens.

## Table of Contents
- [Managing API Tokens](#managing-api-tokens)
- [GitHub Actions Secrets](#github-actions-secrets)
- [Development Security Guidelines](#development-security-guidelines)
- [Credential Rotation](#credential-rotation)
- [Security Incident Reporting](#security-incident-reporting)

## Managing API Tokens

ADRI requires authentication tokens for certain operations, such as publishing to PyPI. These tokens should be handled securely:

### General Token Guidelines

1. **Never hardcode tokens** in source code or configuration files.
2. **Never commit tokens** to version control, even in comments or documentation.
3. **Use environment variables** to pass tokens to applications.
4. **Scope tokens** to the minimum permissions required for their function.
5. **Treat tokens like passwords** - they provide direct access to services and resources.

### Local Development

When working with tokens in local development:

1. **Use environment variables in current shell session:**
   ```bash
   # Set token
   export TESTPYPI_API_TOKEN="your-token-here"
   
   # Run command requiring token
   pytest tests/integration/test_publishing.py
   
   # Unset token when done
   unset TESTPYPI_API_TOKEN
   ```

2. **Use `.env` files with proper exclusion from git:**
   - Create a `.env` file for environment variables
   - Add `.env` to `.gitignore`
   - Use a library like `python-dotenv` to load variables
   - Never share these files directly with team members

3. **Use credential managers** when available:
   - macOS Keychain
   - Windows Credential Manager
   - Secret Management services in IDEs

## GitHub Actions Secrets

ADRI utilizes GitHub Actions Secrets for storing tokens used in CI/CD pipelines:

### Setting Up GitHub Secrets

1. **Repository Secrets**: Navigate to the repository settings:
   - Go to Settings → Secrets and variables → Actions
   - Click "New repository secret"
   - Enter the name (e.g., `TESTPYPI_API_TOKEN`) and value
   - Click "Add secret"

2. **Organization Secrets** (if applicable):
   - Go to Organization Settings → Secrets and variables → Actions
   - Create secrets that can be used across multiple repositories

### Using Secrets in Workflows

Secrets are referenced in workflow files as:

```yaml
steps:
  - name: Step that needs the secret
    env:
      SECRET_NAME: ${{ secrets.SECRET_NAME }}
    run: command-that-uses-secret
```

### Security Considerations for GitHub Actions

1. **Limit workflow permissions** to only what is necessary
2. **Use OIDC tokens** instead of long-lived access tokens when possible
3. **Avoid printing secrets** to logs or outputs
4. **Pin action versions** to avoid supply chain attacks

## Development Security Guidelines

### Code and Repository Guidelines

1. **Scan for secrets** before committing:
   - Use tools like `detect-secrets` or `gitleaks`
   - Configure pre-commit hooks to prevent accidental commits
   - Run periodic scans on the repository

2. **Use specific imports** to avoid exposing sensitive parts of the codebase:
   ```python
   # Avoid
   from config import *  # Could expose secrets
   
   # Prefer
   from config import public_settings  # Explicit, no secrets
   ```

3. **Secure logging practices**:
   - Implement redaction for sensitive values
   - Use debug level for detailed information
   - Avoid logging credentials even in debug mode

### Testing with Secrets

1. **Mock secrets in tests** whenever possible
2. **Use fake tokens with specific formats** for testing patterns
3. **Have separate tokens for testing** environments
4. **Use conditional execution** for tests requiring real credentials:
   ```python
   @pytest.mark.skipif(
       not os.environ.get('TESTPYPI_API_TOKEN'),
       reason="TestPyPI token not available"
   )
   def test_requiring_token():
       # Test code
   ```

## Credential Rotation

Regular credential rotation prevents issues from leaked credentials:

1. **Establish a rotation schedule** for all tokens and credentials
2. **Document expiration dates** in a secure location
3. **Automate rotation** where possible
4. **Perform rotation after team member departures**

### Immediate Rotation

If you suspect a token has been compromised:

1. Immediately invalidate/rotate the token
2. Check for any unauthorized usage
3. Review security logs
4. Follow the security incident reporting process

## Security Incident Reporting

If you discover a security issue:

1. **Don't disclose it publicly** in issues or discussions
2. **Report directly** to project maintainers via secure channels
3. **Provide details** including steps to reproduce
4. **Wait for confirmation** before discussing publicly
