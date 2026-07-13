# Secret Management

Date: 2026-07-10

## Policy

- Never commit secrets.
- Use `.env` files only for local development.
- `.env` must remain gitignored.
- `.env.example`, `.env.local.example`, and `.env.test.example` must contain placeholders only.
- Never log secrets.
- Database passwords must be redacted in diagnostics.
- API keys must not be introduced in v1.
- Exchange keys are explicitly out of scope.

## Current Repository Rules

- Runtime defaults may exist for local scaffolding, but they are not a substitute for secret management.
- Startup diagnostics only expose sanitized database backend metadata, not full connection strings.
- Security reviews must confirm that observability changes do not leak sensitive values.

## Local Development Guidance

1. Copy `.env.example` to `.env`.
2. Use `.env.local.example` and `.env.test.example` as profile-specific references when preparing local or automated test values.
3. Replace placeholders with local development values.
4. Do not share `.env` contents in issues, logs, screenshots, or commits.
5. Rotate any accidentally exposed credentials outside this repository.
