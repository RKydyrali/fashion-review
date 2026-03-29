from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field
from pydantic import field_validator

from app.domain.language import LanguageCode
from app.domain.roles import UserRole
from app.schemas.sizing import BodyMeasurements, FitType

BODY_PROFILE_FIELDS = (
    "height_cm",
    "weight_kg",
    "chest_cm",
    "waist_cm",
    "hips_cm",
    "preferred_fit",
    "alpha_size",
    "top_size",
    "bottom_size",
    "dress_size",
)


class UserBodyProfileRead(BaseModel):
    height_cm: float | None = None
    weight_kg: float | None = None
    chest_cm: float | None = None
    waist_cm: float | None = None
    hips_cm: float | None = None
    preferred_fit: FitType | None = None
    alpha_size: str | None = None
    top_size: str | None = None
    bottom_size: str | None = None
    dress_size: str | None = None

    def to_body_measurements(self) -> BodyMeasurements | None:
        if self.chest_cm is None or self.waist_cm is None or self.hips_cm is None:
            return None
        return BodyMeasurements(
            chest_cm=self.chest_cm,
            waist_cm=self.waist_cm,
            hips_cm=self.hips_cm,
        )


class UserBodyProfilePatch(BaseModel):
    height_cm: float | None = Field(default=None, gt=0)
    weight_kg: float | None = Field(default=None, gt=0)
    chest_cm: float | None = Field(default=None, gt=0)
    waist_cm: float | None = Field(default=None, gt=0)
    hips_cm: float | None = Field(default=None, gt=0)
    preferred_fit: FitType | None = None
    alpha_size: str | None = Field(default=None, max_length=32)
    top_size: str | None = Field(default=None, max_length=32)
    bottom_size: str | None = Field(default=None, max_length=32)
    dress_size: str | None = Field(default=None, max_length=32)

    @field_validator("alpha_size", "top_size", "bottom_size", "dress_size")
    @classmethod
    def normalize_optional_size_label(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("size label must not be empty")
        return cleaned


class UserPatch(UserBodyProfilePatch):
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    preferred_language: LanguageCode | None = None


def build_user_body_profile(user: Any) -> UserBodyProfileRead | None:
    payload = {field_name: getattr(user, field_name, None) for field_name in BODY_PROFILE_FIELDS}
    if all(value is None for value in payload.values()):
        return None
    return UserBodyProfileRead.model_validate(payload)


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    full_name: str
    role: UserRole
    preferred_language: LanguageCode
    is_active: bool
    branch_id: int | None = None
    body_profile: UserBodyProfileRead | None = None
    first_order_discount_used: bool = False

    @classmethod
    def from_user(cls, user: Any) -> "UserRead":
        return cls.model_validate(
            {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role,
                "preferred_language": user.preferred_language,
                "is_active": user.is_active,
                "branch_id": user.managed_branches[0].id if getattr(user, "managed_branches", None) else None,
                "body_profile": build_user_body_profile(user),
                "first_order_discount_used": getattr(user, "first_order_discount_used", False),
            }
        )


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class SignupRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=8, max_length=255)
    preferred_language: LanguageCode = LanguageCode.EN


class AuthSession(Token):
    refresh_token: str
    user: UserRead


class TokenPayload(BaseModel):
    sub: str
    role: UserRole
    exp: int | None = None
