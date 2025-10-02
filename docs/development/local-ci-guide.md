# Local CI Validation with ACT

This guide explains how to run GitHub Actions workflows locally using ACT to validate changes before pushing to GitHub.

## Overview

ACT allows you to run GitHub Actions workflows locally in Docker containers, providing fast feedback on CI issues without pushing to GitHub. This is particularly useful for:

- Testing CI workflow changes
- Debugging failing tests
- Validating security scans
- Checking build processes
- Running pre-commit hooks locally

## Prerequisites

1. **Docker**: ACT requires Docker to run workflows in containers
2. **ACT**: Install using: `brew install act` (macOS) or see [ACT installation guide](https://github.com/nektos/act#installation)

## ACT Configuration

The project includes a pre-configured `.actrc` file with optimal settings:

```bash
# Platform mappings for Ubuntu workflows
-P ubuntu-latest=catthehacker/ubuntu:act-latest

# Use Docker host networking for better compatibility
--use-gitignore=false
--artifact-server-path=/tmp/artifacts
```

## Available Workflows

### 1. Test Workflow (`act pull_request --job test`)

**Purpose**: Runs the complete test suite across multiple Python versions

**What it tests**:
- Python 3.10, 3.11, 3.12 compatibility
- Pre-commit hooks (formatting, linting, security)
- Unit and integration tests
- Code coverage reporting

**Example usage**:
```bash
# Run all test matrix jobs
act pull_request --job test

# Run specific Python version (if needed)
act pull_request --job test --matrix python-version:3.11
```

**Common issues**:
- Pre-commit hook failures (whitespace, formatting)
- Test failures due to missing mocks or import issues
- Coverage threshold not met

### 2. Security Workflow (`act pull_request --job security`)

**Purpose**: Performs security scans on the codebase

**What it tests**:
- Bandit security scan for Python vulnerabilities
- Safety scan for dependency vulnerabilities
- pip-audit for package security issues

**Example usage**:
```bash
act pull_request --job security
```

**Typical output**:
- Bandit: No security issues found
- Safety: Dependency vulnerability scan
- pip-audit: Package vulnerability audit

### 3. Build Test Workflow (`act pull_request --job build-test`)

**Purpose**: Tests package building and installation

**What it tests**:
- setuptools_scm version detection
- Package building (sdist and wheel)
- Package installation verification
- CLI command functionality

**Example usage**:
```bash
act pull_request --job build-test
```

## Workflow Commands Reference

### Run All PR Checks
```bash
# Run all pull request workflows
act pull_request

# Run specific job only
act pull_request --job test
act pull_request --job security
act pull_request --job build-test
```

### Debugging Options
```bash
# Verbose output for debugging
act pull_request --job test --verbose

# List available workflows and jobs
act --list

# Dry run to see what would execute
act pull_request --dry-run
```

### Environment Customization
```bash
# Set custom environment variables
act pull_request --env CUSTOM_VAR=value

# Use custom event file
act pull_request --eventpath .github/events/pull_request.json
```

## Troubleshooting Common Issues

### 1. Docker Permission Issues
```bash
# Ensure Docker daemon is running
sudo systemctl start docker

# Add user to docker group (Linux)
sudo usermod -aG docker $USER
```

### 2. Container Platform Issues
If you see "unsupported platform" errors:
```bash
# Use specific platform mapping
act pull_request --platform ubuntu-latest=catthehacker/ubuntu:act-latest
```

### 3. Memory/Resource Issues
For resource-intensive workflows:
```bash
# Increase Docker memory limits
docker system prune -f

# Run jobs sequentially instead of parallel
act pull_request --job test --matrix python-version:3.11
```

### 4. Pre-commit Hook Failures
```bash
# Run pre-commit locally first
pre-commit run --all-files

# Fix common issues
pre-commit run trailing-whitespace --all-files
pre-commit run black --all-files
```

## Workflow Integration

### Before Pushing Changes
```bash
# 1. Run pre-commit checks
pre-commit run --all-files

# 2. Run core tests locally
python -m pytest tests/ -v

# 3. Validate with ACT
act pull_request --job test
act pull_request --job security

# 4. Push changes
git push origin feature-branch
```

### CI/CD Best Practices

1. **Test Locally First**: Always run ACT before pushing
2. **Incremental Testing**: Test specific jobs when making targeted changes
3. **Resource Management**: Use `--job` flag to run specific workflows
4. **Log Analysis**: Use `--verbose` for debugging failures

## Performance Tips

### Speeding Up ACT Runs
```bash
# Cache Docker images locally
docker pull catthehacker/ubuntu:act-latest

# Use job-specific runs instead of full matrix
act pull_request --job test --matrix python-version:3.11

# Skip artifact uploads in local runs
act pull_request --job build-test --skip-checkout
```

### Resource Optimization
```bash
# Clean up Docker resources periodically
docker system prune -f

# Monitor Docker usage
docker stats
```

## Integration with Development Workflow

### VS Code Integration
Add to `.vscode/tasks.json`:
```json
{
    "version": "2.0.0",
    "tasks": [
        {
            "label": "ACT: Run Tests",
            "type": "shell",
            "command": "act pull_request --job test",
            "group": "test",
            "problemMatcher": []
        },
        {
            "label": "ACT: Security Scan",
            "type": "shell",
            "command": "act pull_request --job security",
            "group": "test",
            "problemMatcher": []
        }
    ]
}
```

### Git Hooks Integration
Add to `.git/hooks/pre-push`:
```bash
#!/bin/bash
echo "Running local CI validation..."
act pull_request --job test --matrix python-version:3.11
if [ $? -ne 0 ]; then
    echo "❌ Local CI validation failed"
    exit 1
fi
echo "✅ Local CI validation passed"
```

## Monitoring and Logs

### Log Locations
ACT logs are available in:
- Terminal output (real-time)
- Docker container logs
- `/tmp/act/` directory (if configured)

### Log Analysis
```bash
# View last ACT run logs
docker logs $(docker ps -l -q)

# Follow logs in real-time
act pull_request --job test --verbose | tee act-logs.txt
```

## Conclusion

ACT provides powerful local CI validation capabilities that help catch issues early in the development process. By following this guide, you can:

- Validate changes before pushing to GitHub
- Debug CI issues locally
- Reduce failed PR builds
- Speed up development cycles

For additional help, see:
- [ACT Documentation](https://github.com/nektos/act)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- Project-specific workflow files in `.github/workflows/`
