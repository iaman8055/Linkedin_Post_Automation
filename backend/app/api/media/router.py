from uuid import UUID

from fastapi import APIRouter, Query, Request, Response, status

from app.api.dependencies import AppSettings, CurrentUser, DatabaseSession
from app.core.errors import ApplicationError
from app.schemas.media import PostMediaListResponse, PostMediaResponse
from app.services.media.service import PostMediaService
from app.services.media.storage import create_media_storage

router = APIRouter()


def media_service(session: DatabaseSession, settings: AppSettings) -> PostMediaService:
    return PostMediaService(session, settings, create_media_storage(settings))


@router.post(
    "/posts/{post_id}/media",
    response_model=PostMediaResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_media(
    post_id: UUID,
    request: Request,
    user: CurrentUser,
    session: DatabaseSession,
    settings: AppSettings,
    filename: str = Query(min_length=1, max_length=255),
) -> PostMediaResponse:
    content_type = request.headers.get("content-type", "").split(";", 1)[0].strip().lower()
    maximum = max(
        settings.storage_max_image_bytes,
        settings.storage_max_video_bytes,
        settings.storage_max_document_bytes,
    )
    content = bytearray()
    async for chunk in request.stream():
        content.extend(chunk)
        if len(content) > maximum:
            raise ApplicationError("MEDIA_SIZE_INVALID", "The uploaded file is too large.", 422)
    item = media_service(session, settings).upload(
        user.id,
        post_id,
        filename=filename,
        content_type=content_type,
        content=bytes(content),
    )
    return PostMediaResponse.model_validate(item)


@router.get("/posts/{post_id}/media", response_model=PostMediaListResponse)
def list_media(
    post_id: UUID,
    user: CurrentUser,
    session: DatabaseSession,
    settings: AppSettings,
) -> PostMediaListResponse:
    items = media_service(session, settings).list(user.id, post_id)
    return PostMediaListResponse(
        items=[PostMediaResponse.model_validate(item) for item in items]
    )


@router.get("/media/{media_id}/content")
def media_content(
    media_id: UUID,
    user: CurrentUser,
    session: DatabaseSession,
    settings: AppSettings,
) -> Response:
    item, content = media_service(session, settings).content(user.id, media_id)
    filename = str(item.metadata_json.get("filename") or "attachment")
    return Response(
        content=content,
        media_type=item.mime_type,
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )


@router.delete("/media/{media_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_media(
    media_id: UUID,
    user: CurrentUser,
    session: DatabaseSession,
    settings: AppSettings,
) -> Response:
    media_service(session, settings).delete(user.id, media_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
