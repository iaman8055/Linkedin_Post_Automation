# AI Copilot

J2 adds persistent, workspace-scoped Copilot conversations at `/copilot`.

The assistant builds a bounded context from J1 read tools. Recent posts, ideas, and plans are included;
writing style and analytics follow the user's context toggles. Private knowledge is excluded unless the
user explicitly enables **My knowledge** for that message.

Responses use a validated structured schema containing an answer, evidence, an optional suggested
action, and an optional `create_draft` proposal. Evidence must refer to supplied workspace data. Missing
LinkedIn analytics remain unavailable rather than being estimated.

## Confirmation lifecycle

Draft proposals are stored as `PENDING` actions for 30 minutes. Confirmation atomically claims an
action before calling the controlled tool layer, which prevents duplicate execution. Outcomes are
`EXECUTED`, `CANCELLED`, `EXPIRED`, or `FAILED`. A created post remains a draft.

Publishing, scheduling, deletion, OAuth changes, and arbitrary database operations are not available
to the Copilot.

## API

- `POST /api/v1/copilot/conversations`
- `GET /api/v1/copilot/conversations`
- `GET /api/v1/copilot/conversations/{conversation_id}`
- `POST /api/v1/copilot/conversations/{conversation_id}/messages`
- `POST /api/v1/copilot/actions/{action_id}/confirm`
- `POST /api/v1/copilot/actions/{action_id}/cancel`

Apply migration `b7c3e91a4d22` before using the feature.
