# Branch Protection

Date: 2026-07-10

## Recommended Rules For `main`

- require pull requests before merge
- require at least one review
- require code owner review where applicable
- require passing status checks
- block force pushes
- block branch deletion
- require conversation resolution before merge

## Required Status Checks

- `CI`
- `Security`

## Governance Notes

- platform-only sprint scope must be enforced during review
- changelog updates must be checked for release-impacting changes
- governance, security, and observability changes should not bypass review
