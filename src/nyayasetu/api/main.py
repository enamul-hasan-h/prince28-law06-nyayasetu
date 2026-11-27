"""App factory: build a fully wired FastAPI app from settings."""

import asyncio
import logging
from contextlib import asynccontextmanager, suppress

from fastapi import APIRouter, FastAPI

from nyayasetu.api.errors import register_error_handlers
from nyayasetu.api.middleware import request_context
from nyayasetu.api.routes import chat, documents, health, ingest
from nyayasetu.config import Settings, get_settings
from nyayasetu.db.llm_calls import make_recorder
from nyayasetu.db.session import make_engine, make_sessionmaker
from nyayasetu.llm.gateway import build_gateway
from nyayasetu.logging_setup import setup_logging

logger = logging.getLogger("nyayasetu")


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    setup_logging(settings.log_level)
    engine = make_engine(settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        logger.info("starting", extra={"status": settings.app_env})
        worker = None
        if settings.worker_in_api:
            from nyayasetu.workers.main import run_embedded

            worker = asyncio.create_task(run_embedded(settings))
        yield
        if worker:
            worker.cancel()
            with suppress(asyncio.CancelledError):
                await worker
        if getattr(app.state, "queue", None):
            await app.state.queue.close()
        await engine.dispose()

    app = FastAPI(
        title=settings.app_name,
        version="0.2.0",
        lifespan=lifespan,
    )
    app.state.settings = settings
    app.state.engine = engine
    app.state.sessionmaker = make_sessionmaker(engine)
    app.state.system_prompt = chat.load_prompt(settings.prompts_dir)
    app.state.gateway = build_gateway(settings, make_recorder(app.state.sessionmaker))

    app.middleware("http")(request_context)
    register_error_handlers(app)

    v1 = APIRouter(prefix="/v1")
    v1.include_router(documents.router)
    v1.include_router(chat.router)
    v1.include_router(ingest.router)

    app.include_router(health.router)
    app.include_router(v1)
    return app
