"""
BALLY FLOW API - Open Positions Routes

Read-only MT5 open-position information for the BALLY FLOW mobile app.

This module is an API/presentation layer.

It does NOT:
    - place orders
    - modify positions
    - calculate risk
    - perform execution validation
    - make trading decisions
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

from backend.trading_engine.market_data.mt5_connection import (
    get_positions,
    is_mt5_connected,
)


router = APIRouter()


# ==================================================================
# HELPERS
# ==================================================================

def _read_value(
    position: Any,
    name: str,
    default: Any = None,
) -> Any:
    """Safely read a value from an MT5 position object."""

    try:
        return getattr(
            position,
            name,
            default,
        )
    except Exception:
        return default


def _safe_float(
    value: Any,
) -> float:
    """Convert a value to float safely."""

    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _safe_int(
    value: Any,
) -> int:
    """Convert a value to int safely."""

    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _position_type(
    value: Any,
) -> str:
    """
    Convert MT5 position type to a mobile-friendly direction.
    """

    try:
        raw_type = int(value)
    except (TypeError, ValueError):
        return "UNKNOWN"

    # MetaTrader 5:
    # POSITION_TYPE_BUY  = 0
    # POSITION_TYPE_SELL = 1

    if raw_type == 0:
        return "BUY"

    if raw_type == 1:
        return "SELL"

    return "UNKNOWN"


def _format_open_time(
    value: Any,
) -> str | None:
    """
    Convert MT5 position time into an ISO-8601 UTC string.
    """

    if value is None:
        return None

    try:
        timestamp = float(value)

        return datetime.fromtimestamp(
            timestamp,
            tz=timezone.utc,
        ).isoformat()

    except (TypeError, ValueError, OSError, OverflowError):
        return None


def _normalize_position(
    position: Any,
) -> Dict[str, Any]:
    """
    Convert a raw MT5 position object into the stable BALLY FLOW API
    representation.
    """

    raw_type = _read_value(
        position,
        "type",
    )

    return {
        "ticket": _safe_int(
            _read_value(
                position,
                "ticket",
            )
        ),

        "symbol": _read_value(
            position,
            "symbol",
        ),

        "type": _position_type(
            raw_type
        ),

        "volume": _safe_float(
            _read_value(
                position,
                "volume",
            )
        ),

        "open_price": _safe_float(
            _read_value(
                position,
                "price_open",
            )
        ),

        "current_price": _safe_float(
            _read_value(
                position,
                "price_current",
            )
        ),

        "stop_loss": _safe_float(
            _read_value(
                position,
                "sl",
            )
        ),

        "take_profit": _safe_float(
            _read_value(
                position,
                "tp",
            )
        ),

        "profit": _safe_float(
            _read_value(
                position,
                "profit",
            )
        ),

        "swap": _safe_float(
            _read_value(
                position,
                "swap",
            )
        ),

        "magic": _safe_int(
            _read_value(
                position,
                "magic",
            )
        ),

        "comment": _read_value(
            position,
            "comment",
        ),

        "open_time": _format_open_time(
            _read_value(
                position,
                "time",
            )
        ),
    }


# ==================================================================
# OPEN POSITIONS
# ==================================================================

@router.get("")
def get_open_positions() -> Dict[str, Any]:
    """
    Return all currently open MT5 positions.

    This endpoint is strictly read-only.
    """

    if not is_mt5_connected():
        return {
            "status": "OFFLINE",
            "connected": False,
            "count": 0,
            "positions": [],
        }

    try:
        raw_positions = get_positions()

        positions: List[Dict[str, Any]] = [
            _normalize_position(position)
            for position in raw_positions
        ]

        return {
            "status": "READY",
            "connected": True,
            "count": len(positions),
            "positions": positions,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail={
                "message": (
                    "Unable to retrieve MT5 open positions."
                ),
                "error": str(exc),
            },
        ) from exc