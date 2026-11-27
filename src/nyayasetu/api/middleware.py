"""Request ID, timing, and unexpected-error middleware."""

import logging
import time
from uuid import uuid4

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from nyayasetu.api.errors import problem_response
from nyayasetu.logging_setup import request_id_ctx

logger = logging.getLogger("nyayasetu.api")


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next,
    ) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid4())
        token = request_id_ctx.set(request_id)
        start = time.perf_counter()

        try:
            response = await call_next(request)
        except Exception:
            logger.exception(
                "unhandled request error",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status": 500,
                },
            )
            response = problem_response(
                request,
                500,
                "Internal Server Error",
                "An unexpected error occurred.",
            )
        finally:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)

        response.headers["X-Request-ID"] = request_id
        logger.info(
            "request completed",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "duration_ms": duration_ms,
            },
        )
        request_id_ctx.reset(token)
        return response


async def request_context(request: Request, call_next) -> Response:
    """Attach request context, handle unexpected errors, and log timing."""
    request_id = request.headers.get("X-Request-ID") or str(uuid4())
    token = request_id_ctx.set(request_id)
    start = time.perf_counter()

    try:
        response = await call_next(request)
    except Exception:
        logger.exception(
            "unhandled request error",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status": 500,
            },
        )
        response = problem_response(
            request,
            500,
            "Internal Server Error",
            "An unexpected error occurred.",
        )
    finally:
        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        request_id_ctx.reset(token)

    response.headers["X-Request-ID"] = request_id
    logger.info(
        "request completed",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "duration_ms": duration_ms,
        },
    )
    return response
