from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import RequestLanguage, get_wardrobe_service
from app.schemas.wardrobe import CapsuleWardrobeRequest, CapsuleWardrobeResponse
from app.services.wardrobe_service import WardrobeService

router = APIRouter(tags=["wardrobes"])


@router.post("/wardrobes/capsule", response_model=CapsuleWardrobeResponse)
def generate_capsule_wardrobe(
    payload: CapsuleWardrobeRequest,
    service: Annotated[WardrobeService, Depends(get_wardrobe_service)],
    language: RequestLanguage,
) -> CapsuleWardrobeResponse:
    return service.generate_capsule(payload, language=language)
