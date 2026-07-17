# Milestone B Entry Gate

Date: 2026-07-17
Scope: HYDRA Engineering Task B0

## Purpose

This checklist closes the main remaining Milestone A condition before
Controlled Feature Development begins: enforce review and status-check
protection on `main`.

## Current State

Observed on Friday, July 17, 2026:

- `main` branch protection is not enabled
- CI and Security workflows are green
- `dependency-review` is pull-request scoped and skipped on push by design
- Milestone A final review marked branch protection as the primary remaining owner action

## Owner Action Checklist

- [ ] Enable branch protection for `main`
- [ ] Require a pull request before merging
- [ ] Require at least 1 approving review
- [ ] Dismiss stale approvals when new commits are pushed
- [ ] Require conversation resolution before merge
- [ ] Require status checks to pass before merging
- [ ] Require branches to be up to date before merging if GitHub exposes that option
- [ ] Require `CI / quality`
- [ ] Require `Security / repository-security-baseline`
- [ ] Require `Security / codeql (python)`
- [ ] Include administrators in enforcement, unless the owner makes an explicit documented exception
- [ ] Block force pushes
- [ ] Block branch deletion
- [ ] Verify Dependabot PR flow is active
- [ ] Verify `dependency-review` runs on pull requests
- [ ] Confirm no direct pushes to `main` for Milestone B feature work
- [ ] Confirm PR template usage remains mandatory
- [ ] Confirm Milestone B work keeps live trading and exchange execution out of scope

## Evidence Reviewed

- `docs/reviews/milestone_A_final_review/README.md`
- `docs/reviews/milestone_A_final_review/10_risk_register.md`
- `docs/reviews/milestone_A_final_review/11_controlled_feature_readiness.md`
- `docs/reviews/milestone_A_final_review/12_next_phase_recommendation.md`
- `docs/governance/Branch Protection.md`
- `.github/workflows/ci.yml`
- `.github/workflows/security.yml`
- `.github/pull_request_template.md`

Observed latest successful runs before this document:

- CI run `29612680096`: `success`
- Security run `29612680058`: `success`
- Security job `dependency-review`: `skipped` on push by design

## Entry Decision

Milestone B may begin only after the repository owner confirms the checklist
above, or explicitly accepts temporary owner-managed risk in writing.
