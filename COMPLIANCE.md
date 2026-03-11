# Compliance Statement

`crepe` is a metadata analytics tool and does not perform automated Team/channel mutation.

## Compliance design principles

- Data minimization: only metadata required for information-flow analysis is stored.
- Purpose limitation: analytics outputs are for internal governance, planning, and operational insight.
- Least privilege: operators should grant only required Microsoft Graph permissions.
- Auditability: run artifacts and run metadata provide traceability of extraction/analysis outputs.

## Deployment controls expected from operators

- Restrict application and API access with enterprise identity controls.
- Store credentials in managed secret storage.
- Apply retention and deletion schedules for run artifacts and reports.
- Align with internal policy and regulatory requirements (for example SOC 2, ISO 27001, GDPR, regional privacy law) as applicable to your organization.

## Non-goals

- This project does not independently certify legal compliance for your organization.
- This project does not replace legal, privacy, or security review for production deployment.
