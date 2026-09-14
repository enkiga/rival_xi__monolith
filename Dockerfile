# syntax=docker/dockerfile:1
FROM ghcr.io/astral-sh/uv:0.12.11 AS uv

FROM python:3.12-slim-bookworm AS dependencies
COPY --from=uv /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/opt/venv
WORKDIR /build
COPY backend/pyproject.toml backend/uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-install-project

FROM python:3.12-slim-bookworm AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"
RUN groupadd --gid 10001 app \
    && useradd --uid 10001 --gid app --no-create-home app
WORKDIR /app
COPY --from=dependencies /opt/venv /opt/venv
COPY backend/app ./app
COPY backend/alembic ./alembic
COPY backend/alembic.ini ./alembic.ini
USER app
EXPOSE 8000
# A single worker prevents duplicate instances of the in-process scheduler.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
