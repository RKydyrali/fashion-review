from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import router as api_v1_router
from app.core.config import get_settings
from app.core.database import (
    initialize_database,
    seed_default_branch,
    seed_demo_size_charts,
    seed_demo_users,
)
from app.websocket.routes import router as websocket_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    Path(get_settings().media_root).mkdir(parents=True, exist_ok=True)
    initialize_database()
    seed_demo_users()
    seed_default_branch()
    seed_demo_size_charts()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    Path(settings.media_root).mkdir(parents=True, exist_ok=True)
    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api_v1_router, prefix=settings.api_v1_prefix)
    app.include_router(websocket_router, prefix=settings.websocket_prefix)
    app.mount(settings.media_url_prefix, StaticFiles(directory=settings.media_root), name="media")
    return app


app = create_app()
