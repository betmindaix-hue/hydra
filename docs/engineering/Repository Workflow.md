# Repository Workflow

Date: 2026-07-09

## Branch And Commit Workflow

1. Pull the latest `main`.
2. Create a focused branch for a single engineering objective.
3. Run local validation:
   - `make lint`
   - `make test`
   - `make alembic-check`
4. Run `pre-commit run --all-files`.
5. Commit using Conventional Commits.
6. Push and open a pull request.

## Pull Request Expectations

Every pull request should include:

- a concise problem statement
- the SDS or engineering documents affected
- validation evidence
- explicit note if any acceptance item could not be locally verified

## Review Rules

Reviewers should check:

1. architecture boundary compliance
2. absence of new business features in platform-only sprints
3. reproducibility of tooling and Docker configuration
4. documentation updates for workflow or architecture changes

## Merge Policy

Changes should be merged only when:

- CI is green
- required documentation is updated
- review comments are resolved
- no forbidden scope expansion has occurred

