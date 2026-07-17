# Repository Inventory

Date: 2026-07-17
Scope: HYDRA Engineering Task A8

## Current State

The repository is compact, layered, and documentation-heavy. The source layout reflects the accepted DDD plus Hexagonal Architecture, while tests and tools focus on architecture enforcement and platform hardening rather than product features.

## Top-Level Directory Tree

```text
hydra/
|-- .github/
|   |-- workflows/
|   |   |-- ci.yml
|   |   `-- security.yml
|   |-- CODEOWNERS
|   |-- dependabot.yml
|   `-- pull_request_template.md
|-- alembic/
|-- docs/
|   |-- adr/
|   |-- configuration/
|   |-- engineering/
|   |-- governance/
|   |-- observability/
|   |-- operations/
|   |-- reviews/
|   |-- security/
|   `-- templates/
|-- src/
|   `-- hydra/
|       |-- adapters/
|       |-- application/
|       |-- domain/
|       |-- infrastructure/
|       |-- ports/
|       |-- presentation/
|       `-- shared/
|-- tests/
|-- tools/
|-- CHANGELOG.md
|-- CONTRIBUTING.md
|-- Dockerfile
|-- Makefile
|-- README.md
|-- SECURITY.md
|-- alembic.ini
|-- docker-compose.yml
|-- pyproject.toml
`-- uv.lock
```

## Key Source Modules

- `src/hydra/main.py`: composition root and FastAPI app wiring
- `src/hydra/domain/system.py`: domain blueprint and future-facing conceptual module map
- `src/hydra/application/services.py`: root, health, liveness, readiness, and system overview services
- `src/hydra/application/dto.py`: response DTOs
- `src/hydra/ports/runtime_settings.py`: runtime settings contract
- `src/hydra/ports/observability.py`: runtime diagnostics contract
- `src/hydra/adapters/runtime_settings.py`: settings adapter
- `src/hydra/adapters/runtime_diagnostics.py`: readiness adapter
- `src/hydra/infrastructure/config.py`: settings parsing and validation
- `src/hydra/infrastructure/logging.py`: structured logging and startup diagnostics
- `src/hydra/infrastructure/database/session.py`: database engine and session factory wiring
- `src/hydra/presentation/api/middleware.py`: correlation ID middleware
- `src/hydra/presentation/api/routes/health.py`: health endpoint route

## Key Test Modules

- `tests/test_architecture_layers.py`: dependency direction and port enforcement
- `tests/test_configuration.py`: configuration and validation behavior
- `tests/test_health.py`: runtime health endpoint behavior
- `tests/test_logging.py`: structured logging and startup diagnostics redaction
- `tests/test_observability.py`: operational endpoint and diagnostics behavior
- `tests/test_database_session.py`: session factory and engine wiring
- `tests/test_security_baseline.py`: secret handling and forbidden-keyword baseline
- `tests/test_release_readiness.py`: release-readiness checks
- `tests/test_operations_readiness.py`: operations-readiness checks
- `tests/test_developer_workstation.py`: workstation self-check script
- `tests/test_local_verify.py`: local verification script

## Key Tools

- `tools/local_verify.py`
- `tools/check_developer_workstation.py`
- `tools/validate_alembic.py`
- `tools/check_repository_security.py`
- `tools/check_release_readiness.py`
- `tools/check_operations_readiness.py`

## Key Workflows

- `.github/workflows/ci.yml`
- `.github/workflows/security.yml`

## Key Governance Documents

- `docs/governance/Governance Model.md`
- `docs/governance/Definition of Done.md`
- `docs/governance/Release Process.md`
- `docs/governance/Branch Protection.md`
- `docs/governance/Versioning Policy.md`
- `docs/governance/Decision Records.md`
- `docs/governance/RFC Process.md`
- `CHANGELOG.md`
- `CONTRIBUTING.md`
- `SECURITY.md`

## Key Review Documents

- `docs/reviews/a1_1_cleanup_review.md`
- `docs/reviews/a2_observability_review.md`
- `docs/reviews/a3_security_review.md`
- `docs/reviews/a4_governance_review.md`
- `docs/reviews/a5_configuration_review.md`
- `docs/reviews/a6_operations_review.md`
- `docs/reviews/a7_developer_workstation_review.md`
- `docs/reviews/architecture_review_v1.md`
- `docs/reviews/refactor_report.md`

## Evidence

Inventory built from repository filesystem review on 2026-07-17 with noise excluded:

- `.venv/`
- `.mypy_cache/`
- `.pytest_cache/`
- `.ruff_cache/`
- coverage artifacts

## Remaining Risks

- The repository is still small enough to understand manually, but review cost will rise once Milestone B adds more domain and application modules.
- The domain blueprint contains future concept names that may be misread as implemented functionality unless inventory and docs stay current.

## Recommendation

Regenerate and update this inventory whenever:

- a new top-level source package is introduced
- new workflows are added
- Milestone B introduces new review or governance artifacts
