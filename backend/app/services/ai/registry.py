from app.core.config import Settings
from app.services.ai.contracts import AIProvider
from app.services.ai.nvidia_provider import NvidiaProvider
from app.services.ai.openai_provider import OpenAIProvider


class AIProviderRegistry:
    def __init__(self) -> None:
        self._providers: dict[str, AIProvider] = {}

    def register(self, provider: AIProvider) -> None:
        name = provider.name.strip().lower()
        if not name:
            raise ValueError("AI provider name cannot be empty")
        if name in self._providers:
            raise ValueError(f"AI provider '{name}' is already registered")
        self._providers[name] = provider

    def get(self, name: str) -> AIProvider | None:
        return self._providers.get(name.strip().lower())

    def names(self) -> list[str]:
        return sorted(self._providers)


def create_provider_registry(settings: Settings) -> AIProviderRegistry:
    registry = AIProviderRegistry()
    registry.register(OpenAIProvider(settings))
    registry.register(NvidiaProvider(settings))
    return registry
