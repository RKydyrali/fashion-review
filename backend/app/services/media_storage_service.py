from __future__ import annotations

from pathlib import Path
from uuid import uuid4
from urllib.parse import urlparse


class LocalMediaStorageService:
    def __init__(self, root: str | Path, url_prefix: str) -> None:
        self.root = Path(root)
        self.url_prefix = url_prefix.rstrip("/")
        self.root.mkdir(parents=True, exist_ok=True)

    def source_relative_path(self, session_id: int, extension: str) -> str:
        return f"try_on/{session_id}/source/original{extension}"

    def render_relative_path(self, session_id: int, extension: str) -> str:
        return f"try_on/{session_id}/render/result{extension}"

    def save_bytes(self, relative_path: str, content: bytes) -> Path:
        destination = self.root / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)
        return destination

    def read_bytes(self, relative_path: str) -> bytes:
        return (self.root / relative_path).read_bytes()

    def url_for(self, relative_path: str | None) -> str | None:
        if relative_path is None:
            return None
        return f"{self.url_prefix}/{relative_path}".replace("\\", "/")

    def save_catalog_upload(self, *, entity: str, slot: str, filename: str, content: bytes) -> str:
        extension = Path(filename).suffix or ".bin"
        relative_path = f"catalog/{entity}/{slot}/{uuid4().hex}{extension}"
        self.save_bytes(relative_path, content)
        return relative_path

    def relative_path_from_url(self, url: str | None) -> str | None:
        if not url:
            return None
        parsed = urlparse(url)
        path = parsed.path or url
        normalized_prefix = f"{self.url_prefix}/"
        if path.startswith(normalized_prefix):
            return path.removeprefix(normalized_prefix)
        return None

    def cleanup_session(self, session_id: int) -> None:
        # Reserved for future TTL-based cleanup or explicit pruning hooks.
        return None
