# AI Content Studio

Milestone A expands the existing post generator and editor into one connected content workflow. It does
not introduce a second post model or bypass the existing draft lifecycle.

## Generation brief

`POST /api/v1/ai/posts/generate` remains backward compatible and now also accepts a post type,
keywords, personal experience, reference material, and desired hashtags. Supported post types include
educational, storytelling, personal experience, technical, career advice, industry insight, case study,
opinion, promotional, question, and poll. Audience remains free text so presets and custom audiences use
the same validated field.

Every generated variation is stored as an owned `DRAFT`. Multiple requested variations must remain
distinct, and none are approved, scheduled, or published automatically. Writing profiles and saved
research sources continue to flow through the existing generation service.

## Writing assistant

`POST /api/v1/ai/posts/{post_id}/assist` supports rewrite, shorten, expand, improve, change tone,
improve hook, improve CTA, and add hashtags. The service:

- operates only on an owned draft;
- uses the configured provider-neutral AI execution layer;
- validates structured output and the LinkedIn character limit;
- returns a suggestion without changing the stored draft.

The editor presents the suggestion separately. The user must explicitly choose **Use suggestion** and
then save the draft. This preserves the review requirement and prevents silent AI rewrites.

## Existing lifecycle

The studio reuses the existing preview, quality checker, media panel, approval transition and calendar
scheduler. Publishing still requires explicit user confirmation through the authorized LinkedIn flow.
