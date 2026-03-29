from enum import Enum


class OrderEventType(str, Enum):
    CREATED = "created"
    STATUS_CHANGED = "status_changed"
    REJECTED = "rejected"
    REASSIGNED = "reassigned"
    CANCELLED = "cancelled"
    ESCALATED = "escalated"
    SLA_MISSED = "sla_missed"
