# Writing profiles

Writing profiles store a user's reusable AI style preferences. They are user-owned records and are
available in the frontend under `/settings/writing-profiles` and from the API under
`/api/v1/writing-profiles`.

## Preferences

A profile can define tone, sentence style, language, emoji preference, paragraph length, technical
depth, CTA preference, preferred vocabulary, and bounded additional guidance. These fields guide AI
generation; they do not rewrite existing posts or publish content.

The first profile created for a user becomes the default. Setting another profile as default clears the
previous default in the same transaction. Deleting the default promotes the next remaining profile.

## AI generation

`POST /api/v1/ai/posts/generate` accepts an optional `writing_profile_id`. The service resolves that ID
through the authenticated user's repository boundary before generation, so another user's profile cannot
be selected. Style data is added to the structured content requirements while the system message retains
authority over safety and output rules.

Selecting a profile is optional. Existing generation requests without a profile continue to use their
explicit tone and language fields.

## API

- `POST /api/v1/writing-profiles` creates a profile.
- `GET /api/v1/writing-profiles` lists owned profiles with the default first.
- `GET /api/v1/writing-profiles/{profile_id}` returns one owned profile.
- `PATCH /api/v1/writing-profiles/{profile_id}` updates profile preferences or makes it the default.
- `DELETE /api/v1/writing-profiles/{profile_id}` deletes a profile and safely reassigns the default.

Campaigns already carry an optional writing-profile relationship in the domain model. Applying profiles
to future campaign-wide generation belongs with that generation workflow rather than being simulated in
the current campaign UI.
