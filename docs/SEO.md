# Frontend SEO and social sharing

RivalXI is a private application for friends. Its current routes are not intended
to appear in search results.

## Indexing strategy

The initial HTML contains `noindex, nofollow`, covering every route served by the
Vite single-page application. This includes sign-in, OTP verification,
onboarding, invitation-token URLs, private leagues, gameweeks, member views, and
the authenticated dashboard.

`robots.txt` permits crawlers to request pages so they can read the `noindex`
directive and social services can retrieve sharing metadata. It is not an access
control mechanism; authentication and authorization continue to protect private
application data.

There is no sitemap because the application has no indexable routes. A canonical
element is also intentionally omitted: every route receives the same static HTML,
and declaring one canonical URL there would incorrectly canonicalize private and
invitation-token routes.

## Social previews

The initial HTML supplies a generic Open Graph and Twitter large-image preview:

- Title: `RivalXI League Invitation`
- Description: `Private Fantasy Premier League competitions where each gameweek
  is its own contest.`
- Image: `https://rival-xi.com/rivalxi-social-card.png`

The image contains no league, member, or invitation-token information. Since
RivalXI is a static Vite application, all routes receive this same preview.
League-specific previews would require route-aware HTML generation at the server
or edge and careful handling of invitation tokens.

## Verification

After deployment, inspect the initial HTML response rather than only the rendered
DOM. Confirm that `/rivalxi-social-card.png` is publicly reachable, then refresh
cached previews using the relevant social platform's link-debugging tool.
