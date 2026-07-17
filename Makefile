UV ?= uv
PYTHON ?= $(UV) run python
SYSTEM_PYTHON ?= python

.PHONY: test lint format run docker alembic-check ops-check workstation-check local-verify

test:
	$(UV) run pytest

lint:
	$(UV) run ruff check .
	$(UV) run black --check .
	$(UV) run mypy src tests tools

format:
	$(UV) run ruff check . --fix
	$(UV) run black .

run:
	$(UV) run uvicorn hydra.main:app --reload

docker:
	docker build -t hydra .

alembic-check:
	$(PYTHON) tools/validate_alembic.py

ops-check:
	$(PYTHON) tools/check_operations_readiness.py

workstation-check:
	$(SYSTEM_PYTHON) tools/check_developer_workstation.py

local-verify:
	$(SYSTEM_PYTHON) tools/local_verify.py
