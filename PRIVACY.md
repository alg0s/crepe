# Privacy Statement

`crepe` is designed for communication-flow analysis using metadata, not message content.

## Data minimization

- The system extracts and stores message metadata only:
  - sender identifiers
  - receiver/route inference
  - entity identifiers (users/channels/teams/chats)
  - metadata-derived sentiment scores
- Message body and subject fields are explicitly excluded by extraction filters and privacy guards.

## Privacy guard behavior

- Privacy guards run during extraction, normalization, and API serialization.
- If content-bearing keys (for example `body` or `subject`) appear in message payloads, strict mode blocks processing.
- If forbidden text-like columns appear in output frames, strict mode blocks persistence.

## Scope and operator responsibility

- This repository is intended for internal enterprise administration use.
- Operators remain responsible for lawful use, access control, retention, and deletion policies in their environment.

## Legacy data

- Runs created before metadata-only enforcement may contain historical text fields.
- Purge old run artifacts and regenerate datasets if strict privacy posture is required.
