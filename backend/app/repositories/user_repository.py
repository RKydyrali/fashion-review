from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.user import User
from app.schemas.auth import UserBodyProfilePatch


class UserRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_all(self) -> list[User]:
        return list(self.session.scalars(select(User)))

    def get_by_id(self, user_id: int) -> User | None:
        statement = select(User).options(joinedload(User.managed_branches)).where(User.id == user_id)
        return self.session.scalar(statement)

    def get_by_email(self, email: str) -> User | None:
        statement = select(User).where(User.email == email)
        return self.session.scalar(statement)

    def create(
        self,
        *,
        email: str,
        full_name: str,
        hashed_password: str,
        role,
        preferred_language: str,
        is_active: bool = True,
    ) -> User:
        user = User(
            email=email,
            full_name=full_name,
            hashed_password=hashed_password,
            role=role,
            preferred_language=preferred_language,
            is_active=is_active,
        )
        self.session.add(user)
        self.session.flush()
        return user

    def update_body_profile(self, user_id: int, payload: UserBodyProfilePatch) -> User | None:
        user = self.get_by_id(user_id)
        if user is None:
            return None

        for field_name, value in payload.model_dump(exclude_unset=True).items():
            setattr(user, field_name, value)

        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user

    def update_fields(self, user_id: int, payload: dict[str, object]) -> User | None:
        user = self.get_by_id(user_id)
        if user is None:
            return None
        for field_name, value in payload.items():
            setattr(user, field_name, value)
        self.session.add(user)
        self.session.flush()
        self.session.refresh(user)
        return user
