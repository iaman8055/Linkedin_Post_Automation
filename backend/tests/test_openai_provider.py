import json

import httpx
import pytest
from pydantic import SecretStr

from app.core.config import Settings
from app.services.ai.contracts import AIGenerationRequest, AIMessage, AIMessageRole, AIProviderError
from app.services.ai.openai_provider import OpenAIProvider


def request() -> AIGenerationRequest:
    return AIGenerationRequest(
        messages=[
            AIMessage(role=AIMessageRole.SYSTEM, content="System rules"),
            AIMessage(role=AIMessageRole.USER, content="Generate posts"),
        ],
        model="configured-model",
        max_output_tokens=800,
        response_schema={
            "type": "object",
            "properties": {"posts": {"type": "array"}},
            "required": ["posts"],
            "additionalProperties": False,
        },
        metadata={"schema_name": "post_drafts"},
    )


def test_openai_provider_uses_responses_api_without_storage() -> None:
    captured: dict[str, object] = {}

    def handler(http_request: httpx.Request) -> httpx.Response:
        captured.update(json.loads(http_request.content))
        assert http_request.headers["Authorization"] == "Bearer test-api-key"
        output = json.dumps({"posts": []})
        return httpx.Response(
            200,
            json={
                "id": "resp_123",
                "model": "resolved-model",
                "status": "completed",
                "output": [
                    {
                        "type": "message",
                        "content": [{"type": "output_text", "text": output}],
                    }
                ],
                "usage": {"input_tokens": 10, "output_tokens": 5, "total_tokens": 15},
            },
        )

    client = httpx.Client(
        transport=httpx.MockTransport(handler), base_url="https://api.openai.com/v1"
    )
    settings = Settings(ai_api_key=SecretStr("test-api-key"))
    result = OpenAIProvider(settings, client).generate(request())

    assert captured["store"] is False
    assert captured["instructions"] == "System rules"
    assert captured["text"] == {
        "format": {
            "type": "json_schema",
            "name": "post_drafts",
            "strict": True,
            "schema": request().response_schema,
        }
    }
    assert result.provider_request_id == "resp_123"
    assert result.structured_output == {"posts": []}
    assert result.usage.total_tokens == 15
    client.close()


def test_openai_provider_requires_a_key() -> None:
    with pytest.raises(AIProviderError) as error:
        OpenAIProvider(Settings(ai_api_key=None)).generate(request())
    assert error.value.code == "OPENAI_NOT_CONFIGURED"
