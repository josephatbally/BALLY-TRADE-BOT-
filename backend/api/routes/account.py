"""
BALLY FLOW API - Account Routes

Authenticated account presentation. SQLite identifies the tenant's configured
trading account; MT5 remains the source of truth for live account state.
"""
from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Depends

from backend.security.jwt_auth import get_current_user
from backend.trading_engine.trading_account_runtime import (
    resolve_authenticated_trading_account,
)
from backend.trading_engine.market_data.mt5_connection import get_positions

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
def get_account(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Return the authenticated user's configured account plus live MT5 state."""
    resolved = resolve_authenticated_trading_account(int(user["id"]))
    configured = resolved["configured_account"]
    live = resolved["live_account"]

    if not configured:
        return {
            "status": "NO_ACCOUNT",
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

    if resolved["status"] != "READY":
        return {
            "status": resolved["status"],
            "connected": False,
            "identity_match": False,
            "account": {
                "id": configured["id"],
                "trading_account_id": configured["id"],
                "account_number": configured["account_number"],
                "broker_server": configured["broker_server"],
                "broker_name": configured["broker_name"],
                "platform": configured["platform"],
                "connection_status": configured["connection_status"],
                "is_demo": bool(configured["is_demo"]),
            },
            "broker": {
                "company": configured["broker_name"],
                "server": configured["broker_server"],
                "login": configured["account_number"],
                "leverage": configured["leverage"],
                "name": None,
                "trade_mode": "DEMO" if configured["is_demo"] else "REAL",
            },
            "balance": 0.0,
            "equity": 0.0,
            "profit": 0.0,
            "margin": 0.0,
            "free_margin": 0.0,
            "open_trades": 0,
            "currency": configured["currency"],
        }

    try:
        positions = get_positions() or []
        open_trades_count = len(positions)
    except Exception:
        open_trades_count = 0

    return {
        "status": "READY",
        "connected": True,
        "identity_match": True,
        "account": {
            "id": configured["id"],
            "trading_account_id": configured["id"],
            "account_number": configured["account_number"],
            "broker_server": configured["broker_server"],
            "broker_name": configured["broker_name"],
            "platform": configured["platform"],
            "connection_status": configured["connection_status"],
            "is_demo": bool(configured["is_demo"]),
        },
        "broker": {
            "company": getattr(live, "company", configured["broker_name"]),
            "server": getattr(live, "server", configured["broker_server"]),
            "login": getattr(live, "login", configured["account_number"]),
            "leverage": _safe_int(getattr(live, "leverage", configured["leverage"])),
            "name": getattr(live, "name", None),
            "trade_mode": "DEMO" if configured["is_demo"] else "REAL",
        },
        "balance": _safe_float(getattr(live, "balance", 0.0)),
        "equity": _safe_float(getattr(live, "equity", 0.0)),
        "profit": _safe_float(getattr(live, "profit", 0.0)),
        "margin": _safe_float(getattr(live, "margin", 0.0)),
        "free_margin": _safe_float(getattr(live, "margin_free", 0.0)),
        "open_trades": open_trades_count,
        "currency": getattr(live, "currency", configured["currency"]),
    }
