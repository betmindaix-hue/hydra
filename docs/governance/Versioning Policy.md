# Versioning Policy

Date: 2026-07-10

## Scheme

HYDRA uses Semantic Versioning.

Format:

- `MAJOR.MINOR.PATCH`

## Pre-1.0 Compatibility Policy

Before `1.0.0`:

- `MINOR` releases may include incompatible internal changes
- `PATCH` releases should remain low-risk and backward-compatible where practical
- release notes must call out breaking or operationally relevant changes explicitly

## Tag Format

- release tags use `vX.Y.Z`
- example: `v0.1.0`

## Release Expectations

- update `CHANGELOG.md` for release-impacting changes
- call out security changes in the changelog
- confirm CI and Security workflows are green before tagging
