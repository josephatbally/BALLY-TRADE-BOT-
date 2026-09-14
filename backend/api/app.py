
"""
BALLY FLOW API

HTTP API layer for the BALLY FLOW mobile application.

IMPORTANT
---------
This module is an API/presentation layer.

It does NOT:
    - calculate SMC
    - calculate confluence
    - create trading decisions
    - calculate risk
    - calculate position size
    - place MT5 orders

Those responsibilities remain inside the existing trading engine.

The API delegates application operations to backend.main.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes.account import router as account_router
from .routes.application import router as application_router
from .routes.health import router as health_router
from .routes.markets import router as markets_router
from .routes.positions import router as positions_router
from .routes.history import router as history_router

from backend.main import app as application

APP_NAME = "BALLY FLOW API"
APP_VERSION = "1.0.0"


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """
    Start BALLY FLOW application orchestration.

    This initializes the shared MT5 connection.
    It does not execute trades.
    """
    application.start()
    yield


app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description=(
        "Backend API for the BALLY FLOW mobile application."
    ),
    lifespan=lifespan,
)


# =====================================================================
# CORS
# =====================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =====================================================================
# ROUTES
# =====================================================================

app.include_router(
    health_router,
    prefix="/health",
    tags=["Health"],
)

app.include_router(
    application_router,
    prefix="/api/v1/app",
    tags=["Application"],
)

app.include_router(
    positions_router,
    prefix="/api/v1/positions",
    tags=["Positions"],
)

app.include_router(
    history_router,
    prefix="/api/v1/history",
    tags=["History"],
)

app.include_router(
    account_router,
    prefix="/api/v1/account",
    tags=["Account"],
)

app.include_router(
    markets_router,
    prefix="/api/v1/markets",
    tags=["Markets"],
)



@app.get("/")
def root():
    return {
        "application": APP_NAME,
        "version": APP_VERSION,
        "status": "ONLINE",
    }


app.include_router(orders.router)
