# Security Policy

## Supported Versions

We release patches for security vulnerabilities. Which versions are eligible for receiving such patches depends on the CVSS v3.0 Rating:

| Version | Supported          |
| ------- | ------------------ |
| 4.x.x   | :white_check_mark: |
| 3.x.x   | :white_check_mark: |
| < 3.0   | :x:                |

## Reporting a Vulnerability

The ADRI team and community take security bugs seriously. We appreciate your efforts to responsibly disclose your findings, and will make every effort to acknowledge your contributions.

### How to Report a Security Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report them via email to: **security@adri-standard.org**

If you prefer, you can also report vulnerabilities through GitHub's security advisory feature:
1. Go to the [Security tab](https://github.com/adri-standard/adri/security) of this repository
2. Click "Report a vulnerability" 
3. Fill out the advisory form

### What to Include

Please include the following information in your report:

- Type of issue (e.g. buffer overflow, SQL injection, cross-site scripting, etc.)
- Full paths of source file(s) related to the manifestation of the issue
- The location of the affected source code (tag/branch/commit or direct URL)
- Any special configuration required to reproduce the issue
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the issue, including how an attacker might exploit the issue

### Response Timeline

You can expect the following response timeline:

- **Initial Response**: Within 48 hours of receiving your report
- **Status Update**: Within 7 days with our assessment and next steps
- **Resolution**: We aim to resolve critical vulnerabilities within 30 days

### What to Expect

After submitting a report, you will receive:

1. **Acknowledgment** of your vulnerability report
2. **Assessment** of the vulnerability and its impact
3. **Timeline** for fixes and releases
4. **Credit** in our security advisories (if desired)

### Safe Harbor

We support safe harbor for security researchers who:

- Make a good faith effort to avoid privacy violations, destruction of data, and interruption or degradation of our services
- Only interact with accounts you own or with explicit permission of the account holder
- Do not access a system beyond what is necessary to demonstrate a vulnerability
- Report vulnerabilities to us according to this policy

We will not pursue legal action against researchers who follow this policy.

### Security Best Practices for Users

When using ADRI in production environments:

1. **Keep Updated**: Always use the latest stable version
2. **Validate Input**: Ensure data validation for all external inputs
3. **Secure Configuration**: Follow security configuration guidelines
4. **Monitor Dependencies**: Keep dependencies updated and monitor for vulnerabilities
5. **Access Control**: Implement appropriate access controls for sensitive data

### Security Features

ADRI includes several built-in security features:

- **Input Validation**: Automatic validation of data against defined standards
- **Audit Logging**: Comprehensive logging of all assessment activities
- **Data Protection**: Built-in data boundary controls and privacy protection
- **Secure Defaults**: Security-first configuration defaults

### Dependencies

We regularly monitor our dependencies for security vulnerabilities using:

- GitHub Dependabot alerts
- Automated security scans in our CI/CD pipeline
- Regular dependency updates following semantic versioning

### Contact

For questions about this security policy, please contact:
- Email: security@adri-standard.org
- GitHub: [@adri-standard](https://github.com/adri-standard)

---

This security policy is effective as of the date of the latest commit to this file and will be updated as needed.
