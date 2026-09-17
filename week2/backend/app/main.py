"""Application factory with database startup and connection cleanup."""

import os
from collections.abc import Callable
from contextlib import asynccontextmanager
from time import time

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .auth import AuthStore
from .database import Database
from .routers import auth, events
from .store import EventStore, StoreError


def create_app(database_url: str | None = None, clock: Callable[[], float] = time) -> FastAPI:
    database = Database(database_url)
    store = EventStore(database)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        try:
            database.initialize()
            store.seed()
            app.state.auth = AuthStore(database, clock=clock)
            yield
        finally:
            database.close()

    app = FastAPI(
        lifespan=lifespan,
        title="Chip In API",
        version="1.0.0",
        description=(
            "Event endpoints are public. Optional accounts use /api/auth/register and "
            "/api/auth/login; only /api/auth/me requires a bearer token. "
            "The seeded event is available at /api/events/demo. Data is persisted in the configured database."
        ),
    )
    app.state.database = database
    app.state.store = store
    origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[origin.strip() for origin in origins.split(",") if origin.strip()],
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "Authorization"],
    )

    @app.exception_handler(StoreError)
    async def store_error(request: Request, error: StoreError):
        return JSONResponse(
            status_code=error.status,
            content={"code": error.code, "message": error.message},
            headers={"WWW-Authenticate": "Bearer"} if error.status == 401 else None,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, error: RequestValidationError):
        # Do not reflect request inputs, especially passwords, in error responses.
        return JSONResponse(
            status_code=422,
            content={
                "code": "validation_error",
                "message": "Revisa los datos enviados.",
            },
        )

    app.include_router(events.router)
    app.include_router(auth.router)
    return app


app = create_app()
