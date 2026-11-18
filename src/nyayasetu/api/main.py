"""Application factory for the NyayaSetu API."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from nyayasetu.api.errors import (
    http_exception_handler,
    validation_exception_handler,
)
from nyayasetu.api.middleware import RequestContextMiddleware
from nyayasetu.api.routes import documents, health
from nyayasetu.config import Settings, get_settings
from nyayasetu.db.session import SessionLocal, engine
from nyayasetu.logging_setup import setup_logging

logger = logging.getLogger("nyayasetu")


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()

    setup_logging(settings.log_level)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.settings = settings
        app.state.session_factory = SessionLocal

        logger.info("NyayaSetu API started")

        try:
            yield
        finally:
            await engine.dispose()
            logger.info("NyayaSetu API stopped")

    app = FastAPI(
        title="NyayaSetu API",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(RequestContextMiddleware)

    app.add_exception_handler(
        404,
        http_exception_handler,
    )
    app.add_exception_handler(
        405,
        http_exception_handler,
    )
    app.add_exception_handler(
        422,
        validation_exception_handler,
    )

    app.include_router(health.router)
    app.include_router(documents.router, prefix="/v1")

    return app
