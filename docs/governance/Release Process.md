# Release Process

Date: 2026-07-10

## Release Baseline

HYDRA uses a lightweight pre-1.0 release discipline focused on repository health and reproducibility.

## Required Inputs

- updated `CHANGELOG.md`
- passing CI workflow
- passing Security workflow
- release-impacting docs updated
- release readiness script passing

## Release Steps

1. Confirm scope is complete and approved.
2. Confirm `CHANGELOG.md` includes release-impacting entries.
3. Run local quality gates.
4. Ensure CI and Security workflow results are green.
5. Review `docs/templates/RELEASE_CHECKLIST_TEMPLATE.md`.
6. Tag the release using the versioning policy.

## Release Review

Release review is required when:

- version changes are introduced
- governance or workflow gates changed
- security-sensitive changes are included
- Docker, CI, or release-readiness behavior changed

## Non-Goals

- no deployment automation is defined yet
- no production trading release path exists in v1
