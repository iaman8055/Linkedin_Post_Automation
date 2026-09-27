# In-app notifications

Phase 22 adds user-owned in-app notifications for generated drafts awaiting approval, successful and
failed publishing, scheduled retries, campaign completion, and rejected LinkedIn access tokens.

The notification center supports recent-first listing, unread count, marking one notification read, and
marking all read. Every query includes the authenticated user's ID, so one user cannot read or mutate
another user's events. Notification data contains resource identifiers and sanitized error codes only;
tokens and provider payloads are never stored.

API endpoints:

- `GET /api/v1/notifications`
- `GET /api/v1/notifications/unread-count`
- `PATCH /api/v1/notifications/{notification_id}/read`
- `POST /api/v1/notifications/read-all`

This phase implements in-app delivery. Email, push, and scheduled "approaching" reminders require a
configured delivery provider and are intentionally not simulated.
