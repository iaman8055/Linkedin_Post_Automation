import json
from typing import Any

import httpx

from app.core.config import Settings
from app.services.ai.contracts import (
    AIGenerationRequest,
    AIGenerationResult,
    AIProviderError,
    AIUsage,
)


class NvidiaProvider:
    """NVIDIA API Catalog/NIM adapter for OpenAI-compatible chat completions."""

    name = "nvidia"

    def __init__(self, settings: Settings, client: httpx.Client | None = None) -> None:
        self.settings = settings
        self.client = client

    def generate(self, request: AIGenerationRequest) -> AIGenerationResult:
        api_key = self.settings.nvidia_api_key or self.settings.ai_api_key
        if api_key is None:
            raise AIProviderError("NVIDIA_NOT_CONFIGURED", "NVIDIA API key is missing.")

        headers = {
            "Authorization": f"Bearer {api_key.get_secret_value()}",
            "Content-Type": "application/json",
        }
        try:
            if self.client is not None:
                response = self.client.post(
                    "/chat/completions", headers=headers, json=self._build_payload(request)
                )
            else:
                with httpx.Client(
                    base_url=self.settings.nvidia_base_url.rstrip("/"),
                    timeout=self.settings.ai_request_timeout_seconds,
                ) as client:
                    response = client.post(
                        "/chat/completions", headers=headers, json=self._build_payload(request)
                    )
        except httpx.TimeoutException as exc:
            raise AIProviderError(
                "NVIDIA_TIMEOUT", "NVIDIA request timed out.", retryable=True
            ) from exc
        except httpx.RequestError as exc:
            raise AIProviderError(
                "NVIDIA_CONNECTION_ERROR", "NVIDIA request failed.", retryable=True
            ) from exc

        if response.is_error:
            retryable = response.status_code in {408, 409, 429} or response.status_code >= 500
            raise AIProviderError(
                f"NVIDIA_HTTP_{response.status_code}",
                "NVIDIA returned an error.",
                retryable=retryable,
            )

        try:
            data = response.json()
            choice = data["choices"][0]
            text = choice["message"]["content"]
            if not isinstance(text, str) or not text:
                raise ValueError("No message content returned")
            structured = json.loads(text) if request.response_schema is not None else None
        except (KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise AIProviderError(
                "NVIDIA_INVALID_RESPONSE", "NVIDIA response was invalid."
            ) from exc

        usage_data = data.get("usage") or {}
        return AIGenerationResult(
            text=text,
            provider=self.name,
            model=data.get("model") or request.model,
            provider_request_id=data.get("id"),
            finish_reason=choice.get("finish_reason"),
            usage=AIUsage(
                input_tokens=usage_data.get("prompt_tokens"),
                output_tokens=usage_data.get("completion_tokens"),
                total_tokens=usage_data.get("total_tokens"),
            ),
            structured_output=structured,
        )

    @staticmethod
    def _build_payload(request: AIGenerationRequest) -> dict[str, Any]:
        messages = [message.model_dump(mode="json") for message in request.messages]
        if request.response_schema is not None:
            schema_instruction = (
                "Return only one valid JSON value matching this JSON Schema exactly. "
                "Do not wrap it in Markdown or add explanatory text:\n"
                f"{json.dumps(request.response_schema, separators=(',', ':'))}"
            )
            messages.insert(0, {"role": "system", "content": schema_instruction})
        payload: dict[str, Any] = {
            "model": request.model,
            "messages": messages,
            "max_tokens": request.max_output_tokens,
            "stream": False,
            "chat_template_kwargs": {"enable_thinking": False},
        }
        if request.temperature is not None:
            payload["temperature"] = request.temperature
        return payload
