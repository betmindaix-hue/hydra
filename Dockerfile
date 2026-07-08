FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_PROJECT_ENVIRONMENT=/opt/venv
ENV PATH="/opt/venv/bin:${PATH}"

WORKDIR /app

COPY pyproject.toml README.md .python-version ./
COPY alembic.ini ./
COPY alembic ./alembic
COPY src ./src

RUN uv sync --no-dev

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "hydra.main:app", "--host", "0.0.0.0", "--port", "8000"]

