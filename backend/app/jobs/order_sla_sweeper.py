from app.core.database import SessionLocal
from app.services.order_sla_service import OrderSLAService


def main() -> None:
    with SessionLocal() as session:
        service = OrderSLAService(session)
        service.run_due_actions()


if __name__ == "__main__":
    main()
