"""
BALLY FLOW - Terminal-attached trading-account runtime resolution.

BALLY FLOW does NOT ask the user to log into MT5.

The bot runs on the same machine as the MetaTrader 5 terminal.
The authenticated tenant must have an active DB-3 trading account, and the
currently connected MT5 login must match that configured account identity.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from backend.trading_engine.market_data.mt5_connection import (
    ensure_mt5_connected,
    get_account_info,
    is_mt5_connected,
)
from backend.trading_engine.tenant_router import tenant_router


def _read(source: Any, name: str, default: Any = None) -> Any:
    if source is None:
        return default
    if isinstance(source, dict):
        return source.get(name, default)
    return getattr(source, name, default)


def get_authenticated_trading_account(user_id: int | str) -> Optional[Dict[str, Any]]:
    """Return the stored trading-account metadata for the tenant, if any."""
    return tenant_router.get_user_trading_account(user_id)


def terminal_account_snapshot(live_account: Any) -> Dict[str, Any]:
    """Build a trading-account record from the running MT5 terminal."""
    login = _read(live_account, "login")
    try:
        account_id = int(login)
    except (TypeError, ValueError):
        account_id = 0

    return {
        "id": account_id,
        "trading_account_id": account_id,
        "account_number": str(login or ""),
        "broker_server": _read(live_account, "server", "") or "",
        "broker_name": _read(live_account, "company", "") or "",
        "account_name": _read(live_account, "name", "") or "",
        "currency": _read(live_account, "currency", "USD") or "USD",
        "leverage": _read(live_account, "leverage"),
        "platform": "MT5",
        "is_active": 1,
        "connection_status": "CONNECTED",
        "source": "MT5_TERMINAL",
    }


def resolve_authenticated_trading_account(user_id: int | str) -> Dict[str, Any]:
    """Resolve and authenticate the tenant's configured MT5 account."""
    stored_account=get_authenticated_trading_account(user_id)
    if not stored_account:
        return {"status":"NO_ACCOUNT","configured_account":None,"stored_account":None,"live_account":None,"identity_match":False,"reason":"No active trading account is configured for this user."}
    if not is_mt5_connected():
        return {"status":"OFFLINE","configured_account":stored_account,"stored_account":stored_account,"live_account":None,"identity_match":False,"reason":"MetaTrader 5 terminal is not connected."}
    live_account=get_account_info()
    if live_account is None:
        return {"status":"ACCOUNT_UNAVAILABLE","configured_account":stored_account,"stored_account":stored_account,"live_account":None,"identity_match":False,"reason":"MetaTrader 5 is connected but no account information is available."}
    configured_number=str(stored_account.get("account_number","")).strip()
    live_number=str(_read(live_account,"login","")).strip()
    if not configured_number or configured_number != live_number:
        return {"status":"ACCOUNT_MISMATCH","configured_account":stored_account,"stored_account":stored_account,"live_account":live_account,"identity_match":False,"reason":"Connected MT5 account does not match the authenticated user's configured trading account."}
    return {"status":"READY","configured_account":stored_account,"stored_account":stored_account,"live_account":live_account,"identity_match":True}
