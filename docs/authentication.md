# Authentication

Phase 3 provides local account authentication under `/api/v1/auth`.

## Endpoints

- `POST /register` creates an account and returns an access/refresh token pair.
- `POST /login` verifies credentials and returns a new token pair.
- `POST /refresh` rotates a refresh token and returns a new pair.
- `POST /logout` revokes the submitted refresh-token family.
- `GET /me` returns the authenticated user.
- `POST /verify-email` consumes an email-verification token.
- `POST /reset-password` consumes a password-reset token and revokes existing refresh tokens.
- `POST /forgot-password` and `/resend-verification` return an explicit 503 until a real
  transactional email provider is configured.

## Token design

Access tokens are short-lived signed JWTs containing issuer, audience, subject, expiry, issued-at,
token type, and unique token ID claims. Refresh and account-action tokens are cryptographically random
opaque values. Only keyed SHA-256 hashes of opaque tokens are stored.

Refresh tokens rotate on use. Reuse of a consumed refresh token revokes the entire token family.
Database row locks protect one-time token consumption from concurrent requests. Password changes also
revoke all active refresh tokens for the user.

## Passwords

Passwords are hashed with Argon2 through `pwdlib`. The API accepts passwords from 12 to 128 characters.
Login performs a password verification operation even when the account does not exist to reduce timing
differences.

## Email delivery boundary

`AuthenticationEmailSender` defines the required integration with a real transactional email service.
No development or production endpoint claims to send mail while this provider is absent. Verification
and reset token issuance/consumption are implemented and tested independently of delivery.

## Rate limiting

`RateLimiter` defines the distributed rate-limiting boundary. A real Redis-backed implementation must
be installed before public deployment; authentication endpoints are not yet safe for public exposure
without it.

