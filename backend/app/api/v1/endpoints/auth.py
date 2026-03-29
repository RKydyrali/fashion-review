from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import CurrentUser, get_auth_service
from app.schemas.auth import AuthSession, RefreshTokenRequest, SignupRequest, UserBodyProfilePatch, UserPatch, UserRead
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=AuthSession)
def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> AuthSession:
    token = auth_service.login(form_data.username, form_data.password)
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token


@router.post("/signup", response_model=AuthSession, status_code=status.HTTP_201_CREATED)
def signup(
    payload: SignupRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> AuthSession:
    return auth_service.signup(payload)


@router.post("/refresh", response_model=AuthSession)
def refresh_session(
    payload: RefreshTokenRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> AuthSession:
    return auth_service.refresh(payload)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout_session(
    payload: RefreshTokenRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> Response:
    auth_service.logout(payload)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me", response_model=UserRead)
def read_current_user(current_user: CurrentUser) -> UserRead:
    return current_user


@router.patch("/me", response_model=UserRead)
def update_current_user(
    payload: UserPatch,
    current_user: CurrentUser,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> UserRead:
    try:
        return auth_service.update_user(current_user.id, payload)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")


@router.patch("/me/body-profile", response_model=UserRead)
def update_current_user_body_profile(
    payload: UserBodyProfilePatch,
    current_user: CurrentUser,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> UserRead:
    try:
        return auth_service.update_body_profile(current_user.id, payload)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
