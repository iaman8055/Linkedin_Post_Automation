from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.research import ResearchSearchRequest
from app.services.research.contracts import ResearchQuery, ResearchResponse, ResearchResult
from app.services.research.service import ResearchService


class StubResearchProvider:
    name = "stub"

    def search(self, query: ResearchQuery) -> ResearchResponse:
        assert query.query == "AI agents"
        return ResearchResponse(
            answer="Summary",
            provider=self.name,
            request_id="stub-1",
            results=[ResearchResult(
                title="Documented source",
                url="https://example.com/source",
                content="Evidence from the source.",
                score=0.8,
            )],
        )


def test_research_service_persists_real_provider_sources(db_session: Session) -> None:
    session = db_session
    user = User(email="research@example.com", password_hash="hashed", display_name="Researcher")
    session.add(user)
    session.commit()
    answer, provider, sources = ResearchService(session, StubResearchProvider()).search(
        user.id, ResearchSearchRequest(query="AI agents")
    )
    assert answer == "Summary"
    assert provider == "stub"
    assert sources[0].url == "https://example.com/source"
    assert sources[0].source_metadata["request_id"] == "stub-1"
