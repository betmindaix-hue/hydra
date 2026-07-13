# Shutdown Runbook

Date: 2026-07-13
Scope: HYDRA Engineering Task A6

## Goal

Stop HYDRA safely in local and shared development environments without implying a
production deployment model.

## API Shutdown

If HYDRA is running in the foreground:

```powershell
Ctrl+C
```

If HYDRA is running under a local process manager, stop that process using the
host-appropriate command and confirm the port is no longer listening.

## Dependency Shutdown

Stop local infrastructure after the API is no longer serving traffic:

```powershell
docker compose stop postgres redis
```

If you want to remove the containers entirely:

```powershell
docker compose down
```

## Post-Shutdown Validation

- confirm the API no longer responds on `http://127.0.0.1:8000/health`
- confirm no local migration is running
- confirm no operational command is waiting for a stale database connection

## Non-Goals

- production deployment shutdown automation
- live trading shutdown procedures
- exchange execution shutdown procedures
