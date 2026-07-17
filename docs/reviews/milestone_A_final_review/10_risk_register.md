# Final Risk Register

Date: 2026-07-17
Scope: HYDRA Engineering Task A8

## Current State

Milestone A risks are manageable, visible, and mostly procedural rather than architectural. The repository is healthy enough for controlled next-phase work, but several safeguards should be strengthened before scope expands.

## Evidence

- architecture rules are documented and tested
- CI and Security workflows are active
- local verification and workstation checks are available
- branch protection is currently disabled on `main`
- Docker validation is reliable in CI but not reproducible on the current workstation

## Commands Or Source Files Reviewed

Sources reviewed:

- `docs/adr/ADR-0001-hexagonal-architecture.md`
- `docs/governance/*.md`
- `docs/configuration/*.md`
- `docs/operations/*.md`
- `docs/reviews/a1_1_cleanup_review.md` through `docs/reviews/a7_developer_workstation_review.md`
- `.github/workflows/ci.yml`
- `.github/workflows/security.yml`
- `tests/test_architecture_layers.py`

Repository metadata reviewed:

- `https://api.github.com/repos/betmindaix-hue/hydra/branches/main`

## Risk Register

| Risk | Severity | Likelihood | Current mitigation | Next action | Owner role |
| --- | --- | --- | --- | --- | --- |
| Architecture drift as new modules are added | High | Medium | ADR, architecture tests, layered package structure | expand architecture tests before new adapters or repositories | CTO / Architecture Owner |
| Premature feature expansion beyond approved scope | High | Medium | explicit non-goals in docs, reviews, and contributing guidance | require scope confirmation at sprint start and PR review | Product Owner |
| Docker local availability gaps | Medium | High | CI Docker build is authoritative, docs state Docker is optional locally | document reproducible local Docker setup when needed | Lead Engineer |
| Environment misconfiguration on workstations | Medium | Medium | runtime validation, workstation check, docs, env templates | add checklist enforcement during onboarding and PR review | Lead Engineer |
| Secret leakage through code, docs, or diagnostics | High | Low | `.env` gitignore, secret policy, repository security script, redaction tests | enable broader secret scanning if repository complexity grows | Security Reviewer |
| CI fragility from tooling or workflow drift | Medium | Medium | CI and Security workflows, local verification, prior A7 coverage fix | periodically refresh action versions and watch deprecation warnings | Lead Engineer |
| Coverage blind spots in selected infrastructure or adapter modules | Medium | Medium | 97 percent total coverage, focused tests for critical scripts and session wiring | target weak modules in the next non-feature hardening pass | Reviewer |
| Documentation drift across engineering and operations guides | Medium | Medium | definition of done, release readiness, docs-heavy milestones | require doc updates in every cross-cutting PR | Reviewer |
| Operations runbook staleness | Medium | Medium | operations readiness script validates required files and anchors | add scenario-based runbook rehearsal when shared environments appear | QA Responsibility |
| Dependency update risk | Medium | Medium | Dependabot, uv lockfile, dependency review on PRs | enforce PR-based dependency changes under branch protection | Security Reviewer |
| GitHub branch protection not enforced in repository settings | High | High | branch protection expectations are only documented today | enable required checks and PR-based merge rules on `main` | CTO / Architecture Owner |
| Future market data scope creep | High | Medium | non-goals are repeated in docs and reviews | require ADR or RFC before any external data integration | Product Owner |
| Future trading or live execution boundary erosion | Critical | Low | live trading hard-disabled, no exchange credentials, no execution code | preserve explicit prohibition through Milestone B and beyond | CTO / Architecture Owner |

## Remaining Risks

- The highest unmanaged risk is enforcement gap between documented governance and actual branch settings.
- The next highest risk is scope creep once research-oriented concepts start entering the domain model.

## Recommendation

Treat branch protection and PR enforcement as the first operational control to add before meaningful Milestone B growth begins.
