"""
BALLY FLOW API - Account Routes

Direct MT5 Terminal Bridge: reads live account data, equity, balance, margin,
and positions straight from the running MetaTrader 5 terminal on the PC.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends

from backend.security.jwt_auth import get_current_user_optional
from backend.trading_engine.market_data.mt5_connection import (
    get_account_info,
    get_positions,
    is_mt5_connected,
)

router = APIRouter()


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


@router.get("")
def get_account(user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)) -> Dict[str, Any]:
    """Return live account state directly from the active MT5 terminal."""
    if not is_mt5_connected():
        return {
            "status": "OFFLINE",
            "connected": False,
            "account": None,
            "broker": None,
            "balance": 0.0,
            "equity": 0.0,
            "profit": 0.0,
            "margin": 0.0,
            "free_margin": 0.0,
            "open_trades": 0,
            "currency": "USD",
        }

    info = get_account_info()
    if info is None:
        return {
            "status": "ACCOUNT_UNAVAILABLE",
            "connected": False,
            "account": None,
            "broker": None,
            "balance": 0.0,
            "equity": 0.0,
            "profit": 0.0,
            "margin": 0.0,
            "free_margin": 0.0,
            "open_trades": 0,
            "currency": "USD",
        }

    try:
        positions = get_positions() or []
        open_trades_count = len(positions)
    except Exception:
        open_trades_count = 0

    login = getattr(info, "login", 0)
    company = getattr(info, "company", "MetaTrader 5 Broker")
    server = getattr(info, "server", "MT5-Server")
    leverage = _safe_int(getattr(info, "leverage", 100))
    trade_mode = "DEMO" if getattr(info, "trade_mode", 0) == 0 else "REAL"
    currency = getattr(info, "currency", "USD")

    return {
        "status": "READY",
        "connected": True,
        "identity_match": True,
        "account": {
            "id": login,
            "trading_account_id": login,
            "account_number": str(login),
            "broker_server": server,
            "broker_name": company,
            "platform": "MT5",
            "connection_status": "CONNECTED",
            "is_demo": (trade_mode == "DEMO"),
        },
        "broker": {
            "company": company,
            "server": server,
            "login": login,
            "leverage": leverage,
            "name": getattr(info, "name", None),
            "trade_mode": trade_mode,
        },
        "balance": _safe_float(getattr(info, "balance", 0.0)),
        "equity": _safe_float(getattr(info, "equity", 0.0)),
        "profit": _safe_float(getattr(info, "profit", 0.0)),
        "margin": _safe_float(getattr(info, "margin", 0.0)),
        "free_margin": _safe_float(getattr(info, "margin_free", 0.0)),
        "open_trades": open_trades_count,
        "currency": currency,
    }
