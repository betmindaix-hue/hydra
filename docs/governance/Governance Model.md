# Governance Model

Date: 2026-07-10

## Purpose

This document defines how HYDRA engineering decisions are made, reviewed, and approved during pre-1.0 development.

## Roles

### Product Owner

- owns scope prioritization
- confirms whether work belongs to the approved sprint objective
- rejects product-scope expansion during platform-only sprints

### CTO / Architecture Owner

- approves architectural direction
- decides when an ADR or RFC is required
- reviews cross-cutting design changes
- approves release readiness for architecture-sensitive changes

### Lead Engineer

- translates sprint goals into executable repository changes
- ensures code, tests, workflows, and docs remain aligned
- confirms quality gates and release-readiness checks pass

### Reviewer

- validates correctness, maintainability, and scope control
- confirms tests and documentation are sufficient
- verifies changelog and release impact handling when applicable

### Security Reviewer

- reviews secret handling, dependency risk, workflow security, and sensitive logging behavior
- confirms security policy and checklist requirements are satisfied

### QA Responsibility

- validates acceptance criteria through automated or documented verification
- confirms regressions are covered by tests or explicit release notes

## Decision Thresholds

### Changes That Require An ADR

- top-level architectural restructuring
- dependency direction changes
- new composition-root patterns
- major infrastructure ownership changes
- changes that alter domain purity rules

### Changes That Require An RFC

- multi-step implementation plans spanning multiple sprints
- cross-cutting workflow or platform governance changes
- significant release-process changes
- substantial tooling or CI strategy changes with trade-offs

### Changes That Require Security Review

- secret handling changes
- logging or observability changes that may expose sensitive data
- dependency governance changes
- CI or workflow security changes
- changes touching repository policies under `SECURITY.md` or `docs/security/`

### Changes That Require Release Review

- release-impacting workflow changes
- versioning policy changes
- changelog policy changes
- Docker, CI, or release-readiness changes
- any change that modifies required release gates
