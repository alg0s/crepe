# Security Policy

## Supported versions

This repository is currently maintained as a single active line on `main`.

## Reporting a vulnerability

Do not open public issues for security problems.

Report vulnerabilities privately to the repository owner through GitHub security reporting or direct contact. Include:

- a clear description of the issue
- impact and affected components
- reproduction steps or proof of concept
- suggested mitigation if available

## Sensitive data warning

`crepe` can ingest and process sensitive Microsoft Teams communication content.

- Never commit real extracted data under `data/raw`, `data/normalized`, `data/processed`, or `data/reports`.
- Never commit tenant credentials.
- Treat generated reports as confidential unless explicitly sanitized.
- Privacy and compliance policy statements are documented in `PRIVACY.md` and `COMPLIANCE.md`.
