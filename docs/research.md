# Research assistant

Phase 17 introduces a provider-neutral research boundary with Tavily as the first concrete integration.
The implementation was checked against Tavily's Search API documentation on September 27, 2026.

## Provider capability

Tavily Search uses `POST https://api.tavily.com/search` with Bearer authentication. The adapter requests
safe-search results, attributable titles and URLs, compact source content, publication dates, relevance
scores, and a basic provider-generated answer. It supports general and news searches plus day, week,
month, and year freshness filters.

The API documents separate responses for invalid credentials, rate limits, plan/usage limits, invalid
requests, and provider failures. The adapter maps these to structured application errors and never logs
the API key.

Official references:

- https://docs.tavily.com/documentation/api-reference/endpoint/search
- https://docs.tavily.com/documentation/api-credits

## Configuration

```env
RESEARCH_PROVIDER=tavily
RESEARCH_API_KEY=tvly-your-real-key
RESEARCH_REQUEST_TIMEOUT_SECONDS=30
TAVILY_BASE_URL=https://api.tavily.com
```

Without both provider and key, `/api/v1/research/status` reports the integration as unavailable and live
search returns a structured `RESEARCH_PROVIDER_NOT_CONFIGURED` response. The UI does not substitute
sample sources.

## Data flow

1. An authenticated user submits a query, source type, result limit, and optional freshness range.
2. The provider returns URLs, titles, relevant content, metadata, and an optional generated answer.
3. Each returned source is stored with retrieval time, query, provider, request ID, score, and publication
   date where available.
4. The user selects stored sources before creating a draft.
5. AI generation resolves every selected source through the user's ownership boundary, supplies source
   context to the provider, and links the generated post to those source records.

Provider summaries and generated posts must still be reviewed. The interface explicitly asks users to
verify important claims against the underlying sources.

## API and workers

- `GET /api/v1/research/status` reports configuration without exposing credentials.
- `POST /api/v1/research/search` performs live research and stores results.
- `GET /api/v1/research/sources` lists the authenticated user's recent source library.
- `DELETE /api/v1/research/sources/{source_id}` removes an owned source.
- `POST /api/v1/ai/posts/generate` accepts up to ten owned `research_source_ids`.
- `workers.research_tasks.research_topic` provides the same research workflow on the `research` queue.

Automated tests replace the provider boundary and do not make billable Tavily requests.
