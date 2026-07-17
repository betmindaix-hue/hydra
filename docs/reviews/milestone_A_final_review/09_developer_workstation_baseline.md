# Developer Workstation Baseline

Date: 2026-07-17
Scope: HYDRA Engineering Task A8

## Current State

HYDRA now provides a practical developer workstation baseline for Windows PowerShell and Git Bash or MINGW64:

- Python 3.12 requirement
- `uv` direct mode and `python -m uv` fallback
- optional local Docker
- optional `make`
- workstation self-check tooling
- local verification tooling
- command parity documentation

This materially lowers onboarding friction while keeping Docker validation authoritative in CI.

## Evidence

- Setup guidance: `docs/engineering/Developer Setup.md`
- Workstation guide: `docs/engineering/Developer Workstation.md`
- Windows guide: `docs/engineering/Windows Setup.md`
- Command parity guide: `docs/engineering/Command Parity.md`
- Local runtime verification guide: `docs/engineering/Local Runtime Verification.md`
- Workstation checker: `tools/check_developer_workstation.py`
- Local verification tool: `tools/local_verify.py`
- Tool tests: `tests/test_developer_workstation.py`, `tests/test_local_verify.py`

Local workstation evidence from 2026-07-17:

- `python tools/check_developer_workstation.py` equivalent via `python -m uv run python tools/check_developer_workstation.py`: PASS with optional warnings for missing Docker and `make`
- `python tools/local_verify.py`: PASS
- explicit quality gates: PASS

## Commands Or Source Files Reviewed

Commands executed:

- `python tools/local_verify.py`
- `python -m uv run python tools/check_developer_workstation.py`

Source files reviewed:

- `docs/engineering/Developer Setup.md`
- `docs/engineering/Developer Workstation.md`
- `docs/engineering/Windows Setup.md`
- `docs/engineering/Command Parity.md`
- `docs/engineering/Local Runtime Verification.md`
- `tools/check_developer_workstation.py`
- `tools/local_verify.py`

## Remaining Risks

- The current workstation still lacks Docker CLI access, so contributors depend on CI for authoritative image validation.
- The workstation check verifies command and file availability, but it cannot fully validate every shell profile or PATH quirk.
- `make` remains optional, which is good for portability but increases the chance of direct-command drift if docs are not maintained.

## Recommendation

Keep the current self-check tooling as a required first step for new contributors. If Milestone B adds new local commands, update:

- `Makefile`
- `Command Parity.md`
- `Local Runtime Verification.md`
- `tools/local_verify.py`
