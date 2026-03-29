from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, File, Query, Response, UploadFile, status

from app.ai.text_service import AITextService
from app.api.deps import get_admin_service, get_ai_text_service, require_roles
from app.domain.roles import UserRole
from app.schemas.admin import (
    AdminBranchSummary,
    AdminCollectionCreate,
    AdminCollectionRead,
    AdminCollectionUpdate,
    AdminMediaUploadRead,
    AdminProductCreate,
    AdminProductTranslationGenerateRequest,
    AdminProductTranslationGenerateResponse,
    AdminProductRead,
    AdminProductUpdate,
    AdminUserCreate,
    AdminUserRead,
    AdminUserUpdate,
)
from app.schemas.auth import UserRead
from app.services.admin_service import AdminService

router = APIRouter(prefix="/admin", tags=["admin"])
AdminActor = Annotated[UserRead, Depends(require_roles(UserRole.ADMIN))]


@router.get("/users", response_model=list[AdminUserRead])
def list_users(
    _: AdminActor,
    service: Annotated[AdminService, Depends(get_admin_service)],
    query: str | None = Query(default=None),
) -> list[AdminUserRead]:
    return service.list_users(query)


@router.post("/users", response_model=AdminUserRead, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: AdminUserCreate,
    _: AdminActor,
    service: Annotated[AdminService, Depends(get_admin_service)],
) -> AdminUserRead:
    return service.create_user(payload)


@router.patch("/users/{user_id}", response_model=AdminUserRead)
def update_user(
    user_id: int,
    payload: AdminUserUpdate,
    _: AdminActor,
    service: Annotated[AdminService, Depends(get_admin_service)],
) -> AdminUserRead:
    return service.update_user(user_id, payload)


@router.get("/branches", response_model=list[AdminBranchSummary])
def list_branches(
    _: AdminActor,
    service: Annotated[AdminService, Depends(get_admin_service)],
) -> list[AdminBranchSummary]:
    return service.list_branches()


@router.get("/products", response_model=list[AdminProductRead])
def list_products(
    _: AdminActor,
    service: Annotated[AdminService, Depends(get_admin_service)],
) -> list[AdminProductRead]:
    return service.list_products()


@router.post("/products", response_model=AdminProductRead, status_code=status.HTTP_201_CREATED)
def create_product(
    payload: AdminProductCreate,
    _: AdminActor,
    service: Annotated[AdminService, Depends(get_admin_service)],
) -> AdminProductRead:
    return service.create_product(payload)


@router.post("/products/translate", response_model=AdminProductTranslationGenerateResponse)
def translate_product_copy(
    payload: AdminProductTranslationGenerateRequest,
    current_user: AdminActor,
    ai_text_service: Annotated[AITextService, Depends(get_ai_text_service)],
) -> AdminProductTranslationGenerateResponse:
    return AdminProductTranslationGenerateResponse.model_validate(
        ai_text_service.translate_product_copy_from_english(
            english_copy=payload.english.model_dump(),
            normalized_category=payload.normalized_category,
            color=payload.color,
            season_tags=payload.season_tags,
            user_id=current_user.id,
        ).model_dump()
    )


@router.patch("/products/{product_id}", response_model=AdminProductRead)
def update_product(
    product_id: int,
    payload: AdminProductUpdate,
    _: AdminActor,
    service: Annotated[AdminService, Depends(get_admin_service)],
) -> AdminProductRead:
    return service.update_product(product_id, payload)


@router.delete("/products/{product_id}", response_model=AdminProductRead)
def archive_product(
    product_id: int,
    _: AdminActor,
    service: Annotated[AdminService, Depends(get_admin_service)],
) -> AdminProductRead:
    return service.archive_product(product_id)


@router.post("/products/{product_id}/restore", response_model=AdminProductRead)
def restore_product(
    product_id: int,
    _: AdminActor,
    service: Annotated[AdminService, Depends(get_admin_service)],
) -> AdminProductRead:
    return service.restore_product(product_id)


@router.delete("/products/{product_id}/permanent", status_code=status.HTTP_204_NO_CONTENT)
def permanently_delete_product(
    product_id: int,
    _: AdminActor,
    service: Annotated[AdminService, Depends(get_admin_service)],
) -> Response:
    service.permanently_delete_product(product_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/collections", response_model=list[AdminCollectionRead])
def list_collections(
    _: AdminActor,
    service: Annotated[AdminService, Depends(get_admin_service)],
) -> list[AdminCollectionRead]:
    return service.list_collections()


@router.post("/collections", response_model=AdminCollectionRead, status_code=status.HTTP_201_CREATED)
def create_collection(
    payload: AdminCollectionCreate,
    _: AdminActor,
    service: Annotated[AdminService, Depends(get_admin_service)],
) -> AdminCollectionRead:
    return service.create_collection(payload)


@router.patch("/collections/{collection_id}", response_model=AdminCollectionRead)
def update_collection(
    collection_id: int,
    payload: AdminCollectionUpdate,
    _: AdminActor,
    service: Annotated[AdminService, Depends(get_admin_service)],
) -> AdminCollectionRead:
    return service.update_collection(collection_id, payload)


@router.delete("/collections/{collection_id}", response_model=AdminCollectionRead)
def archive_collection(
    collection_id: int,
    _: AdminActor,
    service: Annotated[AdminService, Depends(get_admin_service)],
) -> AdminCollectionRead:
    return service.archive_collection(collection_id)


@router.post("/collections/{collection_id}/restore", response_model=AdminCollectionRead)
def restore_collection(
    collection_id: int,
    _: AdminActor,
    service: Annotated[AdminService, Depends(get_admin_service)],
) -> AdminCollectionRead:
    return service.restore_collection(collection_id)


async def _upload_media(file: UploadFile, *, entity: str, slot: str, service: AdminService) -> AdminMediaUploadRead:
    content = await file.read()
    return service.store_catalog_media(entity=entity, slot=slot, filename=file.filename or f"{slot}.bin", content=content)


@router.post("/uploads/products/hero-image", response_model=AdminMediaUploadRead, status_code=status.HTTP_201_CREATED)
async def upload_product_hero_image(
    _: AdminActor,
    service: Annotated[AdminService, Depends(get_admin_service)],
    file: UploadFile = File(...),
) -> AdminMediaUploadRead:
    return await _upload_media(file, entity="products", slot="hero-image", service=service)


@router.post("/uploads/products/reference-image", response_model=AdminMediaUploadRead, status_code=status.HTTP_201_CREATED)
async def upload_product_reference_image(
    _: AdminActor,
    service: Annotated[AdminService, Depends(get_admin_service)],
    file: UploadFile = File(...),
) -> AdminMediaUploadRead:
    return await _upload_media(file, entity="products", slot="reference-image", service=service)


@router.post("/uploads/products/gallery-image", response_model=AdminMediaUploadRead, status_code=status.HTTP_201_CREATED)
async def upload_product_gallery_image(
    _: AdminActor,
    service: Annotated[AdminService, Depends(get_admin_service)],
    file: UploadFile = File(...),
) -> AdminMediaUploadRead:
    return await _upload_media(file, entity="products", slot="gallery-image", service=service)


@router.post("/uploads/collections/hero-image", response_model=AdminMediaUploadRead, status_code=status.HTTP_201_CREATED)
async def upload_collection_hero_image(
    _: AdminActor,
    service: Annotated[AdminService, Depends(get_admin_service)],
    file: UploadFile = File(...),
) -> AdminMediaUploadRead:
    return await _upload_media(file, entity="collections", slot="hero-image", service=service)


@router.post("/uploads/collections/cover-image", response_model=AdminMediaUploadRead, status_code=status.HTTP_201_CREATED)
async def upload_collection_cover_image(
    _: AdminActor,
    service: Annotated[AdminService, Depends(get_admin_service)],
    file: UploadFile = File(...),
) -> AdminMediaUploadRead:
    return await _upload_media(file, entity="collections", slot="cover-image", service=service)
