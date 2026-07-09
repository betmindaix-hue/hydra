# RFC Process

Date: 2026-07-10

## Purpose

RFCs are used for cross-cutting or multi-step technical proposals that need structured design review before implementation.

## When To Write An RFC

- the design spans multiple layers or teams
- the work introduces meaningful trade-offs
- the change is too large for a single PR explanation
- the change affects security, observability, release process, or architecture boundaries

## Workflow

1. Start from `docs/templates/RFC_TEMPLATE.md`.
2. Clearly define goals and non-goals.
3. Capture alternatives and open questions.
4. Review with architecture and security stakeholders when applicable.
5. Convert accepted decisions into implementation tasks and ADRs as needed.

## Approval Expectations

- CTO / Architecture Owner for architectural risk
- Security reviewer for security-sensitive changes
- Lead Engineer for implementation feasibility

## Exit Criteria

An RFC is ready for execution when:

- open questions are resolved or explicitly deferred
- risk areas are documented
- testing and migration plans are clear
- required follow-up ADRs are identified
