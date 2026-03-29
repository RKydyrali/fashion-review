import os
from pathlib import Path


TEST_TMP_DIR = Path(__file__).resolve().parent / ".tmp"
TEST_TMP_DIR.mkdir(parents=True, exist_ok=True)

test_database_path = (TEST_TMP_DIR / "test_fashion.db").resolve()
test_media_root = (TEST_TMP_DIR / "media").resolve()

os.environ["DATABASE_URL"] = f"sqlite:///{test_database_path.as_posix()}"
os.environ["MEDIA_ROOT"] = test_media_root.as_posix()
