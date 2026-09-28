# AI scoring and hook generation

Milestone B adds structured content scoring and categorized hook generation through the existing
provider-neutral AI execution layer. Prompts remain centralized in `ContentIntelligenceService`, and
provider output is validated before it reaches the UI.

## Post scoring

`POST /api/v1/ai/posts/{post_id}/score` evaluates an owned post across hook, clarity, readability,
engagement potential, storytelling, value, CTA, structure, and authenticity. Every dimension is bounded
from 0 to 100 and includes an explanation. Duplicate or incomplete dimensions are rejected as invalid
provider output.

The score is an AI-based writing-quality assessment. It does not predict virality, reach, impressions,
or actual LinkedIn performance. The UI displays this limitation alongside every result. **Improve post**
uses the existing writing assistant and still requires the user to review and apply its suggestion.

## Hook generation

`POST /api/v1/ai/hooks/generate` accepts a topic and a count from five to ten. Results use the supported
curiosity, contrarian, story, question, data-driven, personal-experience, mistake, lesson, and bold-
statement categories. Duplicate hooks and unexpected result counts are rejected.

Selecting **Use hook** inserts the text into the manual editor. It does not save, approve, schedule, or
publish the content automatically.
