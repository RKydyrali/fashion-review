from app.core.database import SessionLocal
from app.services.try_on_worker_service import TryOnWorkerService


def main() -> None:
    with SessionLocal() as session:
        service = TryOnWorkerService(session)
        while service.process_next_session() is not None:
            session.expunge_all()


if __name__ == "__main__":
    main()
