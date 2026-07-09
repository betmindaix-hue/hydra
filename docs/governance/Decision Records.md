# Decision Records

Date: 2026-07-10

## ADR Policy

HYDRA uses Architecture Decision Records for durable technical decisions that affect structure, dependency rules, platform boundaries, or cross-cutting behavior.

## Naming

- file format: `ADR-XXXX-short-title.md`
- sequence: zero-padded incremental numbers
- current baseline: `ADR-0001-hexagonal-architecture.md`

## Required Sections

- status
- context
- decision
- alternatives considered
- consequences
- affected layers
- rollback strategy

## Lifecycle

1. Draft the ADR from `docs/templates/ADR_TEMPLATE.md`.
2. Link the ADR in the related task, pull request, or RFC.
3. Review with the CTO / Architecture Owner.
4. Mark the ADR with its final status.
5. Update dependent docs when the decision is accepted.

## Status Values

- Proposed
- Accepted
- Superseded
- Rejected
- Deprecated
