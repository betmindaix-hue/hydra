# HYDRA Architecture Review Report v1

Date: 2026-07-09
Reviewer: Senior Software Architect
Scope: Entire repository at `H:\hydra`

## Executive Summary

HYDRA currently presents a solid repository skeleton with a clear product intent, sensible top-level module boundaries, and strong alignment with the SDS documents under `docs/`. The project is off to a disciplined start: live trading is explicitly excluded, raw market payload preservation is reflected in the schema, and the repository already includes FastAPI, PostgreSQL, Redis configuration hooks, Alembic, Docker, and Pytest.

That said, the current implementation is closer to an infrastructure-first scaffold than a Clean Architecture implementation. The most important architectural gap is the absence of a true application/domain core that is independent of FastAPI, SQLAlchemy, and process-wide singletons. Core concepts exist today primarily as ORM models in `src/hydra/db/models.py:14-161`, while API routes depend directly on hard-coded architecture metadata in `src/hydra/core/architecture.py:1-40` and on global settings in `src/hydra/core/config.py:22-27`.

Overall assessment: good foundation, limited operational maturity, and only partial compliance with Clean Architecture and SOLID at this stage.

## Evidence Reviewed

Reviewed repository artifacts include:

- All SDS documents under `docs/`
- Runtime and packaging files: `README.md`, `pyproject.toml`, `Dockerfile`, `docker-compose.yml`, `alembic.ini`, `.env.example`, `.gitignore`, `.dockerignore`, `.python-version`
- All application packages under `src/hydra/`
- Alembic environment and initial migration
- Test suite under `tests/`

Validation performed:

- `H:\hydra\.venv\Scripts\python.exe -m pytest`
- Result: `2 passed, 1 warning`

## Rating by Dimension

| Dimension | Rating | Summary |
| --- | --- | --- |
| Clean Architecture | Partial | Package separation exists, but business core is not independent from frameworks or persistence. |
| SOLID Principles | Partial | Some SRP and modular intent are visible, but abstractions are too thin and dependencies are mostly concrete. |
| Dependency Direction | Partial | Dependencies are simple and mostly acyclic, yet there is no strong inward dependency rule around the domain. |
| Configuration Management | Fair | Centralized settings exist, but singleton/import-time bootstrapping makes override and test isolation harder. |
| Logging / Observability | Weak | Logging configuration exists, but observability is far below the SDS requirement to "log everything." |
| Testing | Weak | Tooling is present and passing, but coverage is only smoke-level and does not protect the architecture. |
| Modularity | Fair | Module folders match the intended pipeline, but modules are placeholders without contracts, orchestration, or ports. |

## Strengths

1. The repository structure already mirrors the SDS pipeline well. The folders under `src/hydra/modules/` map directly to `docs/04_SYSTEM_ARCHITECTURE.md:3-17`, which is a strong starting point for modular evolution.
2. Scope control is explicit and correctly enforced at the skeleton level. Live trading is excluded in the SDS (`docs/00_READ_FIRST.md:5-10`, `docs/01_VISION.md:9-12`) and represented in code by `src/hydra/core/architecture.py:23-40`, `src/hydra/main.py:27-34`, and `src/hydra/api/routes/health.py:8-13`.
3. Configuration is centralized through `pydantic-settings` in `src/hydra/core/config.py:6-27`, with a matching `.env.example`, which is a good baseline for twelve-factor style configuration.
4. The schema reflects important business constraints from the SDS. In particular, raw payload preservation appears in `src/hydra/db/models.py:30-32` and experiment versioning appears in `src/hydra/db/models.py:149-161`, aligning with `docs/02_CONSTITUTION.md:3-10`.
5. Database naming conventions are standardized in `src/hydra/db/base.py:4-14`, which reduces migration inconsistency over time.
6. The project already includes operational scaffolding that many early repositories skip: Alembic, Docker, Compose, and a locked dependency file.

## Weaknesses

1. Clean Architecture is only partially implemented because the domain is persistence-shaped. Core business entities exist only as SQLAlchemy models in `src/hydra/db/models.py:14-161`. There is no framework-independent domain model, application service layer, or port/adapter boundary.
2. High-level behavior depends on concrete globals rather than abstractions. `src/hydra/main.py:17-39` imports concrete settings and concrete routers, while `src/hydra/db/session.py:8-9` creates the engine and session factory at import time. This weakens dependency inversion and makes isolation harder.
3. The SDS is declared the single source of truth in `docs/00_READ_FIRST.md:3-10`, but the same architectural facts are duplicated in `src/hydra/core/architecture.py:1-40` and then surfaced through `src/hydra/api/routes/system.py:8-15`. This creates a parallel truth that can drift from the documents.
4. The module abstraction is too weak for the intended workflow. `src/hydra/modules/base.py:11-16` forces every pipeline module into a synchronous `run() -> None` contract, which is unlikely to fit collectors, feature generation, backtesting, reporting, and memory persistence equally well.
5. Observability is materially below the constitutional requirement to "log everything" in `docs/02_CONSTITUTION.md:3-10`. The implementation is limited to `logging.basicConfig(...)` in `src/hydra/core/logging.py:4-8`, with no structured logs, request correlation, audit events, or consistent logger usage across modules.
6. Testing currently validates only HTTP reachability. The entire suite is `tests/test_health.py:1-23`, which does not protect migration correctness, configuration override behavior, data model integrity, module contracts, or the live-trading guardrail.
7. The container build is not fully reproducible. `uv.lock` exists, but `Dockerfile:10-15` copies `pyproject.toml` without `uv.lock`, so container resolution may drift from local development.
8. Database schema knowledge is duplicated manually across ORM and Alembic. The same structure appears in `src/hydra/db/models.py:14-161` and `alembic/versions/20260708_0001_create_core_tables.py:13-173`, but there is no automated guard against divergence.

## Clean Architecture Compliance

Current state:

- There is a presentation layer shape (`src/hydra/api/`).
- There is an infrastructure/persistence layer shape (`src/hydra/db/`, `alembic/`, Docker files).
- There is a modules package aligned to business capabilities (`src/hydra/modules/`).

Gaps:

- No domain layer containing pure entities, value objects, and policies independent of SQLAlchemy.
- No application/use-case layer orchestrating flows such as collect data, compute features, backtest, paper trade, or generate reports.
- No ports for repositories, event publishing, caching, or logging.
- No adapter layer that clearly separates FastAPI DTOs from domain requests/responses.

Assessment:

The repository shows the beginnings of a layered architecture, but not yet Clean Architecture. The dependency rule is not explicitly enforced, because the current "core" is mostly configuration and static metadata rather than business logic.

## SOLID Principles Assessment

### Single Responsibility Principle

- Positive: route files are small and focused; settings are centralized; module folders map to single business areas.
- Concern: `src/hydra/db/models.py:14-161` contains all persistent entities in one file, which will become a high-churn hotspot as the system grows.
- Concern: `src/hydra/core/architecture.py:1-40` mixes pipeline topology, non-goals, entity catalog, module descriptions, and a runtime feature flag.

### Open/Closed Principle

- Positive: per-module folders provide a natural place for extension.
- Concern: the current abstractions are not rich enough to extend safely. A single `run()` method on `PipelineModule` does not express inputs, outputs, side effects, or orchestration semantics.

### Liskov Substitution Principle

- No immediate violation is visible because implementations are placeholders.
- Risk: once behavior is added, substitutability will be hard to reason about unless the module contract becomes more explicit.

### Interface Segregation Principle

- Concern: one generic module interface for every engine is likely too broad and underspecified for the expected responsibilities.

### Dependency Inversion Principle

- Weakest area today. High-level code depends directly on framework types, concrete settings singletons, and concrete persistence machinery rather than ports or injectable providers.

## Dependency Direction Assessment

What is good:

- Imports are straightforward and mostly acyclic.
- The pipeline modules do not currently depend on one another directly.
- API routing is separated from database code.

What is risky:

- `src/hydra/db/session.py:6-9` depends directly on global settings and initializes infrastructure eagerly.
- `alembic/env.py:6-16` depends on application configuration and model imports, which couples migration tooling to app bootstrapping details.
- There is no inward dependency direction from adapters to application to domain, because application and domain layers are not yet distinct.

## Configuration Management Assessment

Strengths:

- Centralized settings type in `src/hydra/core/config.py:6-27`
- Environment variable prefixing
- Example environment file
- Python version pinned in `.python-version`

Issues:

1. `settings = get_settings()` in `src/hydra/core/config.py:27` creates a process-wide singleton that is imported directly throughout the application.
2. `engine = create_engine(settings.database_url, pool_pre_ping=True)` in `src/hydra/db/session.py:8` binds infrastructure at import time, which complicates test overrides and alternate runtimes.
3. `docker-compose.yml:6-9` duplicates configuration values instead of consuming a shared env strategy, which increases config drift risk.
4. `Dockerfile:15` installs from dependency metadata rather than from the checked-in lock file, reducing build reproducibility.

## Logging and Observability Assessment

Current state:

- Logging setup exists only in `src/hydra/core/logging.py:4-8`.
- Logging is initialized during app lifespan in `src/hydra/main.py:11-14`.

Gaps:

- No structured logging format
- No per-request or per-operation correlation ID
- No audit trail for research decisions, paper trades, or experiment execution
- No metrics, traces, or health depth beyond a simple status endpoint
- No module-level logger usage anywhere in `src/hydra/modules/`

Assessment:

This area is significantly underbuilt relative to `docs/02_CONSTITUTION.md:3-10` and `docs/03_PRODUCT_REQUIREMENTS.md:10-15`, both of which require observability and comprehensive logging.

## Testing Assessment

Current state:

- Pytest is configured in `pyproject.toml:31-34`.
- The suite passes locally.
- Coverage is limited to `tests/test_health.py:1-23`.

Gaps:

- No unit tests for settings, logging, or module contracts
- No integration tests for PostgreSQL, Redis, or Alembic migrations
- No tests for entity constraints or schema compatibility
- No tests protecting the live-trading prohibition
- No architecture tests that verify dependency direction or module isolation

Additional note:

- The executed test run emitted a deprecation warning from `fastapi.testclient`, which is not breaking today but signals future maintenance work in the test stack.

## Modularity Assessment

Strengths:

- The repository already uses business-oriented package names rather than purely technical layers.
- Module folders support future independent implementation and ownership.

Gaps:

- Modules are not yet autonomous units; each service is a placeholder with `NotImplementedError`.
- No explicit contracts exist between stages in the pipeline.
- `Pattern`, `Experiment`, and `PerformanceSnapshot` are modeled in persistence but are not yet represented in module boundaries or application flows.

Assessment:

The physical layout is modular; the runtime architecture is not yet modular.

## Technical Debt

1. Parallel truth between SDS documents and `src/hydra/core/architecture.py`.
2. Global settings singleton and eager database engine creation.
3. Monolithic ORM file for all entities.
4. Manual duplication between ORM models and Alembic migration.
5. Shallow test suite with no architectural guardrails.
6. Reproducibility gap in Docker builds because the lock file is not used.
7. Placeholder module contracts that will likely be refactored once real workflows arrive.

## Risks

### High Risk

1. Architectural drift: the documented source of truth may diverge from hard-coded runtime metadata.
2. Framework lock-in: business logic added directly into FastAPI handlers or SQLAlchemy models will make later clean separation expensive.
3. Testability erosion: import-time infrastructure initialization will become progressively harder to override as more components are added.

### Medium Risk

1. Schema drift between ORM models and Alembic migrations.
2. Incomplete observability for a system that must explain decisions and preserve research lineage.
3. Container builds producing dependency sets different from local development.

### Low Risk

1. Current placeholders may encourage premature assumptions about module behavior if they are treated as stable contracts.

## Prioritized Recommendations

### P0

1. Introduce a real domain/application core.
   Evidence: `src/hydra/db/models.py:14-161`, `src/hydra/main.py:17-39`
   Recommendation: create explicit domain entities or value objects, application use cases, and repository/cache/logging ports so that FastAPI, SQLAlchemy, and Redis become adapters rather than the center of the design.

2. Remove import-time infrastructure bootstrapping.
   Evidence: `src/hydra/core/config.py:22-27`, `src/hydra/db/session.py:8-9`
   Recommendation: move settings access and engine/session creation behind injectable providers or lifespan-managed factories so tests and future workers can override runtime dependencies safely.

### P1

1. Eliminate or govern the duplicate architecture metadata.
   Evidence: `docs/00_READ_FIRST.md:3-10`, `src/hydra/core/architecture.py:1-40`
   Recommendation: either generate runtime metadata from a versioned config/source or clearly designate code as the executable contract and update the SDS governance rule accordingly.

2. Establish an observability baseline that matches the constitution.
   Evidence: `docs/02_CONSTITUTION.md:3-10`, `src/hydra/core/logging.py:4-8`
   Recommendation: add structured logs, correlation IDs, domain audit events, and module-level loggers before real trading research flows are implemented.

3. Expand the test suite from smoke tests to architectural protection.
   Evidence: `tests/test_health.py:1-23`
   Recommendation: add migration smoke tests, database integration tests, settings override tests, live-trading guard tests, and dependency-boundary tests.

### P2

1. Split persistence models into bounded files or subpackages.
   Evidence: `src/hydra/db/models.py:14-161`
   Recommendation: separate market, strategy, trading, and research persistence models to reduce file churn and improve maintainability.

2. Make container builds reproducible from the lock file.
   Evidence: `Dockerfile:10-15`, `uv.lock`
   Recommendation: copy `uv.lock` into the image and install from the locked dependency graph.

3. Replace the generic `PipelineModule.run()` with explicit stage contracts.
   Evidence: `src/hydra/modules/base.py:11-16`
   Recommendation: define typed use-case interfaces per stage once the next SDS packages arrive, instead of growing a one-size-fits-all orchestration method.

## Final Verdict

HYDRA is a promising, disciplined scaffold with good strategic boundaries and a repository structure that respects the documented pipeline. However, it is not yet a Clean Architecture implementation in the strict sense. The next design step should not be adding more framework code; it should be creating a framework-independent application/domain core and enforcing dependency direction around it.

No production code was modified as part of this review. Only this report was added.

