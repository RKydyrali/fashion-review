from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import RequestLanguage, get_catalog_service
from app.schemas.collection import CollectionRead, FeedRead
from app.schemas.product import ProductDetailRead, ProductRead
from app.services.catalog_service import CatalogService

router = APIRouter(tags=["products"])


@router.get("/products", response_model=list[ProductRead])
def list_products(
    service: Annotated[CatalogService, Depends(get_catalog_service)],
    language: RequestLanguage,
) -> list[ProductRead]:
    return service.list_products(language)


@router.get("/feed", response_model=FeedRead, tags=["feed"])
def get_feed(
    service: Annotated[CatalogService, Depends(get_catalog_service)],
    language: RequestLanguage,
) -> FeedRead:
    return service.get_feed(language)


@router.get("/collections", response_model=list[CollectionRead], tags=["collections"])
def list_collections(
    service: Annotated[CatalogService, Depends(get_catalog_service)],
    language: RequestLanguage,
) -> list[CollectionRead]:
    return service.list_collections(language)


@router.get("/products/{slug}", response_model=ProductDetailRead)
def get_product_detail(
    slug: str,
    service: Annotated[CatalogService, Depends(get_catalog_service)],
    language: RequestLanguage,
) -> ProductDetailRead:
    product = service.get_product_by_slug(slug, language)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return product
