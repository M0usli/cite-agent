import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import debug, documents, health
from app.config import Settings, get_settings

logging.basicConfig(level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)  # model-download chatter


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    app = FastAPI(title="Cite API", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health.router)
    app.include_router(documents.router)
    if settings.debug_endpoints:
        app.include_router(debug.router)
    return app


app = create_app()
