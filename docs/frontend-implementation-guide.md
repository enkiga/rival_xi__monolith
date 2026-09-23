# RivalXI frontend implementation guide

This document translates the backend currently in this repository into a frontend product and API plan. It is based on the routes, Pydantic schemas, domain enums, and service rules in `backend/app` as of 2026-09-15.

## 1. Product scope supported today

The current backend supports this core journey:

1. A visitor signs in with an email and a six-digit one-time code.
2. A newly authenticated user links one Fantasy Premier League (FPL) team.
3. The user either creates a league or opens an invitation link.
4. A league owner configures rules, creates reusable invitations, and approves or rejects applicants.
5. The owner activates the league. Draft league settings cannot be changed after activation.
6. Approved members view league gameweek standings and individual team details.
7. Users receive in-app notifications about membership decisions, rule changes, deadlines, and gameweek winners.

All application routes except the health checks and the two OTP endpoints require the `rivalxi_session` HTTP-only cookie. The frontend must not attempt to read that cookie; it should determine login state through `GET /api/v1/auth/me`.

## 2. Recommended route and screen map

| Frontend route | Screen | Access | Primary backend calls |
|---|---|---|---|
| `/` | Landing page | Public | None |
| `/sign-in` | Email sign-in | Public | `POST /auth/otp/request` |
| `/verify` | OTP verification | Public, after email submission | `POST /auth/otp/verify` |
| `/onboarding/fpl` | Link FPL team | Authenticated, onboarding required | `POST /onboarding/fpl/preview`, `POST /onboarding/fpl/claim` |
| `/dashboard` | Home / league entry point | Authenticated and onboarded | `GET /auth/me`, notifications; see backend gaps |
| `/leagues/new` | Create league | Authenticated and onboarded | `POST /leagues` |
| `/leagues/:slug` | League overview and members | Approved member | `GET /leagues/{slug}` |
| `/leagues/:slug/settings` | Draft league settings | Owner only | `GET /leagues/{slug}`, `PATCH /leagues/{slug}`, `PATCH /leagues/{slug}/activate` |
| `/leagues/:slug/members` | Member approvals | Owner only | `GET /leagues/{slug}`, approve/reject endpoints |
| `/leagues/:slug/invitations` | Invitation management | Owner only | create/list/revoke invitation endpoints |
| `/invite/:token` | Invitation preview and acceptance | Authentication and onboarding required | invitation preview/accept endpoints |
| `/leagues/:slug/gameweeks/:gameweek` | Gameweek standings | Approved member | league gameweek endpoint; owner may sync |
| `/leagues/:slug/gameweeks/:gameweek/members/:memberId` | Member gameweek detail | Approved member | member gameweek endpoint |
| `/notifications` | Notification inbox | Authenticated | notification list/read endpoints |
| `/account` | Account and sign-out | Authenticated | `GET /auth/me`, `POST /auth/logout` |

The landing page can be implemented immediately without backend data. The dashboard cannot show a reliable list of the current user's leagues until the missing league-list endpoint described in section 10 is added.

## 3. Global user flow and route guards

On application startup, call `GET /api/v1/auth/me` with credentials included.

```text
GET /auth/me
  ├─ 401 → anonymous → public pages or /sign-in
  ├─ 200 + onboarding_required=true → /onboarding/fpl
  └─ 200 + onboarding_required=false → authenticated application
```

Recommended guard behavior:

- Public-only routes (`/sign-in`, `/verify`) redirect an authenticated, onboarded user to `/dashboard`.
- Any protected route redirects a user receiving `401` to `/sign-in` and stores the intended path.
- Any authenticated user with `onboarding_required: true` is sent to `/onboarding/fpl`. Preserve an invitation token or intended path so they can resume afterward.
- A `403` from a league resource is not equivalent to signed out. Render the pending/unauthorized state described by the response `detail`.
- Role-based controls are inferred from the league member whose `fpl_entry_id` matches `auth.me.fpl_account.fpl_entry_id`. Show owner controls only if that member has `role: "OWNER"`. This works, but an explicit `viewer` field from the backend would be safer.

All browser requests should use the API base URL plus `/api/v1` and include cookies:

```ts
fetch(`${API_BASE_URL}/api/v1/auth/me`, {
  credentials: "include",
});
```

For non-2xx responses, FastAPI normally returns `{ "detail": "..." }`. Validation failures return a structured `detail` array. The shared API client should support both forms.

## 4. Authentication screens

### 4.1 Email sign-in (`/sign-in`)

Form:

| Field | Type | Client validation |
|---|---|---|
| Email | Email input | Required and valid email syntax |

Submit `POST /api/v1/auth/otp/request`:

```json
{ "email": "manager@example.com" }
```

Successful response is `202`:

```json
{
  "message": "If the email address is valid, a verification code has been sent.",
  "expires_in_seconds": 600
}
```

Store the email only in short-lived frontend state or session storage, then navigate to `/verify`. Keep the neutral success message to avoid exposing whether an account exists.

Important states:

- Disable submit while pending.
- On `429`, show `detail` and use the `Retry-After` response header to disable resend with a countdown.
- On `503`, show that email delivery or authentication is temporarily unavailable, with a retry action.

### 4.2 Verify OTP (`/verify`)

Form:

| Field | Type | Client validation |
|---|---|---|
| Code | Numeric/OTP input | Exactly six digits (`^\d{6}$`) |

Submit `POST /api/v1/auth/otp/verify`:

```json
{
  "email": "manager@example.com",
  "code": "123456"
}
```

The response sets the HTTP-only session cookie and returns `{ "user": AuthUser }`. Send requests with `credentials: "include"`.

There is no separate registration flow: successful OTP verification automatically creates a user when the normalized email does not already exist.

Behavior:

- `401 Invalid verification code`: keep the form and allow retry.
- `401 Verification code has expired`: offer “Request a new code.”
- `429 Maximum verification attempts exceeded`: require a new code.
- `429` rate limit: honor `Retry-After` when present.
- On success, resume the preserved invite/intended route; otherwise go to onboarding when `user.onboarding_required`, or `/dashboard` when onboarding is complete.

### 4.3 Account and logout (`/account`)

Display email and linked FPL account from `GET /auth/me`. Provide:

- “Sign out” → `POST /auth/logout` with `{ "all_sessions": false }`.
- “Sign out all devices” → same endpoint with `{ "all_sessions": true }` and a confirmation dialog.

After success, clear all cached protected data and navigate to `/sign-in`.

## 5. FPL onboarding (`/onboarding/fpl`)

This is a two-step lookup-and-confirm flow. The backend accepts either a positive numeric entry ID or an FPL URL containing `/entry/{id}`.

### Step 1: Find team

Form:

| Field | Type | Client validation |
|---|---|---|
| FPL team URL or entry ID | Text | Required, 1–500 characters |

Submit `POST /api/v1/onboarding/fpl/preview`:

```json
{ "reference": "https://fantasy.premierleague.com/entry/123456/event/4" }
```

Render the returned `team_name`, `manager_name`, and `fpl_entry_id` as a confirmation card.

- If `available` is false, disable confirmation and explain that the team is linked to another RivalXI account.
- If `linked_to_current_user` is true, confirmation is safe and idempotent.
- `422`: invalid entry ID or URL.
- `404`: FPL team not found.
- `502`: FPL is temporarily unavailable; preserve the input and allow retry.

### Step 2: Confirm team

Submit `POST /api/v1/onboarding/fpl/claim` with the same `reference`. On success, refresh `GET /auth/me` and resume a saved invitation or intended route.

The current API deliberately supports one immutable FPL account per RivalXI user. Do not display a “change FPL team” action because no unlink/replace endpoint exists.

## 6. League creation and management

### 6.1 Create league (`/leagues/new`)

The user must have linked an FPL account. Form:

| Field | Control | Rules |
|---|---|---|
| League name | Text | Trimmed, 3–100 characters |
| Start gameweek | Select/number | Integer 1–38 |
| Include transfer deductions | Switch | Required boolean |
| Allowed chips | Checkbox group | Zero to four unique values |

Chip values and suggested labels:

| API value | Label |
|---|---|
| `WILDCARD` | Wildcard |
| `FREE_HIT` | Free Hit |
| `BENCH_BOOST` | Bench Boost |
| `TRIPLE_CAPTAIN` | Triple Captain |

Request:

```json
{
  "name": "Nairobi Rivals",
  "rules": {
    "start_gameweek": 5,
    "include_transfer_deductions": true,
    "allowed_chips": ["WILDCARD", "FREE_HIT"]
  }
}
```

Success returns a `DRAFT` league and its automatically approved owner membership. Navigate to `/leagues/{slug}`. A duplicate normalized name/slug returns `409`.

Explain the rules in the UI:

- Transfer deductions included: transfer hits reduce the displayed scoreboard score.
- Allowed chips: using a chip not selected by the owner makes that member ineligible for that gameweek.
- Start gameweek: results before this week are unavailable for the league.
- Maximum league size is 20 approved members, including the owner.

### 6.2 League overview (`/leagues/:slug`)

`GET /api/v1/leagues/{slug}` returns league metadata, rules, and members.

Show:

- League name and `DRAFT`/`ACTIVE` badge.
- Rules summary.
- Approved member count out of 20.
- Approved member rows.
- Owner-only sections for pending/rejected members, invite management, editing, activation, and manual gameweek sync.

Members do not currently include team or manager names—only `fpl_entry_id`. A frontend could make one authenticated `GET /fpl/teams/{entry_id}` request per row, but that creates an N+1 request pattern and invokes an external service. Prefer the backend enhancement in section 10.

The owner receives all membership statuses. Non-owners receive only approved members. A pending applicant cannot retrieve the league and receives `403 Your league membership is awaiting approval`.

### 6.3 Edit draft league (`/leagues/:slug/settings`)

Use the same controls as creation. Submit only changed fields to `PATCH /api/v1/leagues/{slug}`; an empty update is invalid. Example:

```json
{
  "name": "Nairobi Super Rivals",
  "rules": {
    "allowed_chips": ["FREE_HIT", "BENCH_BOOST"]
  }
}
```

Changing the name may change the slug. After success, replace the URL with the returned slug. Editing an active league returns `409`; hide or disable editing when status is `ACTIVE`.

### 6.4 Approve and reject members (`/leagues/:slug/members`)

For each `PENDING` member shown to the owner:

- Approve: `PATCH /leagues/{slug}/members/{member_id}/approve`.
- Reject: `PATCH /leagues/{slug}/members/{member_id}/reject`.

Use a confirmation dialog for rejection and disable both row actions during mutation. Replace the returned member in the local cache, then refresh league details and unread notifications.

Approval can return `409` when the league has 20 approved members or the member is no longer pending. It can return `502` if the backend cannot determine the current FPL gameweek. When approved after league activation, scoring begins at the later of the league's configured start week and the current gameweek.

### 6.5 Activate league

Owner action: `PATCH /api/v1/leagues/{slug}/activate` with no request body.

Activation is irreversible through the current API and permanently closes editing. Use a confirmation dialog that summarizes the rules. On success, update the status to `ACTIVE`, hide editing controls, and expose gameweek navigation. Repeated activation returns `409`.

## 7. Invitation flows

### 7.1 Owner invitation management

List with `GET /api/v1/leagues/{slug}/invitations`. Each row has expiry time, acceptance count, and active/revoked state.

Creation form:

| Field | Control | Rules |
|---|---|---|
| Valid for | Select/number | 1–30 days; default 7 |

Submit `POST /api/v1/leagues/{slug}/invitations`:

```json
{ "expires_in_days": 7 }
```

The raw `token` appears only in the create response. Immediately build and display a share URL such as `${FRONTEND_ORIGIN}/invite/${token}`, with copy/share actions. Do not expect to retrieve the token again from the invitation list.

Revoke with `DELETE /api/v1/leagues/{slug}/invitations/{invitation_id}`. Success is `204` with no JSON body; the API client must not attempt to parse JSON for it.

### 7.2 Invite recipient (`/invite/:token`)

The preview endpoint requires authentication. Preserve the token through both authentication and onboarding:

```text
Open invite
  ├─ not signed in → sign in/verify → return to invite
  ├─ signed in, no FPL team → FPL onboarding → return to invite
  └─ signed in and onboarded → preview → accept
```

Call `GET /api/v1/invitations/{token}` and render league name and expiry.

- `already_member: false`: show “Request to join.”
- `already_member: true`, `PENDING`: show “Awaiting owner approval.”
- `already_member: true`, `APPROVED`: show “Open league.”
- A previously rejected member is returned with `already_member: false` and `membership_status: "REJECTED"`; allow them to request again.
- `404`: invalid invitation.
- `410`: expired or revoked invitation.

Accept with `POST /api/v1/invitations/{token}/accept` and no body. A successful new request normally returns `membership_status: "PENDING"`. Show a waiting-for-approval screen; do not navigate to league details because pending users receive `403` there. `409` means onboarding is incomplete or the league is full.

## 8. Gameweek screens

### 8.1 League standings

Call `GET /api/v1/leagues/{slug}/gameweeks/{gameweek}` for weeks 1–38. The response status is `LIVE` or `FINAL`.

Recommended table columns:

- Rank (render `—` when null)
- Team/member (currently identified by `league_member_id`/`fpl_entry_id`)
- Scoreboard points (primary score)
- Gross points
- Transfer deduction
- Net points
- Transfers made
- Bench points
- Chip used
- Eligibility

If `eligible` is false, visually de-emphasize the row, show `ineligibility_label`, and do not infer behavior beyond the returned rank/score. The only current reason enum is `PROHIBITED_CHIP`.

Error states:

- `403`: membership pending or approved membership required.
- `404 FPL gameweek not found`: invalid/unavailable FPL week.
- `404 Gameweek results are not available`: owner has not synced or scheduled sync has not persisted results.
- `409`: week is before league start or has not started.
- `502`: FPL is temporarily unavailable.

For an owner-only manual refresh, call `POST /api/v1/leagues/{slug}/gameweeks/{gameweek}/sync`. Disable the action for draft leagues and weeks before the league start. On success, refresh standings. The backend also runs a scheduled sync, so label this “Refresh results,” not as a mandatory scoring step.

### 8.2 Member gameweek detail

Call `GET /api/v1/leagues/{slug}/gameweeks/{gameweek}/members/{member_id}`.

Show the score summary followed by a 15-player squad grouped by goalkeeper, defender, midfielder, and forward. Each pick includes squad position, starter/bench state, captain/vice-captain, multiplier, raw gameweek points, and points contribution. Make `points_contribution` the primary per-player number because it accounts for multiplier and lineup contribution.

The standalone authenticated FPL endpoints are also available:

- `GET /api/v1/fpl/teams/{entry_id}` for manager summary.
- `GET /api/v1/fpl/teams/{entry_id}/gameweeks/{gameweek}` for raw FPL gameweek data.

Use the league-specific endpoints for league UI because they apply league eligibility and scoring rules.

## 9. Notifications

Use `GET /api/v1/notifications/unread-count` for the navigation badge. Polling on window focus or every 30–60 seconds is reasonable; there is no push/WebSocket endpoint.

Inbox query:

```text
GET /api/v1/notifications?unread_only=false&limit=50&offset=0
```

`limit` is 1–100 and `offset` is zero or greater. The response includes `items` and the user's total `unread_count`.

Actions:

- Mark one read: `PATCH /notifications/{notification_id}/read`.
- Mark all read: `PATCH /notifications/read-all`.

Route notifications using their `type` and `data`:

| Type | Relevant data | Suggested destination |
|---|---|---|
| `MEMBERSHIP_PENDING` | `league_slug`, `member_user_id` | League member management |
| `MEMBERSHIP_APPROVED` | `league_slug` | League overview |
| `MEMBERSHIP_REJECTED` | `league_slug` | Informational; dashboard |
| `LEAGUE_RULES_CHANGED` | `league_slug`, `changed_fields` | League overview |
| `GAMEWEEK_WINNER` | `league_slug`, `gameweek` | League gameweek |
| `FPL_DEADLINE` | `gameweek`, `deadline_time` | Notifications or external FPL site |

Treat `data` as an extensible object and safely handle missing fields.

## 10. Backend gaps that affect the frontend

These are not frontend implementation details; they are missing or awkward server capabilities discovered while mapping the flow.

### Must address for a complete first release

1. **No endpoint lists the current user's leagues.** There is only `GET /leagues/{slug}`. Add something like `GET /api/v1/leagues` returning memberships, league summary, role, and membership status. Without it, `/dashboard` cannot discover a user's leagues after refresh.
2. **League member responses omit display information.** They expose only IDs, role, and status. Add `team_name` and `manager_name` to `LeagueMemberResponse` (preferably from the stored FPL account) so standings and approval screens are understandable without N+1 FPL calls.
3. **No CORS middleware is configured.** If frontend and API use different origins in development or production, cookie-bearing requests will fail in the browser. Configure explicit allowed frontend origins, credentials, methods, and headers; never use wildcard origin with credentialed cookies.
4. **No frontend/API deployment contract is defined.** Add a frontend API base URL setting and decide whether production serves both behind one origin. Same-origin routing is simplest for the HTTP-only cookie.
5. **No current-gameweek metadata endpoint exists.** The UI cannot know which gameweek to open or which weeks are future without guessing. Expose current gameweek plus deadline/status metadata.

### Useful follow-ups

- An explicit `viewer_membership` field in league detail would avoid inferring the current user's role from FPL entry ID.
- There is no leave-league, remove-member, delete/archive-league, transfer-ownership, or deactivate endpoint.
- There is no change/unlink FPL account endpoint.
- There is no resend-specific OTP endpoint; reuse `/auth/otp/request` and honor cooldown.
- There is no invitation preview for anonymous users, so invite routing must preserve the token through sign-in.
- There is no total notification count or cursor pagination; offset pagination is supported.
- League activation has no backend precondition requiring a minimum member count. The frontend should not invent one.
- The API exposes FastAPI docs at `/docs`, but no generated TypeScript client is currently checked into the frontend.

## 11. Complete endpoint inventory

All paths below are relative to `/api/v1`.

| Method | Path | Auth | Success | Purpose |
|---|---|---:|---:|---|
| `GET` | `/health` | No | 200 | Service health |
| `GET` | `/health/db` | No | 200 | Database health |
| `GET` | `/health/redis` | No | 200 | Redis health |
| `POST` | `/auth/otp/request` | No | 202 | Request sign-in code |
| `POST` | `/auth/otp/verify` | No | 200 | Verify code and set session cookie |
| `GET` | `/auth/me` | Yes | 200 | Current user/session bootstrap |
| `POST` | `/auth/logout` | Yes | 200 | Revoke current/all sessions |
| `POST` | `/onboarding/fpl/preview` | Yes | 200 | Validate and preview FPL team |
| `POST` | `/onboarding/fpl/claim` | Yes | 200 | Link FPL team |
| `GET` | `/fpl/teams/{entry_id}` | Yes | 200 | FPL manager summary |
| `GET` | `/fpl/teams/{entry_id}/gameweeks/{gameweek}` | Yes | 200 | Raw FPL picks and score |
| `POST` | `/leagues` | Yes | 201 | Create draft league |
| `GET` | `/leagues/{slug}` | Yes, approved member | 200 | League details and members |
| `PATCH` | `/leagues/{slug}` | Yes, owner | 200 | Edit draft league |
| `PATCH` | `/leagues/{slug}/activate` | Yes, owner | 200 | Activate league |
| `PATCH` | `/leagues/{slug}/members/{member_id}/approve` | Yes, owner | 200 | Approve applicant |
| `PATCH` | `/leagues/{slug}/members/{member_id}/reject` | Yes, owner | 200 | Reject applicant |
| `POST` | `/leagues/{slug}/invitations` | Yes, owner | 201 | Create reusable invite |
| `GET` | `/leagues/{slug}/invitations` | Yes, owner | 200 | List invites without raw tokens |
| `DELETE` | `/leagues/{slug}/invitations/{invitation_id}` | Yes, owner | 204 | Revoke invite |
| `GET` | `/invitations/{token}` | Yes | 200 | Preview invite |
| `POST` | `/invitations/{token}/accept` | Yes, onboarded | 200 | Request membership |
| `POST` | `/leagues/{slug}/gameweeks/{gameweek}/sync` | Yes, owner | 200 | Refresh persisted results |
| `GET` | `/leagues/{slug}/gameweeks/{gameweek}` | Yes, approved member | 200 | League standings |
| `GET` | `/leagues/{slug}/gameweeks/{gameweek}/members/{member_id}` | Yes, approved member | 200 | Member picks and scoring |
| `GET` | `/notifications` | Yes | 200 | Paginated notification list |
| `GET` | `/notifications/unread-count` | Yes | 200 | Navigation badge count |
| `PATCH` | `/notifications/{notification_id}/read` | Yes | 200 | Mark notification read |
| `PATCH` | `/notifications/read-all` | Yes | 200 | Mark all notifications read |

## 12. Suggested frontend delivery order

1. Shared API client, credentials, response-error normalization, auth bootstrap, and route guards.
2. Sign-in, OTP verification, FPL onboarding, and invite-token resume behavior.
3. Backend league-list and member-display enhancements from section 10.
4. Dashboard and league creation.
5. League overview, draft settings, invitation management, and member approvals.
6. Activation, gameweek standings, member detail, and owner refresh.
7. Notification badge/inbox and account/logout.
8. Loading skeletons, empty states, retry states, accessibility, and responsive polish.

At every mutation, prevent duplicate submission, keep the submitted values on recoverable errors, show the backend `detail` in user-friendly language, and invalidate only the affected cached resources.
