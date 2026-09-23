# RivalXI

Docker Compose runs the FastAPI backend and Redis. PostgreSQL is external; the
frontend will be added later.

Backend image files live in `backend/Dockerfile` and `backend/.dockerignore`.
Compose uses `backend/` as the build context, so only backend build inputs are
sent to Docker. Shared Compose files stay at the repository root because they
configure the full stack. Backend environment files and their template live in
`backend/`, leaving room for the frontend to own its environment separately.
Run Compose commands from the root.

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

The development environment file is `backend/.env`. Create it from the backend
template if it is missing:

```sh
test -f backend/.env || cp backend/.env.example backend/.env
```

Edit `backend/.env` and set `DATABASE_URL` to a real database using the
`postgresql+asyncpg://user:password@host:5432/database` format. Direct backend
runs read this file automatically, regardless of the working directory. Docker
Compose reads the same file and passes the backend's settings into the container;
the file itself is not mounted or copied into the image.

Set `AUTH_OTP_SECRET` to a long random secret in `backend/.env`;
generate one with `python3 -c "import secrets; print(secrets.token_hex(32))"`.
Keep the value stable across container restarts. Compose requires it for backend
commands, including Alembic, because migrations import the backend settings.
For local HTTP development, set `AUTH_COOKIE_SECURE=false`; use `true` with
production HTTPS.

Set `BREVO_API_KEY`, `BREVO_SENDER_EMAIL`, and optionally `BREVO_SENDER_NAME` in
the same backend environment file to enable OTP and notification email delivery.
The sender address must be registered and verified in Brevo. Compose passes the
complete file to the backend while retaining the container-specific database and
Redis overrides. Do not commit a real API key.

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
docker compose --env-file backend/.env -f compose.yaml -f compose.dev.yaml build --pull
docker compose --env-file backend/.env -f compose.yaml -f compose.dev.yaml run --rm --no-deps backend alembic upgrade head
docker compose --env-file backend/.env -f compose.yaml -f compose.dev.yaml up -d --wait
```

To stay in `backend/` instead, prefix every root file path with `../`:

```sh
docker compose --env-file .env -f ../compose.yaml -f ../compose.dev.yaml build --pull
docker compose --env-file .env -f ../compose.yaml -f ../compose.dev.yaml run --rm --no-deps backend alembic upgrade head
docker compose --env-file .env -f ../compose.yaml -f ../compose.dev.yaml up -d --wait
```

An error about a missing environment file means its path is being resolved from
the current working directory. Use the matching command set above.

- API documentation: http://localhost:8000/docs
- Application health: http://localhost:8000/api/v1/health
- Database connectivity: http://localhost:8000/api/v1/health/db
- Redis connectivity: http://localhost:8000/api/v1/health/redis

Changes under `backend/app` trigger automatic reload. Application and migration
directories are mounted read-only; the container's dependencies stay separate
from your local virtual environment. After changing `backend/pyproject.toml` or
`backend/uv.lock`, rebuild with `up -d --build --wait` using the same Compose flags.
Keep the lockfile in sync with `uv lock` when editing dependencies.

## Production

```sh
cp backend/.env.example backend/.env.prod
```

Keep `backend/.env.prod` with the backend and edit it with production credentials
and an external PostgreSQL hostname. Set `BACKEND_ENV_FILE=./backend/.env.prod`
inside it. Remove the example `DOCKER_DATABASE_URL`
override so Compose uses the production `DATABASE_URL`, or set both deliberately.
Use a separate database from development. Environment files are ignored by Git
and excluded from the image; restrict access to them on the deployment host.
They supply container environment variables at runtime, so Docker administrators
can inspect them.

```sh
docker compose --env-file backend/.env.prod -f compose.yaml -f compose.prod.yaml build --pull
docker compose --env-file backend/.env.prod -f compose.yaml -f compose.prod.yaml run --rm --no-deps backend alembic upgrade head
docker compose --env-file backend/.env.prod -f compose.yaml -f compose.prod.yaml up -d --wait
```

The production API defaults to http://127.0.0.1:8001. Put a TLS reverse proxy in
front of it for public access. `BACKEND_BIND_ADDRESS` and `BACKEND_PORT` override
the published address and port. The localhost default works with a proxy on the
Docker host; a containerized proxy needs a shared network configured separately.
Set `FORWARDED_ALLOW_IPS` to the exact IP or CIDR of that trusted proxy so Uvicorn
can supply the real client address to authentication rate limits. Keep the
loopback-only default until the proxy address is known; never use `*` while the
backend can be reached directly by untrusted clients.

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

Use `backend/.env`. With uv installed, run these commands from the repository
root:

```sh
uv run --directory backend alembic upgrade head
uv run --directory backend uvicorn app.main:app --reload
```

Settings resolve `backend/.env` relative to the settings module, so running from
`backend/` also works. Exported environment variables take precedence. Compose
and Uvicorn keys such as `BACKEND_PORT`, `DOCKER_DATABASE_URL`, and
`FORWARDED_ALLOW_IPS` are ignored by application settings. Direct runs load
`backend/.env`; production Compose selects `backend/.env.prod` explicitly.

When adding a backend setting, define it in `Settings` and document it in
`backend/.env.example`. Compose loads the complete backend environment file and
overrides only container-specific connection addresses.

## Redis

Redis is available to the backend at `redis://redis:6379/0`, supplied as
`REDIS_URL`. Compose overrides the backend file's host-side Redis URL so backend
caching can reach the Redis service over the Docker network.

Redis has no published host port and uses an internal Docker network shared only
with the backend. This configuration relies on network isolation rather than a
Redis password. It is intended for a trusted, single-host Compose deployment.
Append-only persistence writes to a separate named volume per environment.
Back up those volumes if Redis begins storing data that must be retained.

```sh
docker compose --env-file backend/.env -f compose.yaml -f compose.dev.yaml exec redis redis-cli ping
```

Expected output: `PONG`.

## Common commands

These examples target development. For production, replace `backend/.env` with
`backend/.env.prod` and `compose.dev.yaml` with `compose.prod.yaml`.

```sh
# Check service status.
docker compose --env-file backend/.env -f compose.yaml -f compose.dev.yaml ps

# Follow backend logs.
docker compose --env-file backend/.env -f compose.yaml -f compose.dev.yaml logs -f backend

# Stop and remove containers; preserve Redis data.
docker compose --env-file backend/.env -f compose.yaml -f compose.dev.yaml down

# Validate configuration without starting services.
docker compose --env-file backend/.env -f compose.yaml -f compose.dev.yaml config --quiet
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
docker compose --env-file backend/.env.prod -f compose.yaml -f compose.prod.yaml build --pull --no-cache backend
docker scout cves --only-severity critical,high rivalxi-prod-backend
```

Dockerfile editor warnings describe the upstream `FROM` image. They can still
show findings fixed by later package updates; scan the built backend image to
check what will actually run. A clean scan is a point-in-time result, so repeat
it when rebuilding and deploying.

Build conventions follow the [Docker build guidance](https://docs.docker.com/build/building/best-practices/)
and [uv Docker integration guide](https://docs.astral.sh/uv/guides/integration/docker/).
