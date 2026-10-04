Implement FPL club kit support in the existing Rival XI squad display.

Use the existing public FPL integration and `bootstrap-static/` data.

### Mapping

Build/reference lookup maps from `bootstrap-static`:

- `elements[].id` = FPL player/element ID
- `elements[].team` = club/team ID
- `elements[].element_type` = position ID
- `teams[].id` = club ID
- `teams[].code` = club code
- `element_types[].id` = position type:
  - 1 = Goalkeeper
  - 2 = Defender
  - 3 = Midfielder
  - 4 = Forward

For every squad pick:

`pick.element_id -> FPL element -> team + element_type`

Use the team to determine the club kit and `element_type` to determine whether the player needs the goalkeeper or normal outfield kit.

### Implementation

Create a centralized helper/service such as:

`get_player_kit(player)`

which returns something similar to:

```ts
{
  teamId,
  teamCode,
  position,
  kitType: "GOALKEEPER" | "OUTFIELD",
  kitUrl
}
```

Do not maintain manual player-to-team mappings.

The flow should be:

```text
Squad Pick
   ↓ element_id
FPL elements[]
   ↓
Player
   ├── team → teams[]
   │          └── team code / club identity
   │
   └── element_type → element_types[]
                      └── GK / DEF / MID / FWD
   ↓
Resolve club kit asset
   ↓
Render kit + player name + GW points
```

Prefer using the same Premier League/FPL static kit assets used by their frontend where a stable asset pattern can be verified.

However, because FPL has no supported public developer API contract, isolate the external kit URL construction in one adapter such as:

```text
FPLKitAssetProvider
```

so the URL pattern can be replaced without changing squad/domain logic.

Add a fallback:

```text
official FPL kit asset
    ↓ unavailable
local/default shirt silhouette
```

Do not download or persist a separate kit for every player. A kit belongs to a club/position type, so reuse/cache it.

The existing backend squad response can then either:

1. expose `team_id`, `team_code`, `player_position`, and optionally `kit_url`, or
2. let the frontend derive `kit_url` from the supplied team/position metadata.

Prefer backend enrichment if Rival XI already performs FPL normalization there.