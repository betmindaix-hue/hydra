# Security Policy

## Supported Versions

| Version | Supported |
| --- | --- |
| `0.1.x` | Yes |
| `< 0.1.0` | No |

## Reporting A Vulnerability

If you believe you have found a security issue in HYDRA:

1. Do not open a public issue with exploit details.
2. Use a private reporting channel made available by the repository maintainers.
3. If no private channel is yet configured, open a minimal issue asking maintainers to establish a private disclosure path without including sensitive details.

This repository does not currently publish a dedicated security contact address in version control.

## Responsible Disclosure

- Give maintainers reasonable time to triage and remediate before public disclosure.
- Share reproduction steps privately.
- Avoid publishing secrets, tokens, or exploit payloads in public threads.
- Treat proof-of-concept material as sensitive until maintainers confirm disclosure timing.

## Secret Handling Policy

- Never commit secrets, tokens, credentials, or private keys.
- Use `.env` files only for local development.
- Keep `.env` out of version control.
- Keep `.env.example`, `.env.local.example`, and `.env.test.example` limited to placeholders.
- Never log raw secrets or full database credentials.

## v1 Non-Goals

The following remain out of scope for HYDRA v1:

- live trading
- exchange execution
- market data collection implementation
- exchange API key support
- strategy execution
- AI features
- websocket infrastructure

HYDRA does not support live trading or exchange execution in this phase.
