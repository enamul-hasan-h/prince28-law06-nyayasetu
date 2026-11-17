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
from nyayasetu.logging_setup import setup_logging
from nyayasetu.store import RecordStore

logger = logging.getLogger("nyayasetu")


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()

    setup_logging(settings.log_level)
    store = RecordStore(settings.data_file)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.settings = settings
        app.state.store = store

        try:
            store.load()
            logger.info(
                "records loaded",
                extra={"records": len(store.search())},
            )
        except Exception:
            logger.exception("failed to load records")

        yield

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
