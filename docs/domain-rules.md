# Domain rules

This document describes behavior enforced by the current models and services.

## Identity and FPL accounts

- Email addresses are normalized and unique.
- Successful OTP verification creates a user when one does not exist; there is no separate registration flow.
- A RivalXI user can claim exactly one FPL entry, and an FPL entry can belong to only one RivalXI user.
- Claiming the same entry again is idempotent. Changing or unlinking an FPL team is not implemented.
- Manager search is only discovery. The selected entry is verified against official FPL data before preview and again before persistence.

## Leagues

- A user must have a claimed FPL account before creating or joining a league.
- A league has a unique slug and at most 20 approved members, including the owner.
- The creator becomes an approved owner immediately.
- A league begins in `DRAFT`. Owners may change its name and rules while it remains a draft.
- Activation changes the league to `ACTIVE`; active league configuration cannot be edited and activation cannot be reversed through the API.
- Only approved members may read league results. Owners may also see and act on pending or rejected membership records.

## Invitations and membership

- Each league has one reusable invitation link. The owner can retrieve or regenerate it; regeneration invalidates the old code.
- Invitation preview and acceptance require authentication. Acceptance also requires completed FPL onboarding.
- A new or previously rejected applicant becomes `PENDING`; an owner must approve or reject them.
- A user and FPL entry can each have only one membership record per league.
- If a member is approved after league activation, their scoring starts at the later of the configured league start gameweek and the then-current FPL gameweek. This avoids retroactive participation.

## Scoring

Every league chooses:

- a start gameweek from 1 through 38;
- whether transfer deductions count; and
- a set of allowed FPL chips: Wildcard, Free Hit, Bench Boost, and Triple Captain.

For every synchronized member/gameweek, RivalXI stores:

- gross FPL points;
- transfer deduction and net points;
- the league's displayed `scoreboard_points`;
- transfers made and bench points;
- chip use and whether that chip is allowed; and
- eligibility plus an ineligibility reason.

When transfer deductions are enabled, the displayed score is net points; otherwise it is gross points. A manager using a chip that is not in the league's allowed set is persisted as ineligible and receives no rank. The only current ineligibility reason is `PROHIBITED_CHIP`.

Eligible managers are ranked by displayed points descending, then by not using a chip, then by lower transfer deduction. Exact ties share a rank; membership order only stabilizes their display. Final results trigger deduplicated winner notifications.

## Timing and persistence

- Results cannot be synchronized or read before the gameweek deadline or before the league's start week.
- Results are `LIVE` until official FPL marks the event finished and data checked; then they become `FINAL`.
- An owner may trigger a sync, and the in-process scheduler syncs the current gameweek for all active leagues.
- Player picks and normalized result fields are stored in PostgreSQL, so league pages do not need to reconstruct every result from live upstream data.

## Notifications

In-app notifications exist for pending, approved, and rejected memberships; league rule changes; gameweek winners; and upcoming FPL deadlines. Approval and rejection also attempt Brevo email delivery. Event-specific deduplication prevents repeated winner, deadline, and membership-decision notifications during retries.
