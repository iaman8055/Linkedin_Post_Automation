import json

import httpx
import pytest
from pydantic import SecretStr

from app.core.config import Settings
from app.services.ai.contracts import AIGenerationRequest, AIMessage, AIMessageRole, AIProviderError
from app.services.ai.nvidia_provider import NvidiaProvider


def request() -> AIGenerationRequest:
    return AIGenerationRequest(
        messages=[
            AIMessage(role=AIMessageRole.SYSTEM, content="Return JSON"),
            AIMessage(role=AIMessageRole.USER, content="Generate posts"),
        ],
        model="nvidia/test-nemotron",
        temperature=0.4,
        max_output_tokens=800,
        response_schema={"type": "object", "properties": {"posts": {"type": "array"}}},
    )


def test_nvidia_provider_uses_supported_chat_completion_payload() -> None:
    captured: dict[str, object] = {}

    def handler(http_request: httpx.Request) -> httpx.Response:
        captured.update(json.loads(http_request.content))
        assert http_request.headers["Authorization"] == "Bearer nvidia-test-key"
        return httpx.Response(
            200,
            json={
                "id": "chatcmpl_123",
                "model": "nvidia/resolved-nemotron",
                "choices": [{
                    "message": {"role": "assistant", "content": '{"posts": []}'},
                    "finish_reason": "stop",
                }],
                "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
            },
        )

    client = httpx.Client(
        transport=httpx.MockTransport(handler),
        base_url="https://integrate.api.nvidia.com/v1",
    )
    result = NvidiaProvider(
        Settings(nvidia_api_key=SecretStr("nvidia-test-key")), client
    ).generate(request())

    assert captured["stream"] is False
    assert "nvext" not in captured
    assert captured["chat_template_kwargs"] == {"enable_thinking": False}
    messages = captured["messages"]
    assert isinstance(messages, list)
    assert "JSON Schema" in messages[0]["content"]
    assert result.structured_output == {"posts": []}
    assert result.provider_request_id == "chatcmpl_123"
    assert result.usage.total_tokens == 15
    client.close()


def test_nvidia_provider_requires_a_key() -> None:
    with pytest.raises(AIProviderError) as error:
        NvidiaProvider(Settings(nvidia_api_key=None, ai_api_key=None)).generate(request())
    assert error.value.code == "NVIDIA_NOT_CONFIGURED"
