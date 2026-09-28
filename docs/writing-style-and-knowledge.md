# Writing style and personal knowledge

Milestone D extends the existing writing-profile and AI-generation architecture. It does not create a
parallel generator.

## Writing style analysis

`POST /api/v1/writing-profiles/analyze` analyzes either explicitly selected post IDs or up to 30 recent
posts owned by the authenticated user. At least two samples are required. The AI returns observable
style characteristics and a suggested, editable writing profile.

The result is labelled as an AI approximation. Analysis does not silently change an existing profile;
the user must explicitly create the suggested profile before it can be used for generation.

## Personal knowledge

Knowledge items are managed through `/api/v1/knowledge` and the `/knowledge` workspace. Supported
categories include projects, resume details, skills, experience, articles, notes, achievements, previous
content, and technical knowledge.

All queries enforce user ownership. Items are private by default and are not automatically added to AI
requests. The create-post form sends only the item IDs checked by the user for that individual request.
The backend resolves those IDs against the authenticated owner and treats their contents as untrusted
reference material rather than executable prompt instructions.

Apply the migration before using the feature:

```powershell
cd backend
uv run alembic upgrade head
```
