"""
Wire the AutoTraderDaemon into FastAPI lifecycle and application routes
"""
import os

APP_PATH = "backend/api/app.py"
ROUTES_PATH = "backend/api/routes/application.py"

APP_CONTENT = '''"""
BALLY FLOW API

HTTP API layer for the BALLY FLOW mobile application.
"""

from __future__ import annotations

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
'''

ROUTES_CONTENT = '''"""
BALLY FLOW API - Application Routes
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.main import (
    app as application,
)
from backend.trading_engine.modes.mode_controller import (
    TradingMode,
)
from backend.trading_engine.auto_trader import auto_trader

router = APIRouter()


class ModeRequest(BaseModel):
    mode: TradingMode


class AutoTradeToggleRequest(BaseModel):
    enabled: bool


class BotSettingsRequest(BaseModel):
    min_confidence: Optional[float] = None
    risk_per_trade_pct: Optional[float] = None
    max_positions: Optional[int] = None
    scan_interval_seconds: Optional[int] = None


@router.get("/status")
def get_status():
    """
    Return complete application status.
    """
    return application.status()


@router.post("/start")
def start_application():
    """
    Start application orchestration.
    """
    return application.start()


@router.post("/stop")
def stop_application():
    """
    Stop application orchestration.
    """
    return application.stop()


@router.get("/mode")
def get_mode():
    """
    Return active trading mode.
    """
    return {"mode": application.mode.value}


@router.put("/mode")
def set_mode(request: ModeRequest):
    """
    Switch active trading mode.
    """
    return application.set_mode(request.mode)


@router.get("/bot/telemetry")
def get_bot_telemetry():
    """
    Return live telemetry, heartbeat, and audit logs from the auto-trader daemon.
    """
    return auto_trader.get_telemetry()


@router.post("/bot/toggle")
def toggle_auto_trade(request: AutoTradeToggleRequest):
    """
    Toggle automatic trading execution on or off.
    """
    enabled = auto_trader.set_enabled(request.enabled)
    application.set_auto_trading(enabled)
    return {
        "status": "OK",
        "auto_trading_enabled": enabled,
    }


@router.post("/bot/settings")
def update_bot_settings(request: BotSettingsRequest):
    """
    Update confidence threshold, risk percentage, and position limits.
    """
    updated = auto_trader.update_settings(
        min_confidence=request.min_confidence,
        risk_per_trade_pct=request.risk_per_trade_pct,
        max_positions=request.max_positions,
        scan_interval_seconds=request.scan_interval_seconds,
    )
    return {
        "status": "OK",
        "settings": updated,
    }
'''

with open(APP_PATH, "w", encoding="utf-8") as f:
    f.write(APP_CONTENT)
print(f"[OK] Successfully wired {APP_PATH}")

with open(ROUTES_PATH, "w", encoding="utf-8") as f:
    f.write(ROUTES_CONTENT)
print(f"[OK] Successfully wired {ROUTES_PATH}")
