from sqlalchemy import Enum as SAEnum
from sqlalchemy import inspect


def test_core_model_tables_are_registered() -> None:
    import app.models  # noqa: F401
    from app.models.base import Base

    assert {"users", "products", "branches", "orders", "order_events"}.issubset(
        Base.metadata.tables.keys()
    )


def test_user_and_order_columns_use_enums() -> None:
    import app.models  # noqa: F401
    from app.models.base import Base
    from app.domain.order_deadline_stage import OrderDeadlineStage
    from app.domain.order_event_type import OrderEventType
    from app.domain.order_status import OrderStatus
    from app.domain.roles import UserRole

    user_role_column = Base.metadata.tables["users"].c["role"]
    order_status_column = Base.metadata.tables["orders"].c["status"]
    order_deadline_stage_column = Base.metadata.tables["orders"].c["current_deadline_stage"]
    order_event_type_column = Base.metadata.tables["order_events"].c["event_type"]

    assert isinstance(user_role_column.type, SAEnum)
    assert isinstance(order_status_column.type, SAEnum)
    assert isinstance(order_deadline_stage_column.type, SAEnum)
    assert isinstance(order_event_type_column.type, SAEnum)
    assert user_role_column.type.enum_class is UserRole
    assert order_status_column.type.enum_class is OrderStatus
    assert order_deadline_stage_column.type.enum_class is OrderDeadlineStage
    assert order_event_type_column.type.enum_class is OrderEventType


def test_model_relationships_are_wired_with_foreign_keys() -> None:
    from app.models.branch import Branch
    from app.models.order import Order
    from app.models.order_event import OrderEvent
    from app.models.product import Product
    from app.models.user import User

    user_mapper = inspect(User)
    branch_mapper = inspect(Branch)
    order_mapper = inspect(Order)
    product_mapper = inspect(Product)
    order_event_mapper = inspect(OrderEvent)

    assert user_mapper.relationships["client_orders"].mapper.class_ is Order
    assert user_mapper.relationships["managed_branches"].mapper.class_ is Branch
    assert user_mapper.relationships["order_events"].mapper.class_ is OrderEvent
    assert branch_mapper.relationships["manager"].mapper.class_ is User
    assert branch_mapper.relationships["orders"].mapper.class_ is Order
    assert product_mapper.relationships["orders"].mapper.class_ is Order
    assert order_mapper.relationships["client"].mapper.class_ is User
    assert order_mapper.relationships["product"].mapper.class_ is Product
    assert order_mapper.relationships["branch"].mapper.class_ is Branch
    assert order_mapper.relationships["events"].mapper.class_ is OrderEvent
    assert order_event_mapper.relationships["order"].mapper.class_ is Order
    assert order_event_mapper.relationships["actor"].mapper.class_ is User

    assert Order.__table__.c["client_id"].foreign_keys
    assert Order.__table__.c["product_id"].foreign_keys
    assert Order.__table__.c["branch_id"].foreign_keys
    assert OrderEvent.__table__.c["order_id"].foreign_keys
    assert OrderEvent.__table__.c["actor_user_id"].foreign_keys
    assert OrderEvent.__table__.c["actor_user_id"].nullable is True


def test_timestamps_and_uniqueness_match_contract() -> None:
    import app.models  # noqa: F401
    from app.models.base import Base

    users = Base.metadata.tables["users"]
    products = Base.metadata.tables["products"]
    branches = Base.metadata.tables["branches"]
    orders = Base.metadata.tables["orders"]
    order_events = Base.metadata.tables["order_events"]

    for table in (users, products, branches, orders):
        assert "created_at" in table.c
        assert "updated_at" in table.c

    assert "created_at" in order_events.c
    assert "updated_at" not in order_events.c
    assert "delivery_city" in orders.c
    assert "branch_attempt_count" in orders.c
    assert "current_deadline_at" in orders.c
    assert "current_deadline_stage" in orders.c
    assert "cancellation_reason" in orders.c
    assert "escalation_reason" in orders.c
    assert "event_type" in order_events.c
    assert "metadata" in order_events.c

    assert users.c["email"].unique is True
    assert products.c["sku"].unique is True
    assert branches.c["code"].unique is True
