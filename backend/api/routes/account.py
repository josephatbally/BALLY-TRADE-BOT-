"""
BALLY FLOW API - Account Routes
Provides read-only MT5 account information and broker identity to the BALLY FLOW
mobile application.
"""
from __future__ import annotations
from typing import Any, Dict
from fastapi import APIRouter, HTTPException
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
def get_account() -> Dict[str, Any]:
    """
    Return read-only MT5 account and broker identity.
    """
    if not is_mt5_connected():
        return {
            "status": "OFFLINE",
            "connected": False,
            "broker": {
                "company": "Not Connected",
                "server": "Unavailable",
                "login": None,
                "leverage": None,
                "name": None,
                "trade_mode": "UNKNOWN",
            },
            "balance": 0.0,
            "equity": 0.0,
            "profit": 0.0,
            "margin": 0.0,
            "free_margin": 0.0,
            "open_trades": 0,
            "currency": "USD",
        }

    try:
        account = get_account_info()
        if account is None:
            raise RuntimeError("MT5 account information is unavailable.")

        company = getattr(account, "company", "MetaQuotes Software Corp.")
        server = getattr(account, "server", "Unknown Server")
        login = getattr(account, "login", 0)
        leverage = getattr(account, "leverage", 100)
        name = getattr(account, "name", "Trader")
        trade_mode_val = getattr(account, "trade_mode", 0)
        trade_mode = "DEMO" if trade_mode_val == 0 else "REAL"

        return {
            "status": "READY",
            "connected": True,
            "broker": {
                "company": company,
                "server": server,
                "login": login,
                "leverage": leverage,
                "name": name,
                "trade_mode": trade_mode,
            },
            "balance": _safe_float(getattr(account, "balance", 0.0)),
            "equity": _safe_float(getattr(account, "equity", 0.0)),
            "profit": _safe_float(getattr(account, "profit", 0.0)),
            "margin": _safe_float(getattr(account, "margin", 0.0)),
            "free_margin": _safe_float(getattr(account, "margin_free", 0.0)),
            "open_trades": open_trades_count,
            "currency": getattr(account, "currency", "USD"),
        }
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail={
                "message": "Unable to retrieve MT5 account information.",
                "error": str(exc),
            },
        ) from exc