"""BALLY FLOW API - authenticated open positions."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException

from backend.security.jwt_auth import get_current_user
from backend.trading_engine.market_data.mt5_connection import get_positions, is_mt5_connected
from backend.trading_engine.tenant_router import tenant_router
from backend.trading_engine.trading_account_runtime import get_authenticated_trading_account

router = APIRouter()


def _read(position: Any, name: str, default: Any = None) -> Any:
    try:
        return getattr(position, name, default)
    except Exception:
        return default


def _float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _position_type(value: Any) -> str:
    raw = _int(value)
    return "BUY" if raw == 0 else "SELL" if raw == 1 else "UNKNOWN"


def _open_time(value: Any) -> str | None:
    try:
        return datetime.fromtimestamp(float(value), tz=timezone.utc).isoformat()
    except (TypeError, ValueError, OSError, OverflowError):
        return None


def _normalize(position: Any) -> Dict[str, Any]:
    return {
        "ticket": _int(_read(position, "ticket")),
        "symbol": _read(position, "symbol"),
        "type": _position_type(_read(position, "type")),
        "volume": _float(_read(position, "volume")),
        "open_price": _float(_read(position, "price_open")),
        "current_price": _float(_read(position, "price_current")),
        "stop_loss": _float(_read(position, "sl")),
        "take_profit": _float(_read(position, "tp")),
        "profit": _float(_read(position, "profit")),
        "swap": _float(_read(position, "swap")),
        "magic": _int(_read(position, "magic")),
        "comment": _read(position, "comment"),
        "open_time": _open_time(_read(position, "time")),
    }


@router.get("")
def get_open_positions(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Return only live MT5 positions belonging to the authenticated tenant.

    SQLite user_orders provides tenant ownership; MT5 provides the live
    position fields. If the tenant has no active account or no recorded
    tickets, this endpoint fails closed with an empty position set.
    """
    user_id = int(user["id"])
    account = get_authenticated_trading_account(user_id)
    if not account:
        return {"status": "NO_ACCOUNT", "connected": False, "count": 0, "positions": []}

    if not is_mt5_connected():
        return {"status": "OFFLINE", "connected": False, "count": 0, "positions": []}

    try:
        raw_positions = get_positions() or []
        live_positions: List[Dict[str, Any]] = [_normalize(p) for p in raw_positions]
        positions = tenant_router.filter_user_positions(user_id, live_positions)
        return {
            "status": "READY",
            "connected": True,
            "count": len(positions),
            "positions": positions,
        }
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail={"message": "Unable to retrieve MT5 open positions.", "error": str(exc)},
        ) from exc
