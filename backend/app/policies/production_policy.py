from app.domain.roles import UserRole


def can_manage_production(role: UserRole) -> bool:
    return role == UserRole.PRODUCTION
