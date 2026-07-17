# Windows Setup

Date: 2026-07-17
Scope: HYDRA Engineering Task A7

## Supported Shells

- Windows PowerShell
- Git Bash / MINGW64

## Python Requirement

HYDRA requires Python 3.12.

PowerShell:

```powershell
python --version
python tools/check_developer_workstation.py
```

Git Bash / MINGW64:

```bash
python --version
python tools/check_developer_workstation.py
```

## uv Usage

Preferred:

```powershell
uv sync --group dev
```

Fallback when `uv` is not directly on `PATH`:

```powershell
python -m uv sync --group dev
python -m uv run pytest
```

The same fallback works in Git Bash / MINGW64:

```bash
python -m uv sync --group dev
python -m uv run pytest
```

## Missing make

If `make` is unavailable on Windows, use direct commands instead of Makefile
targets:

```powershell
python tools/check_developer_workstation.py
python tools/local_verify.py
```

## Missing Docker

Docker is optional locally. If Docker is unavailable:

- you may skip local image build verification
- you may still run the Python quality gates and local API checks
- GitHub Actions is the authoritative Docker validation path

## Explicit Non-Goals

- no production deployment
- no live trading
- no exchange execution
- no exchange credentials
- no real-money operations
