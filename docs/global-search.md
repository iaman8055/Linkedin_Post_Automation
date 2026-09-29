# Global search

Milestone I adds one authenticated, owner-scoped search surface for posts, content ideas, knowledge
items, and templates. The persistent application-header field opens `/search`; filters remain in the
URL so a search can be bookmarked or shared within the same signed-in account.

## API

`GET /api/v1/search` accepts `q`, `entity_type`, `status`, `topic`, `tag`, `date_from`, `date_to`, and
`limit`. Every entity query includes the authenticated user's identifier before any other filters are
applied. The service never exposes content belonging to another user.

- Status applies to posts.
- Topic applies to content ideas.
- Tag is an exact, case-insensitive knowledge tag match.
- Date filters apply to entity creation dates and are interpreted as inclusive calendar dates in UTC.
- Results are combined, sorted by last update, and capped by the requested limit.

No database migration or additional environment variable is required.
