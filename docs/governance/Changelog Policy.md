# Changelog Policy

Date: 2026-07-10

## Format

HYDRA uses Keep a Changelog style.

## Required Sections

- `Added`
- `Changed`
- `Fixed`
- `Security`

## Rules

- maintain an `Unreleased` section
- add release-impacting changes before merge when practical
- highlight security changes explicitly
- do not use the changelog for internal noise with no release impact

## Release Requirement

If a change affects governance, security, observability, runtime behavior, CI, Docker, or release discipline, the contributor must decide whether `CHANGELOG.md` needs an update and record that decision in the pull request.
