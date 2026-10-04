# Testing and verification

## Backend tests

The backend suite uses the Python standard library's `unittest`, including `IsolatedAsyncioTestCase` and mocks. Tests focus on service behavior and route/error contracts; they do not require a running PostgreSQL, Redis, Brevo, or FPL service in their current form.

Install locked backend dependencies, then run from the repository root:

```sh
uv sync --directory backend --locked
uv run --directory backend python -m unittest discover -s tests -v
```

To run one module:

```sh
uv run --directory backend python -m unittest tests.test_gameweek_summary -v
```

Coverage includes authentication/authorization contracts, CORS, Brevo payloads and failure handling, FPL kit resolution, score summaries, league access/listing, notification events, and Redis degradation behavior.

## Frontend checks

There is no frontend automated test suite configured. The checked-in verification commands are the TypeScript production build and Biome check:

```sh
bun install --cwd frontend --frozen-lockfile
bun run --cwd frontend lint
bun run --cwd frontend build
```

The build runs `tsc -b` before Vite. API TypeScript types are generated from the running backend's OpenAPI schema:

```sh
bun run --cwd frontend api:generate
```

The generator configuration points to `http://localhost:8000/openapi.json`, so start the backend first. Generated API files should be reviewed because generation can update many schema modules.

## Compose validation

Validate development and production configuration without starting services:

```sh
docker compose --env-file backend/.env -f compose.yaml -f compose.dev.yaml config --quiet
docker compose --env-file backend/.env.prod -f compose.yaml -f compose.prod.yaml config --quiet
```

Runtime smoke checks are documented in [Installation](installation.md). External integrations need separate verification because the unit suite mocks them; see [Integrations](integrations.md).

## Current limitations

- No browser/component tests are configured.
- No live database migration or end-to-end test harness is checked in.
- No CI configuration is present, so these checks are not automatically enforced by this repository.
