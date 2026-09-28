# LinkedIn analytics

Phase 20 collects available metrics for the authenticated user's own published LinkedIn posts. The
integration was checked against LinkedIn's Member Post Statistics documentation on September 27, 2026.

## Product and permission requirements

LinkedIn exposes member post statistics through:

```text
GET https://api.linkedin.com/rest/memberCreatorPostAnalytics
```

Single-post collection uses the `entity` finder, `TOTAL` aggregation, the Rest.li 2.0 header, and a
versioned `Linkedin-Version` header. Access requires:

- an approved Community Management API product;
- the three-legged member permission `r_member_postAnalytics`;
- renewed member consent after that scope is enabled.

Official references:

- https://learn.microsoft.com/en-us/linkedin/marketing/community-management/members/post-statistics
- https://learn.microsoft.com/en-us/linkedin/marketing/increasing-access

The default OAuth scope list does not request this restricted permission. After LinkedIn approves the
application, add it explicitly and reconnect:

```env
LINKEDIN_OAUTH_SCOPES=["openid","profile","email","w_member_social","r_member_postAnalytics"]
```

## Collected metrics

The current database stores the documented lifetime totals for:

- `IMPRESSION` as impressions;
- `REACTION` as likes/reactions;
- `COMMENT` as comments;
- `RESHARE` as shares.

Engagement rate is derived per snapshot as `(reactions + comments + reshares) / impressions * 100`.
When impressions are unavailable or zero, engagement rate remains null. No missing metric is converted
to a fabricated zero in the UI.

LinkedIn documents these counts as best-effort and not suitable for billing. Newer metrics such as saves,
sends, link clicks, followers, and profile views are deliberately not stored until the schema and product
requirements are expanded.

## Data flow

1. Collection is allowed only for an owned post with `PUBLISHED` state and a LinkedIn post URN.
2. The service verifies a connected account and the required scope before decrypting its token.
3. LinkedIn is queried separately for each supported metric.
4. One timestamped `PostAnalytics` snapshot is stored; raw metadata contains metric names but no token.
5. The overview uses only the latest snapshot for each post, while history remains available.

Permission failures, rate limits, and provider failures return structured errors. No analytics are
invented when access is missing.

## API and worker

- `GET /api/v1/analytics/status` reports connection and scope availability.
- `GET /api/v1/analytics/overview` returns latest owned snapshots and aggregates.
- `POST /api/v1/analytics/posts/{post_id}/refresh` performs real collection.
- `GET /api/v1/analytics/posts/{post_id}/history` returns up to 100 snapshots.
- `workers.analytics_tasks.fetch_analytics` performs the same collection on the analytics queue.

Automated tests replace the LinkedIn boundary and never call the real API.

## Performance insights

`GET /api/v1/analytics/insights` analyzes the latest real snapshot for each owned post. It requires at
least five posts with a measured engagement rate before returning observations. Available observations
cover the strongest individual post and, when each comparison has enough samples, content length,
publishing time in the user's configured timezone, and campaign performance.

These results are deterministic summaries of the user's own data. Every result includes its evidence
and sample size, and the UI explicitly states that observations are not universal LinkedIn rules. The
service does not invent missing metrics or send private analytics to an external AI provider.

## Personalized scheduling suggestions

`GET /api/v1/analytics/scheduling-suggestions` groups the user's measured posts by weekday and local
publishing hour. Suggestions require at least five measured posts, and an individual window is shown
only after it has at least two samples. At most three windows are returned, ranked by average measured
engagement rate.

The endpoint uses the user's configured timezone and returns evidence and sample size for every result.
If there is not enough repeated history, it returns `insufficient_data` rather than generic industry
advice. Suggestions are observations, not guarantees and not universal LinkedIn best times.
