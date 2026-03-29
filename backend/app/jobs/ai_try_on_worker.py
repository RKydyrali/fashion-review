from app.core.database import SessionLocal
from app.ai.try_on_worker_service import AITryOnWorkerService
from app.ai.client import OpenRouterClient
from app.core.config import get_settings


def main() -> None:
    settings = get_settings()
    client = OpenRouterClient(
        api_key=settings.openrouter_api_key,
        base_url=settings.openrouter_base_url,
        timeout_seconds=settings.ai_try_on_timeout_seconds,
    )
    with SessionLocal() as session:
        service = AITryOnWorkerService(session, openrouter_client=client)
        while service.process_next_job() is not None:
            session.expunge_all()


if __name__ == "__main__":
    main()
