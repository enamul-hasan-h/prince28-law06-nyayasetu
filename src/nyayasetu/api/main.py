"""Application factory for the NyayaSetu API."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from nyayasetu.api.errors import (
    http_exception_handler,
    validation_exception_handler,
)
from nyayasetu.api.middleware import RequestContextMiddleware
from nyayasetu.api.routes import chat, documents, health
from nyayasetu.config import Settings, get_settings
from nyayasetu.db.llm_calls import make_recorder
from nyayasetu.db.session import SessionLocal, engine
from nyayasetu.llm.gateway import build_gateway
from nyayasetu.logging_setup import setup_logging

logger = logging.getLogger("nyayasetu")


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()

    setup_logging(settings.log_level)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        logger.info("NyayaSetu API started")

        try:
            yield
        finally:
            await engine.dispose()
            logger.info("NyayaSetu API stopped")

    app = FastAPI(
        title="NyayaSetu API",
        version="0.2.0",
        lifespan=lifespan,
    )

    app.state.settings = settings
    app.state.engine = engine
    app.state.session_factory = SessionLocal
    app.state.system_prompt = chat.load_prompt(settings.prompts_dir)
    app.state.gateway = build_gateway(
        settings,
        make_recorder(SessionLocal),
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
        RequestValidationError,
        validation_exception_handler,
    )

    app.include_router(health.router)

    app.include_router(documents.router, prefix="/v1")
    app.include_router(chat.router, prefix="/v1")

    return app
