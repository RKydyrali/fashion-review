from app.domain.roles import UserRole

ROLE_PERMISSIONS: dict[UserRole, set[str]] = {
    UserRole.ADMIN: {"admin:manage", "catalog:write", "users:write"},
    UserRole.CLIENT: {"preorders:create", "preorders:read:self"},
    UserRole.FRANCHISEE: {"preorders:review", "catalog:read", "franchise:dashboard"},
    UserRole.PRODUCTION: {"production:update", "production:queue"},
}
