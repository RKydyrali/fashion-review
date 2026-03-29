from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.domain.language import DEFAULT_LANGUAGE, LanguageCode, coerce_language, parse_accept_language
from app.domain.roles import UserRole
from app.policies.auth_policy import has_any_role
from app.ai.client import OpenRouterClient
from app.ai.text_service import AITextService
from app.ai.try_on_service import AITryOnJobService
from app.ai.try_on_worker_service import AITryOnWorkerService
from app.repositories.product_repository import ProductRepository
from app.repositories.ai_call_repository import AICallRepository
from app.repositories.size_chart_repository import SizeChartRepository
from app.schemas.auth import UserRead
from app.services.media_storage_service import LocalMediaStorageService
from app.services.admin_service import AdminService
from app.services.auth_service import AuthService
from app.services.bag_service import BagService
from app.services.catalog_service import CatalogService
from app.services.favorite_service import FavoriteService
from app.services.order_service import OrderService
from app.services.preorder_batch_service import PreorderBatchService
from app.services.size_recommendation_service import SizeRecommendationService
from app.services.try_on_service import TryOnService
from app.services.wardrobe_service import WardrobeService
from app.services.personal_wardrobe_service import PersonalWardrobeService
from app.websocket.publisher import realtime_order_event_publisher
from app.websocket.try_on_publisher import realtime_try_on_event_publisher

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
optional_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


def _credentials_exception() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(db)


def get_catalog_service(db: Session = Depends(get_db)) -> CatalogService:
    return CatalogService(db)


def get_admin_service(db: Session = Depends(get_db)) -> AdminService:
    settings = get_settings()
    return AdminService(db, LocalMediaStorageService(settings.media_root, settings.media_url_prefix))


def get_favorite_service(db: Session = Depends(get_db)) -> FavoriteService:
    return FavoriteService(db)


def get_bag_service(db: Session = Depends(get_db)) -> BagService:
    return BagService(db)


def get_order_service(db: Session = Depends(get_db)) -> OrderService:
    return OrderService(db, event_publisher=realtime_order_event_publisher)


def get_preorder_batch_service(db: Session = Depends(get_db)) -> PreorderBatchService:
    return PreorderBatchService(db)


def get_wardrobe_service(db: Session = Depends(get_db)) -> WardrobeService:
    return WardrobeService(repository=ProductRepository(db))


def get_personal_wardrobe_service(db: Session = Depends(get_db)) -> PersonalWardrobeService:
    return PersonalWardrobeService(db)


def get_size_recommendation_service(
    db: Session = Depends(get_db),
) -> SizeRecommendationService:
    return SizeRecommendationService(repository=SizeChartRepository(db))


def get_size_chart_repository(db: Session = Depends(get_db)) -> SizeChartRepository:
    return SizeChartRepository(db)


def get_try_on_service(db: Session = Depends(get_db)) -> TryOnService:
    return TryOnService(db, event_publisher=realtime_try_on_event_publisher)


def get_openrouter_text_client() -> OpenRouterClient:
    settings = get_settings()
    return OpenRouterClient(
        api_key=settings.openrouter_api_key,
        base_url=settings.openrouter_base_url,
        timeout_seconds=settings.ai_text_timeout_seconds,
    )


def get_openrouter_try_on_client() -> OpenRouterClient:
    settings = get_settings()
    return OpenRouterClient(
        api_key=settings.openrouter_api_key,
        base_url=settings.openrouter_base_url,
        timeout_seconds=settings.ai_try_on_timeout_seconds,
    )


def get_ai_text_service(db: Session = Depends(get_db)) -> AITextService:
    return AITextService(
        openrouter_client=get_openrouter_text_client(),
        call_repository=AICallRepository(db),
    )


def get_ai_try_on_job_service(db: Session = Depends(get_db)) -> AITryOnJobService:
    settings = get_settings()
    return AITryOnJobService(
        db,
        openrouter_client=get_openrouter_try_on_client(),
        media_storage=LocalMediaStorageService(settings.media_root, settings.media_url_prefix),
    )


def get_ai_try_on_worker_service(db: Session = Depends(get_db)) -> AITryOnWorkerService:
    settings = get_settings()
    return AITryOnWorkerService(
        db,
        openrouter_client=get_openrouter_try_on_client(),
        media_storage=LocalMediaStorageService(settings.media_root, settings.media_url_prefix),
    )


def get_current_user(
    token: str = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(get_auth_service),
) -> UserRead:
    try:
        return auth_service.get_current_user(token)
    except ValueError:
        raise _credentials_exception()


def get_optional_current_user(
    token: str | None = Depends(optional_oauth2_scheme),
    auth_service: AuthService = Depends(get_auth_service),
) -> UserRead | None:
    if token is None:
        return None
    try:
        return auth_service.get_current_user(token)
    except ValueError:
        raise _credentials_exception()


def get_current_active_user(current_user: UserRead = Depends(get_current_user)) -> UserRead:
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")
    return current_user


def get_request_language(
    accept_language: str | None = Header(default=None, alias="Accept-Language"),
    current_user: UserRead | None = Depends(get_optional_current_user),
) -> LanguageCode:
    header_language = parse_accept_language(accept_language)
    if header_language is not None:
        return header_language

    user_language = coerce_language(current_user.preferred_language) if current_user is not None else None
    if user_language is not None:
        return user_language

    settings = get_settings()
    return coerce_language(settings.default_language) or DEFAULT_LANGUAGE


def require_roles(*roles: UserRole):
    def dependency(current_user: UserRead = Depends(get_current_active_user)) -> UserRead:
        if not has_any_role(current_user.role, roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions",
            )
        return current_user

    return dependency


CurrentUser = Annotated[UserRead, Depends(get_current_active_user)]
OptionalCurrentUser = Annotated[UserRead | None, Depends(get_optional_current_user)]
RequestLanguage = Annotated[LanguageCode, Depends(get_request_language)]
