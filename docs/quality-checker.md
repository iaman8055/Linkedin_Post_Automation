# AI quality checker

Phase 18 adds an advisory, non-destructive review to saved posts. Users start it explicitly from the post
editor. The checker returns structured issues and never changes post content.

## Checks

Deterministic checks run without an external provider:

- excessive hashtags;
- excessive emoji use;
- very short content;
- excessive blank spacing;
- repeated sentences;
- exact duplicate content within the authenticated user's library.

When a real AI provider and model are configured, the same request also reviews grammar, unsupported
claims, potentially misleading claims, and formatting. The post is supplied as untrusted content and the
provider is explicitly instructed not to rewrite it.

If AI is unavailable, deterministic results are still returned with `ai_review_performed: false`. The UI
labels this as a partial structural check instead of implying that grammar or claims were reviewed.

## Response

`POST /api/v1/posts/{post_id}/quality-check` returns:

```json
{
  "post_id": "...",
  "status": "warning",
  "issues": [
    {
      "type": "unsupported_claim",
      "severity": "medium",
      "message": "A numerical claim has no supporting context.",
      "suggestion": "Add a source or qualify the claim."
    }
  ],
  "ai_review_performed": true,
  "job_id": "..."
}
```

High-severity issues produce `fail`, lower-severity issues produce `warning`, and an empty issue list
produces `pass`. These statuses are review aids, not automated publishing decisions.

## Data and safety

- Post ownership is checked before any analysis.
- AI execution uses the existing provider abstraction and creates a sanitized `AIJob` audit record.
- Prompt content is not stored in the AI job metadata.
- Results are not persisted as post mutations.
- Editing or saving the post clears the displayed result so advice cannot appear current after changes.
- Automated tests use local provider boundaries and never call a real AI API.
