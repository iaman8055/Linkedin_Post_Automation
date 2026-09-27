import json
from typing import Any

import httpx

from app.core.config import Settings
from app.services.ai.contracts import (
    AIGenerationRequest,
    AIGenerationResult,
    AIMessageRole,
    AIProviderError,
    AIUsage,
)


class OpenAIProvider:
    name = "openai"

    def __init__(self, settings: Settings, client: httpx.Client | None = None) -> None:
        self.settings = settings
        self.client = client

    def generate(self, request: AIGenerationRequest) -> AIGenerationResult:
        if self.settings.ai_api_key is None:
            raise AIProviderError("OPENAI_NOT_CONFIGURED", "OpenAI API key is missing.")

        payload = self._build_payload(request)
        headers = {
            "Authorization": f"Bearer {self.settings.ai_api_key.get_secret_value()}",
            "Content-Type": "application/json",
        }
        try:
            if self.client is not None:
                response = self.client.post("/responses", headers=headers, json=payload)
            else:
                with httpx.Client(
                    base_url=self.settings.openai_base_url.rstrip("/"),
                    timeout=self.settings.ai_request_timeout_seconds,
                ) as client:
                    response = client.post("/responses", headers=headers, json=payload)
        except httpx.TimeoutException as exc:
            raise AIProviderError(
                "OPENAI_TIMEOUT", "OpenAI request timed out.", retryable=True
            ) from exc
        except httpx.RequestError as exc:
            raise AIProviderError(
                "OPENAI_CONNECTION_ERROR", "OpenAI request failed.", retryable=True
            ) from exc

        if response.is_error:
            retryable = response.status_code in {408, 409, 429} or response.status_code >= 500
            raise AIProviderError(
                f"OPENAI_HTTP_{response.status_code}",
                "OpenAI returned an error.",
                retryable=retryable,
            )

        try:
            data = response.json()
            text = self._extract_output_text(data)
            structured = json.loads(text) if request.response_schema is not None else None
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise AIProviderError(
                "OPENAI_INVALID_RESPONSE", "OpenAI response was invalid."
            ) from exc

        usage_data = data.get("usage") or {}
        return AIGenerationResult(
            text=text,
            provider=self.name,
            model=data.get("model") or request.model,
            provider_request_id=data.get("id"),
            finish_reason=data.get("status"),
            usage=AIUsage(
                input_tokens=usage_data.get("input_tokens"),
                output_tokens=usage_data.get("output_tokens"),
                total_tokens=usage_data.get("total_tokens"),
            ),
            structured_output=structured,
        )

    @staticmethod
    def _build_payload(request: AIGenerationRequest) -> dict[str, Any]:
        instructions = "\n\n".join(
            message.content for message in request.messages if message.role == AIMessageRole.SYSTEM
        )
        model_input = [
            {"role": message.role.value, "content": message.content}
            for message in request.messages
            if message.role != AIMessageRole.SYSTEM
        ]
        payload: dict[str, Any] = {
            "model": request.model,
            "input": model_input,
            "max_output_tokens": request.max_output_tokens,
            "store": False,
        }
        if instructions:
            payload["instructions"] = instructions
        if request.temperature is not None:
            payload["temperature"] = request.temperature
        if request.response_schema is not None:
            payload["text"] = {
                "format": {
                    "type": "json_schema",
                    "name": request.metadata.get("schema_name", "structured_response"),
                    "strict": True,
                    "schema": request.response_schema,
                }
            }
        return payload

    @staticmethod
    def _extract_output_text(data: dict[str, Any]) -> str:
        text_parts = [
            content["text"]
            for item in data.get("output", [])
            if item.get("type") == "message"
            for content in item.get("content", [])
            if content.get("type") == "output_text" and content.get("text")
        ]
        if not text_parts:
            raise ValueError("No output text returned")
        return "".join(text_parts)
