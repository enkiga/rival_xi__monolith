# Installation

This guide runs the React frontend on the host and the FastAPI backend plus Redis through Docker Compose. PostgreSQL is deliberately external to the Compose stack.

## Prerequisites

- Git
- Docker Engine with Compose v2, or Docker Desktop
- PostgreSQL reachable from both the host and the backend container
- Python 3.12 and [uv](https://docs.astral.sh/uv/) for direct backend development
- [Bun](https://bun.sh/) for the frontend lockfile and scripts
- A configured Brevo sender and API key to complete email sign-in

The repository pins Python 3.12 in `backend/.python-version`. It does not pin a Bun version.

## 1. Clone and configure

```sh
git clone <repository-url>
cd rivalxi__monolith
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

Edit `backend/.env` at minimum:

```dotenv
DATABASE_URL=postgresql+asyncpg://rivalxi:change-me@localhost:5432/rivalxi
DOCKER_DATABASE_URL=postgresql+asyncpg://rivalxi:change-me@host.docker.internal:5432/rivalxi
AUTH_OTP_SECRET=replace-with-a-generated-secret
BREVO_API_KEY=your_api_key_here
BREVO_SENDER_EMAIL=no-reply@yourdomain.example
AUTH_COOKIE_SECURE=false
```

Generate the authentication secret with:

```sh
python3 -c "import secrets; print(secrets.token_hex(32))"
```

Set the frontend API origin in `frontend/.env`:

```dotenv
VITE_API_URL=http://localhost:8000
```

See [Configuration](configuration.md) for every setting and [Integrations](integrations.md) for service setup.

## 2. Prepare PostgreSQL

Create the database and credentials represented by `DATABASE_URL`. The application does not create a PostgreSQL server or database for you.

For Docker Compose, use `DOCKER_DATABASE_URL` when PostgreSQL runs on the host. `host.docker.internal` is added through `host-gateway` in development. PostgreSQL must listen on an interface available to Docker and permit the Docker subnet. If the same database hostname is reachable from the host and container, omit `DOCKER_DATABASE_URL` and use `DATABASE_URL` alone.

Use a URL with the asyncpg driver:

```text
postgresql+asyncpg://user:password@hostname:5432/database
```

## 3. Start the backend and Redis

Run all Compose commands from the repository root:

```sh
docker compose --env-file backend/.env -f compose.yaml -f compose.dev.yaml build --pull
docker compose --env-file backend/.env -f compose.yaml -f compose.dev.yaml run --rm --no-deps backend alembic upgrade head
docker compose --env-file backend/.env -f compose.yaml -f compose.dev.yaml up -d --wait
```

Backend changes under `backend/app` reload automatically. Rebuild after changing `backend/pyproject.toml` or `backend/uv.lock`.

## 4. Start the frontend

In another terminal:

```sh
bun install --cwd frontend --frozen-lockfile
bun run --cwd frontend dev
```

Open `http://localhost:5173`. The API documentation is at `http://localhost:8000/docs`.

## 5. Verify the installation

```sh
curl http://localhost:8000/api/v1/health
curl http://localhost:8000/api/v1/health/db
curl http://localhost:8000/api/v1/health/redis
docker compose --env-file backend/.env -f compose.yaml -f compose.dev.yaml exec redis redis-cli ping
```

The health responses should report `ok`; Redis should return `PONG`. Requesting an OTP through the UI verifies the Brevo integration.

## Direct backend development

Install locked dependencies and run migrations from the repository root:

```sh
uv sync --directory backend --locked
uv run --directory backend alembic upgrade head
uv run --directory backend uvicorn app.main:app --reload
```

Run Redis separately and keep `REDIS_URL=redis://localhost:6379` in `backend/.env`. Settings load that file by its location, so these commands also work when invoked from `backend/` without `--directory`.

## Common problems

- **Compose cannot find the environment file:** run the commands from the repository root, or change root-relative paths to `../...` when working inside `backend/`.
- **Database connection fails in Docker:** `localhost` inside the backend container is the container itself. Use `host.docker.internal` or a network-reachable database hostname.
- **OTP request returns 503:** configure an active Brevo API key and verified sender, then restart the backend.
- **The browser rejects API calls:** `VITE_API_URL` must point to the API origin and that frontend origin must appear in `CORS_ALLOWED_ORIGINS`.
- **Authentication succeeds but the cookie is absent locally:** set `AUTH_COOKIE_SECURE=false` for HTTP development. Use `true` only behind HTTPS.
- **Frontend environment validation fails:** `VITE_API_URL` is required and must be a complete URL.

For test commands, see [Testing](testing.md).
