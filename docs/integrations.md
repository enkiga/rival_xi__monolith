# External integrations

All third-party calls are made by the backend. Do not expose service credentials in `frontend/.env`.

## Official Fantasy Premier League data

RivalXI reads Fantasy Premier League web endpoints for bootstrap metadata, manager entries, gameweek picks, and live player points. This data validates claimed teams and drives scoring and squad views. Kit images use the static shirt asset pattern isolated in `app/integrations/fpl/kit_assets.py`.

No credential is required. Redis coordinates a minimum interval between uncached requests, and transient failures are retried. Configure pacing, retries, and cache TTLs with the `FPL_*` variables in [Configuration](configuration.md).

Verification:

1. Start the API and Redis.
2. Sign in and preview a valid FPL entry during onboarding.
3. For an authenticated session, `GET /api/v1/fpl/teams/{entry_id}` should return the manager summary.

These endpoints are not a supported public developer API contract. The integration can break when FPL changes response fields or paths; adapters and response validation limit the impact but do not remove that risk.

## FPL Rivals

FPL Rivals supplies manager/team name search during onboarding through `https://api.fplrivals.org/api/v1/search`. It returns candidate entry IDs only. RivalXI never uses it as the source of truth for account ownership, picks, or scores.

No credential or environment setting is currently required. A failed or malformed response sets `search_available=false`, allowing the user to enter an FPL team ID or URL manually.

Verification: after authentication, request `GET /api/v1/onboarding/fpl/search?q=<three-or-more-characters>`. A healthy provider returns normalized results with `entry_id`, `manager_name`, and `team_name`.

## Brevo transactional email

Brevo's REST API delivers sign-in codes and membership approval/rejection email. The project uses direct HTTP calls, not SMTP or the Brevo SDK.

### Account setup

1. In Brevo, authenticate the sending domain under **Settings → Senders, Domains & Dedicated IPs**.
2. Create and verify the sender address.
3. Create a v3 API key under **Settings → SMTP & API → API Keys**.
4. Ensure transactional sending is active and quota is available.

Configure development in `backend/.env` and production in the selected backend environment file:

```dotenv
BREVO_API_KEY=your_api_key_here
BREVO_SENDER_EMAIL=no-reply@yourdomain.example
BREVO_SENDER_NAME=RivalXI
FRONTEND_BASE_URL=https://app.yourdomain.example
```

`FRONTEND_BASE_URL` is used for email assets, league actions, and invitation links. The sender must match a sender Brevo permits.

Verification:

```sh
curl -i -X POST http://localhost:8000/api/v1/auth/otp/request \
  -H 'Content-Type: application/json' \
  --data '{"email":"your-inbox@example.com"}'
```

A successful request returns `202`. Confirm delivery and inspect **Transactional → Logs** in Brevo; OTP messages use the `authentication` tag and membership messages use `notification`.

If the API returns `503`, verify the key, sender, account activation, quota, and network access to `https://api.brevo.com`. OTP delivery failure invalidates the new challenge. Membership email failure is logged without removing the in-app notification.

## PostgreSQL and Redis

PostgreSQL is required durable infrastructure but is not included in Compose. Any provider is acceptable if it supports the schema and an asyncpg connection URL.

Redis 7.4 is included in Compose with append-only persistence and an internal-only network. It has no password or host port in that topology; isolation relies on the Docker network. Direct backend development must supply a reachable Redis separately.
