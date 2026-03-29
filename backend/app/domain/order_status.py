from enum import Enum


class OrderStatus(str, Enum):
    CREATED = "created"
    ACCEPTED = "accepted"
    IN_PRODUCTION = "in_production"
    READY = "ready"
    PICKED_UP = "picked_up"
    CANCELLED = "cancelled"
    ESCALATED = "escalated"
