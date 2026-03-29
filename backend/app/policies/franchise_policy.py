from app.domain.roles import UserRole


def can_review_preorders(role: UserRole) -> bool:
    return role == UserRole.FRANCHISEE
