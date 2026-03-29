from datetime import datetime, timedelta, timezone
from secrets import token_urlsafe

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import create_access_token, decode_access_token, get_password_hash, verify_password
from app.domain.roles import UserRole
from app.repositories.refresh_session_repository import RefreshSessionRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import (
    AuthSession,
    RefreshTokenRequest,
    SignupRequest,
    Token,
    UserBodyProfilePatch,
    UserPatch,
    UserRead,
)


class AuthService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.repository = UserRepository(session)
        self.refresh_sessions = RefreshSessionRepository(session)
        self.settings = get_settings()

    def authenticate_user(self, email: str, password: str):
        user = self.repository.get_by_email(email)
        if user is None:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        if not user.is_active:
            return None
        return user

    def login(self, email: str, password: str) -> AuthSession | None:
        user = self.authenticate_user(email, password)
        if user is None:
            return None

        return self._issue_session(UserRead.from_user(user))

    def signup(self, payload: SignupRequest) -> AuthSession:
        if self.repository.get_by_email(payload.email) is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email is already registered")
        user = self.repository.create(
            email=payload.email,
            full_name=payload.full_name,
            hashed_password=get_password_hash(payload.password),
            role=UserRole.CLIENT,
            preferred_language=payload.preferred_language.value,
            is_active=True,
        )
        self.session.commit()
        self.session.refresh(user)
        return self._issue_session(UserRead.from_user(user))

    def get_current_user(self, token: str) -> UserRead:
        payload = decode_access_token(token)
        user = self.repository.get_by_id(int(payload.sub))
        if user is None:
            raise ValueError("User not found")
        return UserRead.from_user(user)

    def refresh(self, payload: RefreshTokenRequest) -> AuthSession:
        refresh_session = self.refresh_sessions.get_by_token(payload.refresh_token)
        now = self._normalize_datetime(datetime.now(timezone.utc))
        if refresh_session is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token is invalid")
        expires_at = self._normalize_datetime(refresh_session.expires_at)
        revoked_at = self._normalize_datetime(refresh_session.revoked_at)
        if revoked_at is not None or expires_at <= now:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token is invalid")

        user = self.repository.get_by_id(refresh_session.user_id)
        if user is None or not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token is invalid")

        self.refresh_sessions.revoke(refresh_session, revoked_at=datetime.now(timezone.utc))
        self.session.commit()
        return self._issue_session(UserRead.from_user(user))

    def logout(self, payload: RefreshTokenRequest) -> None:
        refresh_session = self.refresh_sessions.get_by_token(payload.refresh_token)
        if refresh_session is None or refresh_session.revoked_at is not None:
            return None
        self.refresh_sessions.revoke(refresh_session, revoked_at=datetime.now(timezone.utc))
        self.session.commit()
        return None

    def update_body_profile(self, user_id: int, payload: UserBodyProfilePatch) -> UserRead:
        user = self.repository.update_body_profile(user_id, payload)
        if user is None:
            raise ValueError("User not found")
        return UserRead.from_user(user)

    def update_user(self, user_id: int, payload: UserPatch) -> UserRead:
        user = self.repository.update_fields(user_id, payload.model_dump(exclude_unset=True))
        if user is None:
            raise ValueError("User not found")
        self.session.commit()
        self.session.refresh(user)
        return UserRead.from_user(user)

    def _issue_session(self, user: UserRead) -> AuthSession:
        refresh_token = token_urlsafe(48)
        expires_at = datetime.now(timezone.utc) + timedelta(days=30)
        self.refresh_sessions.create(user_id=user.id, token=refresh_token, expires_at=expires_at)
        self.session.commit()
        return AuthSession(
            access_token=create_access_token(subject=str(user.id), role=user.role),
            refresh_token=refresh_token,
            user=user,
        )

    def _normalize_datetime(self, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            return value
        return value.astimezone(timezone.utc).replace(tzinfo=None)
