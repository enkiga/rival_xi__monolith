# Deployment

The supported repository-level deployment artifact is Docker Compose for one FastAPI container and one Redis container. PostgreSQL, TLS termination, and frontend hosting must be provided separately.

## Prepare the environment

```sh
cp backend/.env.example backend/.env.prod
```

Set production values, including:

```dotenv
BACKEND_ENV_FILE=./backend/.env.prod
DATABASE_URL=postgresql+asyncpg://user:password@database-host:5432/rivalxi
AUTH_OTP_SECRET=replace-with-a-production-secret
AUTH_COOKIE_SECURE=true
FRONTEND_BASE_URL=https://app.example.com
CORS_ALLOWED_ORIGINS=https://app.example.com
BREVO_API_KEY=your_api_key_here
BREVO_SENDER_EMAIL=no-reply@example.com
```

Remove the example `DOCKER_DATABASE_URL` unless an intentional container-specific override is needed. Use a production database separate from development. Environment files are excluded from the image and ignored by Git, but container administrators can inspect runtime environment variables.

## Build, migrate, and start

From the repository root:

```sh
docker compose --env-file backend/.env.prod -f compose.yaml -f compose.prod.yaml build --pull
docker compose --env-file backend/.env.prod -f compose.yaml -f compose.prod.yaml run --rm --no-deps backend alembic upgrade head
docker compose --env-file backend/.env.prod -f compose.yaml -f compose.prod.yaml up -d --wait
```

Migrations are an explicit deployment step. Review migration compatibility and back up PostgreSQL before applying schema changes.

The production API is published on `127.0.0.1:8001` by default. Override `BACKEND_BIND_ADDRESS` and `BACKEND_PORT` deliberately. Put an HTTPS reverse proxy in front of the API; a containerized proxy needs a shared Docker network not supplied here.

The environment template contains `FORWARDED_ALLOW_IPS`, but the current Compose/Uvicorn commands do not pass `--proxy-headers` or `--forwarded-allow-ips`. Do not assume forwarded client addresses affect authentication rate limits until the deployment command is explicitly wired and tested.

## Runtime characteristics

- The backend runs as a non-root user with a read-only filesystem, temporary `/tmp`, dropped Linux capabilities, bounded local logs, and `unless-stopped` restart behavior.
- Redis is internal to the backend network, has no password or published host port, and persists append-only data in a named volume.
- Docker health checks report status but do not restart a process solely because it becomes unhealthy.
- The backend image contains the application and migrations; production does not mount source or enable reload.
- The API process owns APScheduler. Keep exactly one backend container and one Uvicorn worker per environment to avoid duplicate sync and reminder jobs.

## Frontend and database

No frontend image or hosting configuration is checked in. Build the static frontend with `bun run --cwd frontend build`, host the resulting Vite output separately, and set `VITE_API_URL` at build time to the public API origin. Configure the API's CORS origin and secure cookie behavior to match.

PostgreSQL is also external. Provision backups, access controls, TLS, monitoring, and retention according to the chosen provider; this repository does not define them.

## Operations

```sh
# Status
docker compose --env-file backend/.env.prod -f compose.yaml -f compose.prod.yaml ps

# Backend logs
docker compose --env-file backend/.env.prod -f compose.yaml -f compose.prod.yaml logs -f backend

# Stop containers while preserving the Redis volume
docker compose --env-file backend/.env.prod -f compose.yaml -f compose.prod.yaml down
```

Adding `--volumes` to `down` deletes that environment's Redis data; it does not affect external PostgreSQL.

The backend base is Python 3.12 on Alpine 3.24. Rebuild with pulled base images and validate the result before deployment. Native dependencies must support musl-based Linux.
