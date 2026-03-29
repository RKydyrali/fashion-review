from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Response, UploadFile, status

from app.api.deps import CurrentUser, get_try_on_service
from app.schemas.try_on import TryOnSessionRead
from app.services.try_on_service import TryOnService

router = APIRouter(tags=["try-on"])


@router.post("/try-on/sessions", response_model=TryOnSessionRead, status_code=status.HTTP_201_CREATED)
def create_try_on_session(
    response: Response,
    current_user: CurrentUser,
    user_image: UploadFile = File(...),
    product_ids: list[int] = Form(...),
    service: Annotated[TryOnService, Depends(get_try_on_service)] = None,
) -> TryOnSessionRead:
    session_read, created = service.create_or_reuse_session_from_upload(
        user_id=current_user.id,
        product_ids=product_ids,
        upload=user_image,
    )
    if not created:
        response.status_code = status.HTTP_200_OK
    return session_read


@router.get("/try-on/sessions/{session_id}", response_model=TryOnSessionRead)
def get_try_on_session(
    session_id: int,
    current_user: CurrentUser,
    service: Annotated[TryOnService, Depends(get_try_on_service)],
) -> TryOnSessionRead:
    return service.get_session(user_id=current_user.id, session_id=session_id)
