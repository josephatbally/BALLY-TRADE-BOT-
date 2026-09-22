"""
BALLY FLOW API - Application Routes
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from backend.main import (
    app as application,
)
from backend.trading_engine.modes.mode_controller import (
    TradingMode,
    get_mode_controller,
)
from backend.trading_engine.auto_trader import auto_trader
from backend.security.jwt_auth import get_current_user

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
def get_status(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Return complete application status.
    """
    return application.status()


@router.post("/start")
def start_application(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Start application orchestration.
    """
    return application.start()


@router.post("/stop")
def stop_application(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Stop application orchestration.
    """
    return application.stop()


@router.get("/mode")
def get_mode(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Return active trading mode.
    """
    from backend.trading_engine.modes.mode_controller import get_mode_controller
    mode_ctrl = get_mode_controller()
    return {
        "mode": mode_ctrl.mode.value,
        "is_hybrid": mode_ctrl.is_hybrid(),
        "is_technical": mode_ctrl.is_technical(),
    }


@router.put("/mode")
def set_mode(request: ModeRequest, current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Switch active trading mode (technical or hybrid).
    """
    from backend.trading_engine.modes.mode_controller import get_mode_controller
    mode_ctrl = get_mode_controller()
    mode_ctrl.set_mode(request.mode)
    application.set_mode(request.mode)
    return {
        "status": "OK",
        "mode": mode_ctrl.mode.value,
        "is_hybrid": mode_ctrl.is_hybrid(),
        "is_technical": mode_ctrl.is_technical(),
    }


@router.get("/bot/telemetry")
def get_bot_telemetry(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Return live telemetry, heartbeat, and audit logs from the auto-trader daemon.
    """
    return auto_trader.get_telemetry()


@router.post("/bot/toggle")
def toggle_auto_trade(request: AutoTradeToggleRequest, current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Toggle automatic trading execution on or off.
    """
    user_id = int(current_user["id"])
    enabled = auto_trader.set_enabled(request.enabled, user_id=user_id)
    application.set_auto_trading(enabled)
    return {
        "status": "OK",
        "auto_trading_enabled": enabled,
    }


@router.post("/bot/settings")
def update_bot_settings(request: BotSettingsRequest, current_user: Dict[str, Any] = Depends(get_current_user)):
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


class StrategyUpdateRequest(BaseModel):
    strategy: str


SUPPORTED_STRATEGY_VALUES = ("SMC", "HYBRID", "CANDLE_SCALPER")


@router.get("/strategy")
def get_bot_strategy(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Return the strategy the bot is currently trading with."""
    return {
        "status": "ok",
        "strategy": auto_trader.get_strategy(),
        "supported": list(SUPPORTED_STRATEGY_VALUES),
    }


@router.put("/strategy")
def update_bot_strategy(
    req: StrategyUpdateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Switch the live trading strategy.

    The strategy is wired straight into the running bot: it selects the
    execution branch and re-routes the analysis pipeline (HYBRID enables
    the fundamental/news layer, SMC stays purely technical).
    """
    strat = str(req.strategy or "").strip().upper()
    if strat not in SUPPORTED_STRATEGY_VALUES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported strategy '{req.strategy}'. "
                   f"Supported: {', '.join(SUPPORTED_STRATEGY_VALUES)}",
        )

    applied = auto_trader.set_strategy(strat)
    mode_ctrl = get_mode_controller()
    try:
        application.set_mode(mode_ctrl.mode)
    except Exception:
        pass

    return {
        "status": "ok",
        "strategy": applied,
        "mode": mode_ctrl.mode.value,
        "running": auto_trader.running,
        "enabled": auto_trader.enabled,
        "message": f"Strategy updated to {applied}",
    }
