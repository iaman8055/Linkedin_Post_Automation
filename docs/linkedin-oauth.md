# LinkedIn OAuth integration

Phase 4 implements LinkedIn's 3-legged OAuth 2.0 authorization-code flow using the **Sign in with
LinkedIn using OpenID Connect** product. Phase 5 adds an explicitly initiated text-only test post, and
Phase 12 reuses the verified Posts API client for due scheduled posts.

## Verified API contract

The implementation was checked against LinkedIn's current official documentation on September 27,
2026:

- Authorization endpoint: `https://www.linkedin.com/oauth/v2/authorization`
- Token endpoint: `https://www.linkedin.com/oauth/v2/accessToken`
- User-info endpoint: `https://api.linkedin.com/v2/userinfo`
- Default scopes: `openid profile email w_member_social`
- Product required: Sign in with LinkedIn using OpenID Connect
- Access tokens currently report their lifetime through `expires_in`; documentation describes a
  typical 60-day lifetime.
- Programmatic refresh tokens are restricted to approved Marketing Developer Platform partners. The
  application therefore accepts and encrypts a refresh token when LinkedIn returns one, but never
  assumes one will be present.
- `w_member_social` comes from the self-service **Share on LinkedIn** product and is required for
  member publishing.
- Rate limits apply at application and member levels, reset daily at midnight UTC, and the Developer
  Portal is the source of truth for limits available to a particular application.

Official references:

- [Authorization code flow](https://learn.microsoft.com/en-us/linkedin/shared/authentication/authorization-code-flow)
- [Sign in with LinkedIn using OpenID Connect](https://learn.microsoft.com/en-us/linkedin/consumer/integrations/self-serve/sign-in-with-linkedin-v2)
- [Programmatic refresh tokens](https://learn.microsoft.com/en-us/linkedin/shared/authentication/programmatic-refresh-tokens)
- [LinkedIn API rate limiting](https://learn.microsoft.com/en-us/linkedin/shared/api-guide/concepts/rate-limits)
- [Getting access and open permissions](https://learn.microsoft.com/en-us/linkedin/shared/authentication/getting-access)
- [Posts API](https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/posts-api)
- [Marketing API versioning](https://learn.microsoft.com/en-us/linkedin/marketing/versioning)

## Developer Portal setup

1. Create or select a LinkedIn application.
2. Request the **Sign in with LinkedIn using OpenID Connect** and **Share on LinkedIn** products.
3. Add the exact callback URL configured as `LINKEDIN_REDIRECT_URI` to the application's authorized
   redirect URLs. Local frontend development uses
   `http://localhost:5173/settings/linkedin/callback`. Use HTTPS outside local development.
4. Configure the client ID, client secret, and a dedicated Fernet encryption key in `.env`.
5. Never place the client secret or access tokens in browser URLs or logs.

## Security design

- The connect route requires an authenticated application user.
- OAuth state is signed, audience-bound, issuer-bound, short-lived, and tied to that user.
- Access and optional refresh tokens are encrypted before persistence.
- API responses never expose LinkedIn tokens.
- Disconnecting removes encrypted tokens while preserving non-secret connection history.
- External errors are converted to structured application errors without leaking provider responses.

## Test-post publishing

`POST /api/v1/linkedin/{account_id}/test-post` publishes one public, text-only member post. It requires
an authenticated application user, a connected account containing `w_member_social`, and an
`Idempotency-Key` header between 16 and 128 characters.

The integration uses `POST https://api.linkedin.com/rest/posts`, `Linkedin-Version: 202609`, and
`X-Restli-Protocol-Version: 2.0.0`. A successful response must be HTTP 201 and include the post URN in
`x-restli-id`. The local post and publishing log record both successes and failures.

API versions are supported for a limited period. Review LinkedIn's versioning page regularly and update
`LINKEDIN_API_VERSION` before the configured version is sunset.

Repeated test-post requests with the same user-scoped idempotency key return the previously successful
result and do not call LinkedIn again. Scheduled publishing uses a deterministic key per schedule attempt.
Only definitive rate-limit failures retry automatically; a network timeout can leave the external result
uncertain and is never retried automatically.

## Automatic scheduled publishing

Celery Beat checks for due schedules once per minute. A dispatcher claims eligible rows using PostgreSQL
row locks and `SKIP LOCKED`, then sends each claimed identifier to the publishing queue. The publishing
worker requires a connected account with `w_member_social`, decrypts its token only in worker memory,
calls the same current `/rest/posts` endpoint, and records the result in `publishing_logs`.

The implementation was rechecked against the official Posts API and Share on LinkedIn documentation on
September 27, 2026. The Posts API remains the current replacement for `ugcPosts`; text-only organic posts
require `w_member_social`, `Linkedin-Version`, and `X-Restli-Protocol-Version: 2.0.0`.
