# A1 Docker Reproducibility Report

Date: 2026-07-09
Scope: Container build reproducibility and local build evidence
Final Verdict: PASS WITH WARNINGS

## What Changed

A1 replaced the earlier container approach with a multi-stage Docker build that copies `uv.lock`, performs `uv sync --frozen`, and separates build-time dependency preparation from the runtime image.

## Evidence

- `Dockerfile`
- `uv.lock`
- `pyproject.toml`
- `docker-compose.yml`
- `docs/engineering/Developer Setup.md`
- `.dockerignore`

## Commands Executed

```powershell
docker build .
git show --stat --oneline --summary 213248c
```

## Command Results

Repository evidence indicates the intended reproducibility controls are present:

- base builder image: `ghcr.io/astral-sh/uv:python3.12-bookworm-slim`
- runtime base image: `python:3.12-slim-bookworm`
- lockfile copied into the build context
- `uv sync --frozen` used in both dependency preparation steps
- multi-stage image layout used to keep the runtime image smaller

Local execution result:

```text
docker : The term 'docker' is not recognized as the name of a cmdlet, function,
script file, or operable program.
```

Assessment: WARNING. The Dockerfile design is materially stronger than the earlier baseline, but the local host could not verify a successful image build because Docker is unavailable.

## Remaining Risks

- No local image digest, size, or runtime smoke-test evidence was produced in this session.
- Base images are version-pinned by tag but not by immutable digest.
- Reproducibility is strong at the dependency layer, but full build reproducibility still depends on the exact upstream base images available at build time.

## Recommended Next Actions

1. Run `docker build .` on a Docker-enabled host and archive the image digest and size.
2. Consider pinning base images by digest when the team wants stricter supply-chain reproducibility.
3. Add a lightweight container startup smoke test in CI once Docker execution evidence is available.
