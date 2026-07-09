UV ?= uv
PYTHON ?= $(UV) run python

.PHONY: test lint format run docker alembic-check

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

