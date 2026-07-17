# Branch Protection

Date: 2026-07-17
Scope: HYDRA Engineering Task B0

## Current Observed State

As of Friday, July 17, 2026, the public GitHub branch metadata for `main`
shows:

- branch protection enabled: `false`
- required status checks configured: none
- pull request review requirement visible: no
- force push prevention visible: no
- branch deletion prevention visible: no
- admin enforcement visible: no

Observed evidence:

- branch endpoint: `GET /repos/betmindaix-hue/hydra/branches/main`
- observed head SHA: `a3e80ad370af04c336e099d9fb3c14e63e7fe42f`
- observed branch field: `"protected": false`
- observed protection summary: `"enabled": false`

Detailed protection inspection through:

- `GET /repos/betmindaix-hue/hydra/branches/main/protection`

returned `401 Unauthorized` in the current execution context, so deeper
protection details cannot be confirmed through this environment unless a GitHub
token with branch-protection access is available.

## Required Rules For `main`

Milestone B should not begin feature work on `main` without these GitHub branch
protection rules:

- require a pull request before merging
- require at least 1 approving review
- dismiss stale approvals when new commits are pushed
- require conversation resolution before merge
- require status checks to pass before merging
- require branches to be up to date before merging when GitHub exposes that option
- include administrators in branch protection enforcement
- prevent force pushes
- prevent branch deletion

Code owner review may remain enabled when the repository owner wants stricter
governance, but the minimum Milestone B entry gate is one approving review plus
the required checks listed below.

## Required Status Checks

The exact check names should be taken from the latest successful GitHub Actions
results visible on the repository.

Latest observed successful checks for commit
`30dff80acbe6d7d0afbcce3814b5c5691f440d3d` on Friday, July 17, 2026:

- workflow `CI`, run `29613384777`, job `quality`
- workflow `Security`, run `29613384816`, job `repository-security-baseline`
- workflow `Security`, run `29613384816`, job `codeql (python)`

Recommended required status checks in GitHub UI, when shown with workflow and
job names:

- `CI / quality`
- `Security / repository-security-baseline`
- `Security / codeql (python)`

`dependency-review` is intentionally pull-request scoped and appeared as
`skipped` on the latest push workflow. It should be validated on pull requests,
but it should not be faked as a push-only required check name.

## Recommended Owner Setting

For Milestone B feature work, administrator enforcement is appropriate because
the highest remaining Milestone A governance gap is direct push exposure on
`main`. If the owner needs an emergency override path later, that decision
should be explicit and documented rather than left open by default.

## Governance Notes

- platform-only and foundation-to-feature transition scope must still be enforced during review
- changelog updates must be checked for release-impacting changes
- governance, security, observability, and architecture-sensitive changes should not bypass PR review
- no Milestone B work should introduce live trading, exchange execution, exchange credentials, or real-money operations
