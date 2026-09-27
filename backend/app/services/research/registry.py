from app.core.config import Settings
from app.services.research.contracts import ResearchProvider
from app.services.research.tavily import TavilyResearchProvider


def create_research_provider(settings: Settings) -> ResearchProvider | None:
    selected = settings.research_provider.strip().lower() if settings.research_provider else None
    if selected != "tavily" or settings.research_api_key is None:
        return None
    key = settings.research_api_key.get_secret_value()
    if not key:
        return None
    return TavilyResearchProvider(
        key, settings.tavily_base_url, settings.research_request_timeout_seconds
    )
