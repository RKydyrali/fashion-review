def test_size_chart_repository_returns_chart_by_id_and_preserves_declared_order() -> None:
    from app.core.database import SessionLocal, initialize_database, seed_demo_size_charts
    from app.repositories.size_chart_repository import SizeChartRepository

    initialize_database(reset=True)
    seed_demo_size_charts()

    with SessionLocal() as session:
        repository = SizeChartRepository(session)
        chart = repository.get_by_id(2)

    assert chart is not None
    assert chart.id == 2
    assert [size.size_label for size in chart.sizes] == ["M", "S", "L"]

