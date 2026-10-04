# API guide

The FastAPI application serves JSON under `/api/v1`. In development, interactive OpenAPI documentation is available at `http://localhost:8000/docs` and the schema at `/openapi.json`.

## Authentication

`POST /auth/otp/verify` sets the configured HTTP-only session cookie. Browser clients must include credentials; the frontend API client does this automatically. Except for health checks and the two OTP endpoints, routes require that cookie.

Typical errors use:

```json
{ "detail": "Human-readable message" }
```

FastAPI request validation uses a structured `detail` array. Authentication rate limits return `429` and may include `Retry-After`. Upstream FPL failures generally return `502`; unavailable authentication rate limiting or email delivery returns `503`.

## Endpoint groups

All paths below are relative to `/api/v1`.

### Health

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/health` | API process health. |
| `GET` | `/health/db` | PostgreSQL query check. |
| `GET` | `/health/redis` | Redis ping check. |

### Authentication and onboarding

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/auth/otp/request` | Email a sign-in code. |
| `POST` | `/auth/otp/verify` | Verify the code and set a session. |
| `GET` | `/auth/me` | Return the user and onboarding state. |
| `POST` | `/auth/logout` | Revoke the current or all user sessions. |
| `GET` | `/onboarding/fpl/search` | Search manager candidates through FPL Rivals. |
| `POST` | `/onboarding/fpl/preview` | Validate an ID/URL through official FPL and show availability. |
| `POST` | `/onboarding/fpl/claim` | Permanently claim the validated FPL team. |

### FPL data

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/fpl/teams/{entry_id}` | Official-FPL manager summary. |
| `GET` | `/fpl/teams/{entry_id}/gameweeks/{gameweek}` | Normalized picks and gameweek score. |

### Leagues and gameweeks

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/leagues` | Create a draft league. |
| `GET` | `/leagues` | Paginate/search/sort the current user's leagues. |
| `GET` | `/leagues/{slug}` | League rules and visible members. |
| `PATCH` | `/leagues/{slug}` | Owner edit of a draft league. |
| `PATCH` | `/leagues/{slug}/activate` | Owner activation. |
| `PATCH` | `/leagues/{slug}/members/{member_id}/approve` | Approve an applicant. |
| `PATCH` | `/leagues/{slug}/members/{member_id}/reject` | Reject an applicant. |
| `POST` | `/leagues/{slug}/gameweeks/{gameweek}/sync` | Owner-triggered result synchronization. |
| `GET` | `/leagues/{slug}/gameweeks/{gameweek}/summary` | Current user/winner summary. |
| `GET` | `/leagues/{slug}/gameweeks/{gameweek}` | Ranked league results. |
| `GET` | `/leagues/{slug}/gameweeks/{gameweek}/members/{member_id}` | Member score and 15-player picks. |

`GET /leagues` supports `page`, `page_size`, `search`, `sort_by=name|created_at`, and `sort_order=asc|desc`.

### Invitations

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/leagues/{slug}/invitation-link` | Owner retrieval of the permanent invite URL. |
| `POST` | `/leagues/{slug}/invitation-link/regenerate` | Owner replacement of the invitation code. |
| `GET` | `/invitations/{token}` | Preview an invitation and membership state. |
| `POST` | `/invitations/{token}/accept` | Request league membership. |

### Notifications

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/notifications` | List notifications with `unread_only`, `limit`, and `offset`. |
| `GET` | `/notifications/unread-count` | Return the unread count. |
| `PATCH` | `/notifications/{notification_id}/read` | Mark one notification read. |
| `PATCH` | `/notifications/read-all` | Mark every notification read. |

## Access rules

- League creation and invitation acceptance require a claimed FPL account.
- League owners alone can edit/activate a league, decide memberships, manage the invite link, and manually sync results.
- Approved members can read league and gameweek data; pending users receive `403`.
- Gameweek values are limited to 1–38. Pre-start or pre-deadline requests return `409`.

For precise request and response schemas, use the generated OpenAPI documentation rather than duplicating every field here. See [Domain rules](domain-rules.md) for behavioral semantics.
