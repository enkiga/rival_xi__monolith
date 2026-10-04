# Configuration

Backend settings live in `backend/.env`; direct runs load that file automatically. Docker Compose loads the file named by `BACKEND_ENV_FILE` and overrides container-specific database and Redis addresses. Exported environment variables take precedence.

Never commit real credentials. `backend/.env*` and `frontend/.env*` are ignored, while their `.env.example` templates are tracked.

## Backend application settings

| Variable | Required | Default/example | Purpose |
|---|---:|---|---|
| `DATABASE_URL` | Yes | `postgresql+asyncpg://...` | PostgreSQL connection used by direct backend runs. |
| `REDIS_URL` | Yes | `redis://localhost:6379` | Cache, request pacing, and authentication rate limits. Compose replaces it with `redis://redis:6379/0`. |
| `AUTH_OTP_SECRET` | Yes | generated random hex | HMAC secret for stored OTP hashes. Keep stable across restarts. |
| `GAMEWEEK_SYNC_INTERVAL_MINUTES` | Yes | `5` | Interval for live gameweek synchronization. |
| `CORS_ALLOWED_ORIGINS` | No | local Vite origins | Comma-separated browser origins; credentials require explicit origins. |
| `FRONTEND_BASE_URL` | No | `http://localhost:5173` | Builds invitation links and email asset/action URLs. |
| `FPL_REQUEST_INTERVAL_MS` | No | `2000` | Minimum Redis-coordinated gap between uncached official FPL requests. |
| `FPL_MAX_RETRIES` | No | `3` | Retries for transient official FPL responses. |
| `FPL_BOOTSTRAP_CACHE_TTL` | No | `300` | Bootstrap metadata cache lifetime, seconds. |
| `FPL_ENTRY_CACHE_TTL` | No | `600` | Manager entry cache lifetime, seconds. |
| `FPL_LIVE_CACHE_TTL` | No | `120` | Live event data cache lifetime, seconds. |
| `FPL_PICKS_CACHE_TTL` | No | `120` | Manager picks cache lifetime, seconds. |
| `LIVE_GAMEWEEK_CACHE_TTL` | No | `30` | RivalXI live result response cache lifetime, seconds. |
| `FINAL_GAMEWEEK_CACHE_TTL` | No | `86400` | RivalXI final result response cache lifetime, seconds. |
| `AUTH_OTP_TTL_MINUTES` | No | `10` | OTP validity. |
| `AUTH_OTP_MAX_ATTEMPTS` | No | `5` | Verification attempts per challenge. |
| `AUTH_OTP_RESEND_COOLDOWN_SECONDS` | No | `60` | Minimum delay before issuing another OTP. |
| `AUTH_SESSION_TTL_DAYS` | No | `30` | Session and cookie lifetime. |
| `AUTH_SESSION_COOKIE_NAME` | No | `rivalxi_session` | HTTP-only session cookie name. |
| `AUTH_COOKIE_SECURE` | No | application default `true` | Require HTTPS for the session cookie; the example sets `false` for local HTTP. |
| `AUTH_RATE_LIMIT_WINDOW_SECONDS` | No | `900` | Fixed authentication rate-limit window. |
| `AUTH_OTP_REQUEST_EMAIL_LIMIT` | No | `5` | OTP requests per email per window. |
| `AUTH_OTP_REQUEST_IP_LIMIT` | No | `20` | OTP requests per IP per window. |
| `AUTH_OTP_VERIFY_EMAIL_LIMIT` | No | `10` | OTP verification attempts per email per window. |
| `AUTH_OTP_VERIFY_IP_LIMIT` | No | `30` | OTP verification attempts per IP per window. |
| `BREVO_API_KEY` | For sign-in | `your_api_key_here` | Brevo v3 API credential. |
| `BREVO_SENDER_EMAIL` | For sign-in | `no-reply@...` | Verified Brevo sender. |
| `BREVO_SENDER_NAME` | No | `RivalXI` | Display name for outgoing mail. |
| `BREVO_API_BASE_URL` | No | `https://api.brevo.com` | Brevo API origin. |
| `BREVO_TIMEOUT_SECONDS` | No | `10` | Outbound Brevo timeout. |

Brevo fields are optional at settings-validation time, but OTP delivery fails without the key and sender, so a user cannot complete normal sign-in.

## Compose and server settings

These values are consumed by Compose or Uvicorn, not by the `Settings` model.

| Variable | Required | Default/example | Purpose |
|---|---:|---|---|
| `BACKEND_ENV_FILE` | No | `./backend/.env` | Runtime environment file loaded by Compose. |
| `DOCKER_DATABASE_URL` | No | `postgresql+asyncpg://...@host.docker.internal/...` | Container-only override for `DATABASE_URL`. |
| `BACKEND_BIND_ADDRESS` | No | `127.0.0.1` | Host address on which Compose publishes the API. |
| `BACKEND_PORT` | No | dev `8000`, prod `8001` | Published host port. |
| `FORWARDED_ALLOW_IPS` | No | `127.0.0.1` | Trusted proxy addresses passed to Uvicorn by deployment configuration. It is currently documented in the template but not wired into the Compose command. |

## Frontend setting

| Variable | Required | Example | Purpose |
|---|---:|---|---|
| `VITE_API_URL` | Yes | `http://localhost:8000` | API origin prepended to generated client paths. It is validated as a URL at startup. |

Vite exposes `VITE_*` values to browser code. Do not place secrets in the frontend environment.
