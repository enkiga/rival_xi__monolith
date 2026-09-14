# RivalXI

Docker Compose runs the FastAPI backend and Redis. PostgreSQL is external; the
frontend will be added later.

Backend image files live in `backend/Dockerfile` and `backend/.dockerignore`.
Compose uses `backend/` as the build context, so only backend build inputs are
sent to Docker. The shared `compose.yaml`, development and production Compose
files, and Docker environment template stay at the repository root because they
configure the full stack, including Redis. Run Compose commands from the root.

## Prerequisites

- Docker Engine with Docker Compose v2 or newer, or Docker Desktop (running).
- An accessible PostgreSQL database and its connection URL.
- Run the commands below from the repository root.

## Development

Run Docker Compose from the **repository root**, not from `backend/`. If your
terminal is currently in `backend/`, move up first:

```sh
cd ..
```

The development environment file is now **root `.env`**, not `.env.dev` or
`backend/.env`. If your existing backend configuration was migrated, root `.env`
already exists. Only create it from the template if it is missing:

```sh
test -f .env || cp .env.example .env
```

Edit the root `.env` and set `DATABASE_URL` to a real database using the
`postgresql+asyncpg://user:password@host:5432/database` format. Direct backend
runs read this file automatically, regardless of the working directory. Docker
Compose reads the same file and passes the backend's settings into the container;
the file itself is not mounted or copied into the image.

For PostgreSQL running on your computer, use `localhost` in `DATABASE_URL` for
direct runs and set `DOCKER_DATABASE_URL` with the same credentials and database
but `host.docker.internal` as the hostname. Compose passes that override as the
container's `DATABASE_URL`. For a database hostname reachable from both the host
and containers, omit `DOCKER_DATABASE_URL` and use only `DATABASE_URL`. On Linux,
Compose adds this hostname through `host-gateway`; PostgreSQL must listen on an
interface reachable from Docker and allow connections from the Docker subnet.
`localhost` inside a container refers to that container.

Build, apply migrations, and start:

```sh
docker compose --env-file .env -f compose.yaml -f compose.dev.yaml build --pull
docker compose --env-file .env -f compose.yaml -f compose.dev.yaml run --rm --no-deps backend alembic upgrade head
docker compose --env-file .env -f compose.yaml -f compose.dev.yaml up -d --wait
```

To stay in `backend/` instead, prefix every root file path with `../`:

```sh
docker compose --env-file ../.env -f ../compose.yaml -f ../compose.dev.yaml build --pull
docker compose --env-file ../.env -f ../compose.yaml -f ../compose.dev.yaml run --rm --no-deps backend alembic upgrade head
docker compose --env-file ../.env -f ../compose.yaml -f ../compose.dev.yaml up -d --wait
```

An error such as `couldn't find env file: .../backend/.env.dev` means the command
uses the old filename and resolves it from the backend directory. Use one of the
command sets above; do not create another environment file inside `backend/`.

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

Keep `.env.prod` at the repository root and edit it with production credentials
and an external PostgreSQL hostname. Remove the example `DOCKER_DATABASE_URL`
override so Compose uses the production `DATABASE_URL`, or set both deliberately.
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

## Running the backend directly

Use the same root `.env`; do not create environment files inside `backend/`.
With uv installed, run these commands from the repository root:

```sh
uv run --directory backend alembic upgrade head
uv run --directory backend uvicorn app.main:app --reload
```

Settings resolve the root `.env` relative to the settings module, so running from
`backend/` also works. Exported environment variables take precedence over the
file, and Compose-only keys such as `BACKEND_PORT` and `DOCKER_DATABASE_URL` are
ignored by backend settings. Direct runs load `.env`, not `.env.prod`; the latter
is an optional root file selected explicitly by the production Compose commands.
On a dedicated production host, you can instead keep its configuration in root
`.env` and change the commands to `--env-file .env`.

When adding a backend setting, define it in `Settings`, document it in the root
`.env.example`, and add it to the backend's `environment` mapping in `compose.yaml`.

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
docker compose --env-file .env -f compose.yaml -f compose.dev.yaml exec redis redis-cli ping
```

Expected output: `PONG`.

## Common commands

These examples target development. For production, replace `.env` with
`.env.prod` and `compose.dev.yaml` with `compose.prod.yaml`.

```sh
# Check service status.
docker compose --env-file .env -f compose.yaml -f compose.dev.yaml ps

# Follow backend logs.
docker compose --env-file .env -f compose.yaml -f compose.dev.yaml logs -f backend

# Stop and remove containers; preserve Redis data.
docker compose --env-file .env -f compose.yaml -f compose.dev.yaml down

# Validate configuration without starting services.
docker compose --env-file .env -f compose.yaml -f compose.dev.yaml config --quiet
```

Adding `--volumes` to `down` deletes that instance's Redis data. PostgreSQL remains
external and is unaffected. Use both Compose files in every command: `compose.yaml`
contains shared services, while the second file selects the environment.

The image installs locked production dependencies with uv in a separate build
stage. Python and Redis use explicit release-series tags, and uv uses an exact
version; tags can receive upstream updates. Rebuild regularly with `--pull` and
validate before deployment. For deployments requiring immutable base images, pin
reviewed image digests and maintain an update process.

The backend uses Python 3.12 on Alpine 3.24, with distro package updates applied
in a shared base stage for both dependency installation and runtime. Alpine uses
musl rather than glibc; when adding native Python dependencies, verify their
Linux wheels support this base. To pick up new security fixes even when Docker
has cached the package-update layer, rebuild and scan the resulting image:

```sh
docker compose --env-file .env.prod -f compose.yaml -f compose.prod.yaml build --pull --no-cache backend
docker scout cves --only-severity critical,high rivalxi-prod-backend
```

Dockerfile editor warnings describe the upstream `FROM` image. They can still
show findings fixed by later package updates; scan the built backend image to
check what will actually run. A clean scan is a point-in-time result, so repeat
it when rebuilding and deploying.

Build conventions follow the [Docker build guidance](https://docs.docker.com/build/building/best-practices/)
and [uv Docker integration guide](https://docs.astral.sh/uv/guides/integration/docker/).
