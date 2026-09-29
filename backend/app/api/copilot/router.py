from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.ai.router import get_provider_registry
from app.api.dependencies import AppSettings, CurrentUser, DatabaseSession
from app.schemas.copilot import (
    ConversationListResponse,
    ConversationResponse,
    ConversationSummaryResponse,
    CopilotActionResponse,
    CopilotMessageResponse,
    CreateConversationRequest,
    SendCopilotMessageRequest,
    SendCopilotMessageResponse,
)
from app.services.ai.copilot import CopilotService
from app.services.ai.registry import AIProviderRegistry

router = APIRouter(prefix="/copilot")
ProviderRegistry = Annotated[AIProviderRegistry, Depends(get_provider_registry)]


def service(
    session: DatabaseSession, settings: AppSettings, registry: ProviderRegistry
) -> CopilotService:
    return CopilotService(session, settings, registry)


CopilotServiceDependency = Annotated[CopilotService, Depends(service)]


@router.post("/conversations", response_model=ConversationResponse, status_code=201)
def create_conversation(
    payload: CreateConversationRequest,
    user: CurrentUser,
    copilot: CopilotServiceDependency,
) -> ConversationResponse:
    conversation = copilot.create_conversation(user.id, payload.title)
    return ConversationResponse(
        **ConversationSummaryResponse.model_validate(conversation).model_dump(), messages=[]
    )


@router.get("/conversations", response_model=ConversationListResponse)
def list_conversations(
    user: CurrentUser, copilot: CopilotServiceDependency
) -> ConversationListResponse:
    return ConversationListResponse(items=[
        ConversationSummaryResponse.model_validate(item)
        for item in copilot.list_conversations(user.id)
    ])


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
def get_conversation(
    conversation_id: UUID, user: CurrentUser, copilot: CopilotServiceDependency
) -> ConversationResponse:
    return conversation_response(copilot, user.id, conversation_id)


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=SendCopilotMessageResponse,
)
def send_message(
    conversation_id: UUID,
    payload: SendCopilotMessageRequest,
    user: CurrentUser,
    copilot: CopilotServiceDependency,
) -> SendCopilotMessageResponse:
    conversation, assistant, action = copilot.send_message(user.id, conversation_id, payload)
    assistant_response = message_response(assistant, action)
    return SendCopilotMessageResponse(
        conversation=conversation_response(copilot, user.id, conversation.id),
        assistant_message=assistant_response,
    )


@router.post("/actions/{action_id}/confirm", response_model=CopilotActionResponse)
def confirm_action(
    action_id: UUID, user: CurrentUser, copilot: CopilotServiceDependency
) -> CopilotActionResponse:
    return CopilotActionResponse.model_validate(copilot.confirm_action(user.id, action_id))


@router.post("/actions/{action_id}/cancel", response_model=CopilotActionResponse)
def cancel_action(
    action_id: UUID, user: CurrentUser, copilot: CopilotServiceDependency
) -> CopilotActionResponse:
    return CopilotActionResponse.model_validate(copilot.cancel_action(user.id, action_id))


def conversation_response(
    copilot: CopilotService, user_id: UUID, conversation_id: UUID
) -> ConversationResponse:
    conversation = copilot.get_conversation(user_id, conversation_id)
    return ConversationResponse(
        **ConversationSummaryResponse.model_validate(conversation).model_dump(),
        messages=[
            message_response(message, copilot.action_for_message(user_id, message.id))
            for message in conversation.messages
        ],
    )


def message_response(
    message: object, action: object | None
) -> CopilotMessageResponse:
    response = CopilotMessageResponse.model_validate(message)
    return response.model_copy(update={
        "action": CopilotActionResponse.model_validate(action) if action is not None else None
    })
