# Creator progress

Milestone G adds a professional progress panel to the existing dashboard. All values are calculated
from owned database records; the system does not generate sample activity or estimated impressions.

## Metrics

- Published posts use posts currently in `PUBLISHED` state with a real publication timestamp.
- Drafts use posts currently in `DRAFT` state.
- Idea runs count successful AI content-idea generation jobs.
- Impressions sum the latest available real analytics snapshot for each post. The value remains
  unavailable when LinkedIn analytics have not been collected.
- A publishing streak counts unique consecutive UTC publication dates and remains active when the last
  publication was today or yesterday.

Creator levels use transparent activity points: 100 per published post, 20 per current draft, and 10
per successful idea-generation run. Each level contains 500 points.

## Goals and achievements

`GET /api/v1/creator-progress` returns current progress and idempotently records newly earned
achievements. `PATCH /api/v1/creator-progress/goal` changes the monthly publishing target from 1 to 100.

Supported achievements are first post, 10 posts, 50 posts, 7-day streak, 30-day streak, and 10,000
measured impressions. Impression achievements cannot unlock without real analytics.

Apply the migration before loading the dashboard:

```powershell
cd backend
uv run alembic upgrade head
```
