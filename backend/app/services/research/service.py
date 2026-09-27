from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.errors import ApplicationError
from app.models.research_source import ResearchSource
from app.repositories.research_source import ResearchSourceRepository
from app.schemas.research import ResearchSearchRequest
from app.services.research.contracts import ResearchProvider, ResearchProviderError, ResearchQuery


class ResearchService:
    def __init__(self, session: Session, provider: ResearchProvider | None) -> None:
        self.session = session
        self.provider = provider
        self.sources = ResearchSourceRepository(session)

    def search(
        self, user_id: UUID, payload: ResearchSearchRequest
    ) -> tuple[str | None, str, list[ResearchSource]]:
        if self.provider is None:
            raise ApplicationError(
                "RESEARCH_PROVIDER_NOT_CONFIGURED",
                "Research provider is not configured.",
                503,
            )
        try:
            response = self.provider.search(ResearchQuery(**payload.model_dump()))
        except ResearchProviderError as exc:
            status = 503 if exc.retryable else 502
            raise ApplicationError(exc.code, str(exc), status) from exc
        retrieved_at = datetime.now(UTC)
        sources = [
            self.sources.create_for_user(
                user_id,
                url=str(result.url),
                title=result.title,
                retrieved_at=retrieved_at,
                summary=None,
                relevant_content=result.content or None,
                source_metadata={
                    "provider": response.provider,
                    "request_id": response.request_id,
                    "score": result.score,
                    "published_at": (
                        result.published_at.isoformat() if result.published_at else None
                    ),
                    "query": payload.query,
                },
            )
            for result in response.results
        ]
        self.session.commit()
        for source in sources:
            self.session.refresh(source)
        return response.answer, response.provider, sources

    def list_sources(
        self, user_id: UUID, *, offset: int, limit: int
    ) -> tuple[list[ResearchSource], int]:
        return self.sources.list_recent(user_id, offset=offset, limit=limit)

    def delete(self, user_id: UUID, source_id: UUID) -> None:
        source = self.sources.get_for_user(source_id, user_id)
        if source is None:
            raise ApplicationError("RESEARCH_SOURCE_NOT_FOUND", "Research source not found.", 404)
        self.sources.delete(source)
        self.session.commit()
