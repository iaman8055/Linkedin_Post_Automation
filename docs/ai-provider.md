# AI provider foundation

Phase 6 introduced the provider-neutral execution boundary. Phase 8 adds a real OpenAI Responses API
adapter and LinkedIn draft generation. No successful provider response is simulated in production.

## Design

Application services submit an `AIGenerationRequest` through `AIExecutionService`. The service resolves
the configured adapter from `AIProviderRegistry`, records the attempt in `AIJob`, and returns a normalized
`AIGenerationResult`. Provider SDK types and errors must remain inside each adapter.

The core contracts support chat messages, model selection, temperature, output limits, optional structured
output schemas, token usage, provider request identifiers, and retry classification. Later content services
can depend on this contract without depending directly on a vendor SDK.

## Configuration

The following environment variables are available:

```dotenv
AI_PROVIDER=
AI_MODEL=
AI_API_KEY=
AI_REQUEST_TIMEOUT_SECONDS=60
AI_MAX_OUTPUT_TOKENS=4000
```

Set `AI_PROVIDER=openai`, choose an available model in `AI_MODEL`, and supply the key in `AI_API_KEY`.
Leaving the provider blank keeps AI execution disabled. The
authenticated `GET /api/v1/ai/status` endpoint reports configuration and adapter availability without
returning credentials.

The OpenAI adapter sends `store: false`, uses strict Structured Outputs for generated drafts, applies
the configured timeout, and normalizes retryable transport and HTTP failures. The API key is sent only
in the provider authorization header.

## Adding a real provider

A provider integration should:

1. Implement the `AIProvider` protocol in `app/services/ai/contracts.py`.
2. Translate normalized requests into the provider's current API format.
3. Convert provider responses into `AIGenerationResult`.
4. Convert provider failures into `AIProviderError`, accurately marking retryable failures.
5. Register the adapter once during application startup.
6. Keep API keys in environment-backed settings and never log them.

Before adding an adapter, verify the provider's current authentication, models, request and response
formats, structured-output behavior, safety policies, rate limits, and data-retention controls against its
official documentation.

## Data handling

`AIJob` stores operational metadata such as job type, provider, model, status, request identifier, token
usage, and sanitized errors. Prompts and generated text are intentionally not stored in job metadata.
Future features that persist generated content must do so in the appropriate user-owned domain model and
apply its authorization rules.

Tests use local test doubles and HTTP transports at the provider boundary. They are test-only and are
not registered in the application. Automated tests never make real OpenAI calls.

## Post generation

`POST /api/v1/ai/posts/generate` accepts topic, subject, audience, tone, language, length, CTA, hashtag,
and post-count settings. It supports one to ten posts per request. Results are validated for schema,
requested count, uniqueness, and LinkedIn length before being stored as user-owned `DRAFT` posts.
Generated content is never published automatically.

Implementation references:

- [OpenAI text generation guide](https://developers.openai.com/api/docs/guides/text)
- [OpenAI Structured Outputs guide](https://developers.openai.com/api/docs/guides/structured-outputs)
