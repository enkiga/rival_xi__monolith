# Rival XI --- FPL Team Discovery & Claim Implementation Plan

## Purpose

Replace the current onboarding experience that requires a user to
manually obtain or paste an FPL entry URL/ID as the primary path.

The desired onboarding experience is:

> **Search by manager name or FPL team name → select the correct result
> → verify against official FPL data → claim the team once.**

The implementation must preserve the existing Rival XI domain rules:

-   FPL team claiming happens during onboarding.
-   A Rival XI user can claim only one FPL team.
-   An FPL team can belong to only one Rival XI user.
-   Once onboarding is complete, the linked FPL team is not
    user-changeable.
-   Rival XI leagues remain completely independent of FPL leagues.
-   FPL leagues must **not** become part of the Rival XI domain model.
-   The existing official FPL integration remains authoritative for team
    information, gameweek picks, scoring, and other FPL data.
-   Manager-name/team-name search is only a **discovery mechanism**.
-   Team ID / FPL link remains the fallback when discovery is
    unavailable or cannot find the manager.

------------------------------------------------------------------------

# 1. Implementation Principle

Before changing code, inspect the existing repository.

**Do not design a parallel architecture without first understanding the
current one.**

The implementation should reuse the existing:

-   onboarding flow;
-   authentication/session dependency;
-   user/FPL-account relationship;
-   FPL HTTP client;
-   FPL exception hierarchy;
-   request pacing/rate-limiting;
-   configuration/settings pattern;
-   API router conventions;
-   schemas/validators;
-   services/use-cases;
-   database transaction boundaries;
-   tests and fixtures.

Then make only the changes necessary to add manager/team discovery.

> **Only make meaningful code changes. Do not overengineer. Read through
> how the code has been coded and follow the existing flow and
> conventions.**

Do not introduce repositories, service layers, protocols, abstractions,
tables, caches, queues, workers, or background jobs merely because this
document mentions them conceptually. Add something only when the
existing code structure or an actual requirement justifies it.

------------------------------------------------------------------------

# 2. First Task --- Inspect the Existing Codebase

Before implementation, identify the actual files responsible for the
current flow.

Do not assume filenames from this document.

Find the code handling:

1.  user authentication;
2.  email OTP completion;
3.  onboarding;
4.  current FPL team claiming/linking;
5.  FPL entry validation;
6.  FPL API HTTP requests;
7.  FPL request pacing/rate limiting;
8.  FPL exception → HTTP response mapping;
9.  user/FPL-entry persistence;
10. database uniqueness constraints;
11. onboarding API routes;
12. settings/environment variables;
13. relevant tests.

Create a short **Existing Implementation Map** before changing code.

Example format:

``` md
## Existing Implementation Map

| Responsibility | Existing file | Existing function/class | Notes |
|---|---|---|---|
| FPL HTTP client | `actual/path.py` | `ActualClass` | ... |
| Onboarding | `actual/path.py` | `actual_function()` | ... |
| Team claim | `actual/path.py` | `actual_function()` | ... |
| FPL exceptions | `actual/path.py` | ... | ... |
| User/FPL relationship | `actual/path.py` | ... | ... |
```

The paths above must come from the repository. Do not invent them.

------------------------------------------------------------------------

# 3. Confirm the Existing Claim Model

The repository should answer most of these questions.

## Questions to resolve from code first

### Q1. Where is `fpl_entry_id` currently stored?

Determine whether it lives directly on:

``` text
User
```

or on a dedicated model such as:

``` text
FPLAccount
UserFPLAccount
FPLProfile
```

or another existing model.

**Do not introduce a new FPL account model if the existing model already
represents the relationship correctly.**

------------------------------------------------------------------------

### Q2. Is `fpl_entry_id` already unique?

The required invariant is:

``` text
one Rival XI user -> one FPL entry
one FPL entry     -> one Rival XI user
```

Verify database constraints rather than relying only on application
checks.

If the database already enforces this, make no schema change.

If it does not, determine whether adding the constraint is safe with
existing data before creating a migration.

------------------------------------------------------------------------

### Q3. How does the current claim flow validate an entry?

Locate the current path used when the user provides an FPL URL or entry
ID.

Determine whether it already:

1.  extracts an entry ID;
2.  calls official FPL;
3.  validates the response;
4.  obtains manager/team information;
5.  persists the relationship.

The new search flow should feed into this existing claim logic rather
than creating a second claim implementation.

Desired convergence:

``` text
Manager search
      |
      v
selected entry_id
      |
      +-------------------+
                          |
Manual ID / FPL link -----+
                          |
                          v
                 EXISTING CLAIM FLOW
                          |
                          v
                   Official FPL
                          |
                          v
                       Claim
```

------------------------------------------------------------------------

# 4. External Discovery Provider

For the first implementation, use **FPL Rivals** only for manager/team
discovery.

Official documentation:

-   Website: `https://fplrivals.org/`
-   API documentation: `https://fplrivals.org/api/`
-   API base: `https://api.fplrivals.org/api/v1`

Current search shape:

``` http
GET /search?q=<query>&type=manager&limit=<limit>
```

The provider can return candidate FPL managers containing information
such as:

``` text
id
player_name
entry_name
```

Normalize those into Rival XI terminology:

``` text
entry_id
manager_name
team_name
```

## Important boundary

FPL Rivals is **not authoritative FPL data for Rival XI**.

Use it only for:

``` text
text query -> candidate entry IDs
```

Once an entry is selected, return to the existing official FPL
integration.

``` text
FPL Rivals
    |
    | discovery
    v
candidate entry_id
    |
    v
Official FPL API
    |
    | validation
    v
Rival XI claim
```

Do not start routing existing:

-   gameweek data;
-   picks;
-   standings;
-   player data;
-   team details;
-   scoring;
-   synchronization;

through FPL Rivals.

------------------------------------------------------------------------

# 5. Dependency Boundary

The frontend should not call FPL Rivals directly.

Use:

``` text
Client
  |
  | GET Rival XI manager-search endpoint
  v
FastAPI
  |
  | server-side request
  v
FPL Rivals
```

Reasons:

-   Rival XI owns its frontend API contract.
-   Third-party response changes are isolated to the backend.
-   CORS behavior is irrelevant to the client.
-   provider rate limiting can be controlled centrally;
-   errors can be normalized;
-   the provider can later be replaced without rewriting the UI.

------------------------------------------------------------------------

# 6. Do Not Over-Abstract the Provider

First inspect how external clients are currently implemented.

If the project already has an FPL client pattern, follow it.

For example, if the existing application uses simple client functions,
prefer something equivalent to:

``` python
async def search_fpl_managers(query: str) -> list[ManagerSearchResult]:
    ...
```

Do **not** automatically introduce:

``` text
ManagerSearchProvider
FPLManagerDiscoveryRepository
ManagerSearchGateway
ManagerSearchAdapter
ManagerSearchFactory
ManagerSearchStrategy
```

for one provider.

A provider interface becomes useful only if:

-   the existing codebase already follows that pattern; or
-   a second provider is actually being introduced.

Until then, keep the implementation small.

------------------------------------------------------------------------

# 7. Proposed API

The exact route must follow the repository's existing route conventions.

Conceptually:

``` http
GET /api/v1/fpl/managers/search?q=Kevin%20Garoli
```

or, if onboarding routes own this concern:

``` http
GET /api/v1/onboarding/fpl/search?q=Kevin%20Garoli
```

## Question

**Which route grouping matches the existing application?**

Resolve this from the router structure before implementation.

Do not add a new router solely because this document uses
`/fpl/managers/search`.

------------------------------------------------------------------------

# 8. Search Request Rules

Recommended initial behavior:

``` text
minimum query length: 3 characters
maximum query length: reasonable bounded value, e.g. 100
result limit: 8–10
```

The backend should:

1.  trim whitespace;
2.  reject queries below the minimum;
3.  URL-encode the query through the HTTP client's normal parameter
    handling;
4.  use a fixed provider-side result limit;
5.  normalize provider results;
6.  return only fields needed by the UI.

Suggested Rival XI response:

``` json
{
  "results": [
    {
      "entry_id": 4250337,
      "manager_name": "Kevin Garoli",
      "team_name": "Rival XI"
    }
  ]
}
```

Do not expose the complete upstream payload.

------------------------------------------------------------------------

# 9. Search Authentication

The manager-search endpoint should be available only to the appropriate
authenticated onboarding user.

Reuse the existing session/authentication dependency.

## Question

**Does Rival XI currently permit only authenticated-but-not-onboarded
users to call onboarding endpoints, or simply any authenticated user?**

Resolve this from existing onboarding authorization.

Follow the same rule.

Do not create a second onboarding authorization model for manager
search.

------------------------------------------------------------------------

# 10. Search UI

The primary onboarding UI should become:

``` text
┌────────────────────────────────────────┐
│ Find your FPL team                     │
│                                        │
│ Search using your name or FPL team     │
│ name.                                  │
│                                        │
│ ┌────────────────────────────────────┐ │
│ │ Kevin Garoli                       │ │
│ └────────────────────────────────────┘ │
│                                        │
│ Search results                         │
│                                        │
│ ┌────────────────────────────────────┐ │
│ │ Kevin Garoli                       │ │
│ │ Rival XI                           │ │
│ │                           Select → │ │
│ └────────────────────────────────────┘ │
│                                        │
│ ┌────────────────────────────────────┐ │
│ │ Kevin Garoli                       │ │
│ │ Haaland Oates                      │ │
│ │                           Select → │ │
│ └────────────────────────────────────┘ │
│                                        │
│ Can't find your team?                  │
│ Use your FPL Team ID instead →         │
└────────────────────────────────────────┘
```

Use **one search field**.

Do not create separate:

``` text
Manager Name
Team Name
```

tabs or inputs.

The discovery service already supports matching both.

------------------------------------------------------------------------

# 11. Frontend Search Behaviour

Use approximately:

``` text
400 ms debounce
```

and require at least:

``` text
3 characters
```

before searching.

Do not fire a request on every keypress.

The UI needs these states:

``` text
idle
searching
results
no results
provider unavailable
```

If the existing frontend data-fetching setup supports request
cancellation, cancel stale searches.

If it does not, do not introduce a large data-fetching library solely
for this feature. A simple stale-request guard or `AbortController` is
sufficient.

------------------------------------------------------------------------

# 12. Selecting a Search Result

**Do not claim immediately when a search result is selected.**

Search results come from a third-party discovery index.

Selection should produce only:

``` text
entry_id
```

Then call Rival XI's existing official-FPL validation path.

Conceptually:

``` text
User selects:
Kevin Garoli
Rival XI
entry_id = 4250337
        |
        v
Rival XI backend
        |
        v
Official FPL:
GET /entry/4250337/
        |
        v
verified current entry
        |
        v
confirmation UI
```

------------------------------------------------------------------------

# 13. Confirmation Screen

Use official FPL data for the confirmation screen.

Example:

``` text
┌────────────────────────────────────────┐
│ Is this your team?                     │
│                                        │
│               RIVAL XI                 │
│                                        │
│             Kevin Garoli               │
│                                        │
│     341 pts            #482,291        │
│     Total points       Overall         │
│                                        │
│ ┌────────────────────────────────────┐ │
│ │       Yes, claim this team        │ │
│ └────────────────────────────────────┘ │
│                                        │
│             That's not me              │
└────────────────────────────────────────┘
```

Use only fields already available from the existing FPL entry response.

Do not add additional FPL requests merely to decorate this screen unless
there is a real UX requirement.

------------------------------------------------------------------------

# 14. Claim Flow

The final claim should use the existing claim/use-case logic.

Conceptually:

``` http
POST <existing claim endpoint>
```

with:

``` json
{
  "entry_id": 4250337
}
```

If the existing endpoint currently accepts:

``` json
{
  "fpl_url": "..."
}
```

inspect whether it can be safely extended to accept a normalized entry
ID without breaking the current fallback.

Prefer one underlying use case:

``` text
claim_fpl_team(user, entry_id)
```

with multiple discovery/input methods feeding it.

Avoid:

``` text
claim_from_search()
claim_from_url()
claim_from_manual_id()
```

if they duplicate the same business logic.

------------------------------------------------------------------------

# 15. Manual Fallback

The fallback remains mandatory.

If:

-   no manager is found;
-   the manager is new and not indexed;
-   FPL Rivals is stale;
-   FPL Rivals is unavailable;
-   Rival XI receives `429`;
-   Rival XI receives a provider timeout;
-   the user simply knows their ID;

show:

``` text
Can't find your team?

[ Use FPL Team ID instead ]
```

The existing URL/ID mechanism should remain available if already
implemented.

Do not delete a working fallback just because search becomes the primary
path.

------------------------------------------------------------------------

# 16. Failure Behaviour

FPL Rivals is an onboarding convenience, not a core Rival XI dependency.

Therefore:

``` text
FPL Rivals down
       !=
Rival XI onboarding down
```

Desired behaviour:

``` text
search request
    |
    +-- success ----------> show results
    |
    +-- no results -------> show manual fallback
    |
    +-- timeout -----------> show manual fallback
    |
    +-- 429 ---------------> show manual fallback
    |
    +-- upstream 5xx ------> show manual fallback
```

User-facing copy can be simple:

``` text
We couldn't search FPL right now.

You can still connect your team using your FPL Team ID.
```

Do not expose upstream service names or stack traces to the user.

------------------------------------------------------------------------

# 17. Upstream Error Mapping

Inspect the existing FPL exception conventions.

Rival XI already has established handling for upstream failures. Reuse
those conventions where appropriate.

However, distinguish:

``` text
official FPL failure
```

from:

``` text
optional manager-search provider failure
```

The latter should generally degrade to the manual onboarding path rather
than make the entire onboarding workflow fail.

## Question

**Does the existing frontend need an HTTP error to trigger fallback, or
would a successful response such as
`{"results": [], "search_available": false}` fit the current API style
better?**

Answer this from the existing API/error conventions.

Do not invent a special response envelope unless needed.

------------------------------------------------------------------------

# 18. Timeouts

Manager search is interactive.

Do not allow a third-party request to hang onboarding for a long period.

Inspect existing HTTP client timeout settings first.

If there is an established timeout policy, reuse it.

If not, add a sensible short timeout specifically for the manager-search
request.

Do not globally change FPL client timeouts just for this feature.

------------------------------------------------------------------------

# 19. Rate Limiting

Rival XI already has Redis-based FPL request pacing/rate-limiting
infrastructure.

Do not automatically route FPL Rivals traffic through the official-FPL
request slot.

They are different upstream services with different limits.

First inspect how rate limiting is structured.

Questions:

1.  Is the existing Redis limiter specifically an FPL upstream pacing
    mechanism?
2.  Is there already generic per-user API rate limiting?
3.  Is authentication search already rate-limited?
4.  Can manager search reuse an existing per-user request limiter?

Recommended behaviour:

-   client debounce reduces normal traffic;
-   authenticated endpoint prevents anonymous abuse;
-   add/reuse lightweight per-user limiting if the existing architecture
    supports it cleanly;
-   handle upstream `429`;
-   do not build a new distributed rate-limiting subsystem solely for
    this endpoint.

------------------------------------------------------------------------

# 20. Caching

Do **not** add a manager-index cache in the first implementation unless
the existing code already has a suitable generic cache abstraction.

Reasons:

-   search is used once during onboarding;
-   FPL Rivals already performs its own caching;
-   the feature is not performance-critical after onboarding;
-   cache invalidation adds unnecessary complexity.

If measurements later show repeated identical searches causing upstream
pressure, add a short-lived cache then.

Do not optimize a problem that has not appeared.

------------------------------------------------------------------------

# 21. Database Changes

The discovery feature itself should require **no new manager-index
table**.

Do not create:

``` text
fpl_manager_index
manager_search_cache
fpl_search_results
```

for V1.

The only persisted result should remain the FPL identity already
associated with the user.

Before making a migration, answer:

1.  Is `fpl_entry_id` already stored?
2.  Is it already unique?
3.  Is `user_id` already unique on the FPL relationship?
4.  Are manager/team names already persisted?
5.  Does existing onboarding already prevent relinking?

If all required invariants exist:

> **No migration is needed.**

------------------------------------------------------------------------

# 22. Configuration

The provider base URL should follow the project's existing settings
convention.

Potential configuration:

``` env
FPL_MANAGER_SEARCH_BASE_URL=https://api.fplrivals.org/api/v1
```

But first inspect how existing external URLs are configured.

If the codebase currently keeps stable public upstream base URLs as
constants rather than environment configuration, follow that pattern.

Do not create environment variables merely for configurability that the
project does not use.

No API key is currently required by FPL Rivals.

------------------------------------------------------------------------

# 23. Logging

Follow existing logging conventions.

Useful events:

``` text
manager_search_requested
manager_search_upstream_failed
manager_search_rate_limited
fpl_team_claimed
```

Do not log unnecessary personal information.

Prefer:

``` text
query length
result count
HTTP status
duration
```

over storing raw manager-name searches in logs unless existing
observability practices require them.

Never log:

-   authentication tokens;
-   OTPs;
-   session cookies.

------------------------------------------------------------------------

# 24. Security Boundary

Treat all FPL Rivals responses as untrusted external data.

Validate the upstream response before returning it.

At minimum ensure:

``` text
entry_id     -> expected integer
manager_name -> bounded string
team_name    -> bounded string
```

Do not trust an upstream `entry_id` merely because it was returned.

The selected ID must still be validated against official FPL before
claim.

------------------------------------------------------------------------

# 25. Ownership Limitation

Manager search does **not** prove ownership.

Neither does knowing an FPL entry ID or URL.

For Rival XI V1, claiming means:

> The authenticated Rival XI user identifies the FPL team that
> represents them.

Do not describe the search provider as identity verification.

The protection currently comes from:

-   authenticated Rival XI account;
-   explicit confirmation;
-   unique FPL-entry constraint;
-   permanent link after onboarding;
-   league-level social visibility/approval where applicable.

Do not add fake "verification" semantics that the system cannot actually
guarantee.

------------------------------------------------------------------------

# 26. Tests

Follow the existing test style and fixture structure.

Do not create a parallel test framework.

At minimum cover the meaningful new behaviour.

## Backend search tests

``` text
authenticated search succeeds
query below minimum rejected
upstream response normalized correctly
no results handled
provider timeout handled
provider 429 handled
provider 5xx handled
malformed upstream response handled
unauthenticated request rejected
```

## Claim integration/regression tests

Ensure existing claim behaviour still covers:

``` text
valid entry can be claimed
invalid FPL entry rejected
same FPL entry cannot be claimed by two users
user cannot claim second team after onboarding
official FPL remains source of validation
manual ID/link fallback still works
```

Do not duplicate tests already present. Extend existing test modules
where that matches the repository structure.

------------------------------------------------------------------------

# 27. Mock External Services in Tests

Tests must not depend on the live FPL Rivals API.

Mock the manager-search HTTP response using whatever HTTP mocking
pattern the repository already uses.

Likewise, preserve existing official-FPL mocking conventions.

Tests should be deterministic and runnable offline.

------------------------------------------------------------------------

# 28. Frontend Tests

If the frontend currently has meaningful component/integration test
coverage, add tests for:

``` text
search starts after minimum query length
debounce behaviour
results rendered
result selection
no-results state
provider-failure fallback
manual ID fallback
confirmation screen
```

If the frontend currently has no component test infrastructure, **do not
introduce an entire frontend testing stack solely for this feature**
unless requested.

Prioritize backend correctness and manually verify the UI flow.

------------------------------------------------------------------------

# 29. Suggested User Journey

The final onboarding should feel like:

``` text
OTP successful
      |
      v
Find your FPL team
      |
      | type "Kevin Garoli"
      v
Search results
      |
      | select Rival XI
      v
Official FPL validation
      |
      v
Is this your team?
      |
      | Yes
      v
Claim
      |
      v
Onboarding complete
```

Normal users should never need to understand:

``` text
entry_id
FPL API
FPL Rivals
manager index
```

Those are implementation details.

------------------------------------------------------------------------

# 30. UI Copy

Recommended primary copy:

## Heading

``` text
Find your FPL team
```

## Supporting text

``` text
Search using your name or FPL team name.
```

## Search placeholder

``` text
Your name or team name
```

## Result action

``` text
Select
```

## Confirmation

``` text
Is this your team?
```

## Claim action

``` text
Yes, claim this team
```

## Fallback

``` text
Can't find your team?
Use your FPL Team ID instead
```

Keep the interface concise. This is a one-time onboarding action.

------------------------------------------------------------------------

# 31. Do Not Build These

Unless inspection of the repository proves one is required, do **not**
add:

-   a global FPL manager database;
-   Overall-league crawling;
-   background manager scraper;
-   Celery;
-   scheduled indexing jobs;
-   manager search history table;
-   search-result database cache;
-   browser extension;
-   PWA share-target logic for this feature;
-   Premier League credential collection;
-   FPL session-cookie handling;
-   new FPL league models;
-   FPL OAuth assumptions;
-   generic provider factories;
-   multiple provider failover;
-   a new Redis caching layer.

They are outside the scope of the problem being solved.

------------------------------------------------------------------------

# 32. Implementation Order

Use this order.

## Phase 1 --- Codebase inspection

Map the existing:

``` text
onboarding
FPL client
claim flow
models
constraints
auth
errors
tests
```

No implementation yet.

------------------------------------------------------------------------

## Phase 2 --- Resolve questions

Answer from the repository where possible:

-   Where is the FPL entry stored?
-   What endpoint currently claims it?
-   What function validates an entry?
-   How are FPL upstream requests made?
-   What auth dependency protects onboarding?
-   What error style does the API use?
-   Is `fpl_entry_id` unique?
-   How is relinking prevented?
-   What frontend component currently asks for the URL/ID?
-   What HTTP client/data-fetching mechanism does the frontend already
    use?

Only ask the developer/user questions that cannot be answered from code.

------------------------------------------------------------------------

## Phase 3 --- Minimal backend discovery

Add the smallest implementation necessary for:

``` text
query
  -> Rival XI backend
  -> FPL Rivals
  -> normalized candidates
```

Do not touch claim logic yet unless required to make the selected
`entry_id` use the existing path.

------------------------------------------------------------------------

## Phase 4 --- Connect to existing validation

Selection should reuse official-FPL entry validation.

Do not duplicate it.

------------------------------------------------------------------------

## Phase 5 --- UI

Replace the current primary onboarding interaction with manager/team
search.

Keep manual ID/link as fallback.

------------------------------------------------------------------------

## Phase 6 --- Tests

Add focused tests for the new discovery path and regression coverage
around claim behaviour.

------------------------------------------------------------------------

## Phase 7 --- Review diff

Before considering the task complete, inspect the entire diff.

Ask:

``` text
Did we modify code unrelated to onboarding?
Did we introduce abstractions with one implementation?
Did we duplicate existing FPL logic?
Did we introduce a migration unnecessarily?
Did we weaken existing auth?
Did we bypass the existing FPL rate-limited client?
Did we make FPL Rivals authoritative anywhere?
Did we remove the fallback?
Did we add dependencies that are not necessary?
```

Remove unnecessary changes.

------------------------------------------------------------------------

# 33. Questions That Must Be Answered Before/During Implementation

These are not necessarily questions for the user. **Inspect the
repository first.**

### Existing architecture

1.  Where is the current onboarding implementation?
2.  Where is the current FPL URL/ID claim implementation?
3.  What model owns `fpl_entry_id`?
4.  Is `fpl_entry_id` database-unique?
5.  Is the user/FPL relationship already one-to-one?
6.  How does the application currently prevent team changes after
    onboarding?

### Existing FPL integration

7.  What class/function performs FPL HTTP requests?
8.  Is there already an `entry/{id}` method?
9.  How are FPL responses validated?
10. How are FPL errors normalized?
11. How does the Redis request-slot limiter wrap FPL requests?

### API

12. Should manager search belong under the existing FPL router or
    onboarding router?
13. What response schema convention does the project use?
14. What auth dependency should protect the route?

### Frontend

15. Which component currently asks for the FPL link?
16. What data-fetching approach does the React app currently use?
17. Is there already a reusable search/loading/error pattern?
18. How is onboarding state advanced after a successful claim?

### Provider behaviour

19. Does the current FPL Rivals search response exactly match the
    documented schema when tested?
20. What happens for newly created FPL accounts?
21. How stale can search results become?
22. Does `type=manager` search both `player_name` and `entry_name` as
    expected?
23. Does the provider return useful candidates for common duplicate
    names?

If provider behaviour differs from documentation, stop and report the
difference before building assumptions around it.

------------------------------------------------------------------------

# 34. Definition of Done

This feature is complete when:

-   an authenticated onboarding user can type their manager or FPL team
    name;
-   Rival XI returns candidate teams without the frontend talking
    directly to FPL Rivals;
-   results show enough information to distinguish candidates;
-   selecting a result does **not** immediately persist it;
-   selected `entry_id` is verified using the existing official FPL
    integration;
-   the user sees a confirmation screen;
-   confirmation uses the existing claim path;
-   the FPL entry remains uniquely and permanently associated with the
    user according to existing domain rules;
-   manual Team ID/FPL-link onboarding remains available;
-   FPL Rivals failure does not prevent onboarding;
-   no FPL league dependency has been introduced into Rival XI;
-   no manager crawler/index/background job has been introduced;
-   tests cover the meaningful new behaviour;
-   the final diff follows existing project conventions and contains no
    unrelated refactor.

------------------------------------------------------------------------

# 35. Instruction to the Implementer

Use this implementation discipline throughout the task:

> **Read the existing Rival XI code before making changes. Reference the
> actual existing files, functions, models, schemas, routes, clients,
> and tests in the implementation plan. Resolve uncertainty from the
> codebase first. Where the code cannot answer a product or
> architectural question, ask before assuming.**
>
> **Then make only meaningful code changes. Do not overengineer. Follow
> the way the existing codebase has already been structured and coded.
> Reuse existing flows wherever possible, especially authentication,
> onboarding, FPL validation, error handling, request pacing,
> persistence, and tests.**
>
> **FPL Rivals is discovery only. Official FPL remains authoritative.
> The selected entry ID must converge into the existing FPL team claim
> flow rather than creating a parallel implementation.**
>
> **If implementing a requirement would require a substantial
> architectural change not justified by the current code, stop and
> explain why before making that change.**

------------------------------------------------------------------------

# 36. Expected Output Before Coding

Before modifying code, return:

``` md
## Existing Implementation Map

[actual files/functions]

## Existing Claim Flow

[current flow from code]

## Proposed Minimal Change

[files that actually need modification]

## Questions / Uncertainties

[only questions not answerable from repository]

## Expected Database Changes

None / exact migration required and why

## Expected API Changes

[exact routes/schemas]

## Expected Frontend Changes

[actual components]

## Test Changes

[actual existing test files to extend]
```

Only after that review should implementation begin.

This prevents the search feature from becoming an excuse to restructure
working Rival XI code.
