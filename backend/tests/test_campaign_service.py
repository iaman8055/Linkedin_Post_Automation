from uuid import UUID

import pytest
from sqlalchemy.orm import Session

from app.core.errors import ApplicationError
from app.models.enums import ApprovalMode, CampaignStatus
from app.models.post import Post
from app.models.user import User
from app.schemas.campaign import CampaignCreate, CampaignUpdate
from app.services.campaigns import CampaignService


def create_user(session: Session, email: str) -> User:
    user = User(email=email, password_hash="hashed", display_name="Campaign Owner")
    session.add(user)
    session.commit()
    return user


def create_campaign(service: CampaignService, user_id: UUID) -> UUID:
    campaign = service.create(
        user_id,
        CampaignCreate(
            name="AI Week",
            topic="Artificial Intelligence",
            duration_days=7,
            timezone="Asia/Calcutta",
        ),
    )
    return campaign.id


def test_campaign_crud_defaults_to_manual_and_enforces_transitions(
    db_session: Session,
) -> None:
    user = create_user(db_session, "campaign-owner@example.com")
    service = CampaignService(db_session)
    campaign_id = create_campaign(service, user.id)

    campaign = service.get(user.id, campaign_id)
    assert campaign.status == CampaignStatus.DRAFT
    assert campaign.approval_mode == ApprovalMode.MANUAL

    updated = service.update(
        user.id,
        campaign_id,
        CampaignUpdate(description="  Seven useful posts.  ", approval_mode=ApprovalMode.AUTOMATIC),
    )
    assert updated.description == "Seven useful posts."
    assert updated.approval_mode == ApprovalMode.AUTOMATIC

    active = service.transition(user.id, campaign_id, CampaignStatus.ACTIVE)
    assert active.status == CampaignStatus.ACTIVE
    paused = service.transition(user.id, campaign_id, CampaignStatus.PAUSED)
    assert paused.status == CampaignStatus.PAUSED

    with pytest.raises(ApplicationError) as invalid:
        service.transition(user.id, campaign_id, CampaignStatus.DRAFT)
    assert invalid.value.code == "INVALID_CAMPAIGN_TRANSITION"


def test_campaign_post_organization_is_user_scoped(db_session: Session) -> None:
    owner = create_user(db_session, "campaign-post-owner@example.com")
    other = create_user(db_session, "campaign-post-other@example.com")
    service = CampaignService(db_session)
    campaign_id = create_campaign(service, owner.id)
    post = Post(user_id=owner.id, content="Owned draft")
    other_post = Post(user_id=other.id, content="Private draft")
    db_session.add_all([post, other_post])
    db_session.commit()

    campaign = service.add_post(owner.id, campaign_id, post.id)
    assert campaign.posts == [post]
    assert campaign.posts[0].campaign_id == campaign_id

    with pytest.raises(ApplicationError) as not_found:
        service.add_post(owner.id, campaign_id, other_post.id)
    assert not_found.value.code == "POST_NOT_FOUND"

    campaign = service.remove_post(owner.id, campaign_id, post.id)
    assert campaign.posts == []


def test_terminal_campaign_is_immutable_and_hidden_from_other_users(
    db_session: Session,
) -> None:
    owner = create_user(db_session, "terminal-owner@example.com")
    other = create_user(db_session, "terminal-other@example.com")
    service = CampaignService(db_session)
    campaign_id = create_campaign(service, owner.id)

    with pytest.raises(ApplicationError) as hidden:
        service.get(other.id, campaign_id)
    assert hidden.value.code == "CAMPAIGN_NOT_FOUND"

    service.transition(owner.id, campaign_id, CampaignStatus.CANCELLED)
    with pytest.raises(ApplicationError) as immutable:
        service.update(owner.id, campaign_id, CampaignUpdate(name="Changed"))
    assert immutable.value.code == "CAMPAIGN_NOT_EDITABLE"
