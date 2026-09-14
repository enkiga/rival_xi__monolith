# syntax=docker/dockerfile:1
FROM ghcr.io/astral-sh/uv:0.12.11 AS uv

FROM python:3.12-alpine3.24 AS python-base
# Apply distro security fixes published since the upstream image was built.
RUN apk upgrade --no-cache

FROM python-base AS dependencies
COPY --from=uv /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/opt/venv
WORKDIR /build
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-install-project

FROM python-base AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"
RUN addgroup -g 10001 -S app \
    && adduser -u 10001 -S -D -H -G app app
WORKDIR /app
COPY --from=dependencies /opt/venv /opt/venv
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./alembic.ini
USER app
EXPOSE 8000
# A single worker prevents duplicate instances of the in-process scheduler.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
