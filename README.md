# RivalXI

Docker Compose runs the FastAPI backend and Redis. PostgreSQL is external; the
frontend will be added later.

## Prerequisites

- Docker Engine with Docker Compose v2 or newer, or Docker Desktop (running).
- An accessible PostgreSQL database and its connection URL.
- Run the commands below from the repository root.

## Development

Create your local configuration:

```sh
cp .env.example .env.dev
```

Edit `.env.dev` and set `DATABASE_URL` to a real database using the
`postgresql+asyncpg://user:password@host:5432/database` format. For PostgreSQL
running on your computer, use `host.docker.internal` as the hostname. On Linux,
Compose adds this hostname through `host-gateway`; PostgreSQL must listen on an
interface reachable from Docker and allow connections from the Docker subnet.
`localhost` inside a container refers to that container.

Build, apply migrations, and start:

```sh
docker compose --env-file .env.dev -f compose.yaml -f compose.dev.yaml build --pull
docker compose --env-file .env.dev -f compose.yaml -f compose.dev.yaml run --rm --no-deps backend alembic upgrade head
docker compose --env-file .env.dev -f compose.yaml -f compose.dev.yaml up -d --wait
```

- API documentation: http://localhost:8000/docs
- Application health: http://localhost:8000/api/v1/health
- Database connectivity: http://localhost:8000/api/v1/health/db

Changes under `backend/app` trigger automatic reload. Application and migration
directories are mounted read-only; the container's dependencies stay separate
from your local virtual environment. After changing `backend/pyproject.toml` or
`backend/uv.lock`, rebuild with `up -d --build --wait` using the same Compose flags.
Keep the lockfile in sync with `uv lock` when editing dependencies.

## Production

```sh
cp .env.example .env.prod
```

Edit `.env.prod` with production credentials and an external PostgreSQL hostname.
Use a separate database from development. Environment files are ignored by Git
and excluded from the image; restrict access to them on the deployment host.
They supply container environment variables at runtime, so Docker administrators
can inspect them.

```sh
docker compose --env-file .env.prod -f compose.yaml -f compose.prod.yaml build --pull
docker compose --env-file .env.prod -f compose.yaml -f compose.prod.yaml run --rm --no-deps backend alembic upgrade head
docker compose --env-file .env.prod -f compose.yaml -f compose.prod.yaml up -d --wait
```

The production API defaults to http://127.0.0.1:8001. Put a TLS reverse proxy in
front of it for public access. `BACKEND_BIND_ADDRESS` and `BACKEND_PORT` override
the published address and port. The localhost default works with a proxy on the
Docker host; a containerized proxy needs a shared network configured separately.

Production runs the image's bundled source without reload or source mounts,
with a non-root backend user, a read-only backend filesystem, temporary `/tmp`
storage, dropped backend capabilities, bounded logs, and automatic restart after
process exit or Docker restart. Health checks report unhealthy containers; Docker
Compose does not restart a container solely because its health check fails.

Migrations are an explicit deployment step, not an automatic startup action.
For updates, assess migration compatibility with the running application and back
up your database before applying schema changes.

The backend currently starts its gameweek scheduler inside the API process.
Keep **one backend container with one worker** per environment to avoid duplicate
scheduled jobs. Dev and prod have separate Compose project names, ports, networks,
and Redis volumes, so they can run together when given separate databases.

## Redis

Redis is available to the backend at `redis://redis:6379/0`, supplied as
`REDIS_URL`. This Docker setup provisions Redis; application caching or job
integration still needs to consume that variable. The existing settings class
does not yet define a Redis setting.

Redis has no published host port and uses an internal Docker network shared only
with the backend. This configuration relies on network isolation rather than a
Redis password. It is intended for a trusted, single-host Compose deployment.
Append-only persistence writes to a separate named volume per environment.
Back up those volumes if Redis begins storing data that must be retained.

```sh
docker compose --env-file .env.dev -f compose.yaml -f compose.dev.yaml exec redis redis-cli ping
```

Expected output: `PONG`.

## Common commands

These examples target development. For production, replace `.env.dev` with
`.env.prod` and `compose.dev.yaml` with `compose.prod.yaml`.

```sh
# Check service status.
docker compose --env-file .env.dev -f compose.yaml -f compose.dev.yaml ps

# Follow backend logs.
docker compose --env-file .env.dev -f compose.yaml -f compose.dev.yaml logs -f backend

# Stop and remove containers; preserve Redis data.
docker compose --env-file .env.dev -f compose.yaml -f compose.dev.yaml down

# Validate configuration without starting services.
docker compose --env-file .env.dev -f compose.yaml -f compose.dev.yaml config --quiet
```

Adding `--volumes` to `down` deletes that instance's Redis data. PostgreSQL remains
external and is unaffected. Use both Compose files in every command: `compose.yaml`
contains shared services, while the second file selects the environment.

The image installs locked production dependencies with uv in a separate build
stage. Python and Redis use explicit release-series tags, and uv uses an exact
version; tags can receive upstream updates. Rebuild regularly with `--pull` and
validate before deployment. For deployments requiring immutable base images, pin
reviewed image digests and maintain an update process.

Build conventions follow the [Docker build guidance](https://docs.docker.com/build/building/best-practices/)
and [uv Docker integration guide](https://docs.astral.sh/uv/guides/integration/docker/).
