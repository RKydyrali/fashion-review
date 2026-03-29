from app.domain.roles import UserRole


def can_access_role_scope(current_role: UserRole, target_role: UserRole) -> bool:
    if current_role == UserRole.ADMIN:
        return True
    if current_role == UserRole.FRANCHISEE:
        return target_role in {UserRole.CLIENT, UserRole.FRANCHISEE}
    return current_role == target_role


def has_any_role(current_role: UserRole, allowed_roles: tuple[UserRole, ...]) -> bool:
    return current_role in allowed_roles
