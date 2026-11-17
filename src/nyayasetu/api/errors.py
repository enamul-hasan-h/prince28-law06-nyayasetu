"""Consistent API error responses using RFC 9457 Problem Details."""

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from nyayasetu.logging_setup import request_id_ctx


def problem_response(
    request: Request,
    status: int,
    title: str,
    detail: str,
) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        media_type="application/problem+json",
        content={
            "type": "about:blank",
            "title": title,
            "status": status,
            "detail": detail,
            "instance": request.url.path,
            "request_id": request_id_ctx.get(),
        },
    )


async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException,
) -> JSONResponse:
    titles = {
        404: "Not Found",
        405: "Method Not Allowed",
    }
    return problem_response(
        request,
        exc.status_code,
        titles.get(exc.status_code, "HTTP Error"),
        str(exc.detail),
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    return problem_response(
        request,
        422,
        "Validation Error",
        "The request contains invalid or missing fields.",
    )
