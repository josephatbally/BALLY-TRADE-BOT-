"""
BALLY FLOW - Authenticated trading-account runtime resolution.

DB-3 durable trading_accounts identify which MT5 account belongs to the
authenticated tenant. MT5 remains the source of truth for live connection and
account state; this module only resolves and validates the relationship.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from backend.trading_engine.market_data.mt5_connection import (
    get_account_info,
    is_mt5_connected,
)
from backend.trading_engine.tenant_router import tenant_router


def get_authenticated_trading_account(user_id: int | str) -> Optional[Dict[str, Any]]:
    """Return the authenticated user's active DB-3 trading account."""
    return tenant_router.get_user_trading_account(user_id)


def _normalise_text(value: Any) -> str:
    return str(value or "").strip().casefold()


def _account_identity_matches(configured: Dict[str, Any], live: Any) -> bool:
    """Validate login and broker server when both are available."""
    configured_login = _normalise_text(configured.get("account_number"))
    live_login = _normalise_text(getattr(live, "login", None))
    configured_server = _normalise_text(configured.get("broker_server"))
    live_server = _normalise_text(getattr(live, "server", None))

    if not configured_login or not live_login or configured_login != live_login:
        return False

    # Server identity is part of the durable account identity. Require it when
    # MT5 exposes it; this prevents a same-login account from being misrouted.
    if configured_server and live_server and configured_server != live_server:
        return False

    return True


def resolve_authenticated_trading_account(
    user_id: int | str,
) -> Dict[str, Any]:
    """
    Resolve the authenticated tenant's active account and current MT5 state.

    The returned ``live_account`` is always read directly from MT5. No live
    balance/equity/margin/position state is read from SQLite.
    """
    configured = get_authenticated_trading_account(user_id)
    if not configured:
        return {
            "status": "NO_ACCOUNT",
            "configured_account": None,
            "live_account": None,
            "identity_match": False,
        }

    if not is_mt5_connected():
        return {
            "status": "OFFLINE",
            "configured_account": configured,
            "live_account": None,
            "identity_match": False,
        }

    live_account = get_account_info()
    if live_account is None:
        return {
            "status": "ACCOUNT_UNAVAILABLE",
            "configured_account": configured,
            "live_account": None,
            "identity_match": False,
        }

    identity_match = _account_identity_matches(configured, live_account)
    return {
        "status": "READY" if identity_match else "ACCOUNT_MISMATCH",
        "configured_account": configured,
        "live_account": live_account,
        "identity_match": identity_match,
    }
