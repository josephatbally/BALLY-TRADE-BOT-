"""
BALLY FLOW API - Account Routes

Provides read-only MT5 account information to the BALLY FLOW
mobile application.

IMPORTANT
---------
This module is an API/presentation layer.

It does NOT:
    - calculate trading signals
    - calculate SMC
    - calculate confluence
    - calculate risk
    - calculate position size
    - place orders
    - modify account state

All account information comes directly from the connected MT5
terminal through the shared MT5 connection layer.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from backend.trading_engine.market_data.mt5_connection import (
    get_account_info,
    is_mt5_connected,
)


router = APIRouter()


# =====================================================================
# HELPERS
# =====================================================================

def _safe_float(value: Any) -> float:
    """
    Safely convert an MT5 numeric value to float.
    """

    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


# =====================================================================
# ACCOUNT
# =====================================================================

@router.get("")
def get_account():
    """
    Return read-only MT5 account information.

    This endpoint is intended for dashboard portfolio metrics.
    """

    if not is_mt5_connected():
        return {
            "status": "OFFLINE",
            "connected": False,
            "balance": None,
            "equity": None,
            "profit": None,
            "margin": None,
            "free_margin": None,
            "open_trades": None,
            "currency": None,
        }

    try:
        account = get_account_info()

        if account is None:
            raise RuntimeError(
                "MT5 account information is unavailable."
            )

        open_trades = 0

        return {
            "status": "READY",
            "connected": True,
            "balance": _safe_float(
                getattr(account, "balance", None)
            ),
            "equity": _safe_float(
                getattr(account, "equity", None)
            ),
            "profit": _safe_float(
                getattr(account, "profit", None)
            ),
            "margin": _safe_float(
                getattr(account, "margin", None)
            ),
            "free_margin": _safe_float(
                getattr(account, "margin_free", None)
            ),
            "open_trades": open_trades,
            "currency": getattr(
                account,
                "currency",
                None,
            ),
        }

    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail={
                "message": (
                    "Unable to retrieve MT5 account information."
                ),
                "error": str(exc),
            },
        ) from exc