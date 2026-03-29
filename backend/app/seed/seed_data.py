import json
from pathlib import Path


def load_fixture(name: str) -> list[dict]:
    fixture_path = Path(__file__).parent / "fixtures" / f"{name}.json"
    return json.loads(fixture_path.read_text(encoding="utf-8"))


def load_all_seed_data() -> dict[str, list[dict]]:
    return {
        "users": load_fixture("users"),
        "products": load_fixture("products"),
        "preorders": load_fixture("preorders"),
    }
