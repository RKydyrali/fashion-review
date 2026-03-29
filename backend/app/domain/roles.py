from enum import Enum


class UserRole(str, Enum):
    ADMIN = "admin"
    CLIENT = "client"
    FRANCHISEE = "franchisee"
    PRODUCTION = "production"
