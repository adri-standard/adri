# Security Policy

## Disclaimer

This security policy is provided for informational purposes only and does not create any legal obligations, warranties, or guarantees. This open source software is provided "AS IS" without warranty of any kind. Please refer to the LICENSE file for complete terms and liability limitations.

## Supported Versions

We make best efforts to release patches for security vulnerabilities when resources permit. Which versions may receive patches depends on the CVSS v3.0 Rating and maintainer availability:

| Version | Supported          |
| ------- | ------------------ |
| 4.x.x   | :white_check_mark: |
| 3.x.x   | :white_check_mark: |
| < 3.0   | :x:                |

## Reporting a Vulnerability

The ADRI community appreciates security research conducted responsibly. This is volunteer-maintained open source software with no service level agreements or guaranteed response times.

### How to Report a Security Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report them through GitHub's security advisory feature:
1. Go to the [Security tab](https://github.com/adri-standard/adri/security) of this repository
2. Click "Report a vulnerability"
3. Fill out the advisory form

You can also email the maintainers directly using the contact information in the repository, but GitHub Security Advisories is our preferred method for coordinated disclosure.

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

**IMPORTANT: These are aspirational timelines, not contractual commitments.**

We will make reasonable efforts to respond when maintainer time permits:

- **Initial Response**: Typically 5-7 business days, may vary significantly
- **Status Update**: Approximately 2 weeks, subject to maintainer availability
- **Resolution**: Best effort basis, complexity and volunteer availability dependent

**No SLA or guaranteed response times are provided. This is volunteer-maintained software.**

### What to Expect

After submitting a report, you will receive:

1. **Acknowledgment** of your vulnerability report
2. **Assessment** of the vulnerability and its impact
3. **Timeline** for fixes and releases
4. **Credit** in our security advisories (if desired)

### Responsible Disclosure Appreciation

We appreciate security researchers who conduct responsible research within these guidelines:

- Make a good faith effort to avoid privacy violations, destruction of data, and interruption or degradation of services
- Only interact with systems they own or have explicit permission to test
- Do not access systems beyond what is necessary to demonstrate a vulnerability
- Report vulnerabilities according to this policy

**Disclaimer**: This policy does not create any legal obligations, safe harbor protections, or immunity from prosecution. Researchers should consult their own legal counsel regarding applicable laws. We will make reasonable efforts to work constructively with researchers who follow responsible disclosure practices, subject to applicable law and available resources.

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

For questions about this security policy, please:
- Open a GitHub discussion in this repository
- Contact the maintainers through GitHub
- Use GitHub Security Advisories for vulnerability reports

---

## Legal Notice

- This security policy creates no contractual obligations or guarantees
- No warranties are provided regarding security, fitness for purpose, or merchantability
- All software is provided under the terms of the LICENSE file
- Maintainers disclaim liability for security vulnerabilities or their consequences
- This is volunteer-maintained open source software with no service commitments
- Policy may be updated or discontinued at any time without notice

This security policy is effective as of the date of the latest commit to this file and may be updated as needed.
