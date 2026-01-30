# Security Policy

## Preventing secrets in the repo

- **Do not commit** real AWS keys, passwords, `.env` files (use `.env.example` as a template), or private keys (e.g. `.pem`).
- **CI** runs a secret scan (Gitleaks) on push/PR; commits that appear to contain secrets will fail the check.
- **API** does not return `aws_access_key_id` or `aws_secret_access_key` in profile GET/list responses; only non-sensitive fields are exposed.

## Supported Versions

Use this section to tell people about which versions of your project are
currently being supported with security updates.

| Version | Supported          |
| ------- | ------------------ |
| 5.1.x   | :white_check_mark: |
| 5.0.x   | :x:                |
| 4.0.x   | :white_check_mark: |
| < 4.0   | :x:                |

## Reporting a Vulnerability

Use this section to tell people how to report a vulnerability.

Tell them where to go, how often they can expect to get an update on a
reported vulnerability, what to expect if the vulnerability is accepted or
declined, etc.
