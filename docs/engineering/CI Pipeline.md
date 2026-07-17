# CI Pipeline

Date: 2026-07-09

## Trigger

The CI workflow runs on:

- every push
- every pull request

## Pipeline Stages

1. Check out the repository
2. Set up Python 3.12
3. Install `uv`
4. Install dependencies with `uv sync --frozen --group dev`
5. Run Ruff
6. Run Black in check mode
7. Run Mypy
8. Run Pytest with coverage output
9. Validate Alembic configuration
10. Run developer workstation checks
11. Run repository security baseline checks
12. Run release readiness checks
13. Run operations readiness checks
14. Build the Docker image

## Failure Policy

CI fails immediately on any step error.

Blocking failures include:

- linting violations
- formatting drift
- typing failures
- test failures
- Alembic validation failures
- developer workstation check failures
- repository security baseline failures
- release readiness failures
- operations readiness failures
- Docker build failures

## Expected Outcomes

The pipeline proves that:

- local engineering standards are automated
- package dependencies are lockfile-driven
- architecture rules are test-enforced
- the application remains buildable as a container
