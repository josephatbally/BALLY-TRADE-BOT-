from __future__ import annotations

from backend.config.env import load_local_env
load_local_env()
from backend.trading_engine.ai.ai_engine import ai_engine
"""
BALLY FLOW API

HTTP API layer for the BALLY FLOW mobile application.
"""


from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend import main as application
from backend.api.routes import orders
from backend.trading_engine.auto_trader import auto_trader

from .routes.account import router as account_router
from .routes.application import router as application_router
from .routes.health import router as health_router
from .routes.markets import router as markets_router
from .routes.positions import router as positions_router
from .routes.history import router as history_router
from .routes.flow import router as flow_router
from .routes.auth import router as auth_router
from .routes.trading_accounts import router as trading_accounts_router

APP_NAME = "BALLY FLOW API"
APP_VERSION = "1.0.0"


@asynccontextmanager
async def lifespan(_: FastAPI):
    """
    Start BALLY FLOW orchestration and the auto-trader background daemon.
    """
    application.start()
    await auto_trader.start()
    yield
    await auto_trader.stop()


app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description="Backend API for the BALLY FLOW mobile application.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/health", tags=["Health"])
app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(trading_accounts_router, prefix="/api/v1/trading-accounts", tags=["Trading Accounts"])
app.include_router(application_router, prefix="/api/v1/app", tags=["Application"])
app.include_router(positions_router, prefix="/api/v1/positions", tags=["Positions"])
app.include_router(history_router, prefix="/api/v1/history", tags=["History"])
app.include_router(account_router, prefix="/api/v1/account", tags=["Account"])
app.include_router(markets_router, prefix="/api/v1/markets", tags=["Markets"])
app.include_router(flow_router, prefix="/api/v1", tags=["Flow"])
app.include_router(orders.router)


@app.get("/")
def root():
    return {
        "application": APP_NAME,
        "version": APP_VERSION,
        "status": "ONLINE",
    }

@app.get("/api/v1/ai/telemetry", tags=["AI"])
def get_ai_learning_telemetry():
    """Returns continuous multi-pair AI learning memory, win rates, and structural regimes."""
    return ai_engine.get_learning_telemetry()
