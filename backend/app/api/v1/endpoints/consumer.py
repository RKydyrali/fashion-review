from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from app.api.deps import CurrentUser, RequestLanguage, get_bag_service, get_favorite_service, get_personal_wardrobe_service, require_roles
from app.domain.roles import UserRole
from app.schemas.bag import BagItemCreate, BagItemPatch, BagItemRead, BagSummaryRead
from app.schemas.favorite import FavoriteCreate, FavoriteRead
from app.schemas.wardrobe import WardrobeItemCreate, WardrobeItemUpdate, WardrobeItemRead, WardrobeOutfitCreate, WardrobeOutfitRead, WardrobeSummary
from app.services.bag_service import BagService
from app.services.favorite_service import FavoriteService
from app.services.personal_wardrobe_service import PersonalWardrobeService

router = APIRouter(prefix="/client", tags=["client"])
ClientUser = Annotated[CurrentUser, Depends(require_roles(UserRole.CLIENT))]


@router.get("/favorites", response_model=list[FavoriteRead])
def list_favorites(
    current_user: ClientUser,
    language: RequestLanguage,
    service: Annotated[FavoriteService, Depends(get_favorite_service)],
) -> list[FavoriteRead]:
    return service.list_for_user(current_user.id, language)


@router.post("/favorites", response_model=FavoriteRead, status_code=201)
def create_favorite(
    payload: FavoriteCreate,
    current_user: ClientUser,
    language: RequestLanguage,
    service: Annotated[FavoriteService, Depends(get_favorite_service)],
) -> FavoriteRead:
    return service.create(current_user.id, payload.product_id, language)


@router.delete("/favorites/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_favorite(
    product_id: int,
    current_user: ClientUser,
    service: Annotated[FavoriteService, Depends(get_favorite_service)],
) -> Response:
    service.delete(current_user.id, product_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/bag/items", response_model=BagSummaryRead)
def list_bag(
    current_user: ClientUser,
    language: RequestLanguage,
    service: Annotated[BagService, Depends(get_bag_service)],
) -> BagSummaryRead:
    return service.list_for_user(current_user.id, language)


@router.post("/bag/items", response_model=BagItemRead, status_code=201)
def add_bag_item(
    payload: BagItemCreate,
    current_user: ClientUser,
    language: RequestLanguage,
    service: Annotated[BagService, Depends(get_bag_service)],
) -> BagItemRead:
    return service.add_item(current_user.id, payload, language)


@router.patch("/bag/items/{item_id}", response_model=BagItemRead)
def update_bag_item(
    item_id: int,
    payload: BagItemPatch,
    current_user: ClientUser,
    language: RequestLanguage,
    service: Annotated[BagService, Depends(get_bag_service)],
) -> BagItemRead:
    return service.update_item(current_user.id, item_id, payload, language)


@router.delete("/bag/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_bag_item(
    item_id: int,
    current_user: ClientUser,
    service: Annotated[BagService, Depends(get_bag_service)],
) -> Response:
    service.delete_item(current_user.id, item_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/wardrobe/items", response_model=list[WardrobeItemRead])
def list_wardrobe_items(
    current_user: ClientUser,
    service: Annotated[PersonalWardrobeService, Depends(get_personal_wardrobe_service)],
) -> list[WardrobeItemRead]:
    return service.list_items(current_user.id)


@router.post("/wardrobe/items", response_model=WardrobeItemRead, status_code=201)
def add_wardrobe_item(
    payload: WardrobeItemCreate,
    current_user: ClientUser,
    service: Annotated[PersonalWardrobeService, Depends(get_personal_wardrobe_service)],
) -> WardrobeItemRead:
    return service.add_item(current_user.id, payload)


@router.patch("/wardrobe/items/{item_id}", response_model=WardrobeItemRead)
def update_wardrobe_item(
    item_id: int,
    payload: WardrobeItemUpdate,
    current_user: ClientUser,
    service: Annotated[PersonalWardrobeService, Depends(get_personal_wardrobe_service)],
) -> WardrobeItemRead:
    return service.update_item(current_user.id, item_id, payload)


@router.delete("/wardrobe/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_wardrobe_item(
    item_id: int,
    current_user: ClientUser,
    service: Annotated[PersonalWardrobeService, Depends(get_personal_wardrobe_service)],
) -> Response:
    service.remove_item(current_user.id, item_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/wardrobe/outfits", response_model=list[WardrobeOutfitRead])
def list_wardrobe_outfits(
    current_user: ClientUser,
    service: Annotated[PersonalWardrobeService, Depends(get_personal_wardrobe_service)],
) -> list[WardrobeOutfitRead]:
    return service.list_outfits(current_user.id)


@router.post("/wardrobe/outfits", response_model=WardrobeOutfitRead, status_code=201)
def create_wardrobe_outfit(
    payload: WardrobeOutfitCreate,
    current_user: ClientUser,
    service: Annotated[PersonalWardrobeService, Depends(get_personal_wardrobe_service)],
) -> WardrobeOutfitRead:
    return service.create_outfit(current_user.id, payload)


@router.delete("/wardrobe/outfits/{outfit_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_wardrobe_outfit(
    outfit_id: int,
    current_user: ClientUser,
    service: Annotated[PersonalWardrobeService, Depends(get_personal_wardrobe_service)],
) -> Response:
    service.delete_outfit(current_user.id, outfit_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/wardrobe/summary", response_model=WardrobeSummary)
def get_wardrobe_summary(
    current_user: ClientUser,
    service: Annotated[PersonalWardrobeService, Depends(get_personal_wardrobe_service)],
) -> WardrobeSummary:
    return service.get_summary(current_user.id)
