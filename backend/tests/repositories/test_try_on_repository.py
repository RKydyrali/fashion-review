def test_try_on_repository_persists_ordered_products_and_idempotency_key() -> None:
    from app.core.database import SessionLocal, initialize_database, seed_demo_users
    from app.domain.try_on_status import TryOnStatus
    from app.models.try_on_session import TryOnSession
    from app.repositories.try_on_repository import TryOnRepository

    initialize_database(reset=True)
    seed_demo_users()

    with SessionLocal() as session:
        repository = TryOnRepository(session)
        session_model = TryOnSession(
            user_id=1,
            product_ids=[3, 1, 2],
            idempotency_key="abc123",
            source_image_path="try_on/1/source/original.png",
            rendered_image_path=None,
            provider_name="flux",
            status=TryOnStatus.QUEUED,
            attempt_count=0,
            max_attempts=3,
        )
        session.add(session_model)
        session.commit()

        saved = repository.get_by_id(session_model.id)

    assert saved is not None
    assert saved.product_ids == [3, 1, 2]
    assert saved.idempotency_key == "abc123"

