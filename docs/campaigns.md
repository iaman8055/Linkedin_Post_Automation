# Campaigns

Phase 9 introduces user-owned campaigns for grouping related posts and configuring future approval and
scheduling behavior. Scheduling itself remains Phase 10 work.

## API

All campaign routes require authentication and verify the owning user:

- `POST /api/v1/campaigns` creates a campaign in `DRAFT`.
- `GET /api/v1/campaigns` returns a paginated list with optional status filtering.
- `GET /api/v1/campaigns/{id}` returns one campaign.
- `PATCH /api/v1/campaigns/{id}` updates mutable campaign settings.
- `POST /api/v1/campaigns/{id}/transition` applies a legal lifecycle transition.
- `DELETE /api/v1/campaigns/{id}` deletes a draft campaign.
- `GET /api/v1/campaigns/{id}/posts` lists its posts.
- `POST` and `DELETE /api/v1/campaigns/{id}/posts/{post_id}` manage membership.

Both the campaign and post must belong to the authenticated user. Requests for another user's records
return the same not-found result as unknown identifiers.

## Lifecycle

Legal transitions are:

```text
DRAFT -> ACTIVE | CANCELLED
ACTIVE -> PAUSED | COMPLETED | CANCELLED
PAUSED -> ACTIVE | COMPLETED | CANCELLED
```

Completed and cancelled campaigns are terminal and read-only. Only draft campaigns can be deleted.
Deleting a draft campaign retains its posts and removes their campaign association.

## Approval

New campaigns default to `MANUAL` approval. `AUTOMATIC` can be selected explicitly, but this phase does
not schedule or publish posts. Those behaviors remain gated behind the later scheduling and publishing
services.

Campaign timezones must be valid IANA timezone identifiers. UTC remains the internal timestamp standard;
the campaign timezone is configuration for future scheduling and display.
